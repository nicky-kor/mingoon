# Local LLM Setup + Benchmark

## Status: verified on the real PC ✅

The benchmark kit below was built in a cloud sandbox that couldn't run
Ollama itself (see "Where this actually runs"). It has since been run for
real on the target PC and the results are in `config/models.yaml`:

| Hardware (measured, not assumed) | |
|---|---|
| CPU | AMD64 Family 25 Model 120 (12 logical cores) — matches Ryzen 5 8500G |
| RAM | 15.1 GB |
| OS | Windows 11 |
| Ollama | 0.34.0, installed and running |

**Round 1 (2 models: qwen2.5:3b-instruct, qwen2.5:7b-instruct):**

| Role | Model | Quality | Korean | Latency | Composite |
|---|---|---|---|---|---|
| `local_fast` | `qwen2.5:3b-instruct` | 94 | 90 | 4931 ms | **84** |
| `local_standard` | `qwen2.5:7b-instruct` | 97 | 88 | 7394 ms | 82 |
| `local_reasoning` | `qwen2.5:7b-instruct` | 97 | 88 | 7394 ms | 82 |

The 3B model won `local_fast` on speed despite slightly lower raw quality
(the composite score weights latency); the 7B model won `local_standard`/
`local_reasoning` on quality — exactly the split the design intended.

**Round 2 (added deepseek-r1:7b as a dedicated reasoning candidate):**

First attempt gave deepseek-r1:7b quality=17, korean=0, stability=30% —
looking broken. It wasn't the model; it was the benchmark: a 400-token
cap and Ollama's default 60s timeout starved a model that emits a long
`<think>...</think>` trace before its actual answer (some of its 6 calls
plausibly timed out before ever finishing). Fixed by raising the (same
for every model) token budget to 1500 and the benchmark's timeout to
180s, and stripping `<think>` blocks before scoring
(`evaluation/scoring.strip_reasoning_preamble`) — see commit `42ef001`.
Re-run with the fix:

| Model | Role won | Quality | Korean | Latency | Composite |
|---|---|---|---|---|---|
| `deepseek-r1:7b` | *(none)* | 78 | **0** | 21982 ms | 53 |
| `qwen2.5:7b-instruct` | local_standard, local_reasoning | 100 | 89 | 8319 ms | **82** |
| `qwen2.5:3b-instruct` | local_fast | 93 | 99 | 5061 ms | **84** |

Quality/stability recovered dramatically once the harness was fair
(17→78, 30%→100%) — confirming it really was a benchmark bug, not the
model. But `deepseek-r1:7b` still doesn't win any role here: it answered
the Korean-summary task in English (korean_quality=0 — a known trait of
some R1 distillations on non-English prompts) and is 3-4x slower than
either qwen2.5 model. For *this* project's actual workload (Korean +
English industrial-AI research assistant tasks), `qwen2.5:7b-instruct`
remains the better `local_reasoning` choice despite being the "general"
rather than "reasoning-branded" model — `config/models.yaml` is
unchanged from Round 1 (`benchmark-apply` confirmed "already matches").

Full reports: `data/reports/model-benchmark.md` on that machine (each
`evaluate` run overwrites it — the numbers above are what each run
printed to the console at the time). `pytest` — 112/112 passing on
Python 3.14.7, the PC's actual interpreter version (a `datetime.utcnow()`
deprecation surfaced by that newer Python was found and fixed along the
way — see `docs/autonomous-session-report.md`).

Cloud tiers are still unverified (`ANTHROPIC_API_KEY` not set on that
machine).

## Where this actually runs

This session (Claude Code on the web) executes in a cloud Linux
container, **not** on the target Windows PC. That container has no GPU
and no Ollama, and its network egress is blocked for both
`export.arxiv.org` and `ollama.com` by organization policy (confirmed via
`curl`/`WebFetch` — see `docs/environment.md`). So none of the
hardware-dependent steps below (installing Ollama, pulling models,
running real inference, measuring real VRAM) could be executed *from this
session*. What was built instead is a **local execution kit**: all the
code, benchmark dataset, scoring, and reporting needed to run a real
benchmark, verified end-to-end here with a mocked Ollama backend
(`tests/test_local_benchmark.py`) — the actual numbers must come from
running it on the real PC.

```
research-os evaluate
```

run on this container right now produces an honest, non-fabricated
result:

```
Ollama installed: NO — see Limitations
...
## Best Model for local_fast
- UNKNOWN / BLOCKED — no model was actually benchmarked for this role.
```

That is the correct output when no local model has actually been run —
not a bug. See "Run it on the real PC" below for what changes once this
runs where Ollama and the RX 6600 actually exist.

## Backend

One local backend is implemented: **Ollama**, via its HTTP API
(`research_os/models/local.py`, `OllamaAdapter`). It never downloads or
assumes a specific model — `OllamaAdapter.list_models()` calls Ollama's
own `/api/tags` (what `ollama list` shows) and the benchmark only ever
tests models that are already pulled. llama.cpp and vLLM are named in the
spec as future backends behind the same `ProviderAdapter` interface —
not implemented, since there's nothing to validate the need for them
against yet (spec: "don't overengineer").

## Why Ollama first, on this hardware

Target PC: Ryzen 5 8500G, RX 6600 8 GB VRAM, 16 GB RAM, Windows 11, no
CUDA. Ollama runs on Windows, has the widest model catalog of the three
named backends, and falls back to CPU automatically when a model doesn't
fit in VRAM.

## Installing and checking (run this on the actual PC)

