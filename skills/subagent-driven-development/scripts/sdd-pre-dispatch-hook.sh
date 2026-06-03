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

# Item 5 (2026-05-29): Legacy non-manifest enforcement path removed. The hook
# now requires a .sdd-session.json manifest (see the guard near line 126); all
# checks read paths and enforcement flags from it exclusively.

# Minimum file size (bytes) for report files to be considered valid.
# Prevents forgery via `touch` or `echo "PASS" > file` (0-49 bytes).
# Real review reports are 500+ bytes.
MIN_REPORT_BYTES=50

# Context load threshold (bytes) above which a compression warning is injected.
# 400KB of accumulated files is roughly 100K tokens.
CONTEXT_LOAD_WARNING_BYTES=$((400 * 1024))

# Resolve the superpowers repo root. Self-resolves from script location by default;
# set SUPERPOWERS_ROOT env var to override (e.g., for team distribution).
SUPERPOWERS_ROOT="${SUPERPOWERS_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"

# Python with PyYAML/Pydantic — use the superpowers venv, fall back to system python3
if [ -f "$SUPERPOWERS_ROOT/.venv/bin/python3" ]; then
  PYTHON="$SUPERPOWERS_ROOT/.venv/bin/python3"
else
  PYTHON="python3"
fi

# Script paths derived from repo root (no hardcoded absolute paths)
VALIDATE_REPORT_SCRIPT="$SUPERPOWERS_ROOT/skills/subagent-driven-development/scripts/validate-report.py"

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

# ─── Manifest-based path resolution (CWD-stable) ────────────────────────
# Resolve all paths git-root-relative from the manifest. No manifest → not a
# manifest-mode SDD session (handled by the guard clause below).
MANIFEST=""
MANIFEST_MODE=false
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "")
FEAT=""
DEVIATIONS_FILE=""
REPORTS_DIR=""
DISPATCH_LOG=""
MANIFEST_TIER=""
MANIFEST_TASK_START=""
MANIFEST_TASK_END=""
MANIFEST_PLAN_FILE=""
MANIFEST_MODULE_FILE=""
NEED_AUDIT=""
NEED_PROV=""
NEED_CHECKPOINT=""
NEED_PARTNER=""
CONTEXT_SUMMARY_AT=""
PR_DISPATCH=""
PR_SPEC=""
PR_QUALITY=""
PR_PARTNER=""
PR_DEVLOG=""
PR_CHECKPOINT=""
PROCESS_CONTRACT=""
SENTINEL_LINE=""
SESSION_ID=""
SENTINEL_HASH=""
SENTINEL=""
TEMP_LOG=""

if [ -n "$GIT_ROOT" ] && [ -f "$GIT_ROOT/.active-feature" ]; then
  FEAT_FROM_ROOT=$(cat "$GIT_ROOT/.active-feature" 2>/dev/null | tr -d '\n' | sed 's|/$||')
  if [ -n "$FEAT_FROM_ROOT" ] && [ -f "$GIT_ROOT/$FEAT_FROM_ROOT/.sdd-session.json" ]; then
    MANIFEST="$GIT_ROOT/$FEAT_FROM_ROOT/.sdd-session.json"
    MANIFEST_MODE=true
    # Read all paths from manifest — CWD-stable
    FEAT="$FEAT_FROM_ROOT"
    DEVIATIONS_FILE="$GIT_ROOT/$(jq -r '.paths.deviations_file' "$MANIFEST")"
    REPORTS_DIR="$GIT_ROOT/$(jq -r '.paths.reports_dir' "$MANIFEST")"
    DISPATCH_LOG="$GIT_ROOT/$(jq -r '.paths.dispatch_log' "$MANIFEST")"
    # Read enforcement and tier
    MANIFEST_TIER=$(jq -r '.tier' "$MANIFEST")
    MANIFEST_TASK_START=$(jq -r '.task_range[0]' "$MANIFEST")
    MANIFEST_TASK_END=$(jq -r '.task_range[1]' "$MANIFEST")
    MANIFEST_PLAN_FILE="$GIT_ROOT/$(jq -r '.plan_file' "$MANIFEST")"
    MANIFEST_MODULE_FILE=$(jq -r '.active_module_file // empty' "$MANIFEST")
    if [ -n "$MANIFEST_MODULE_FILE" ]; then
      MANIFEST_MODULE_FILE="$GIT_ROOT/$FEAT/$MANIFEST_MODULE_FILE"
    fi
  fi
fi

