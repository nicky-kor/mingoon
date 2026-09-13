from research_os.collectors import board_cms as board_cms_module
from research_os.collectors.board_cms import KIEECollector, KSNVECollector

# Trimmed from KIEE's real 학회소식 board (fetched 2026-09-13): one pinned
# "공지" row and one regular numbered row. This CMS's table includes a
# "첨부" (attachment) column between title and author.
_KIEE_FIXTURE_HTML = """
<table>
  <thead>
    <tr><th>번호</th><th>제목</th><th>첨부</th><th>작성자</th><th>작성일</th><th>조회</th></tr>
  </thead>
  <tbody>
    <tr class="td-highlight">
      <td class="text-center"><span class="label label-primary">공지</span></td>
      <td class="title ta-left"><a href="?_0000_method=view&ncode=a001&num=2644&page=1"><b>산업계 차기회장 추대 안내</b></a></td>
      <td class="text-center hidden-xs"></td>
      <td class="text-center hidden-xs">이상필</td>
      <td class="text-center hidden-xs">2026-03-04</td>
      <td class="text-center hidden-xs">664</td>
    </tr>
    <tr>
      <td class="text-center">713</td>
      <td class="title ta-left"><a href="?_0000_method=view&ncode=a001&num=2682&page=1">[독자 퀴즈] 학회지 [전기의세계] 75권 9호(2026년 9월호) 발행 안내</a></td>
      <td class="text-center hidden-xs"></td>
      <td class="text-center hidden-xs">송호석</td>
      <td class="text-center hidden-xs">2026-09-08</td>
      <td class="text-center hidden-xs">82</td>
    </tr>
  </tbody>
</table>
"""

# Trimmed from KSNVE's real 공지사항 board (fetched 2026-09-13): one pinned
# row (with a file-download link inside the "첨부" cell, unlike KIEE's
# empty one) and one regular numbered row.
_KSNVE_FIXTURE_HTML = """
<table>
  <thead>
    <tr><th>번호</th><th>제목</th><th>첨부</th><th>작성자</th><th>작성일</th><th>조회</th></tr>
  </thead>
  <tbody>
    <tr class="td-highlight">
      <td class="ta-center"><span class="label label-primary">공지</span></td>
      <td class="ta-left fs-15"><a href="?_0000_method=view&ncode=a001&num=124&page=1"><b>[필독]한국소음진동공학회 회원 FAQ</b></a></td>
      <td class="pd-l15 ta-center">
        <a href="javascript:FileDown('06','x.pdf','y.pdf')" class="file"><img src="/board/icons/pdf.png"></a>
      </td>
      <td class="ta-center">한국소음진동공학회</td>
      <td class="ta-center">2021-03-16</td>
      <td class="ta-center">5541</td>
    </tr>
    <tr>
      <td class="ta-center">267</td>
      <td class="ta-left fs-15"><a href="?_0000_method=view&ncode=a001&num=274&page=1">
        <b>저널레터 : Trans. Korean Soc. Noise Vib. Eng., Vol. 36, No. 4</b></a>
      </td>
      <td class="pd-l15 ta-center"></td>
      <td class="ta-center">한국소음진동공학회</td>
      <td class="ta-center">2026-08-26</td>
      <td class="ta-center">100</td>
    </tr>
  </tbody>
</table>
"""


class FakeResponse:
    def __init__(self, html: str, status_code: int = 200):
        self.text = html
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def test_kiee_collector_parses_pinned_and_numbered_rows_and_skips_attachment_column(monkeypatch):
    def fake_get(url, timeout=None, follow_redirects=None):
        return FakeResponse(_KIEE_FIXTURE_HTML)

    monkeypatch.setattr(board_cms_module.httpx, "get", fake_get)

    items = KIEECollector().collect()

    assert len(items) == 2
    pinned, numbered = items
    assert pinned["external_id"] == "kiee:2644"
    assert pinned["title"] == "산업계 차기회장 추대 안내"
    assert pinned["url"] == "https://www.kiee.or.kr/board/?_0000_method=view&ncode=a001&num=2644&page=1"
    assert pinned["published_at"] == "2026-03-04"
    assert pinned["source"] == "kiee"

    assert numbered["external_id"] == "kiee:2682"
    assert numbered["published_at"] == "2026-09-08"


def test_ksnve_collector_parses_rows_with_a_populated_attachment_cell(monkeypatch):
    def fake_get(url, timeout=None, follow_redirects=None):
        return FakeResponse(_KSNVE_FIXTURE_HTML)

    monkeypatch.setattr(board_cms_module.httpx, "get", fake_get)

    items = KSNVECollector().collect()

    assert len(items) == 2
    pinned, numbered = items
    assert pinned["external_id"] == "ksnve:124"
    assert pinned["title"] == "[필독]한국소음진동공학회 회원 FAQ"
    assert pinned["published_at"] == "2021-03-16"
    assert pinned["source"] == "ksnve"

    assert numbered["external_id"] == "ksnve:274"
    assert numbered["published_at"] == "2026-08-26"


def test_board_cms_collector_returns_empty_on_network_error(monkeypatch):
    def fake_get(url, timeout=None, follow_redirects=None):
        raise ConnectionError("network down")

    monkeypatch.setattr(board_cms_module.httpx, "get", fake_get)

    assert KIEECollector().run() == []
    assert KSNVECollector().run() == []


def test_board_cms_collector_returns_empty_when_no_rows_match(monkeypatch):
    def fake_get(url, timeout=None, follow_redirects=None):
        return FakeResponse("<html><body>redesigned page</body></html>")

    monkeypatch.setattr(board_cms_module.httpx, "get", fake_get)

    assert KIEECollector().collect() == []
    assert KSNVECollector().collect() == []
