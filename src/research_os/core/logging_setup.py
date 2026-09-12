"""Logging setup: rotating file handler + console, used for observability.

Every LLM call and pipeline stage should log through this so that
timestamp/agent/task/model/provider/latency/tokens/cost/status/error are
all captured (see docs/architecture.md, section: Observability).
"""
from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

from research_os.core.config import system_config
from research_os.core.paths import resolve

_CONFIGURED = False


def setup_logging() -> logging.Logger:
    global _CONFIGURED
    logger = logging.getLogger("research_os")
    if _CONFIGURED:
        return logger

    cfg = system_config().get("logging", {})
    level = getattr(logging, str(cfg.get("level", "INFO")).upper(), logging.INFO)
    log_file: Path = resolve(cfg.get("file", "logs/research_os.log"))
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger.setLevel(level)
    logger.propagate = False

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
    )

    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=int(cfg.get("max_bytes", 5_242_880)),
        backupCount=int(cfg.get("backup_count", 5)),
        encoding="utf-8",
    )
    file_handler.setFormatter(fmt)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)

    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    _CONFIGURED = True
    return logger


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(f"research_os.{name}")
