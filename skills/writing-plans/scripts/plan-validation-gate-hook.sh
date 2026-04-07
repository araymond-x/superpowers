#!/usr/bin/env bash
# plan-validation-gate-hook.sh — Block execution skills without plan validation
#
# PreToolUse hook on the Skill tool. Fires when subagent-driven-development
# or executing-plans is invoked. Blocks if:
#   1. Plan files exist but validate-plan.py reports FAIL on any of them
#   2. No plan-review-report.md exists (>50 bytes)
#
# Exit codes:
#   0 — Allow (no plans, or validation passed)
#   2 — Block (validation failed or review report missing)

set -o pipefail

MIN_REPORT_BYTES=50

VALIDATE_PLAN_SCRIPT="/Users/araymond/projects/claude-custom/superpowers/skills/subagent-driven-development/scripts/validate-plan.py"

INPUT=$(cat)

# Check for jq
if ! command -v jq &>/dev/null; then
  echo "WARNING: jq not found — plan-validation-gate-hook.sh cannot enforce. Install jq." >&2
  exit 0
fi

# Extract skill name from tool_input
SKILL=$(echo "$INPUT" | jq -r '.tool_input.skill // (.tool_input.args // "") | split(" ")[0]' 2>/dev/null || true)

# Only gate on execution skills
case "$SKILL" in
  *subagent-driven-development*|*executing-plans*) ;;
  *) exit 0 ;;
esac

# Get CWD from hook payload
CWD=$(echo "$INPUT" | jq -r '.cwd // ""' 2>/dev/null || true)
if [ -z "$CWD" ] || [ ! -d "$CWD" ]; then
  exit 0
fi

# ---- Find plan files --------------------------------------------------------

PLAN_FILES=()
for dir in "$CWD/docs/imp-plans" "$CWD/docs/plans"; do
  if [ -d "$dir" ]; then
    while IFS= read -r f; do
      [ -f "$f" ] && PLAN_FILES+=("$f")
    done < <(find "$dir" -maxdepth 1 -name "*.md" \
      ! -name "*-review-report*" \
      ! -name "*-validation*" \
      ! -name "*-original*" \
      2>/dev/null)
  fi
done

# No plan files found — nothing to validate, allow
if [ ${#PLAN_FILES[@]} -eq 0 ]; then
  exit 0
fi

# ---- Gate 1: Run validate-plan.py on each plan file -------------------------

ERRORS=()

if [ -f "$VALIDATE_PLAN_SCRIPT" ]; then
  for pf in "${PLAN_FILES[@]}"; do
    BASENAME=$(basename "$pf")

    # Skip non-plan files (review reports, etc.)
    if echo "$BASENAME" | grep -qiE '(review-report|validation-report|context-summary)'; then
      continue
    fi

    # Run validator
    OUTPUT=$(python3 "$VALIDATE_PLAN_SCRIPT" --plan-file "$pf" 2>/dev/null || echo "")
    if [ -z "$OUTPUT" ]; then
      continue
    fi

    STATUS=$(echo "$OUTPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || echo "")

    if [ "$STATUS" = "FAIL" ]; then
      BLOCKERS=$(echo "$OUTPUT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for b in data.get('blockers', []):
    print(f'  - {b}')
" 2>/dev/null || echo "  - (could not parse blockers)")
      ERRORS+=("BLOCKED: validate-plan.py FAIL on $BASENAME:\n$BLOCKERS\nFix these issues before proceeding to execution.")
    fi
  done
else
  # validate-plan.py not found — warn but allow
  echo "WARNING: validate-plan.py not found at $VALIDATE_PLAN_SCRIPT — structural validation skipped." >&2
fi

# ---- Gate 2: Check for plan-review-report.md --------------------------------

REVIEW_REPORT=""
for dir in "$CWD/docs/imp-plans" "$CWD/docs/plans"; do
  if [ -d "$dir" ]; then
    FOUND=$(find "$dir" -maxdepth 1 -name "*plan-review-report*" -type f 2>/dev/null | head -1)
    if [ -n "$FOUND" ]; then
      REVIEW_REPORT="$FOUND"
      break
    fi
  fi
done

if [ -z "$REVIEW_REPORT" ]; then
  ERRORS+=("BLOCKED: No plan-review-report.md found in docs/imp-plans/ or docs/plans/. The writing-plans skill requires dispatching the plan-document-reviewer and saving its output before execution. Run the Plan Review Loop (checklist steps 8-10) first.")
elif [ -f "$REVIEW_REPORT" ]; then
  REPORT_SIZE=$(wc -c < "$REVIEW_REPORT" 2>/dev/null | tr -d ' ')
  if [ "$REPORT_SIZE" -lt "$MIN_REPORT_BYTES" ] 2>/dev/null; then
    ERRORS+=("BLOCKED: plan-review-report ($REVIEW_REPORT) is only $REPORT_SIZE bytes — likely a placeholder. Save the complete reviewer output (minimum $MIN_REPORT_BYTES bytes).")
  fi
fi

# ---- Report results ----------------------------------------------------------

if [ ${#ERRORS[@]} -gt 0 ]; then
  ERROR_MSG=""
  for err in "${ERRORS[@]}"; do
    ERROR_MSG="${ERROR_MSG}${err}\n\n"
  done
  echo -e "$ERROR_MSG" >&2
  exit 2
fi

# ---- All checks passed — inject reminder and allow --------------------------

CONTEXT="PLAN VALIDATION GATE: Plan files validated and review report confirmed. Proceeding to execution. Remember: the plan is the source of truth — implement against it, not your assumptions."

ENCODED=$(python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$CONTEXT" 2>/dev/null || echo "\"$CONTEXT\"")

cat << HOOKJSON
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": $ENCODED
  }
}
HOOKJSON

exit 0
