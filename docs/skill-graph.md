# Personal Skill Graph

Tracks the user's own Industrial AI capability level, separate from the
document knowledge graph (spec section 27).

## Levels

| Level | Meaning |
|---|---|
| 0 | Unknown |
| 1 | Concept |
| 2 | Understands Papers |
| 3 | Can Implement |
| 4 | Can Apply Practically |
| 5 | Can Teach |

## Seed tree

`research_os/knowledge/skills.py` seeds a starter tree on `research-os
init` (and idempotently on `research-os skills`):

```
Predictive Maintenance          Level 2
├── Anomaly Detection           Level 0
├── Fault Diagnosis             Level 0
├── RUL                         Level 0
├── Transformer                 Level 0
└── Digital Twin                Level 0
```

Edit levels directly via the `skills` table (or a small script using
`session_scope()`) until a CLI edit command exists.

## Viewing

```
research-os skills
```

## Roadmap (Phase 3+)

Recommendation logic — next skill to learn, recommended papers/projects/
experiments, suggested learning order — is intentionally not built yet: it
needs a meaningful backlog of analyzed, scored documents and
transfer opportunities to recommend from. `SkillEvidence` (the
`skill_evidence` table) is already modeled to link a skill to the
documents that justify raising its level, ready for that phase.
