#!/usr/bin/env bash
# sdd-pre-dispatch-hook-patched.sh — POC patched version of sdd-pre-dispatch-hook.sh
#
# This is a MINIMAL patch of the real hook to test whether SDD enforcement
# works when reports/ and deviations.md live inside a feature directory
# instead of at the project root.
#
# Changes from original:
#   - Accepts feature directory as $1 argument
#   - Looks for reports/ inside $FEATURE_DIR instead of project root
#   - Looks for deviations.md inside $FEATURE_DIR instead of project root
#   - Removes worktree checks (not relevant to this POC)
#   - Removes token estimation (not relevant to this POC)
#
# Usage: echo '{"tool_input":{...},"cwd":"/path"}' | bash this-script.sh <feature-dir>

set -o pipefail

MIN_REPORT_BYTES=50

VALIDATE_REPORT_SCRIPT="/Users/araymond/projects/claude-custom/superpowers/skills/subagent-driven-development/scripts/validate-report.py"

# Feature directory passed as argument (the key difference from the original)
FEATURE_DIR="${1:-}"

INPUT=$(cat)

if ! command -v jq &>/dev/null; then
  echo "WARNING: jq not found" >&2
  exit 0
fi

DESCRIPTION=$(echo "$INPUT" | jq -r '.tool_input.description // ""' 2>/dev/null)
PROMPT=$(echo "$INPUT" | jq -r '.tool_input.prompt // ""' 2>/dev/null | head -c 500)
CWD=$(echo "$INPUT" | jq -r '.cwd // ""' 2>/dev/null)

if [ -z "$CWD" ] || [ ! -d "$CWD" ]; then
  exit 0
fi

cd "$CWD" || exit 0

# Determine dispatch type
TASK_NUMBER=""
IS_IMPLEMENTER=false
if echo "$DESCRIPTION" | grep -qiE '(implement|dispatch).*task\s*[0-9]'; then
  TASK_NUMBER=$(echo "$DESCRIPTION" | grep -oiE 'task\s*[0-9]+' | grep -oE '[0-9]+' | head -1)
  IS_IMPLEMENTER=true
elif echo "$PROMPT" | grep -qiE 'you are implementing task\s*[0-9]'; then
  TASK_NUMBER=$(echo "$PROMPT" | grep -oiE 'task\s*[0-9]+' | grep -oE '[0-9]+' | head -1)
  IS_IMPLEMENTER=true
fi

IS_REVIEWER=false
if echo "$DESCRIPTION" | grep -qiE '(review|spec.compliance|code.quality)'; then
  IS_REVIEWER=true
fi

if [ "$IS_REVIEWER" = true ]; then
  exit 0
fi

if [ "$IS_IMPLEMENTER" = false ]; then
  exit 0
fi

# ---- Feature-dir scoped helpers (THE KEY CHANGE) ----------------------------

# Reports directory is inside the feature dir
REPORTS_DIR="$FEATURE_DIR/reports"
DEVIATIONS_FILE="$FEATURE_DIR/deviations.md"

task_report_glob() {
  local task_num="$1"
  local report_type="$2"
  local padded
  padded=$(printf "%03d" "$task_num" 2>/dev/null || echo "$task_num")
  echo "$REPORTS_DIR/task-${padded}-${report_type}*"
}

check_report_file() {
  local pattern="$1"
  local label="$2"
  local matches
  matches=$(ls $pattern 2>/dev/null)
  if [ -z "$matches" ]; then
    echo "MISSING"
    return
  fi
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

# ---- Enforcement checks (feature-dir scoped) --------------------------------

ERRORS=()

# Check: Pre-execution audit (inside feature dir reports/)
AUDIT_RESULT=$(check_report_file "$REPORTS_DIR/pre-execution-audit*" "pre-execution audit")
case "$AUDIT_RESULT" in
  MISSING)
    ERRORS+=("BLOCKED: No pre-execution audit report found in $REPORTS_DIR/")
    ;;
  TOO_SMALL*)
    FILE_SIZE=$(echo "$AUDIT_RESULT" | cut -d: -f2)
    ERRORS+=("BLOCKED: Pre-execution audit report is only $FILE_SIZE bytes")
    ;;
