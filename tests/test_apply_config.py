from research_os.evaluation.apply_config import apply_role_selection_to_models_yaml

_SAMPLE_YAML = """\
providers:
  ollama:
    kind: "local"

tiers:
  local_fast:
    provider: ollama
    model: "qwen2.5:3b-instruct"
  local_standard:
    provider: ollama
    model: "qwen2.5:7b-instruct"
  local_reasoning:
    provider: ollama
    model: "deepseek-r1:7b"
  cloud_fast:
    provider: anthropic
    model: "claude-haiku-4-5-20251001"
"""


def test_apply_updates_only_matching_tiers(tmp_path):
    config_path = tmp_path / "models.yaml"
    config_path.write_text(_SAMPLE_YAML, encoding="utf-8")

    changes = apply_role_selection_to_models_yaml(
        {"local_fast": "gemma2:2b", "local_reasoning": None}, config_path=config_path,
    )

    content = config_path.read_text(encoding="utf-8")
    assert 'local_fast:\n    provider: ollama\n    model: "gemma2:2b"' in content
    assert 'model: "qwen2.5:7b-instruct"' in content  # local_standard untouched
    assert 'model: "deepseek-r1:7b"' in content  # local_reasoning untouched (None selection)
    assert 'model: "claude-haiku-4-5-20251001"' in content  # cloud tier untouched
    assert any("local_fast" in c for c in changes)


def test_apply_is_a_noop_when_already_matching(tmp_path):
    config_path = tmp_path / "models.yaml"
    config_path.write_text(_SAMPLE_YAML, encoding="utf-8")

    changes = apply_role_selection_to_models_yaml({"local_fast": "qwen2.5:3b-instruct"}, config_path=config_path)

    assert changes == []


def test_apply_warns_on_unknown_tier(tmp_path):
    config_path = tmp_path / "models.yaml"
    config_path.write_text(_SAMPLE_YAML, encoding="utf-8")

    changes = apply_role_selection_to_models_yaml({"local_nonexistent": "some-model"}, config_path=config_path)

    assert any("WARNING" in c for c in changes)
