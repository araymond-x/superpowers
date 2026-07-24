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
# Percent threshold; may legitimately be fractional (e.g. 12.5). Validated because
# it is interpolated into an awk program below — an unvalidated value is code
# injection. Invalid input warns and reverts to the default (never exits: the
# quota check's contract is fail-open).
QUOTA_MIN_PCT_DEFAULT=15
QUOTA_MIN_PCT="${SUPERPOWERS_CMUX_QUOTA_MIN_PCT:-$QUOTA_MIN_PCT_DEFAULT}"
if ! [[ "$QUOTA_MIN_PCT" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
  echo "WARNING: invalid SUPERPOWERS_CMUX_QUOTA_MIN_PCT ($QUOTA_MIN_PCT) — reverting to default $QUOTA_MIN_PCT_DEFAULT." >&2
  QUOTA_MIN_PCT="$QUOTA_MIN_PCT_DEFAULT"
fi
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
# --- Precondition 5: quota (fail-open; parameters pinned in spec §5.3) ------
# Tool resolution: an explicit SUPERPOWERS_CMUX_QUOTA_TOOL override is
# authoritative — a bad override classifies `unchecked`, it never silently falls
# back. Only the pinned default is allowed a PATH lookup, for installs where
# ~/.claude/bin is absent (it is not on PATH by default).
QUOTA_TOOL="${SUPERPOWERS_CMUX_QUOTA_TOOL:-$QUOTA_TOOL_DEFAULT}"
if [ -z "$SUPERPOWERS_CMUX_QUOTA_TOOL" ] && [ ! -x "$QUOTA_TOOL" ]; then
  QUOTA_TOOL="$(command -v claude-usage-pace 2>/dev/null)"
fi
# Watchdog bound passed to `sleep`. Integer-only: POSIX `sleep` guarantees only
# an integer operand, and a coarse watchdog has no use for sub-second precision.
# Unvalidated, a typo made `sleep` fail instantly — the watcher killed the tool
# immediately and the quota gate went permanently inert with no diagnostic.
QUOTA_TIMEOUT_DEFAULT=60
QUOTA_TIMEOUT="${SUPERPOWERS_CMUX_QUOTA_TIMEOUT:-$QUOTA_TIMEOUT_DEFAULT}"
if ! [[ "$QUOTA_TIMEOUT" =~ ^[0-9]+$ ]]; then
  echo "WARNING: invalid SUPERPOWERS_CMUX_QUOTA_TIMEOUT ($QUOTA_TIMEOUT) — reverting to default $QUOTA_TIMEOUT_DEFAULT." >&2
  QUOTA_TIMEOUT="$QUOTA_TIMEOUT_DEFAULT"
fi
QUOTA_STATUS="unchecked"
check_quota() {
  # Emits ok:<pct> | low:<pct> | unchecked  (never fails the caller).
  if [ ! -x "$QUOTA_TOOL" ]; then echo "unchecked"; return 0; fi
  local out rc pct tmpf pid watcher
  # macOS has no `timeout`, so bound the tool with a background watcher. Capture
  # through a temp FILE, not a pipe: the watcher's `sleep` (and any child the
  # tool forks) inherits a command-substitution pipe and holds it open, stalling
  # the read for the full timeout even on the success path.
  tmpf="$(mktemp)" || { echo "unchecked"; return 0; }
  "$QUOTA_TOOL" --json --no-log >"$tmpf" 2>/dev/null & pid=$!
  ( sleep "$QUOTA_TIMEOUT"; kill -9 $pid 2>/dev/null ) >/dev/null 2>&1 & watcher=$!
  wait $pid; rc=$?
  kill $watcher 2>/dev/null
  out="$(cat "$tmpf" 2>/dev/null)"; rm -f "$tmpf"
  if [ $rc -ne 0 ]; then echo "unchecked"; return 0; fi
  # $out is passed as sys.argv[1], never interpolated into the program text.
  pct="$("$PYTHON" - "$out" <<'PY' 2>/dev/null
import json,sys
try:
    d=json.loads(sys.argv[1])
    w=[x for x in d.get("windows",[]) if x.get("key")=="session"]
    print(float(w[0]["remaining_pct"]))
except Exception:
    sys.exit(1)
PY
)"
  if [ -z "$pct" ]; then echo "unchecked"; return 0; fi
  if awk "BEGIN{exit !($pct < $QUOTA_MIN_PCT)}"; then echo "low:$pct"; else echo "ok:$pct"; fi
}
QCLASS="$(check_quota)"
case "$QCLASS" in
  low:*)
    QUOTA_STATUS="$QCLASS"
    cmux notify --title "SDD handoff" --body "Session quota ${QCLASS#low:}% < ${QUOTA_MIN_PCT}% — manual resume" 2>/dev/null || true
    echo "[spawn-handoff] quota=$QCLASS below threshold — manual fallback." >&2
    print_manual_instructions
    exit 3 ;;
  ok:*) QUOTA_STATUS="$QCLASS"; echo "[spawn-handoff] quota=$QCLASS" >&2 ;;
  *)    QUOTA_STATUS="unchecked"; echo "[spawn-handoff] quota=unchecked (fail-open)" >&2 ;;