# ─── Require manifest mode (legacy non-manifest path removed) ───────────────
# No manifest + SDD artifacts present → upstream failure, block with guidance.
# No manifest + no artifacts → not an SDD session, allow.
if [ "$MANIFEST_MODE" = false ]; then
  if [ -f ".active-feature" ]; then
    FEAT_CHECK=$(cat .active-feature | tr -d '\n' | sed 's|/$||')
    if [ -d "$FEAT_CHECK/reports" ] || [ -f "$FEAT_CHECK/deviations.md" ]; then
      echo "BLOCKED: SDD artifacts found in $FEAT_CHECK/ but no .sdd-session.json manifest. Run Plan Ingestion (materialize-manifest.py) to create the session manifest before dispatching tasks." >&2
      exit 2
    fi
  fi
  exit 0
fi

# ─── Manifest-mode dispatch classification (3-stage pipeline) ───────────────
# Order is load-bearing: reviewers are logged BEFORE any passthrough so that
# general-purpose reviewers (the post-2026-05-07 default) are recorded.
IS_REVIEWER=false
IS_IMPLEMENTER=false
REVIEW_TASK=""
REVIEW_TYPE="unknown"
TASK_NUMBER=""

# Stage 1: Reviewer detection (by description).
if echo "$DESCRIPTION" | grep -qiE '(review|spec.compliance|code.quality|spec.review|quality.review|trace.audit|partner.review)'; then
  IS_REVIEWER=true
fi

if [ "$IS_REVIEWER" = true ]; then
  # Item 3: ensure dispatch log dir + file exist (idempotent) before logging.
  mkdir -p "$(dirname "$DISPATCH_LOG")"
  touch "$DISPATCH_LOG"
  REVIEW_TASK=$(echo "$DESCRIPTION" | grep -oiE 'task\s*[0-9]+' | grep -oE '[0-9]+' | head -1)
  if echo "$DESCRIPTION" | grep -qiE '(spec.compliance|spec.review)'; then REVIEW_TYPE="spec-review"
  elif echo "$DESCRIPTION" | grep -qiE '(code.quality|quality.review)'; then REVIEW_TYPE="quality-review"
  elif echo "$DESCRIPTION" | grep -qiE 'trace.audit'; then REVIEW_TYPE="trace-audit"
  elif echo "$DESCRIPTION" | grep -qiE '(partner.review|controller.partner)'; then REVIEW_TYPE="partner-review"
  fi
  if [ -n "$REVIEW_TASK" ]; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) DISPATCH reviewer task=$REVIEW_TASK type=$REVIEW_TYPE" >> "$DISPATCH_LOG"
  fi
  # Sentinel — write on first reviewer dispatch.
  SENTINEL_LINE=$(head -1 "$DISPATCH_LOG" 2>/dev/null)
  if ! echo "$SENTINEL_LINE" | grep -q "^# sdd-hook-sentinel "; then
    SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"' 2>/dev/null)
    SENTINEL_HASH=$(echo -n "${SESSION_ID}-$(date -u +%Y%m%d%H%M%S)" | shasum -a 256 | cut -d' ' -f1)
    SENTINEL="# sdd-hook-sentinel $SENTINEL_HASH"
    TEMP_LOG=$(mktemp)
    echo "$SENTINEL" > "$TEMP_LOG"
    cat "$DISPATCH_LOG" >> "$TEMP_LOG"
    mv "$TEMP_LOG" "$DISPATCH_LOG"
  fi
  exit 0
fi

# Stage 2: Implementer detection (by description or prompt).
if echo "$DESCRIPTION" | grep -qiE '(implement|dispatch).*task\s*[0-9]'; then
  TASK_NUMBER=$(echo "$DESCRIPTION" | grep -oiE 'task\s*[0-9]+' | grep -oE '[0-9]+' | head -1)
  IS_IMPLEMENTER=true
elif echo "$PROMPT" | grep -qiE 'you are implementing task\s*[0-9]'; then
  TASK_NUMBER=$(echo "$PROMPT" | grep -oiE 'task\s*[0-9]+' | grep -oE '[0-9]+' | head -1)
  IS_IMPLEMENTER=true
fi

# Log implementer dispatch (gives git reality check reliable timestamps).
# Written here in Stage 2 — BEFORE the enforcement gate below — so the
# timestamp is recorded even when the dispatch is ultimately blocked.
if [ "$IS_IMPLEMENTER" = true ] && [ -n "$TASK_NUMBER" ]; then
  if [ -f "$DISPATCH_LOG" ]; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) DISPATCH implementer task=$TASK_NUMBER type=implementer" >> "$DISPATCH_LOG"
  elif [ -d "$(dirname "$DISPATCH_LOG")" ]; then
    touch "$DISPATCH_LOG"
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) DISPATCH implementer task=$TASK_NUMBER type=implementer" >> "$DISPATCH_LOG"
  fi
