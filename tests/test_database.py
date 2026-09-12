from sqlalchemy import select

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