```powershell
# https://ollama.com/download
ollama --version
ollama serve            # if it isn't already running as a service
ollama list              # should run without error, even if empty
```

`research-os status` / `research-os models` call `OllamaAdapter.is_available()`
(a 3s-timeout GET to `/api/tags`) and `OllamaAdapter.get_version()` (GET
`/api/version`) — both real checks, not assumptions. If `ollama --version`
works but `research-os models` still says unreachable, `ollama serve`
likely isn't running, or `OLLAMA_BASE_URL` in `.env` doesn't match where
it's listening.

## Model candidates (verify before pulling — not live-checked)

`ollama.com/library` could not be browsed from this session (egress
blocked), so this list is drawn from general knowledge of Ollama's
catalog as of this project's training data, **not a live check**. Confirm
each name still resolves (`ollama pull <name>` will simply fail loudly if
not) before relying on it:

| Family | Candidate | Class | Notes |
|---|---|---|---|
| Qwen | `qwen2.5:3b-instruct` | 3B | current `local_fast` default in `config/models.yaml` |
| Qwen | `qwen2.5:7b-instruct` | 7B | current `local_standard` default |
| DeepSeek | `deepseek-r1:7b` (or a distilled variant) | 7B, reasoning-oriented | current `local_reasoning` default |
| Gemma | `gemma2:2b` / `gemma2:9b` | 2B / 9B | worth benchmarking as an alternative to Qwen |
| Embedding | `nomic-embed-text` | small | not yet used by any agent (Phase 3) |

**Do not pull all of these at once.** Per spec: start with the smallest
(3B class), confirm it runs, benchmark it, then decide whether a bigger
model is worth the disk/VRAM budget. A 7-8B instruct model, Q4-quantized,
is roughly 4-5 GB on disk — comfortably fits the 8 GB VRAM target if
nothing else is competing for it, but leaves little headroom, so measure
before assuming.

## Run it on the real PC

```powershell
cd manufacturing-ai-research-os
research-os init                          # once
ollama pull qwen2.5:3b-instruct           # smallest candidate first
research-os evaluate                       # runs the real benchmark
```

`research-os evaluate` (`research_os/evaluation/local_benchmark.py`):

1. Discovers installed models via `OllamaAdapter.list_models()`.
2. Runs the 6 fixed prompt tasks from `evaluation/prompts.py` — exact same
   prompt text for every model, so results are comparable — against the
   matching case from the 10-item dataset in `evaluation/dataset.py`
   (spec section 7; each dataset case states its real source or is
   labeled `synthetic` when it's a representative test case this project
   wrote, never a fabricated citation).
3. Scores each response with the heuristics in `evaluation/scoring.py`
   (JSON-schema validity, whether returned industry/technology/problem
   values are real keys from this project's own taxonomy — not
   hallucinated categories, Korean-character ratio, response
   length/structure) — **automated proxies, not human grading**.
4. Measures latency for real, and RAM/VRAM/disk size best-effort
   (`core/resource_probe.py` — returns `None`/`UNKNOWN` rather than a
   guess when a tool like `nvidia-smi`/`rocm-smi` isn't available; on the
   RX 6600 this likely means VRAM stays UNKNOWN unless ROCm tooling is
   installed — that's expected and reported honestly, not treated as 0).
5. Computes a weighted composite score per spec section 10 (Quality 30%,
   Technical accuracy 20%, Korean quality 15%, Latency 15%, Resource
   efficiency 10%, Stability 10% — re-normalized over whatever was
   actually measured).
6. Recommends `local_fast`/`local_standard`/`local_reasoning` from the
   real results and writes everything to
   `data/reports/model-benchmark.md` (exact structure: Hardware, Models
   Tested, Benchmark Tasks, Results table, Best Model per role,
   Recommended Configuration, Limitations, Next Benchmark).
7. Persists every task run and a per-model aggregate row to the
   `model_benchmarks` table.

Then, once you're happy with the recommendation:

```powershell
research-os benchmark-apply
```

reads the latest aggregate benchmark rows from the database and edits
only the `model:` line inside the matching `local_fast`/`local_standard`/
`local_reasoning` blocks of `config/models.yaml` — a targeted text edit,
not a full YAML re-dump, so comments and every other tier (cloud tiers
included) are left untouched. Nothing is changed automatically by
`evaluate` itself; `benchmark-apply` is a separate, explicit step.

## Caching and repeat calls

`ModelGateway` caches every (provider, model, prompt, system, max_tokens,
temperature) combination in the `llm_cache` table (spec section 15) — an
identical call is never re-sent to a model. The benchmark runner bypasses
this (`use_cache` isn't set on benchmark calls) since fresh timing is the
point; normal agent traffic uses it automatically.

## What happens with no local model at all

Every stage that would call a `local_*` tier fails over to its configured
cloud tier (`config/models.yaml` `fallback`), and if no cloud key is
configured either, every agent has a deterministic non-LLM fallback (see
`docs/architecture.md`). Both paths were verified end-to-end during
Phase 1 development in an environment with neither Ollama nor a cloud key
available.

## Known limitations of this benchmark design

- Scoring is heuristic/automated, not human-graded — treat the composite
  score as a first filter, not a final verdict; read a few raw responses
  before trusting a close call.
- The dataset is 10 fixed cases; a model tuned to this exact prompt style
  could look better than it is in general use. Expand
  `evaluation/dataset.py` if a role selection feels off in practice.
- VRAM is genuinely hard to measure for an AMD GPU without ROCm tooling
  installed — expect `UNKNOWN` there on a stock Windows+Ollama setup
  unless `rocm-smi` (or equivalent) is present.
