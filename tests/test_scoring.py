from research_os.scoring.scorer import ScoreInput, compute_score


def test_full_marks_is_critical():
    result = compute_score(ScoreInput(100, 100, 100, 100, 100))
    assert result.overall_score == 100.0
    assert result.priority == "Critical"


def test_zero_is_archive():
    result = compute_score(ScoreInput(0, 0, 0, 0, 0))
    assert result.overall_score == 0.0
    assert result.priority == "Archive"


def test_weights_applied_correctly():
    # battery_relevance weight is 0.25 per config/scoring.yaml
    result = compute_score(ScoreInput(battery_relevance=100, transferability=0, evidence_quality=0,
                                       practical_applicability=0, novelty=0))
    assert result.overall_score == 25.0


def test_priority_thresholds_are_ordered():
    scores = [compute_score(ScoreInput(v, v, v, v, v)).priority for v in [95, 80, 65, 45, 10]]
    assert scores == ["Critical", "High", "Medium", "Low", "Archive"]
