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

# Skip non-code files even when they live inside a matching directory.
# e.g. apps/api/.env matches /api/ above but is a config file, not source code.
case "${FILE_PATH##*.}" in
  env|yaml|yml|json|toml|md|txt|sh|bash|zsh|cfg|ini|conf|lock|sum|mod|log)
    exit 0 ;;
esac

# No transcript available (shouldn't happen but be safe)
if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
  exit 0
fi

# ─── Check if SDD was requested in this session ──────────────────────────

# Grep the transcript for user messages requesting SDD.
# User messages have "role":"user" in the JSONL.
#
# IMPORTANT — exclude tool_result entries: Claude Code stores tool results
# (hook error messages, pickup bundle content, Skill outputs) as user-role
# JSONL entries with "type":"tool_result". These are NOT user requests and
# must not be counted as SDD imperatives. The hook's own "invoke
# subagent-driven-development" error message would otherwise poison the session
# and block every subsequent edit (self-reinforcing loop). Filtering lines that
# contain "type":"tool_result" is safe because genuine user-typed messages
# never have this marker — they are in separate JSONL entries.
#
# NOTE: do NOT pipe the producer grep into `grep -q`. Under `set -o pipefail`,
# when `grep -q` matches early it exits and closes the pipe; the upstream grep
# then takes SIGPIPE (exit 141), pipefail propagates that as the pipeline's
# status, and the `if` evaluates FALSE — so the hook would FAIL TO BLOCK on
# every real (>64KB) transcript. We read the filtered lines into a variable via
# command substitution (no pipe, whole file consumed) and feed `grep -q` from a
# here-string (a temp buffer — no upstream process to SIGPIPE).
SDD_REQUESTED=false
if grep -q '"role":"user"' "$TRANSCRIPT_PATH" 2>/dev/null; then
  USER_LINES=$(grep '"role":"user"' "$TRANSCRIPT_PATH" 2>/dev/null | grep -v '"type":"tool_result"')
  # Require an explicit SDD imperative (not a bare mention) to avoid false
  # blocks. Both alternation groups are \b-anchored so the verb does not match
  # inside a larger word (reuse/misuse) and "sdd" does not match inside a larger
  # word (assddata). What this does NOT catch: semantic false positives where the
  # words legitimately appear ("run the sdd tests") will still block — that is
  # inherent to a regex heuristic. Use SUPERPOWERS_SDD_BYPASS to override.
  if grep -qiE "\b(invoke|use|run|follow|start|let'?s use)\b.{0,20}\b(subagent-driven-development|sdd)\b" <<< "${USER_LINES:-}" 2>/dev/null; then
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