esac
# --- Launch composition A: decode metadata, label, telemetry ---------------
VERSIONS_DIR="$HOME/.local/share/claude/versions"

# ARGS decodability flag (a non-v1 / corrupt value => metadata unusable).
ARGS_OK=1
if [ -n "${CLAUDE_CODE_PICKER_ARGS:-}" ]; then
  case "${CLAUDE_CODE_PICKER_ARGS}" in v1:*) : ;; *) ARGS_OK=0 ;; esac
fi

# Decode forwarded argv (v1 codec, NO eval) + rematerialize the append-prompt.
# Absent ARGS => empty argv (ARGS_OK stays 1). Corrupt v1 body OR failed
# rematerialization => ARGS_OK=0 (degrade to picker-manual); never a silent
# arg-drop on auto. CLAUDE_CODE_PICKER_APPEND_PROMPT (base64 of the append-prompt
# CONTENTS) is the designed remedy for a dead append path (temp gone for an
# ABSOLUTE menu path, or a CWD-relative passthrough path). Prefer content: decode
# to a stable absolute file OUTSIDE any repo and SUBSTITUTE it into the forwarded
# --append-system-prompt-file value. Empty-but-flag-present => keep the path.
# Each element is NUL-*terminated* so `read -d ''` keeps the last.
FORWARDED=()
APPEND_TARGET_DIR="$HOME/.claude-codex-handoff/append-prompts"
APPEND_TARGET="$APPEND_TARGET_DIR/${BUNDLE_ID}-hop${SP_HOP}.md"
if [ "$ARGS_OK" = "1" ] && [ -n "${CLAUDE_CODE_PICKER_ARGS:-}" ]; then
  DECODE_TMP="$(mktemp)"
  APPEND_TARGET="$APPEND_TARGET" SPAWN_DRY_RUN="$DRY_RUN" "$PYTHON" - "$DECODE_TMP" <<'PY'
import base64, json, os, sys
out = sys.argv[1]
raw = os.environ.get("CLAUDE_CODE_PICKER_ARGS", "")   # read from env (no ARG_MAX limit)
try:
    argv = json.loads(base64.b64decode(raw[3:]).decode())
    assert isinstance(argv, list) and all(isinstance(x, str) for x in argv)
except Exception:
    sys.exit(3)                       # decode failure -> caller sets ARGS_OK=0
if argv and argv[-1].startswith("/pickup"):
    argv = argv[:-1]                  # hop-recursion strip guard
ap_b64 = os.environ.get("CLAUDE_CODE_PICKER_APPEND_PROMPT", "")
if ap_b64:                            # prefer content: rematerialize + substitute
    target = os.environ["APPEND_TARGET"]
    if os.environ.get("SPAWN_DRY_RUN") != "1":
        try:
            # Create the dir HERE, beside the write it exists for — not in the
            # shell gated on ARGS-being-present. That gating made an empty
            # append-prompts/ on every non-dry-run auto spawn, and when the path
            # already existed as a FILE it leaked a raw `mkdir: … File exists`
            # to stderr and carried on. Failure now routes to the same exit 4
            # (=> ARGS_OK=0 => degrade to picker-manual) as a failed write.
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "wb") as f:
                f.write(base64.b64decode(ap_b64))
        except Exception:
            sys.exit(4)               # rematerialization failed -> ARGS_OK=0
    i = 0                             # substitute both `--flag value` and `--flag=value`
    while i < len(argv):
        if argv[i] == "--append-system-prompt-file" and i + 1 < len(argv):
            argv[i+1] = target; i += 2; continue
        if argv[i].startswith("--append-system-prompt-file="):
            argv[i] = "--append-system-prompt-file=" + target
        i += 1
with open(out, "wb") as f:
    f.write(b"".join(x.encode() + b"\0" for x in argv))   # each element NUL-terminated
PY
  if [ $? -ne 0 ]; then
    ARGS_OK=0                         # corrupt body or rematerialization failure
  else
    while IFS= read -r -d '' tok; do FORWARDED+=("$tok"); done < "$DECODE_TMP"
  fi
  rm -f "$DECODE_TMP"
fi

# Label rule (spec §5.4b). Empty result => omit --session-label.
LABEL="$("$PYTHON" - "${CLAUDE_CODE_PICKER_LABEL:-}" <<'PY'
import re, sys
raw = sys.argv[1]
m = re.search(r"-Session-(\d+)$", raw)
if m:
    n = int(m.group(1)) + 1; base = raw[:m.start()]
