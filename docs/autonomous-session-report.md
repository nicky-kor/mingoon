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

## Round 4: Verified on the real PC ✅

Everything "Blocked" above has since been done, live, on the user's
actual machine, in the same conversation (guided step-by-step: PowerShell
selection → Python not on PATH → PowerShell execution-policy blocked venv
activation, worked around via a global-Python PATH fix → Ollama already
installed (0.34.0) → pulled `qwen2.5:3b-instruct`, then
`qwen2.5:7b-instruct` → `research-os evaluate` → `research-os
benchmark-apply` → `pytest`).

Real results (see `docs/local-llm.md`'s new "Status: verified on the real
PC" section for the full table): CPU/RAM/OS matched the target spec
exactly; `local_fast` → `qwen2.5:3b-instruct` (composite 84, won on
latency); `local_standard`/`local_reasoning` → `qwen2.5:7b-instruct`
(composite 82, won on quality) — the fast/quality split the benchmark
design intended, confirmed with real inference rather than the mocked
backend. `config/models.yaml` was updated by `benchmark-apply` itself
(only the `local_reasoning` line actually changed).

Along the way, running the real test suite on the PC's actual Python
3.14.7 (this project was built/tested against 3.11.15) surfaced a
`datetime.utcnow()` DeprecationWarning (67 occurrences across the test
output) that hadn't shown up in the sandbox's older Python — fixed in
commit `42e9037` (see "Bugs Fixed" above) and reverified on the PC:
`pytest` went from 106 passed/67 warnings to **107 passed/0 warnings**.

Remaining, not yet done (optional, not blocking): verifying the cloud
fallback tiers with a real `ANTHROPIC_API_KEY`.

## Round 5: deepseek-r1:7b added, and a real benchmark-fairness bug found

At the user's request, `deepseek-r1:7b` was pulled and benchmarked
against the two qwen2.5 models as a dedicated reasoning candidate. First
attempt: quality=17, korean=0, stability=30%, won no role — looking like
a broken/bad model. It wasn't the model; the benchmark harness was unfair
to it: a 400-token cap and Ollama's default 60s timeout starved a model
that emits a long `<think>...</think>` trace before its actual answer
(consistent with ~2/6 calls plausibly timing out outright, matching the
30% stability).

Fixed in commit `42ef001`: raised the token budget (400 → 1500) and the
benchmark's HTTP timeout (60s → 180s) uniformly for every model (still
fair — same generous budget for all, not special-cased for one), and
added `evaluation/scoring.strip_reasoning_preamble()` to strip
`<think>...</think>` before scoring so a model is judged on its answer,
not penalized for showing its work. Added a regression test asserting a
`<think>`-wrapped answer scores identically to the same answer without
the wrapping (112 tests total, up from 107).

