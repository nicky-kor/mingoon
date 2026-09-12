"""Daily Industrial AI Briefing (spec section 37)."""
from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session

from research_os.agents.briefing import BriefingAgent
from research_os.core.paths import resolve
from research_os.database.models import Document, Score, TransferOpportunity
from research_os.models.gateway import ModelGateway


def _top_documents(session: Session, since: dt.datetime, limit: int = 10) -> list[tuple[Document, Score | None]]:
    docs = session.scalars(
        select(Document).where(Document.collected_at >= since)
    ).all()
    scored = []
    for d in docs:
        score = session.scalars(select(Score).where(Score.document_id == d.id)).first()
        scored.append((d, score))
    scored.sort(key=lambda pair: pair[1].overall_score if pair[1] else -1, reverse=True)
    return scored[:limit]


def generate_daily_report(session: Session, use_llm: bool = True) -> str:
    today = dt.datetime.utcnow()
    since = today - dt.timedelta(days=1)
    top = _top_documents(session, since)

    battery_docs = [d for d, s in top if d.industry == "battery_manufacturing"]
    pm_docs = [d for d, s in top if d.problem in ("fault_diagnosis", "rul_estimation", "condition_monitoring")]
    transfers = session.scalars(
        select(TransferOpportunity).where(TransferOpportunity.created_at >= since)
    ).all()
    github_docs = [d for d, s in top if d.source_type == "github"]
    papers = [d for d, s in top if d.source_type == "arxiv"]

    gateway = ModelGateway() if use_llm else None
    briefing = BriefingAgent(gateway)
    facts = [f"{d.title} (score={s.overall_score if s else 'n/a'}, priority={s.priority if s else 'n/a'})" for d, s in top[:5]]
    summary = briefing.executive_summary(facts)

    lines = [
        f"# Daily Industrial AI Briefing — {today.date().isoformat()}",
        "",
        "## Executive Summary",
        summary,
        "",
        "## Top Industrial AI Developments",
    ]
    if top:
        for d, s in top:
            lines.append(f"- **{d.title}** — priority: {s.priority if s else 'n/a'} ({d.url or 'no url'})")
    else:
        lines.append("- No new documents collected in the last 24 hours.")

    lines += ["", "## Battery Manufacturing"]
    lines += [f"- {d.title}" for d in battery_docs] or ["- No battery-specific items today."]

    lines += ["", "## Predictive Maintenance"]
    lines += [f"- {d.title}" for d in pm_docs] or ["- No predictive-maintenance items today."]

    lines += ["", "## AI Technology"]
    tech_set = sorted({d.technology for d, _ in top if d.technology})
    lines += [f"- {t}" for t in tech_set] or ["- No technology classified today."]

    lines += ["", "## Cross-Industry Transfer"]
    lines += [f"- {t.source_industry} → {t.target_battery_process} (confidence {t.transfer_confidence:.0f})" for t in transfers] or ["- No transfer opportunities identified today."]

    lines += ["", "## Important Papers"]
    lines += [f"- {d.title} ({d.url})" for d in papers] or ["- None."]

    lines += ["", "## Important GitHub"]
    lines += [f"- {d.title} ({d.url})" for d in github_docs] or ["- None."]

    lines += ["", "## Topics to Watch"]
    lines += [f"- {t}" for t in tech_set[:5]] or ["- N/A"]

    return "\n".join(lines) + "\n"


def write_daily_report(session: Session, use_llm: bool = True) -> str:
    content = generate_daily_report(session, use_llm=use_llm)
    today = dt.datetime.utcnow().date().isoformat()
    out_path = resolve("data/reports") / f"{today}-daily.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    return str(out_path)
