"""Shared types for model provider adapters."""
from __future__ import annotations

from dataclasses import dataclass, field


class ModelUnavailableError(Exception):
    """Raised by an adapter when its backend cannot serve a request right
    now (Ollama not running, no API key configured, network error, ...).
    The ModelGateway catches this and moves to the next fallback tier."""


@dataclass
class GenerationRequest:
    prompt: str
    system: str | None = None
    max_tokens: int = 1024
    temperature: float = 0.2
    metadata: dict = field(default_factory=dict)


@dataclass
class GenerationResult:
    text: str
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: float = 0.0


class ProviderAdapter:
    """Base interface every provider adapter implements."""

    name: str = "base"

    def is_available(self) -> bool:
        raise NotImplementedError

    def generate(self, request: GenerationRequest, model: str) -> GenerationResult:
        raise NotImplementedError
