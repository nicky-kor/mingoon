# Autonomous Development Session

Three chained requests handled without further user input:
1. "Local LLM Setup + Benchmark" — build the tooling to select
   `local_fast`/`local_standard`/`local_reasoning` from real Ollama
   benchmarks.
2. An explicit autonomous-session instruction to audit, stabilize, test,
   and document the current state while the user was away.
3. "스스로 더 할건 없어?" (anything else you can do yourself?) — closed
   out the audit checklist items skipped in round 2 (RSS/GitHub collector
   tests, CLI wiring tests, config consistency checks) and found a real
   bug in the process; see "Round 3" below.

## Completed

- **Local LLM benchmark kit** (spec: LOCAL LLM SETUP + BENCHMARK TASK),
  fully implemented and unit-tested, ready to run for real on the target
  PC:
  - `evaluation/dataset.py` — 10 benchmark cases across the required
    categories; real public abstracts cited by arXiv ID where used
    (1706.03762, 2010.11929), everything else explicitly labeled
    `synthetic` rather than attributed to an invented paper.
  - `evaluation/prompts.py` — the 6 fixed prompt templates from the spec,
    identical wording for every model.
  - `evaluation/scoring.py` — automated heuristic scoring (JSON-schema
    validity, taxonomy-key correctness against this project's own
    config, Korean-character ratio, response structure), latency/
    resource/stability scoring, and the weighted composite (30/20/15/15/
    10/10 per spec section 10, re-normalized over whatever was actually
    measured).
  - `evaluation/local_benchmark.py` — discovers installed models via
    `OllamaAdapter.list_models()` (never assumes a model name), runs all
    6 tasks per model, persists results to `model_benchmarks`, selects
    per-role winners, renders the exact report structure the spec asked
    for.
  - `evaluation/apply_config.py` — `research-os benchmark-apply`: edits
    only the matching `model:` lines in `config/models.yaml` (regex
    substitution, not a YAML re-dump), so comments and untouched tiers
    survive.
  - `core/resource_probe.py` — best-effort, dependency-free RAM (Windows
    `tasklist` / POSIX `ps`) and VRAM (`nvidia-smi`/`rocm-smi`) probing;
    returns `None` rather than a guess when unmeasurable.
  - `models/cache.py` + `ModelGateway` wiring — LLM response cache (spec
    section 15), new `llm_cache` table; `LLMRun`/`ModelBenchmark` gained
    `ram_usage_mb`/`vram_usage_mb`/`cache_hit` columns (spec section 16).
  - CLI: `research-os evaluate` now runs this real benchmark (plus a
    cloud-tier availability smoke test); new `research-os benchmark-apply`.
- **Codebase audit**: grepped for TODO/FIXME/placeholder markers and
  hardcoded model name strings in `src/` — none found outside docstrings
  and log messages (all actual model selection still flows through
  `config/models.yaml`).
- **Documentation refreshed** to match the current code:
  `docs/local-llm.md` (full rewrite around the new benchmark kit and an
  explicit "what was/wasn't verified here" section), `docs/environment.md`
  (added this session's re-confirmation of the network/hardware
  constraints), `docs/architecture.md` (cache + resource probe),
  `docs/troubleshooting.md` (new BLOCKED-output guidance), `README.md`
  (CLI list, test count, Local LLM section).

## Tests

- 40 → 79 → **106 passing**, 0 failing (`pytest`, full suite in ~2s).
  New coverage: LLM cache (hit/miss, gateway integration), resource probe
  (never raises, returns `None` when unmeasurable), benchmark
  dataset/prompts, all scoring heuristics, the full local benchmark flow
  against a mocked Ollama backend (blocked-when-unavailable,
  blocked-when-no-models, and a successful end-to-end run), Ollama
  model/version discovery, `config/models.yaml` auto-update (including
  the no-op and unknown-tier-warning cases), the RSS and GitHub
  collectors (parses correctly, never raises on a network error,
  disabled-by-default stays network-free), the CLI itself via
  `typer.testing.CliRunner` (init/status/models/skills/collect/evaluate/
  benchmark-apply/report), and cross-checks that every tier name
  referenced in `config/routing.yaml`'s agent defaults, rules, and
  `config/models.yaml`'s fallback/escalation chains actually exists.
- `ruff check src tests` — all checks passed.
- Existing Phase 1 tests untouched and still green — nothing was broken.

## Real Internet Validation

- **BLOCKED**: `export.arxiv.org` and `ollama.com` are both blocked by
  this container's egress policy (`curl`/`WebFetch` both return
  `EGRESS_BLOCKED`/403 — see `docs/environment.md`). This is unchanged
  from the Phase 1 session; re-confirmed here rather than assumed.
