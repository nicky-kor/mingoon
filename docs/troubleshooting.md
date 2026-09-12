# Troubleshooting

## `research-os` command not found

`pip install -e .` (or `pip install -e ".[dev]"` for tests/lint) registers
the console script. If your shell doesn't pick it up, run
`python -m research_os.cli <command>` instead, or check that the
environment's `Scripts`/`bin` directory is on `PATH`.

## arXiv collector returns 0 items

- Check connectivity: `curl https://export.arxiv.org/api/query?search_query=cat:cs.AI&max_results=1`
- Corporate proxy / restricted network: set `HTTPS_PROXY`/`HTTP_PROXY` as
  usual for `httpx`, or check with your network administrator — some
  environments block `export.arxiv.org` outright (this happened in the
  cloud container this project was originally built in; see
  `docs/environment.md`).
- Look at `logs/research_os.log` — `ArxivCollector` logs each retry
  attempt and the final error before giving up; the pipeline itself never
  crashes on a collector failure, it just collects 0 items.

## `research-os models` shows everything unavailable

- Local tiers (`ollama:...`): `ollama serve` isn't running, or the
  `OLLAMA_BASE_URL` in `.env` doesn't match where it's listening (default
  `http://localhost:11434`).
- Cloud tiers (`anthropic:...`): `ANTHROPIC_API_KEY` isn't set in `.env`
  (copy `.env.example` to `.env` and fill it in).
- This is not fatal — every agent has a rule-based/heuristic fallback, so
  `research-os run` still works, just with lower-quality
  classification/summarization/analysis. `research-os status` shows
  whether documents were processed via a model or a fallback
  (`Document.model_used`).

## `sqlite3.OperationalError: unable to open database file`

`data/database/` doesn't exist yet, or the process doesn't have write
permission there. `research-os init` creates it; if you deleted the `data/`
tree, re-run `init`.

## Tests fail with "config file not found"

Run pytest from the project root (or rely on the `pyproject.toml`
`[tool.pytest.ini_options]` `pythonpath`/`testpaths` settings, which assume
the repo root as the working directory) — `research_os.core.paths` resolves
`config/` relative to the installed package location, not the current
working directory, so this should generally not happen; if it does, check
that `config/*.yaml` wasn't accidentally excluded from the install.

## A cloud call is failing but the key looks right

Check `logs/research_os.log` for the exact provider error (rate limit,
invalid model ID, malformed response) — `ModelGateway` logs the message
from `ModelUnavailableError` before falling back to the next tier. Model
IDs live in `config/models.yaml`; a typo or a decommissioned model name
there is a common cause.

## I want to test the pipeline without hitting any real network/API

Every collector, and every agent, has a documented fallback path with zero
external dependencies:

```
research-os collect --source arxiv   # will collect 0 items if network/API is unreachable, not crash
research-os run --no-llm             # skip all LLM calls, use rule-based/heuristic fallback only
```

See `tests/test_pipeline_integration.py` for a fully offline, monkeypatched
example.
