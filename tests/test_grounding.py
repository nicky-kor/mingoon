from research_os.core.grounding import percentages_in, unsupported_percentages


def test_percentages_in_extracts_normalized_forms():
    assert percentages_in("achieves 96% accuracy and 12.5 % recall") == {"96%", "12.5%"}


def test_percentages_in_empty_text():
    assert percentages_in("") == set()
    assert percentages_in(None) == set()  # type: ignore[arg-type]


def test_unsupported_percentages_finds_only_the_missing_ones():
    source = "We achieve 96% accuracy on a public benchmark."
    generated = "The method reaches 96% accuracy and reduces defects by 42%."
    assert unsupported_percentages(generated, source) == ["42%"]


def test_unsupported_percentages_empty_when_fully_grounded():
    source = "Improves throughput by 15% and reduces defects by 42%."
    generated = "Both a 15% throughput gain and a 42% defect reduction were observed."
    assert unsupported_percentages(generated, source) == []