- Per the task's own instruction ("실제 인터넷 접근이 막혀 있다면 억지로
  우회하지 않는다. BLOCKED로 기록하고 기존 mock test는 계속 유지한다"),
  no workaround was attempted; the existing mock-server-based integration
  test (`tests/test_pipeline_integration.py`, plus the manual mock-server
  run recorded in `docs/environment.md`) remains the standing evidence
  that the collect→...→store pipeline works against a real-shaped feed.
  A fresh manual mock-server run was also repeated this session (arXiv
  Atom fixture on `127.0.0.1:8899`) to confirm the gateway/cache changes
  didn't regress it — collect → classify → summarize → analyze →
  transfer → store → status all matched Phase 1 behavior.

## Local LLM

- **BLOCKED**: no `ollama` binary, no `nvidia-smi`/`rocm-smi` in this
  container. `research-os evaluate` was run for real here and correctly
  reported `Ollama installed: NO` and `UNKNOWN / BLOCKED` for every role
  — this is the honest, spec-required output (spec: "Do not claim success
  unless the model was actually executed on the user's PC. If GPU
  acceleration cannot be verified, mark it as UNKNOWN or BLOCKED rather
  than PASS.").
- What *is* verified: the entire benchmark pipeline (discovery → 6-task
  run → scoring → aggregation → role selection → report → config write)
  works correctly, via `tests/test_local_benchmark.py`'s mocked Ollama
  backend that returns realistic per-task responses.
- **Next step, on the actual PC**: `ollama pull qwen2.5:3b-instruct`,
  then `research-os evaluate`, then `research-os benchmark-apply` — see
  `docs/local-llm.md`.

## Model Router

- Verified the `Agent -> ModelGateway -> ModelRouter -> ProviderAdapter`
  structure is still intact: no agent imports a provider adapter
  directly (checked via grep across `agents/*.py`). Model names remain
  entirely in `config/models.yaml`; the benchmark's role selections are
  applied through `benchmark-apply`'s targeted text edit, never by
  writing a Python literal.
- `ModelGateway.generate()` gained optional `use_cache` and
  `measure_resources` parameters — both default to today's existing
  behavior (`use_cache=True`, `measure_resources=False`) so no existing
  caller's behavior changed; only the local benchmark opts into resource
  measurement.

## Bugs Fixed

- `evaluation/local_benchmark.py` report renderer: the "Benchmark Tasks"
  section listed all 6 tasks as "1." (fixed `f"1. {key}"` instead of an
  incrementing number) — fixed to `enumerate(..., start=1)`.
- **Round 3 (self-audit follow-up):** `ArxivCollector` and
  `GitHubCollector` used `param or cfg.get(...)` to fall back to
  `config/system.yaml` defaults — since an empty list is falsy in Python,
  passing `categories=[]` / `topics=[]` *explicitly* silently fell back
  to the config defaults instead of being honored as "collect nothing".
  `RSSCollector` already used the correct `feeds if feeds is not None
  else ...` pattern. This wasn't reachable from production code
  (`DiscoveryAgent` never passes an explicit empty list), but it was
  caught the moment a test tried to construct
  `GitHubCollector(topics=[])` to verify disabled-by-default behavior —
  that test instead made **10 real, unmocked calls to the live GitHub
  API** (~13s) because it silently used the real 10-topic config list.
  Fixed both to the `is not None` pattern, added the same
  empty-input-returns-`[]` guard `ArxivCollector.collect()` was missing,
  and added a regression test per collector that fails loudly (raises)
  if a network call is made at all when an empty list is passed
  explicitly. Full test suite dropped from ~15s to ~2s once fixed.

## Improvements

- `ModelBenchmark` and `LLMRun` tables extended for the fields the spec's
  benchmark report needs (`category`, `role_hint`-equivalent via
  `fast_task_score`/`reasoning_task_score`, `korean_quality_score`,
  `technical_accuracy_score`, `resource_efficiency_score`,
  `stability_score`, `composite_score`, `ram_usage_mb`, `vram_usage_mb`,
  `disk_size_mb`, `cache_hit`).
- `research-os evaluate`'s output changed from a simple tier-availability
  table to the full spec-shaped "Local LLM Benchmark" report, with the
  original cloud-tier smoke test folded in as a trailing section rather
  than dropped.

## Blocked

- Real Ollama install/model pull/inference/VRAM measurement — requires
  the target Windows PC; not possible from this cloud container (no
  workaround attempted, per the task's own instruction).
- Live verification of the Ollama model-name candidate list against
  `ollama.com/library` — that domain is also egress-blocked here;
  `docs/local-llm.md` states plainly that the candidate list is drawn
  from training knowledge and must be verified with `ollama pull` on the
  real machine, not treated as a live catalog check.

## Recommended Next Step

On the actual Windows PC:

```powershell
git pull origin claude/festive-lovelace-8kb0ku
pip install -e ".[dev]"
ollama pull qwen2.5:3b-instruct
research-os evaluate
research-os benchmark-apply
pytest
```

Then decide, from real numbers, whether a second (7-8B) or third
(reasoning-oriented) candidate is worth the additional VRAM/disk budget
before pulling it — per spec, one model at a time, smallest first.
