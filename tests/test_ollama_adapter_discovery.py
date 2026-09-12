from research_os.models import local as local_module
from research_os.models.local import OllamaAdapter


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def test_list_models_parses_ollama_tags_response(monkeypatch):
    def fake_get(url, timeout=None):
        return FakeResponse({"models": [{"name": "qwen2.5:3b-instruct", "size": 1900000000}]})

    monkeypatch.setattr(local_module.httpx, "get", fake_get)
    models = OllamaAdapter().list_models()
    assert models == [{"name": "qwen2.5:3b-instruct", "size": 1900000000}]


def test_list_models_returns_empty_list_on_connection_error(monkeypatch):
    def fake_get(url, timeout=None):
        raise ConnectionError("refused")

    monkeypatch.setattr(local_module.httpx, "get", fake_get)
    assert OllamaAdapter().list_models() == []


def test_get_version_returns_none_when_unreachable(monkeypatch):
    def fake_get(url, timeout=None):
        raise ConnectionError("refused")

    monkeypatch.setattr(local_module.httpx, "get", fake_get)
    assert OllamaAdapter().get_version() is None


def test_get_version_parses_response(monkeypatch):
    def fake_get(url, timeout=None):
        return FakeResponse({"version": "0.3.12"})

    monkeypatch.setattr(local_module.httpx, "get", fake_get)
    assert OllamaAdapter().get_version() == "0.3.12"