Re-run on the PC with the fix: `deepseek-r1:7b` recovered to quality=78,
stability=100% (confirming the harness was the problem) but still won no
role — it answered the Korean task in English (korean_quality=0, a known
trait of some R1 distillations on non-English prompts) and is 3-4x
slower than either qwen2.5 model. Real conclusion, not a benchmark
artifact this time: `qwen2.5:7b-instruct` genuinely is the better
`local_reasoning` choice for this project's actual (Korean+English)
workload, despite `deepseek-r1:7b`'s "reasoning" branding.
`config/models.yaml` is unchanged (`benchmark-apply` confirmed "already
matches"). `pytest`: 112/112 passing on the PC, 0 warnings.

Full detail and the exact before/after numbers: `docs/local-llm.md`'s
"Round 2" section.

## Round 6: Cost-safety, agent review, QA, Korean sources, self-audit

Chain of requests, same session: cloud credit ran out mid-testing → "check
credit automatically, use local if none" → 8-agent overlap review → "build
the QA agent you flagged but skipped" → "search out Korean academic
societies and news/blogs too" → user stepped away, asked for a self-audit
+ continuity write-up + automation draft + UI proposal while unattended.

### Provider circuit breaker (automatic cost safety, no manual toggle)

`ANTHROPIC_API_KEY` ran out of credit mid-session. The first fix was a
manual `config/routing.yaml` edit (reasoning agents → local tiers); the
user explicitly asked for something that didn't require editing config by
hand every time credit ran out or was topped up. Built:

- `database/models.py`: new `ProviderCircuitBreaker` table
  (provider/tripped_until/reason/tripped_at) — persisted, not in-memory,
  since every `research-os` invocation is a fresh process.
- `models/circuit_breaker.py`: `is_unrecoverable_failure()` recognizes
  billing/auth error text (credit balance too low, insufficient_quota,
  invalid api key, authentication_error) — deliberately NOT timeouts or
  plain rate limits, which often resolve on the very next call.
  `trip()`/`is_tripped()`/`clear()`/`list_active()` manage the row with a
  1-hour default cooldown after which cloud is retried automatically.
- `models/gateway.py`: checks the breaker before calling each tier's
  adapter (skips a tripped provider without wasting a call) and trips it
  on an unrecoverable `ModelUnavailableError`.
- `config/routing.yaml` reverted to cloud-first defaults for reasoning
  agents (better quality when usable); `config/models.yaml`'s fallback
  chains extended so `cloud_reasoning`/`cloud_deep_research` both
  eventually reach `local_reasoning` — without this the breaker would
  skip past both cloud tiers (same provider) and never actually land on
  a free local model.
- **Verified live on the PC**: a real "credit balance is too low" error
  tripped the breaker and the very next call skipped straight to local
  with zero additional Anthropic calls.

### 8-agent review: two real overlap/gap findings, fixed

Reviewed all 8 agents' actual code (not just descriptions) for duplicated
work and unmet responsibilities, at the user's request. Found and fixed:

1. **TransferAgent re-derived what ClassifierAgent already computed.**
   Both called `classify_battery_process(title, abstract)` independently
   — nothing reconciled `doc.target_process` (Classifier) against
   `doc.candidate_process` (Transfer), so they could silently disagree on
   the same document. Fixed: TransferAgent now reuses `item.target_process`
   when set, and passes it to the LLM as an anchor hint.
2. **TrendAgent's stated purpose ("recurring/emerging technologies and
   shifting research direction") wasn't actually implemented** — it only
   counted one fixed window, so "emerging" had no real signal; the weekly
   report approximated it with `count == 1`, which is wrong in both
   directions. Fixed: real period-over-period comparison
   (`rising_technologies`/`new_technologies` vs. the immediately
   preceding window of the same length).
   Also removed the dead `TrendAgent: local_standard` routing entry —
   TrendAgent never calls `ModelGateway` at all (deterministic counts are
   more trustworthy than an LLM here), so the config entry was misleading.

No true duplicate agents found otherwise — the 8 (now 9) map cleanly to
distinct pipeline stages. Noted but deliberately not touched: Briefing/
Research agents share a similar "don't invent facts" prompt pattern
(cosmetic duplication, not a functional bug).

### QAAgent — the gap flagged above, built on request

A 9th agent whose only job is catching the other LLM-backed agents
inventing something not in the source text:

- `agents/qa.py`: compares every percentage-style figure in a document's
  generated fields (summary/limitations/expected_benefit/risk/
  key_findings) against the percentages in its own title+abstract,
  flagging anything unsupported. Also flags an empty summary and
  evidence/practical/novelty scores that are all identically 0 or 100
  (a common sign of a generic non-answer). Deliberately percentage-only,
  not bare-number matching (years/counts would drown the signal), and
  deliberately has no LLM call of its own (checking a hallucination with
  a second LLM call trades one hallucination-prone step for two, at
  double the cost, for no stronger guarantee). Flags, never blocks.
- New `qa_status`/`qa_flags` columns on `Document`/`ResearchItem`, a
  `run_qa_check()` pipeline stage between transfer and mark_analyzed, a
  `research-os qa` CLI command, a "QA Flags" section in both reports, and
  a QA-flagged count in `research-os status`.
- **Building this surfaced a real, separate bug**: `_document_to_item()`
  only ever round-tripped the handful of fields the classify stage
  needed — `target_process`, `summary`, all the scores, etc. set by
  earlier stages were silently `None` whenever a later stage (transfer,
  and now qa) read them back from the DB in the real pipeline. This
  meant the TransferAgent fix above never actually took effect end-to-end
  despite passing its own unit test (which constructs `ResearchItem`
  directly, bypassing the DB round-trip). Fixed by round-tripping every
  generated field, not just the original subset.

### A second real bug, found dogfooding on the PC: DB migration

After pulling the QAAgent commit, `research-os run` against the PC's
existing DB file crashed with `no such column: documents.qa_status`.
`init_db()` only ever called `Base.metadata.create_all()`, which creates
whole tables that don't exist yet (fine for the new
`provider_circuit_breaker` table) but is a silent no-op for a column
added to a table that already exists on disk. Fixed: `init_db()` now
also inspects each pre-existing table and `ALTER TABLE ... ADD COLUMN`s
anything the model declares that the live table is missing. This will
keep mattering for every future column addition, not just this one.

