"""Database engine/session management (SQLite + SQLAlchemy)."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from research_os.core.config import system_config
from research_os.core.paths import resolve
from research_os.database.models import Base

_engine = None
_SessionLocal = None


def get_engine(echo: bool = False):
    global _engine
    if _engine is None:
        db_path = resolve(system_config()["paths"]["database"])
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(f"sqlite:///{db_path}", echo=echo, future=True)
    return _engine


def init_db() -> None:
    """Create all tables if they do not already exist."""
    engine = get_engine()
    Base.metadata.create_all(engine)


def get_session_factory() -> sessionmaker:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), expire_on_commit=False, future=True)
    return _SessionLocal


@contextmanager
def session_scope() -> Iterator[Session]:
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def reset_engine_for_tests() -> None:
    """Used by tests to force a fresh engine (e.g. after changing cwd/db path)."""
    global _engine, _SessionLocal
    _engine = None
    _SessionLocal = None
