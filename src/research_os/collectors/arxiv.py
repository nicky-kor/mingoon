"""arXiv collector (spec section 22).

Queries the public arXiv Atom API (export.arxiv.org). No API key required.
`base_url` is overridable so tests can point this at a local fixture server
instead of the real network.
"""
from __future__ import annotations

import time
from typing import Any

import feedparser
import httpx

from research_os.collectors.base import Collector, CollectorError
from research_os.core.config import system_config
from research_os.core.logging_setup import get_logger

logger = get_logger("collectors.arxiv")


class ArxivCollector(Collector):
    source_type = "arxiv"
    source_name = "arxiv"

    def __init__(
        self,
        categories: list[str] | None = None,
        max_results: int | None = None,
        base_url: str | None = None,
        timeout: float = 20.0,
        max_retries: int = 2,
    ) -> None:
        cfg = system_config().get("sources", {}).get("arxiv", {})
        self.categories = categories if categories is not None else cfg.get("categories", ["cs.AI"])
        self.max_results = max_results if max_results is not None else cfg.get("max_results_per_run", 25)
        self.base_url = base_url or cfg.get("base_url", "http://export.arxiv.org/api/query")
        self.timeout = timeout
        self.max_retries = max_retries

    def _build_query(self) -> str:
        return " OR ".join(f"cat:{c}" for c in self.categories)

    def _fetch(self) -> str:
        params = {
            "search_query": self._build_query(),
            "start": 0,
            "max_results": self.max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        last_exc: Exception | None = None
        for attempt in range(1, self.max_retries + 2):
            try:
                resp = httpx.get(self.base_url, params=params, timeout=self.timeout)
                resp.raise_for_status()
                return resp.text
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                logger.warning("arxiv fetch attempt %d failed: %s", attempt, exc)
                time.sleep(min(2 ** attempt, 8))
        raise CollectorError(f"arXiv fetch failed after retries: {last_exc}")

    @staticmethod
    def _extract_arxiv_id(entry_id: str) -> str:
        # entry.id looks like http://arxiv.org/abs/2401.01234v1
        tail = entry_id.rstrip("/").split("/")[-1]
        return tail.split("v")[0] if "v" in tail and tail.split("v")[-1].isdigit() else tail

    def collect(self) -> list[dict[str, Any]]:
        if not self.categories:
            return []
        raw_xml = self._fetch()
        feed = feedparser.parse(raw_xml)
        if getattr(feed, "bozo", 0) and not feed.entries:
            raise CollectorError(f"arXiv feed parse error: {feed.bozo_exception}")

        items: list[dict[str, Any]] = []
        for entry in feed.entries:
            arxiv_id = self._extract_arxiv_id(entry.get("id", ""))
            items.append(
                {
                    "external_id": f"arxiv:{arxiv_id}",
                    "arxiv_id": arxiv_id,
                    "title": entry.get("title", "").strip(),
                    "url": entry.get("link"),
                    "source": "arxiv",
                    "source_type": "arxiv",
                    "published_at": entry.get("published"),
                    "authors": [a.get("name") for a in entry.get("authors", []) if a.get("name")],
                    "abstract": entry.get("summary", "").strip(),
                    "content": None,
                    "privacy_level": "public",
                }
            )
        return items
