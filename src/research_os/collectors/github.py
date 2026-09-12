"""GitHub collector (spec section 22, Phase 2).

Uses the public GitHub search API (unauthenticated, rate-limited to 10
requests/min). Set GITHUB_TOKEN in .env to raise that limit; not required
for Phase 1.
"""
from __future__ import annotations

import os
import time
from typing import Any

import httpx

from research_os.collectors.base import Collector
from research_os.core.config import system_config
from research_os.core.logging_setup import get_logger

logger = get_logger("collectors.github")


class GitHubCollector(Collector):
    source_type = "github"
    source_name = "github"

    def __init__(
        self,
        topics: list[str] | None = None,
        api_url: str | None = None,
        per_topic_limit: int = 5,
        timeout: float = 20.0,
    ) -> None:
        cfg = system_config().get("sources", {}).get("github", {})
        self.topics = topics or cfg.get("topics", [])
        self.api_url = api_url or cfg.get("api_url", "https://api.github.com/search/repositories")
        self.per_topic_limit = per_topic_limit
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/vnd.github+json"}
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _search(self, topic: str) -> list[dict[str, Any]]:
        params = {"q": topic, "sort": "stars", "order": "desc", "per_page": self.per_topic_limit}
        try:
            resp = httpx.get(self.api_url, params=params, headers=self._headers(), timeout=self.timeout)
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            logger.warning("github search failed topic=%s err=%s", topic, exc)
            return []

        data = resp.json()
        items = []
        for repo in data.get("items", []):
            items.append(
                {
                    "external_id": f"github:{repo['full_name']}",
                    "github_url": repo.get("html_url"),
                    "title": repo.get("full_name"),
                    "url": repo.get("html_url"),
                    "source": "github",
                    "source_type": "github",
                    "published_at": repo.get("created_at"),
                    "authors": [repo.get("owner", {}).get("login")] if repo.get("owner") else [],
                    "abstract": repo.get("description"),
                    "content": None,
                    "keywords": [topic],
                    "privacy_level": "public",
                }
            )
        return items

    def collect(self) -> list[dict[str, Any]]:
        if not self.topics:
            return []
        all_items: list[dict[str, Any]] = []
        for topic in self.topics:
            all_items.extend(self._search(topic))
            time.sleep(1.0)  # stay under the unauthenticated rate limit
        return all_items
