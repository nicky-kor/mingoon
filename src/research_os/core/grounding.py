"""Shared percentage-claim grounding check (spec section 21/44).

Used two ways: by `agents/qa.py` (a full check run after the fact, over
whatever tier actually answered) and by `models/cascade.py` (a lightweight
pre-check on a cheap local answer, deciding whether it's trustworthy
enough to skip paying for a cloud call). Both are asking the same
question — "does this percentage actually appear in the source text" —
so the matching logic is factored out here once instead of drifting
apart across two call sites.
"""
from __future__ import annotations

import re

_PERCENTAGE_PATTERN = re.compile(r"\d+(?:\.\d+)?\s?%")


def percentages_in(text: str) -> set[str]:
    return {m.group(0).replace(" ", "") for m in _PERCENTAGE_PATTERN.finditer(text or "")}


def unsupported_percentages(generated_text: str, source_text: str) -> list[str]:
    """Percentage figures present in `generated_text` that don't appear
    anywhere in `source_text` — sorted for stable, testable output."""
    return sorted(percentages_in(generated_text) - percentages_in(source_text))
