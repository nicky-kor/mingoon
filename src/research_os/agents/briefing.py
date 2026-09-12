"""BriefingAgent (spec section 37-38): daily/weekly report narration.

Reports are assembled primarily from DB queries (facts); the LLM, when
available, is only used to write a short executive-summary paragraph over
those already-computed facts — it is never the source of the facts
themselves.
"""
from __future__ import annotations

from research_os.core.logging_setup import get_logger
from research_os.models.gateway import AllProvidersUnavailableError, ModelGateway

logger = get_logger("agents.briefing")

_PROMPT_TEMPLATE = """Write a 3-4 sentence executive summary for an Industrial AI research briefing,
based ONLY on these facts (do not add information not listed here):

{facts}
"""


class BriefingAgent:
    def __init__(self, gateway: ModelGateway | None = None) -> None:
        self.gateway = gateway

    def executive_summary(self, facts: list[str]) -> str:
        facts_text = "\n".join(f"- {f}" for f in facts) if facts else "- No new documents in this period."
        if self.gateway is not None:
            try:
                result = self.gateway.generate(
                    prompt=_PROMPT_TEMPLATE.format(facts=facts_text),
                    agent="BriefingAgent",
                    task_type="briefing",
                    complexity="medium",
                    reasoning_required=True,
                    importance=60,
                    max_tokens=300,
                )
                return result.text.strip()
            except AllProvidersUnavailableError as exc:
                logger.info("briefing agent falling back to templated summary: %s", exc)
        return facts_text
