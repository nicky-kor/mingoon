"""Scoring (spec section 20). Weights and priority thresholds are read from
config/scoring.yaml so they can be tuned without touching code.
"""
from __future__ import annotations

from dataclasses import dataclass

from research_os.core.config import scoring_config


@dataclass
class ScoreInput:
    battery_relevance: float = 0.0
    transferability: float = 0.0
    evidence_quality: float = 0.0
    practical_applicability: float = 0.0
    novelty: float = 0.0


@dataclass
class ScoreResult:
    overall_score: float
    priority: str
    breakdown: ScoreInput


def compute_score(inputs: ScoreInput) -> ScoreResult:
    cfg = scoring_config()
    weights = cfg["weights"]
    thresholds = cfg["priority_thresholds"]

    overall = (
        inputs.battery_relevance * weights["battery_relevance"]
        + inputs.transferability * weights["transferability"]
        + inputs.evidence_quality * weights["evidence_quality"]
        + inputs.practical_applicability * weights["practical_applicability"]
        + inputs.novelty * weights["novelty"]
    )
    overall = round(max(0.0, min(100.0, overall)), 2)

    if overall >= thresholds["critical"]:
        priority = "Critical"
    elif overall >= thresholds["high"]:
        priority = "High"
    elif overall >= thresholds["medium"]:
        priority = "Medium"
    elif overall >= thresholds["low"]:
        priority = "Low"
    else:
        priority = "Archive"

    return ScoreResult(overall_score=overall, priority=priority, breakdown=inputs)
