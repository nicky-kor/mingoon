# Run one full collection + analysis pass.
# Usage: .\scripts\collect.ps1 [-Source arxiv|rss|github]

param(
    [string]$Source = ""
)

$ErrorActionPreference = "Stop"
if (Test-Path ".\.venv\Scripts\Activate.ps1") { . .\.venv\Scripts\Activate.ps1 }

if ($Source -ne "") {
    research-os collect --source $Source
} else {
    research-os collect
}

research-os classify
research-os summarize
research-os analyze
research-os transfer
research-os report daily
