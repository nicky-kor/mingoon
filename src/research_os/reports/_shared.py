"""Shared query helper for the daily/weekly reports.

Both reports need "documents collected since some cutoff, paired with
their Score row, sorted by score descending" — factored out here (rather
than duplicated per report) and implemented as one query for the
documents plus one batched query for their scores, instead of a separate
Score lookup per document.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session

from research_os.database.models import Document, Score


def fetch_scored_documents(session: Session, since: dt.datetime) -> list[tuple[Document, Score | None]]:
    """Documents collected at/after `since`, each paired with its Score
    (None if not analyzed yet), sorted by overall_score descending
    (unscored documents sort last). Not truncated — callers slice to
    whatever top-N they need."""
    docs = session.scalars(select(Document).where(Document.collected_at >= since)).all()
    if not docs:
        return []

    scores_by_doc_id = {
        s.document_id: s
        for s in session.scalars(select(Score).where(Score.document_id.in_(d.id for d in docs))).all()
    }
    scored = [(d, scores_by_doc_id.get(d.id)) for d in docs]
    scored.sort(key=lambda pair: pair[1].overall_score if pair[1] else -1, reverse=True)
    return scored
