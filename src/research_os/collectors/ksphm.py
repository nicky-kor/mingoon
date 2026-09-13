"""KSPHM (한국PHM학회, Korean Society for Prognostics and Health Management)
notice board collector (spec section 22, Phase 2).

KSPHM publishes no RSS feed -- its announcements live in an old-style PHP
bulletin board (EUC-KR encoded) at /info/notice.php, built from the site's
actual page source (fetched 2026-09-13). Structure: a `<table
class="sol_table">` whose `<tbody>` rows each have 6 *direct* `<td>`
children (blank, 번호/공지, 제목 [a nested table holding the title link],
작성자, 작성일 as "YY.MM.DD", 조회) -- `recursive=False` matters because the
제목 cell itself contains a nested `<table>` with more `<td>`s that would
otherwise pollute a naive `find_all("td")`.

Fragile by nature (a site redesign breaks the selectors below), but
Collector.run() already isolates failures per-source, so a broken parse
here degrades to 0 items for this run rather than failing the pipeline.
"""
from __future__ import annotations

import datetime as dt
import re
from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from research_os.collectors.base import Collector
from research_os.core.logging_setup import get_logger

logger = get_logger("collectors.ksphm")

_BASE_URL = "https://www.phm.or.kr/info/notice.php"
_DETAIL_ID_RE = re.compile(r"idx=(\d+)")
_DATE_RE = re.compile(r"(\d{2})\.(\d{2})\.(\d{2})$")


class KSPHMCollector(Collector):
    source_type = "ksphm"
    source_name = "ksphm"

    def __init__(self, base_url: str | None = None, pages: int | None = None, timeout: float = 20.0) -> None:
        cfg = self._source_config("ksphm")
        self.base_url = base_url or cfg.get("base_url", _BASE_URL)
        self.pages = pages if pages is not None else int(cfg.get("pages", 1))
        self.timeout = timeout

    def _fetch_page(self, page: int) -> list[dict[str, Any]]:
        try:
            resp = httpx.get(
                self.base_url, params={"code": "notice", "page": page}, timeout=self.timeout, follow_redirects=True
            )
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            logger.warning("ksphm fetch failed page=%d err=%s", page, exc)
            return []

        # The site serves EUC-KR (see its own <meta charset>); httpx's
        # default encoding guess mangles the Korean titles, so decode the
        # raw bytes explicitly instead of using resp.text.
        html = resp.content.decode("euc-kr", errors="replace")
        return self._parse(html)

    def _parse(self, html: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        table = soup.select_one("table.sol_table")
        if table is None:
            return []

        tbody = table.find("tbody")
        if tbody is None:
            return []

        items: list[dict[str, Any]] = []
        # recursive=False matters: each row's 제목 cell wraps its title
        # link in its own nested <table><tr><td>, and a plain "tbody tr"
        # CSS selector doesn't respect table boundaries -- it would also
        # match those inner rows since they're still technically
        # descendants of this outer tbody, double-counting every row.
        for row in tbody.find_all("tr", recursive=False):
            link = row.select_one("a[href*='ptype=view']")
            if link is None:
                continue
            href = link.get("href", "")
            match = _DETAIL_ID_RE.search(href)
            if match is None:
                continue

            cells = row.find_all("td", recursive=False)
            date_text = cells[4].get_text(strip=True) if len(cells) >= 5 else ""

            items.append(
                {
                    "external_id": f"ksphm:{match.group(1)}",
                    "title": link.get_text(strip=True),
                    "url": urljoin(self.base_url, href),
                    "source": "ksphm",
                    "source_type": "ksphm",
                    "published_at": self._parse_date(date_text),
                    "authors": ["KSPHM"],
                    "abstract": None,
                    "content": None,
                    "privacy_level": "public",
                }
            )
        return items

    @staticmethod
    def _parse_date(text: str) -> str | None:
        # Rendered as "26.09.07" (YY.MM.DD) -- assume 2000s.
        match = _DATE_RE.match(text.strip())
        if not match:
            return None
        yy, mm, dd = match.groups()
        try:
            return dt.date(2000 + int(yy), int(mm), int(dd)).isoformat()
        except ValueError:
            return None

    def collect(self) -> list[dict[str, Any]]:
        all_items: list[dict[str, Any]] = []
        for page in range(1, self.pages + 1):
            all_items.extend(self._fetch_page(page))
        return all_items
