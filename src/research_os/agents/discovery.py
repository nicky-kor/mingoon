"""DiscoveryAgent (spec section 29): runs the configured collectors."""
from __future__ import annotations

from typing import Any

from research_os.collectors.arxiv import ArxivCollector
from research_os.collectors.board_cms import KIEECollector, KSNVECollector
from research_os.collectors.github import GitHubCollector
from research_os.collectors.kiie import KIIECollector
from research_os.collectors.ksmte import KSMTECollector
from research_os.collectors.ksphm import KSPHMCollector
from research_os.collectors.rss import RSSCollector
from research_os.core.config import system_config
from research_os.core.logging_setup import get_logger

logger = get_logger("agents.discovery")

_COLLECTOR_REGISTRY = {
    "arxiv": ArxivCollector,
    "rss": RSSCollector,
    "github": GitHubCollector,
    "ksphm": KSPHMCollector,
    "kiie": KIIECollector,
    "ksmte": KSMTECollector,
    "kiee": KIEECollector,
    "ksnve": KSNVECollector,
}


class DiscoveryAgent:
    def discover(self, source: str | None = None) -> list[dict[str, Any]]:
        cfg = system_config().get("sources", {})
        sources = [source] if source else [s for s, c in cfg.items() if c.get("enabled")]

        items: list[dict[str, Any]] = []
        for src in sources:
            collector_cls = _COLLECTOR_REGISTRY.get(src)
            if collector_cls is None:
                logger.warning("unknown source requested: %s", src)
                continue
            collector = collector_cls()
            found = collector.run()
            logger.info("source=%s discovered=%d", src, len(found))
            items.extend(found)
        return items
