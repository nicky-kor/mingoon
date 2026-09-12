from research_os.core.config import (
    battery_config,
    industries_config,
    models_config,
    problems_config,
    routing_config,
    scoring_config,
    system_config,
    technologies_config,
)


def test_system_config_loads():
    cfg = system_config()
    assert cfg["system"]["name"] == "Manufacturing AI Research OS"
    assert "arxiv" in cfg["sources"]


def test_industries_battery_is_top_priority():
    industries = {i["id"]: i for i in industries_config()["industries"]}
    assert industries["battery_manufacturing"]["priority"] == 5
    assert all(i["priority"] <= 5 for i in industries.values())


def test_technologies_and_problems_have_ids():
    for tech in technologies_config()["technologies"]:
        assert tech["id"] and tech["name"]
    for problem in problems_config()["problems"]:
        assert problem["id"] and problem["name"]


def test_battery_taxonomy_has_processes_and_equipment():
    cfg = battery_config()
    assert "coating" in cfg["processes"]
    assert "plc" in cfg["equipment"]


def test_scoring_weights_sum_to_one():
    weights = scoring_config()["weights"]
    assert abs(sum(weights.values()) - 1.0) < 1e-6


def test_models_config_has_all_tiers():
    tiers = models_config()["tiers"]
    for expected in [
        "local_fast", "local_standard", "local_reasoning",
        "cloud_fast", "cloud_standard", "cloud_reasoning", "cloud_deep_research",
        "embedding", "reranker",
    ]:
        assert expected in tiers


def test_routing_config_has_agent_defaults():
    agent_defaults = routing_config()["agent_defaults"]
    assert agent_defaults["AnalystAgent"] == "cloud_reasoning"
    assert agent_defaults["ClassifierAgent"] == "local_fast"
