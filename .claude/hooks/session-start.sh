#!/bin/bash
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

python3 -m pip install --user -r "$CLAUDE_PROJECT_DIR/requirements.txt"
