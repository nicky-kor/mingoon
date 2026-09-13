from research_os.collectors import arxiv as arxiv_module

FIXTURE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/9999.0001v1</id>
    <published>2024-01-01T00:00:00Z</published>
    <title>A Test Paper About Anomaly Detection</title>
    <summary>We propose a transformer for anomaly detection in manufacturing sensors.</summary>
    <author><name>Test Author</name></author>
    <link href="http://arxiv.org/abs/9999.0001v1" rel="alternate" type="text/html"/>
  </entry>
</feed>
"""


class FakeResponse:
    def __init__(self, text: str, status_code: int = 200, headers: dict | None = None):
        self.text = text
        self.status_code = status_code
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            import httpx

            raise httpx.HTTPStatusError(f"HTTP {self.status_code}", request=None, response=self)


def test_arxiv_collector_parses_entries(monkeypatch):
    captured = {}

    def fake_get(url, params=None, headers=None, timeout=None, follow_redirects=None):
        captured["follow_redirects"] = follow_redirects
        captured["headers"] = headers
        return FakeResponse(FIXTURE_XML)

    monkeypatch.setattr(arxiv_module.httpx, "get", fake_get)

    collector = arxiv_module.ArxivCollector(categories=["cs.LG"], max_results=5)
    items = collector.collect()

    assert len(items) == 1
    item = items[0]
    assert item["arxiv_id"] == "9999.0001"
    assert item["title"] == "A Test Paper About Anomaly Detection"
    assert item["source_type"] == "arxiv"
    assert "anomaly detection" in item["abstract"].lower()

    # Regression guard: arXiv 301-redirects http:// to https:// on its API
    # endpoint. httpx does NOT follow redirects by default, and
    # response.raise_for_status() actively raises on an unfollowed
    # redirect ("Redirect response '301 Moved Permanently'...") — this
    # broke real collection in production before follow_redirects=True
    # was added.
    assert captured["follow_redirects"] is True
    # Regression guard: an anonymous User-Agent is more likely to be
    # rate-limited (429) by arXiv's API — see test_retry_delay_* below.
    assert "User-Agent" in captured["headers"]


def test_arxiv_collector_default_base_url_is_https():
    # The default (no ARXIV_BASE_URL override) must be https — arXiv
    # redirects the plain-http endpoint, and depending on a redirect
    # succeeding is one avoidable round trip per request.
    collector = arxiv_module.ArxivCollector(categories=["cs.LG"])
    assert collector.base_url.startswith("https://")


def test_arxiv_collector_with_empty_categories_makes_no_network_call(monkeypatch):
    # Regression guard: categories=[] must mean "search nothing", not
    # silently fall back to config/system.yaml's default categories (the
    # same class of bug found in GitHubCollector — see
    # tests/test_collectors_github.py).
    def fail_if_called(*args, **kwargs):
        raise AssertionError("ArxivCollector made a network call despite categories=[]")

    monkeypatch.setattr(arxiv_module.httpx, "get", fail_if_called)

    collector = arxiv_module.ArxivCollector(categories=[])
    assert collector.categories == []
    assert collector.collect() == []


def test_arxiv_collector_run_never_raises_on_network_error(monkeypatch):
    def fake_get(url, params=None, headers=None, timeout=None, follow_redirects=None):
        raise ConnectionError("network down")

    monkeypatch.setattr(arxiv_module.httpx, "get", fake_get)
    monkeypatch.setattr(arxiv_module.time, "sleep", lambda seconds: None)
    collector = arxiv_module.ArxivCollector(categories=["cs.LG"], max_retries=0)
    items = collector.run()
    assert items == []


def test_arxiv_collector_retries_after_429_and_then_succeeds(monkeypatch):
    calls = {"count": 0}
    sleeps: list[float] = []

    def fake_get(url, params=None, headers=None, timeout=None, follow_redirects=None):
        calls["count"] += 1
        if calls["count"] == 1:
            return FakeResponse("rate limited", status_code=429, headers={"Retry-After": "3"})
        return FakeResponse(FIXTURE_XML)

    monkeypatch.setattr(arxiv_module.httpx, "get", fake_get)
    monkeypatch.setattr(arxiv_module.time, "sleep", lambda seconds: sleeps.append(seconds))

    collector = arxiv_module.ArxivCollector(categories=["cs.LG"])
    items = collector.collect()

    assert len(items) == 1  # succeeded on the second attempt
    # Regression guard: a 429 must back off using Retry-After (here 3s),
    # not the short generic-error backoff — retrying a rate limit quickly
    # just gets rate-limited again (this is what broke real collection:
    # two attempts ~2s apart both got 429).
    assert sleeps == [3.0]


def test_retry_delay_honors_retry_after_header():
    response = FakeResponse("", status_code=429, headers={"Retry-After": "7"})
    assert arxiv_module.ArxivCollector._retry_delay(1, response) == 7.0


def test_retry_delay_backs_off_harder_for_429_without_retry_after():
    response = FakeResponse("", status_code=429)
    generic_delay = arxiv_module.ArxivCollector._retry_delay(1, None)
    rate_limited_delay = arxiv_module.ArxivCollector._retry_delay(1, response)
    assert rate_limited_delay > generic_delay
