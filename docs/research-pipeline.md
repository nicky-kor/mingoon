# Research Pipeline

## Stages

| Stage | Function | CLI |
|---|---|---|
| Collect | `pipeline.collect_and_store` | `research-os collect [--source arxiv\|rss\|github]` |
| Normalize | `processing/normalize.py` | (part of collect) |
| Deduplicate | `processing/deduplicate.py` | (part of collect) |
| Classify | `pipeline.run_classify` | `research-os classify` |
| Summarize/Extract | `pipeline.run_summarize` | `research-os summarize` |
| Analyze (evidence/practical/novelty + battery relevance + score) | `pipeline.run_analyze` | `research-os analyze` |
| Transfer analysis | `pipeline.run_transfer` | `research-os transfer` |
| Store | `pipeline.mark_analyzed` | (part of `run`) |
| Report | `reports/daily.py`, `reports/weekly.py` | `research-os report daily\|weekly` |

`research-os run` chains collect → classify → summarize → analyze →
transfer → store in one call. Every stage function only touches documents
that still need that stage (e.g. `run_classify` skips documents that
already have an `industry` set), so re-running a stage, or running `run`
again after adding new documents, is safe and idempotent.

## Deduplication priority (spec section 24)

DOI → arXiv ID → URL → GitHub URL → normalized title → content hash
(`processing/deduplicate.find_existing`). A document that matches any of
these against an existing row is never re-inserted or re-sent to an LLM.

## Evidence discipline (spec section 21)

Prompts to `AnalystAgent`, `TransferAgent`, and `ResearchAgent` explicitly
instruct the model not to invent facts, papers, or numbers, and to
distinguish FACT / INFERENCE / HYPOTHESIS. `ResearchAgent` in particular
only synthesizes over documents actually retrieved from the local
database (`agents/researcher.py`) — it never fabricates a citation.

## Deep Research (`research-os research "<question>"`)

```
Question -> search local documents (title/abstract keyword match)
         -> format as sources
         -> LLM synthesis grounded strictly in those sources
            (or an extractive fallback listing the matched documents,
             if no LLM is configured)
         -> written to data/reports/research-<slug>-<timestamp>.md
```

## Reports

`research-os report daily` and `report weekly` query the database directly
for their facts (top-scored documents, transfer opportunities, technology
trend counts, skill levels); the LLM, when available, is only used for the
executive-summary paragraph on top of those already-computed facts, never
as their source (see `agents/briefing.py`).
