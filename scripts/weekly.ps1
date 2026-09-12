# Weekly maintenance: collect from every enabled source, run the full
# pipeline, generate the weekly briefing, and benchmark whatever models
# are currently reachable.
# Usage: .\scripts\weekly.ps1

$ErrorActionPreference = "Stop"
if (Test-Path ".\.venv\Scripts\Activate.ps1") { . .\.venv\Scripts\Activate.ps1 }

research-os run
research-os report weekly
research-os evaluate
research-os skills

Write-Host ""
Write-Host "Weekly run complete. See data/reports/ for the briefing and benchmark." -ForegroundColor Green
