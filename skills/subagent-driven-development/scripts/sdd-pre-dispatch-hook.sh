#!/usr/bin/env bash
# sdd-pre-dispatch-hook.sh — Process-level enforcement for SDD task dispatches
#
# Runs as a global PreToolUse hook on the Agent tool (settings.json).
# Blocks implementer task dispatches that haven't completed the review cycle.
#
# Exit codes:
#   0 — Allow the dispatch (with optional additionalContext injection)
#   2 — Block the dispatch (error message on stderr fed to Claude)
#
# Input: JSON on stdin with tool_input.description, tool_input.prompt, etc.
# Output: JSON on stdout (additionalContext reminder on allowed dispatches)

set -uo pipefail

# Minimum file size (bytes) for report files to be considered valid.
# Prevents forgery via `touch` or `echo "PASS" > file` (0-49 bytes).
# Real review reports are 500+ bytes.
MIN_REPORT_BYTES=50

# Context load threshold (bytes) above which a compression warning is injected.
# 400KB of accumulated files is roughly 100K tokens.
CONTEXT_LOAD_WARNING_BYTES=$((400 * 1024))

# Absolute path to validate-report.py (must use absolute path — bare scripts/ resolves from CWD)
VALIDATE_REPORT_SCRIPT="/Users/araymond/projects/claude-custom/superpowers/skills/subagent-driven-development/scripts/validate-report.py"

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

# If this is a reviewer dispatch, log it and allow
if [ "$IS_REVIEWER" = true ]; then
  # ─── Dispatch provenance logging ──────────────────────────────────────
  # Log reviewer dispatches to reports/.dispatch-log so the next implementer
  # dispatch can verify reviews were actually dispatched (not self-written).
  DISPATCH_LOG="reports/.dispatch-log"
  if [ -d "reports" ]; then
    # Extract task number from description (e.g., "Review task 3 spec compliance")
    REVIEW_TASK=$(echo "$DESCRIPTION" | grep -oiE 'task\s*[0-9]+' | grep -oE '[0-9]+' | head -1)
    # Determine review type from description
    REVIEW_TYPE="unknown"
    if echo "$DESCRIPTION" | grep -qiE '(spec.compliance|spec.review)'; then
      REVIEW_TYPE="spec-review"
    elif echo "$DESCRIPTION" | grep -qiE '(code.quality|quality.review|superpowers-code-reviewer)'; then
      REVIEW_TYPE="quality-review"
    elif echo "$DESCRIPTION" | grep -qiE 'trace.audit'; then
      REVIEW_TYPE="trace-audit"
    fi

    if [ -n "$REVIEW_TASK" ]; then
      echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) DISPATCH reviewer task=$REVIEW_TASK type=$REVIEW_TYPE" >> "$DISPATCH_LOG"
    fi
  fi
  exit 0
fi

# If this doesn't look like an SDD dispatch at all (e.g., Explore agent, general research), allow
if [ "$IS_IMPLEMENTER" = false ]; then
  exit 0
fi

# ─── Helper: format task number for report file glob ─────────────────────
# Uses zero-padded 3-digit format exclusively (task-007-*). Non-padded names
# (task-7-*) are not matched — they indicate stale reports from a prior
# session that used an older naming convention.

task_report_glob() {
  local task_num="$1"
  local report_type="$2"
  local padded
  padded=$(printf "%03d" "$task_num" 2>/dev/null || echo "$task_num")
  echo "reports/task-${padded}-${report_type}*"
}

# ─── Helper: check report file exists AND has meaningful content ──────────

check_report_file() {
  local pattern="$1"
  local label="$2"

  # Find matching files
  local matches
  matches=$(ls $pattern 2>/dev/null)

  if [ -z "$matches" ]; then
    echo "MISSING"
    return
  fi

  # Check the most recent matching file has meaningful content
  local latest
  latest=$(echo "$matches" | sort | tail -1)
  local size
  size=$(wc -c < "$latest" 2>/dev/null | tr -d ' ')

  if [ "$size" -lt "$MIN_REPORT_BYTES" ] 2>/dev/null; then
    echo "TOO_SMALL:${size}:${latest}"
    return
  fi

  echo "OK"
}

# ─── Enforcement checks (implementer dispatches only) ─────────────────────

ERRORS=()

