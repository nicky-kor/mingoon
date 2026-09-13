"""RSS/Atom collector (spec section 22, Phase 2).

Feed URLs come from config/system.yaml `sources.rss.feeds`. Implemented in
Phase 1 already since feedparser handles both RSS and Atom generically, but
disabled by default until the user configures feeds.
"""
from __future__ import annotations

import time
from typing import Any

import feedparser
import httpx

from research_os.collectors.base import Collector
from research_os.core.logging_setup import get_logger

logger = get_logger("collectors.rss")


class RSSCollector(Collector):
    source_type = "rss"
    source_name = "rss"

    def __init__(self, feeds: list[str] | None = None, timeout: float = 20.0) -> None:
        cfg = self._source_config("rss")
        self.feeds = feeds if feeds is not None else cfg.get("feeds", [])
        self.timeout = timeout

    def _fetch_one(self, feed_url: str) -> list[dict[str, Any]]:
        try:
            resp = httpx.get(feed_url, timeout=self.timeout, follow_redirects=True)
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)
        except Exception as exc:  # noqa: BLE001
            logger.warning("rss feed failed url=%s err=%s", feed_url, exc)
            return []

        items = []
        for entry in feed.entries:
            link = entry.get("link", "")
            items.append(
                {
                    "external_id": f"rss:{link or entry.get('id', entry.get('title', ''))}",
                    "title": entry.get("title", "").strip(),
                    "url": link,
                    "source": feed_url,
                    "source_type": "rss",
                    "published_at": entry.get("published"),
                    "authors": [entry.get("author")] if entry.get("author") else [],
                    "abstract": entry.get("summary", "").strip() if entry.get("summary") else None,
                    "content": None,
                    "privacy_level": "public",
                }
            )
        return items

    def collect(self) -> list[dict[str, Any]]:
        if not self.feeds:
            return []
        all_items: list[dict[str, Any]] = []
        for feed_url in self.feeds:
            all_items.extend(self._fetch_one(feed_url))
            time.sleep(0.2)
        return all_items
