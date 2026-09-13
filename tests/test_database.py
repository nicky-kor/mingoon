from sqlalchemy import create_engine, select, text

import research_os.database.db as db_module
from research_os.database.models import Document


def test_init_db_creates_tables_and_allows_crud(isolated_db):
    with isolated_db.session_scope() as session:
        session.add(
            Document(
                external_id="test:1", title="Test Doc", source="test", source_type="test",
            )
        )

    with isolated_db.session_scope() as session:
        docs = session.scalars(select(Document)).all()
        assert len(docs) == 1
        assert docs[0].external_id == "test:1"


def test_external_id_unique_constraint(isolated_db):
    with isolated_db.session_scope() as session:
        session.add(Document(external_id="dup:1", title="A", source="s", source_type="s"))

    with isolated_db.session_scope() as session:
        session.add(Document(external_id="dup:1", title="B", source="s", source_type="s"))
        try:
            session.commit()
            assert False, "expected an IntegrityError"
        except Exception:
            session.rollback()


def test_init_db_adds_columns_missing_from_a_pre_existing_table(tmp_path, monkeypatch):
    # Reproduces upgrading an existing on-disk DB created before
    # qa_status/qa_flags existed: create_all() alone leaves a table that
    # already exists untouched, so without _add_missing_columns() the
    # very next query for the new column fails with "no such column".
    db_path = tmp_path / "old_schema.db"
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE documents ("
                "id INTEGER PRIMARY KEY, external_id VARCHAR(300) UNIQUE, title TEXT NOT NULL, "
                "source VARCHAR(100) NOT NULL, source_type VARCHAR(50) NOT NULL, "
                "collected_at DATETIME, status VARCHAR(30)"
                ")"
            )
        )
    engine.dispose()

    db_module.reset_engine_for_tests()
    monkeypatch.setattr(db_module, "system_config", lambda: {"paths": {"database": str(db_path)}})
    db_module.init_db()

    with db_module.session_scope() as session:
        session.add(Document(external_id="old-schema:1", title="T", source="s", source_type="s", qa_status="passed"))

    with db_module.session_scope() as session:
        doc = session.scalars(select(Document)).one()
        assert doc.qa_status == "passed"
        assert doc.qa_flags is None

    db_module.reset_engine_for_tests()
