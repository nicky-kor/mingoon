from research_os.collectors import github as github_module
from research_os.collectors.github import GitHubCollector

_SEARCH_RESPONSE = {
    "items": [
        {
            "full_name": "example-org/predictive-maintenance-toolkit",
            "html_url": "https://github.com/example-org/predictive-maintenance-toolkit",
            "created_at": "2023-01-01T00:00:00Z",
            "owner": {"login": "example-org"},
            "description": "An open-source toolkit for predictive maintenance on rotating equipment.",
        }
    ]
}


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def test_github_collector_disabled_by_default_returns_empty(monkeypatch):
    # Regression guard: passing topics=[] explicitly must mean "search
    # nothing", not silently fall back to config/system.yaml's default
    # topic list — that bug once made this exact test hit the real
    # GitHub API 10 times. Failing the network call outright, rather than
    # just asserting on collect()'s return value, catches that class of
    # bug even if collect() happened to still return [] for other reasons.
    def fail_if_called(*args, **kwargs):
        raise AssertionError("GitHubCollector made a network call despite topics=[]")

    monkeypatch.setattr(github_module.httpx, "get", fail_if_called)

    collector = GitHubCollector(topics=[])
    assert collector.topics == []
    assert collector.collect() == []


def test_github_collector_parses_search_results(monkeypatch):
    def fake_get(url, params=None, headers=None, timeout=None):
        return FakeResponse(_SEARCH_RESPONSE)

    monkeypatch.setattr(github_module.httpx, "get", fake_get)
    monkeypatch.setattr(github_module.time, "sleep", lambda s: None)

    collector = GitHubCollector(topics=["predictive maintenance"])
    items = collector.collect()

    assert len(items) == 1
    item = items[0]
    assert item["title"] == "example-org/predictive-maintenance-toolkit"
    assert item["github_url"] == "https://github.com/example-org/predictive-maintenance-toolkit"
    assert item["source_type"] == "github"
    assert item["authors"] == ["example-org"]


def test_github_collector_run_never_raises_on_network_error(monkeypatch):
    def fake_get(url, params=None, headers=None, timeout=None):
        raise ConnectionError("network down")

    monkeypatch.setattr(github_module.httpx, "get", fake_get)
    monkeypatch.setattr(github_module.time, "sleep", lambda s: None)

    collector = GitHubCollector(topics=["predictive maintenance"])
    assert collector.run() == []


def test_github_collector_adds_auth_header_when_token_set(monkeypatch):
    captured = {}

    def fake_get(url, params=None, headers=None, timeout=None):
        captured["headers"] = headers
        return FakeResponse({"items": []})

    monkeypatch.setattr(github_module.httpx, "get", fake_get)
    monkeypatch.setattr(github_module.time, "sleep", lambda s: None)
    monkeypatch.setenv("GITHUB_TOKEN", "test-token-not-real")

    GitHubCollector(topics=["x"]).collect()
    assert captured["headers"]["Authorization"] == "Bearer test-token-not-real"
