#!/usr/bin/env bash
# spawn-handoff-session.sh BUNDLE_ID [--dry-run]
#
# Auto-spawn the SDD controller's successor session in a new cmux workspace via
# the extended claude-picker. Invoked by context-handoff-protocol.md step 4.
# NOTE: intentionally does NOT use `set -u` and never pipes a producer into
# `grep -q` under pipefail. See CLAUDE.md Hook Development Gotchas.

# --- Layer 0: resolution + config ------------------------------------------
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$(cd "$(dirname "$SOURCE")" && pwd)"; SOURCE="$(readlink "$SOURCE")"
  [[ "$SOURCE" != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd "$(dirname "$SOURCE")" && pwd)"
SUPERPOWERS_ROOT="${SUPERPOWERS_ROOT:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"
PYTHON="$SUPERPOWERS_ROOT/.venv/bin/python3"
[ -x "$PYTHON" ] || PYTHON="python3"   # this script needs only json/base64 stdlib

MAX_HOPS="${SUPERPOWERS_CMUX_MAX_HOPS:-3}"
QUOTA_MIN_PCT="${SUPERPOWERS_CMUX_QUOTA_MIN_PCT:-15}"
BUNDLES_DIR="$HOME/.claude-codex-handoff/bundles"
QUOTA_TOOL_DEFAULT="$HOME/.claude/bin/claude-usage-pace"
EXPECTED_BUNDLE_TYPE="work"
EXPECTED_ENTRY_SKILL="superpowers:subagent-driven-development"
PICKER_CONTRACT="1"

# --- Arg parse -------------------------------------------------------------
BUNDLE_ID=""; DRY_RUN=0
for a in "$@"; do
  case "$a" in
    --dry-run) DRY_RUN=1 ;;
    -*) echo "spawn-handoff-session.sh: unknown flag: $a" >&2; exit 1 ;;
    *) if [ -z "$BUNDLE_ID" ]; then BUNDLE_ID="$a"; else
         echo "spawn-handoff-session.sh: unexpected extra arg: $a" >&2; exit 1; fi ;;
  esac
done
if [ -z "$BUNDLE_ID" ]; then
  echo "usage: spawn-handoff-session.sh BUNDLE_ID [--dry-run]  (BUNDLE_ID required)" >&2
  exit 1
fi

# --- Worktree + feature dir ------------------------------------------------
WORKTREE_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$WORKTREE_ROOT" ]; then echo "REFUSED: not in a git repository" >&2; exit 1; fi
cd "$WORKTREE_ROOT" || { echo "REFUSED: cannot cd to worktree root" >&2; exit 1; }
if [ ! -f .active-feature ]; then
  echo "REFUSED: missing .active-feature (SDD sessions always have one)" >&2; exit 1; fi
FEATURE_DIR="$(cat .active-feature)"
REPORTS_DIR="$WORKTREE_ROOT/$FEATURE_DIR/reports"
FEATURE_NAME="$(basename "$FEATURE_DIR")"
HOPS_FILE="$REPORTS_DIR/.handoff-hops"
SPAWN_LOG="$REPORTS_DIR/handoff-spawn.log"

now_iso() { date -u +%Y-%m-%dT%H:%M:%SZ; }

print_manual_instructions() {
  cat <<EOF
[spawn-handoff] Manual resume required. Start a FRESH session FROM the worktree:
    cd "$WORKTREE_ROOT" && claude
then run:
    /pickup $BUNDLE_ID
Then STOP the current session (do not dispatch the next task here).
EOF
}

# --- Precondition 1: clean tree --------------------------------------------
if [ -n "$(git status --porcelain)" ]; then
  echo "REFUSED: worktree not clean — commit pending state first (protocol step 2)" >&2; exit 1; fi

# (Task 2 inserts bundle validation + cmux + hop preconditions here.)
# (Task 3 inserts the quota check here.)
# (Tasks 4-5 insert launch composition here.)
# (Task 6 inserts the spawn sequence + exit here.)
echo "[spawn-handoff] basic preconditions passed (skeleton — later tasks complete the flow)" >&2
exit 0
