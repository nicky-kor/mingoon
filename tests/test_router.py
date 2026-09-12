from research_os.models.router import ModelRouter


def test_agent_default_tier_used_when_no_rule_matches():
    router = ModelRouter()
    decision = router.route(agent="AnalystAgent")
    assert decision.tier == "cloud_reasoning"
    assert decision.provider == "anthropic"


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
