"""AnalystAgent (spec section 32): technical significance / evidence quality.

Heuristic fallback scores 0-100 using simple, explainable signals so the
pipeline can run with zero configured models. When an LLM is available it
is asked for the same fields and is preferred.
"""
from __future__ import annotations

import json
import re

from research_os.core.config import battery_config
from research_os.core.logging_setup import get_logger
from research_os.core.schema import ResearchItem
from research_os.models.gateway import AllProvidersUnavailableError, ModelGateway

logger = get_logger("agents.analyst")

_PROMPT_TEMPLATE = """Analyze this document for an Industrial AI research system focused on Battery Manufacturing.
Return ONLY a JSON object with keys (all 0-100 integers): evidence_score, practical_score, novelty_score, battery_relevance.
Also include: key_findings (list of up to 4 strings, FACTS only from the text), limitations (string).

Title: {title}
Abstract: {abstract}
Industry: {industry}
Technology: {technology}
"""

_QUANT_PATTERN = re.compile(r"\d+(\.\d+)?\s?%")


class AnalystAgent:
    def __init__(self, gateway: ModelGateway | None = None) -> None:
        self.gateway = gateway

    def _battery_relevance_heuristic(self, item: ResearchItem) -> float:
        if item.industry == "battery_manufacturing":
            base = 70.0
        else:
            base = 20.0
        text = f"{item.title} {item.abstract or ''}".lower()
        battery_terms = [t for terms in battery_config().get("keywords", {}).values() for t in terms]
        hits = sum(1 for term in battery_terms if term.lower() in text)
        return min(100.0, base + hits * 5)

    def _heuristic(self, item: ResearchItem) -> dict:
        abstract = item.abstract or ""
        evidence_score = 40.0
        if _QUANT_PATTERN.search(abstract):
            evidence_score += 20
        if any(w in abstract.lower() for w in ["dataset", "experiment", "benchmark", "evaluate"]):
            evidence_score += 15
        if any(w in abstract.lower() for w in ["real-world", "industrial", "deployed", "field test"]):
            evidence_score += 15

        practical_score = 30.0
        if any(w in abstract.lower() for w in ["applied", "deployment", "real-world", "case study"]):
            practical_score += 30
        if item.technology:
            practical_score += 20

        novelty_score = 30.0
        if any(w in abstract.lower() for w in ["novel", "first", "state-of-the-art", "new approach"]):
            novelty_score += 30
        if item.technology in {"llm", "agentic_ai", "physics_informed_ml", "digital_twin"}:
            novelty_score += 20

        return {
            "evidence_score": min(100.0, evidence_score),
            "practical_score": min(100.0, practical_score),
            "novelty_score": min(100.0, novelty_score),
            "battery_relevance": self._battery_relevance_heuristic(item),
            "key_findings": [abstract[:200]] if abstract else [],
            "limitations": "Not enough information to assess limitations (heuristic fallback).",
            "model_used": "heuristic_fallback",
        }

    def analyze(self, item: ResearchItem) -> dict:
        if self.gateway is None:
            return self._heuristic(item)

        try:
            prompt = _PROMPT_TEMPLATE.format(
                title=item.title,
                abstract=(item.abstract or "")[:3000],
                industry=item.industry,
                technology=item.technology,
            )
            result = self.gateway.generate(
                prompt=prompt,
                agent="AnalystAgent",
                task_type="analysis",
                complexity="high",
                reasoning_required=True,
                importance=70,
                privacy_level=item.privacy_level,
                max_tokens=600,
            )
            start, end = result.text.find("{"), result.text.rfind("}")
            parsed = json.loads(result.text[start : end + 1])
            parsed.setdefault("battery_relevance", self._battery_relevance_heuristic(item))
            parsed["model_used"] = f"{result.provider}:{result.model}"
            return parsed
        except (AllProvidersUnavailableError, json.JSONDecodeError, ValueError) as exc:
            logger.info("analyst falling back to heuristic: %s", exc)
            return self._heuristic(item)
