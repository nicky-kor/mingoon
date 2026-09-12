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
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def test_arxiv_collector_parses_entries(monkeypatch):
    def fake_get(url, params=None, timeout=None):
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


def test_arxiv_collector_run_never_raises_on_network_error(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        raise ConnectionError("network down")

    monkeypatch.setattr(arxiv_module.httpx, "get", fake_get)
    monkeypatch.setattr(arxiv_module.time, "sleep", lambda seconds: None)
    collector = arxiv_module.ArxivCollector(categories=["cs.LG"], max_retries=0)
    items = collector.run()
    assert items == []
