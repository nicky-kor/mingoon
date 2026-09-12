# Manufacturing AI Research OS

**Personal Industrial AI Research & Skill OS**

A personal, local-first research system that continuously monitors global
Industrial AI / Manufacturing AI technology, collects and classifies public
research, analyzes it, accumulates it as structured knowledge, actively
looks for technology in *other* industries that could transfer to
**Battery Manufacturing**, and tracks the user's own Industrial AI skill
growth.

This is a personal learning/research tool. It only ever touches public
sources (arXiv, RSS, GitHub) or research material the user supplies
directly — never a company network, company data, or confidential
information.

```
Research -> Knowledge -> Insight -> Learning -> Experiment -> Skill Growth
```

## Purpose

Continuously answer:

1. What changed in Industrial AI?
2. What matters for Battery Manufacturing?
3. What technologies are emerging?
4. What technologies from other industries could transfer to Battery
   Manufacturing?
5. What should I research deeply?
6. What should I learn next?
7. What experiments should I try?

## Architecture

```
CLI -> Research Pipeline -> Agents -> ModelGateway -> ModelRouter -> ProviderAdapter
                          -> Collectors -> Processing (normalize/dedupe/classify/extract)
                          -> SQLite (documents, scores, transfer_opportunities,
                                     knowledge graph, skill graph, llm_runs, ...)
```

Full detail: `docs/architecture.md`. Also see `docs/model-routing.md`,
`docs/local-llm.md`, `docs/research-pipeline.md`, `docs/transfer-radar.md`,
`docs/knowledge-graph.md`, `docs/skill-graph.md`, `docs/troubleshooting.md`.

## Hardware

Designed for a home PC with no CUDA GPU and limited VRAM:

| | |
|---|---|
| CPU | AMD Ryzen 5 8500G (6c/12t) |
| RAM | 16 GB DDR5 (32 GB upgrade planned) |
| GPU | AMD Radeon RX 6600, 8 GB VRAM |
| OS | Windows 11 |

Local inference is optional and abstracted (Ollama today; llama.cpp/vLLM
are documented extension points) — the whole pipeline runs on CPU-only
rule-based fallback if no local or cloud model is configured at all. See
`docs/environment.md` for the full Phase 0 inspection, including of the
cloud container this project was originally built in.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
cp .env.example .env             # optional: add ANTHROPIC_API_KEY etc.
research-os init
```

Windows convenience script: `scripts/setup.ps1`.

## Configuration

Everything tunable lives in `config/*.yaml` — no model name, taxonomy, or
scoring weight is hardcoded in Python:

| File | Controls |
|---|---|
| `system.yaml` | paths, logging, enabled sources, privacy defaults |
| `industries.yaml` / `technologies.yaml` / `problems.yaml` | taxonomies |
| `battery.yaml` | Battery Manufacturing process/equipment taxonomy |
| `models.yaml` | model tiers, provider bindings, fallback/escalation chains |
| `routing.yaml` | agent → model tier default policy |
| `agents.yaml` | agent registry (enable/disable, description) |
| `scoring.yaml` | scoring weights and priority thresholds |

## Local LLM

Ollama-based (`research_os/models/local.py`). `research-os evaluate` runs
a real benchmark (6 fixed tasks x whatever models `ollama list` shows) and
writes `data/reports/model-benchmark.md`; `research-os benchmark-apply`
then writes the winning model per role into `config/models.yaml`. See
`docs/local-llm.md` — including which parts of this were verified in this
build environment (no GPU/Ollama here) versus what's pending a run on the
target PC.

## Cloud LLM

Anthropic (fully implemented via the SDK), OpenAI and Google (REST-based
adapters, ready for a key) — see `docs/model-routing.md`. Set the relevant
`*_API_KEY` in `.env`.

## Model Router

`Agent -> ModelGateway -> ModelRouter -> ProviderAdapter`. The router picks
a tier from task type/complexity/importance/privacy and the agent's default
policy; the gateway walks a fallback chain (local → cloud) and logs every
attempt to the `llm_runs` table. Full detail: `docs/model-routing.md`.

## CLI

```
research-os init                          # create DB, seed taxonomies + skill tree
research-os status                        # environment / DB / LLM / KG / skill summary
research-os models                        # configured tiers + live availability
research-os collect [--source arxiv|rss|github]
research-os classify / summarize / analyze / transfer   # run one pipeline stage
research-os run [--no-llm]                # full pipeline: collect -> ... -> store
research-os report daily [--no-llm]
research-os report weekly [--no-llm]
research-os research "topic" [--no-llm]   # deep research grounded in the local DB
research-os evaluate                      # Local LLM Benchmark -> data/reports/model-benchmark.md
research-os benchmark-apply               # write the benchmark's role picks into config/models.yaml
research-os skills                        # Personal Skill Graph
```

## Research Pipeline

```
COLLECT -> NORMALIZE -> DEDUPLICATE -> CLASSIFY -> SUMMARIZE -> ANALYZE
  (battery relevance, evidence/practical/novelty, score) -> TRANSFER ANALYSIS
  -> STORE -> REPORT
```

Each stage is independently runnable and idempotent. Details:
`docs/research-pipeline.md`. The Cross-Industry Technology Transfer Radar
(the project's core differentiator) is documented in
`docs/transfer-radar.md`.

## Knowledge Graph

SQLite-backed (`knowledge_nodes`/`knowledge_edges`), populated
automatically as documents are analyzed. `docs/knowledge-graph.md`.

## Skill Graph

Tracks the user's own Industrial AI capability per topic (0 Unknown → 5 Can
Teach). `research-os skills`. `docs/skill-graph.md`.

## Testing

```bash
pytest
ruff check src tests
```

79 tests cover configuration, schema/normalization, deduplication,
scoring, the model router, the model gateway's fallback chain and response
cache, the arXiv collector (mocked HTTP), the Ollama adapter's model/version
discovery, every agent's non-LLM fallback path, the knowledge graph, the
skill graph, the local LLM benchmark and scoring heuristics (mocked
Ollama backend), the `config/models.yaml` auto-update, and a full offline
pipeline integration test (collect → classify → summarize → analyze →
transfer → store).

## Troubleshooting

`docs/troubleshooting.md`.

## Roadmap

- **Phase 1 (this build): working MVP** — arXiv collection, full pipeline,
  ModelGateway/Router with local+cloud adapters and fallback, CLI, tests.
- **Phase 2**: GitHub + RSS collectors are already implemented but
  disabled by default (`config/system.yaml`); TrendAgent; richer daily/
  weekly reports.
- **Phase 3**: Knowledge Graph expansion (Process/Equipment/Sensor/Signal
  nodes), Skill Graph recommendations, benchmark-driven ModelRouter.
- **Phase 4**: Deeper multi-source Deep Research synthesis with tracked
  evidence chains.
- **Phase 5**: Scheduled automation (Windows Task Scheduler) once manual
  pipeline runs are stable.
- **Phase 6**: FastAPI + web UI, search, dashboards, graph visualization —
  intentionally deferred; Phase 1 spends no time on UI.
