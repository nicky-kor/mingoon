"""CLI wiring tests: catches argument-parsing/import mistakes that unit
tests of the underlying functions can't (e.g. a command referencing a
function that was renamed, a missing import, a bad Typer option). Uses
`isolated_db` so these never touch the real dev database.
"""
from typer.testing import CliRunner

from research_os.cli import app
from research_os.models.anthropic import AnthropicAdapter
from research_os.models.local import OllamaAdapter

runner = CliRunner()


def test_init_runs_successfully(isolated_db):
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert "initialized" in result.stdout.lower()


def test_status_runs_successfully(isolated_db, monkeypatch):
    monkeypatch.setattr(OllamaAdapter, "is_available", lambda self: False)
    monkeypatch.setattr(AnthropicAdapter, "is_available", lambda self: False)

    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "Research OS Status" in result.stdout
    assert "Documents: 0" in result.stdout


def test_models_runs_successfully(isolated_db, monkeypatch):
    monkeypatch.setattr(OllamaAdapter, "is_available", lambda self: False)
    monkeypatch.setattr(AnthropicAdapter, "is_available", lambda self: False)

    result = runner.invoke(app, ["models"])
    assert result.exit_code == 0
    assert "local_fast" in result.stdout
    assert "unavailable" in result.stdout


def test_skills_runs_successfully(isolated_db):
    result = runner.invoke(app, ["skills"])
    assert result.exit_code == 0
    assert "Predictive Maintenance" in result.stdout


def test_collect_with_unknown_source_runs_without_crashing(isolated_db):
    result = runner.invoke(app, ["collect", "--source", "not-a-real-source"])
    assert result.exit_code == 0
    assert "discovered=0" in result.stdout


def test_evaluate_reports_blocked_when_ollama_unavailable(isolated_db, tmp_path, monkeypatch):
    import research_os.core.paths as paths_module

    monkeypatch.setattr(OllamaAdapter, "is_available", lambda self: False)
    monkeypatch.setattr(paths_module, "resolve", lambda p: tmp_path)

    result = runner.invoke(app, ["evaluate"])
    assert result.exit_code == 0
    assert "BLOCKED" in result.stdout or "UNKNOWN" in result.stdout


def test_benchmark_apply_fails_cleanly_with_no_data(isolated_db):
    result = runner.invoke(app, ["benchmark-apply"])
    assert result.exit_code == 1
    assert "run" in result.stdout.lower()


def test_report_daily_runs_without_llm(isolated_db, tmp_path, monkeypatch):
    import research_os.reports.daily as daily_module

    monkeypatch.setattr(daily_module, "resolve", lambda p: tmp_path)

    result = runner.invoke(app, ["report", "daily", "--no-llm"])
    assert result.exit_code == 0
    assert "Daily report written to" in result.stdout
    assert list(tmp_path.glob("*-daily.md"))


def test_report_weekly_runs_without_llm(isolated_db, tmp_path, monkeypatch):
    import research_os.reports.weekly as weekly_module

    monkeypatch.setattr(weekly_module, "resolve", lambda p: tmp_path)

    result = runner.invoke(app, ["report", "weekly", "--no-llm"])
    assert result.exit_code == 0
    assert "Weekly report written to" in result.stdout
    assert list(tmp_path.glob("*-weekly.md"))
