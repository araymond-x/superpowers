"""Harness for spawn-handoff-session.sh subprocess tests."""

import base64
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = (
    ROOT
    / "skills"
    / "subagent-driven-development"
    / "scripts"
    / "spawn-handoff-session.sh"
)
FIX = Path(__file__).parent / "fixtures" / "spawn-handoff"

PACE_OK = 'echo "{\\"windows\\":[{\\"key\\":\\"session\\",\\"remaining_pct\\":63.0}]}"'
PACE_LOW = 'echo "{\\"windows\\":[{\\"key\\":\\"session\\",\\"remaining_pct\\":8.0}]}"'
PACE_MALFORMED = 'echo "not json {{{"'
PACE_MISSING_FIELD = 'echo "{\\"windows\\":[{\\"key\\":\\"session\\"}]}"'
PACE_MISSING_WINDOW = (
    'echo "{\\"windows\\":[{\\"key\\":\\"week_all\\",\\"remaining_pct\\":50.0}]}"'
)
PACE_NONZERO = "exit 7"


# run_spawn copies os.environ, so a developer's ambient SUPERPOWERS_CMUX_* knobs
# would skew every derived-ceiling / stall assertion. Empty string neutralizes
# BOTH consumers: `${VAR:-default}` treats empty as unset, and the ceiling
# derivation's `[ -n "$VAR" ]` is false on empty. Merge into env_extra.
NO_AMBIENT_HOP_KNOBS = {
    "SUPERPOWERS_CMUX_MAX_HOPS": "",
    "SUPERPOWERS_CMUX_MAX_STALL_HOPS": "",
}


def write_manifest(
    ctx,
    expected_hops=2,
    spawn_policy="auto",
    total_tasks=5,
    tier="standard",
    task_range=(0, 4),
    omit_handoff=False,
):
    """Minimal .sdd-session.json in the feature dir. omit_handoff=True builds a
    pre-v2 manifest (no handoff block) for derivation-path tests. Defaults emit a
    COMPLETE block: deferred order B4 pins handoff as all-or-nothing, so a partial
    block is model-invalid — omit_handoff is the only sanctioned way to have none."""
    import json as _json

    m = {"tier": tier, "total_tasks": total_tasks, "task_range": list(task_range)}
    if not omit_handoff:
        m["handoff"] = {"expected_hops": expected_hops, "spawn_policy": spawn_policy}
    (ctx["wt"] / ctx["feat"] / ".sdd-session.json").write_text(_json.dumps(m))


def write_done_report(ctx, task_id, status="DONE"):
    body = (
        f"---\nschema_version: 1\ntask_id: {task_id}\nstatus: {status}\n"
        "files_changed: [{path: x, description: y}]\n"
        "tests: {written: 1, passing: 1, command: x, result: PASS}\n---\nbody\n"
    )
    (ctx["reports"] / f"task-{task_id:03d}-implementer-report.md").write_text(body)


def append_outcome(ctx, hop, tasks_done, extra=""):
    line = (
        f"2026-07-30T00:00:0{hop}Z uuid-{hop} outcome hop={hop} workspace=w surface=s "
        f"launch=auto bundle=b quota=ok tasks_done={tasks_done} handshake=ok{extra}\n"
    )
    with open(ctx["reports"] / "handoff-spawn.log", "a") as f:
        f.write(line)


def _commit(ctx, msg="fixture state"):
    subprocess.run(["git", "add", "-A"], cwd=ctx["wt"], check=True)  # fixture repo only
    subprocess.run(["git", "commit", "-qm", msg], cwd=ctx["wt"], check=True)


def _spawn_log_text_or_empty(ctx):
    p = ctx["reports"] / "handoff-spawn.log"
    return p.read_text() if p.exists() else ""


# ── v2 topology: spawn-verb vocabulary + the cmux stub ────────────────────────
#
# SPAWN_VERBS is the SINGLE place the spawn vocabulary is written down. Both
# test_spawn_handoff.py and test_spawn_handoff_hardening.py consume
# `did_not_spawn` rather than re-spelling the list — a second copy is the drift
# shape deviations.md:127 already caught once this sprint (two SpawnPolicy
# Literals). `new-workspace` is RETAINED although the script no longer emits it:
# an old stub, or a partial revert, must never read as "did not spawn".
SPAWN_VERBS = ("new-surface", "workspace create", "new-workspace")


def did_not_spawn(log_text):
    """True when the recorded cmux log ATTEMPTED no spawn verb at all.

    The predicate's meaning is deliberately "did not ATTEMPT a spawn verb",
    not "did not succeed": a guard that refuses only after a failed spawn is
    still a guard that spawned. Before Task 9 this was `"new-workspace" not in
    log`, which the surface-topology switch turned fail-OPEN — True even on a
    real spawn — silently voiding seven refusal assertions.
    """
    return not any(verb in log_text for verb in SPAWN_VERBS)


def cmux_log_text(tmp_path):
    p = tmp_path / "cmux.log"
    return p.read_text() if p.exists() else ""


