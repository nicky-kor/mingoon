"""QAAgent: grounding check over what the other LLM-backed agents produced
for a document, run right before it's marked analyzed (spec section 21 —
never store inference as fact; spec section 44 — one document's problem
must never stop the batch).

Deliberately heuristic/deterministic only, with no ModelGateway/LLM call
of its own (same reasoning as TrendAgent, agents/trend.py): the thing
being verified here is "did an LLM invent something", so verifying it
with another LLM call would trade one hallucination-prone step for two,
at double the cost, without a stronger guarantee. A regex-level check for
percentage-style statistics that appear in the generated fields but
nowhere in the document's own source text catches the single most common
and most consequential failure mode — a fabricated number — cheaply and
reproducibly. Deliberately scoped to percentages, not bare numbers: a
bare-digit match would flag years, counts, and other harmless numbers
constantly, drowning out the signal.

This flags, it never blocks: a flagged document still gets scored and
stored like any other. `qa_status`/`qa_flags` exist so a human (or the
daily/weekly briefing) can spot-check the documents most likely to
contain an overclaim, not to gate the pipeline on a heuristic that will
always have false positives (a % figure can legitimately appear in a
HYPOTHESIS/INFERENCE sentence without being copied from the source).
"""
from __future__ import annotations

import re

from research_os.core.schema import ResearchItem

_PERCENTAGE_PATTERN = re.compile(r"\d+(?:\.\d+)?\s?%")


class QAAgent:
    def check(self, item: ResearchItem) -> dict:
        flags: list[str] = []

        source_numbers = self._numbers(f"{item.title} {item.abstract or ''}")
        generated_text = " ".join(
            filter(None, [item.summary, item.limitations, item.expected_benefit, item.risk, *(item.key_findings or [])])
        )
        unsupported = sorted(self._numbers(generated_text) - source_numbers)
        if unsupported:
            flags.append(f"percentage claim(s) not found in source text: {', '.join(unsupported)}")

        if item.summary is not None and not item.summary.strip():
            flags.append("summary field is present but empty")

        scores = [s for s in (item.evidence_score, item.practical_score, item.novelty_score) if s is not None]
        if len(scores) == 3 and len(set(scores)) == 1 and scores[0] in (0.0, 100.0):
            flags.append(f"evidence/practical/novelty scores are all identically {scores[0]:g} — likely a generic non-answer")

        return {
            "qa_status": "flagged" if flags else "passed",
            "qa_flags": flags,
        }

    @staticmethod
    def _numbers(text: str) -> set[str]:
        return {m.group(0).replace(" ", "") for m in _PERCENTAGE_PATTERN.finditer(text or "")}
