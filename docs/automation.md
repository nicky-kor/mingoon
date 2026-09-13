# Automation (Phase 5 draft — not yet wired up)

This is a plan and starter script, not something already running. Nothing
here changes behavior until the user installs the scheduled task
themselves on the target PC. Written so it can be reviewed and adopted (or
adjusted) without live testing from this environment — there's no Windows
Task Scheduler in the sandbox this was drafted in.

## What should run, and how often

| Task | Command | Suggested schedule |
|---|---|---|
| Full pipeline | `research-os run` | Daily, e.g. 07:00 — collects, classifies, summarizes, analyzes, transfer-checks, QA-checks, and marks documents analyzed |
| Daily report | `research-os report daily` | Daily, right after the pipeline run (e.g. 07:15) |
| Weekly report | `research-os report weekly` | Weekly, e.g. Monday 07:30 |

Running the pipeline before the report is important — `report daily`/
`weekly` only read what's already in the database, they don't collect
anything themselves.

## Windows Task Scheduler: one script, two triggers

Rather than configuring `research-os` calls directly inside Task
Scheduler's own UI (fragile — working directory and PATH are easy to get
wrong there), wrap everything in one PowerShell script and let Task
Scheduler just run that:

**`scripts/daily_run.ps1`** (create this file in the repo):

```powershell
# Run from the repo root regardless of Task Scheduler's own working directory.
Set-Location -Path $PSScriptRoot\..

# Activate the project's virtualenv if one exists; otherwise assume
# research-os is already on PATH (e.g. installed with `pip install -e .`
# into the system/user Python, as this project's earlier setup did).
if (Test-Path ".venv\Scripts\Activate.ps1") {
    . .venv\Scripts\Activate.ps1
}

$logFile = "logs\automation-$(Get-Date -Format 'yyyy-MM-dd').log"

research-os run       *>> $logFile
research-os report daily *>> $logFile

# Weekly report only on Mondays (0 = Sunday in .NET's DayOfWeek).
if ((Get-Date).DayOfWeek -eq 'Monday') {
    research-os report weekly *>> $logFile
}
```

`*>> $logFile` appends both stdout and stderr, so a silent failure (e.g.
arXiv rate-limited, or a real crash) is still visible after the fact —
important since a scheduled task has no one watching the terminal.

### Registering it

```powershell
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"C:\Users\jaeho\mingoon\scripts\daily_run.ps1`""
$trigger = New-ScheduledTaskTrigger -Daily -At 7:00am
Register-ScheduledTask -TaskName "ResearchOS Daily Run" -Action $action -Trigger $trigger `
    -Description "Manufacturing AI Research OS: collect -> ... -> report"
```

Check it manually before trusting the schedule:

```powershell
Start-ScheduledTask -TaskName "ResearchOS Daily Run"
Get-ScheduledTaskInfo -TaskName "ResearchOS Daily Run"   # LastRunTime / LastTaskResult
```

`LastTaskResult` of `0` means success; anything else, check the log file
the script wrote.

### Things worth deciding before turning this on

