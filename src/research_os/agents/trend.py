"""TrendAgent (spec section 34): recurring/emerging technologies over recent
documents. Operates on already-stored documents rather than a single item.
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
        since = utc_now() - timedelta(days=window_days)
        docs = session.scalars(
            select(Document).where(Document.collected_at >= since)
        ).all()

        tech_counter: Counter[str] = Counter(d.technology for d in docs if d.technology)
        problem_counter: Counter[str] = Counter(d.problem for d in docs if d.problem)
        industry_counter: Counter[str] = Counter(d.industry for d in docs if d.industry)

        return {
            "window_days": window_days,
            "documents_considered": len(docs),
            "top_technologies": tech_counter.most_common(10),
            "top_problems": problem_counter.most_common(10),
            "top_industries": industry_counter.most_common(10),
        }
