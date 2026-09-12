# Knowledge Graph

## Storage

SQLite (`knowledge_nodes`, `knowledge_edges` tables) — deliberately not
Neo4j in Phase 1-3, per the "don't overengineer" rule (spec section 61).
`research_os/knowledge/graph.py` implements typed nodes (`node_type`:
`industry`, `technology`, `problem`, `paper`, ...) and typed edges
(`relation`: `applies_technology`, `addresses_problem`, `demonstrates`).

The full relation chain from the spec —
Industry → Process → Equipment → Sensor → Signal → Problem →
AI Technology → Paper → Application — is representable with this schema;
Phase 1 populates the Industry/Technology/Problem/Paper slice automatically
as documents are analyzed (`pipeline.mark_analyzed` calls
`knowledge.graph.ingest_document`). Process/Equipment/Sensor/Signal nodes
are a Phase 3 extension once there's enough analyzed battery-specific data
to populate them meaningfully.

## Populating and inspecting

The graph grows automatically as `research-os run` (or `analyze`/`transfer`
followed by the store step) marks documents analyzed — no separate build
command is needed in Phase 1. `research-os status` reports current node/edge
counts. `knowledge.graph.rebuild_from_documents(session)` will re-derive
the graph from scratch from every stored document, useful after a taxonomy
change.

## Querying

There's no dedicated CLI search command yet (Phase 3). In the meantime,
query directly:

```python
from sqlalchemy import select
from research_os.database.db import session_scope
from research_os.database.models import KnowledgeNode, KnowledgeEdge

with session_scope() as session:
    tech_node = session.scalars(
        select(KnowledgeNode).where(KnowledgeNode.node_type == "technology", KnowledgeNode.key == "fault_diagnosis")
    ).first()
```
