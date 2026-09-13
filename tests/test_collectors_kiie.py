from research_os.collectors import kiie as kiie_module
from research_os.collectors.kiie import KIIECollector

# Trimmed from the real KIIE homepage (fetched 2026-09-13): the
# "Announcements" widget's first row carries the rowspan'd image cell,
# later rows don't.
_FIXTURE_HTML = """
<div class="announ_bg">
  <div class="anooun_news">
    <table>
      <tr>
        <td rowspan='5' class='bg_img'><img src='/images/main/broad.gif'></td>
        <td><a href='/board/board.asp?b_code=10342&Action=content&GotoPage=1&B_CATE=BBS1'>[정년퇴직소식] 한성대 원형규 교수, 산업공학 전공책 나눔</a></td>
        <td class='rig_t'>2026-09-04</td>
      </tr>
      <tr>
        <td><a href='/board/board.asp?b_code=10334&Action=content&GotoPage=1&B_CATE=BBS1'>대한산업공학회 제27대 차기회장 선거 결과 안내</a></td>
        <td class='rig_t'>2026-08-21</td>
      </tr>
    </table>
  </div>
</div>
"""


class FakeResponse:
    def __init__(self, html: str, status_code: int = 200):
        self.content = html.encode("euc-kr")
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def test_kiie_collector_parses_announcement_rows(monkeypatch):
    def fake_get(url, timeout=None, follow_redirects=None):
        return FakeResponse(_FIXTURE_HTML)

    monkeypatch.setattr(kiie_module.httpx, "get", fake_get)

    items = KIIECollector().collect()

    assert len(items) == 2
    first, second = items
    assert first["external_id"] == "kiie:10342"
    assert first["title"] == "[정년퇴직소식] 한성대 원형규 교수, 산업공학 전공책 나눔"
    assert first["url"] == "https://kiie.org/board/board.asp?b_code=10342&Action=content&GotoPage=1&B_CATE=BBS1"
    assert first["published_at"] == "2026-09-04"
    assert second["external_id"] == "kiie:10334"


def test_kiie_collector_returns_empty_on_network_error(monkeypatch):
    def fake_get(url, timeout=None, follow_redirects=None):
        raise ConnectionError("network down")

    monkeypatch.setattr(kiie_module.httpx, "get", fake_get)

    assert KIIECollector().run() == []


def test_kiie_collector_returns_empty_when_widget_missing(monkeypatch):
    def fake_get(url, timeout=None, follow_redirects=None):
        return FakeResponse("<html><body>redesigned homepage</body></html>")

    monkeypatch.setattr(kiie_module.httpx, "get", fake_get)

    assert KIIECollector().collect() == []
