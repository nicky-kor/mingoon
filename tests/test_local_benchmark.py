import json

from research_os.evaluation import local_benchmark
from research_os.models.base import GenerationResult
from research_os.models.local import OllamaAdapter


def test_run_local_benchmark_blocked_when_ollama_unavailable(monkeypatch, isolated_db):
    monkeypatch.setattr(OllamaAdapter, "is_available", lambda self: False)

    result = local_benchmark.run_local_benchmark()

    assert result.ollama_available is False
    assert result.models == []
    assert all(v is None for v in result.role_selection.values())
    assert any("not reachable" in item for item in result.limitations)


def test_run_local_benchmark_blocked_when_no_models_installed(monkeypatch, isolated_db):
    monkeypatch.setattr(OllamaAdapter, "is_available", lambda self: True)
    monkeypatch.setattr(OllamaAdapter, "list_models", lambda self: [])
    monkeypatch.setattr(OllamaAdapter, "get_version", lambda self: "0.1.0")

    result = local_benchmark.run_local_benchmark()

    assert result.ollama_available is True
    assert result.models == []
    assert any("no models are installed" in item for item in result.limitations)


def _fake_generate_factory():
    def fake_generate(self, request, model):
        # Return a plausible, schema-shaped response for whichever task
        # prompt this is, so the scoring functions have something to score.
        prompt = request.prompt
        if "industry, technology, problem" in prompt:
            text = json.dumps({"industry": "steel", "technology": "fault_diagnosis", "problem": "root_cause_analysis"})
        elif "problem, method, result, limitation" in prompt:
            text = json.dumps({"problem": "결함 탐지", "method": "딥러닝", "result": "정확도 향상", "limitation": "지연시간 증가"})
        elif "JSON array" in prompt:
            text = json.dumps(["defect detection", "vision transformer", "transfer learning"])
        elif "candidate_process" in prompt:
            text = json.dumps({"score": 2, "reason": "not battery-specific", "candidate_process": "coating", "candidate_equipment": None})
        elif "transfer_score" in prompt:
            text = json.dumps({
                "source_industry": "semiconductor", "technology": "computer_vision",
                "target_battery_process": "inspection", "target_equipment": None,
                "transfer_score": 55, "reason": "similar defect classification task",
            })
        else:
            text = "센서 데이터 표준화와 도메인 차이가 가장 큰 기술적 장애요인이다."
        return GenerationResult(text=text, provider="ollama", model=model, latency_ms=42.0, output_tokens=50)

    return fake_generate


def test_run_local_benchmark_end_to_end_with_fake_ollama(monkeypatch, isolated_db):
    monkeypatch.setattr(OllamaAdapter, "is_available", lambda self: True)
    monkeypatch.setattr(OllamaAdapter, "get_version", lambda self: "0.1.0")
    monkeypatch.setattr(
        OllamaAdapter, "list_models",
        lambda self: [{"name": "fake-model:3b", "size": 2_000_000_000}],
    )
    monkeypatch.setattr(OllamaAdapter, "generate", _fake_generate_factory())

    result = local_benchmark.run_local_benchmark()

    assert result.ollama_available is True
    assert len(result.models) == 1
    model = result.models[0]
    assert model.model == "fake-model:3b"
    assert len(model.task_results) == 6
    assert all(t.success for t in model.task_results)
    assert model.avg_quality is not None
    assert model.composite is not None

    # A single model wins every role by default (it's the only candidate).
    assert result.role_selection["local_fast"] == "fake-model:3b"
    assert result.role_selection["local_standard"] == "fake-model:3b"
    assert result.role_selection["local_reasoning"] == "fake-model:3b"

    report = local_benchmark.render_report(result)
    assert "fake-model:3b" in report
    assert "Best Model for local_fast" in report


def test_derive_role_selection_from_db_after_benchmark(monkeypatch, isolated_db):
    monkeypatch.setattr(OllamaAdapter, "is_available", lambda self: True)
    monkeypatch.setattr(OllamaAdapter, "get_version", lambda self: "0.1.0")
    monkeypatch.setattr(
        OllamaAdapter, "list_models",
        lambda self: [{"name": "fake-model:3b", "size": 2_000_000_000}],
    )
    monkeypatch.setattr(OllamaAdapter, "generate", _fake_generate_factory())

    local_benchmark.run_local_benchmark()

    with isolated_db.session_scope() as session:
        selection = local_benchmark.derive_role_selection_from_db(session)

    assert selection["local_standard"] == "fake-model:3b"
