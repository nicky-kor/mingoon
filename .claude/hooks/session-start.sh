#!/bin/bash
set -euo pipefail

# Only run dependency installs in a remote (Claude Code on the web) session.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"

# Python
if [ -f requirements.txt ]; then
  python3 -m pip install --user -r requirements.txt
fi
if [ -f pyproject.toml ] && ! [ -f requirements.txt ]; then
  python3 -m pip install --user -e . 2>/dev/null || true
fi

# Node
if [ -f package.json ]; then
  npm install
fi
