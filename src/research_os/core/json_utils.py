"""Shared JSON extraction from LLM free-text responses.

Models don't always return pure JSON — there can be leading/trailing
prose, markdown code fences, or (for reasoning models) a preamble before
the answer. This scans for the first `{...}` or `[...]` span in the text
and returns the first one that actually parses as JSON. Used by every
agent that expects a JSON response (`agents/classifier.py`, `summarizer.py`,
`analyst.py`, `transfer.py`) and by the benchmark's scoring heuristics
(`evaluation/scoring.py`) — previously each reimplemented this themselves.
"""
from __future__ import annotations

import json
from typing import Any


def extract_json(text: str) -> Any | None:
    """Return the parsed JSON object/array found in `text`, or None if
    nothing in it parses as JSON."""
    start_obj, end_obj = text.find("{"), text.rfind("}")
    start_arr, end_arr = text.find("["), text.rfind("]")
    candidates = []
    if start_obj != -1 and end_obj != -1:
        candidates.append(text[start_obj : end_obj + 1])
    if start_arr != -1 and end_arr != -1:
        candidates.append(text[start_arr : end_arr + 1])
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None
