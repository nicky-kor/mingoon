from research_os.models.router import ModelRouter


def test_agent_default_tier_used_when_no_rule_matches():
    router = ModelRouter()
    decision = router.route(agent="AnalystAgent")
    assert decision.tier == "local_reasoning"
    assert decision.provider == "ollama"


def test_reasoning_heavy_call_routes_local_first_with_cloud_as_fallback_only():
    # AnalystAgent/TransferAgent call gateway.generate(reasoning_required=True,
    # importance>=70) — this must resolve to the free local tier by
    # default (config/routing.yaml policy: local first, cloud only if
    # local is unavailable), with cloud still reachable as this tier's
    # fallback rather than gone entirely.
    router = ModelRouter()
    decision = router.route(agent="AnalystAgent", reasoning_required=True, importance=80)
    assert decision.tier == "local_reasoning"
    assert router.fallback_chain(decision.tier) == ["cloud_reasoning"]


def test_classification_low_complexity_routes_local_fast():
    router = ModelRouter()
    decision = router.route(task_type="classification", complexity="low")
    assert decision.tier == "local_fast"


def test_restricted_privacy_forces_local():
    router = ModelRouter()
    decision = router.route(agent="AnalystAgent", privacy_level="restricted")
    assert decision.tier.startswith("local_")


def test_fallback_chain_resolves_from_config():
    router = ModelRouter()
    chain = router.fallback_chain("local_fast")
    assert chain == ["cloud_fast"]


def test_resolve_unknown_tier_raises():
    router = ModelRouter()
    try:
        router.resolve_tier("does_not_exist")
        assert False, "expected KeyError"
    except KeyError:
        pass
