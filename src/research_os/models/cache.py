"""LLM response cache (spec section 15): never repeat an identical call.

Keyed on (provider, model, system, prompt, max_tokens, temperature) via a
sha256 hash. Backed by the `llm_cache` table so it survives across runs,
not just within one process.
"""
from __future__ import annotations

import hashlib

from sqlalchemy import select

from research_os.database.db import session_scope
from research_os.database.models import LLMCache
from research_os.models.base import GenerationRequest, GenerationResult


def compute_cache_key(provider: str, model: str, request: GenerationRequest) -> str:
    basis = "|".join(
        [
            provider,
            model,
            request.system or "",
            request.prompt,
            str(request.max_tokens),
            str(request.temperature),
        ]
    )
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


def get_cached(cache_key: str) -> GenerationResult | None:
    with session_scope() as session:
        row = session.scalars(select(LLMCache).where(LLMCache.cache_key == cache_key)).first()
        if row is None:
            return None
        return GenerationResult(
            text=row.response_text,
            provider=row.provider,
            model=row.model,
            input_tokens=row.input_tokens,
            output_tokens=row.output_tokens,
            latency_ms=0.0,
        )


def store_cached(cache_key: str, result: GenerationResult) -> None:
    with session_scope() as session:
        existing = session.scalars(select(LLMCache).where(LLMCache.cache_key == cache_key)).first()
        if existing is not None:
            return  # another call already cached this exact request
        session.add(
            LLMCache(
                cache_key=cache_key,
                provider=result.provider,
                model=result.model,
                response_text=result.text,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
            )
        )