# Check 1: Branch safety
# If SDD artifacts exist (reports/ + DEVIATIONS.md) AND on main → BLOCK
# Unless .allow-main exists (explicit user opt-in for main branch SDD)
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
  SDD_ARTIFACTS_EXIST=false
  if [ -d "reports" ] && [ -f "DEVIATIONS.md" ]; then
    SDD_ARTIFACTS_EXIST=true
  fi

  if [ "$SDD_ARTIFACTS_EXIST" = true ] && [ ! -f ".allow-main" ]; then
    ERRORS+=("BLOCKED: You are on the '$CURRENT_BRANCH' branch with SDD artifacts present (reports/ + DEVIATIONS.md). This usually means you drifted out of your worktree. Either: (1) cd to your worktree directory, or (2) create a .allow-main file in the project root if you intentionally want to run SDD on $CURRENT_BRANCH.")
  else
    echo "WARNING: You are on the '$CURRENT_BRANCH' branch. Consider using a feature branch or worktree for implementation work." >&2
  fi
fi

# Check 1b: Worktree location convention
# Standard: worktrees should be at <project>/.worktrees/<feature>/
# Warn if CWD is a worktree but NOT under .worktrees/ (sibling worktree)
if [ "$CURRENT_BRANCH" != "main" ] && [ "$CURRENT_BRANCH" != "master" ]; then
  # We're on a feature branch — check if we're in the standard location
  if ! echo "$CWD" | grep -q '\.worktrees/'; then
    # Not under .worktrees/ — could be a sibling worktree or unusual location
    GIT_TOPLEVEL=$(git rev-parse --show-toplevel 2>/dev/null || echo "")
    if [ -n "$GIT_TOPLEVEL" ]; then
      # Check if this IS a worktree (not the main repo)
      GIT_COMMON=$(git rev-parse --git-common-dir 2>/dev/null || echo "")
      GIT_DIR=$(git rev-parse --git-dir 2>/dev/null || echo "")
      if [ "$GIT_COMMON" != "$GIT_DIR" ]; then
        # This is a worktree, but not under .worktrees/
        echo "WARNING: This worktree is not in the standard .worktrees/ directory. Standard location: <project-root>/.worktrees/<feature-name>/. Sibling worktrees clutter ~/projects/ and create inconsistency." >&2
      fi
    fi
  fi
fi

# Check 2: Pre-execution audit report must exist with substantive content
AUDIT_RESULT=$(check_report_file "reports/pre-execution-audit*" "pre-execution audit")
case "$AUDIT_RESULT" in
  MISSING)
    ERRORS+=("BLOCKED: No pre-execution audit report found (reports/pre-execution-audit*). Complete the Pre-Execution Audit: (1) Write self-assessment to reports/pre-execution-audit-self-assessment.md, (2) Dispatch auditor via pre-execution-audit-prompt.md, (3) Resolve all remediation orders, (4) Save audit report to reports/pre-execution-audit.md.")
    ;;
  TOO_SMALL*)
    FILE_SIZE=$(echo "$AUDIT_RESULT" | cut -d: -f2)
    ERRORS+=("BLOCKED: Pre-execution audit report exists but is only $FILE_SIZE bytes — likely a placeholder. The audit report must contain the auditor's verdict and any remediation order resolutions (minimum $MIN_REPORT_BYTES bytes).")
    ;;
esac

# Check 3: DEVIATIONS.md must exist
if [ ! -f "DEVIATIONS.md" ]; then
  ERRORS+=("BLOCKED: DEVIATIONS.md does not exist. Create it with the SDD template before dispatching tasks. The SDD skill's Plan Ingestion step 5 requires this.")
fi

# Check 3: reports/ directory must exist
if [ ! -d "reports" ]; then
  ERRORS+=("BLOCKED: reports/ directory does not exist. Create it before dispatching tasks. Reports from each task are saved here for persistence and audit.")
fi

