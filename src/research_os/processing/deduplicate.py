"""Deduplication (spec section 24).

Priority order for identity match: DOI > arXiv ID > URL > GitHub URL >
normalized title > content hash. A duplicate is never re-sent to an LLM.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from research_os.core.schema import ResearchItem
from research_os.database.models import Document


def find_existing(session: Session, item: ResearchItem) -> Document | None:
    checks = [
        (Document.doi, item.doi),
        (Document.arxiv_id, item.arxiv_id),
        (Document.url, item.url),
        (Document.github_url, item.github_url),
        (Document.normalized_title, item.normalized_title),
        (Document.content_hash, item.content_hash),
    ]
    for column, value in checks:
        if not value:
            continue
        existing = session.scalars(select(Document).where(column == value)).first()
        if existing is not None:
            return existing
    return None


def is_duplicate(session: Session, item: ResearchItem) -> bool:
    return find_existing(session, item) is not None
