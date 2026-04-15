#!/usr/bin/env bash
# Superpowers hook baseline — detect drift in our 7 hook scripts and
# settings.json registrations.
#
# Covers:
#   1. Byte-level integrity of 7 hook scripts in this repo (sha256)
#   2. Presence + path + matcher of each superpowers hook entry in
#      ~/.claude/settings.json (ignores unrelated third-party hooks)
#
# Usage:
#   check-hooks.sh --capture   # write baseline.txt
#   check-hooks.sh             # verify current state matches baseline.txt
#
# Exit codes:
#   0 = in sync (or capture succeeded)
#   1 = drift detected, baseline missing, or tooling unavailable

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BASELINE="$SCRIPT_DIR/baseline.txt"
SETTINGS="$HOME/.claude/settings.json"
SUPERPOWERS_PATH="/Users/araymond/projects/claude-custom/superpowers"

HOOKS=(
  "hooks/session-start"
  "skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh"
  "skills/subagent-driven-development/scripts/sdd-report-guard.sh"
  "skills/subagent-driven-development/scripts/sdd-stop-hook.sh"
  "skills/subagent-driven-development/scripts/sdd-skill-enforcement-hook.sh"
  "skills/handoff-acceptance/scripts/handoff-gate-hook.sh"
  "skills/writing-plans/scripts/plan-validation-gate-hook.sh"
)

require_tool() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "ERROR: required tool not found: $1" >&2
    exit 1
  fi
}

require_tool jq
require_tool shasum

generate() {
  echo "# Superpowers hook baseline"
  echo "# Regenerate: bash tests/ARaymond-hook-baseline/check-hooks.sh --capture"
  echo ""
  echo "## Hook script hashes (sha256)"
  for h in "${HOOKS[@]}"; do
    path="$REPO_ROOT/$h"
    if [[ ! -r "$path" ]]; then
      echo "ERROR: missing hook script: $h" >&2
      return 1
    fi
    hash=$(shasum -a 256 "$path" | awk '{print $1}')
    echo "$hash  $h"
  done
  echo ""
  echo "## Superpowers hook entries in ~/.claude/settings.json"
  echo "# Format: <Event>\\t<matcher>\\t<command>"
  if [[ ! -r "$SETTINGS" ]]; then
    echo "ERROR: settings.json not readable: $SETTINGS" >&2
    return 1
  fi
  jq -r --arg prefix "$SUPERPOWERS_PATH" '
    (.hooks // {})
    | to_entries[]
    | .key as $event
    | .value[]
    | (.matcher // "") as $matcher
    | (.hooks // [])[]
    | select((.command // "") | contains($prefix))
    | "\($event)\t\($matcher)\t\(.command)"
  ' "$SETTINGS" | sort
}

mode="${1:-verify}"
case "$mode" in
  --capture|capture)
    echo "Capturing hook baseline..."
    tmp=$(mktemp)
    trap 'rm -f "$tmp"' EXIT
    if ! generate > "$tmp"; then
      echo "Capture failed." >&2
      exit 1
    fi
    mv "$tmp" "$BASELINE"
    trap - EXIT
    echo "Wrote $BASELINE"
    echo ""
    echo "Commit with:"
    echo "  git add tests/ARaymond-hook-baseline/baseline.txt"
    echo "  git commit -m 'chore(tests): update hook baseline'"
    ;;
  --verify|verify|"")
    if [[ ! -r "$BASELINE" ]]; then
      echo "ERROR: no baseline at $BASELINE" >&2
      echo "Run with --capture first." >&2
      exit 1
    fi
    tmp=$(mktemp)
    trap 'rm -f "$tmp"' EXIT
    if ! generate > "$tmp"; then
      echo "FAIL — could not read current state" >&2
      exit 1
    fi
    if diff -u "$BASELINE" "$tmp" > /dev/null; then
      echo "PASS — 7 superpowers hooks intact (scripts unchanged, settings.json entries present)"
      exit 0
    fi
    echo "FAIL — drift detected:"
    echo ""
    diff -u "$BASELINE" "$tmp" || true
    echo ""
    echo "Interpret the diff:"
    echo "  - Changed sha256 = that hook script was edited"
    echo "  - Removed line in '## Superpowers hook entries' = hook de-registered in settings.json"
    echo "  - Added line = new superpowers hook was registered (rerun --capture if intentional)"
    exit 1
    ;;
  --help|-h)
    sed -n '2,20p' "$0"
    ;;
  *)
    echo "Usage: $0 [--capture | --verify | --help]" >&2
    exit 1
    ;;
esac
