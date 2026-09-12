"""Every agent must produce a usable result with gateway=None (no LLM
configured at all) — this is the reliability guarantee from spec section 44."""
from research_os.agents.analyst import AnalystAgent
from research_os.agents.classifier import ClassifierAgent
from research_os.agents.summarizer import SummarizerAgent
from research_os.agents.transfer import TransferAgent
from research_os.core.schema import ResearchItem


def _sample_item(**overrides) -> ResearchItem:
    data = dict(
        id="arxiv:1",
        title="Vibration-based fault diagnosis for rolling mill motors using deep learning",
        url="http://example.com/1",
        source="arxiv",
        source_type="arxiv",
        abstract=(
            "We propose a deep learning approach for fault diagnosis of rolling mill motors "
            "in steel manufacturing using vibration sensor data. Experiments on a real dataset "
            "achieve 96% accuracy, demonstrating industrial applicability."
        ),
    )
    data.update(overrides)
    return ResearchItem(**data)


def test_classifier_rule_based_fallback():
    item = _sample_item()
    result = ClassifierAgent(gateway=None).classify(item)
    assert result["industry"] == "steel"
    assert result["model_used"] == "rule_based_fallback"


def test_summarizer_heuristic_fallback():
    item = _sample_item()
    result = SummarizerAgent(gateway=None).summarize(item)
    assert result["summary"]
    assert result["model_used"] == "heuristic_extraction_fallback"


def test_analyst_heuristic_fallback_produces_scores_in_range():
    item = _sample_item(industry="steel", technology="fault_diagnosis")
    result = AnalystAgent(gateway=None).analyze(item)
    for key in ("evidence_score", "practical_score", "novelty_score", "battery_relevance"):
        assert 0.0 <= result[key] <= 100.0


def test_transfer_agent_skips_battery_items():
    item = _sample_item(industry="battery_manufacturing", technology="fault_diagnosis")
    assert TransferAgent(gateway=None).analyze_transfer(item) is None


def test_transfer_agent_produces_opportunity_for_other_industry():
    item = _sample_item(industry="steel", technology="fault_diagnosis")
    result = TransferAgent(gateway=None).analyze_transfer(item)
    assert result is not None
    assert 0.0 <= result["transfer_confidence"] <= 100.0
    assert result["target_battery_process"]
