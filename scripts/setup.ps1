# Manufacturing AI Research OS — first-time setup (Windows PowerShell)
# Run from the project root: .\scripts\setup.ps1

$ErrorActionPreference = "Stop"

Write-Host "== Manufacturing AI Research OS setup ==" -ForegroundColor Cyan

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python 3.11+ not found on PATH. Install it from https://www.python.org/downloads/ first."
    exit 1
}

python -m venv .venv
. .\.venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install -e ".[dev]"

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example — edit it to add your ANTHROPIC_API_KEY (optional)." -ForegroundColor Yellow
}

research-os init

Write-Host ""
Write-Host "Setup complete. Try:" -ForegroundColor Green
Write-Host "  research-os status"
Write-Host "  research-os collect --source arxiv"
Write-Host "  research-os run"
Write-Host "  research-os report daily"

if (Get-Command ollama -ErrorAction SilentlyContinue) {
    Write-Host ""
    Write-Host "Ollama detected. Consider pulling a small starter model:" -ForegroundColor Cyan
    Write-Host "  ollama pull qwen2.5:3b-instruct"
} else {
    Write-Host ""
    Write-Host "Ollama not found — that's fine, the pipeline runs on rule-based fallback." -ForegroundColor DarkYellow
    Write-Host "Install from https://ollama.com if you want local LLM support (see docs/local-llm.md)."
}
