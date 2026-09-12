"""OpenAI cloud adapter (spec section 8).

Implemented via a plain REST call (no SDK dependency) so it stays available
even though `openai` isn't in requirements.txt yet — add it if this
provider becomes the primary cloud path.
"""
from __future__ import annotations

import os
import time

import httpx

from research_os.core.logging_setup import get_logger
from research_os.models.base import GenerationRequest, GenerationResult, ModelUnavailableError, ProviderAdapter

logger = get_logger("models.openai")


class OpenAIAdapter(ProviderAdapter):
    name = "openai"

    def __init__(self, api_key: str | None = None, base_url: str = "https://api.openai.com/v1") -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.base_url = base_url.rstrip("/")

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate(self, request: GenerationRequest, model: str) -> GenerationResult:
        if not self.api_key:
            raise ModelUnavailableError("OPENAI_API_KEY not configured")

        messages = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages.append({"role": "user", "content": request.prompt})

        start = time.monotonic()
        try:
            resp = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                },
                timeout=60.0,
            )
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            raise ModelUnavailableError(f"OpenAI call failed ({model}): {exc}") from exc

        latency_ms = (time.monotonic() - start) * 1000
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return GenerationResult(
            text=text,
            provider=self.name,
            model=model,
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
            latency_ms=latency_ms,
        )
