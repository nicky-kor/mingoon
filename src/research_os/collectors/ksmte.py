"""KSMTE (한국생산제조학회, Korean Society of Manufacturing Technology
Engineers) notice board collector (Phase 2 Korean-academic-society
sources). No RSS feed; an old-style EUC-KR bulletin board at
/bbs/index.kin?sub=1 (structure confirmed from the site's actual page
source, fetched 2026-09-13). Rows are direct `<table>` children (no
`<tbody>` wrapper): `<tr align="center"><td>번호</td><td><a
href="?mode=view&uid=<id>&no=<n>&...">제목</a></td><td>작성일</td>
<td>조회</td></tr>`.

Fragile by nature (a site redesign breaks the selector below), but
Collector.run() already isolates failures per-source, so a broken parse
here degrades to 0 items for this run rather than failing the pipeline.
"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from research_os.collectors.base import Collector
from research_os.core.logging_setup import get_logger

logger = get_logger("collectors.ksmte")

_BASE_URL = "https://www.ksmte.kr/bbs/index.kin?sub=1"
_UID_RE = re.compile(r"[?&]uid=(\d+)")
_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


class KSMTECollector(Collector):
    source_type = "ksmte"
    source_name = "ksmte"

    def __init__(self, base_url: str | None = None, timeout: float = 20.0) -> None:
        cfg = self._source_config("ksmte")
        self.base_url = base_url or cfg.get("base_url", _BASE_URL)
        self.timeout = timeout

    def _fetch(self) -> str | None:
        try:
            resp = httpx.get(self.base_url, timeout=self.timeout, follow_redirects=True)
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            logger.warning("ksmte fetch failed err=%s", exc)
            return None
        # The site serves EUC-KR (see its own <meta charset>); httpx's
        # default encoding guess mangles the Korean titles, so decode the
        # raw bytes explicitly instead of using resp.text.
        return resp.content.decode("euc-kr", errors="replace")

    def _parse(self, html: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        items: list[dict[str, Any]] = []
        for link in soup.select("a[href*='mode=view']"):
            href = link.get("href", "")
            match = _UID_RE.search(href)
            if match is None:
                continue

            row = link.find_parent("tr")
            date_text = None
            if row is not None:
                title_cell = link.find_parent("td")
                for cell in row.find_all("td"):
                    if cell is title_cell:
                        continue
                    date_match = _DATE_RE.search(cell.get_text(strip=True))
                    if date_match:
                        date_text = date_match.group(0)
                        break

            items.append(
                {
                    "external_id": f"ksmte:{match.group(1)}",
                    "title": link.get_text(strip=True),
                    "url": urljoin(self.base_url, href),
                    "source": "ksmte",
                    "source_type": "ksmte",
                    "published_at": date_text,
                    "authors": ["KSMTE"],
                    "abstract": None,
                    "content": None,
                    "privacy_level": "public",
                }
            )
        return items

    def collect(self) -> list[dict[str, Any]]:
        html = self._fetch()
        if html is None:
            return []
        return self._parse(html)