esac

# Check: deviations.md (inside feature dir)
if [ ! -f "$DEVIATIONS_FILE" ]; then
  ERRORS+=("BLOCKED: $DEVIATIONS_FILE does not exist")
fi

# Check: reports/ directory (inside feature dir)
if [ ! -d "$REPORTS_DIR" ]; then
  ERRORS+=("BLOCKED: $REPORTS_DIR does not exist")
fi

# Check: Report naming convention (inside feature dir)
if [ -d "$REPORTS_DIR" ]; then
  NON_STANDARD_FILES=()
  for rf in "$REPORTS_DIR"/*.md; do
    if [ -f "$rf" ]; then
      BASENAME=$(basename "$rf")
      if ! echo "$BASENAME" | grep -qE '^(task-[0-9]+-|pre-execution-audit|context-summary)'; then
        NON_STANDARD_FILES+=("$BASENAME")
      fi
    fi
  done
  if [ ${#NON_STANDARD_FILES[@]} -gt 0 ]; then
    ERRORS+=("BLOCKED: ${#NON_STANDARD_FILES[@]} non-standard report file(s) in $REPORTS_DIR")
  fi
fi

# Check: Previous task reviewed (inside feature dir)
if [ -n "$TASK_NUMBER" ] && [ "$TASK_NUMBER" -gt 0 ] 2>/dev/null; then
  PREV=$((TASK_NUMBER - 1))
  PREV_PADDED=$(printf "%03d" "$PREV")

  IMPL_GLOB=$(task_report_glob "$PREV" "implementer-report")
  RESULT=$(check_report_file "$IMPL_GLOB" "implementer report")
  case "$RESULT" in
    MISSING) ERRORS+=("BLOCKED: No implementer report for Task $PREV in $REPORTS_DIR") ;;
    TOO_SMALL*) ERRORS+=("BLOCKED: Implementer report for Task $PREV too small") ;;
  esac

  SPEC_GLOB=$(task_report_glob "$PREV" "spec-review")
  RESULT=$(check_report_file "$SPEC_GLOB" "spec review")
  case "$RESULT" in
    MISSING) ERRORS+=("BLOCKED: No spec review for Task $PREV in $REPORTS_DIR") ;;
    TOO_SMALL*) ERRORS+=("BLOCKED: Spec review for Task $PREV too small") ;;
  esac

  QUAL_GLOB=$(task_report_glob "$PREV" "quality-review")
  RESULT=$(check_report_file "$QUAL_GLOB" "quality review")
  case "$RESULT" in
    MISSING) ERRORS+=("BLOCKED: No quality review for Task $PREV in $REPORTS_DIR") ;;
    TOO_SMALL*) ERRORS+=("BLOCKED: Quality review for Task $PREV too small") ;;
  esac
fi

# Check: Pending deviations
if [ -f "$DEVIATIONS_FILE" ]; then
  PENDING_COUNT=$(grep -ciE '\|\s*Pending\s*\|' "$DEVIATIONS_FILE" 2>/dev/null || echo "0")
  if [ "$PENDING_COUNT" -gt 0 ] 2>/dev/null; then
    ERRORS+=("BLOCKED: $DEVIATIONS_FILE has $PENDING_COUNT pending deviation(s)")
  fi
fi

# ---- Report results ---------------------------------------------------------

if [ ${#ERRORS[@]} -gt 0 ]; then
  ERROR_MSG=""
  for err in "${ERRORS[@]}"; do
    ERROR_MSG="${ERROR_MSG}${err}\n"
  done
  echo -e "$ERROR_MSG" >&2
  exit 2
fi

# All passed
CONTEXT="SDD DISPATCH ALLOWED (feature-dir: $FEATURE_DIR): All pre-dispatch checks passed with feature-scoped artifacts."
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
