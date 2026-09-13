"""models/cascade.py: cost-saving local-first cascade (spec section 42)."""
from research_os.models import cascade as cascade_module
from research_os.models.base import GenerationResult
from research_os.models.gateway import AllProvidersUnavailableError


class _FakeGateway:
    """Records every generate() call and returns the next canned response
    (or raises it, if it's an exception instance) in order."""

    def __init__(self, responses):
        self.calls: list[dict] = []
        self._responses = list(responses)

    def generate(self, prompt, **kwargs):
        self.calls.append(kwargs)
        response = self._responses[len(self.calls) - 1]
        if isinstance(response, Exception):
            raise response
        return response


def _result(text="ok", provider="ollama", model="local-model"):
    return GenerationResult(text=text, provider=provider, model=model, latency_ms=1.0)


def _enable_for(monkeypatch, agents, enabled=True):
    monkeypatch.setattr(cascade_module, "routing_config", lambda: {"cost_cascade": {"enabled": enabled, "agents": agents}})


def test_cascade_skips_cloud_when_cheap_tier_is_acceptable(monkeypatch):
    _enable_for(monkeypatch, ["AnalystAgent"])
    gateway = _FakeGateway([_result("cheap answer")])

    result, used_cheap = cascade_module.generate_with_cascade(
        gateway, "prompt", is_acceptable=lambda text: True, agent="AnalystAgent",
    )

    assert used_cheap is True
    assert result.text == "cheap answer"
    assert len(gateway.calls) == 1
    assert gateway.calls[0]["force_tier"] == cascade_module.CHEAP_TIER


def test_cascade_escalates_when_cheap_tier_answer_is_rejected(monkeypatch):
    _enable_for(monkeypatch, ["AnalystAgent"])
    gateway = _FakeGateway([_result("cheap but wrong"), _result("cloud answer", provider="anthropic", model="claude")])

    result, used_cheap = cascade_module.generate_with_cascade(
        gateway, "prompt", is_acceptable=lambda text: False, agent="AnalystAgent",
    )

    assert used_cheap is False
    assert result.text == "cloud answer"
    assert len(gateway.calls) == 2
    assert "force_tier" not in gateway.calls[1]  # the escalation call uses normal routing


def test_cascade_escalates_when_cheap_tier_unavailable(monkeypatch):
    _enable_for(monkeypatch, ["AnalystAgent"])
    gateway = _FakeGateway([AllProvidersUnavailableError("no local model"), _result("cloud answer")])

    result, used_cheap = cascade_module.generate_with_cascade(
        gateway, "prompt", is_acceptable=lambda text: True, agent="AnalystAgent",
    )

    assert used_cheap is False
    assert result.text == "cloud answer"


def test_cascade_disabled_for_this_agent_skips_cheap_attempt_entirely(monkeypatch):
    _enable_for(monkeypatch, ["SomeOtherAgent"])
    gateway = _FakeGateway([_result("cloud answer")])

    result, used_cheap = cascade_module.generate_with_cascade(
        gateway, "prompt", is_acceptable=lambda text: True, agent="AnalystAgent",
    )

    assert used_cheap is False
    assert len(gateway.calls) == 1
    assert "force_tier" not in gateway.calls[0]


def test_cascade_disabled_globally(monkeypatch):
    _enable_for(monkeypatch, ["AnalystAgent"], enabled=False)
    gateway = _FakeGateway([_result("cloud answer")])

    result, used_cheap = cascade_module.generate_with_cascade(
        gateway, "prompt", is_acceptable=lambda text: True, agent="AnalystAgent",
    )

    assert used_cheap is False
    assert len(gateway.calls) == 1


def test_cascade_with_no_agent_kwarg_never_cascades(monkeypatch):
    _enable_for(monkeypatch, [])
    gateway = _FakeGateway([_result("cloud answer")])

    result, used_cheap = cascade_module.generate_with_cascade(gateway, "prompt", is_acceptable=lambda text: True)

    assert used_cheap is False
    assert len(gateway.calls) == 1
