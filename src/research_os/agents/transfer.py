"""TransferAgent (spec section 33): Cross-Industry Technology Transfer Radar.

Evaluates whether a technology proven in another industry could transfer to
Battery Manufacturing. Heuristic fallback produces a conservative
confidence score from keyword overlap; the LLM path (when available) is
asked to reason about the full transfer chain (spec section 4).
"""
from __future__ import annotations

import json

from research_os.core.config import battery_config
from research_os.core.json_utils import extract_json
from research_os.core.logging_setup import get_logger
from research_os.core.schema import ResearchItem
from research_os.models.gateway import AllProvidersUnavailableError, ModelGateway
from research_os.processing.classify import classify_battery_process

logger = get_logger("agents.transfer")

_PROMPT_TEMPLATE = """You evaluate Cross-Industry Technology Transfer opportunities for Battery
Manufacturing. Given a document from another industry, assess whether its technology could
transfer to a battery manufacturing process/equipment.

ClassifierAgent already matched this document's own text against the battery-process keyword
taxonomy and landed on: {process_hint}. Use it as target_battery_process unless the text gives
you a clearly better-justified target — the two should usually agree since they're reading the
same document.

Return ONLY a JSON object with keys:
target_battery_process, target_equipment, expected_benefit, implementation_difficulty
(one of: Low/Medium/High), risk, transfer_confidence (0-100 integer), research_question.
Be conservative. Do not invent papers, numbers, or citations not present in the text.

Source Industry: {industry}
Source Technology: {technology}
Title: {title}
Abstract: {abstract}
"""


class TransferAgent:
    def __init__(self, gateway: ModelGateway | None = None) -> None:
        self.gateway = gateway

    def _applies(self, item: ResearchItem) -> bool:
        # Transfer analysis is most meaningful for non-battery industries.
        return bool(item.industry) and item.industry != "battery_manufacturing" and bool(item.technology)

    def _heuristic(self, item: ResearchItem) -> dict:
        text = f"{item.title} {item.abstract or ''}".lower()
        battery_terms = [t for terms in battery_config().get("keywords", {}).values() for t in terms]
        overlap = sum(1 for term in battery_terms if term.lower() in text)
        confidence = min(80.0, 20.0 + overlap * 10)
        # Reuse ClassifierAgent's own determination when it already ran on
        # this item (the normal pipeline order is classify -> ... ->
        # transfer) instead of re-running the same keyword match here —
        # avoids the two agents silently disagreeing on the same document.
        process = item.target_process or classify_battery_process(item.title, item.abstract) or "coating"
        return {
            "target_battery_process": process,
            "target_equipment": None,
            "expected_benefit": (
                "INFERENCE: potential efficiency/quality gain if the source technology transfers "
                f"to battery {process} — not yet validated for this application."
            ),
            "implementation_difficulty": "Medium",
            "risk": "HYPOTHESIS: transfer feasibility unverified; requires domain validation.",
            "transfer_confidence": confidence,
            "research_question": (
                f"Can {item.technology or 'this technology'} from {item.industry} be adapted to "
                f"battery {process} equipment/process, and what data/sensors would be required?"
            ),
            "model_used": "heuristic_fallback",
        }

    def analyze_transfer(self, item: ResearchItem) -> dict | None:
        if not self._applies(item):
            return None
        if self.gateway is None:
            return self._heuristic(item)

        process_hint = item.target_process or classify_battery_process(item.title, item.abstract) or "unknown"
        try:
            prompt = _PROMPT_TEMPLATE.format(
                industry=item.industry, technology=item.technology, title=item.title,
                abstract=(item.abstract or "")[:3000],
                process_hint=process_hint,
            )
            result = self.gateway.generate(
                prompt=prompt,
                agent="TransferAgent",
                task_type="transferability",
                complexity="high",
                reasoning_required=True,
                importance=80,
                privacy_level=item.privacy_level,
                max_tokens=600,
            )
            parsed = extract_json(result.text)
            if parsed is None:
                raise ValueError("No JSON object found in model output")
            parsed.setdefault("target_battery_process", process_hint)
            parsed["model_used"] = f"{result.provider}:{result.model}"
            return parsed
        except (AllProvidersUnavailableError, json.JSONDecodeError, ValueError) as exc:
            logger.info("transfer agent falling back to heuristic: %s", exc)
            return self._heuristic(item)
