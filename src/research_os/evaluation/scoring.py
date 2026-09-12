"""Automated heuristic scoring for the local LLM benchmark (spec section
10). These are cheap, deterministic proxies for response quality — not a
substitute for human judgment — used so `research-os evaluate` produces a
repeatable score without requiring manual grading of every response. They
are documented as heuristic in every report generated from them.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

# spec section 10 weights
WEIGHTS = {
    "quality": 0.30,
    "technical_accuracy": 0.20,
    "korean_quality": 0.15,
    "latency": 0.15,
    "resource_efficiency": 0.10,
    "stability": 0.10,
}

_JSON_REQUIRED_KEYS = {
    "classification": ["industry", "technology", "problem"],
    "korean_summary": ["problem", "method", "result", "limitation"],
    "battery_relevance": ["score", "reason", "candidate_process", "candidate_equipment"],
    "transferability": ["source_industry", "technology", "target_battery_process", "target_equipment", "transfer_score", "reason"],
}


def _extract_json(text: str):
    start_obj, end_obj = text.find("{"), text.rfind("}")
    start_arr, end_arr = text.find("["), text.rfind("]")
    candidates = []
    if start_obj != -1 and end_obj != -1:
        candidates.append(text[start_obj : end_obj + 1])
    if start_arr != -1 and end_arr != -1:
        candidates.append(text[start_arr : end_arr + 1])
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None


def _korean_ratio(text: str) -> float:
    if not text:
        return 0.0
    korean_chars = len(re.findall(r"[가-힣]", text))
    total_chars = len(re.sub(r"\s", "", text)) or 1
    return korean_chars / total_chars


def score_json_response(task_key: str, response_text: str) -> float:
    """0-100: JSON parses (40) + required keys present (40, split evenly) +
    non-empty values (20)."""
    required = _JSON_REQUIRED_KEYS.get(task_key)
    parsed = _extract_json(response_text)
    if parsed is None:
        return 0.0
    if required is None:
        # keyword_extraction: just needs to be a non-empty JSON array of strings
        if isinstance(parsed, list) and 3 <= len(parsed) <= 15 and all(isinstance(x, str) for x in parsed):
            return 100.0
        return 30.0 if isinstance(parsed, list) and parsed else 10.0

    if not isinstance(parsed, dict):
        return 10.0
    score = 40.0
    present = [k for k in required if k in parsed]
    score += 40.0 * (len(present) / len(required))
    non_empty = [k for k in present if parsed.get(k) not in (None, "", [])]
    score += 20.0 * (len(non_empty) / len(required)) if required else 0.0
    return round(min(100.0, score), 1)


def score_reasoning_response(response_text: str) -> float:
    """0-100 heuristic for the open-ended reasoning task: rewards a
    substantive, structured answer over an empty/degenerate one."""
    text = (response_text or "").strip()
    if not text:
        return 0.0
    length_score = min(60.0, len(text) / 8)  # up to 60 pts for ~480+ chars
    signal_terms = ["센서", "데이터", "환경", "장비", "온도", "습도", "sensor", "data", "환경", "공정", "gap", "domain"]
    signal_score = min(40.0, sum(8 for t in signal_terms if t in text.lower()))
    return round(min(100.0, length_score + signal_score), 1)


def score_technical_accuracy(task_key: str, response_text: str) -> float | None:
    """Proxy for 'did the model actually understand our schema', decidable
    without ground truth: for classification/battery-relevance/
    transferability, check whether the industry/technology/problem values
    it returned are real keys from this project's own taxonomy configs
    (config/industries.yaml etc.) rather than hallucinated categories."""
    from research_os.core.config import industries_config, problems_config, technologies_config

    parsed = _extract_json(response_text)
    if parsed is None or not isinstance(parsed, dict):
        return None

    valid_industries = {i["id"] for i in industries_config().get("industries", [])}
    valid_technologies = {t["id"] for t in technologies_config().get("technologies", [])}
    valid_problems = {p["id"] for p in problems_config().get("problems", [])}

    checks: list[bool] = []
    if task_key in ("classification",):
        if "industry" in parsed:
            checks.append(str(parsed["industry"]).lower().replace(" ", "_") in valid_industries)
        if "technology" in parsed:
            checks.append(str(parsed["technology"]).lower().replace(" ", "_") in valid_technologies)
        if "problem" in parsed:
            checks.append(str(parsed["problem"]).lower().replace(" ", "_") in valid_problems)
    elif task_key == "battery_relevance":
        score = parsed.get("score")
        checks.append(isinstance(score, (int, float)) and 0 <= score <= 5)
    elif task_key == "transferability":
        source_industry = parsed.get("source_industry")
        transfer_score = parsed.get("transfer_score")
        if source_industry is not None:
            checks.append(str(source_industry).lower().replace(" ", "_") in valid_industries)
        checks.append(isinstance(transfer_score, (int, float)) and 0 <= transfer_score <= 100)
    else:
        return None

    if not checks:
        return None
    return round(100.0 * sum(checks) / len(checks), 1)


def score_korean_quality(task_key: str, response_text: str) -> float | None:
    if task_key != "korean_summary":
        return None
    ratio = _korean_ratio(response_text)
    return round(min(100.0, ratio * 130), 1)  # >=77% Korean chars -> 100


def latency_score(latency_ms: float | None) -> float | None:
    if latency_ms is None:
        return None
    # 100 at <=1000ms, linearly down to 0 at >=20000ms (20s) — generous for
    # a 3-8B local model on modest hardware; tune once real numbers exist.
    if latency_ms <= 1000:
        return 100.0
    return round(max(0.0, 100.0 - (latency_ms - 1000) / 190.0), 1)


def resource_efficiency_score(ram_mb: float | None, vram_mb: float | None, disk_mb: float | None) -> float | None:
    if vram_mb is not None:
        return round(max(0.0, min(100.0, 100.0 - (vram_mb / 8192.0) * 100.0)), 1)
    if ram_mb is not None:
        return round(max(0.0, min(100.0, 100.0 - (ram_mb / 16384.0) * 100.0)), 1)
    if disk_mb is not None:
        return round(max(0.0, min(100.0, 100.0 - (disk_mb / 8192.0) * 100.0)), 1)
    return None


def stability_score(success_count: int, total_count: int) -> float | None:
    if total_count == 0:
        return None
    return round(100.0 * success_count / total_count, 1)


@dataclass
class CompositeInputs:
    quality: float | None = None
    technical_accuracy: float | None = None
    korean_quality: float | None = None
    latency: float | None = None
    resource_efficiency: float | None = None
    stability: float | None = None


def composite_score(inputs: CompositeInputs) -> float | None:
    """Weighted sum over whatever components were actually measured,
    re-normalizing the weights over the available ones — a model never
    evaluated on the Korean task shouldn't be penalized as if it scored 0
    on it; it should simply not contribute that term."""
    components = {
        "quality": inputs.quality,
        "technical_accuracy": inputs.technical_accuracy,
        "korean_quality": inputs.korean_quality,
        "latency": inputs.latency,
        "resource_efficiency": inputs.resource_efficiency,
        "stability": inputs.stability,
    }
    available = {k: v for k, v in components.items() if v is not None}
    if not available:
        return None
    weight_sum = sum(WEIGHTS[k] for k in available)
    weighted = sum(WEIGHTS[k] * v for k, v in available.items())
    return round(weighted / weight_sum, 1)
