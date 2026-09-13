from research_os.models.router import ModelRouter


def test_agent_default_tier_used_when_no_rule_matches():
    router = ModelRouter()
    decision = router.route(agent="AnalystAgent")
    assert decision.tier == "cloud_reasoning"
    assert decision.provider == "anthropic"


def test_reasoning_heavy_call_routes_cloud_with_local_as_eventual_fallback():
    # AnalystAgent/TransferAgent call gateway.generate(reasoning_required=True,
    # importance>=70) — this resolves to cloud (better quality) by default,
    # since ModelGateway's circuit breaker (models/circuit_breaker.py)
    # automatically detects an unrecoverable cloud failure and skips to the
    # local fallback for a cooldown, without any manual config edit. The
    # fallback chain must still bottom out on a local tier so that skip has
    # somewhere free to land, rather than dead-ending in more cloud tiers.
    router = ModelRouter()
    decision = router.route(agent="AnalystAgent", reasoning_required=True, importance=80)
    assert decision.tier == "cloud_reasoning"
    chain = router.fallback_chain(decision.tier)
    assert chain[0] == "cloud_deep_research"
    assert "local_reasoning" in chain


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
