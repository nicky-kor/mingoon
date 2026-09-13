# OSS survey: research-agent & model-routing patterns

At the user's request: a look at what other engineers have already built
for (1) "deep research agent" systems and (2) LLM model routing, to see
what's worth adopting here. No code was copied from any of these
projects — everything below is pattern-level comparison plus one small,
low-risk change already applied. Bigger ideas are left for review rather
than implemented, since they'd change default behavior.

## 1. Deep research agents

Looked at: [gpt-researcher](https://github.com/assafelovic/gpt-researcher)
(the most widely used one — planner/execution split, ~20 web sources
crawled in parallel per sub-question, LangGraph DAG), [tarun7r/deep-research-agent](https://github.com/tarun7r/deep-research-agent)
(4 specialized agents, credibility-scored citations),
[aymenfurter/smartrag](https://github.com/aymenfurter/smartrag) (critic +
researcher agents over GraphRAG).

**Important framing difference**: all of these crawl the live web per
query. Our `ResearchAgent` searches an already-curated local database
(spec's own design — public sources are vetted through the
collect→classify→QA pipeline *before* research ever runs against them).
Most of what these projects solve (source discovery, live crawling,
dealing with the open web's noise) isn't our problem at all. Only two
ideas transfer:

| Idea | Applicable here? | Action |
|---|---|---|
| Rank/weight sources by a credibility signal before synthesis, not just keyword match | **Yes, directly** — we already compute this (AnalystAgent's `overall_score`), it just wasn't wired into `ResearchAgent.search()`'s ordering | **Done this session** — `search()` now orders by `Score.overall_score` (unscored docs sort last), with a new test file (`test_researcher_agent.py`, previously no dedicated tests existed for this agent at all) |
| Planner step: decompose the question into sub-questions, search each separately | Maybe, later — meaningful once the local DB is large enough that a single keyword pass under- or over-matches | **Not implemented.** Would mean: LLM call to decompose → N separate `search()` calls → merge/dedupe results → one synthesis call. Adds LLM cost and latency for a benefit that's speculative until the corpus is bigger. Worth revisiting once `research-os research` starts feeling like it's missing obviously-relevant documents in practice, not before. |

Everything else these projects do (live web crawling, PDF/report export
formats, parallel multi-source fetching) doesn't fit this project's
local-first, already-curated-DB design and isn't recommended.

## 2. Model routing

Looked at: [LiteLLM](https://github.com/BerriAI/litellm) (unified gateway
to 100+ provider APIs, with load balancing/retries/**cooldowns**/
fallback), [RouteLLM](https://github.com/lm-sys/RouteLLM) (a trained
classifier decides strong-vs-weak model per prompt, up to 85% cost
reduction at ~95% of top-model quality on benchmarks), [vLLM Semantic
Router](https://github.com/vllm-project/semantic-router) (policy-based
routing on cost/latency/privacy/safety signals), and the cascade idea
behind **FrugalGPT** (try the cheap model first, escalate only if its
answer looks insufficient).

**Validating finding**: LiteLLM's "cooldown" feature is the same pattern
as this project's own circuit breaker (`models/circuit_breaker.py`,
built earlier this session) — remembering a provider failure for a
period instead of retrying immediately. Independently arriving at a
pattern a well-established project (14k+ stars) also uses is a good sign
the design is sound, not that it was missed.

| Idea | Pros | Cons | Recommendation |
|---|---|---|---|
| **Adopt LiteLLM as the provider-call layer** (replace `models/anthropic.py`/`openai.py`/`google.py`/`local.py` with LiteLLM calls) | One dependency handles API-version drift across all providers (e.g. the Anthropic `temperature` signature break this session hit — LiteLLM's maintainers absorb that churn instead of us); built-in retries/load-balancing/cost-tracking for free | New external dependency for a component that's currently ~60 lines per adapter and stable; loses the exact control we have over `ModelUnavailableError` semantics (needed for the circuit breaker's unrecoverable-vs-transient distinction); `ModelRouter`'s policy layer (agent_defaults, task_type rules, privacy-forced-local) still has to be custom on top either way, so this only replaces the adapter layer, not the interesting part | **Skip for now.** Four adapters is not enough code to justify a new dependency; revisit only if a 5th+ provider is added and the adapter-writing itself becomes the bottleneck. |
| **RouteLLM-style trained classifier for difficulty-based escalation** | Could reduce cloud spend further by sending genuinely-simple requests to `local_fast` even when the calling agent's default is a cloud tier | Needs training data (labeled prompt→ideal-tier pairs) this project doesn't have yet; `config/models.yaml`'s own `escalation` map already documents this as a deliberate Phase 3+ extension point, "not wired in automatically yet, to avoid routing on data we haven't collected" | **Already the plan, correctly deferred** — nothing to change now; this survey just confirms the documented Phase-3 direction matches the field's actual best practice, not just this project's guess. |
| **FrugalGPT-style cascade: try local first, escalate to cloud only if the answer looks insufficient** | Cuts cloud spend on the reasoning-heavy agents (Analyst/Transfer/Research/Briefing) that used to default straight to cloud, on any document where the free local tier's answer already holds up. | Percentage-grounding is a narrower check than "as good as cloud" — a weak-but-fabrication-free local answer still gets kept. Doubles calls for any prompt that does get rejected. | **Implemented, at the user's explicit go-ahead** ("품질은 동일하고 비용은 적게 든다면 진행" — proceed if quality holds and cost drops), with the caveat above stated plainly rather than glossed over. See below. |

## Net effect on the codebase (updated after implementation)

- `core/grounding.py`: the percentage-matching logic, shared by
  `agents/qa.py` (unchanged behavior, just refactored to import it) and
  the new cascade below.
- `models/cascade.py`: `generate_with_cascade()` — tries
  `local_reasoning` first when the calling agent is listed in
  `config/routing.yaml`'s new `cost_cascade` block, keeps that answer if
  `is_acceptable(text)` (the caller's grounding check) passes, otherwise
  falls through to the agent's normal (cloud) routing.
  `ModelGateway.generate()` gained a `force_tier` parameter to make the
  "try this exact tier, bypassing the router" call possible.
- Wired into `AnalystAgent`, `TransferAgent`, `ResearchAgent`,
  `BriefingAgent` — each passes its own source text (document
  title+abstract, matched sources, or the facts list) as the grounding
  reference.
- **Quality safety net kept in place, deliberately not removed**: the
  `run_qa_check()` pipeline stage still runs on every stored document
  regardless of which tier answered, so a document that slipped through
  the cascade's lighter pre-check (percentages only, no generic-answer
  detection) still gets the full QAAgent check afterward and can be
  flagged for review.
- Toggle: `config/routing.yaml`'s `cost_cascade.enabled` / `.agents` —
  remove an agent from the list (or set `enabled: false`) to revert to
  always calling the normal tier directly, no code change needed.
- Verified manually end-to-end with fake local/cloud adapters: a clean
  local answer skips the cloud adapter entirely (0 calls); a local
  answer with a fabricated percentage not in the source correctly
  escalates and returns the cloud answer instead.

165 tests pass (154 → 165: `test_grounding.py`, `test_cascade.py`, a
`force_tier` gateway test, plus the earlier `test_researcher_agent.py`);
`ruff check` clean.
