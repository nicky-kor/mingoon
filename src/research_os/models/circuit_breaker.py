"""Per-provider circuit breaker (spec section 13/42: don't waste calls on
a provider we already know is broken).

There is no cheap "check my credit balance" endpoint on the cloud APIs
this project talks to — the only way to find out is to actually try a
call and see whether it fails on billing. So instead of checking first,
this remembers that failure: once a call to a provider fails for a
reason a retry can't fix (out of credit, invalid key), the provider is
"tripped" for a cooldown, and `ModelGateway` skips straight past it to
the next tier in the fallback chain — no repeated failing calls, and no
manual config edit needed to "use local for now". The breaker clears
itself once the cooldown passes, so the very next call after that
automatically tries the provider again (e.g. once credit is topped up).

Deliberately NOT tripped for transient errors (timeouts, connection
resets, rate limits) — those often resolve on the very next call, and
tripping the breaker on them would need this project's own PC to be
offline for an hour to "fix" what a moment's retry would have solved.
"""
from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from research_os.core.logging_setup import get_logger
from research_os.core.timeutils import utc_now
from research_os.database.models import ProviderCircuitBreaker

logger = get_logger("models.circuit_breaker")

DEFAULT_COOLDOWN_SECONDS = 3600  # 1 hour

# Heuristics for "a retry will not fix this" failures, taken from the
# actual error text providers return. Deliberately conservative: matching
# too broadly would trip the breaker on failures a retry might resolve.
_UNRECOVERABLE_PATTERNS = [
    r"credit balance is too low",
    r"insufficient_quota",
    r"exceeded your current quota",
    r"invalid[_ ]api[_ ]key",
    r"authentication_error",
]
_UNRECOVERABLE_RE = re.compile("|".join(_UNRECOVERABLE_PATTERNS), re.IGNORECASE)


def is_unrecoverable_failure(error_message: str) -> bool:
    return bool(_UNRECOVERABLE_RE.search(error_message or ""))


def is_tripped(session: Session, provider: str) -> ProviderCircuitBreaker | None:
    """Returns the active breaker row for `provider`, or None if it isn't
    tripped (never failed this way, or the cooldown already passed)."""
    row = session.get(ProviderCircuitBreaker, provider)
    if row is None:
        return None
    if row.tripped_until <= utc_now():
        return None
    return row


def trip(session: Session, provider: str, reason: str, cooldown_seconds: int = DEFAULT_COOLDOWN_SECONDS) -> None:
    now = utc_now()
    from datetime import timedelta

    tripped_until = now + timedelta(seconds=cooldown_seconds)
    existing = session.get(ProviderCircuitBreaker, provider)
    if existing is None:
        session.add(ProviderCircuitBreaker(provider=provider, tripped_until=tripped_until, reason=reason, tripped_at=now))
    else:
        existing.tripped_until = tripped_until
        existing.reason = reason
        existing.tripped_at = now
    logger.warning("circuit breaker tripped for provider=%s until=%s reason=%s", provider, tripped_until, reason)


def clear(session: Session, provider: str) -> None:
    """Manual reset (e.g. `research-os models --reset-circuit-breaker`,
    or after topping up credit and not wanting to wait for the cooldown)."""
    row = session.get(ProviderCircuitBreaker, provider)
    if row is not None:
        session.delete(row)


def list_active(session: Session) -> list[ProviderCircuitBreaker]:
    now = utc_now()
    return list(session.scalars(select(ProviderCircuitBreaker).where(ProviderCircuitBreaker.tripped_until > now)).all())
