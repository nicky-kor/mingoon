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
from research_os.core.logging_setup import get_logger

logger = get_logger("collectors.arxiv")

# arXiv's API Terms of Use ask clients to identify themselves via
# User-Agent (https://info.arxiv.org/help/api/tou.html) — an anonymous
# default UA (httpx's own) is more likely to get rate-limited (429).
_USER_AGENT = "manufacturing-ai-research-os/0.1 (personal research project; https://github.com/nicky-kor/mingoon)"


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
        cfg = self._source_config("arxiv")
        self.categories = categories if categories is not None else cfg.get("categories", ["cs.AI"])
        self.max_results = max_results if max_results is not None else cfg.get("max_results_per_run", 25)
        self.base_url = base_url or cfg.get("base_url", "https://export.arxiv.org/api/query")
        self.timeout = timeout
        self.max_retries = max_retries

    def _build_query(self) -> str:
        return " OR ".join(f"cat:{c}" for c in self.categories)

    @staticmethod
    def _retry_delay(attempt: int, response: httpx.Response | None) -> float:
        """arXiv's rate limiting (HTTP 429) needs a longer, Retry-After-aware
        backoff than a generic network hiccup — retrying a 429 quickly just
        gets rate-limited again (this is exactly what happened before this
        was added: two attempts ~2s apart both got 429, the third timed out)."""
        if response is not None and response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    return float(retry_after)
                except ValueError:
                    pass
            return 15.0 * attempt
        return min(5.0 * attempt, 30.0)

    def _fetch(self) -> str:
        params = {
            "search_query": self._build_query(),
            "start": 0,
            "max_results": self.max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        headers = {"User-Agent": _USER_AGENT}
        last_exc: Exception | None = None
        for attempt in range(1, self.max_retries + 2):
            try:
                resp = httpx.get(
                    self.base_url, params=params, headers=headers, timeout=self.timeout, follow_redirects=True,
                )
                resp.raise_for_status()
                return resp.text
            except httpx.HTTPStatusError as exc:
                last_exc = exc
                wait = self._retry_delay(attempt, exc.response)
                logger.warning("arxiv fetch attempt %d failed: %s (retrying in %.0fs)", attempt, exc, wait)
                time.sleep(wait)
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                wait = self._retry_delay(attempt, None)
                logger.warning("arxiv fetch attempt %d failed: %s (retrying in %.0fs)", attempt, exc, wait)
                time.sleep(wait)
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