else:
    n = 2; base = raw
base = re.sub(r"[^A-Za-z0-9_.-]", "", base)
if not base:
    print(""); sys.exit(0)
suffix = "-Session-%d" % n
print(base[:255 - len(suffix)] + suffix)
PY
)"

# Telemetry resolution.
if [ "${CLAUDE_CODE_ENABLE_TELEMETRY:-}" = "1" ]; then TELEMETRY="on"; else TELEMETRY="off"; fi

echo "[spawn-handoff] forwarded=${FORWARDED[*]} label=[$LABEL] telemetry=$TELEMETRY" >&2

# --- Launch composition B: auto preflight + successor command ---------------
# Auto-mode preflight (spec §5.4c). launch=auto only when ALL hold; any failure
# degrades to the attended interactive picker rather than a mismatched session.
LAUNCH_MODE="picker-manual"
preflight_ok() {
  [ -n "${CLAUDE_CODE_PICKER_VERSION:-}" ] || return 1
  [ "$ARGS_OK" = "1" ] || return 1
  # Match the picker's own version discovery predicate (`find -type f -perm -u+x`),
  # not a lenient `-e` — otherwise preflight can pass a version the picker rejects.
  { [ -f "$VERSIONS_DIR/${CLAUDE_CODE_PICKER_VERSION}" ] && [ -x "$VERSIONS_DIR/${CLAUDE_CODE_PICKER_VERSION}" ]; } || return 1
  command -v claude-picker >/dev/null 2>&1 || return 1
  # String equality, not >=: a future v2 picker must degrade, never pass.
  [ "$(claude-picker --handoff-contract 2>/dev/null)" = "$PICKER_CONTRACT" ] || return 1
  return 0
}
if preflight_ok; then LAUNCH_MODE="auto"; fi

# Compose the successor --command with shlex-style re-quoting of EVERY element
# (a shell re-parses this string inside the spawned workspace).
shq() { "$PYTHON" -c 'import shlex,sys;print(shlex.quote(sys.argv[1]))' "$1"; }
build_successor_cmd() {
  local parts=("claude-picker" "--non-interactive"
               "--pick-version" "$(shq "${CLAUDE_CODE_PICKER_VERSION:-}")"
               "--telemetry" "$TELEMETRY")
  # Empty label => omit --session-label entirely (spec §5.4b). Spelled `if/fi`
  # rather than `[ -n … ] && …`: as the function's last statement the `&&` form
  # would make an empty label look like a compose FAILURE (return 1).
  if [ -n "$LABEL" ]; then parts+=("--session-label" "$(shq "$LABEL")"); fi
  local a; for a in "${FORWARDED[@]}"; do parts+=("$(shq "$a")"); done
  parts+=("$PICKUP_ARG")
  # `printf`, not `echo`: with BASHOPTS=xpg_echo set in the environment, bash 5's
  # `echo` interprets backslash escapes — a forwarded arg containing \t/\n/\\ would
  # be mangled and a \c would truncate the command mid-string.
  printf '%s\n' "${parts[*]}"
}
# Quoted once, used on both branches and in the fallback tail (SSOT + 2 fewer
# Python spawns).
PICKUP_ARG="$(shq "/pickup $BUNDLE_ID")"
# One spawn id per invocation, generated HERE — before composition — because the
# composed fallback tail is the FOURTH record carrying it (intent, success
# outcome, spawn-failed outcome, and the child's runtime-picker-failure line).
# Generating it later, in the spawn sequence, would leave the composed tail with
# no id to interpolate; generating a second one there would break the very
# correlation §5.4d's id exists for. Cheap and side-effect-free, so --dry-run
# computes one too and still writes nothing.
SPAWN_ID="$("$PYTHON" -c 'import uuid;print(uuid.uuid4())')"
# $SP_HOP and $SPAWN_ID expand at compose time so the workspace's runtime
# fallback logs the concrete hop number and the parent's spawn id; the
# date/printf defer to runtime inside the workspace. Both are interpolated
# double-quoted (not via shq) to match: uuid4 and an integer are both within the
# shell-safe charset by construction, and the literal quotes keep the record's
# field structure obvious in the composed string.
# Worked example — verbatim output of a real run (LABEL=Proj-Session-2, args
# ["--append-system-prompt-file","/tmp/a b.md"]), line-wrapped here, with only the
# absolute log path replaced by <log>. The uuid differs per invocation; every
# other character is as emitted:
#   claude-picker --non-interactive --pick-version 2.1.218 --telemetry on \
#     --session-label Proj-Session-3 --append-system-prompt-file '/tmp/a b.md' '/pickup b1' \
#     || { printf '%s %s runtime-picker-failure hop=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "7b3933fe-0f5d-42f5-8495-9729b0ccff00" "1" >> <log>; claude-picker '/pickup b1'; }
if [ "$LAUNCH_MODE" = "auto" ]; then
  PICKER_CMD="$(build_successor_cmd)"
  SUCCESSOR_CMD="$PICKER_CMD || { printf '%s %s runtime-picker-failure hop=%s\n' \"\$(date -u +%Y-%m-%dT%H:%M:%SZ)\" \"$SPAWN_ID\" \"$SP_HOP\" >> $(shq "$SPAWN_LOG"); claude-picker $PICKUP_ARG; }"
