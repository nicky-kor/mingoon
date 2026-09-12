from research_os.database.models import Document
from research_os.processing.deduplicate import find_existing, is_duplicate
from research_os.processing.normalize import normalize_item


def _make_item(**overrides):
    raw = {
        "external_id": "arxiv:1111.2222",
        "arxiv_id": "1111.2222",
        "title": "Some Paper Title",
        "url": "http://arxiv.org/abs/1111.2222",
        "source": "arxiv",
        "source_type": "arxiv",
        "abstract": "An abstract.",
    }
    raw.update(overrides)
    return normalize_item(raw)


def test_no_duplicate_in_empty_db(isolated_db):
    with isolated_db.session_scope() as session:
        item = _make_item()
        assert is_duplicate(session, item) is False


def test_duplicate_detected_by_arxiv_id(isolated_db):
    with isolated_db.session_scope() as session:
        item = _make_item()
        session.add(
            Document(
                external_id=item.id, title=item.title, url=item.url, source=item.source,
                source_type=item.source_type, arxiv_id=item.arxiv_id,
                normalized_title=item.normalized_title, content_hash=item.content_hash,
            )
        )

    with isolated_db.session_scope() as session:
        duplicate_item = _make_item(title="Some Paper Title (mirror)")
        existing = find_existing(session, duplicate_item)
        assert existing is not None


def test_duplicate_detected_by_content_hash_when_no_ids_match(isolated_db):
    with isolated_db.session_scope() as session:
        item = _make_item(external_id="arxiv:aaa", arxiv_id=None, url=None)
        session.add(
            Document(
                external_id=item.id, title=item.title, url=item.url, source=item.source,
                source_type=item.source_type, normalized_title=item.normalized_title,
                content_hash=item.content_hash,
            )
        )

    with isolated_db.session_scope() as session:
        same_content_item = _make_item(external_id="arxiv:bbb", arxiv_id=None, url=None)
        assert is_duplicate(session, same_content_item) is True
