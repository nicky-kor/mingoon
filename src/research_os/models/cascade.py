"""Cost-saving generation cascade (spec section 42: don't call an
expensive model unnecessarily).

Tries a free local tier first; only pays for the caller's normal routing
(usually a cloud tier) if that local answer doesn't pass the caller's own
acceptability check. This is the FrugalGPT-style pattern (try cheap,
escalate only on a quality doubt), applied here using each agent's own
generated-text grounding as the "quality doubt" signal
(`core/grounding.py`'s percentage check) rather than a trained classifier
— consistent with this project's existing preference for a deterministic
check over an ML one where it's good enough (see QAAgent, TrendAgent).

**Important, deliberately not hidden from callers**: passing
`is_acceptable` means "no fabricated percentage found in this answer" —
it is NOT a guarantee that the local tier's answer is as deep or as good
as what cloud would have produced. A local model can give a shallower
but still "acceptable" answer and this cascade would keep it. That's a
real, accepted trade (cost down, a small and mostly-invisible quality
risk) rather than a strict equivalence guarantee. The QA_CHECK pipeline
stage (`agents/qa.py`) still runs afterward regardless of which tier
answered, so the same grounding check is applied a second time on
whatever was actually stored.

Toggle off per-agent (or entirely) via `config/routing.yaml`'s
`cost_cascade` block — no code change needed to revert to always calling
the normal (cloud-first) routing directly.
"""
from __future__ import annotations

from typing import Callable

from research_os.core.config import routing_config
from research_os.core.logging_setup import get_logger
from research_os.models.base import GenerationResult
from research_os.models.gateway import AllProvidersUnavailableError, ModelGateway

logger = get_logger("models.cascade")

CHEAP_TIER = "local_reasoning"


def _cascade_enabled_for(agent_name: str | None) -> bool:
    if agent_name is None:
        return False
    cfg = routing_config().get("cost_cascade", {})
    return bool(cfg.get("enabled")) and agent_name in (cfg.get("agents") or [])


def generate_with_cascade(
    gateway: ModelGateway,
    prompt: str,
    *,
    is_acceptable: Callable[[str], bool],
    **gateway_kwargs,
) -> tuple[GenerationResult, bool]:
    """Returns (result, used_cheap_tier). `gateway_kwargs` are passed
    through to both the cheap attempt (with `force_tier` added) and the
    normal-routing fallback (unchanged) — same `agent`/`task_type`/
    `max_tokens`/etc either way, so logging/caching behave exactly as a
    plain `gateway.generate(prompt, **gateway_kwargs)` call would, just
    with a cheap attempt tried first when this agent has cascading
    enabled."""
    if _cascade_enabled_for(gateway_kwargs.get("agent")):
        try:
            cheap_result = gateway.generate(prompt, force_tier=CHEAP_TIER, **gateway_kwargs)
        except AllProvidersUnavailableError:
            cheap_result = None
        if cheap_result is not None:
            if is_acceptable(cheap_result.text):
                logger.info("cascade: %s tier answer accepted, cloud call skipped", CHEAP_TIER)
                return cheap_result, True
            logger.info("cascade: %s tier answer rejected, escalating to normal routing", CHEAP_TIER)

    result = gateway.generate(prompt, **gateway_kwargs)
    return result, False
