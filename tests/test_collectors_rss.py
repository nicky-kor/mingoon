from research_os.collectors import rss as rss_module
from research_os.collectors.rss import RSSCollector

_FEED_XML = """<?xml version="1.0"?>
<rss version="2.0">
<channel>
  <title>Test Feed</title>
  <item>
    <title>Predictive Maintenance for Wind Turbines</title>
    <link>http://example.com/item1</link>
    <description>A survey of predictive maintenance techniques for wind turbine gearboxes.</description>
    <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
    <author>Jane Doe</author>
  </item>
</channel>
</rss>
"""


class FakeResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def test_rss_collector_disabled_by_default_returns_empty():
    collector = RSSCollector(feeds=[])
    assert collector.collect() == []


def test_rss_collector_parses_feed_entries(monkeypatch):
    def fake_get(url, timeout=None, follow_redirects=None):
        return FakeResponse(_FEED_XML)

    monkeypatch.setattr(rss_module.httpx, "get", fake_get)
    monkeypatch.setattr(rss_module.time, "sleep", lambda s: None)

    collector = RSSCollector(feeds=["http://example.com/feed"])
    items = collector.collect()

    assert len(items) == 1
    item = items[0]
    assert item["title"] == "Predictive Maintenance for Wind Turbines"
    assert item["url"] == "http://example.com/item1"
    assert item["source_type"] == "rss"
    assert "predictive maintenance" in item["abstract"].lower()


def test_rss_collector_run_never_raises_on_network_error(monkeypatch):
    def fake_get(url, timeout=None, follow_redirects=None):
        raise ConnectionError("network down")

    monkeypatch.setattr(rss_module.httpx, "get", fake_get)
    monkeypatch.setattr(rss_module.time, "sleep", lambda s: None)

    collector = RSSCollector(feeds=["http://example.com/feed"])
    assert collector.run() == []
