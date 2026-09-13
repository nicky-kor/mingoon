"""QAAgent (spec section 21/44): grounding check over generated fields."""
from research_os.agents.qa import QAAgent
from research_os.core.schema import ResearchItem


def _item(**overrides) -> ResearchItem:
    data = dict(
        id="arxiv:1",
        title="Vibration-based fault diagnosis for rolling mill motors",
        source="arxiv",
        source_type="arxiv",
        abstract="We achieve 96% accuracy on a real industrial dataset using vibration sensors.",
    )
    data.update(overrides)
    return ResearchItem(**data)


def test_clean_document_passes():
    item = _item(summary="The method achieves 96% accuracy.", key_findings=["96% accuracy demonstrated"])
    result = QAAgent().check(item)
    assert result["qa_status"] == "passed"
    assert result["qa_flags"] == []


def test_fabricated_percentage_not_in_source_is_flagged():
    item = _item(summary="The method achieves 99.9% accuracy, a new state of the art.")
    result = QAAgent().check(item)
    assert result["qa_status"] == "flagged"
    assert any("99.9%" in flag for flag in result["qa_flags"])


def test_fabricated_percentage_in_key_findings_is_flagged():
    item = _item(key_findings=["Reduced defect rate by 42% in field deployment"])
    result = QAAgent().check(item)
    assert result["qa_status"] == "flagged"
    assert any("42%" in flag for flag in result["qa_flags"])


def test_empty_summary_is_flagged():
    item = _item(summary="   ")
    result = QAAgent().check(item)
    assert result["qa_status"] == "flagged"
    assert any("empty" in flag for flag in result["qa_flags"])


def test_identical_extreme_scores_are_flagged_as_likely_generic():
    item = _item(evidence_score=100.0, practical_score=100.0, novelty_score=100.0)
    result = QAAgent().check(item)
    assert result["qa_status"] == "flagged"
    assert any("generic non-answer" in flag for flag in result["qa_flags"])


def test_varied_scores_are_not_flagged():
    item = _item(evidence_score=80.0, practical_score=60.0, novelty_score=40.0)
    result = QAAgent().check(item)
    assert result["qa_status"] == "passed"


def test_no_generated_fields_at_all_passes_cleanly():
    item = _item()
    result = QAAgent().check(item)
    assert result["qa_status"] == "passed"
    assert result["qa_flags"] == []
