# UI Proposal (Phase 6 — not built, planning only)

Phase 1-2 deliberately spent no time on UI (everything is CLI + markdown
reports). This is a concrete proposal for what a UI should be *when* it's
built, so Phase 6 has a plan to execute against rather than starting from
a blank page — nothing here changes the running system today.

## Start from the real question: who reads this, and when?

One user (the project owner), checking in a few times a week, mostly on:
- **Weekly review** — "what happened this week, what's worth reading,
  what's flagged."
- **Ad-hoc research** — "let me ask a specific question against what's
  been collected" (`research-os research`).
- **Occasional health check** — "is collection still working, is cloud
  cost under control, did QA flag something concerning."

That's a **dashboard + drill-down** shape, not a multi-user app — no
auth system, no roles, no real-time collaboration needed. This should
stay a local single-page app talking to a local API, not a hosted
service, consistent with the project's local-first design (spec's own
framing: personal tool, no company data, no cloud dependency required).

## Recommended stack (minimal, matches what's already installed)

- **Backend**: FastAPI (already the Phase 6 plan) as a thin read layer
  over the existing SQLAlchemy models — no new business logic, it just
  exposes `pipeline.py`/`reports/_shared.py`'s existing queries as JSON
  endpoints. Write actions (trigger a collect/run) shell out to the
  existing CLI commands rather than duplicating pipeline logic in the API
  layer.
- **Frontend**: A single static HTML/JS page (or a small React build) is
  enough — this is a low-traffic personal dashboard, not a product.
  Server-rendered Jinja templates would also work and skip a JS build
  step entirely if simplicity matters more than interactivity.
- **No new database** — same SQLite file, opened read-mostly by the API.

## Screens, in priority order

### 1. Dashboard (home)

The single screen that should answer "do I need to look at anything
today" in five seconds:

- Stat tiles: documents collected this week, pending/analyzed/failed
  counts, **QA flagged count** (should be visually prominent — it's the
  one number that means "something might be wrong with the data"), local
  vs. cloud LLM call counts + estimated cost this week.
- A short list of the top 5 documents by `overall_score` this week
  (title, priority badge, one-line summary) — click through to detail.
- A small "circuit breaker" status indicator: if `provider_circuit_breaker`
  has an active row for `anthropic`, show it plainly ("cloud unavailable
  until HH:MM, using local") rather than the user discovering it only by
  noticing worse output quality.

### 2. Document list + detail

- List: filterable/sortable table (industry, technology, problem,
  priority, QA status, source_type) over `documents` — this is the one
  screen doing real work, so give it real filtering, not just a static
  table.
- Detail: everything on one `Document` row rendered as sections matching
  the existing report structure (Summary, Analysis scores, Transfer
  opportunity if any, QA flags if any) — basically the daily/weekly
  report's per-document format, but for one document instead of a batch,
  and always current rather than a point-in-time snapshot.
- **QA flags should render inline here, not just in the weekly report** —
  this is where a flag actually matters (deciding whether to trust this
  specific document's numbers), and today it only shows up in a periodic
  report that might not even mention this particular document if it
  falls outside that period's top-N.

### 3. Transfer Radar

A dedicated view over `transfer_opportunities` — this is the project's
stated differentiator (Cross-Industry Technology Transfer), and right now
it's buried as one section of the weekly report. Table: source industry →
target battery process, confidence, expected benefit, research question,
sorted by confidence descending. This is the screen most worth building
early, since it's the one piece of information genuinely hard to get any
other way (a plain document list doesn't surface *why* something from
another industry might matter).

### 4. Trends

Chart over `TrendAgent`'s rising/new-technology output (already computed,
just not visualized) — a simple bar/line view of technology mention
counts over the last few periods would make the "shifting research
direction" purpose of that agent actually visible, instead of only
appearing as a markdown list.

### 5. Skill Graph

Simple tree/list view over `skills` — lower priority than the above since
it's read-rarely (checked in, not something to check daily), but easy to
build once the API layer exists at all (`list_skills()` is already a
clean read function to expose).

### 6. Research (ad-hoc)

A single text box → calls `ResearchAgent.research()` → renders the
FACT/INFERENCE/HYPOTHESIS synthesis with clickable source links. This
is the CLI's `research-os research "..."` command with a UI instead of
stdout — genuinely nice to have, but the CLI already covers this
adequately, so it's last in priority.

## What NOT to build

- **No document editing UI.** Everything here is generated/collected,
  not authored — an edit screen would need conflict-resolution with the
  next pipeline run overwriting it, which isn't worth solving for a
  personal tool.
- **No live collection trigger from the UI, at least initially.** Firing
  `research-os run` from a button click means the API process needs to
  either block on a long-running pipeline call or manage a background
  job queue — real complexity for a feature the Task Scheduler automation
  (`docs/automation.md`) already covers on its own schedule. Add a
  "trigger now" button only after the scheduled automation is stable and
  the UI otherwise has nothing better to spend effort on.
- **No multi-user anything** — accounts, permissions, sharing links —
  unless the actual usage pattern changes from "one person checking their
  own research."

## Suggested build order

1. FastAPI read-only endpoints for documents/scores/transfer/trends/
   skills + QA status — thin wrappers, no new logic.
2. Dashboard + document list/detail (screens 1-2) — this alone replaces
   most of what the daily report does today, interactively.
3. Transfer Radar (screen 3) — the differentiator, worth a dedicated view
   sooner rather than later.
4. Trends + Skill Graph + Research UI (screens 4-6) — nice-to-have,
   build when there's time, no urgency.

This order front-loads the two screens (dashboard, document detail) that
would get used every single check-in, and defers the ones that are
either low-frequency (skills) or already served fine by the CLI
(research).
