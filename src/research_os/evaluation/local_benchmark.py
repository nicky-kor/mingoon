"""Local LLM Benchmark (spec: "LOCAL LLM SETUP + BENCHMARK TASK").

Discovers whatever Ollama models are actually installed on this machine
(`OllamaAdapter.list_models()` — never assumes a model name), runs the 6
fixed benchmark-prompt tasks from `evaluation/prompts.py` against each one
using the fixed dataset in `evaluation/dataset.py`, scores the responses
with the heuristics in `evaluation/scoring.py`, and recommends a
local_fast/local_standard/local_reasoning assignment from the actual
results.

If Ollama isn't running, or no models are installed, this returns a
result with `ollama_available=False` / an empty model list — it does not
fabricate placeholder numbers. `research-os evaluate` reports that plainly
as BLOCKED rather than claiming a role was selected.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

from research_os.core import env_info
from research_os.core.logging_setup import get_logger
from research_os.core.resource_probe import gpu_vram_usage_mb, process_ram_mb
from research_os.database.db import session_scope
from research_os.database.models import ModelBenchmark
from research_os.evaluation import dataset as ds
from research_os.evaluation import scoring
from research_os.evaluation.prompts import TASK_KEYS, build_prompt
from research_os.models.base import GenerationRequest, ModelUnavailableError
from research_os.models.local import OllamaAdapter

logger = get_logger("evaluation.local_benchmark")

# task_key -> representative dataset case id (spec section 8's 6 prompt
# tasks are evaluated against one matching dataset case each, keeping one
# full benchmark pass to 6 calls/model instead of 6x10).
_TASK_CASE = {
    "classification": "industrial-ai-classification",
    "korean_summary": "korean-technical-summary",
    "keyword_extraction": "keyword-extraction",
    "battery_relevance": "battery-relevance-evaluation",
    "transferability": "cross-industry-transfer-reasoning",
    "reasoning": "research-question-generation",  # any case; reasoning prompt is fixed-text
}


@dataclass
class TaskRunResult:
    task: str
    category: str
    success: bool
    latency_ms: float | None
    output_tokens: int | None
    quality: float | None
    technical_accuracy: float | None
    korean_quality: float | None
    error: str | None = None


@dataclass
class ModelRunResult:
    model: str
    provider: str = "ollama"
    disk_size_mb: float | None = None
    task_results: list[TaskRunResult] = field(default_factory=list)
    ram_usage_mb: float | None = None
    vram_usage_mb: float | None = None

    @property
    def avg_quality(self) -> float | None:
        vals = [t.quality for t in self.task_results if t.quality is not None]
        return round(sum(vals) / len(vals), 1) if vals else None

    @property
    def avg_technical_accuracy(self) -> float | None:
        vals = [t.technical_accuracy for t in self.task_results if t.technical_accuracy is not None]
        return round(sum(vals) / len(vals), 1) if vals else None

    @property
    def korean_quality(self) -> float | None:
        vals = [t.korean_quality for t in self.task_results if t.korean_quality is not None]
        return round(sum(vals) / len(vals), 1) if vals else None

    @property
    def avg_latency_ms(self) -> float | None:
        vals = [t.latency_ms for t in self.task_results if t.latency_ms is not None]
        return round(sum(vals) / len(vals), 1) if vals else None

    @property
    def stability(self) -> float | None:
        return scoring.stability_score(sum(1 for t in self.task_results if t.success), len(self.task_results))

    @property
    def composite(self) -> float | None:
        inputs = scoring.CompositeInputs(
            quality=self.avg_quality,
            technical_accuracy=self.avg_technical_accuracy,
            korean_quality=self.korean_quality,
            latency=scoring.latency_score(self.avg_latency_ms),
            resource_efficiency=scoring.resource_efficiency_score(self.ram_usage_mb, self.vram_usage_mb, self.disk_size_mb),
            stability=self.stability,
        )
        return scoring.composite_score(inputs)

    # task-family scores used for role recommendation (spec section 11)
    @property
    def fast_task_score(self) -> float | None:
        vals = [t.quality for t in self.task_results if t.task in ("classification", "keyword_extraction") and t.quality is not None]
        return round(sum(vals) / len(vals), 1) if vals else None

    @property
    def reasoning_task_score(self) -> float | None:
        vals = [
            t.quality for t in self.task_results
            if t.task in ("battery_relevance", "transferability", "reasoning") and t.quality is not None
        ]
        return round(sum(vals) / len(vals), 1) if vals else None


@dataclass
class LocalBenchmarkResult:
    generated_at: str
    hardware: dict
    ollama_available: bool
    ollama_version: str | None
    models: list[ModelRunResult]
    role_selection: dict
    limitations: list[str]


@dataclass
class _RoleCandidate:
    """Just enough of a model's benchmark results to pick role winners —
    normalizes over the two shapes this comes from: a fresh in-memory
    `ModelRunResult` (this run) or a persisted `ModelBenchmark` DB row
    (a past run), so the selection formula lives in exactly one place."""

    model: str
    fast_task_score: float | None
    quality: float | None
    reasoning_task_score: float | None
    latency_ms: float | None


def _empty_role_selection() -> dict:
    return {"local_fast": None, "local_standard": None, "local_reasoning": None}


def _best_by(candidates: list[_RoleCandidate], key_fn) -> str | None:
    scored = [(c, key_fn(c)) for c in candidates]
    scored = [(c, s) for c, s in scored if s is not None]
    return max(scored, key=lambda pair: pair[1])[0].model if scored else None


def _select_role_winners(candidates: list[_RoleCandidate]) -> dict:
    if not candidates:
        return _empty_role_selection()
    return {
        "local_fast": _best_by(candidates, lambda c: (
            (c.fast_task_score or 0) * 0.5 + (scoring.latency_score(c.latency_ms) or 0) * 0.5
        )),
        "local_standard": _best_by(candidates, lambda c: c.quality),
        "local_reasoning": _best_by(candidates, lambda c: c.reasoning_task_score),
    }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _blocked_result(hardware: dict, ollama_available: bool, ollama_version: str | None, limitation: str) -> LocalBenchmarkResult:
    """A result for the two "couldn't even start" cases (Ollama unreachable,
    or reachable but no models installed) — no model was executed, so
    role selection is honestly empty rather than fabricated."""
    return LocalBenchmarkResult(
        generated_at=_now_iso(), hardware=hardware, ollama_available=ollama_available,
        ollama_version=ollama_version, models=[], role_selection=_empty_role_selection(),
        limitations=[limitation],
    )


# Reasoning-oriented models (e.g. DeepSeek-R1) emit a long internal
# "thinking" trace before the actual answer — a tight max_tokens budget
# cuts that off before the model ever reaches its answer, and a short
# HTTP timeout can abort the call outright, which looks like the model
# failing when it's really the benchmark being unfair to a verbose model.
# Same budget/timeout for every model (fairness), just generous enough
# that a thinking-model's answer isn't truncated away.
_BENCHMARK_MAX_TOKENS = 1500
_BENCHMARK_TIMEOUT_SECONDS = 180.0


def _run_one(adapter: OllamaAdapter, model: str, task_key: str) -> TaskRunResult:
    case = ds.get_case(_TASK_CASE[task_key])
    category = case.category if case else task_key
    prompt = build_prompt(task_key, case)
    request = GenerationRequest(prompt=prompt, max_tokens=_BENCHMARK_MAX_TOKENS, temperature=0.2)

    start = time.monotonic()
    try:
        result = adapter.generate(request, model)
    except ModelUnavailableError as exc:
        return TaskRunResult(
            task=task_key, category=category, success=False,
            latency_ms=(time.monotonic() - start) * 1000, output_tokens=None,
            quality=None, technical_accuracy=None, korean_quality=None, error=str(exc),
        )

    answer_text = scoring.strip_reasoning_preamble(result.text)

    if task_key == "reasoning":
        quality = scoring.score_reasoning_response(answer_text)
    else:
        quality = scoring.score_json_response(task_key, answer_text)
    technical_accuracy = scoring.score_technical_accuracy(task_key, answer_text)
    korean_quality = scoring.score_korean_quality(task_key, answer_text)

    return TaskRunResult(
        task=task_key, category=category, success=True, latency_ms=result.latency_ms,
        output_tokens=result.output_tokens, quality=quality,
        technical_accuracy=technical_accuracy, korean_quality=korean_quality,
    )


def run_local_benchmark(ollama_base_url: str | None = None) -> LocalBenchmarkResult:
    adapter = (
        OllamaAdapter(base_url=ollama_base_url, timeout=_BENCHMARK_TIMEOUT_SECONDS)
        if ollama_base_url
        else OllamaAdapter(timeout=_BENCHMARK_TIMEOUT_SECONDS)
    )
    limitations: list[str] = []
    hardware = env_info.summary()

    if not adapter.is_available():
        return _blocked_result(
            hardware, False, None,
            "Ollama is not reachable at " + adapter.base_url + " — install it and run "
            "`ollama pull <model>` for at least one candidate before benchmarking "
            "(see docs/local-llm.md). No local model was executed; role selection is BLOCKED.",
        )

    installed = adapter.list_models()
    if not installed:
        return _blocked_result(
            hardware, True, adapter.get_version(),
            "Ollama is running but no models are installed (`ollama list` is empty). "
            "Pull at least one small candidate (e.g. `ollama pull qwen2.5:3b-instruct`) "
            "and re-run `research-os evaluate`.",
        )

    ram_before = process_ram_mb("ollama")
    model_results: list[ModelRunResult] = []
    for entry in installed:
        model_name = entry.get("name") or entry.get("model")
        disk_size_mb = round(entry["size"] / (1024 * 1024), 1) if entry.get("size") else None
        run = ModelRunResult(model=model_name, disk_size_mb=disk_size_mb)
        for task_key in TASK_KEYS:
            task_result = _run_one(adapter, model_name, task_key)
            run.task_results.append(task_result)
            if not task_result.success:
                logger.warning("local benchmark: model=%s task=%s failed: %s", model_name, task_key, task_result.error)
        run.ram_usage_mb = process_ram_mb("ollama")
        run.vram_usage_mb = gpu_vram_usage_mb()
        if run.ram_usage_mb is None and ram_before is None:
            limitations.append(f"RAM usage for {model_name} could not be measured on this OS/toolchain.")
        if run.vram_usage_mb is None:
            limitations.append(f"VRAM usage for {model_name} could not be measured (no nvidia-smi/rocm-smi found).")
        model_results.append(run)

    _persist(model_results)
    role_selection = _select_roles(model_results)

    return LocalBenchmarkResult(
        generated_at=_now_iso(),
        hardware=hardware, ollama_available=True, ollama_version=adapter.get_version(),
        models=model_results, role_selection=role_selection,
        limitations=sorted(set(limitations)),
    )


def _persist(model_results: list[ModelRunResult]) -> None:
    with session_scope() as session:
        for run in model_results:
            for t in run.task_results:
                session.add(
                    ModelBenchmark(
                        task=t.task, category=t.category, provider=run.provider, model=run.model,
                        quality_score=t.quality, technical_accuracy_score=t.technical_accuracy,
                        korean_quality_score=t.korean_quality, latency_ms=t.latency_ms,
                        token_usage=t.output_tokens, success=t.success,
                        failure_rate=0.0 if t.success else 1.0,
                    )
                )
            session.add(
                ModelBenchmark(
                    task="__aggregate__", provider=run.provider, model=run.model,
                    quality_score=run.avg_quality, technical_accuracy_score=run.avg_technical_accuracy,
                    korean_quality_score=run.korean_quality, resource_efficiency_score=scoring.resource_efficiency_score(
                        run.ram_usage_mb, run.vram_usage_mb, run.disk_size_mb,
                    ),
                    stability_score=run.stability, composite_score=run.composite,
                    latency_ms=run.avg_latency_ms, ram_usage_mb=run.ram_usage_mb,
                    vram_usage_mb=run.vram_usage_mb, disk_size_mb=run.disk_size_mb,
                    fast_task_score=run.fast_task_score, reasoning_task_score=run.reasoning_task_score,
                    success=run.stability is not None and run.stability > 0,
                )
            )


def derive_role_selection_from_db(session) -> dict:
    """Re-derive local_fast/local_standard/local_reasoning from the most
    recent `__aggregate__` ModelBenchmark row per model — lets
    `research-os benchmark-apply` run independently of `evaluate`, against
    whatever was last actually measured."""
    from sqlalchemy import select

    from research_os.database.models import ModelBenchmark

    rows = session.scalars(
        select(ModelBenchmark).where(ModelBenchmark.task == "__aggregate__").order_by(ModelBenchmark.timestamp.desc())
    ).all()
    latest_per_model: dict[str, ModelBenchmark] = {}
    for row in rows:
        latest_per_model.setdefault(row.model, row)  # first hit per model = most recent, due to desc order

    candidates = [
        _RoleCandidate(row.model, row.fast_task_score, row.quality_score, row.reasoning_task_score, row.latency_ms)
        for row in latest_per_model.values()
    ]
    return _select_role_winners(candidates)


def _select_roles(model_results: list[ModelRunResult]) -> dict:
    candidates = [
        _RoleCandidate(m.model, m.fast_task_score, m.avg_quality, m.reasoning_task_score, m.avg_latency_ms)
        for m in model_results
    ]
    return _select_role_winners(candidates)


def render_report(result: LocalBenchmarkResult) -> str:
    """Renders the exact report structure from the build spec."""
    lines = ["# Local LLM Benchmark", "", f"_Generated: {result.generated_at}_", ""]

    lines += ["## Hardware", ""]
    hw = result.hardware
    lines += [
        f"- OS: {hw.get('os')}",
        f"- CPU: {hw.get('cpu')}",
        f"- RAM: {hw.get('ram_gb')} GB" if hw.get("ram_gb") else "- RAM: unknown",
        f"- GPU: {hw.get('gpu')}",
        f"- Ollama installed: {'yes' if result.ollama_available else 'NO — see Limitations'}",
        f"- Ollama version: {result.ollama_version or 'UNKNOWN'}",
        "",
    ]

    lines += ["## Models Tested", ""]
    if result.models:
        for m in result.models:
            size_str = f"{m.disk_size_mb:.0f} MB" if m.disk_size_mb else "unknown"
            lines.append(f"- `{m.model}` (provider: {m.provider}, size on disk: {size_str})")
    else:
        lines.append("- None — see Limitations below.")
    lines.append("")

    lines += ["## Benchmark Tasks", ""]
    lines += [f"{i}. {key}" for i, key in enumerate(TASK_KEYS, start=1)]
    lines.append("")
    lines += [
        "Scoring is automated/heuristic (JSON schema validity, taxonomy-key correctness, "
        "Korean character ratio, response length/structure for open reasoning) — not "
        "human-graded. See `research_os/evaluation/scoring.py`.",
        "",
    ]

    lines += ["## Results", ""]
    lines.append("| Model | Role Candidate | Quality | Korean | Latency | Resource | Stability | Score |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for m in result.models:
        role_hints = [role for role, model in result.role_selection.items() if model == m.model]
        role_str = ", ".join(role_hints) if role_hints else "-"

        def fmt(v, suffix=""):
            return f"{v:.0f}{suffix}" if v is not None else "UNKNOWN"

        lines.append(
            f"| {m.model} | {role_str} | {fmt(m.avg_quality)} | {fmt(m.korean_quality)} | "
            f"{fmt(m.avg_latency_ms, 'ms')} | {fmt(scoring.resource_efficiency_score(m.ram_usage_mb, m.vram_usage_mb, m.disk_size_mb))} | "
            f"{fmt(m.stability)} | {fmt(m.composite)} |"
        )
    if not result.models:
        lines.append("| (none tested) | - | - | - | - | - | - | - |")
    lines.append("")

    for role in ("local_fast", "local_standard", "local_reasoning"):
        lines.append(f"## Best Model for {role}")
        lines.append("")
        selected = result.role_selection.get(role)
        lines.append(f"- **{selected}**" if selected else "- UNKNOWN / BLOCKED — no model was actually benchmarked for this role.")
        lines.append("")

    lines += ["## Recommended Configuration", ""]
    if any(result.role_selection.values()):
        lines.append("Run `research-os benchmark-apply` to write these selections into `config/models.yaml` "
                      "(it edits the tier `model:` lines in place; nothing is changed automatically).")
        for role, model in result.role_selection.items():
            lines.append(f"- {role}: {model or 'UNKNOWN'}")
    else:
        lines.append("No local model was benchmarked, so no configuration change is recommended yet. "
                      "`config/models.yaml` is left as-is.")
    lines.append("")

    lines += ["## Limitations", ""]
    if result.limitations:
        lines += [f"- {item}" for item in result.limitations]
    else:
        lines.append("- None recorded for this run.")
    lines.append("")

    lines += ["## Next Benchmark", ""]
    lines += [
        "- Re-run after pulling additional candidates (e.g. a 7-8B general model and a "
        "reasoning-oriented model) once disk/VRAM budget allows.",
        "- Add an embedding-model benchmark once Research OS uses embeddings for search "
        "(Phase 3).",
        "- Re-run `research-os evaluate` periodically as Ollama model versions update — "
        "scores are not assumed to be stable over time.",
    ]

    return "\n".join(lines) + "\n"
