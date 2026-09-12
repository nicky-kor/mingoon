import pytest

from research_os.database import db as db_module


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    """Point the database layer at a throwaway SQLite file for this test."""
    db_module.reset_engine_for_tests()
    fake_db_path = tmp_path / "test.db"
    monkeypatch.setattr(db_module, "system_config", lambda: {"paths": {"database": str(fake_db_path)}})
    db_module.init_db()
    yield db_module
    db_module.reset_engine_for_tests()