fi

# Stage 3: Not a reviewer, not an implementer → allow (Explore, Plan, ad-hoc).
if [ "$IS_IMPLEMENTER" = false ]; then
  exit 0
fi

# Validate task number is within the manifest's task range.
if [ -n "$TASK_NUMBER" ]; then
  if [ "$TASK_NUMBER" -lt "$MANIFEST_TASK_START" ] || [ "$TASK_NUMBER" -gt "$MANIFEST_TASK_END" ] 2>/dev/null; then
    echo "BLOCKED: Task $TASK_NUMBER is outside the manifest's task_range [$MANIFEST_TASK_START, $MANIFEST_TASK_END]. Check the active module in .sdd-session.json." >&2
    exit 2
  fi
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
  echo "${REPORTS_DIR}/task-${padded}-${report_type}*"
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

# ─── Helper: read task_type from plan YAML frontmatter ────────────────────
# Uses $PYTHON (PyYAML) to parse the YAML frontmatter's tasks array.
# Returns "implementation" (default) or "verification".
get_task_type() {
  local plan_file="$1"
  local task_id="$2"
  if [ ! -f "$plan_file" ]; then
    echo "implementation"
    return
  fi
  local result
  result=$($PYTHON -c "
import yaml, sys
with open(sys.argv[1]) as f:
    content = f.read()
if not content.startswith('---'):
    print('implementation')
    sys.exit(0)
end = content.find('---', 3)
if end == -1:
    print('implementation')
    sys.exit(0)
try:
    fm = yaml.safe_load(content[3:end])
except Exception:
    print('implementation')
    sys.exit(0)
tasks = fm.get('tasks', []) if isinstance(fm, dict) else []
tid = int(sys.argv[2])
for t in tasks:
    if isinstance(t, dict) and t.get('id') == tid:
        print(t.get('task_type', 'implementation'))
        sys.exit(0)
print('implementation')
" "$plan_file" "$task_id" 2>/dev/null)
  echo "${result:-implementation}"
}

# ─── Resolve plan file + task types for downstream check skipping ─────────
# get_task_type is defined above, so it is safe to call here. CURRENT_TASK_TYPE
# and PREV_TASK_TYPE are consumed by Task 3's verification-aware check skipping.
EFFECTIVE_PLAN_FILE=""
if [ -n "$MANIFEST_MODULE_FILE" ] && [ -f "$MANIFEST_MODULE_FILE" ]; then
  EFFECTIVE_PLAN_FILE="$MANIFEST_MODULE_FILE"
elif [ -n "$MANIFEST_PLAN_FILE" ] && [ -f "$MANIFEST_PLAN_FILE" ]; then
  EFFECTIVE_PLAN_FILE="$MANIFEST_PLAN_FILE"
fi

CURRENT_TASK_TYPE="implementation"
PREV_TASK_TYPE="implementation"
if [ -n "$EFFECTIVE_PLAN_FILE" ] && [ -n "$TASK_NUMBER" ]; then
  CURRENT_TASK_TYPE=$(get_task_type "$EFFECTIVE_PLAN_FILE" "$TASK_NUMBER")
  if [ "$TASK_NUMBER" -gt 0 ] 2>/dev/null; then
    PREV_TASK_TYPE=$(get_task_type "$EFFECTIVE_PLAN_FILE" "$((TASK_NUMBER - 1))")
  fi
fi

# ─── Enforcement checks (implementer dispatches only) ─────────────────────

# Check dispatch log sentinel integrity (WARN only, never blocks)
if [ -f "$DISPATCH_LOG" ]; then
  SENTINEL_LINE=$(head -1 "$DISPATCH_LOG" 2>/dev/null)
  if ! echo "$SENTINEL_LINE" | grep -q "^# sdd-hook-sentinel "; then
    echo "WARNING: Dispatch log exists but has no hook-written sentinel. The log may have been manually created." >&2
  fi
fi

ERRORS=()

# Check 1: Branch safety
# If SDD artifacts exist (reports/ + DEVIATIONS.md) AND on main → BLOCK
# Unless .allow-main exists (explicit user opt-in for main branch SDD)
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
  SDD_ARTIFACTS_EXIST=false
  if [ -d "$REPORTS_DIR" ] && [ -f "$DEVIATIONS_FILE" ]; then
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
# Gated by enforcement.pre_execution_audit in manifest mode ("false" → skip).
NEED_AUDIT=$(jq -r '.enforcement.pre_execution_audit' "$MANIFEST")
if [ "$NEED_AUDIT" = "false" ]; then
  : # Skip — manifest tier does not require pre-execution audit
else
  AUDIT_RESULT=$(check_report_file "${REPORTS_DIR}/pre-execution-audit*" "pre-execution audit")
  case "$AUDIT_RESULT" in
    MISSING)
      ERRORS+=("BLOCKED: No pre-execution audit report found (${REPORTS_DIR}/pre-execution-audit*). Complete the Pre-Execution Audit: (1) Write self-assessment to ${REPORTS_DIR}/pre-execution-audit-self-assessment.md, (2) Dispatch auditor via pre-execution-audit-prompt.md, (3) Resolve all remediation orders, (4) Save audit report to ${REPORTS_DIR}/pre-execution-audit.md.")
      ;;
    TOO_SMALL*)
      FILE_SIZE=$(echo "$AUDIT_RESULT" | cut -d: -f2)
      ERRORS+=("BLOCKED: Pre-execution audit report exists but is only $FILE_SIZE bytes — likely a placeholder. The audit report must contain the auditor's verdict and any remediation order resolutions (minimum $MIN_REPORT_BYTES bytes).")
      ;;
  esac
