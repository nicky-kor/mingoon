"""ClassifierAgent (spec section 30): Industry x Technology x Problem.

Tries the LLM (local_fast by default, per config/routing.yaml) for a JSON
classification first; falls back to the deterministic rule-based classifier
in processing/classify.py whenever no model is available or the response
can't be parsed, so classification always succeeds.
"""
from __future__ import annotations

import json

from research_os.core.config import industries_config, problems_config, technologies_config
from research_os.core.json_utils import extract_json
from research_os.core.logging_setup import get_logger
from research_os.core.schema import ResearchItem
from research_os.models.gateway import AllProvidersUnavailableError, ModelGateway
from research_os.processing.classify import (
    classify_battery_process,
    classify_industry,
    classify_problem,
    classify_technology,
    extract_keywords,
)

logger = get_logger("agents.classifier")

_PROMPT_TEMPLATE = """You are classifying a technical document for an Industrial AI research system.
Return ONLY a JSON object with keys: industry, technology, problem, keywords (list of up to 6 strings).

Allowed industry values: {industries}
Allowed technology values: {technologies}
Allowed problem values: {problems}

Title: {title}
Abstract: {abstract}
"""


class ClassifierAgent:
    def __init__(self, gateway: ModelGateway | None = None) -> None:
        self.gateway = gateway

    def _rule_based(self, item: ResearchItem) -> dict:
        return {
            "industry": classify_industry(item.title, item.abstract),
            "technology": classify_technology(item.title, item.abstract),
            "problem": classify_problem(item.title, item.abstract),
            "keywords": extract_keywords(item.title, item.abstract),
            "target_process": classify_battery_process(item.title, item.abstract),
            "model_used": "rule_based_fallback",
        }

    def classify(self, item: ResearchItem) -> dict:
        if self.gateway is None:
            return self._rule_based(item)

        try:
            prompt = _PROMPT_TEMPLATE.format(
                industries=[i["id"] for i in industries_config().get("industries", [])],
                technologies=[t["id"] for t in technologies_config().get("technologies", [])],
                problems=[p["id"] for p in problems_config().get("problems", [])],
                title=item.title,
                abstract=(item.abstract or "")[:1500],
            )
            result = self.gateway.generate(
                prompt=prompt,
                agent="ClassifierAgent",
                task_type="classification",
                complexity="low",
                privacy_level=item.privacy_level,
                max_tokens=300,
            )
            parsed = extract_json(result.text)
            if parsed is None:
                raise ValueError("No JSON object found in model output")
            return {
                "industry": parsed.get("industry"),
                "technology": parsed.get("technology"),
                "problem": parsed.get("problem"),
                "keywords": parsed.get("keywords", []),
                "target_process": classify_battery_process(item.title, item.abstract),
                "model_used": f"{result.provider}:{result.model}",
            }
        except (AllProvidersUnavailableError, json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.info("classifier falling back to rule-based: %s", exc)
            return self._rule_based(item)
