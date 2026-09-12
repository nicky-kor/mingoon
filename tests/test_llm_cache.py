from research_os.models.base import GenerationRequest, GenerationResult
from research_os.models.cache import compute_cache_key, get_cached, store_cached


def test_cache_miss_then_hit(isolated_db):
    request = GenerationRequest(prompt="hello", system="sys", max_tokens=100, temperature=0.2)
    key = compute_cache_key("ollama", "qwen2.5:3b-instruct", request)

    assert get_cached(key) is None

    result = GenerationResult(text="cached answer", provider="ollama", model="qwen2.5:3b-instruct")
    store_cached(key, result)

    cached = get_cached(key)
    assert cached is not None
    assert cached.text == "cached answer"


def test_cache_key_differs_for_different_prompt():
    r1 = GenerationRequest(prompt="a")
    r2 = GenerationRequest(prompt="b")
    assert compute_cache_key("ollama", "m", r1) != compute_cache_key("ollama", "m", r2)


def test_cache_key_stable_for_identical_request():
    r1 = GenerationRequest(prompt="a", system="s", max_tokens=10, temperature=0.1)
    r2 = GenerationRequest(prompt="a", system="s", max_tokens=10, temperature=0.1)
    assert compute_cache_key("ollama", "m", r1) == compute_cache_key("ollama", "m", r2)


def test_gateway_uses_cache_on_second_call(isolated_db):
    from research_os.models.base import ProviderAdapter
    from research_os.models.gateway import ModelGateway
    from research_os.models.router import ModelRouter

    calls = {"count": 0}

    class CountingAdapter(ProviderAdapter):
        name = "ollama"

        def is_available(self):
            return True

        def generate(self, request, model):
            calls["count"] += 1
            return GenerationResult(text="a fresh response", provider=self.name, model=model, latency_ms=5.0)

    gateway = ModelGateway(router=ModelRouter())
    gateway.register_adapter("ollama", CountingAdapter())
    gateway.register_adapter("anthropic", CountingAdapter())  # unused fallback here

    r1 = gateway.generate(prompt="same prompt", agent="ClassifierAgent", task_type="classification", complexity="low")
    r2 = gateway.generate(prompt="same prompt", agent="ClassifierAgent", task_type="classification", complexity="low")

    assert calls["count"] == 1  # second call was served from cache
    assert r1.text == r2.text == "a fresh response"
