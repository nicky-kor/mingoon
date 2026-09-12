"""Personal Knowledge Graph (spec section 26).

Backed by SQLite (knowledge_nodes / knowledge_edges) — no Neo4j in Phase 1-3
per the "don't overengineer" rule (spec section 61). The relation chain
Industry -> Process -> Equipment -> Sensor -> Signal -> Problem ->
AI Technology -> Paper -> Application is expressed as typed nodes/edges.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from research_os.database.models import Document, KnowledgeEdge, KnowledgeNode


def get_or_create_node(session: Session, node_type: str, key: str, label: str) -> KnowledgeNode:
    existing = session.scalars(
        select(KnowledgeNode).where(KnowledgeNode.node_type == node_type, KnowledgeNode.key == key)
    ).first()
    if existing:
        return existing
    node = KnowledgeNode(node_type=node_type, key=key, label=label)
    session.add(node)
    session.flush()
    return node


def add_edge(session: Session, source: KnowledgeNode, target: KnowledgeNode, relation: str, document_id: int | None = None) -> KnowledgeEdge:
    edge = KnowledgeEdge(
        source_node_id=source.id, target_node_id=target.id, relation=relation, document_id=document_id
    )
    session.add(edge)
    return edge


def ingest_document(session: Session, doc: Document) -> None:
    """Add Industry -> Technology -> Problem nodes/edges for one document."""
    if doc.industry:
        industry_node = get_or_create_node(session, "industry", doc.industry, doc.industry)
    else:
        industry_node = None

    if doc.technology:
        tech_node = get_or_create_node(session, "technology", doc.technology, doc.technology)
        if industry_node:
            add_edge(session, industry_node, tech_node, "applies_technology", doc.id)
    else:
        tech_node = None

    if doc.problem:
        problem_node = get_or_create_node(session, "problem", doc.problem, doc.problem)
        if tech_node:
            add_edge(session, tech_node, problem_node, "addresses_problem", doc.id)

    paper_node = get_or_create_node(session, "paper", doc.external_id, doc.title)
    if tech_node:
        add_edge(session, paper_node, tech_node, "demonstrates", doc.id)


def rebuild_from_documents(session: Session) -> int:
    count = 0
    for doc in session.scalars(select(Document)).all():
        ingest_document(session, doc)
        count += 1
    return count


def node_count(session: Session) -> int:
    return len(session.scalars(select(KnowledgeNode)).all())


def edge_count(session: Session) -> int:
    return len(session.scalars(select(KnowledgeEdge)).all())