- **PC must be on/awake at 07:00.** Task Scheduler has a "wake the
  computer to run this task" option (`New-ScheduledTaskSettingsSet
  -WakeToRun`) if the PC sleeps — worth enabling, otherwise a missed run
  just silently doesn't happen (Task Scheduler does have "run task as
  soon as possible after a scheduled start is missed" as a related
  setting, `-StartWhenAvailable`, which is the safer default to pair with
  this).
- **Cloud cost while unattended.** The circuit breaker already prevents a
  runaway retry loop against a broken cloud key, but an automated daily
  run against `cloud_reasoning`/`cloud_deep_research` still spends real
  money on a schedule, unattended. Worth checking `research-os status`'s
  "Estimated cost" occasionally, or considering `--no-llm` for the
  automated run and doing LLM-based passes manually until there's a
  comfortable sense of the actual daily cost.
- **arXiv rate limiting.** If the daily run's `collect` stage hits a 429
  at the same time every day, that's a sign the schedule itself (not just
  manual testing) is calling too often — space it out further, or drop
  arXiv from `--source` on some days and let RSS/GitHub/KIIE/KSPHM carry
  those runs.

## Sharing the weekly report

Right now `research-os report weekly` only writes a markdown file to
`data/reports/`. Options for actually seeing it without opening that
folder, roughly in order of setup effort:

1. **Email it to yourself (recommended starting point).** Works well with
   an existing pattern in this project — a phone notification when it's
   ready plays the same role as the `PushNotification`-style "review this
   when you're free" flow already used earlier in this session. Simplest
   version: add a step to `daily_run.ps1`'s weekly branch that sends the
   report file as an email via a script (Python's `smtplib` against
   Gmail's SMTP with an app password, or PowerShell's `Send-MailMessage`
   — deprecated but still functional, or a small `research-os` command
   wrapping `smtplib` so the credential handling stays inside the
   project's own `.env` pattern instead of being pasted into a PS1 file).
   Downside: markdown renders as plain text in most mail clients unless
   converted to HTML first (a `markdown` PyPI package pass would do that
   cheaply).
2. **Drop it in a synced cloud folder** (OneDrive/Dropbox/Google Drive
   desktop client already running on the PC). Change
   `system.yaml`'s `paths.reports` to point inside that synced folder —
   zero new code, and the phone's OneDrive/Drive app already gets a
   notification on a new file. Least effort of any option here.
3. **Push to a private Notion page.** This session has a Notion
   connector available generally (not from inside `research-os` itself,
   which has no network credentials for it) — a natural fit if the user
   already has Claude access to Notion day-to-day: ask a Claude session
   with Notion access to read the week's `data/reports/*-weekly.md` and
   publish/update a page, on the same schedule. Gets comments/sharing/
   mobile access for free from Notion itself.
4. **Slack/Discord webhook.** A single `httpx.post` to an incoming
   webhook URL with the report's Executive Summary section (full markdown
   is usually too long for a chat message) — cheap to add as another
   `research-os` command, good if the user already lives in one of those
   apps.
5. **Publish as a Claude Artifact.** Convert the weekly markdown into a
   small HTML page and publish it (this session's own `Artifact` tool) —
   gets a shareable private link with no extra service to configure, but
   requires this session (or one like it) to be the one doing the
   publishing each week, i.e. it doesn't run unattended from the PC
   itself the way the options above do.

None of these are implemented yet.

### Blog / social platforms (Naver Blog, Instagram, Facebook)

Also worth weighing if the goal is more "keep a public/semi-public
research log" than "just notify myself" — each needs a one-time manual
setup step on the platform itself that only the user can do (registering
a developer app, granting API scopes), before any code here could post
to it automatically.

| Platform | Fit for this content | Setup burden | Notes |
|---|---|---|---|
| **Naver Blog** | Good — long-form, rich text, Korean-native, comments | Medium — register an app at Naver Developers, OAuth client ID/secret, one-time login to get a refresh token | Best match of the three for a full weekly briefing as-is (markdown → Naver's editor format needs a small conversion, but no length/format fight) |
| **Facebook (Page)** | OK for a short summary, not the full report | Medium-high — needs a Facebook Page (not a personal profile — Meta's API doesn't allow posting to personal timelines), a Page access token, and some permission scopes go through Meta's app review even for a single-user tool | Better suited to posting just the Executive Summary + a link/image than the full weekly briefing |
| **Instagram** | Poor for text, needs a visual | High — requires a Business/Creator account linked to a Facebook Page, and Instagram posts need an image (Graph API won't take plain text) | Would need a "카드뉴스"-style summary image generated from the report (e.g. render key stats/priority items onto a template with Pillow) — a real feature to build, not just an API call; lowest priority unless the visual format itself is wanted |

**Recommendation, in order of effort-to-value:**

1. **Synced cloud folder** (above) first — zero setup, immediate mobile
   visibility, good enough while still validating the report's own
   content quality week to week.
2. **Naver Blog** next, once the report content feels worth keeping
   publicly — closest fit to the actual content shape (long, structured,
   Korean), and doubles as a public portfolio of the research work over
   time. Needs the user to register a Naver Developers app first (a
   5-minute manual step) before any posting code is worth writing.
3. **Facebook Page** as a lighter-weight companion to Naver Blog if
   wider reach matters — post the Executive Summary with a link back to
   the full Naver Blog post, rather than trying to fit everything into
   one Facebook post.
4. **Instagram** last, and only as a deliberate content project (auto-
   generated summary cards), not a mechanical repost of the same
   markdown — the format mismatch is real, not just a formatting
   inconvenience.

Email and Notion (above) remain reasonable if the report should stay
private rather than become a public blog/social presence — worth
deciding that before investing in any platform's API setup, since it
changes which option is "better."
