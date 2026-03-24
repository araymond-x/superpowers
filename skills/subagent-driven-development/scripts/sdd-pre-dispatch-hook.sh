#!/usr/bin/env bash
# sdd-pre-dispatch-hook.sh — Process-level enforcement for SDD task dispatches
#
# Runs as a PreToolUse hook on the Agent tool via SDD skill frontmatter.
# Blocks implementer task dispatches that haven't completed the review cycle.
#
# Exit codes:
#   0 — Allow the dispatch
#   2 — Block the dispatch (error message on stderr fed to Claude)
#
# Input: JSON on stdin with tool_input.description, tool_input.prompt, etc.
# Output: JSON on stdout (optional — for additionalContext injection)

set -uo pipefail

# Read stdin
INPUT=$(cat)

# Check for jq — required for JSON parsing
if ! command -v jq &>/dev/null; then
  echo "WARNING: jq not found — sdd-pre-dispatch-hook.sh cannot enforce SDD dispatch rules. Install jq to enable enforcement." >&2
  exit 0
fi

# Extract the description field from tool_input
DESCRIPTION=$(echo "$INPUT" | jq -r '.tool_input.description // ""' 2>/dev/null)

# Extract the prompt field for additional pattern matching (first 500 chars)
PROMPT=$(echo "$INPUT" | jq -r '.tool_input.prompt // ""' 2>/dev/null | head -c 500)

# Get current working directory from hook input
CWD=$(echo "$INPUT" | jq -r '.cwd // ""' 2>/dev/null)
if [ -z "$CWD" ] || [ ! -d "$CWD" ]; then
  # Can't determine CWD — allow and let the controller handle it
  exit 0
fi

cd "$CWD" || exit 0

# ─── Determine dispatch type ──────────────────────────────────────────────

# Is this an implementer task dispatch?
TASK_NUMBER=""
IS_IMPLEMENTER=false
if echo "$DESCRIPTION" | grep -qiE '(implement|dispatch).*task\s*[0-9]'; then
  TASK_NUMBER=$(echo "$DESCRIPTION" | grep -oiE 'task\s*[0-9]+' | grep -oE '[0-9]+' | head -1)
  IS_IMPLEMENTER=true
elif echo "$PROMPT" | grep -qiE 'you are implementing task\s*[0-9]'; then
  TASK_NUMBER=$(echo "$PROMPT" | grep -oiE 'task\s*[0-9]+' | grep -oE '[0-9]+' | head -1)
  IS_IMPLEMENTER=true
fi

# Is this a reviewer dispatch? (always allowed)
IS_REVIEWER=false
if echo "$DESCRIPTION" | grep -qiE '(review|spec.compliance|code.quality|spec.review|quality.review|trace.audit)'; then
  IS_REVIEWER=true
fi

# If this is a reviewer dispatch, always allow
if [ "$IS_REVIEWER" = true ]; then
  exit 0
fi

# If this doesn't look like an SDD dispatch at all (e.g., Explore agent, general research), allow
if [ "$IS_IMPLEMENTER" = false ]; then
  exit 0
fi

# ─── Enforcement checks (implementer dispatches only) ─────────────────────

ERRORS=()

# Check 1: Branch safety
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
  ERRORS+=("BLOCKED: You are on the '$CURRENT_BRANCH' branch. Create a feature branch or worktree before dispatching implementation tasks.")
fi

# Check 2: DEVIATIONS.md must exist
if [ ! -f "DEVIATIONS.md" ]; then
  ERRORS+=("BLOCKED: DEVIATIONS.md does not exist. Create it with the SDD template before dispatching tasks. The SDD skill's Plan Ingestion step 5 requires this.")
fi

# Check 3: reports/ directory must exist
if [ ! -d "reports" ]; then
  ERRORS+=("BLOCKED: reports/ directory does not exist. Create it before dispatching tasks. Reports from each task are saved here for persistence and audit.")
fi

# Check 4: If Task N > 0, verify previous task was fully reviewed
if [ -n "$TASK_NUMBER" ] && [ "$TASK_NUMBER" -gt 0 ] 2>/dev/null; then
  PREV=$((TASK_NUMBER - 1))

  # Previous task implementer report
  if ! ls reports/task-${PREV}-implementer-report* 1>/dev/null 2>&1; then
    ERRORS+=("BLOCKED: No implementer report found for Task $PREV (reports/task-${PREV}-implementer-report*). The previous task must have its report saved before dispatching the next task.")
  fi

  # Previous task spec review report
  if ! ls reports/task-${PREV}-spec-review* 1>/dev/null 2>&1; then
    ERRORS+=("BLOCKED: No spec compliance review report found for Task $PREV (reports/task-${PREV}-spec-review*). Spec review must be dispatched and its report saved before proceeding to the next task.")
  fi

  # Previous task quality review report
  if ! ls reports/task-${PREV}-quality-review* 1>/dev/null 2>&1; then
    ERRORS+=("BLOCKED: No code quality review report found for Task $PREV (reports/task-${PREV}-quality-review*). Quality review must be dispatched and its report saved before proceeding. If minimum review tier was declared, save a reports/task-${PREV}-quality-review-minimum-tier.md noting the tier declaration.")
  fi
fi

# Check 5: If Task N > 0 and plan has Source Contracts, verify Task 0 completed
if [ -n "$TASK_NUMBER" ] && [ "$TASK_NUMBER" -gt 0 ] 2>/dev/null; then
  # Look for any plan file that has Source Contracts (not "None")
  HAS_SOURCE_CONTRACTS=false
  for plan_file in docs/imp-plans/*.md docs/plans/*.md; do
    if [ -f "$plan_file" ]; then
      if grep -q "Source Contracts" "$plan_file" && ! grep -qiE "Source Contracts.*:.*None" "$plan_file"; then
        HAS_SOURCE_CONTRACTS=true
        break
      fi
    fi
  done

  if [ "$HAS_SOURCE_CONTRACTS" = true ]; then
    if ! ls reports/task-0-implementer-report* 1>/dev/null 2>&1; then
      ERRORS+=("BLOCKED: Plan has Source Contracts but no Task 0 report found (reports/task-0-implementer-report*). Task 0 (Contract Verification) must complete before any other task is dispatched.")
    fi
  fi
fi

# ─── Report results ───────────────────────────────────────────────────────

if [ ${#ERRORS[@]} -gt 0 ]; then
  # Build error message
  ERROR_MSG=""
  for err in "${ERRORS[@]}"; do
    ERROR_MSG="${ERROR_MSG}${err}\n"
  done

  echo -e "$ERROR_MSG" >&2
  exit 2
fi

# All checks passed — allow the dispatch
exit 0
