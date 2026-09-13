"""KIIE (대한산업공학회, Korean Institute of Industrial Engineers) notices
collector (spec section 22, Phase 2).

KIIE publishes no RSS feed, and its full notice board is a classic ASP
listing (/Board/Board.asp?b_Cate=BBS1) whose structure hasn't been
confirmed. Instead this reads the "Announcements" widget already
embedded on the KIIE homepage itself (`div.anooun_news table`, verified
from the site's actual homepage source fetched 2026-09-13) -- it lists
the 5 most recent 공지사항 items with title, link, and an ISO-formatted
date, the same information a full board scrape would need pagination
and extra guesswork to get.

Fragile by nature (a homepage redesign breaks the selector below), but
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

logger = get_logger("collectors.kiie")

_BASE_URL = "https://kiie.org/"
_DETAIL_ID_RE = re.compile(r"b_code=(\d+)")


class KIIECollector(Collector):
    source_type = "kiie"
    source_name = "kiie"

    def __init__(self, base_url: str | None = None, timeout: float = 20.0) -> None:
        cfg = self._source_config("kiie")
        self.base_url = base_url or cfg.get("base_url", _BASE_URL)
        self.timeout = timeout

    def _fetch(self) -> str | None:
        try:
            resp = httpx.get(self.base_url, timeout=self.timeout, follow_redirects=True)
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            logger.warning("kiie fetch failed err=%s", exc)
            return None
        # The site serves EUC-KR (see its own <meta charset>); decode the
        # raw bytes explicitly rather than trusting resp.text's guess.
        return resp.content.decode("euc-kr", errors="replace")

    def _parse(self, html: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        container = soup.select_one("div.anooun_news")
        if container is None:
            return []

        items: list[dict[str, Any]] = []
        for link in container.select("a[href*='b_code=']"):
            href = link.get("href", "")
            match = _DETAIL_ID_RE.search(href)
            if match is None:
                continue
            row = link.find_parent("tr")
            date_cell = row.select_one("td.rig_t") if row else None
            items.append(
                {
                    "external_id": f"kiie:{match.group(1)}",
                    "title": link.get_text(strip=True),
                    "url": urljoin(self.base_url, href),
                    "source": "kiie",
                    "source_type": "kiie",
                    "published_at": date_cell.get_text(strip=True) if date_cell else None,
                    "authors": ["KIIE"],
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
