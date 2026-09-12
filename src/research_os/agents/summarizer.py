"""SummarizerAgent (spec section 31): technical summary plus
problem/method/result/limitation/application extraction.
"""
from __future__ import annotations

import json

from research_os.core.logging_setup import get_logger
from research_os.core.schema import ResearchItem
from research_os.models.gateway import AllProvidersUnavailableError, ModelGateway
from research_os.processing.extraction import extract_structured, heuristic_summary

logger = get_logger("agents.summarizer")

_PROMPT_TEMPLATE = """Summarize this technical document for an Industrial AI researcher.
Return ONLY a JSON object with keys: summary (2-3 sentences), problem, method, result, limitation, application.
Do not invent facts not present in the text.

Title: {title}
Abstract: {abstract}
"""


class SummarizerAgent:
    def __init__(self, gateway: ModelGateway | None = None) -> None:
        self.gateway = gateway

    def _rule_based(self, item: ResearchItem) -> dict:
        fields = extract_structured(item.abstract)
        return {
            "summary": heuristic_summary(item.title, item.abstract),
            **fields,
            "model_used": "heuristic_extraction_fallback",
        }

    def summarize(self, item: ResearchItem) -> dict:
        if self.gateway is None:
            return self._rule_based(item)

        try:
            prompt = _PROMPT_TEMPLATE.format(title=item.title, abstract=(item.abstract or "")[:3000])
            result = self.gateway.generate(
                prompt=prompt,
                agent="SummarizerAgent",
                task_type="summarization",
                complexity="medium",
                privacy_level=item.privacy_level,
                max_tokens=500,
            )
            start, end = result.text.find("{"), result.text.rfind("}")
            parsed = json.loads(result.text[start : end + 1])
            parsed["model_used"] = f"{result.provider}:{result.model}"
            return parsed
        except (AllProvidersUnavailableError, json.JSONDecodeError, ValueError) as exc:
            logger.info("summarizer falling back to heuristic extraction: %s", exc)
            return self._rule_based(item)
