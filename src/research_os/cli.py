"""Manufacturing AI Research OS CLI (spec section 39)."""
from __future__ import annotations

import typer
from sqlalchemy import func, select

from research_os.core import env_info
from research_os.core.config import industries_config, models_config, problems_config, technologies_config
from research_os.core.logging_setup import get_logger, setup_logging
from research_os.core.timeutils import utc_now
from research_os.database.db import init_db, session_scope
from research_os.database.models import (
    Document,
    Industry,
    KnowledgeEdge,
    KnowledgeNode,
    LLMRun,
    Problem,
    Skill,
    Technology,
)
from research_os.evaluation.apply_config import apply_role_selection_to_models_yaml
from research_os.evaluation.lab import render_report, run_evaluation
from research_os.evaluation.local_benchmark import (
    derive_role_selection_from_db,
    render_report as render_local_benchmark_report,
    run_local_benchmark,
)
from research_os.knowledge.skills import LEVEL_LABELS, list_skills, seed_default_skills
from research_os.models.anthropic import AnthropicAdapter
from research_os.models.gateway import build_default_adapters
from research_os.models.local import OllamaAdapter
from research_os.research import pipeline
from research_os.reports.daily import write_daily_report
from research_os.reports.weekly import write_weekly_report
from research_os.agents.researcher import ResearchAgent
from research_os.models.gateway import ModelGateway

app = typer.Typer(help="Manufacturing AI Research OS — Personal Industrial AI Research & Skill OS")
report_app = typer.Typer(help="Generate reports")
app.add_typer(report_app, name="report")

logger = get_logger("cli")


@app.command()
def init() -> None:
    """Initialize the database and seed taxonomy/skill data."""
    setup_logging()
    init_db()

    with session_scope() as session:
        for industry in industries_config().get("industries", []):
            if not session.scalars(select(Industry).where(Industry.key == industry["id"])).first():
                session.add(Industry(key=industry["id"], name=industry["name"], priority=industry.get("priority", 1)))

        for tech in technologies_config().get("technologies", []):
            if not session.scalars(select(Technology).where(Technology.key == tech["id"])).first():
                session.add(Technology(key=tech["id"], name=tech["name"]))

        for problem in problems_config().get("problems", []):
            if not session.scalars(select(Problem).where(Problem.key == problem["id"])).first():
                session.add(Problem(key=problem["id"], name=problem["name"]))

        created_skills = seed_default_skills(session)

    typer.echo("Research OS initialized.")
    typer.echo("  Database: data/database/research_os.db")
    typer.echo(f"  Skills seeded: {created_skills}")


@app.command()
def status() -> None:
    """Show system, database, LLM, knowledge graph and skill graph status."""
    setup_logging()
    env = env_info.summary()

    with session_scope() as session:
        total = session.scalar(select(func.count()).select_from(Document)) or 0
        analyzed = session.scalar(select(func.count()).select_from(Document).where(Document.status == "analyzed")) or 0
        pending = session.scalar(select(func.count()).select_from(Document).where(Document.status != "analyzed")) or 0
        failed = session.scalar(select(func.count()).select_from(Document).where(Document.processing_status == "error")) or 0
        qa_flagged = session.scalar(select(func.count()).select_from(Document).where(Document.qa_status == "flagged")) or 0

        local_calls = session.scalar(select(func.count()).select_from(LLMRun).where(LLMRun.provider == "ollama")) or 0
        cloud_calls = session.scalar(
            select(func.count()).select_from(LLMRun).where(LLMRun.provider.in_(["anthropic", "openai", "google"]))
        ) or 0
        est_cost = session.scalar(select(func.sum(LLMRun.estimated_cost_usd))) or 0.0

        node_count = session.scalar(select(func.count()).select_from(KnowledgeNode)) or 0
        edge_count = session.scalar(select(func.count()).select_from(KnowledgeEdge)) or 0
        skill_count = session.scalar(select(func.count()).select_from(Skill)) or 0

    routing = models_config()
    local_available = OllamaAdapter().is_available()
    cloud_available = AnthropicAdapter().is_available()

    typer.echo("Research OS Status")
    typer.echo("")
    typer.echo("Environment:")
    typer.echo(f"  OS:   {env['os']}")
    typer.echo(f"  CPU:  {env['cpu']}")
    typer.echo(f"  RAM:  {env['ram_gb']} GB" if env["ram_gb"] else "  RAM:  unknown")
    typer.echo(f"  GPU:  {env['gpu']}")
    typer.echo("")
    typer.echo("Database:")
    typer.echo(f"  Documents: {total}")
    typer.echo(f"  Analyzed:  {analyzed}")
    typer.echo(f"  Pending:   {pending}")
    typer.echo(f"  Failed:    {failed}")
    typer.echo(f"  QA flagged: {qa_flagged}")
    typer.echo("")
    typer.echo("LLM:")
    typer.echo(f"  Local (Ollama):    {'available' if local_available else 'not available'}")
    typer.echo(f"  Cloud (Anthropic): {'configured' if cloud_available else 'not configured'}")
    typer.echo("")
    typer.echo("Model Router:")
    typer.echo(f"  Current local tier model:  {routing['tiers']['local_standard']['model']}")
    typer.echo(f"  Current cloud tier model:  {routing['tiers']['cloud_standard']['model']}")
    typer.echo("")
    typer.echo("LLM Calls:")
    typer.echo(f"  Local:  {local_calls}")
    typer.echo(f"  Cloud:  {cloud_calls}")
    typer.echo(f"  Estimated cost: ${est_cost:.4f}")
    typer.echo("")
    typer.echo("Knowledge Graph:")
    typer.echo(f"  Nodes: {node_count}")
    typer.echo(f"  Edges: {edge_count}")
    typer.echo("")
    typer.echo("Skill Graph:")
    typer.echo(f"  Skills: {skill_count}")


