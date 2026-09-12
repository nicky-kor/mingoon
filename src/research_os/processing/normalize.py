"""Normalization: turn a raw collector dict into a canonical ResearchItem.

Handles whitespace cleanup, date parsing, title normalization for dedup,
and content-hash computation.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any

from dateutil import parser as date_parser

from research_os.core.schema import ResearchItem


def normalize_title(title: str) -> str:
    t = title.lower().strip()
    t = re.sub(r"[^a-z0-9\s]", "", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def compute_content_hash(title: str, abstract: str | None) -> str:
    basis = normalize_title(title) + "|" + (abstract or "").strip().lower()[:500]
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


def _parse_date(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    try:
        return date_parser.parse(str(value))
    except (ValueError, TypeError):
        return None


def normalize_item(raw: dict[str, Any]) -> ResearchItem:
    title = (raw.get("title") or "").strip()
    abstract = (raw.get("abstract") or "").strip() or None

    data = dict(raw)
    data["title"] = title
    data["abstract"] = abstract
    data["published_at"] = _parse_date(raw.get("published_at"))
    data.setdefault("collected_at", datetime.now(timezone.utc).replace(tzinfo=None))
    data["normalized_title"] = normalize_title(title)
    data["content_hash"] = compute_content_hash(title, abstract)
    data.setdefault("id", raw.get("external_id") or data["content_hash"])
    data.setdefault("keywords", raw.get("keywords") or [])
    data.setdefault("authors", raw.get("authors") or [])
    # ResearchItem doesn't have an `external_id` field name for `id`; map it.
    data.pop("external_id", None)

    return ResearchItem(**{k: v for k, v in data.items() if k in ResearchItem.model_fields})
