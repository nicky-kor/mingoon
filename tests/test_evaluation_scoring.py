import json

from research_os.evaluation.scoring import (
    CompositeInputs,
    composite_score,
    latency_score,
    resource_efficiency_score,
    score_json_response,
    score_korean_quality,
    score_reasoning_response,
    score_technical_accuracy,
    stability_score,
    strip_reasoning_preamble,
)


def test_strip_reasoning_preamble_removes_think_block():
    raw = "<think>hmm let me consider the options here</think>" + json.dumps({"industry": "steel"})
    stripped = strip_reasoning_preamble(raw)
    assert "<think>" not in stripped
    assert "hmm let me consider" not in stripped
    assert json.loads(stripped) == {"industry": "steel"}


def test_strip_reasoning_preamble_handles_multiline_and_case_insensitive():
    raw = "<THINK>\nline one\nline two\n</THINK>\nfinal answer"
    assert strip_reasoning_preamble(raw) == "final answer"


def test_strip_reasoning_preamble_leaves_plain_text_untouched():
    assert strip_reasoning_preamble("no think tags here") == "no think tags here"


def test_strip_reasoning_preamble_falls_back_to_raw_text_if_all_preamble():
    raw = "<think>only thinking, no final answer at all</think>"
    # Nothing left after stripping — still return something scoreable
    # (a score of 0 for empty content) rather than an empty string that
    # would look identical to "no response at all".
    assert strip_reasoning_preamble(raw) == raw


def test_score_json_response_full_marks():
    response = json.dumps({"industry": "steel", "technology": "fault_diagnosis", "problem": "root_cause_analysis"})
    assert score_json_response("classification", response) == 100.0


def test_score_json_response_missing_keys_scores_lower():
    response = json.dumps({"industry": "steel"})
    score = score_json_response("classification", response)
    assert 0 < score < 100


def test_score_json_response_unparseable_is_zero():
    assert score_json_response("classification", "not json at all") == 0.0


def test_score_json_response_keyword_extraction_array():
    response = json.dumps(["anomaly detection", "transformer", "sensor fusion", "predictive maintenance"])
    assert score_json_response("keyword_extraction", response) == 100.0


def test_score_technical_accuracy_valid_taxonomy_keys():
    response = json.dumps({"industry": "steel", "technology": "fault_diagnosis", "problem": "root_cause_analysis"})
    score = score_technical_accuracy("classification", response)
    assert score == 100.0


def test_score_technical_accuracy_hallucinated_category():
    response = json.dumps({"industry": "moon_mining", "technology": "telekinesis", "problem": "root_cause_analysis"})
    score = score_technical_accuracy("classification", response)
    assert score < 100.0


def test_score_korean_quality_only_applies_to_korean_task():
    assert score_korean_quality("classification", "아무 내용") is None
    assert score_korean_quality("korean_summary", "이것은 완전한 한국어 문장입니다") is not None


def test_score_korean_quality_low_for_english_response():
    score = score_korean_quality("korean_summary", "This is entirely in English with no Korean at all.")
    assert score < 20.0


def test_score_reasoning_response_empty_is_zero():
    assert score_reasoning_response("") == 0.0


def test_score_reasoning_response_substantive_scores_higher():
    short = score_reasoning_response("짧음")
    long_answer = score_reasoning_response(
        "센서 데이터 표준화와 도메인 gap이 가장 큰 장애요인이다. " * 10
    )
    assert long_answer > short


def test_latency_score_bounds():
    assert latency_score(500) == 100.0
    assert latency_score(None) is None
    assert 0 <= latency_score(15000) <= 100


def test_resource_efficiency_prefers_vram_when_available():
    assert resource_efficiency_score(ram_mb=8000, vram_mb=1000, disk_mb=2000) == resource_efficiency_score(None, 1000, None)


def test_resource_efficiency_none_when_nothing_measured():
    assert resource_efficiency_score(None, None, None) is None


def test_stability_score():
    assert stability_score(6, 6) == 100.0
    assert stability_score(0, 6) == 0.0
    assert stability_score(0, 0) is None


def test_composite_score_renormalizes_over_available_components():
    only_quality = composite_score(CompositeInputs(quality=80))
    assert only_quality == 80.0  # single component: its weight is 100% of the total


def test_composite_score_none_when_nothing_available():
    assert composite_score(CompositeInputs()) is None