# Env knobs the body below honours (all optional, all "unset means normal"):
#   CMUX_PING_FAIL        ping answers NOPE / exit 1
#   CMUX_NEW_SURFACE_RC   `new-surface` exits with this rc, printing nothing
#   CMUX_WS_CREATE_RC     `workspace create` exits with this rc
#   CMUX_SEND_RC          every `send` exits with this rc
#   CMUX_SEND_FAIL_COUNT  the first N `send` calls fail (rc 1), later ones succeed
#   CMUX_RENAME_RC        `rename-tab` exits with this rc
#   CMUX_NOTIFY_RC        `notify` exits with this rc
#   CMUX_WAITFOR_RC       `wait-for` exit code (default 0 = token received)
#   CMUX_SCREEN_FILE      `read-screen` cats this file instead of erroring
#   CMUX_LIST_SURFACES_NO_REF   `list-pane-surfaces` emits a row carrying NO
#                         `surface:N` token, so the awk parser resolves nothing.
#                         The ONLY way to reach `create_workspace_target`'s
#                         ref-shape gate: under every other shape this stub can
#                         emit, the parser yields `^surface:[0-9]+$` or the verb
#                         is never reached, so the gate is redundant with the
#                         parser and no assertion can distinguish it from
#                         `if true`. A row rather than empty output, so the test
#                         proves the parser SKIPPED a non-matching token.
#   CMUX_LIST_SURFACES_TWO_ROWS   two surface rows with `[selected]` on the
#                         SECOND. On the default one-row shape the first row IS
#                         the selected row, so `first == selected` and the
#                         `[selected]` branch is indistinguishable from `if(0)`
#                         — the same mutual masking Task 0's review caught at the
#                         fixture level, recurring at the script level.
#
# Both knobs are guarded BEFORE the default `printf`, so the default output is
# byte-identical when neither is set.
#
# The `list-pane-surfaces` row carries the `* ` selected-row marker and the
# two-space non-selected indent measured in cmux-verb-shapes.json's
# `selected_row_marker`. A marker-less stub is exactly what made the old `$1`
# parser look green while failing 100% in production — do not drop the marker.
# The title carries BOTH a space and a colon so field-position parsing cannot
# pass by luck.
_CMUX_V2_STUB = r"""
if [ "$1" = "ping" ]; then
  [ -n "$CMUX_PING_FAIL" ] && { echo NOPE; exit 1; }
  echo PONG; exit 0
fi
printf '%s\n' "$@" >> "$CMUX_LOG.$1.argv"
echo "$@" >> "$CMUX_LOG"
__EXTRA__
case "$1" in
  new-surface)   [ -n "$CMUX_NEW_SURFACE_RC" ] && exit "$CMUX_NEW_SURFACE_RC"
                 echo "OK surface:7 pane:2 workspace:5"; exit 0 ;;
  rename-tab)    [ -n "$CMUX_RENAME_RC" ] && exit "$CMUX_RENAME_RC"
                 echo "OK action=rename tab=tab:77 workspace=workspace:29"; exit 0 ;;
  send)          if [ -n "$CMUX_SEND_FAIL_COUNT" ]; then
                   _n=0; [ -f "$CMUX_LOG.sendcount" ] && _n="$(cat "$CMUX_LOG.sendcount")"
                   _n=$((_n + 1)); echo "$_n" > "$CMUX_LOG.sendcount"
                   [ "$_n" -le "$CMUX_SEND_FAIL_COUNT" ] && exit 1
                 fi
                 [ -n "$CMUX_SEND_RC" ] && exit "$CMUX_SEND_RC"
                 echo "OK surface:7 workspace:5"; exit 0 ;;
  send-key)      echo "OK surface:7 workspace:5"; exit 0 ;;
  wait-for)      exit "${CMUX_WAITFOR_RC:-0}" ;;
  read-screen)   [ -n "$CMUX_SCREEN_FILE" ] && { cat "$CMUX_SCREEN_FILE"; exit 0; }
                 echo "internal_error: Failed to read terminal text" >&2; exit 1 ;;
  notify)        [ -n "$CMUX_NOTIFY_RC" ] && exit "$CMUX_NOTIFY_RC"
                 echo OK; exit 0 ;;
  workspace)     [ "$2" = "create" ] || { echo OK; exit 0; }
                 [ -n "$CMUX_WS_CREATE_RC" ] && exit "$CMUX_WS_CREATE_RC"
                 echo "OK workspace:9"; exit 0 ;;
  list-pane-surfaces)
                 [ -n "$CMUX_LIST_SURFACES_NO_REF" ] && { printf '* pane:3  SDD resume: demo  [selected]\n'; exit 0; }
                 [ -n "$CMUX_LIST_SURFACES_TWO_ROWS" ] && {
                   printf '  surface:10  Other: window  \n* surface:11  SDD resume: demo  [selected]\n'; exit 0; }
                 printf '* surface:11  SDD resume: demo  [selected]\n'; exit 0 ;;
  *) echo OK; exit 0 ;;
esac
"""


