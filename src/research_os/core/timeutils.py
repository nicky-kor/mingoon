"""Single source of truth for "now" in UTC.

`datetime.utcnow()` is deprecated as of Python 3.12 (fully removed in a
future version) in favor of timezone-aware `datetime.now(timezone.utc)`.
This project stores and compares *naive* UTC datetimes everywhere
(SQLite/SQLAlchemy columns, `ResearchItem.collected_at`, published_at
parsed via dateutil, ...), so switching to a naive/aware mix mid-codebase
would risk "can't compare naive and aware datetimes" errors. `utc_now()`
returns the same naive-UTC value `utcnow()` did, without the deprecated
call — everything else about the codebase's datetime handling is
unchanged.
"""
from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)
