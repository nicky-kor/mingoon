import pytest

from research_os.models import circuit_breaker
from research_os.models.base import GenerationRequest, GenerationResult, ModelUnavailableError, ProviderAdapter
from research_os.models.gateway import AllProvidersUnavailableError, ModelGateway
from research_os.models.router import ModelRouter


class AlwaysFailsAdapter(ProviderAdapter):
    name = "always_fails"

    def __init__(self, message: str = "simulated failure"):
        self.message = message
        self.call_count = 0

    def is_available(self):
        return False

    def generate(self, request: GenerationRequest, model: str) -> GenerationResult:
        self.call_count += 1
        raise ModelUnavailableError(self.message)


class AlwaysSucceedsAdapter(ProviderAdapter):
    name = "always_succeeds"

    def __init__(self):
        self.call_count = 0

    def is_available(self):
        return True

    def generate(self, request: GenerationRequest, model: str) -> GenerationResult:
        self.call_count += 1
        return GenerationResult(text="ok response", provider=self.name, model=model, latency_ms=1.0)


def test_gateway_falls_back_local_to_cloud(isolated_db):
    gateway = ModelGateway(router=ModelRouter(), log_runs=True)
    gateway.register_adapter("ollama", AlwaysFailsAdapter())
    gateway.register_adapter("anthropic", AlwaysSucceedsAdapter())

    result = gateway.generate(prompt="hello", agent="ClassifierAgent", task_type="classification", complexity="low")
    assert result.provider == "always_succeeds"
    assert result.text == "ok response"


def test_gateway_raises_when_all_providers_unavailable(isolated_db):
    gateway = ModelGateway(router=ModelRouter(), log_runs=True)
    gateway.register_adapter("ollama", AlwaysFailsAdapter())
    gateway.register_adapter("anthropic", AlwaysFailsAdapter())

    with pytest.raises(AllProvidersUnavailableError):
        gateway.generate(prompt="hello", agent="ClassifierAgent", task_type="classification", complexity="low")


def test_gateway_logs_llm_runs(isolated_db):
    from sqlalchemy import select

    from research_os.database.models import LLMRun

    gateway = ModelGateway(router=ModelRouter(), log_runs=True)
    gateway.register_adapter("ollama", AlwaysSucceedsAdapter())
    gateway.generate(prompt="hi", agent="ClassifierAgent", task_type="classification", complexity="low")

    with isolated_db.session_scope() as session:
        runs = session.scalars(select(LLMRun)).all()
        assert len(runs) == 1
        assert runs[0].status == "ok"


def test_gateway_trips_breaker_on_unrecoverable_error_and_falls_back(isolated_db):
    # AnalystAgent defaults to cloud_reasoning, whose fallback chain
    # (config/models.yaml) is [cloud_deep_research, local_reasoning] —
    # both cloud tiers share the "anthropic" provider, so a credit-balance
    # failure should trip the breaker once and skip straight to the local
    # tier instead of calling the (still-broken) anthropic adapter again.
    gateway = ModelGateway(router=ModelRouter(), log_runs=True)
    anthropic_adapter = AlwaysFailsAdapter(message="Your credit balance is too low to access the Claude API")
    local_adapter = AlwaysSucceedsAdapter()
    gateway.register_adapter("anthropic", anthropic_adapter)
    gateway.register_adapter("ollama", local_adapter)

    result = gateway.generate(prompt="hello", agent="AnalystAgent", reasoning_required=True, importance=80)

    assert result.provider == "always_succeeds"
    assert anthropic_adapter.call_count == 1  # tried once, tripped, not retried for cloud_deep_research

    with isolated_db.session_scope() as session:
        assert circuit_breaker.is_tripped(session, "anthropic") is not None


def test_gateway_skips_tripped_provider_without_calling_its_adapter(isolated_db):
    with isolated_db.session_scope() as session:
        circuit_breaker.trip(session, "anthropic", reason="credit balance is too low")

    gateway = ModelGateway(router=ModelRouter(), log_runs=True)
    anthropic_adapter = AlwaysFailsAdapter()
    local_adapter = AlwaysSucceedsAdapter()
    gateway.register_adapter("anthropic", anthropic_adapter)
    gateway.register_adapter("ollama", local_adapter)

    result = gateway.generate(prompt="hello", agent="AnalystAgent", reasoning_required=True, importance=80)

    assert result.provider == "always_succeeds"
    assert anthropic_adapter.call_count == 0  # breaker skipped it before any call was made


def test_force_tier_bypasses_normal_routing(isolated_db):
    # AnalystAgent's normal routing (config/routing.yaml agent_defaults)
    # picks cloud_reasoning/anthropic. force_tier should skip that
    # entirely and go straight to the given tier's provider instead —
    # used by models/cascade.py's cost-saving cascade.
    gateway = ModelGateway(router=ModelRouter(), log_runs=True)
    anthropic_adapter = AlwaysSucceedsAdapter()
    local_adapter = AlwaysSucceedsAdapter()
    gateway.register_adapter("anthropic", anthropic_adapter)
    gateway.register_adapter("ollama", local_adapter)

    gateway.generate(prompt="hello", agent="AnalystAgent", force_tier="local_reasoning")

    assert local_adapter.call_count == 1
    assert anthropic_adapter.call_count == 0


def test_gateway_does_not_trip_breaker_on_transient_error(isolated_db):
    # A plain timeout/connection error must NOT trip the breaker — only
    # unrecoverable (billing/auth) failures should.
    gateway = ModelGateway(router=ModelRouter(), log_runs=True)
    gateway.register_adapter("anthropic", AlwaysFailsAdapter(message="Connection timed out"))
    gateway.register_adapter("ollama", AlwaysSucceedsAdapter())

    gateway.generate(prompt="hello", agent="AnalystAgent", reasoning_required=True, importance=80)

    with isolated_db.session_scope() as session:
        assert circuit_breaker.is_tripped(session, "anthropic") is None
