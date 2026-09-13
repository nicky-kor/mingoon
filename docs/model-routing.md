# Model Routing

## Flow

```
Agent -> ModelGateway.generate(...) -> ModelRouter.route(...) -> (tier)
       -> ModelRouter.resolve_tier(tier) -> (provider, model)
       -> ProviderAdapter.generate(...)
       -> on ModelUnavailableError: try next tier in models.yaml `fallback`
       -> on total failure: AllProvidersUnavailableError (agent catches, uses heuristic)
```

## Tiers (`config/models.yaml`)

`local_fast`, `local_standard`, `local_reasoning`, `cloud_fast`,
`cloud_standard`, `cloud_reasoning`, `cloud_deep_research`, plus
`embedding`/`reranker`. Each maps to a `(provider, model)` pair. Change the
model a tier uses by editing this file — no code changes needed.

## Routing decision (`config/routing.yaml`)

`ModelRouter.route()` resolves a tier in this order:

1. `privacy_level == "restricted"` forces a local variant of whatever tier
   would otherwise be chosen (`config/routing.yaml` rule with
   `prefer_local: true`).
2. The first matching rule in `rules` (matched by `task_type`, `complexity`,
   `reasoning_required`, `importance_gte`, ...).
3. The calling agent's default tier (`agent_defaults`).
4. `default_tier` as a last resort.

This is intentionally simple (first-match rules, not a scoring model) so it
stays auditable. `config/models.yaml`'s `escalation` map is the documented
extension point for a future difficulty-driven escalation
(cheap → standard → reasoning → deep research) and
`model_benchmarks` (populated by `research-os evaluate`) is the intended
input for making `ModelRouter` benchmark-aware in Phase 3 — neither is
wired into the routing decision automatically yet, to avoid routing on
data we haven't collected.

## Agent → tier defaults (initial policy, `config/routing.yaml`)

| Agent | Default tier |
|---|---|
| DiscoveryAgent | local_fast |
| ClassifierAgent | local_fast |
| SummarizerAgent | local_standard |
| AnalystAgent | cloud_reasoning |
| TransferAgent | cloud_reasoning |
| TrendAgent | *(none — no LLM call; see agents/trend.py)* |
| ResearchAgent | cloud_deep_research |
| BriefingAgent | cloud_reasoning |

## Adding a provider

Implement `research_os.models.base.ProviderAdapter` (`is_available()`,
`generate(request, model) -> GenerationResult`), register it in
`ModelGateway.__init__`, and point a tier at it in `config/models.yaml`.
`anthropic.py` (SDK-based), `openai.py` and `google.py` (plain REST) are
reference implementations.
