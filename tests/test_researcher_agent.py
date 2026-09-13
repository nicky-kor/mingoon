"""ResearchAgent.search() (spec section 35-36) had no dedicated tests
before this — added alongside the score-ranking change below."""
from research_os.agents.researcher import ResearchAgent
from research_os.database.models import Document, Score


def _doc(session, external_id: str, title: str, overall_score: float | None) -> Document:
    doc = Document(external_id=external_id, title=title, source="arxiv", source_type="arxiv", abstract=title)
    session.add(doc)
    session.flush()
    if overall_score is not None:
        session.add(Score(document_id=doc.id, overall_score=overall_score, priority="Medium"))
    return doc


def test_search_ranks_matches_by_score_not_insertion_order(isolated_db):
    with isolated_db.session_scope() as session:
        _doc(session, "low", "battery coating anomaly detection", overall_score=20.0)
        _doc(session, "high", "battery coating defect classification", overall_score=90.0)
        _doc(session, "mid", "battery coating quality inspection", overall_score=50.0)

    with isolated_db.session_scope() as session:
        results = ResearchAgent().search(session, "battery coating", limit=10)

    assert [d.external_id for d in results] == ["high", "mid", "low"]


def test_search_sorts_unscored_documents_last(isolated_db):
    with isolated_db.session_scope() as session:
        _doc(session, "unscored", "battery coating pending analysis", overall_score=None)
        _doc(session, "scored", "battery coating scored result", overall_score=10.0)

    with isolated_db.session_scope() as session:
        results = ResearchAgent().search(session, "battery coating", limit=10)

    assert [d.external_id for d in results] == ["scored", "unscored"]


def test_search_respects_limit_after_ranking(isolated_db):
    with isolated_db.session_scope() as session:
        for i in range(5):
            _doc(session, f"doc-{i}", "battery coating test document", overall_score=float(i))

    with isolated_db.session_scope() as session:
        results = ResearchAgent().search(session, "battery coating", limit=2)

    assert len(results) == 2
    assert results[0].external_id == "doc-4"  # highest score kept


def test_search_returns_empty_for_no_meaningful_terms(isolated_db):
    with isolated_db.session_scope() as session:
        results = ResearchAgent().search(session, "a an", limit=10)
    assert results == []
