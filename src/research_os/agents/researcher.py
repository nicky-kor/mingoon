"""ResearchAgent (spec section 35-36): Deep Research over a question.

Pipeline: Question -> Search existing knowledge (DB) -> Rank -> Synthesize.
Never invents papers/URLs/authors/numbers: synthesis is grounded strictly in
retrieved document rows, and the LLM prompt explicitly forbids fabrication.
"""
from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from research_os.core.grounding import unsupported_percentages
from research_os.core.logging_setup import get_logger
from research_os.database.models import Document, Score
from research_os.models.cascade import generate_with_cascade
from research_os.models.gateway import AllProvidersUnavailableError, ModelGateway

logger = get_logger("agents.researcher")

_PROMPT_TEMPLATE = """You are performing Deep Research for an Industrial AI researcher.
Question: {question}

Below are existing documents retrieved from the local knowledge base. Use ONLY these as your
evidence base. Clearly separate FACT (stated in the sources), INFERENCE (your reasoning from
the sources), and HYPOTHESIS (untested idea). Never invent a paper, author, URL, or number that
is not in the sources below. If evidence is thin, say so explicitly.

Sources:
{sources}

Write a concise research synthesis (structured with FACT / INFERENCE / HYPOTHESIS sections,
plus open research questions).
"""


class ResearchAgent:
    def __init__(self, gateway: ModelGateway | None = None) -> None:
        self.gateway = gateway

    def search(self, session: Session, question: str, limit: int = 10) -> list[Document]:
        terms = [t for t in question.lower().split() if len(t) > 2]
        if not terms:
            return []
        conditions = []
        for term in terms:
            like = f"%{term}%"
            conditions.append(Document.title.ilike(like))
            conditions.append(Document.abstract.ilike(like))
        # Rank keyword matches by AnalystAgent's own quality score
        # (overall_score) rather than arbitrary DB order, so a `limit`
        # cutoff keeps the most credible matches, not just the first ones
        # found. Prior art: OSS "deep research" agents (e.g. gpt-researcher,
        # deep-research-agent) rank/weight sources by a credibility signal
        # before synthesis rather than treating every match equally — we
        # already compute that signal (AnalystAgent's evidence/practical/
        # novelty scores feeding Score.overall_score), it just wasn't used
        # here. Documents without a Score yet (not analyzed) sort last
        # rather than being excluded.
        stmt = (
            select(Document)
            .outerjoin(Score, Score.document_id == Document.id)
            .where(or_(*conditions))
            .order_by(Score.overall_score.desc().nulls_last())
            .distinct()
            .limit(limit)
        )
        return list(session.scalars(stmt).all())

    def _format_sources(self, docs: list[Document]) -> str:
        if not docs:
            return "(no matching documents found in the local knowledge base)"
        lines = []
        for d in docs:
            lines.append(f"- [{d.external_id}] {d.title} ({d.url or 'no url'}) — {(d.abstract or '')[:300]}")
        return "\n".join(lines)

    def research(self, session: Session, question: str) -> dict:
        docs = self.search(session, question)
        sources_text = self._format_sources(docs)

        if self.gateway is not None:
            try:
                result, _ = generate_with_cascade(
                    self.gateway,
                    _PROMPT_TEMPLATE.format(question=question, sources=sources_text),
                    is_acceptable=lambda text: not unsupported_percentages(text, sources_text),
                    agent="ResearchAgent",
                    task_type="deep_research",
                    complexity="high",
                    reasoning_required=True,
                    importance=90,
                    max_tokens=1200,
                )
                synthesis = result.text
                model_used = f"{result.provider}:{result.model}"
            except AllProvidersUnavailableError as exc:
                logger.info("research agent falling back to extractive synthesis: %s", exc)
                synthesis = self._extractive_synthesis(question, docs)
                model_used = "extractive_fallback"
        else:
            synthesis = self._extractive_synthesis(question, docs)
            model_used = "extractive_fallback"

        return {
            "question": question,
            "documents_used": [d.external_id for d in docs],
            "sources_text": sources_text,
            "synthesis": synthesis,
            "model_used": model_used,
        }

    def _extractive_synthesis(self, question: str, docs: list[Document]) -> str:
        if not docs:
            return (
                f"FACT: No documents in the local knowledge base currently match '{question}'.\n"
                "HYPOTHESIS: Running `research-os collect` for relevant sources may surface evidence.\n"
            )
        lines = [f"FACT: {len(docs)} related document(s) found in the local knowledge base:"]
        for d in docs:
            lines.append(f"  - {d.title} ({d.url or 'no url'})")
        lines.append(
            "INFERENCE: These documents are keyword-related to the question; no LLM was "
            "available to synthesize deeper connections in this run."
        )
        return "\n".join(lines)
