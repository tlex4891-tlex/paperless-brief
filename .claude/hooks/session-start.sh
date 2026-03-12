#!/bin/bash
set -euo pipefail

# Only run in Claude Code on the web (remote environment)
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

echo "==> Syncing global CLAUDE.md from tlex4891-tlex/claude-global-config..."

mkdir -p "$HOME/.claude"

curl -fsSL \
  "https://raw.githubusercontent.com/tlex4891-tlex/claude-global-config/main/CLAUDE.md" \
  -o "$HOME/.claude/CLAUDE.md"

echo "==> CLAUDE.md synced to ~/.claude/CLAUDE.md"
