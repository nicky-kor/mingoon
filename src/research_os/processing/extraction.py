"""Structured field extraction fallback (spec section 31: problem/method/
result/limitation/application), used when no LLM is available.

This is a lightweight heuristic (first-sentence splitting + keyword cues),
not a substitute for LLM-based extraction — `agents/summarizer.py` prefers
the LLM path and only falls back to this.
"""
from __future__ import annotations

import re


def split_sentences(text: str) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


_CUES = {
    "method": ["propose", "present", "introduce", "develop", "method", "approach", "framework"],
    "result": ["result", "achieve", "outperform", "improve", "accuracy", "demonstrate", "show that"],
    "limitation": ["however", "limitation", "limited", "future work", "remains a challenge"],
    "application": ["applied to", "application", "used in", "deploy", "real-world"],
}


def extract_structured(abstract: str | None) -> dict[str, str | None]:
    sentences = split_sentences(abstract or "")
    if not sentences:
        return {"problem": None, "method": None, "result": None, "limitation": None, "application": None}

    fields: dict[str, str | None] = {"problem": sentences[0]}
    remaining = sentences[1:] if len(sentences) > 1 else sentences

    for field, cues in _CUES.items():
        match = next(
            (s for s in remaining if any(cue in s.lower() for cue in cues)),
            None,
        )
        fields[field] = match

    return fields


def heuristic_summary(title: str, abstract: str | None, max_sentences: int = 2) -> str:
    sentences = split_sentences(abstract or "")
    if not sentences:
        return title
    return " ".join(sentences[:max_sentences])
