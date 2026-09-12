"""Google Gemini cloud adapter (spec section 8), via plain REST call."""
from __future__ import annotations

import os
import time

import httpx

from research_os.core.logging_setup import get_logger
from research_os.models.base import GenerationRequest, GenerationResult, ModelUnavailableError, ProviderAdapter

logger = get_logger("models.google")


class GoogleAdapter(ProviderAdapter):
    name = "google"

    def __init__(self, api_key: str | None = None, base_url: str = "https://generativelanguage.googleapis.com/v1beta") -> None:
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self.base_url = base_url.rstrip("/")

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate(self, request: GenerationRequest, model: str) -> GenerationResult:
        if not self.api_key:
            raise ModelUnavailableError("GOOGLE_API_KEY not configured")

        prompt = f"{request.system}\n\n{request.prompt}" if request.system else request.prompt
        start = time.monotonic()
        try:
            resp = httpx.post(
                f"{self.base_url}/models/{model}:generateContent",
                params={"key": self.api_key},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "maxOutputTokens": request.max_tokens,
                        "temperature": request.temperature,
                    },
                },
                timeout=60.0,
            )
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            raise ModelUnavailableError(f"Google call failed ({model}): {exc}") from exc

        latency_ms = (time.monotonic() - start) * 1000
        data = resp.json()
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            raise ModelUnavailableError(f"Google response malformed: {exc}") from exc
        usage = data.get("usageMetadata", {})
        return GenerationResult(
            text=text,
            provider=self.name,
            model=model,
            input_tokens=usage.get("promptTokenCount"),
            output_tokens=usage.get("candidatesTokenCount"),
            latency_ms=latency_ms,
        )