fi

# Check 3: DEVIATIONS.md must exist
if [ ! -f "$DEVIATIONS_FILE" ]; then
  ERRORS+=("BLOCKED: ${DEVIATIONS_FILE} does not exist. Create it with the SDD template before dispatching tasks. The SDD skill's Plan Ingestion step 5 requires this.")
fi

# Check 3: reports/ directory must exist
if [ ! -d "$REPORTS_DIR" ]; then
  ERRORS+=("BLOCKED: ${REPORTS_DIR}/ directory does not exist. Create it before dispatching tasks. Reports from each task are saved here for persistence and audit.")
fi

# Check 3b: Report naming convention
# Catches non-standard naming (m2-task-N, m3-feature-N, module1-task-N, etc.)
# BEFORE the per-task checks, so the error message explains the root cause.
if [ -d "$REPORTS_DIR" ]; then
  NON_STANDARD_FILES=()
  for rf in "${REPORTS_DIR}"/*.md; do
    if [ -f "$rf" ]; then
      BASENAME=$(basename "$rf")
      # Allow: task-NNN-*, pre-execution-audit*, context-summary*
      if ! echo "$BASENAME" | grep -qE '^(task-[0-9]+-|pre-execution-audit|context-summary|partner-review|checkpoint-pre-dispatch)'; then
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

  # ── Check 4 N-1 file existence: skip when current task is the first in the module ──
  # In manifest mode, the previous task's reports are archived from the prior module.
  # Wrap only this sub-block — dispatch provenance is gated separately below.
  if [ -n "$TASK_NUMBER" ] && [ "$TASK_NUMBER" -eq "$MANIFEST_TASK_START" ] 2>/dev/null; then
    : # Skip — first task in module, N-1 reports are from a prior archived module
  else
    # Previous task implementer report
    IMPL_GLOB=$(task_report_glob "$PREV" "implementer-report")
    RESULT=$(check_report_file "$IMPL_GLOB" "implementer report")
    case "$RESULT" in
      MISSING)
        ERRORS+=("BLOCKED: No implementer report found for Task $PREV (expected: ${REPORTS_DIR}/task-${PREV_PADDED}-implementer-report.md). Save the implementer's report using the task-NNN naming convention.")
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
        VALIDATE_OUTPUT=$($PYTHON "$VALIDATE_REPORT_SCRIPT" --report-file "$IMPL_LATEST" 2>&1)
        VALIDATE_EXIT=$?
        if [ "$VALIDATE_EXIT" -ne 0 ]; then
          VALIDATE_EXCERPT=$(echo "$VALIDATE_OUTPUT" | head -n 12)
          ERRORS+=("BLOCKED: Implementer report for Task $PREV ($IMPL_LATEST) failed validation (exit $VALIDATE_EXIT):\n${VALIDATE_EXCERPT}\n\nRe-dispatch the implementer to fix Pydantic frontmatter or complete all 5 required prose sections before proceeding.")
        else
          VALIDATE_STATUS=$(echo "$VALIDATE_OUTPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status',''))" 2>/dev/null)
          if [ "$VALIDATE_STATUS" = "INCOMPLETE" ]; then
            MISSING_SECTIONS=$(echo "$VALIDATE_OUTPUT" | python3 -c "import json,sys; print(', '.join(json.load(sys.stdin).get('sections_missing',[])))" 2>/dev/null)
            ERRORS+=("BLOCKED: Implementer report for Task $PREV ($IMPL_LATEST) is structurally incomplete — missing sections: $MISSING_SECTIONS. Re-dispatch the implementer to complete all 5 required prose sections before proceeding.")
          fi
        fi
      fi
    fi

    # Previous task spec + quality review reports.
    # Skipped when the previous task was a verification task — verification
    # tasks file an implementer report (checked above) but undergo no spec/quality
    # review cycle, so there are no review reports to require here.
    if [ "$PREV_TASK_TYPE" = "verification" ]; then
      : # Previous task was verification — no spec/quality reviews to check
    else
      # Previous task spec review report
      SPEC_GLOB=$(task_report_glob "$PREV" "spec-review")
      RESULT=$(check_report_file "$SPEC_GLOB" "spec review")
      case "$RESULT" in
        MISSING)
          ERRORS+=("BLOCKED: No spec review found for Task $PREV (expected: ${REPORTS_DIR}/task-${PREV_PADDED}-spec-review.md). Dispatch spec compliance review and save the report.")
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
          ERRORS+=("BLOCKED: No quality review found for Task $PREV (expected: ${REPORTS_DIR}/task-${PREV_PADDED}-quality-review.md). Dispatch code quality review, or save ${REPORTS_DIR}/task-${PREV_PADDED}-quality-review-minimum-tier.md if minimum tier declared.")
          ;;
        TOO_SMALL*)
          FILE_SIZE=$(echo "$RESULT" | cut -d: -f2)
          FILE_NAME=$(echo "$RESULT" | cut -d: -f3-)
          ERRORS+=("BLOCKED: Quality review for Task $PREV ($FILE_NAME) is only $FILE_SIZE bytes — save the actual reviewer output.")
          ;;
      esac
    fi
  fi

  # Check 4c: Dispatch provenance — verify reviewers were actually dispatched
  # Report files can be self-written by the controller. The dispatch log is written
  # by THIS HOOK when it processes Agent calls with reviewer descriptions.
  # The controller cannot forge dispatch log entries without going through the Agent tool.
  # Gated by enforcement.dispatch_provenance in manifest mode ("false" → skip).
  NEED_PROV=$(jq -r '.enforcement.dispatch_provenance' "$MANIFEST")
  if [ "$NEED_PROV" = "false" ]; then
    : # Skip — manifest tier does not require dispatch provenance
  elif [ "$PREV_TASK_TYPE" = "verification" ]; then
    : # Previous task was verification — no dispatch provenance to verify
  elif [ "$PREV" -lt "$MANIFEST_TASK_START" ] 2>/dev/null; then
    # N3a: PREV belongs to a prior (archived) module, or precedes the module's
    # first task (no-Task-0 plan, start=1). The live dispatch log was truncated
    # at the module boundary, so PREV's provenance lives in the archived log.
    # The completing module's boundary provenance is re-verified at transition
    # time by transition-module.py:validate_module_completion (sibling enforcement).
    : # Skip — boundary provenance verified at transition, not here
  else
    if [ -f "$DISPATCH_LOG" ]; then
      # Check for spec-review dispatch entry for previous task
      SPEC_DISPATCHED=false
      if grep -q "task=$PREV type=spec-review" "$DISPATCH_LOG" 2>/dev/null; then
        SPEC_DISPATCHED=true
      fi

      # Check for quality-review dispatch entry for previous task
      # quality-review-minimum-tier is acceptable if the report file matches that pattern
      QUAL_DISPATCHED=false
      QUAL_GLOB_MIN=$(task_report_glob "$PREV" "quality-review-minimum-tier")
      HAS_MINIMUM_TIER=$(ls $QUAL_GLOB_MIN 2>/dev/null | head -1)
      if grep -q "task=$PREV type=quality-review" "$DISPATCH_LOG" 2>/dev/null; then
        QUAL_DISPATCHED=true
      elif [ -n "$HAS_MINIMUM_TIER" ]; then
        # Minimum tier allows controller-written quality review (no dispatch needed)
        QUAL_DISPATCHED=true
      fi

      if [ "$SPEC_DISPATCHED" = false ]; then
        ERRORS+=("BLOCKED: No spec-review dispatch recorded for Task $PREV. The dispatch log ($DISPATCH_LOG) has no entry for a spec reviewer being dispatched via the Agent tool. Spec reviews must be dispatched subagents, not self-written by the controller. Dispatch the spec reviewer now.")
      fi

      if [ "$QUAL_DISPATCHED" = false ]; then
        ERRORS+=("BLOCKED: No quality-review dispatch recorded for Task $PREV. Dispatch the code quality reviewer via the Agent tool. Controller-written quality reviews are only allowed for minimum-tier tasks (and the file must be named task-NNN-quality-review-minimum-tier.md).")
      fi
    else
      # No dispatch log exists at all — log was deleted or no reviewers were ever dispatched
      ERRORS+=("BLOCKED: No dispatch log found ($DISPATCH_LOG). This file is created automatically by the SDD hook when reviewers are dispatched. Its absence means no reviewers were dispatched via the Agent tool for any task. Start by dispatching the spec reviewer for Task $PREV.")
    fi
  fi
fi

# Check 5: If Task N > 0 and plan has Source Contracts, verify Task 0 completed
# Unconditional — no enforcement flag gates this check. Required at any tier
# when the plan declares Source Contracts (Task 0 verifies them regardless).
# Checks only MANIFEST_PLAN_FILE (CWD-stable absolute path).
if [ -n "$TASK_NUMBER" ] && [ "$TASK_NUMBER" -gt 0 ] 2>/dev/null; then
  HAS_SOURCE_CONTRACTS=false
  # Check only the manifest's plan file (CWD-stable absolute path)
  if [ -f "$MANIFEST_PLAN_FILE" ]; then
    if grep -q "Source Contracts" "$MANIFEST_PLAN_FILE" && ! grep -qiE "Source Contracts.*:.*None" "$MANIFEST_PLAN_FILE"; then
      HAS_SOURCE_CONTRACTS=true
    fi
  fi

  if [ "$HAS_SOURCE_CONTRACTS" = true ]; then
    # N10: cover both the live reports dir and archived module dirs. A multi-
    # module plan with Source Contracts archives Task 0's report under
    # reports/archive-<module>/ at the first transition; Check 5 must still find
    # it. check_report_file runs `ls $pattern`, so space-separated globs work.
    T0_GLOB="${REPORTS_DIR}/task-000-implementer-report* ${REPORTS_DIR}/archive-*/task-000-implementer-report*"
    RESULT=$(check_report_file "$T0_GLOB" "Task 0 report")
    case "$RESULT" in
      MISSING)
        ERRORS+=("BLOCKED: Plan has Source Contracts but no Task 0 report found (expected: ${REPORTS_DIR}/task-000-implementer-report.md). Task 0 (Contract Verification) must complete first.")
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

