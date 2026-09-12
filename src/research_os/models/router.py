"""ModelRouter: decides which model *tier* serves a request (spec section 11).

Resolution order:
1. Privacy: `restricted` always prefers a local tier.
2. First matching rule in config/routing.yaml `rules`.
3. The requesting agent's default tier (config/routing.yaml `agent_defaults`).
4. `default_tier`.

Tier -> (provider, model) resolution and the escalation/fallback chains live
in config/models.yaml. Model-benchmark-driven auto-routing is a Phase 3+
extension point (`route()` is the single place that would change).
"""
from __future__ import annotations

from dataclasses import dataclass

from research_os.core.config import models_config, routing_config


@dataclass
class RouteDecision:
    tier: str
    provider: str
    model: str


def _rule_matches(rule_when: dict, ctx: dict) -> bool:
    for key, expected in rule_when.items():
        if key.endswith("_gte"):
            field = key[: -len("_gte")]
            if ctx.get(field) is None or ctx[field] < expected:
                return False
        elif key.endswith("_lte"):
            field = key[: -len("_lte")]
            if ctx.get(field) is None or ctx[field] > expected:
                return False
        else:
            if ctx.get(key) != expected:
                return False
    return True


class ModelRouter:
    def __init__(self) -> None:
        self.routing = routing_config()
        self.models = models_config()

    def _tier_to_local_variant(self, tier: str) -> str:
        if tier.startswith("local_"):
            return tier
        # crude mapping cloud_x -> local_x for privacy-forced local routing
        mapping = {"cloud_fast": "local_fast", "cloud_standard": "local_standard", "cloud_reasoning": "local_reasoning"}
        return mapping.get(tier, "local_standard")

    def route(
        self,
        task_type: str | None = None,
        complexity: str | None = None,
        importance: int = 50,
        latency_budget: str | None = None,
        cost_budget: str | None = None,
        privacy_level: str = "public",
        agent: str | None = None,
        reasoning_required: bool = False,
    ) -> RouteDecision:
        ctx = {
            "task_type": task_type,
            "complexity": complexity,
            "importance": importance,
            "latency_budget": latency_budget,
            "cost_budget": cost_budget,
            "privacy_level": privacy_level,
            "reasoning_required": reasoning_required,
        }

        tier = None
        for rule in self.routing.get("rules", []):
            when = rule.get("when", {})
            if not _rule_matches(when, ctx):
                continue
            if rule.get("tier"):
                tier = rule["tier"]
                break
            if rule.get("prefer_local") and agent:
                tier = self._tier_to_local_variant(self.routing["agent_defaults"].get(agent, self.routing["default_tier"]))
                break

        if tier is None and agent:
            tier = self.routing.get("agent_defaults", {}).get(agent)

        if tier is None:
            tier = self.routing.get("default_tier", "local_fast")

        if privacy_level == "restricted":
            tier = self._tier_to_local_variant(tier)

        provider, model = self.resolve_tier(tier)
        return RouteDecision(tier=tier, provider=provider, model=model)

    def resolve_tier(self, tier: str) -> tuple[str, str]:
        entry = self.models.get("tiers", {}).get(tier)
        if not entry:
            raise KeyError(f"Unknown model tier: {tier}")
        return entry["provider"], entry["model"]

    def fallback_chain(self, tier: str) -> list[str]:
        return self.models.get("fallback", {}).get(tier, [])
