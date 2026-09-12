"""Personal Skill Graph (spec section 27).

Level scale: 0 Unknown, 1 Concept, 2 Understands Papers, 3 Can Implement,
4 Can Apply Practically, 5 Can Teach.

Phase 1 seeds a starter tree and exposes read access via `research-os
skills`. Recommendation logic (next skill to learn, papers, experiments) is
a Phase 3+ extension once enough documents/evidence accumulate.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from research_os.database.models import Skill

LEVEL_LABELS = {
    0: "Unknown",
    1: "Concept",
    2: "Understands Papers",
    3: "Can Implement",
    4: "Can Apply Practically",
    5: "Can Teach",
}

_SEED_TREE = [
    ("predictive_maintenance", "Predictive Maintenance", None, 2),
    ("anomaly_detection", "Anomaly Detection", "predictive_maintenance", 0),
    ("fault_diagnosis", "Fault Diagnosis", "predictive_maintenance", 0),
    ("rul", "RUL", "predictive_maintenance", 0),
    ("transformer", "Transformer", "predictive_maintenance", 0),
    ("digital_twin", "Digital Twin", "predictive_maintenance", 0),
]


def seed_default_skills(session: Session) -> int:
    created = 0
    for key, name, parent_key, level in _SEED_TREE:
        existing = session.scalars(select(Skill).where(Skill.key == key)).first()
        if existing:
            continue
        session.add(Skill(key=key, name=name, parent_key=parent_key, level=level))
        created += 1
    return created


def list_skills(session: Session) -> list[Skill]:
    return list(session.scalars(select(Skill).order_by(Skill.parent_key, Skill.key)).all())
