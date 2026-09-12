"""Apply real benchmark results to config/models.yaml (spec section 12/18).

Edits only the `model:` line inside the matching tier block via a targeted
regex substitution — never a full YAML re-dump — so the file's comments
and structure (including the tiers this benchmark didn't touch, like the
cloud tiers) are preserved exactly. Only tiers with an actual selected
model are changed; a tier the benchmark marked UNKNOWN/BLOCKED is left as
whatever it was already configured to.
"""
from __future__ import annotations

import re
from pathlib import Path

from research_os.core.config import clear_cache
from research_os.core.paths import CONFIG_DIR

_TIER_PATTERN = (
    r'(^([ \t]*){tier}:\s*\n'
    r'[ \t]*provider:[^\n]*\n'
    r'[ \t]*model:\s*)"[^"]*"'
)


def apply_role_selection_to_models_yaml(
    role_selection: dict[str, str | None], config_path: Path | None = None,
) -> list[str]:
    """role_selection: {"local_fast": "qwen2.5:3b-instruct", ...}. Returns a
    list of human-readable change descriptions (empty if nothing changed)."""
    path = config_path or (CONFIG_DIR / "models.yaml")
    content = path.read_text(encoding="utf-8")
    changes: list[str] = []

    for tier, model in role_selection.items():
        if not model:
            continue
        pattern = re.compile(_TIER_PATTERN.format(tier=re.escape(tier)), re.MULTILINE)
        match = pattern.search(content)
        if not match:
            changes.append(f"WARNING: could not find a `{tier}:` tier block to update (skipped)")
            continue
        old_model_match = re.search(r'model:\s*"([^"]*)"', match.group(0))
        old_model = old_model_match.group(1) if old_model_match else "?"
        if old_model == model:
            continue  # already set, nothing to change
        content = pattern.sub(lambda m, model=model: f'{m.group(1)}"{model}"', content, count=1)
        changes.append(f"{tier}: {old_model} -> {model}")

    if changes:
        path.write_text(content, encoding="utf-8")
        clear_cache()

    return changes
