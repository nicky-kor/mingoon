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
| **FrugalGPT-style cascade: try local first, escalate to cloud only if the answer looks insufficient** | A genuinely new idea for this project specifically: **QAAgent's grounding check could double as the escalation trigger** — try `local_reasoning` first (free), run QAAgent's check on the result, and only re-run on `cloud_reasoning` if flagged. Could cut cloud spend substantially on the reasoning-heavy agents (Analyst/Transfer/Research/Briefing) that currently default straight to cloud. | Changes default routing again (third time this session, after the circuit-breaker revert) — needs the user's sign-off before flipping; QAAgent's check is percentage-specific today, so it wouldn't catch every case a human would consider "insufficient" (weak novelty reasoning with no numbers at all would pass QA cleanly but still be a worse answer than cloud would give); doubles LLM calls for any document QA flags, so it trades "always expensive" for "sometimes 2x calls," not obviously cheaper in every case. | **Worth a real proposal, not implemented.** Flagging for the user to weigh in on directly rather than silently changing routing defaults a third time. |

## Net effect on the codebase

Only the ResearchAgent ranking change went in (small, unambiguous
improvement, no default-routing behavior changed). 154 tests pass after
adding `test_researcher_agent.py`; `ruff check` clean.