if [ -f "$DEVIATIONS_FILE" ]; then
  PENDING_COUNT=$(grep -ciE '\|\s*Pending\s*\|' "$DEVIATIONS_FILE" 2>/dev/null || echo "0")
  if [ "$PENDING_COUNT" -gt 0 ] 2>/dev/null; then
    ERRORS+=("BLOCKED: $DEVIATIONS_FILE has $PENDING_COUNT pending deviation(s). Disposition all entries (Accepted/Rejected/Deferred) before dispatching the next task.")
  fi
fi

# ─── Check 5c: Controller checkpoint evidence ───────────────────────────────
# The controller must run controller-checkpoint.py --phase pre-dispatch before each
# dispatch and save the JSON output. This replaces the advisory instruction with
# a mechanical gate.
# Gated by enforcement.checkpoint_files in manifest mode ("false" → skip).
if [ -n "$TASK_NUMBER" ]; then
  NEED_CHECKPOINT=$(jq -r '.enforcement.checkpoint_files' "$MANIFEST")
  if [ "$NEED_CHECKPOINT" = "false" ]; then
    : # Skip — manifest tier does not require checkpoint files
  else
    TASK_PADDED=$(printf "%03d" "$TASK_NUMBER" 2>/dev/null || echo "$TASK_NUMBER")
    CHECKPOINT_FILE="${REPORTS_DIR}/checkpoint-pre-dispatch-${TASK_PADDED}.json"
    if [ ! -f "$CHECKPOINT_FILE" ]; then
      ERRORS+=("BLOCKED: No pre-dispatch checkpoint found for Task $TASK_NUMBER (expected: $CHECKPOINT_FILE). Run controller-checkpoint.py and save the output: python3 ~/.claude/skills/superpowers/subagent-driven-development/scripts/controller-checkpoint.py --phase pre-dispatch --task-number $TASK_NUMBER --plan-file <plan.md> --deviations-file $DEVIATIONS_FILE --reports-dir $REPORTS_DIR > $CHECKPOINT_FILE")
    elif [ "$(wc -c < "$CHECKPOINT_FILE" 2>/dev/null | tr -d ' ')" -lt "$MIN_REPORT_BYTES" ]; then
      ERRORS+=("BLOCKED: Checkpoint file $CHECKPOINT_FILE is too small (< $MIN_REPORT_BYTES bytes). Run the full controller-checkpoint.py command and redirect its JSON output to this file.")
    fi
  fi
