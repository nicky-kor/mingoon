from research_os.evaluation.dataset import CASES, categories, get_case
from research_os.evaluation.prompts import TASK_KEYS, build_prompt


def test_dataset_has_at_least_ten_cases():
    assert len(CASES) >= 10


def test_every_case_has_required_fields():
    for case in CASES:
        assert case.id and case.category and case.title and case.abstract
        assert case.source  # provenance must always be stated


def test_categories_cover_spec_list():
    cats = categories()
    expected_substrings = [
        "Industrial AI", "Battery Manufacturing", "keyword", "Korean",
        "English", "Predictive Maintenance", "Anomaly Detection",
        "Battery relevance", "transfer", "Research question",
    ]
    joined = " ".join(cats).lower()
    for expected in expected_substrings:
        assert expected.lower() in joined


def test_get_case_returns_none_for_unknown_id():
    assert get_case("does-not-exist") is None


def test_build_prompt_for_every_task_key():
    case = CASES[0]
    for task_key in TASK_KEYS:
        prompt = build_prompt(task_key, case)
        assert isinstance(prompt, str) and len(prompt) > 10
