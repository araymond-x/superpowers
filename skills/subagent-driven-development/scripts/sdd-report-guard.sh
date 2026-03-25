#!/usr/bin/env bash
# sdd-report-guard.sh — Warn when the controller directly creates report files
#
# Legitimate report creation: controller saves subagent output via Write/Edit tool
# Suspicious report creation: controller uses Bash to touch/echo empty files
#
# This is a WARNING hook (exit 0), not a blocking hook (exit 2).
# It makes forgery attempts visible without preventing legitimate Bash usage.
#
# Exit codes:
#   0 — Always (warning only, never blocks)

set -uo pipefail

INPUT=$(cat)

# Check for jq
if ! command -v jq &>/dev/null; then
  exit 0
fi

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null)

# Only check commands that interact with the reports/ directory
if ! echo "$COMMAND" | grep -qiE 'reports/task-'; then
  exit 0
fi

# Detect suspicious patterns: creating empty or trivially small report files
# touch, empty echo/cat, or redirecting minimal content
if echo "$COMMAND" | grep -qiE '(touch\s+reports/|>\s*reports/task-|echo\s+["'"'"']?\s*["'"'"']?\s*>\s*reports/|cat\s*/dev/null\s*>\s*reports/)'; then
  echo "" >&2
  echo "WARNING: Direct creation of report files detected." >&2
  echo "Command: $COMMAND" >&2
  echo "" >&2
  echo "Report files should contain actual subagent output (500+ bytes)," >&2
  echo "not empty placeholders. If you are saving real subagent output" >&2
  echo "via a script, this warning can be ignored." >&2
  echo "" >&2
fi

exit 0