fi

# ─── Check 5d: Partner review evidence + dispatch provenance ─────────────────
# The controller must dispatch the partner agent (or declare minimum tier)
# before dispatching the implementer. Task 0 is exempt — it's contract
# verification with no prior implementer context to cross-reference.
#
# Minimum-tier reviews are controller-written (no dispatch needed).
# Full-tier reviews must come from an actual agent dispatch — verified by
# checking the dispatch log for type=partner-review task=N, written by this
# hook when the partner Agent call passed through it.
#
# Gated by enforcement.partner_review in manifest mode ("false" → skip).
if [ -n "$TASK_NUMBER" ] && [ "$TASK_NUMBER" -gt 0 ] 2>/dev/null; then
  NEED_PARTNER=$(jq -r '.enforcement.partner_review' "$MANIFEST")
  if [ "$CURRENT_TASK_TYPE" = "verification" ]; then
    : # Current task is verification — no partner review required
  elif [ "$NEED_PARTNER" = "false" ]; then
    : # Skip — manifest tier does not require partner review
  else
    TASK_PADDED=$(printf "%03d" "$TASK_NUMBER" 2>/dev/null || echo "$TASK_NUMBER")
    PARTNER_FILE="${REPORTS_DIR}/partner-review-${TASK_PADDED}.md"
    PARTNER_FILE_MIN="${REPORTS_DIR}/partner-review-${TASK_PADDED}-minimum-tier.md"
    if [ -f "$PARTNER_FILE_MIN" ] && [ "$(wc -c < "$PARTNER_FILE_MIN" 2>/dev/null | tr -d ' ')" -ge "$MIN_REPORT_BYTES" ]; then
      : # Minimum tier — controller-written, no dispatch provenance needed
    elif [ -f "$PARTNER_FILE" ] && [ "$(wc -c < "$PARTNER_FILE" 2>/dev/null | tr -d ' ')" -ge "$MIN_REPORT_BYTES" ]; then
      # Full-tier review exists — verify it came from an actual agent dispatch
      if [ -f "$DISPATCH_LOG" ] && grep -q "task=$TASK_NUMBER type=partner-review" "$DISPATCH_LOG" 2>/dev/null; then
        : # Dispatch provenance confirmed
      else
        ERRORS+=("BLOCKED: partner-review-${TASK_PADDED}.md exists but no dispatch log entry found for type=partner-review task=$TASK_NUMBER. The partner review appears to be controller-written. Dispatch the partner agent (description must contain 'partner review') via the Agent tool so the hook can record provenance, then save the output to $PARTNER_FILE.")
      fi
    else
      ERRORS+=("BLOCKED: No partner review found for Task $TASK_NUMBER (expected: $PARTNER_FILE or $PARTNER_FILE_MIN). Dispatch the controller partner (see controller-partner-prompt.md) and save the output, or write a minimum-tier review with rationale (>$MIN_REPORT_BYTES bytes).")
    fi
  fi
