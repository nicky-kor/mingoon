"""ModelGateway: the only door agents use to reach an LLM (spec section 8).

Agent -> ModelGateway -> ModelRouter -> ProviderAdapter

Handles the Local -> Fallback -> Cloud chain (spec section 13) and logs
every attempt to `llm_runs` for observability/cost tracking (spec section
43). No agent ever imports a provider adapter directly.
"""
from __future__ import annotations

import time

from research_os.core.logging_setup import get_logger
from research_os.core.resource_probe import gpu_vram_usage_mb, process_ram_mb
from research_os.database.db import session_scope
from research_os.database.models import LLMRun
from research_os.models.anthropic import AnthropicAdapter
from research_os.models.base import GenerationRequest, GenerationResult, ModelUnavailableError, ProviderAdapter
from research_os.models.cache import compute_cache_key, get_cached, store_cached
from research_os.models.google import GoogleAdapter
from research_os.models.local import OllamaAdapter
from research_os.models.openai import OpenAIAdapter
from research_os.models.router import ModelRouter

logger = get_logger("models.gateway")


class AllProvidersUnavailableError(Exception):
    pass


def build_default_adapters() -> dict[str, ProviderAdapter]:
    """The provider registry every part of the app shares — built once
    here so ModelGateway, the evaluation lab, and the CLI's `models`
    command never duplicate (or drift out of sync on) which providers
    exist. Adapter construction is cheap (no network calls), so building
    all four eagerly costs nothing even where only one ends up used."""
    return {
        "ollama": OllamaAdapter(),
        "anthropic": AnthropicAdapter(),
        "openai": OpenAIAdapter(),
        "google": GoogleAdapter(),
    }


class ModelGateway:
    def __init__(self, router: ModelRouter | None = None, log_runs: bool = True) -> None:
        self.router = router or ModelRouter()
        self.log_runs = log_runs
        self._adapters: dict[str, ProviderAdapter] = build_default_adapters()

    def register_adapter(self, name: str, adapter: ProviderAdapter) -> None:
        self._adapters[name] = adapter

    def _log(
        self, agent, task, tier, model, provider, latency_ms, result, status, error,
        ram_mb=None, vram_mb=None, cache_hit=False,
    ) -> None:
        if not self.log_runs:
            return
        try:
            with session_scope() as session:
                session.add(
                    LLMRun(
                        agent=agent,
                        task=task,
                        tier=tier,
                        model=model,
                        provider=provider,
                        latency_ms=latency_ms,
                        input_tokens=result.input_tokens if result else None,
                        output_tokens=result.output_tokens if result else None,
                        status=status,
                        error=error,
                        ram_usage_mb=ram_mb,
                        vram_usage_mb=vram_mb,
                        cache_hit=cache_hit,
                    )
                )
        except Exception as exc:  # noqa: BLE001 - logging must never break the pipeline
            logger.warning("failed to log llm_run: %s", exc)

    def generate(
        self,
        prompt: str,
        agent: str | None = None,
        task_type: str | None = None,
        system: str | None = None,
        complexity: str | None = None,
        importance: int = 50,
        latency_budget: str | None = None,
        cost_budget: str | None = None,
        privacy_level: str = "public",
        max_tokens: int = 1024,
        temperature: float = 0.2,
        reasoning_required: bool = False,
        use_cache: bool = True,
        measure_resources: bool = False,
    ) -> GenerationResult:
        decision = self.router.route(
            task_type=task_type,
            complexity=complexity,
            importance=importance,
            latency_budget=latency_budget,
            cost_budget=cost_budget,
            privacy_level=privacy_level,
            agent=agent,
            reasoning_required=reasoning_required,
        )

        chain = [decision.tier] + self.router.fallback_chain(decision.tier)
        request = GenerationRequest(prompt=prompt, system=system, max_tokens=max_tokens, temperature=temperature)

        last_error: Exception | None = None
        for tier in chain:
            try:
                provider_name, model_name = self.router.resolve_tier(tier)
            except KeyError as exc:
                last_error = exc
                continue

            adapter = self._adapters.get(provider_name)
            if adapter is None:
                last_error = ModelUnavailableError(f"No adapter registered for provider {provider_name}")
                continue

            cache_key = compute_cache_key(provider_name, model_name, request) if use_cache else None
            if cache_key is not None:
                cached = get_cached(cache_key)
                if cached is not None:
                    self._log(agent, task_type, tier, model_name, provider_name, 0.0, cached, "cache_hit", None, cache_hit=True)
                    return cached

            ram_before = process_ram_mb(provider_name) if measure_resources else None
            start = time.monotonic()
            try:
                result = adapter.generate(request, model_name)
            except ModelUnavailableError as exc:
                latency_ms = (time.monotonic() - start) * 1000
                logger.warning("tier=%s provider=%s model=%s unavailable: %s", tier, provider_name, model_name, exc)
                self._log(agent, task_type, tier, model_name, provider_name, latency_ms, None, "fallback", str(exc))
                last_error = exc
                continue

            ram_mb = process_ram_mb(provider_name) if measure_resources else None
            vram_mb = gpu_vram_usage_mb() if measure_resources else None
            if ram_before is not None and ram_mb is not None:
                ram_mb = max(ram_mb, ram_before)  # report peak, not the (possibly lower) post-call sample

            if cache_key is not None:
                store_cached(cache_key, result)

            self._log(
                agent, task_type, tier, model_name, provider_name, result.latency_ms, result, "ok", None,
                ram_mb=ram_mb, vram_mb=vram_mb,
            )
            return result

        error_msg = f"All model tiers exhausted for chain={chain}: {last_error}"
        logger.error(error_msg)
        raise AllProvidersUnavailableError(error_msg)