### Sources: RSS/GitHub enabled, Korean academic societies, news/blogs

arXiv's own rate limiting (429, unrelated to any of this session's code)
left the DB with nothing to test the pipeline against, prompting a wider
push on sources:

- `rss`/`github` flipped from disabled to enabled in `config/system.yaml`
  — both were already fully implemented in Phase 1, just waiting for
  real feed URLs/topics. RSS feeds added: MIT News AI, IEEE Spectrum AI,
  ScienceDaily AI (all *news*, not journals — worth noting since the
  user specifically asked why coverage looked papers-only), Nature
  Machine Intelligence (journal), 전자신문 (Korean tech news), NVIDIA's
  industrial/manufacturing blog tag feed (URL pattern inferred from a
  confirmed sibling feed, not independently fetched — flag for PC-side
  confirmation).
- **Two new dedicated collectors for Korean academic societies that
  publish no RSS**: `collectors/kiie.py` (대한산업공학회 — reads the
  homepage's own "Announcements" widget rather than the full unconfirmed
  ASP board) and `collectors/ksphm.py` (한국PHM학회 — scrapes the actual
  `/info/notice.php` list page, handling its EUC-KR encoding, "YY.MM.DD"
  dates, and a nested-table row structure that requires
  `recursive=False` to avoid double-counting rows). Both built from real
  page source the user pasted in (this sandbox has no general web
  access — confirmed blocked even for google.com, so live fetching for
  scraper-writing purposes had to route through the user pasting
  view-source HTML, same as the earlier arXiv work routed through PC
  dogfooding for anything needing real network access).
- **KSMA (한국제조데이터인공지능학회)** — despite matching this project's
  subject matter most directly of any candidate source, its `/notice`
  page currently has zero posted items (confirmed by the user); skipped
  for now, structure (Next.js + Supabase) already scoped for whenever it
  has content.
- Remaining candidates from a longer list the user provided (한국생산제조
  학회, 한국경영과학회, 한국품질경영학회, 한국소음진동공학회, 대한기계학회,
  제어·로봇·시스템학회, 대한전기학회, 한국정보과학회) are not yet started —
  each would need the same "paste the real page source" treatment before
  a working scraper could be written.

### Self-audit (this round, unattended)

Read through effectively the entire `src/research_os` tree end-to-end
looking for missed items or over-engineering. Findings:
- No correctness bugs beyond the two already fixed above.
- `Source`, `DocumentTag`, `SkillEvidence`, `Report` DB tables are
  defined but never read/written by any code path — this is intentional
  documented pre-scaffolding ("later phases populate these," per
  `database/models.py`'s own module docstring), not a bug. Worth
  reconsidering now that `init_db()` auto-migrates columns (the original
  "avoid migration churn" rationale for scaffolding tables this early is
  weaker than it was), but not urgent.
- Deliberate restraint confirmed as still appropriate, not
  under-building: knowledge graph is SQLite-only rather than a graph DB
  (spec section 61, "don't overengineer"); local inference targets only
  Ollama, not llama.cpp/vLLM yet, both explicitly documented as
  intentional rather than incomplete.
- Fixed in passing: stale `cli.py` `--source` help text (didn't list
  `kiie`/`ksphm`), README's roadmap (still described Phase 2 items as
  future when they're done) and test count (79 → 150), cli.py import
  ordering.
- Wrote `docs/automation.md` (Windows Task Scheduler plan + script for
  scheduled `research-os run`/`report daily`/`report weekly`, plus a
  comparison of ways to actually see the weekly report without opening
  the reports folder — synced cloud folder, email, Notion, Slack/Discord,
  a published Claude Artifact, and — per the user's specific follow-up —
  Naver Blog/Facebook/Instagram, ranked by setup effort vs. fit for this
  content) and `docs/ui-proposal.md` (a Phase 6 dashboard plan: screens
  in priority order — dashboard, document list/detail, Transfer Radar,
  trends, skills, ad-hoc research — a recommended FastAPI-over-existing-
  models stack, and an explicit "what not to build" section). Neither
  changes running behavior; both are planning documents for later phases.

### Tests

165 passing at the end of this round (up from 132 at Round 5), 0 failing,
`ruff check` clean throughout. New coverage this round: circuit breaker
(heuristic matching, trip/clear/cooldown, gateway integration proving a
tripped provider is skipped without an adapter call), the 8-agent-review
fixes (TrendAgent rising/new-technology detection, TransferAgent
target_process reuse through the real DB round-trip), QAAgent (clean
pass, fabricated-percentage detection in two different fields, empty
summary, generic-score detection), the DB auto-migration
(pre-existing-table column addition), all four new/newly-enabled
collectors (RSS's existing tests already covered the mechanism; KIIE/
KSPHM got dedicated fixture-based tests from real page source),
ResearchAgent's score-based ranking (this agent had no tests at all
before this round), and the cost-saving cascade (`test_grounding.py`,
`test_cascade.py`, a `force_tier` gateway test).

