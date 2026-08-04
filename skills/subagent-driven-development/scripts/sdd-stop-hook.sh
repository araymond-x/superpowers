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

SUPERPOWERS_ROOT="${SUPERPOWERS_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"

if [ -f "$SUPERPOWERS_ROOT/.venv/bin/python3" ]; then
  PYTHON="$SUPERPOWERS_ROOT/.venv/bin/python3"
else
  PYTHON="python3"
fi

CHECKPOINT_SCRIPT="$SUPERPOWERS_ROOT/skills/subagent-driven-development/scripts/controller-checkpoint.py"

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

# ─── Resolve active feature directory ─────────────────────────────────────
FEAT=""
if [ -f "${CWD}/.active-feature" ]; then
  FEAT=$(cat "${CWD}/.active-feature")
fi

# ─── SDD session detection ────────────────────────────────────────────────────
# Only proceed if both SDD sentinel artifacts exist in CWD.
# reports/ + deviations.md (or DEVIATIONS.md at root) = this is an active SDD session.

if [ -n "$FEAT" ]; then
  REPORTS_DIR="${CWD}/${FEAT}/reports"
  DEVIATIONS_FILE="${CWD}/${FEAT}/deviations.md"
else
  REPORTS_DIR="${CWD}/reports"
  DEVIATIONS_FILE="${CWD}/DEVIATIONS.md"
fi

if [ ! -d "$REPORTS_DIR" ]; then
  exit 0
fi

if [ ! -f "$DEVIATIONS_FILE" ]; then
  exit 0
fi

# ─── Spawn-outcome step-completion check (cmux-spawn-v2 Decision 15) ─────────
# A handoff bundle created during THIS session with no matching spawn outcome
# and no decline record means the controller stopped mid-protocol (built the
# bundle, never ran the spawn script, never declined). Matching key: bundle id
# (outcome records carry bundle=<id>); mtime only bounds the candidate set.
SPAWN_WARN=""
BUNDLES_DIR="$HOME/.claude-codex-handoff/bundles"
TRANSCRIPT=$(echo "$INPUT" | jq -r '.transcript_path // ""' 2>/dev/null)
SESSION_START=""
if [ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ]; then
  SESSION_START=$(head -n 1 "$TRANSCRIPT" 2>/dev/null | jq -r '.timestamp // ""' 2>/dev/null)
fi
if [ -n "$SESSION_START" ] && [ -d "$BUNDLES_DIR" ]; then
  SPAWN_LOG_FILE="${REPORTS_DIR}/handoff-spawn.log"
  REPO_ID=$(cd "$CWD" && python3 -c 'import os,subprocess;c=subprocess.run(["git","rev-parse","--git-common-dir"],capture_output=True,text=True).stdout.strip();print(os.path.realpath(c if os.path.isabs(c) else os.path.join(os.getcwd(),c)))' 2>/dev/null)
  START_EPOCH=$(python3 -c 'import sys,datetime;print(int(datetime.datetime.fromisoformat(sys.argv[1].replace("Z","+00:00")).timestamp()))' "$SESSION_START" 2>/dev/null)
  for bdir in "$BUNDLES_DIR"/*/; do
    [ -d "$bdir" ] || continue
    BID=$(basename "$bdir")
    BMTIME=$(stat -f %m "$bdir" 2>/dev/null || stat -c %Y "$bdir" 2>/dev/null)
    [ -n "$BMTIME" ] && [ -n "$START_EPOCH" ] && [ "$BMTIME" -ge "$START_EPOCH" ] || continue
    BTYPE=$(jq -r '.session.bundle_type // ""' "$bdir/manifest.json" 2>/dev/null)
    BSKILL=$(jq -r '.session.entry_skill // ""' "$bdir/manifest.json" 2>/dev/null)
    BREPO=$(jq -r '.project.repo_id // ""' "$bdir/manifest.json" 2>/dev/null)
    [ "$BTYPE" = "work" ] && [ "$BSKILL" = "superpowers:subagent-driven-development" ] && [ "$BREPO" = "$REPO_ID" ] || continue
    # Regex-escape $BID: it is interpolated into an ERE below, and a validated
    # bundle id may contain '.', which would otherwise match any char (N84).
    BID_RE=$(printf '%s' "$BID" | sed 's/[][\\.^$*+?(){}|/]/\\&/g')
    if [ -f "$SPAWN_LOG_FILE" ] && grep -qE "( outcome .*bundle=$BID_RE( |$))|( decline bundle=$BID_RE( |$))" "$SPAWN_LOG_FILE"; then
      continue
    fi
    SPAWN_WARN="WARNING: handoff bundle $BID was created this session but reports/handoff-spawn.log has no outcome or decline record for it. Either run spawn-handoff-session.sh $BID (protocol step 4), or record the decline: printf '%s - decline bundle=%s reason=<word>\n' \"\$(date -u +%Y-%m-%dT%H:%M:%SZ)\" $BID >> $SPAWN_LOG_FILE"
    break
  done
fi

# ─── Prerequisite checks ──────────────────────────────────────────────────────

# controller-checkpoint.py must exist
if [ ! -f "$CHECKPOINT_SCRIPT" ]; then
  exit 0
fi

# Find the plan file
PLAN_FILE=""
if [ -n "$FEAT" ]; then
  for candidate in "${CWD}/${FEAT}/"*.md; do
    if [ -f "$candidate" ]; then
      PLAN_FILE="$candidate"
      break
    fi
  done
else
  for candidate in "${CWD}/docs/imp-plans/"*.md "${CWD}/docs/plans/"*.md; do
    if [ -f "$candidate" ]; then
      PLAN_FILE="$candidate"
      break
    fi
  done
fi

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
  for candidate in "${REPORTS_DIR}"/honesty-check-*.md; do
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
  $PYTHON "$CHECKPOINT_SCRIPT" \
    --phase pre-completion \
    --plan-file "$PLAN_FILE" \
    --deviations-file "$DEVIATIONS_FILE" \
    --reports-dir "$REPORTS_DIR/" \
    2>/dev/null
)

# Key off emptiness ALONE. controller-checkpoint.py prints its JSON to stdout
# BEFORE choosing an exit code and returns 1 on status=FAIL / 2 on advisory
# WARNING — so a non-zero exit with non-empty output is a real gate result that
# must be surfaced below, not swallowed. Only a genuine crash (except-path prints
# to stderr) leaves stdout empty; that alone is the don't-block case.
if [ -z "$CHECKPOINT_OUTPUT" ]; then
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
  if [ -n "$SPAWN_WARN" ]; then
    CONTEXT_MSG="${CONTEXT_MSG}

${SPAWN_WARN}"
  fi
  ESCAPED_MSG=$(echo "$CONTEXT_MSG" | python3 -c 'import sys, json; print(json.dumps(sys.stdin.read().rstrip()))')
  # Use systemMessage for Stop hooks (hookSpecificOutput not supported for Stop events)
  cat << HOOKJSON
{
  "systemMessage": ${ESCAPED_MSG}
}
HOOKJSON
elif [ -n "$SPAWN_WARN" ]; then
  # Gate passed but a this-session handoff bundle has no outcome/decline record.
  ESCAPED_MSG=$(echo "$SPAWN_WARN" | python3 -c 'import sys, json; print(json.dumps(sys.stdin.read().rstrip()))')
  cat << HOOKJSON
{
  "systemMessage": ${ESCAPED_MSG}
}
HOOKJSON
else
  # Gate passed, no spawn warning — no output needed (exit 0 silently)
  :
fi

exit 0
