"""Shared collector for the "ncode="-style Korean society board CMS used by
한국소음진동공학회 (KSNVE) and 대한전기학회 (KIEE) -- confirmed to be the same
vendor board software from both sites' actual page source (fetched
2026-09-13): identical query-string shape for a post link
(`?_0000_method=view&ncode=<board>&num=<id>&page=<n>`) and identical CSS
scaffolding (`td.title`, `tr.td-highlight` for pinned rows, `hidden-xs`
utility classes). One parser, one thin subclass per site.

Deliberately column-position-independent: KIEE's table has an extra "첨부"
(attachment) column KSNVE's doesn't, so instead of indexing `td`s by
position this finds the title link directly and then scans the row's
*other* cells for a YYYY-MM-DD date, skipping the title cell itself so a
title that happens to contain a date-shaped substring can't be picked up
as the published date.

Fragile by nature (a site redesign breaks the selectors below), but
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

logger = get_logger("collectors.board_cms")

_NUM_RE = re.compile(r"[?&]num=(\d+)")
_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


class BoardCMSCollector(Collector):
    """Base class. Subclasses set source_type/source_name/_default_base_url."""

    _default_base_url: str = ""

    def __init__(self, base_url: str | None = None, timeout: float = 20.0) -> None:
        cfg = self._source_config(self.source_type)
        self.base_url = base_url or cfg.get("base_url", self._default_base_url)
        self.timeout = timeout

    def _fetch(self) -> str | None:
        try:
            resp = httpx.get(self.base_url, timeout=self.timeout, follow_redirects=True)
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            logger.warning("%s fetch failed err=%s", self.source_type, exc)
            return None
        # Both sites serve UTF-8 (confirmed via their own <meta charset>),
        # unlike KIIE/KSPHM/KSMTE's EUC-KR -- httpx's default decode is fine here.
        return resp.text

    def _parse(self, html: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        items: list[dict[str, Any]] = []
        for row in soup.select("table tbody tr"):
            link = row.select_one("a[href*='_0000_method=view']")
            if link is None:
                continue
            href = link.get("href", "")
            match = _NUM_RE.search(href)
            if match is None:
                continue

            title_cell = link.find_parent("td")
            date_text = None
            for cell in row.find_all("td"):
                if cell is title_cell:
                    continue
                date_match = _DATE_RE.search(cell.get_text(strip=True))
                if date_match:
                    date_text = date_match.group(0)
                    break

            items.append(
                {
                    "external_id": f"{self.source_type}:{match.group(1)}",
                    "title": link.get_text(strip=True),
                    "url": urljoin(self.base_url, href),
                    "source": self.source_name,
                    "source_type": self.source_type,
                    "published_at": date_text,
                    "authors": [self.source_name.upper()],
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


class KIEECollector(BoardCMSCollector):
    source_type = "kiee"
    source_name = "kiee"
    _default_base_url = "https://www.kiee.or.kr/board/?ncode=a001"


class KSNVECollector(BoardCMSCollector):
    source_type = "ksnve"
    source_name = "ksnve"
    _default_base_url = "https://www.ksnve.or.kr/board/?ncode=a001"
