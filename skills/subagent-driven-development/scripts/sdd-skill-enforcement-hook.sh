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
#   0 — Always (advisory injection via additionalContext, never blocks Write/Edit)
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
  # Check if any user message mentions SDD by name
  if grep '"role":"user"' "$TRANSCRIPT_PATH" | grep -qiE '(subagent-driven-development|SDD|superpowers:subagent-driven|invoke.*sdd|use.*sdd|follow.*sdd)' 2>/dev/null; then
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

# ─── SDD requested but skill NOT loaded — inject warning ─────────────────

# The agent is writing implementation code in an SDD session without
# having loaded the skill. Inject a point-of-decision reminder.
CONTEXT_MSG="WARNING: The user requested subagent-driven-development but you have not loaded the skill via the Skill tool. You are writing implementation code directly, bypassing the SDD review cycle, enforcement hooks, and quality gates. Load the skill now: invoke superpowers:subagent-driven-development. Direct implementation without the skill means zero spec reviews, zero code quality reviews, and no hook enforcement."

ENCODED=$(python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$CONTEXT_MSG" 2>/dev/null || echo "\"$CONTEXT_MSG\"")

cat << HOOKJSON
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": $ENCODED
  }
}
HOOKJSON

exit 0
