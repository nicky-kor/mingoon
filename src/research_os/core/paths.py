"""Central path resolution for the project.

All paths are resolved relative to the project root, which is found by
walking up from this file, so the CLI works regardless of the current
working directory it is invoked from.
"""
from __future__ import annotations

from pathlib import Path

# src/research_os/core/paths.py -> project root is 3 parents up.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"


def resolve(relative_path: str) -> Path:
    """Resolve a path from system.yaml (relative to project root) to absolute."""
    p = Path(relative_path)
    if p.is_absolute():
        return p
    return PROJECT_ROOT / p
