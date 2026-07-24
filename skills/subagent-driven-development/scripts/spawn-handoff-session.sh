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

# --- Precondition 2: parameterized bundle validation (Decision 22) ----------
# validate_bundle BUNDLE_ID EXPECTED_TYPE EXPECTED_SKILL WORKTREE_ROOT
validate_bundle() {
  local bid="$1" exp_type="$2" exp_skill="$3" wt="$4"
  if ! [[ "$bid" =~ ^[A-Za-z0-9_.-]+$ ]]; then
    echo "REFUSED: bundle id fails charset ^[A-Za-z0-9_.-]+$" >&2; return 1; fi
  local real_bundles real_bdir
  real_bundles="$(cd "$BUNDLES_DIR" 2>/dev/null && pwd -P)"
  if [ -z "$real_bundles" ]; then echo "REFUSED: bundles dir not found: $BUNDLES_DIR" >&2; return 1; fi
  real_bdir="$(cd "$BUNDLES_DIR/$bid" 2>/dev/null && pwd -P)"
  if [ -z "$real_bdir" ]; then echo "REFUSED: bundle dir not found for id: $bid" >&2; return 1; fi
  case "$real_bdir" in
    "$real_bundles"/*) : ;;
    *) echo "REFUSED: bundle resolves outside bundles dir" >&2; return 1 ;;
  esac
  local manifest="$real_bdir/manifest.json"
  if [ ! -f "$manifest" ]; then echo "REFUSED: bundle has no manifest.json" >&2; return 1; fi
  local btype bskill brepo active_id
  btype="$("$PYTHON" -c 'import json,sys;print((json.load(open(sys.argv[1])).get("session") or {}).get("bundle_type",""))' "$manifest")"
  bskill="$("$PYTHON" -c 'import json,sys;print((json.load(open(sys.argv[1])).get("session") or {}).get("entry_skill",""))' "$manifest")"
  brepo="$("$PYTHON" -c 'import json,sys;print((json.load(open(sys.argv[1])).get("project") or {}).get("repo_id",""))' "$manifest")"
  if [ "$btype" != "$exp_type" ]; then echo "REFUSED: bundle_type '$btype' != expected '$exp_type'" >&2; return 1; fi
  if [ "$bskill" != "$exp_skill" ]; then echo "REFUSED: entry_skill '$bskill' != expected '$exp_skill'" >&2; return 1; fi
  if [ -z "$brepo" ]; then echo "REFUSED: bundle manifest has no project.repo_id" >&2; return 1; fi
  # Worktree-invariant identity — mirrors the pickup guard's repo_identity() exactly.
  active_id="$("$PYTHON" - "$wt" <<'PY'
import os, subprocess, sys
wt = sys.argv[1]
c = subprocess.run(["git","rev-parse","--git-common-dir"], cwd=wt,
                   capture_output=True, text=True).stdout.strip()
p = c if os.path.isabs(c) else os.path.join(wt, c)
print(os.path.realpath(p))
PY
)"
  if [ "$active_id" != "$brepo" ]; then
    echo "REFUSED: bundle repo mismatch (active '$active_id' != bundle '$brepo')" >&2; return 1; fi
  return 0
}
if ! validate_bundle "$BUNDLE_ID" "$EXPECTED_BUNDLE_TYPE" "$EXPECTED_ENTRY_SKILL" "$WORKTREE_ROOT"; then
  exit 1; fi

# --- Precondition 3: cmux reachable ----------------------------------------
if [ -z "$CMUX_WORKSPACE_ID" ] || [ "$(cmux ping 2>/dev/null)" != "PONG" ]; then
  echo "[spawn-handoff] not in a reachable cmux workspace — manual fallback." >&2
  print_manual_instructions
  exit 3
fi

# --- Precondition 4: hop limit ---------------------------------------------
HOPS="$(cat "$HOPS_FILE" 2>/dev/null)"; [ -n "$HOPS" ] || HOPS=0
# SP_HOP is the successor's hop number; defined early because the Task-5 launch
# composition references it in the runtime fallback chain.
SP_HOP=$((HOPS + 1))
if [ "$HOPS" -ge "$MAX_HOPS" ]; then
  cmux notify --title "SDD handoff" --body "Hop limit $MAX_HOPS reached — manual resume needed" 2>/dev/null || true
  echo "[spawn-handoff] hop limit reached ($HOPS/$MAX_HOPS) — manual fallback." >&2
  print_manual_instructions
  exit 3
fi
# (Task 3 inserts the quota check here.)
# (Tasks 4-5 insert launch composition here.)
# (Task 6 inserts the spawn sequence + exit here.)
echo "[spawn-handoff] basic preconditions passed (skeleton — later tasks complete the flow)" >&2
exit 0
