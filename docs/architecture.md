# Architecture

## Layers

```
CLI (research_os/cli.py)
   |
Research Pipeline (research_os/research/pipeline.py)
   |
Agents (research_os/agents/*)          Collectors (research_os/collectors/*)
   |                                        |
ModelGateway -> ModelRouter -> ProviderAdapter        Processing (normalize/dedupe/classify/extract)
   |
Database (SQLAlchemy models + SQLite)
```

Nothing outside `research_os/models/` talks to a provider SDK/API directly.
Agents call `ModelGateway.generate(...)`; the gateway asks `ModelRouter` for
a tier, resolves it to a `(provider, model)` pair from `config/models.yaml`,
and calls the matching `ProviderAdapter`. If that fails, the gateway walks
the tier's fallback chain (also in `config/models.yaml`) before giving up.

Every agent additionally implements a **deterministic, non-LLM fallback**
(rule-based classification, heuristic extraction/scoring) so the pipeline
never stops just because no model is configured — see
`research_os/processing/classify.py` and `.../extraction.py`.

## The Research Pipeline (Phase 1)

```
COLLECT -> NORMALIZE -> DEDUPLICATE -> CLASSIFY -> SUMMARIZE -> ANALYZE
   (battery relevance + evidence/practical/novelty scores + SCORE)
-> TRANSFER ANALYSIS -> STORE -> (REPORT, on demand)
```

Each stage is its own function in `research_os/research/pipeline.py` and
its own CLI command (`collect`, `classify`, `summarize`, `analyze`,
`transfer`), so any stage can be re-run independently against whatever is
pending in the database. `research-os run` chains all of them.

A failure processing one document (bad LLM response, parse error, network
hiccup) is caught per-document; it's recorded on that document
(`processing_status=error`) and the batch continues (spec section 44).

## Data model

See `research_os/database/models.py`. `documents` is the main table and
carries the full Research Item schema (spec section 19) denormalized onto
one row for simplicity; `scores`, `transfer_opportunities`,
`knowledge_nodes/edges`, `skills/skill_evidence`, `llm_runs`, and
`model_benchmarks` are separate tables per the spec's table list. Some
tables (`sources`, `industries`, `technologies`, `problems`,
`document_tags`) exist as reference/lookup tables seeded by `research-os
init` from `config/*.yaml`, ahead of the per-phase features that will use
them more heavily (search filters, multi-tag documents in Phase 2+).

## Configuration, not code

Taxonomies (`config/industries.yaml`, `technologies.yaml`, `problems.yaml`,
`battery.yaml`), model tiers and provider bindings (`config/models.yaml`),
agent→tier policy (`config/routing.yaml`), and scoring weights
(`config/scoring.yaml`) are all YAML. No model name or scoring weight is
hardcoded in Python — see `research_os/core/config.py`.

## Reliability

- Collectors never raise out of `.run()` (`collectors/base.py`).
- `ModelGateway` walks a fallback chain and only raises
  `AllProvidersUnavailableError` after every tier in the chain has failed;
  every agent catches that and falls back to a heuristic.
- Every LLM attempt (success, fallback, or failure) is logged to the
  `llm_runs` table and to `logs/research_os.log` (spec section 43).
- Deduplication runs before any LLM call, so a re-collected duplicate is
  never re-analyzed (cost control, spec section 24/42).
- `ModelGateway` caches every (provider, model, prompt, system,
  max_tokens, temperature) combination in the `llm_cache` table
  (`models/cache.py`) — an identical request is never re-sent to a model
  (spec section 15). Best-effort RAM/VRAM probing
  (`core/resource_probe.py`) is opt-in per call (`measure_resources=True`)
  so normal agent traffic doesn't pay that overhead; the local LLM
  benchmark (`docs/local-llm.md`) uses it directly.
