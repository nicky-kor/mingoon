import datetime as dt

from research_os.agents.trend import TrendAgent
from research_os.core.timeutils import utc_now
from research_os.database.models import Document


def _doc(external_id: str, technology: str, days_ago: int) -> Document:
    return Document(
        external_id=external_id,
        title=f"doc {external_id}",
        source="arxiv",
        source_type="arxiv",
        technology=technology,
        collected_at=utc_now() - dt.timedelta(days=days_ago),
    )


def test_rising_technologies_reflects_growth_not_just_current_volume(isolated_db):
    # "digital_twin" is flat (2 vs 2) -> not rising. "llm" grew 1 -> 4 ->
    # rising despite being less common overall than digital_twin this week.
    with isolated_db.session_scope() as session:
        # current window (last 7 days)
        for i in range(4):
            session.add(_doc(f"llm-now-{i}", "llm", days_ago=1))
        for i in range(2):
            session.add(_doc(f"twin-now-{i}", "digital_twin", days_ago=1))
        # previous window (7-14 days ago)
        session.add(_doc("llm-prev-0", "llm", days_ago=10))
        for i in range(2):
            session.add(_doc(f"twin-prev-{i}", "digital_twin", days_ago=10))

    with isolated_db.session_scope() as session:
        result = TrendAgent().analyze(session, window_days=7)

    rising_techs = dict(result["rising_technologies"])
    assert rising_techs.get("llm") == 3
    assert "digital_twin" not in rising_techs


def test_new_technologies_only_includes_techs_absent_from_previous_window(isolated_db):
    with isolated_db.session_scope() as session:
        session.add(_doc("agentic-now", "agentic_ai", days_ago=1))
        session.add(_doc("llm-now", "llm", days_ago=1))
        session.add(_doc("llm-prev", "llm", days_ago=10))

    with isolated_db.session_scope() as session:
        result = TrendAgent().analyze(session, window_days=7)

    assert result["new_technologies"] == ["agentic_ai"]


def test_analyze_ignores_documents_outside_the_current_window(isolated_db):
    with isolated_db.session_scope() as session:
        session.add(_doc("old", "llm", days_ago=60))

    with isolated_db.session_scope() as session:
        result = TrendAgent().analyze(session, window_days=7)

    assert result["documents_considered"] == 0
    assert result["top_technologies"] == []
