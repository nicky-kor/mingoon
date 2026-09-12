from research_os.processing.normalize import compute_content_hash, normalize_item, normalize_title


def test_normalize_title_strips_punctuation_and_case():
    assert normalize_title("Attention Is All You Need!") == "attention is all you need"


def test_content_hash_is_stable_for_same_input():
    h1 = compute_content_hash("Title A", "abstract text")
    h2 = compute_content_hash("Title A", "abstract text")
    assert h1 == h2


def test_content_hash_differs_for_different_input():
    h1 = compute_content_hash("Title A", "abstract text")
    h2 = compute_content_hash("Title B", "abstract text")
    assert h1 != h2


def test_normalize_item_produces_valid_research_item():
    raw = {
        "external_id": "arxiv:1234.5678",
        "arxiv_id": "1234.5678",
        "title": "  A Great Paper  ",
        "url": "http://arxiv.org/abs/1234.5678",
        "source": "arxiv",
        "source_type": "arxiv",
        "published_at": "2024-01-01T00:00:00Z",
        "authors": ["A. Author"],
        "abstract": "This paper proposes a new method.",
    }
    item = normalize_item(raw)
    assert item.id == "arxiv:1234.5678"
    assert item.title == "A Great Paper"
    assert item.arxiv_id == "1234.5678"
    assert item.normalized_title == "a great paper"
    assert item.content_hash
    assert item.published_at is not None
