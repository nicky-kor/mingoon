from research_os.database.models import Document
from research_os.knowledge.graph import edge_count, ingest_document, node_count


def test_ingest_document_creates_nodes_and_edges(isolated_db):
    with isolated_db.session_scope() as session:
        doc = Document(
            external_id="kg:1", title="Paper", source="arxiv", source_type="arxiv",
            industry="steel", technology="fault_diagnosis", problem="root_cause_analysis",
        )
        session.add(doc)
        session.flush()
        ingest_document(session, doc)

    with isolated_db.session_scope() as session:
        assert node_count(session) >= 4  # industry, technology, problem, paper
        assert edge_count(session) >= 3
