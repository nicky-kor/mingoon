"""Cross-checks between config/*.yaml files that a typo would otherwise
only surface at runtime (a router rule pointing at a tier that doesn't
exist, an agent default naming a nonexistent tier, a benchmark fallback
chain pointing at itself, duplicate taxonomy ids, ...).
"""
from research_os.core.config import (
    battery_config,
    industries_config,
    models_config,
    problems_config,
    routing_config,
    scoring_config,
    technologies_config,
)


def _tier_names() -> set[str]:
    return set(models_config()["tiers"].keys())


def test_agent_defaults_all_reference_real_tiers():
    tiers = _tier_names()
    for agent, tier in routing_config()["agent_defaults"].items():
        assert tier in tiers, f"{agent} default tier '{tier}' is not defined in config/models.yaml"


def test_routing_rules_only_reference_real_tiers():
    tiers = _tier_names()
    for rule in routing_config().get("rules", []):
        if "tier" in rule:
            assert rule["tier"] in tiers, f"routing rule references unknown tier '{rule['tier']}'"


def test_default_tier_is_real():
    assert routing_config()["default_tier"] in _tier_names()


def test_fallback_chains_reference_real_tiers_and_never_self_reference():
    tiers = _tier_names()
    for tier, chain in models_config().get("fallback", {}).items():
        assert tier in tiers
        for next_tier in chain:
            assert next_tier in tiers, f"fallback for '{tier}' references unknown tier '{next_tier}'"
            assert next_tier != tier, f"fallback for '{tier}' points at itself"


def test_escalation_chains_reference_real_tiers_and_never_self_reference():
    tiers = _tier_names()
    for tier, chain in models_config().get("escalation", {}).items():
        assert tier in tiers
        for next_tier in chain:
            assert next_tier in tiers, f"escalation for '{tier}' references unknown tier '{next_tier}'"
            assert next_tier != tier, f"escalation for '{tier}' points at itself"


def test_every_tier_has_provider_and_model():
    for tier, entry in models_config()["tiers"].items():
        assert entry.get("provider"), f"tier '{tier}' has no provider"
        assert entry.get("model"), f"tier '{tier}' has no model"


def test_taxonomy_ids_are_unique():
    for cfg, key in [
        (industries_config()["industries"], "id"),
        (technologies_config()["technologies"], "id"),
        (problems_config()["problems"], "id"),
    ]:
        ids = [item[key] for item in cfg]
        assert len(ids) == len(set(ids)), f"duplicate ids found: {ids}"


def test_battery_relevance_industry_key_exists():
    industry_ids = {i["id"] for i in industries_config()["industries"]}
    assert "battery_manufacturing" in industry_ids


def test_battery_process_keywords_are_all_non_empty():
    for process, keywords in battery_config()["keywords"].items():
        assert keywords, f"battery process '{process}' has an empty keyword list"


def test_scoring_priority_thresholds_are_strictly_descending():
    thresholds = scoring_config()["priority_thresholds"]
    ordered = [thresholds["critical"], thresholds["high"], thresholds["medium"], thresholds["low"]]
    assert ordered == sorted(ordered, reverse=True)
