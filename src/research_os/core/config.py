"""Configuration loading.

All tunable knobs (taxonomies, model names, routing rules, scoring weights)
live in config/*.yaml, never hardcoded in Python. This module loads and
caches them, and resolves `${VAR}` / `${VAR:-default}` placeholders against
environment variables.
"""
from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from research_os.core.paths import CONFIG_DIR, PROJECT_ROOT

load_dotenv(PROJECT_ROOT / ".env")

_ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(:-(.*?))?\}")


def _expand_env(value: Any) -> Any:
    if isinstance(value, str):
        def repl(match: re.Match) -> str:
            var, _, default = match.groups()
            return os.environ.get(var, default or "")

        return _ENV_PATTERN.sub(repl, value)
    if isinstance(value, dict):
        return {k: _expand_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env(v) for v in value]
    return value


@lru_cache(maxsize=None)
def load_yaml(name: str) -> dict:
    """Load and cache a YAML config file by name (without .yaml extension)."""
    path: Path = CONFIG_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    return _expand_env(raw)


def clear_cache() -> None:
    load_yaml.cache_clear()


def system_config() -> dict:
    return load_yaml("system")


def models_config() -> dict:
    return load_yaml("models")


def routing_config() -> dict:
    return load_yaml("routing")


def agents_config() -> dict:
    return load_yaml("agents")


def scoring_config() -> dict:
    return load_yaml("scoring")


def industries_config() -> dict:
    return load_yaml("industries")


def technologies_config() -> dict:
    return load_yaml("technologies")


def problems_config() -> dict:
    return load_yaml("problems")


def battery_config() -> dict:
    return load_yaml("battery")
