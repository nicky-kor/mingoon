"""Anthropic cloud adapter (spec section 8)."""
from __future__ import annotations

import os
import time

from research_os.core.logging_setup import get_logger
from research_os.models.base import GenerationRequest, GenerationResult, ModelUnavailableError, ProviderAdapter

logger = get_logger("models.anthropic")


class AnthropicAdapter(ProviderAdapter):
    name = "anthropic"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate(self, request: GenerationRequest, model: str) -> GenerationResult:
        if not self.api_key:
            raise ModelUnavailableError("ANTHROPIC_API_KEY not configured")

        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover
            raise ModelUnavailableError(f"anthropic package not installed: {exc}") from exc

        client = anthropic.Anthropic(api_key=self.api_key)
        start = time.monotonic()
        try:
            message = client.messages.create(
                model=model,
                max_tokens=request.max_tokens,
                system=request.system or "",
                messages=[{"role": "user", "content": request.prompt}],
                temperature=request.temperature,
            )
        except Exception as exc:  # noqa: BLE001
            raise ModelUnavailableError(f"Anthropic call failed ({model}): {exc}") from exc

        latency_ms = (time.monotonic() - start) * 1000
        text = "".join(block.text for block in message.content if getattr(block, "type", "") == "text")
        return GenerationResult(
            text=text,
            provider=self.name,
            model=model,
            input_tokens=getattr(message.usage, "input_tokens", None),
            output_tokens=getattr(message.usage, "output_tokens", None),
            latency_ms=latency_ms,
        )
