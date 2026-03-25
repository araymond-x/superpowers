#!/usr/bin/env bash
# handoff-gate-hook.sh — Block writing-plans if handoff package not accepted
#
# PreToolUse hook on the Skill tool. Only fires when writing-plans is invoked.
# Checks for handoff package directories and their acceptance reports.
#
# Exit codes:
#   0 — Allow (no handoff, or handoff accepted)
#   2 — Block (handoff exists but not accepted)

set -uo pipefail

INPUT=$(cat)

# Extract skill name from tool_input.skill or tool_input.args
SKILL=$(echo "$INPUT" | jq -r '.tool_input.skill // (.tool_input.args // "") | split(" ")[0]' 2>/dev/null || true)

# Only gate on writing-plans
if [ "$SKILL" != "writing-plans" ]; then
  exit 0
fi

# Get CWD from hook payload
CWD=$(echo "$INPUT" | jq -r '.cwd // ""' 2>/dev/null || true)

if [ -z "$CWD" ] || [ ! -d "$CWD" ]; then
  exit 0
fi

DOCS_DIR="$CWD/docs"

if [ ! -d "$DOCS_DIR" ]; then
  exit 0
fi

# Check for handoff package directories
HANDOFF_DIR=$(find "$DOCS_DIR" -type d -name "*handoff*" 2>/dev/null | head -1)

if [ -z "$HANDOFF_DIR" ]; then
  # No handoff package exists — nothing to gate on
  exit 0
fi

# Handoff package exists — require an acceptance report
ACCEPTANCE_REPORT=$(find "$DOCS_DIR" \( -name "*acceptance*report*" -o -name "*handoff*acceptance*" \) -type f 2>/dev/null | head -1)

if [ -z "$ACCEPTANCE_REPORT" ]; then
  echo '{"decision": "block", "reason": "A handoff package exists but no acceptance report was found. Run superpowers:handoff-acceptance before writing plans."}' >&2
  exit 2
fi

# Acceptance report found — check verdict
if grep -qiE 'verdict\s*:\s*REJECTED' "$ACCEPTANCE_REPORT" 2>/dev/null; then
  REASON=$(grep -iE 'verdict\s*:\s*REJECTED' "$ACCEPTANCE_REPORT" | head -1 | sed 's/^[[:space:]]*//')
  echo "{\"decision\": \"block\", \"reason\": \"Handoff acceptance report verdict is REJECTED. Resolve handoff issues before writing plans. ($REASON)\"}" >&2
  exit 2
fi

# Check for ACCEPTED verdict (covers ACCEPTED and ACCEPTED_WITH_REMEDIATION)
if grep -qiE 'verdict\s*:\s*ACCEPTED' "$ACCEPTANCE_REPORT" 2>/dev/null; then
  exit 0
fi

# Report exists but no clear verdict found — treat as not accepted
echo '{"decision": "block", "reason": "Handoff acceptance report found but no ACCEPTED verdict detected. Ensure the report contains a verdict line before writing plans."}' >&2
exit 2
