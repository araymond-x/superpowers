#!/usr/bin/env bash
# sdd-stop-hook.sh — Auto-run pre-completion checkpoint when SDD controller stops
#
# Stop hook that detects SDD sessions (via reports/ and DEVIATIONS.md presence)
# and injects pre-completion gate results into the controller's context.
#
# Exit codes:
#   0 — Always (advisory injection, never blocks)

set -o pipefail
# Note: not using -u (strict unset vars) because jq pipe chains can produce
# empty variables that would cause silent exit with no error message

CHECKPOINT_SCRIPT="/Users/araymond/projects/claude-custom/superpowers/skills/subagent-driven-development/scripts/controller-checkpoint.py"

# Read stdin
INPUT=$(cat)

# Check for jq — required for JSON parsing
if ! command -v jq &>/dev/null; then
  exit 0
fi

# Extract CWD from the hook payload
CWD=$(echo "$INPUT" | jq -r '.cwd // ""' 2>/dev/null)
if [ -z "$CWD" ] || [ ! -d "$CWD" ]; then
  exit 0
fi

# ─── SDD session detection ────────────────────────────────────────────────────
# Only proceed if both SDD sentinel artifacts exist in CWD.
# reports/ + DEVIATIONS.md = this is an active SDD session.

if [ ! -d "${CWD}/reports" ]; then
  exit 0
fi

if [ ! -f "${CWD}/DEVIATIONS.md" ]; then
  exit 0
fi

# ─── Prerequisite checks ──────────────────────────────────────────────────────

# controller-checkpoint.py must exist
if [ ! -f "$CHECKPOINT_SCRIPT" ]; then
  exit 0
fi

# Find the plan file — look in docs/imp-plans/ then docs/plans/
PLAN_FILE=""
for candidate in "${CWD}/docs/imp-plans/"*.md "${CWD}/docs/plans/"*.md; do
  if [ -f "$candidate" ]; then
    PLAN_FILE="$candidate"
    break
  fi
done

if [ -z "$PLAN_FILE" ]; then
  exit 0
fi

# ─── Capture honesty check response to vault ─────────────────────────────────
# Copies reports/honesty-check-*.md to individual files in the vault so
# responses accumulate across all projects and are QMD-searchable.

VAULT_DIR="${VAULT_DIR:-}"

if [ -n "$VAULT_DIR" ]; then
  # Find the most recent honesty check file (glob for honesty-check-*.md)
  HONESTY_FILE=""
  for candidate in "${CWD}"/reports/honesty-check-*.md; do
    if [ -f "$candidate" ] && [ "$(wc -c < "$candidate" | tr -d ' ')" -ge 50 ]; then
      HONESTY_FILE="$candidate"
    fi
  done

  if [ -n "$HONESTY_FILE" ]; then
    VAULT_HC_DIR="${VAULT_DIR}/References/SDD/honesty-checks"
    mkdir -p "$VAULT_HC_DIR"

    TODAY=$(date +%Y-%m-%d)
    BRANCH=$(cd "$CWD" && git branch --show-current 2>/dev/null || echo "unknown")
    PROJECT=$(cd "$CWD" && basename "$(git rev-parse --show-toplevel 2>/dev/null)" || basename "$CWD")

    # Sanitize branch name for filesystem (replace / with -)
    SAFE_BRANCH=$(echo "$BRANCH" | tr '/' '-')
    VAULT_FILE="${VAULT_HC_DIR}/${TODAY}-${PROJECT}-${SAFE_BRANCH}.md"

    # Idempotency: skip if file already exists
    if [ ! -f "$VAULT_FILE" ]; then
      {
        echo "---"
        echo "type: honesty-check"
        echo "date: ${TODAY}"
        echo "project: ${PROJECT}"
        echo "branch: ${BRANCH}"
        echo "source: $(basename "$HONESTY_FILE")"
        echo "---"
        echo ""
        cat "$HONESTY_FILE"
      } > "$VAULT_FILE"
    fi
  fi
fi

# ─── Run pre-completion checkpoint ────────────────────────────────────────────

CHECKPOINT_OUTPUT=$(
  python3 "$CHECKPOINT_SCRIPT" \
    --phase pre-completion \
    --plan-file "$PLAN_FILE" \
    --deviations-file "${CWD}/DEVIATIONS.md" \
    --reports-dir "${CWD}/reports/" \
    2>/dev/null
)

if [ $? -ne 0 ] || [ -z "$CHECKPOINT_OUTPUT" ]; then
  exit 0
fi

# Extract status and blocker details from checkpoint JSON output
STATUS=$(echo "$CHECKPOINT_OUTPUT" | jq -r '.status // "UNKNOWN"' 2>/dev/null)
BLOCKERS=$(echo "$CHECKPOINT_OUTPUT" | jq -r '
  if .blockers and (.blockers | length) > 0 then
    .blockers | map(
      . as $key |
      ($key + ": " + (
        if .checks[$key]? then .checks[$key].detail
        else "see checkpoint output"
        end
      ))
    ) | join("; ")
  else ""
  end
' 2>/dev/null || echo "")

# Extract blocker details from checks using a simpler approach
if [ -z "$BLOCKERS" ] || [ "$BLOCKERS" = "null" ]; then
  BLOCKERS=$(echo "$CHECKPOINT_OUTPUT" | jq -r '
    [.checks // {} | to_entries[] | select(.value.status == "FAIL") | .value.detail]
    | join("; ")
  ' 2>/dev/null || echo "see checkpoint output")
fi

# ─── Inject result based on checkpoint status ────────────────────────────────

if [ "$STATUS" = "FAIL" ]; then
  CONTEXT_MSG="Pre-Completion Gate FAILED. Issues: ${BLOCKERS:-see checkpoint output}. Address these before declaring implementation complete."
  ESCAPED_MSG=$(echo "$CONTEXT_MSG" | python3 -c 'import sys, json; print(json.dumps(sys.stdin.read().rstrip()))')
  # Use systemMessage for Stop hooks (hookSpecificOutput not supported for Stop events)
  cat << HOOKJSON
{
  "systemMessage": ${ESCAPED_MSG}
}
HOOKJSON
else
  # Gate passed — no output needed (exit 0 silently)
  :
fi

exit 0