_UNAVAILABLE_HINTS = {
    "ollama": "Ollama not reachable",
    "anthropic": "ANTHROPIC_API_KEY not set",
    "openai": "OPENAI_API_KEY not set",
    "google": "GOOGLE_API_KEY not set",
}


@app.command()
def models() -> None:
    """List configured model tiers and provider availability."""
    cfg = models_config()
    adapters = build_default_adapters()
    availability = {name: adapter.is_available() for name, adapter in adapters.items()}
    typer.echo("Configured model tiers:")
    for tier, entry in cfg.get("tiers", {}).items():
        provider = entry["provider"]
        if provider not in adapters:
            avail = "unknown"
        elif availability[provider]:
            avail = "available"
        else:
            avail = f"unavailable ({_UNAVAILABLE_HINTS.get(provider, 'not configured')})"
        typer.echo(f"  {tier:20s} -> {provider}:{entry['model']:30s} [{avail}]")


@app.command()
def collect(source: str = typer.Option(None, "--source", help="arxiv | rss | github")) -> None:
    """Run collectors (COLLECT -> NORMALIZE -> DEDUPLICATE -> STORE)."""
    setup_logging()
    init_db()
    stats = pipeline.collect_and_store(source=source)
    typer.echo(
        f"Collected: discovered={stats.discovered} new={stats.new_documents} "
        f"duplicates={stats.duplicates} failed={stats.failed}"
    )
    for err in stats.errors[:10]:
        typer.echo(f"  ! {err}")


@app.command()
def classify(no_llm: bool = typer.Option(False, "--no-llm")) -> None:
    """Classify pending documents into Industry x Technology x Problem."""
    setup_logging()
    init_db()
    stats = pipeline.run_classify(use_llm=not no_llm)
    typer.echo(f"Classified: processed={stats.processed} failed={stats.failed}")


@app.command()
def summarize(no_llm: bool = typer.Option(False, "--no-llm")) -> None:
    """Summarize pending documents."""
    setup_logging()
    init_db()
    stats = pipeline.run_summarize(use_llm=not no_llm)
    typer.echo(f"Summarized: processed={stats.processed} failed={stats.failed}")


@app.command()
def analyze(no_llm: bool = typer.Option(False, "--no-llm")) -> None:
    """Analyze documents (evidence/practical/novelty/battery relevance/score)."""
    setup_logging()
    init_db()
    stats = pipeline.run_analyze(use_llm=not no_llm)
    typer.echo(f"Analyzed: processed={stats.processed} failed={stats.failed}")


@app.command()
def transfer(no_llm: bool = typer.Option(False, "--no-llm")) -> None:
    """Run Cross-Industry Technology Transfer analysis."""
    setup_logging()
    init_db()
    stats = pipeline.run_transfer(use_llm=not no_llm)
    typer.echo(f"Transfer analysis: processed={stats.processed} failed={stats.failed}")


@app.command()
def qa() -> None:
    """Run the QA grounding check over analyzed documents (flags, never blocks)."""
    setup_logging()
    init_db()
    stats = pipeline.run_qa_check()
    typer.echo(f"QA check: processed={stats.processed} failed={stats.failed}")


