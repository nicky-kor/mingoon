"""TrendAgent (spec section 34): recurring/emerging technologies over recent
documents. Operates on already-stored documents rather than a single item.

Deliberately has no ModelGateway/LLM tier of its own (there's no entry for
it in config/routing.yaml's agent_defaults): what it reports are counts and
period-over-period deltas straight out of the database, and an LLM would
add cost/latency without making those numbers any more trustworthy.
"""
from __future__ import annotations

from collections import Counter
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from research_os.core.timeutils import utc_now
from research_os.database.models import Document


class TrendAgent:
    def analyze(self, session: Session, window_days: int = 30) -> dict:
        now = utc_now()
        current_since = now - timedelta(days=window_days)
        previous_since = current_since - timedelta(days=window_days)

        current_docs = session.scalars(select(Document).where(Document.collected_at >= current_since)).all()
        previous_docs = session.scalars(
            select(Document).where(
                Document.collected_at >= previous_since,
                Document.collected_at < current_since,
            )
        ).all()

        tech_counter: Counter[str] = Counter(d.technology for d in current_docs if d.technology)
        problem_counter: Counter[str] = Counter(d.problem for d in current_docs if d.problem)
        industry_counter: Counter[str] = Counter(d.industry for d in current_docs if d.industry)
        previous_tech_counter: Counter[str] = Counter(d.technology for d in previous_docs if d.technology)

        rising, new = self._shifts(tech_counter, previous_tech_counter)

        return {
            "window_days": window_days,
            "documents_considered": len(current_docs),
            "top_technologies": tech_counter.most_common(10),
            "top_problems": problem_counter.most_common(10),
            "top_industries": industry_counter.most_common(10),
            # "Emerging" per spec section 34 means growing attention, not
            # just currently common — a technology mentioned 20 times both
            # this window and last is not emerging, and one mentioned only
            # once is not necessarily emerging either. Comparing against the
            # immediately preceding window of the same length is what
            # actually tells the two apart.
            "rising_technologies": rising,
            "new_technologies": new,
        }

    @staticmethod
    def _shifts(current: Counter, previous: Counter) -> tuple[list[tuple[str, int]], list[str]]:
        """Returns (rising, new): `rising` is technologies present in both
        windows whose count increased, sorted by the size of the increase;
        `new` is technologies seen this window that weren't seen at all in
        the previous one."""
        deltas = ((tech, count - previous.get(tech, 0)) for tech, count in current.items())
        rising = sorted((pair for pair in deltas if pair[1] > 0), key=lambda pair: pair[1], reverse=True)[:10]
        new = sorted(tech for tech in current if tech not in previous)[:10]
        return rising, new
