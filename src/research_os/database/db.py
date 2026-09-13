"""Database engine/session management (SQLite + SQLAlchemy)."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from research_os.core.config import system_config
from research_os.core.logging_setup import get_logger
from research_os.core.paths import resolve
from research_os.database.models import Base

logger = get_logger("database.db")

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
    """Create all tables if they do not already exist, then add any
    columns the models declare that a pre-existing table is still
    missing (there's no separate migrations system for this Phase-1
    project). `create_all()` on its own only creates whole tables that
    don't exist yet -- a brand-new table like `provider_circuit_breaker`
    gets its full schema that way, but adding a column to a `documents`
    table that already exists on disk (e.g. this project's own
    qa_status/qa_flags) is silently a no-op, and the next query for that
    column fails with "no such column" instead of ever creating it."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    _add_missing_columns(engine)


def _add_missing_columns(engine) -> None:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue  # brand new table -- create_all() above already made it in full
            existing_columns = {col["name"] for col in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing_columns:
                    continue
                column_type = column.type.compile(dialect=engine.dialect)
                conn.execute(text(f"ALTER TABLE {table.name} ADD COLUMN {column.name} {column_type}"))
                logger.info("database schema: added missing column %s.%s", table.name, column.name)


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