@app.command()
def run(no_llm: bool = typer.Option(False, "--no-llm", help="Skip LLM calls, use rule-based fallback only")) -> None:
    """Run the full pipeline: collect -> classify -> summarize -> analyze -> transfer -> qa -> store."""
    setup_logging()
    init_db()
    result = pipeline.run_full_pipeline(use_llm=not no_llm)
    for stage, stats in result.items():
        if stage == "stored":
            typer.echo(f"stored: {stats} document(s) marked analyzed")
            continue
        typer.echo(
            f"{stage}: discovered={stats.discovered} new={stats.new_documents} "
            f"processed={stats.processed} failed={stats.failed}"
        )


@report_app.command("daily")
def report_daily(no_llm: bool = typer.Option(False, "--no-llm")) -> None:
    """Generate the Daily Industrial AI Briefing."""
    setup_logging()
    init_db()
    with session_scope() as session:
        path = write_daily_report(session, use_llm=not no_llm)
    typer.echo(f"Daily report written to {path}")


@report_app.command("weekly")
def report_weekly(no_llm: bool = typer.Option(False, "--no-llm")) -> None:
    """Generate the Weekly Industrial AI Briefing."""
    setup_logging()
    init_db()
    with session_scope() as session:
        path = write_weekly_report(session, use_llm=not no_llm)
    typer.echo(f"Weekly report written to {path}")


@app.command()
def research(topic: str, no_llm: bool = typer.Option(False, "--no-llm")) -> None:
    """Deep Research over a specific question, grounded in the local knowledge base."""
    setup_logging()
    init_db()
    gateway = None if no_llm else ModelGateway()
    agent = ResearchAgent(gateway)
    with session_scope() as session:
        result = agent.research(session, topic)

    from research_os.core.paths import resolve

    ts = utc_now().strftime("%Y%m%d-%H%M%S")
    safe_topic = "".join(c if c.isalnum() else "-" for c in topic.lower())[:60]
    out_path = resolve("data/reports") / f"research-{safe_topic}-{ts}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        f"# Research: {topic}\n\nModel: {result['model_used']}\n\n"
        f"## Sources\n{result['sources_text']}\n\n## Synthesis\n{result['synthesis']}\n",
        encoding="utf-8",
    )
    typer.echo(result["synthesis"])
    typer.echo(f"\nSaved to {out_path}")


@app.command()
def evaluate() -> None:
    """Run the Local LLM Benchmark (spec: LOCAL LLM SETUP + BENCHMARK TASK) plus
    a cloud-tier availability smoke test, and write data/reports/model-benchmark.md."""
    setup_logging()
    init_db()

    local_result = run_local_benchmark()
    content = render_local_benchmark_report(local_result)

    cloud_rows = [r for r in run_evaluation() if r.provider != "ollama"]
    if cloud_rows:
        content += "\n" + render_report(cloud_rows).replace(
            "# Model Benchmark Report", "## Cloud Tier Availability (smoke test)"
        )

    from research_os.core.paths import resolve

    out_path = resolve("data/reports") / "model-benchmark.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    typer.echo(content)
    typer.echo(f"Saved to {out_path}")
    if any(local_result.role_selection.values()):
        typer.echo("\nRun `research-os benchmark-apply` to write these role selections into config/models.yaml.")


@app.command("benchmark-apply")
def benchmark_apply() -> None:
    """Update config/models.yaml local_fast/local_standard/local_reasoning
    from the most recent `research-os evaluate` results in the database."""
    setup_logging()
    init_db()
    with session_scope() as session:
        role_selection = derive_role_selection_from_db(session)

    if not any(role_selection.values()):
        typer.echo("No local benchmark results in the database yet — run `research-os evaluate` first.")
        raise typer.Exit(code=1)

    changes = apply_role_selection_to_models_yaml(role_selection)
    if not changes:
        typer.echo("config/models.yaml already matches the latest benchmark results — nothing to change.")
        return

    typer.echo("Updated config/models.yaml:")
    for change in changes:
        typer.echo(f"  {change}")


@app.command()
def skills() -> None:
    """Show the Personal Skill Graph."""
    setup_logging()
    init_db()
    with session_scope() as session:
        seed_default_skills(session)
    with session_scope() as session:
        rows = list_skills(session)
        for skill in rows:
            indent = "  " if skill.parent_key else ""
            typer.echo(f"{indent}{skill.name:30s} Level {skill.level} ({LEVEL_LABELS.get(skill.level, '?')})")


if __name__ == "__main__":
    app()
