"""Local inference adapter (spec section 9/13).

Currently targets Ollama's HTTP API. llama.cpp / vLLM are noted as future
backends behind the same ProviderAdapter interface (spec section 5) — not
implemented yet to avoid overengineering ahead of need (spec section 61).
"""
from __future__ import annotations

import time

import httpx

from research_os.core.logging_setup import get_logger
from research_os.models.base import GenerationRequest, GenerationResult, ModelUnavailableError, ProviderAdapter

logger = get_logger("models.local")


class OllamaAdapter(ProviderAdapter):
    name = "ollama"

    def __init__(self, base_url: str = "http://localhost:11434", timeout: float = 60.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def is_available(self) -> bool:
        try:
            resp = httpx.get(f"{self.base_url}/api/tags", timeout=3.0)
            return resp.status_code == 200
        except Exception:  # noqa: BLE001
            return False

    def generate(self, request: GenerationRequest, model: str) -> GenerationResult:
        payload = {
            "model": model,
            "prompt": request.prompt,
            "system": request.system or "",
            "stream": False,
            "options": {"temperature": request.temperature, "num_predict": request.max_tokens},
        }
        start = time.monotonic()
        try:
            resp = httpx.post(f"{self.base_url}/api/generate", json=payload, timeout=self.timeout)
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            raise ModelUnavailableError(f"Ollama unavailable ({model}): {exc}") from exc

        latency_ms = (time.monotonic() - start) * 1000
        data = resp.json()
        return GenerationResult(
            text=data.get("response", ""),
            provider=self.name,
            model=model,
            input_tokens=data.get("prompt_eval_count"),
            output_tokens=data.get("eval_count"),
            latency_ms=latency_ms,
        )
