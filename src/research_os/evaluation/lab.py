"""LLM Evaluation Lab (spec section 14).

Runs a small fixed sample of tasks (classification, summarization) against
every configured tier that is actually reachable right now, and writes
data/reports/model-benchmark.md. Tiers whose provider is unavailable
(Ollama not running, no API key) are skipped and reported as such rather
than failing the whole evaluation — consistent with the reliability rule.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from research_os.core.config import models_config
from research_os.core.logging_setup import get_logger
from research_os.database.db import session_scope
from research_os.database.models import ModelBenchmark
from research_os.models.base import GenerationRequest, ModelUnavailableError
from research_os.models.gateway import build_default_adapters

logger = get_logger("evaluation.lab")

_SAMPLE_TASKS = [
    {
        "task": "classification",
        "prompt": (
            "Classify this abstract's primary AI technology in one word: "
            "'We propose a transformer-based anomaly detection method for industrial "
            "time-series sensor data.'"
        ),
    },
    {
        "task": "korean_summarization",
        "prompt": (
            "다음 초록을 한국어로 2문장 요약하라: 'We propose a transformer-based anomaly "
            "detection method for industrial time-series sensor data, achieving 95% "
            "accuracy on a public benchmark.'"
        ),
    },
]

_ADAPTERS = build_default_adapters()


@dataclass
class BenchmarkRow:
    task: str
    provider: str
    model: str
    latency_ms: float | None
    output_tokens: int | None
    status: str
    error: str | None = None


def run_evaluation() -> list[BenchmarkRow]:
    tiers = models_config().get("tiers", {})
    rows: list[BenchmarkRow] = []

    for tier_name, tier_cfg in tiers.items():
        if tier_name in ("embedding", "reranker"):
            continue  # evaluated separately; not a generation task
        provider_name, model = tier_cfg["provider"], tier_cfg["model"]
        adapter = _ADAPTERS.get(provider_name)
        if adapter is None or not adapter.is_available():
            rows.append(
                BenchmarkRow(task="availability", provider=provider_name, model=model,
                             latency_ms=None, output_tokens=None, status="unavailable")
            )
            continue

        for sample in _SAMPLE_TASKS:
            start = time.monotonic()
            try:
                result = adapter.generate(GenerationRequest(prompt=sample["prompt"], max_tokens=200), model)
                latency_ms = (time.monotonic() - start) * 1000
                rows.append(
                    BenchmarkRow(task=sample["task"], provider=provider_name, model=model,
                                 latency_ms=latency_ms, output_tokens=result.output_tokens, status="ok")
                )
            except ModelUnavailableError as exc:
                rows.append(
                    BenchmarkRow(task=sample["task"], provider=provider_name, model=model,
                                 latency_ms=None, output_tokens=None, status="error", error=str(exc))
                )

    with session_scope() as session:
        for row in rows:
            if row.task == "availability":
                continue
            session.add(
                ModelBenchmark(
                    task=row.task, provider=row.provider, model=row.model,
                    latency_ms=row.latency_ms, token_usage=row.output_tokens,
                    failure_rate=0.0 if row.status == "ok" else 1.0,
                )
            )

    return rows


def render_report(rows: list[BenchmarkRow]) -> str:
    lines = ["# Model Benchmark Report", ""]
    lines.append("| Task | Provider | Model | Latency (ms) | Output Tokens | Status | Error |")
    lines.append("|---|---|---|---|---|---|---|")
    for row in rows:
        latency = f"{row.latency_ms:.0f}" if row.latency_ms is not None else "-"
        tokens = str(row.output_tokens) if row.output_tokens is not None else "-"
        error = row.error or ""
        lines.append(f"| {row.task} | {row.provider} | {row.model} | {latency} | {tokens} | {row.status} | {error} |")
    return "\n".join(lines) + "\n"
