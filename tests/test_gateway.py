import pytest

from research_os.models.base import GenerationRequest, GenerationResult, ModelUnavailableError, ProviderAdapter
from research_os.models.gateway import AllProvidersUnavailableError, ModelGateway
from research_os.models.router import ModelRouter


class AlwaysFailsAdapter(ProviderAdapter):
    name = "always_fails"

    def is_available(self):
        return False

    def generate(self, request: GenerationRequest, model: str) -> GenerationResult:
        raise ModelUnavailableError("simulated failure")


class AlwaysSucceedsAdapter(ProviderAdapter):
    name = "always_succeeds"

    def is_available(self):
        return True

    def generate(self, request: GenerationRequest, model: str) -> GenerationResult:
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