# Check 3b: Report naming convention
# Catches non-standard naming (m2-task-N, m3-feature-N, module1-task-N, etc.)
# BEFORE the per-task checks, so the error message explains the root cause.
if [ -d "reports" ]; then
  NON_STANDARD_FILES=()
  for rf in reports/*.md; do
    if [ -f "$rf" ]; then
      BASENAME=$(basename "$rf")
      # Allow: task-NNN-*, pre-execution-audit*, context-summary*
      if ! echo "$BASENAME" | grep -qE '^(task-[0-9]+-|pre-execution-audit|context-summary)'; then
        NON_STANDARD_FILES+=("$BASENAME")
      fi
    fi
  done

  if [ ${#NON_STANDARD_FILES[@]} -gt 0 ]; then
    FILE_LIST=""
    for nsf in "${NON_STANDARD_FILES[@]}"; do
      FILE_LIST="${FILE_LIST}  ${nsf}\n"
    done
    ERRORS+=("BLOCKED: ${#NON_STANDARD_FILES[@]} report file(s) use non-standard naming:\n${FILE_LIST}All reports must use task-NNN-{type}.md format (3-digit zero-padded sequential numbering across all modules). Rename these files before proceeding. See CLAUDE.md Report Naming Convention for details.")
  fi
fi

# Check 4: If Task N > 0, verify previous task was fully reviewed with real content
if [ -n "$TASK_NUMBER" ] && [ "$TASK_NUMBER" -gt 0 ] 2>/dev/null; then
  PREV=$((TASK_NUMBER - 1))

  PREV_PADDED=$(printf "%03d" "$PREV" 2>/dev/null || echo "$PREV")

  # Previous task implementer report
  IMPL_GLOB=$(task_report_glob "$PREV" "implementer-report")
  RESULT=$(check_report_file "$IMPL_GLOB" "implementer report")
  case "$RESULT" in
    MISSING)
      ERRORS+=("BLOCKED: No implementer report found for Task $PREV (expected: reports/task-${PREV_PADDED}-implementer-report.md). Save the implementer's report using the task-NNN naming convention.")
      ;;
    TOO_SMALL*)
      FILE_SIZE=$(echo "$RESULT" | cut -d: -f2)
      FILE_NAME=$(echo "$RESULT" | cut -d: -f3-)
      ERRORS+=("BLOCKED: Implementer report for Task $PREV ($FILE_NAME) is only $FILE_SIZE bytes — likely an empty placeholder. Save the full subagent response (minimum $MIN_REPORT_BYTES bytes).")
      ;;
  esac

  # Check 4b: Previous task implementer report is structurally COMPLETE
  # Size check (above) catches empty/trivial files; this catches files that pass
  # the size check but are missing required sections (Swiss Cheese layer 2).
  if [ "$RESULT" = "OK" ] && [ -f "$VALIDATE_REPORT_SCRIPT" ]; then
    IMPL_LATEST=$(ls $IMPL_GLOB 2>/dev/null | sort | tail -1)
    if [ -n "$IMPL_LATEST" ]; then
      VALIDATE_OUTPUT=$(python3 "$VALIDATE_REPORT_SCRIPT" --report-file "$IMPL_LATEST" 2>/dev/null || echo "")
      if [ -n "$VALIDATE_OUTPUT" ]; then
        VALIDATE_STATUS=$(echo "$VALIDATE_OUTPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status',''))" 2>/dev/null)
        if [ "$VALIDATE_STATUS" = "INCOMPLETE" ]; then
          MISSING_SECTIONS=$(echo "$VALIDATE_OUTPUT" | python3 -c "import json,sys; print(', '.join(json.load(sys.stdin).get('sections_missing',[])))" 2>/dev/null)
          ERRORS+=("BLOCKED: Implementer report for Task $PREV ($IMPL_LATEST) is structurally incomplete — missing sections: $MISSING_SECTIONS. Re-dispatch the implementer to complete all 9 required sections before proceeding.")
        fi
      fi
    fi
  fi

  # Previous task spec review report
  SPEC_GLOB=$(task_report_glob "$PREV" "spec-review")
  RESULT=$(check_report_file "$SPEC_GLOB" "spec review")
  case "$RESULT" in
    MISSING)
      ERRORS+=("BLOCKED: No spec review found for Task $PREV (expected: reports/task-${PREV_PADDED}-spec-review.md). Dispatch spec compliance review and save the report.")
      ;;
    TOO_SMALL*)
      FILE_SIZE=$(echo "$RESULT" | cut -d: -f2)
      FILE_NAME=$(echo "$RESULT" | cut -d: -f3-)
      ERRORS+=("BLOCKED: Spec review for Task $PREV ($FILE_NAME) is only $FILE_SIZE bytes — save the actual reviewer output.")
      ;;
  esac

  # Previous task quality review report
  QUAL_GLOB=$(task_report_glob "$PREV" "quality-review")
  RESULT=$(check_report_file "$QUAL_GLOB" "quality review")
  case "$RESULT" in
    MISSING)
      ERRORS+=("BLOCKED: No quality review found for Task $PREV (expected: reports/task-${PREV_PADDED}-quality-review.md). Dispatch code quality review, or save reports/task-${PREV_PADDED}-quality-review-minimum-tier.md if minimum tier declared.")
      ;;
    TOO_SMALL*)
      FILE_SIZE=$(echo "$RESULT" | cut -d: -f2)
      FILE_NAME=$(echo "$RESULT" | cut -d: -f3-)
      ERRORS+=("BLOCKED: Quality review for Task $PREV ($FILE_NAME) is only $FILE_SIZE bytes — save the actual reviewer output.")
      ;;
  esac

  # Check 4c: Dispatch provenance — verify reviewers were actually dispatched
  # Report files can be self-written by the controller. The dispatch log is written
  # by THIS HOOK when it processes Agent calls with reviewer descriptions.
  # The controller cannot forge dispatch log entries without going through the Agent tool.
  DISPATCH_LOG="reports/.dispatch-log"
  if [ -f "$DISPATCH_LOG" ]; then
    # Check for spec-review dispatch entry for previous task
    SPEC_DISPATCHED=false
    if grep -q "task=$PREV .*type=spec-review" "$DISPATCH_LOG" 2>/dev/null; then
      SPEC_DISPATCHED=true
    fi

    # Check for quality-review dispatch entry for previous task
    # quality-review-minimum-tier is acceptable if the report file matches that pattern
    QUAL_DISPATCHED=false
    QUAL_GLOB_MIN=$(task_report_glob "$PREV" "quality-review-minimum-tier")
    HAS_MINIMUM_TIER=$(ls $QUAL_GLOB_MIN 2>/dev/null | head -1)
    if grep -q "task=$PREV .*type=quality-review" "$DISPATCH_LOG" 2>/dev/null; then
      QUAL_DISPATCHED=true
    elif [ -n "$HAS_MINIMUM_TIER" ]; then
      # Minimum tier allows controller-written quality review (no dispatch needed)
      QUAL_DISPATCHED=true
    fi

    if [ "$SPEC_DISPATCHED" = false ]; then
      ERRORS+=("BLOCKED: No spec-review dispatch recorded for Task $PREV. The dispatch log (reports/.dispatch-log) has no entry for a spec reviewer being dispatched via the Agent tool. Spec reviews must be dispatched subagents, not self-written by the controller. Dispatch the spec reviewer now.")
    fi

    if [ "$QUAL_DISPATCHED" = false ]; then
      ERRORS+=("BLOCKED: No quality-review dispatch recorded for Task $PREV. Dispatch the code quality reviewer via the Agent tool. Controller-written quality reviews are only allowed for minimum-tier tasks (and the file must be named task-NNN-quality-review-minimum-tier.md).")
    fi
  else
    # No dispatch log exists at all — log was deleted or no reviewers were ever dispatched
    ERRORS+=("BLOCKED: No dispatch log found (reports/.dispatch-log). This file is created automatically by the SDD hook when reviewers are dispatched. Its absence means no reviewers were dispatched via the Agent tool for any task. Start by dispatching the spec reviewer for Task $PREV.")
  fi
fi

# Check 5: If Task N > 0 and plan has Source Contracts, verify Task 0 completed
if [ -n "$TASK_NUMBER" ] && [ "$TASK_NUMBER" -gt 0 ] 2>/dev/null; then
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
    T0_GLOB=$(task_report_glob "0" "implementer-report")
    RESULT=$(check_report_file "$T0_GLOB" "Task 0 report")
    case "$RESULT" in
      MISSING)
        ERRORS+=("BLOCKED: Plan has Source Contracts but no Task 0 report found (expected: reports/task-000-implementer-report.md). Task 0 (Contract Verification) must complete first.")
        ;;
      TOO_SMALL*)
        FILE_SIZE=$(echo "$RESULT" | cut -d: -f2)
        ERRORS+=("BLOCKED: Task 0 report exists but is only $FILE_SIZE bytes — Task 0 must produce real contract verification output.")
        ;;
    esac
  fi
fi

# ─── Check 5b: Pending deviations in DEVIATIONS.md ────────────────────────
# All deviations must be dispositioned (Accepted/Rejected/Deferred) before
# dispatching the next task. Pending entries indicate unresolved decisions.

if [ -f "DEVIATIONS.md" ]; then
  PENDING_COUNT=$(grep -ciE '\|\s*Pending\s*\|' DEVIATIONS.md 2>/dev/null || echo "0")
  if [ "$PENDING_COUNT" -gt 0 ] 2>/dev/null; then
    ERRORS+=("BLOCKED: DEVIATIONS.md has $PENDING_COUNT pending deviation(s). Disposition all entries (Accepted/Rejected/Deferred) before dispatching the next task.")
  fi
fi

# ─── Check 6: Token budget estimation ─────────────────────────────────────

ESTIMATE_SCRIPT="/Users/araymond/projects/claude-custom/superpowers/skills/subagent-driven-development/scripts/estimate-task-tokens.py"
TOKEN_WARNING=""

if [ -n "$TASK_NUMBER" ] && [ -f "$ESTIMATE_SCRIPT" ]; then
  # Find a plan file to extract the task from
  PLAN_FILE=""
  SEARCHED_DIRS=""
  for pf in docs/imp-plans/*.md docs/plans/*.md; do
    if [ -f "$pf" ]; then
      SEARCHED_DIRS="${SEARCHED_DIRS} $(basename "$pf")"
      if grep -qiE "^###\s+Task\s+${TASK_NUMBER}\b" "$pf"; then
        PLAN_FILE="$pf"
        break
      fi
    fi
  done

  if [ -n "$PLAN_FILE" ]; then
    ESTIMATE_OUTPUT=$(python3 "$ESTIMATE_SCRIPT" --plan-file "$PLAN_FILE" --task "$TASK_NUMBER" 2>/dev/null || echo "")
    if [ -n "$ESTIMATE_OUTPUT" ]; then
      ESTIMATE_STATUS=$(echo "$ESTIMATE_OUTPUT" | jq -r '.status // "OK"' 2>/dev/null)
      ESTIMATE_TOTAL=$(echo "$ESTIMATE_OUTPUT" | jq -r '.total_estimated // "?"' 2>/dev/null)
      ESTIMATE_WARNING=$(echo "$ESTIMATE_OUTPUT" | jq -r '.warning // empty' 2>/dev/null)

      if [ "$ESTIMATE_STATUS" = "TOO_LARGE" ]; then
        ERRORS+=("BLOCKED: Task $TASK_NUMBER estimated at $ESTIMATE_TOTAL tokens — exceeds 50% of context budget. $ESTIMATE_WARNING Split this task into smaller subtasks before dispatching.")
      elif [ "$ESTIMATE_STATUS" = "WARNING" ]; then
        TOKEN_WARNING="TOKEN WARNING: Task $TASK_NUMBER estimated at $ESTIMATE_TOTAL tokens (large). $ESTIMATE_WARNING Instruct the subagent to focus narrowly and ask questions rather than reading broadly."
      fi
    else
      TOKEN_WARNING="TOKEN ESTIMATION FAILED: estimate-task-tokens.py produced no output for Task $TASK_NUMBER in $PLAN_FILE. Check script manually."
    fi
  else
    # Diagnostic: couldn't find the task in any plan file
    if [ -z "$SEARCHED_DIRS" ]; then
      TOKEN_WARNING="TOKEN ESTIMATION SKIPPED: No plan files found in docs/imp-plans/ or docs/plans/. Token budget check could not run for Task $TASK_NUMBER."
    else
      TOKEN_WARNING="TOKEN ESTIMATION SKIPPED: Task $TASK_NUMBER header not found in plan files (searched:${SEARCHED_DIRS}). Token budget check could not run. Verify task numbering matches plan headers."
    fi
  fi
fi

# ─── Check 6b: Context summary at midpoint ────────────────────────────────
# The SDD skill requires context-summary.py to be run at the halfway point
# "regardless of context load." If we're past the midpoint and the summary
# doesn't exist, inject a WARNING.

CONTEXT_SUMMARY_WARNING=""
if [ -n "$TASK_NUMBER" ] && [ "$TASK_NUMBER" -gt 1 ]; then
  # Count total tasks across all plan files
  TOTAL_TASKS=0
  for pf in docs/imp-plans/*.md docs/plans/*.md; do
    if [ -f "$pf" ]; then
      TASK_COUNT=$(grep -ciE "^###\s+Task\s+[0-9]" "$pf" 2>/dev/null || echo "0")
      TOTAL_TASKS=$((TOTAL_TASKS + TASK_COUNT))
    fi
  done

  if [ "$TOTAL_TASKS" -gt 0 ]; then
    MIDPOINT=$(( (TOTAL_TASKS + 1) / 2 ))
    if [ "$TASK_NUMBER" -ge "$MIDPOINT" ]; then
      if [ ! -f "reports/context-summary.md" ]; then
        CONTEXT_SUMMARY_WARNING="CONTEXT SUMMARY REQUIRED: You are at Task $TASK_NUMBER of $TOTAL_TASKS (past midpoint $MIDPOINT). Run context-summary.py to compress completed task reports before proceeding: python3 ~/.claude/skills/superpowers/subagent-driven-development/scripts/context-summary.py --reports-dir reports/ --deviations-file DEVIATIONS.md --output reports/context-summary.md"
      fi
    fi
  fi
fi

# ─── Report results ───────────────────────────────────────────────────────

if [ ${#ERRORS[@]} -gt 0 ]; then
  ERROR_MSG=""
  for err in "${ERRORS[@]}"; do
    ERROR_MSG="${ERROR_MSG}${err}\n"
  done

  echo -e "$ERROR_MSG" >&2
  exit 2
fi

# ─── Check 7: Context load estimate (non-blocking) ───────────────────────
# Estimate accumulated file sizes across plan, deviations, and reports.
# If above threshold, inject a compression warning into additionalContext.

CONTEXT_LOAD_WARNING=""
if [ -d "reports" ]; then
  TOTAL_BYTES=0

  # Sum plan files
  for pf in docs/imp-plans/*.md docs/plans/*.md; do
    if [ -f "$pf" ]; then
      PF_SIZE=$(wc -c < "$pf" 2>/dev/null | tr -d ' ')
      TOTAL_BYTES=$((TOTAL_BYTES + PF_SIZE))
    fi
  done

  # Sum DEVIATIONS.md
  if [ -f "DEVIATIONS.md" ]; then
    DEV_SIZE=$(wc -c < "DEVIATIONS.md" 2>/dev/null | tr -d ' ')
    TOTAL_BYTES=$((TOTAL_BYTES + DEV_SIZE))
  fi

  # Sum all report files
  for rf in reports/*.md; do
    if [ -f "$rf" ]; then
      RF_SIZE=$(wc -c < "$rf" 2>/dev/null | tr -d ' ')
      TOTAL_BYTES=$((TOTAL_BYTES + RF_SIZE))
    fi
  done

  if [ "$TOTAL_BYTES" -ge "$CONTEXT_LOAD_WARNING_BYTES" ] 2>/dev/null; then
    TOTAL_KB=$((TOTAL_BYTES / 1024))
    APPROX_TOKENS=$((TOTAL_BYTES / 4))
    CONTEXT_LOAD_WARNING="CONTEXT LOAD WARNING: Accumulated SDD files total ~${TOTAL_KB}KB (~${APPROX_TOKENS} tokens). Consider running context-summary.py to compress completed task reports before response quality degrades."
  fi
fi

# ─── All checks passed — inject reminder context and allow ────────────────

# Build additionalContext with SDD reminder + optional token warning
CONTEXT="SDD REMINDER: After this subagent completes, you must: (1) Save the implementer report to reports/task-N-implementer-report.md, (2) Dispatch spec compliance review and save to reports/task-N-spec-review.md, (3) Dispatch code quality review and save to reports/task-N-quality-review.md, (4) Log any DONE_WITH_CONCERNS to DEVIATIONS.md, (5) Update plan checkboxes. The next task dispatch will be BLOCKED if these reports are missing or empty."

if [ -n "$TOKEN_WARNING" ]; then
  CONTEXT="$CONTEXT | $TOKEN_WARNING"
fi

if [ -n "$CONTEXT_SUMMARY_WARNING" ]; then
  CONTEXT="$CONTEXT | $CONTEXT_SUMMARY_WARNING"
fi

if [ -n "$CONTEXT_LOAD_WARNING" ]; then
  CONTEXT="$CONTEXT | $CONTEXT_LOAD_WARNING"
fi

# Use python to safely JSON-encode the context string
ENCODED_CONTEXT=$(python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$CONTEXT" 2>/dev/null || echo "\"$CONTEXT\"")

cat << HOOKJSON
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": $ENCODED_CONTEXT
  }
}
HOOKJSON

exit 0