fi

# ─── Check 6: Token budget estimation ─────────────────────────────────────

ESTIMATE_SCRIPT="$SUPERPOWERS_ROOT/skills/subagent-driven-development/scripts/estimate-task-tokens.py"
TOKEN_WARNING=""

if [ -n "$TASK_NUMBER" ] && [ -f "$ESTIMATE_SCRIPT" ]; then
  # Find a plan file to extract the task from.
  # Use the module file if it exists, else fall back to the manifest plan file.
  # These paths are absolute (set up in the manifest resolution block above).
  PLAN_FILE=""
  if [ -n "$MANIFEST_MODULE_FILE" ] && [ -f "$MANIFEST_MODULE_FILE" ]; then
    PLAN_FILE="$MANIFEST_MODULE_FILE"
  elif [ -n "$MANIFEST_PLAN_FILE" ] && [ -f "$MANIFEST_PLAN_FILE" ]; then
    PLAN_FILE="$MANIFEST_PLAN_FILE"
  fi

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
    # Diagnostic: couldn't resolve a plan file from the manifest
    ERRORS+=("BLOCKED: Token estimation could not run for Task $TASK_NUMBER — the manifest's plan file was not found (plan_file: ${MANIFEST_PLAN_FILE:-unset}, active_module_file: ${MANIFEST_MODULE_FILE:-unset}). Verify .sdd-session.json points at an existing plan file.")
  fi
