from research_os.knowledge.skills import list_skills, seed_default_skills


def test_seed_default_skills_creates_tree(isolated_db):
    with isolated_db.session_scope() as session:
        created = seed_default_skills(session)
        assert created == 6

    with isolated_db.session_scope() as session:
        skills = list_skills(session)
        keys = {s.key for s in skills}
        assert "predictive_maintenance" in keys
        assert "anomaly_detection" in keys


def test_seed_default_skills_is_idempotent(isolated_db):
    with isolated_db.session_scope() as session:
        seed_default_skills(session)
    with isolated_db.session_scope() as session:
        created_again = seed_default_skills(session)
        assert created_again == 0