def cmux_v2_stub(extra=""):
    """Body for a v2-topology `cmux` stub.

    `extra` is injected AFTER the argv recording and BEFORE the verb dispatch,
    so a test needing to observe state at a particular verb (e.g. the
    reservation-ordering probe) injects a snippet instead of forking a second
    stub body that would then drift from this one.
    """
    return _CMUX_V2_STUB.replace("__EXTRA__", extra)


def encode_args(argv):
    return "v1:" + base64.b64encode(json.dumps(argv).encode()).decode()


def make_stub(dirpath, name, body):
    p = dirpath / name
    p.write_text("#!/usr/bin/env bash\n" + body + "\n")
    os.chmod(p, 0o755)


def setup_worktree(tmp_path):
    """Clean git worktree with .active-feature + reports dir. Returns context dict."""
    wt = tmp_path / "wt"
    wt.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=wt, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=wt, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=wt, check=True)
    feat = "docs/imp-plans/feat"
    (wt / feat / "reports").mkdir(parents=True)
    (wt / ".active-feature").write_text(feat + "\n")
    (wt / "seed").write_text("x")
    subprocess.run(["git", "add", "-A"], cwd=wt, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=wt, check=True)
    common = subprocess.run(
        ["git", "rev-parse", "--git-common-dir"], cwd=wt, capture_output=True, text=True
    ).stdout.strip()
    repo_id = os.path.realpath(
        str(wt / common) if not os.path.isabs(common) else common
    )
    return {
        "wt": wt,
        "feat": feat,
        "reports": wt / feat / "reports",
        "repo_id": repo_id,
    }


def install_bundle(tmp_path, bundle_id, manifest_src, repo_id):
    bdir = tmp_path / "home" / ".claude-codex-handoff" / "bundles" / bundle_id
    bdir.mkdir(parents=True)
    m = json.loads((FIX / manifest_src).read_text())
    if m["project"]["repo_id"] == "__REPO_ID__":
        m["project"]["repo_id"] = repo_id
    (bdir / "manifest.json").write_text(json.dumps(m))
    return bdir


def install_version(tmp_path, version, executable=True):
    """Install a version binary the picker's discovery predicate would accept.

    The picker finds versions with `find -type f -perm -u+x`, so a REAL version is
    an executable regular file — hence the default. `executable=False` installs the
    file without the u+x bit, which is the only way to exercise the `-x` half of the
    script's preflight predicate independently of the `-f` half.
    """
    vdir = tmp_path / "home" / ".local" / "share" / "claude" / "versions"
    vdir.mkdir(parents=True, exist_ok=True)
    binf = vdir / version
    binf.write_text("#!/bin/sh\n")
    os.chmod(binf, 0o755 if executable else 0o644)


def _path_without(path, name):
    """`path` with every entry that provides `name` removed.

    Dropping the stub is not enough to make a tool absent: this developer's own
    machine has a real `claude-picker` on PATH (~/.local/bin), and run_spawn copies
    os.environ. Filtering by entry keeps git/awk/mktemp reachable while guaranteeing
    the tool genuinely cannot be resolved. Self-validating in both directions: if
    the filter missed a copy, the real picker answers the contract probe with `1`,
    preflight passes, and the picker-absent test fails loudly on launch=auto.
    """
    return os.pathsep.join(
        d
        for d in path.split(os.pathsep)
        if d and not os.path.exists(os.path.join(d, name))
    )


def run_spawn(
    ctx,
    tmp_path,
    *args,
    env_extra=None,
    in_cmux=True,
    pace_body=PACE_OK,
    picker_body=None,
    cmux_body=None,
    picker_stub=True,
):
    stubs = tmp_path / "stubs"
    stubs.mkdir(exist_ok=True)
    make_stub(
        stubs,
        "cmux",
        cmux_body
        or (
            'if [ "$1" = "ping" ]; then [ -n "$CMUX_PING_FAIL" ] && { echo NOPE; exit 1; }; echo PONG; exit 0; fi\n'
            'echo "$@" >> "$CMUX_LOG"; exit 0'
        ),
    )
    if picker_stub:
        make_stub(
            stubs,
            "claude-picker",
            picker_body
            or ('if [ "$1" = "--handoff-contract" ]; then echo 1; exit 0; fi\nexit 0'),
        )
    else:
        assert picker_body is None, "picker_body is meaningless with picker_stub=False"
    make_stub(stubs, "claude-usage-pace", pace_body)
    env = dict(os.environ)
    base_path = env["PATH"]
    if not picker_stub:
        base_path = _path_without(base_path, "claude-picker")
    env["PATH"] = f"{stubs}:{base_path}"
    env["HOME"] = str(tmp_path / "home")
    env["CMUX_LOG"] = str(tmp_path / "cmux.log")
    env["SUPERPOWERS_ROOT"] = str(ROOT)
    if in_cmux:
        env["CMUX_WORKSPACE_ID"] = "TEST-WS"
    else:
        env.pop("CMUX_WORKSPACE_ID", None)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        cwd=str(ctx["wt"]),
        capture_output=True,
        text=True,
        env=env,
    )
