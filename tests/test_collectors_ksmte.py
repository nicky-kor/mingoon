from research_os.collectors import ksmte as ksmte_module
from research_os.collectors.ksmte import KSMTECollector

# Trimmed from KSMTE's real 공지사항 board (fetched 2026-09-13): two
# numbered rows, no <tbody> wrapper (rows are direct <table> children, as
# on the real page).
_FIXTURE_HTML = """
<table>
  <tr align="center" height="20">
    <td class="small">779</td>
    <td align="left">
      <a href="?mode=view&uid=38481&no=779&main=&sub=1&page=1&ifwhat=&ifvalue=">[홍보] 2026 경북 글로벌 미래 모빌리티 포럼  안내</a>
    </td>
    <td class="small">2026-08-07</td>
    <td class="small">93</td>
  </tr>
  <tr align="center" height="20">
    <td class="small">778</td>
    <td align="left">
      <a href="?mode=view&uid=38480&no=778&main=&sub=1&page=1&ifwhat=&ifvalue=">2026년 한국연구재단 공학단 기계분야 전문위원 후보자 모집안내</a> <img src='/images/icon_save.gif'>
    </td>
    <td class="small">2026-07-29</td>
    <td class="small">143</td>
  </tr>
</table>
"""


class FakeResponse:
    def __init__(self, html: str, status_code: int = 200):
        self.content = html.encode("euc-kr")
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def test_ksmte_collector_parses_rows(monkeypatch):
    def fake_get(url, timeout=None, follow_redirects=None):
        return FakeResponse(_FIXTURE_HTML)

    monkeypatch.setattr(ksmte_module.httpx, "get", fake_get)

    items = KSMTECollector().collect()

    assert len(items) == 2
    first, second = items
    assert first["external_id"] == "ksmte:38481"
    assert first["title"] == "[홍보] 2026 경북 글로벌 미래 모빌리티 포럼  안내"
    assert first["url"] == (
        "https://www.ksmte.kr/bbs/index.kin?mode=view&uid=38481&no=779&main=&sub=1&page=1&ifwhat=&ifvalue="
    )
    assert first["published_at"] == "2026-08-07"
    assert first["source"] == "ksmte"

    assert second["external_id"] == "ksmte:38480"
    assert second["published_at"] == "2026-07-29"


def test_ksmte_collector_returns_empty_on_network_error(monkeypatch):
    def fake_get(url, timeout=None, follow_redirects=None):
        raise ConnectionError("network down")

    monkeypatch.setattr(ksmte_module.httpx, "get", fake_get)

    assert KSMTECollector().run() == []


def test_ksmte_collector_returns_empty_when_no_rows_match(monkeypatch):
    def fake_get(url, timeout=None, follow_redirects=None):
        return FakeResponse("<html><body>redesigned page</body></html>")

    monkeypatch.setattr(ksmte_module.httpx, "get", fake_get)

    assert KSMTECollector().collect() == []
