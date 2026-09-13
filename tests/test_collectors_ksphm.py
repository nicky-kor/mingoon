from research_os.collectors import ksphm as ksphm_module
from research_os.collectors.ksphm import KSPHMCollector

# Trimmed from the real page (fetched 2026-09-13): one pinned "공지" row
# (no numeric 번호) and one regular numbered row, inside the nested
# <table> the real markup wraps each title link in.
_FIXTURE_HTML = """
<table width="100%" class="sol_table">
  <tbody>
    <tr>
      <td align="center"></td>
      <td align="center" height="28"><span class='not'>공지</span></td>
      <td style="padding-left:10px;">
        <table><tr><td>
          <a href='/info/notice.php?ptype=view&idx=5605&page=&code=notice'>건전성 예측관리 지식체계 실무가이드(PHM BOK GUIDE) 출판</a>
        </td></tr></table>
      </td>
      <td align="center">KSPHM</td>
      <td align="center">22.11.22</td>
      <td align="center">9245</td>
    </tr>
    <tr>
      <td align="center"></td>
      <td align="center" height="28">146</td>
      <td style="padding-left:10px;">
        <table><tr><td>
          <a href='/info/notice.php?ptype=view&idx=5850&page=1&code=notice'>기술 수요조사 안내</a>
        </td></tr></table>
      </td>
      <td align="center">KSPHM</td>
      <td align="center">26.09.07</td>
      <td align="center">70</td>
    </tr>
  </tbody>
</table>
"""


class FakeResponse:
    def __init__(self, html: str, status_code: int = 200):
        self.content = html.encode("euc-kr")
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def test_ksphm_collector_parses_pinned_and_numbered_rows(monkeypatch):
    def fake_get(url, params=None, timeout=None, follow_redirects=None):
        return FakeResponse(_FIXTURE_HTML)

    monkeypatch.setattr(ksphm_module.httpx, "get", fake_get)

    items = KSPHMCollector(pages=1).collect()

    assert len(items) == 2
    pinned, numbered = items
    assert pinned["external_id"] == "ksphm:5605"
    assert pinned["title"] == "건전성 예측관리 지식체계 실무가이드(PHM BOK GUIDE) 출판"
    assert pinned["url"] == "https://www.phm.or.kr/info/notice.php?ptype=view&idx=5605&page=&code=notice"
    assert pinned["published_at"] == "2022-11-22"

    assert numbered["external_id"] == "ksphm:5850"
    assert numbered["published_at"] == "2026-09-07"


def test_ksphm_collector_returns_empty_on_network_error(monkeypatch):
    def fake_get(url, params=None, timeout=None, follow_redirects=None):
        raise ConnectionError("network down")

    monkeypatch.setattr(ksphm_module.httpx, "get", fake_get)

    assert KSPHMCollector(pages=1).run() == []


def test_ksphm_collector_returns_empty_when_table_missing(monkeypatch):
    def fake_get(url, params=None, timeout=None, follow_redirects=None):
        return FakeResponse("<html><body>redesigned page</body></html>")

    monkeypatch.setattr(ksphm_module.httpx, "get", fake_get)

    assert KSPHMCollector(pages=1).collect() == []