fi

# ─── Check 6b: Context summary at midpoint ────────────────────────────────
# The SDD skill requires context-summary.py to be run at the halfway point
# "regardless of context load." If we're past the midpoint and the summary
# doesn't exist, inject a WARNING.

if [ -n "$TASK_NUMBER" ] && [ "$TASK_NUMBER" -gt 1 ]; then
  # Use enforcement.context_summary_at (int threshold or null).
  # jq returns the literal string "null" when JSON value is null.
  CONTEXT_SUMMARY_AT=$(jq -r '.enforcement.context_summary_at' "$MANIFEST")
  if [ "$CONTEXT_SUMMARY_AT" = "null" ] || [ -z "$CONTEXT_SUMMARY_AT" ]; then
    : # context_summary_at is null — this tier doesn't require a context summary
  elif [ "$TASK_NUMBER" -ge "$CONTEXT_SUMMARY_AT" ] 2>/dev/null; then
    if [ ! -f "${REPORTS_DIR}/context-summary.md" ]; then
      ERRORS+=("BLOCKED: Context summary required at task $CONTEXT_SUMMARY_AT threshold (enforcement.context_summary_at). You are at Task $TASK_NUMBER. Run context-summary.py before dispatching: python3 ~/.claude/skills/superpowers/subagent-driven-development/scripts/context-summary.py --reports-dir $REPORTS_DIR --deviations-file $DEVIATIONS_FILE --output ${REPORTS_DIR}/context-summary.md")
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
if [ -d "$REPORTS_DIR" ]; then
  TOTAL_BYTES=0

  # Sum plan files (from the manifest: plan file + active module file)
  for pf in "$MANIFEST_PLAN_FILE" "$MANIFEST_MODULE_FILE"; do
    if [ -n "$pf" ] && [ -f "$pf" ]; then
      PF_SIZE=$(wc -c < "$pf" 2>/dev/null | tr -d ' ')
      TOTAL_BYTES=$((TOTAL_BYTES + PF_SIZE))
    fi
  done

  # Sum DEVIATIONS file
  if [ -f "$DEVIATIONS_FILE" ]; then
    DEV_SIZE=$(wc -c < "$DEVIATIONS_FILE" 2>/dev/null | tr -d ' ')
    TOTAL_BYTES=$((TOTAL_BYTES + DEV_SIZE))
  fi

  # Sum all report files
  for rf in "${REPORTS_DIR}"/*.md; do
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
CONTEXT="SDD REMINDER: After this subagent completes, you must: (1) Save the implementer report to ${REPORTS_DIR}/task-N-implementer-report.md, (2) Dispatch spec compliance review and save to ${REPORTS_DIR}/task-N-spec-review.md, (3) Dispatch code quality review and save to ${REPORTS_DIR}/task-N-quality-review.md, (4) Log any DONE_WITH_CONCERNS to ${DEVIATIONS_FILE}, (5) Update plan checkboxes. The next task dispatch will be BLOCKED if these reports are missing or empty."

# Read process requirements from manifest for injection
PR_DISPATCH=$(jq -r '.process_requirements.subagent_dispatch' "$MANIFEST")
PR_SPEC=$(jq -r '.process_requirements.spec_review_mode' "$MANIFEST")
PR_QUALITY=$(jq -r '.process_requirements.quality_review_mode' "$MANIFEST")
PR_PARTNER=$(jq -r '.process_requirements.partner_review_mode' "$MANIFEST")
PR_DEVLOG=$(jq -r '.process_requirements.deviations_log' "$MANIFEST")
PR_CHECKPOINT=$(jq -r '.process_requirements.checkpoint_script' "$MANIFEST")

PROCESS_CONTRACT="SDD SESSION CONTRACT (from .sdd-session.json): Tier: $MANIFEST_TIER | Subagent dispatch: $PR_DISPATCH | Spec review: $PR_SPEC | Quality review: $PR_QUALITY | Partner review: $PR_PARTNER | Deviations log: $PR_DEVLOG | Checkpoint script: $PR_CHECKPOINT"

CONTEXT="$CONTEXT | $PROCESS_CONTRACT"

if [ -n "$TOKEN_WARNING" ]; then
  CONTEXT="$CONTEXT | $TOKEN_WARNING"
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