### OSS survey: research-agent & model-routing patterns

At the user's specific follow-up request ("리서치 관련 에이젼트는 github에도
여러 엔지니어가 작업해놓을게 많을거야" / "search out useful model-routing
patterns too"), surveyed comparable open-source projects — full writeup
in `docs/oss-research-notes.md`. No code copied from any of them.

- **Applied**: `ResearchAgent.search()` now ranks keyword matches by
  `Score.overall_score` (AnalystAgent's own quality score) instead of
  arbitrary DB order, matching a pattern common to gpt-researcher/
  deep-research-agent (rank sources by a credibility signal before
  synthesis) — we already compute that signal, it just wasn't wired into
  the ordering. New `tests/test_researcher_agent.py` (this agent had no
  dedicated tests before).
- **Validated, not changed**: LiteLLM's "cooldown" feature is the same
  pattern as this session's own circuit breaker — independent convergence
  on the same idea as a 14k+-star project is a good sign, not something
  to replace with a new dependency for just 4 provider adapters.
  `config/models.yaml`'s own documented Phase-3 escalation extension
  point matches RouteLLM's core idea (classifier-based difficulty
  routing) — confirms the deferral was the right call, nothing to change.
- **Flagged for the user's review, then implemented on their explicit
  go-ahead** ("품질은 동일하고 비용은 적게 든다면 진행"): a FrugalGPT-style
  cascade where a grounding check triggers escalation from local to
  cloud. Built as `core/grounding.py` (percentage-matching, shared with
  `agents/qa.py`, refactored to use it — no behavior change there) +
  `models/cascade.py` (`generate_with_cascade()`, plus a new
  `force_tier` parameter on `ModelGateway.generate()` to bypass normal
  routing for the cheap attempt) + wiring into all four reasoning-heavy
  agents (Analyst/Transfer/Research/Briefing), each passing its own
  source text as the grounding reference. Toggle:
  `config/routing.yaml`'s `cost_cascade` block. The quality caveat was
  stated plainly before implementing, not glossed over: passing the
  grounding check means "no fabricated percentage," not "as good as
  cloud" — `run_qa_check()` still runs the full check afterward on
  whichever tier actually answered, regardless of which path this
  cascade took, so the safety net stays in place either way. Verified
  manually with fake local/cloud adapters (fresh DB per case, after an
  initial false pass caused by the two test cases sharing an LLM-cache
  key — a manual-test artifact, not a cascade bug): a clean local answer
  skips the cloud adapter entirely; a fabricated-percentage local answer
  correctly escalates and returns the cloud answer instead.

### What's still open (not started, or deliberately deferred)

- 8 of the 10 Korean-society sources the user listed (see above).
- Automation (`docs/automation.md`) and UI (`docs/ui-proposal.md`) are
  plans, not implementations — nothing scheduled or built yet.
- Weekly report sharing (email/Notion/blog/social) — not implemented,
  pending a decision on which channel(s) actually matter.
- NVIDIA blog feed URL not independently verified from this session.
