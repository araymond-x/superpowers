#!/usr/bin/env bash
# sdd-skill-enforcement-hook.sh — Detect SDD bypass via direct implementation
#
# PreToolUse hook on Write|Edit. Checks the session transcript to detect
# when a user requested SDD but the agent is writing implementation code
# without having loaded the skill via the Skill tool.
#
# Uses the transcript_path from the hook payload to parse session history.
# This is the "Point-of-Decision Routing" pattern from the Swiss Cheese
# defense model — injecting compliance reminders at the exact moment of action.
#
# Exit codes:
#   0 — Allow the Write/Edit (skill loaded, non-SDD session, casual mention,
#       non-implementation file, or SUPERPOWERS_SDD_BYPASS set)
#   2 — Block the Write/Edit (explicit SDD imperative + implementation file +
#       skill NOT loaded; error message on stderr fed to Claude)
#
# Bypass: set SUPERPOWERS_SDD_BYPASS (mirrors SUPERPOWERS_VALIDATOR_BYPASS) to
# allow with a stderr warning instead of blocking.
#
# Performance: Early exits for non-SDD sessions (<10ms). Transcript grep
# only runs when the file path matches implementation directories.

set -o pipefail

INPUT=$(cat)

# Check for jq
if ! command -v jq &>/dev/null; then
  exit 0
fi

# Extract fields from hook payload
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""' 2>/dev/null)
TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path // ""' 2>/dev/null)

# ─── Early exits ──────────────────────────────────────────────────────────

# No file path (shouldn't happen for Write/Edit but be safe)
if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Only check implementation files — skip configs, docs, tests, reports, plans
# Match: src/, frontend/src/, app/, components/, hooks/, api/, types/, services/
if ! echo "$FILE_PATH" | grep -qiE '(^|/)src/|(^|/)app/|(^|/)frontend/|(^|/)components/|(^|/)hooks/|(^|/)api/|(^|/)types/|(^|/)services/'; then
  exit 0
fi

# No transcript available (shouldn't happen but be safe)
if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
  exit 0
fi

# ─── Check if SDD was requested in this session ──────────────────────────

# Grep the transcript for user messages requesting SDD
# User messages have "role":"user" in the JSONL
SDD_REQUESTED=false
if grep -q '"role":"user"' "$TRANSCRIPT_PATH" 2>/dev/null; then
  # Require an explicit SDD imperative (not a bare mention) to avoid false blocks.
  # Verified under ugrep 7.5 and stock /usr/bin/grep -iE (BSD): imperatives match,
  # casual mentions ("reading about subagent-driven-development", "the SDD hook") do not.
  if grep '"role":"user"' "$TRANSCRIPT_PATH" | grep -qiE "(invoke|use|run|follow|start|let'?s use)\b.{0,20}(subagent-driven-development|sdd)" 2>/dev/null; then
    SDD_REQUESTED=true
  fi
fi

# If no SDD request in session, this is a normal coding session — allow silently
if [ "$SDD_REQUESTED" = false ]; then
  exit 0
fi

# ─── SDD was requested — check if the Skill was actually loaded ──────────

SKILL_LOADED=false
if grep -qiE '"name":"Skill".*subagent-driven-development|"skill":".*subagent-driven-development"' "$TRANSCRIPT_PATH" 2>/dev/null; then
  SKILL_LOADED=true
fi

# If skill was loaded, enforcement hooks are active — allow silently
if [ "$SKILL_LOADED" = true ]; then
  exit 0
fi

# ─── SDD requested but skill NOT loaded — bypass or block ─────────────────
WARNING_MSG="BLOCKED: The user requested subagent-driven-development but you have not loaded the skill via the Skill tool. You are writing implementation code directly, bypassing the SDD review cycle, enforcement hooks, and quality gates. Load the skill now: invoke superpowers:subagent-driven-development. Direct implementation without the skill means zero spec reviews, zero code quality reviews, and no hook enforcement."

# Emergency escape hatch (mirrors SUPERPOWERS_VALIDATOR_BYPASS): allow + warn.
if [ -n "${SUPERPOWERS_SDD_BYPASS:-}" ]; then
  echo "WARNING: $WARNING_MSG (bypassed via SUPERPOWERS_SDD_BYPASS)" >&2
  exit 0
fi

echo "$WARNING_MSG" >&2
exit 2
