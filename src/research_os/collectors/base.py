"""Collector plugin interface (spec section 22).

Every source (arXiv, RSS, GitHub, ...) implements `Collector.collect()` and
returns a list of raw dicts. A collector must never raise out of `run()` —
failures are caught and logged so one bad source cannot halt the pipeline
(spec section 44/24 reliability).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from research_os.core.logging_setup import get_logger

logger = get_logger("collectors")


class CollectorError(Exception):
    pass


class Collector(ABC):
    source_type: str = "unknown"
    source_name: str = "unknown"

    @abstractmethod
    def collect(self) -> list[dict[str, Any]]:
        """Return a list of raw item dicts. May raise CollectorError."""
        raise NotImplementedError

    def run(self) -> list[dict[str, Any]]:
        """Safe wrapper: never raises, always returns a (possibly empty) list."""
        try:
            items = self.collect()
            logger.info("collector=%s collected=%d", self.source_name, len(items))
            return items
        except Exception as exc:  # noqa: BLE001 - intentional broad catch for reliability
            logger.error("collector=%s failed: %s", self.source_name, exc)
            return []