else
  SUCCESSOR_CMD="claude-picker $PICKUP_ARG"
fi
echo "[spawn-handoff] launch=$LAUNCH_MODE" >&2
echo "[spawn-handoff] successor command: $SUCCESSOR_CMD" >&2

# --- Generic, extraction-ready workspace-spawn core (Decision 15) ----------
# spawn_claude_workspace CWD LAUNCH_COMMAND WORKSPACE_NAME NOTIFY_TEXT
# Pure mechanics (no SDD policy). Returns cmux new-workspace's exit code.
# cmux's own stdout/stderr is deliberately NOT captured: `cmux new-workspace`
# has no --json and documents no return value, so there is nothing to parse and
# a command substitution would only swallow its diagnostics.
spawn_claude_workspace() {
  local cwd="$1" launch_cmd="$2" ws_name="$3" notify_text="$4"
  cmux new-workspace --name "$ws_name" --cwd "$cwd" --command "$launch_cmd" --focus false
  local rc=$?
  if [ $rc -eq 0 ]; then
    cmux notify --title "SDD handoff" --body "$notify_text" 2>/dev/null || \
      echo "[spawn-handoff] warn: notify failed (successor already spawned)" >&2
  fi
  return $rc
}

# --- Dry-run short-circuit: preconditions + preflight done, spawn nothing ---
if [ "$DRY_RUN" = "1" ]; then
  echo "[spawn-handoff] --dry-run: would spawn workspace 'SDD resume: $FEATURE_NAME'" >&2
  echo "[spawn-handoff] --dry-run: quota=$QUOTA_STATUS launch=$LAUNCH_MODE (no hop increment, no spawn)" >&2
  exit 0
fi

# --- Spawn sequence (Decision 21 — reserve BEFORE spawn) -------------------
# Ordering is the whole point: a spawn that succeeds but whose bookkeeping fails
# must never look retryable, so the hop is consumed and the intent recorded
# BEFORE the workspace exists. Over-counting a hop is cheap; a double-spawn is
# a runaway chain. $SPAWN_ID is the id composed into the successor command above
# — do NOT regenerate it here, or the child's runtime-failure record stops
# correlating with this hop's intent record.
mkdir -p "$REPORTS_DIR"
# 1. Reserve (SP_HOP computed in Task 2 after the hop-limit check).
printf '%s\n' "$SP_HOP" > "$HOPS_FILE"
printf '%s %s intent hop=%s\n' "$(now_iso)" "$SPAWN_ID" "$SP_HOP" >> "$SPAWN_LOG"
# 2. Spawn.
if spawn_claude_workspace "$WORKTREE_ROOT" "$SUCCESSOR_CMD" "SDD resume: $FEATURE_NAME" \
     "Hop $SP_HOP/$MAX_HOPS — successor spawned"; then
  # 3. Outcome. §5.4d names a "workspace ref" here; cmux does not return one
  # (no --json on new-workspace, no documented output), so the field degrades to
  # the constant `(spawned)`. Post-spawn failures are non-retryable by contract —
  # notify already warns rather than failing, and this exits 0 regardless.
  printf '%s %s outcome hop=%s workspace=%s launch=%s bundle=%s quota=%s\n' \
    "$(now_iso)" "$SPAWN_ID" "$SP_HOP" "(spawned)" "$LAUNCH_MODE" "$BUNDLE_ID" "$QUOTA_STATUS" >> "$SPAWN_LOG"
  echo "[spawn-handoff] spawned successor (launch=$LAUNCH_MODE). STOP this session."
  exit 0
else
  printf '%s %s outcome hop=%s workspace=%s launch=%s bundle=%s quota=%s\n' \
    "$(now_iso)" "$SPAWN_ID" "$SP_HOP" "spawn-failed" "$LAUNCH_MODE" "$BUNDLE_ID" "$QUOTA_STATUS" >> "$SPAWN_LOG"
  cmux notify --title "SDD handoff" --body "Spawn failed after reservation — manual resume" 2>/dev/null || true
  echo "[spawn-handoff] cmux new-workspace failed AFTER reservation (hop $SP_HOP consumed) — manual fallback." >&2
  print_manual_instructions
  exit 3
fi
