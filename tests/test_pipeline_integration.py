"""End-to-end Phase 1 pipeline test (spec section 49):
COLLECT -> NORMALIZE -> DEDUPLICATE -> CLASSIFY -> SUMMARIZE -> ANALYZE ->
TRANSFER -> STORE, entirely with the rule-based/heuristic fallback path
(no network, no LLM) so it is fast and deterministic in CI.
"""
from sqlalchemy import select

from research_os.agents import discovery as discovery_module
from research_os.database.models import Document, Score
from research_os.research import pipeline

_SAMPLE_RAW_ITEMS = [
    {
        "external_id": "arxiv:test.0001",
        "arxiv_id": "test.0001",
        "title": "Vibration-based Fault Diagnosis for Rolling Mill Motors",
        "url": "http://arxiv.org/abs/test.0001",
        "source": "arxiv",
        "source_type": "arxiv",
        "published_at": "2024-01-01T00:00:00Z",
        "authors": ["A. Author"],
        "abstract": (
            "We propose a deep learning approach for fault diagnosis of rolling mill "
            "motors in steel manufacturing using vibration sensor data, achieving 96% "
            "accuracy on a real industrial dataset."
        ),
        "privacy_level": "public",
    }
]


def test_full_pipeline_runs_without_llm(isolated_db, monkeypatch):
    monkeypatch.setattr(discovery_module.DiscoveryAgent, "discover", lambda self, source=None: list(_SAMPLE_RAW_ITEMS))

    result = pipeline.run_full_pipeline(source="arxiv", use_llm=False)

    assert result["collect"].new_documents == 1
    assert result["classify"].processed == 1
    assert result["summarize"].processed == 1
    assert result["analyze"].processed == 1
    assert result["transfer"].processed == 1
    assert result["stored"] == 1

    with isolated_db.session_scope() as session:
        docs = session.scalars(select(Document)).all()
        assert len(docs) == 1
        doc = docs[0]
        assert doc.status == "analyzed"
        assert doc.industry == "steel"
        assert doc.summary is not None

        scores = session.scalars(select(Score)).all()
        assert len(scores) == 1
        assert 0.0 <= scores[0].overall_score <= 100.0


def test_pipeline_does_not_duplicate_on_second_collect(isolated_db, monkeypatch):
    monkeypatch.setattr(discovery_module.DiscoveryAgent, "discover", lambda self, source=None: list(_SAMPLE_RAW_ITEMS))

    stats1 = pipeline.collect_and_store(source="arxiv")
    stats2 = pipeline.collect_and_store(source="arxiv")

    assert stats1.new_documents == 1
    assert stats2.new_documents == 0
    assert stats2.duplicates == 1
