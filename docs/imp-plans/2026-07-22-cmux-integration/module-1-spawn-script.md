# cmux Integration — Module 1: spawn-handoff-session.sh + unit suite

> **Parent plan:** `docs/imp-plans/2026-07-22-cmux-integration/plan.md`
> **Module:** 1 of 2
> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first — direct implementation bypasses review enforcement, quality gates, and hooks.

**Module Goal:** Deliver `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` — a layered, deterministic auto-spawn tool — with a complete pytest unit matrix (`tests/unit/test_spawn_handoff.py` + helper `tests/unit/spawn_handoff_helpers.py`) covering every case in spec §7. Built concern-by-concern via TDD; each task adds one function group to the single script.

**Source Contracts:** Repo-1 picker contract v1, repo-2 vendored-skill symlinks, live cmux CLI argv, handoff bundle manifest, `claude-usage-pace` quota schema. (Full text in the parent plan's Shared Contract Section.)

**Contract Constraints:** See the parent plan's Contract Constraints — all apply. Most load-bearing: `--handoff-contract` string-equals `1`; repo match is `realpath(git rev-parse --git-common-dir)`; ARGS decode without eval; quota fail-open; reservation before spawn; 255 label ceiling.

**Feature Archetype:** Extension (purely additive — new script + new tests).

## File Map

| File | Responsibility |
|------|----------------|
| `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` | The auto-spawn tool: generic `spawn_claude_workspace()` core + SDD policy shell |
| `tests/unit/spawn_handoff_helpers.py` | Test harness: PATH stubs, fake worktree/bundle, `run_spawn` driver (mirrors `sdd_test_helpers.py`) |
| `tests/unit/test_spawn_handoff.py` | Full unit matrix using the helper |
| `tests/unit/fixtures/spawn-handoff/*.json` | Valid + invalid bundle manifests |

## Write-Scope Partitioning

| Task | Owned Files (write) | Read-Only Files | Depends On |
|------|---------------------|-----------------|------------|
| Task 0 | `tests/unit/fixtures/spawn-handoff/*`, `tests/unit/spawn_handoff_helpers.py`, `tests/unit/test_spawn_handoff.py` (contract section) | live picker/cmux/bundle contracts | — |
| Task 1 | `spawn-handoff-session.sh`, `test_spawn_handoff.py` | fixtures, helper | Task 0 |
| Task 2 | `spawn-handoff-session.sh`, `test_spawn_handoff.py` | fixtures, helper | Task 1 |
| Task 3 | `spawn-handoff-session.sh`, `test_spawn_handoff.py` | fixtures, helper | Task 2 |
| Task 4 | `spawn-handoff-session.sh`, `test_spawn_handoff.py` | fixtures, helper | Task 3 |
| Task 5 | `spawn-handoff-session.sh`, `test_spawn_handoff.py` | fixtures, helper | Task 4 |
| Task 6 | `spawn-handoff-session.sh`, `test_spawn_handoff.py` | fixtures, helper | Task 5 |

Tasks 1–6 write the same script and are strictly serialized (never parallel).

## Acceptance Criteria

- [ ] `bash spawn-handoff-session.sh` with no bundle id exits 1 with a usage message.
- [ ] Preconditions fail-closed in order: missing `.active-feature`→1, dirty tree→1, bundle-validation failures→1, not-in-cmux/ping-fail→3, hop-limit→3.
- [ ] Quota: `low`→exit 3; all `unchecked` classes (absent/timeout/malformed/missing-field)→proceed; `ok`→proceed.
- [ ] `launch=auto` composes exact picker flags + decoded, re-quoted forwarded args + incremented label + embedded runtime-failure fallback chain; degraded metadata → `launch=picker-manual`.
- [ ] Reservation (`intent` line + hop increment) precedes `cmux new-workspace`; spawn failure leaves hop consumed + `outcome=spawn-failed` + exit 3.
- [ ] `--dry-run` evaluates preconditions + preflight, prints composed commands, spawns nothing, increments nothing.
- [ ] `pytest tests/unit/test_spawn_handoff.py -v` all green.

---

## Tasks

### Task 0: Contract verification + prerequisite assertions + test harness (BLOCKING)

**This task is the cross-repo dependency gate.** It (a) verifies repos 1+2 have landed, (b) freezes the cmux/picker/bundle contracts into fixtures, and (c) creates the shared test harness. If repos 1+2 are not real, this task **fails and blocks the module** — the intended behavior.

**Files:**
- Read (live): `claude-picker --handoff-contract`; `cmux --help` / `cmux new-workspace --help` / `cmux notify --help`; `~/.claude/skills/{cmux,cmux-workspace,cmux-markdown,cmux-diagnostics}`; an example `~/.claude-codex-handoff/bundles/<id>/manifest.json`
- Create: `tests/unit/fixtures/spawn-handoff/{valid,wrong-type,wrong-skill,foreign-repo}-manifest.json`
- Create: `tests/unit/spawn_handoff_helpers.py`
- Create: `tests/unit/test_spawn_handoff.py` (contract-assertion section only; grows in later tasks)

- [x] **Step 1: Assert prerequisites are live (repos 1+2 landed).**

Run each; all must pass. If any fails, STOP and report `DONE_WITH_CONCERNS` naming the missing prerequisite — do not fabricate fixtures around an absent contract.

```bash
test "$(claude-picker --handoff-contract)" = "1" || echo "BLOCKED: picker contract not landed"
for s in cmux cmux-workspace cmux-markdown cmux-diagnostics; do
  test -e "$HOME/.claude/skills/$s/SKILL.md" || echo "BLOCKED: skill $s symlink unresolved"
done
test "$(cmux ping 2>/dev/null)" = "PONG" && echo "cmux OK" || echo "note: not in a cmux workspace (fine for unit tests)"
```

- [x] **Step 2: Freeze the bundle contract into fixtures.**

Create `tests/unit/fixtures/spawn-handoff/valid-manifest.json` — a minimal valid `work`/SDD manifest. `__REPO_ID__` is a sentinel rewritten per-test to the test repo's real git-common-dir:

```json
{
  "schema_version": "1.1",
  "session": {
    "bundle_type": "work",
    "entry_skill": "superpowers:subagent-driven-development",
    "goal": "resume SDD",
    "status": "in_progress"
  },
  "project": { "repo_id": "__REPO_ID__", "repo_name": "fixture-repo" }
}
```

Create the three invalid variants by copying it and changing exactly one field:
- `wrong-type-manifest.json`: `session.bundle_type` = `"review"`.
- `wrong-skill-manifest.json`: `session.entry_skill` = `"superpowers:brainstorming"`.
- `foreign-repo-manifest.json`: `project.repo_id` = `"/some/other/repo/.git"` (never equals the test repo's git-common-dir).

- [x] **Step 3: Create the shared test harness.**

Create `tests/unit/spawn_handoff_helpers.py` — the single source of harness truth for every task (mirrors `sdd_test_helpers.py`). It exposes all `run_spawn` knobs upfront so later tasks never mutate the harness:

```python
"""Harness for spawn-handoff-session.sh subprocess tests."""
import base64
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "skills" / "subagent-driven-development" / "scripts" / "spawn-handoff-session.sh"
FIX = Path(__file__).parent / "fixtures" / "spawn-handoff"

PACE_OK = 'echo "{\\"windows\\":[{\\"key\\":\\"session\\",\\"remaining_pct\\":63.0}]}"'
PACE_LOW = 'echo "{\\"windows\\":[{\\"key\\":\\"session\\",\\"remaining_pct\\":8.0}]}"'
PACE_MALFORMED = 'echo "not json {{{"'
PACE_MISSING_FIELD = 'echo "{\\"windows\\":[{\\"key\\":\\"session\\"}]}"'
PACE_MISSING_WINDOW = 'echo "{\\"windows\\":[{\\"key\\":\\"week_all\\",\\"remaining_pct\\":50.0}]}"'
PACE_NONZERO = 'exit 7'


def encode_args(argv):
    return "v1:" + base64.b64encode(json.dumps(argv).encode()).decode()


def make_stub(dirpath, name, body):
    p = dirpath / name
    p.write_text("#!/usr/bin/env bash\n" + body + "\n")
    os.chmod(p, 0o755)


def setup_worktree(tmp_path):
    """Clean git worktree with .active-feature + reports dir. Returns context dict."""
    wt = tmp_path / "wt"; wt.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=wt, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=wt, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=wt, check=True)
    feat = "docs/imp-plans/feat"
    (wt / feat / "reports").mkdir(parents=True)
    (wt / ".active-feature").write_text(feat + "\n")
    (wt / "seed").write_text("x")
    subprocess.run(["git", "add", "-A"], cwd=wt, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=wt, check=True)
    common = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=wt,
                            capture_output=True, text=True).stdout.strip()
    repo_id = os.path.realpath(str(wt / common) if not os.path.isabs(common) else common)
    return {"wt": wt, "feat": feat, "reports": wt / feat / "reports", "repo_id": repo_id}


def install_bundle(tmp_path, bundle_id, manifest_src, repo_id):
    bdir = tmp_path / "home" / ".claude-codex-handoff" / "bundles" / bundle_id
    bdir.mkdir(parents=True)
    m = json.loads((FIX / manifest_src).read_text())
    if m["project"]["repo_id"] == "__REPO_ID__":
        m["project"]["repo_id"] = repo_id
    (bdir / "manifest.json").write_text(json.dumps(m))
    return bdir


def install_version(tmp_path, version):
    # Version MUST be an executable regular file (picker: `find -type f -perm -u+x`).
    vdir = tmp_path / "home" / ".local" / "share" / "claude" / "versions"
    vdir.mkdir(parents=True, exist_ok=True)
    binf = vdir / version
    binf.write_text("#!/bin/sh\n")
    os.chmod(binf, 0o755)


def run_spawn(ctx, tmp_path, *args, env_extra=None, in_cmux=True,
              pace_body=PACE_OK, picker_body=None, cmux_body=None):
    stubs = tmp_path / "stubs"; stubs.mkdir(exist_ok=True)
    make_stub(stubs, "cmux", cmux_body or (
        'if [ "$1" = "ping" ]; then [ -n "$CMUX_PING_FAIL" ] && { echo NOPE; exit 1; }; echo PONG; exit 0; fi\n'
        'echo "$@" >> "$CMUX_LOG"; exit 0'))
    make_stub(stubs, "claude-picker", picker_body or (
        'if [ "$1" = "--handoff-contract" ]; then echo 1; exit 0; fi\nexit 0'))
    make_stub(stubs, "claude-usage-pace", pace_body)
    env = dict(os.environ)
    env["PATH"] = f"{stubs}:{env['PATH']}"
    env["HOME"] = str(tmp_path / "home")
    env["CMUX_LOG"] = str(tmp_path / "cmux.log")
    env["SUPERPOWERS_ROOT"] = str(ROOT)
    if in_cmux:
        env["CMUX_WORKSPACE_ID"] = "TEST-WS"
    else:
        env.pop("CMUX_WORKSPACE_ID", None)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(["bash", str(SCRIPT), *args], cwd=str(ctx["wt"]),
                          capture_output=True, text=True, env=env)
```

- [x] **Step 4: Write the contract-fact test.**

Create `tests/unit/test_spawn_handoff.py`:

```python
"""Unit matrix for spawn-handoff-session.sh (SDD auto-spawn tool).

The bash script is driven via subprocess with stub `cmux`, `claude-picker`, and
`claude-usage-pace` on a per-test PATH (harness in spawn_handoff_helpers.py).
Pattern mirrors test_context_gate_tier.py.
"""
import json
from pathlib import Path

FIX = Path(__file__).parent / "fixtures" / "spawn-handoff"

# Contract facts frozen from live `cmux --help` (2026-07-22). If cmux renames a
# flag, the exact-argv assertions in later tasks must be updated too.
CMUX_NEW_WORKSPACE_FLAGS = ["--name", "--cwd", "--command", "--focus"]
CMUX_NOTIFY_FLAGS = ["--title", "--body"]
PICKER_CONTRACT_VERSION = "1"

# claude-picker exports FOUR forwarding vars on EVERY launch path (verified vs
# telemetry-exp launchers/claude-picker v1). The 4th (APPEND_PROMPT = base64 of
# the --append-system-prompt-file CONTENTS) is the designed remedy for a dead/temp
# append path and MUST be consumed (decode->rematerialize->substitute; Task 4).
# Telemetry-on = inherited CLAUDE_CODE_ENABLE_TELEMETRY=1 (via telemetry-vars.sh).
PICKER_EXPORTS = ["CLAUDE_CODE_PICKER_VERSION", "CLAUDE_CODE_PICKER_LABEL",
                  "CLAUDE_CODE_PICKER_ARGS", "CLAUDE_CODE_PICKER_APPEND_PROMPT"]


def test_fixtures_shape_matches_contract():
    valid = json.loads((FIX / "valid-manifest.json").read_text())
    assert valid["session"]["bundle_type"] == "work"
    assert valid["session"]["entry_skill"] == "superpowers:subagent-driven-development"
    assert "repo_id" in valid["project"]
    assert json.loads((FIX / "wrong-type-manifest.json").read_text())["session"]["bundle_type"] == "review"
    assert json.loads((FIX / "wrong-skill-manifest.json").read_text())["session"]["entry_skill"] != \
        "superpowers:subagent-driven-development"
    assert json.loads((FIX / "foreign-repo-manifest.json").read_text())["project"]["repo_id"] == "/some/other/repo/.git"
    assert "CLAUDE_CODE_PICKER_APPEND_PROMPT" in PICKER_EXPORTS  # 4th export is consumed (Task 4)
```

- [x] **Step 5: Verify plan snippets against source.**

Confirm the parent plan's cmux argv surface (`new-workspace --name/--cwd/--command/--focus`, `notify --title/--body`) and picker contract against the live sources: `claude-picker --handoff-contract`→`1`; the **four** exports in `_set_picker_env` (read `telemetry-exp/launchers/claude-picker` — `VERSION`, `LABEL`, `ARGS`, `APPEND_PROMPT`); the append-file exit-3 is `--non-interactive`-only; and `versions/<v>` is an executable file (`find -type f -perm -u+x`). Any difference → report `DONE_WITH_CONCERNS` (the launch-composition tasks depend on these).

**Also freeze the `--command` execution semantics** (the whole `launch=auto` design depends on it): confirm from `cmux new-workspace --help` that `--command <text>` means **"Send text+Enter to the new workspace after creation"** — i.e. the string is typed into the new workspace's *interactive shell* and executed, NOT exec'd directly by cmux. This is why the composed successor command may be a single-line compound (`<picker cmd> || { …; claude-picker …; }`) with quotes and `$(…)`: the workspace's shell re-parses it. Record in the Task 0 report that (a) `--command` is text+Enter into the workspace shell, and (b) that shell is the user's login shell (zsh here), so the composed command must be POSIX/zsh-safe (it is: `||`, `{ ;}`, `printf`, `$(…)`, and `shlex.quote`d args are all portable). If `--help` instead indicates cmux exec's the value directly without a shell, report `DONE_WITH_CONCERNS` — the compound-command fallback in Task 5 would not survive.

- [x] **Step 6: Run and verify.**

Run: `.venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -v`
Expected: `test_fixtures_shape_matches_contract` PASS. (Import assertions: N/A — no importable code constants; cmux flags are external CLI strings frozen as module constants, the picker contract is an integer probe.)

- [x] **Step 7: Commit.**

```bash
git add tests/unit/fixtures/spawn-handoff tests/unit/spawn_handoff_helpers.py tests/unit/test_spawn_handoff.py
git commit -m "test(cmux-int): contract fixtures + prerequisite assertions + harness (Task 0)"
```

---

### Task 1: Script foundation + basic-refusal preconditions

**Files:**
- Create: `skills/subagent-driven-development/scripts/spawn-handoff-session.sh`
- Modify: `tests/unit/test_spawn_handoff.py`
- Read: `tests/unit/spawn_handoff_helpers.py` (created in Task 0)

**Pattern References:** `sdd-pre-dispatch-hook.sh` (house bash style); `tests/unit/test_context_gate_tier.py` (subprocess+PATH-stub harness).

- [x] **Step 1: Write the failing basic-refusal tests.**

Append to `test_spawn_handoff.py`:

```python
import os
from spawn_handoff_helpers import setup_worktree, install_bundle, run_spawn, SCRIPT


def test_script_exists_and_executable():
    assert SCRIPT.exists() and os.access(SCRIPT, os.X_OK)


def test_no_bundle_id_exits_1(tmp_path):
    ctx = setup_worktree(tmp_path)
    r = run_spawn(ctx, tmp_path)
    assert r.returncode == 1 and "BUNDLE_ID" in (r.stdout + r.stderr)


def test_unknown_flag_exits_1(tmp_path):
    ctx = setup_worktree(tmp_path)
    r = run_spawn(ctx, tmp_path, "--bogus", "b1")
    assert r.returncode == 1


def test_missing_active_feature_exits_1(tmp_path):
    ctx = setup_worktree(tmp_path)
    (ctx["wt"] / ".active-feature").unlink()
    subprocess.run(["git", "commit", "-aqm", "rm af"], cwd=ctx["wt"], check=True)
    install_bundle(tmp_path, "b1", "valid-manifest.json", ctx["repo_id"])
    r = run_spawn(ctx, tmp_path, "b1")
    assert r.returncode == 1 and "active-feature" in (r.stdout + r.stderr)


def test_dirty_tree_exits_1(tmp_path):
    ctx = setup_worktree(tmp_path)
    install_bundle(tmp_path, "b1", "valid-manifest.json", ctx["repo_id"])
    (ctx["wt"] / "dirty").write_text("y")  # uncommitted
    r = run_spawn(ctx, tmp_path, "b1")
    assert r.returncode == 1 and "clean" in (r.stdout + r.stderr).lower()
```

(Add `import subprocess` to the test module's imports.) Run: `.venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -v` → new tests FAIL (script absent).

- [x] **Step 2: Write the script foundation.**

Create `skills/subagent-driven-development/scripts/spawn-handoff-session.sh`:

```bash
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
```

- [x] **Step 3: Run tests → pass.**

Run: `.venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -v`
Expected: all Task-0 + Task-1 tests PASS.

- [x] **Step 4: Commit.**

```bash
git add skills/subagent-driven-development/scripts/spawn-handoff-session.sh tests/unit/test_spawn_handoff.py
git commit -m "feat(cmux-int): spawn-handoff foundation + basic-refusal preconditions (Task 1)"
```

---

### Task 2: Bundle validation + cmux/hop preconditions

**Files:**
- Modify: `skills/subagent-driven-development/scripts/spawn-handoff-session.sh`
- Modify: `tests/unit/test_spawn_handoff.py`

- [x] **Step 1: Write the failing tests.**

Append to `test_spawn_handoff.py`:

```python
import pytest


@pytest.mark.parametrize("bundle_id,manifest,needle", [
    ("bad id!", "valid-manifest.json", "charset"),
    ("b1", "wrong-type-manifest.json", "bundle_type"),
    ("b1", "wrong-skill-manifest.json", "entry_skill"),
    ("b1", "foreign-repo-manifest.json", "repo"),
])
def test_bundle_validation_failures_exit_1(tmp_path, bundle_id, manifest, needle):
    ctx = setup_worktree(tmp_path)
    if bundle_id == "b1":
        install_bundle(tmp_path, "b1", manifest, ctx["repo_id"])
    r = run_spawn(ctx, tmp_path, bundle_id)
    assert r.returncode == 1 and needle in (r.stdout + r.stderr).lower()


def test_bundle_dir_missing_exits_1(tmp_path):
    ctx = setup_worktree(tmp_path)
    r = run_spawn(ctx, tmp_path, "does-not-exist")
    assert r.returncode == 1


def test_not_in_cmux_exits_3_with_instructions(tmp_path):
    ctx = setup_worktree(tmp_path)
    install_bundle(tmp_path, "b1", "valid-manifest.json", ctx["repo_id"])
    r = run_spawn(ctx, tmp_path, "b1", in_cmux=False)
    assert r.returncode == 3 and "/pickup b1" in (r.stdout + r.stderr)


def test_ping_failure_exits_3(tmp_path):
    ctx = setup_worktree(tmp_path)
    install_bundle(tmp_path, "b1", "valid-manifest.json", ctx["repo_id"])
    r = run_spawn(ctx, tmp_path, "b1", env_extra={"CMUX_PING_FAIL": "1"})
    assert r.returncode == 3


def test_hop_limit_exits_3(tmp_path):
    ctx = setup_worktree(tmp_path)
    install_bundle(tmp_path, "b1", "valid-manifest.json", ctx["repo_id"])
    (ctx["reports"] / ".handoff-hops").write_text("3\n")
    r = run_spawn(ctx, tmp_path, "b1")
    assert r.returncode == 3 and "hop" in (r.stdout + r.stderr).lower()
```

Run the suite → new tests FAIL (skeleton exits 0 after clean-tree).

- [x] **Step 2: Insert bundle validation + preconditions 2–4.**

Replace the `# (Task 2 inserts bundle validation + cmux + hop preconditions here.)` marker with:

```bash
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
```

- [x] **Step 3: Run tests → pass.**

Run: `.venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -v` → all Task-0/1/2 tests PASS.

- [x] **Step 4: Commit.**

```bash
git add skills/subagent-driven-development/scripts/spawn-handoff-session.sh tests/unit/test_spawn_handoff.py
git commit -m "feat(cmux-int): bundle validation + cmux/hop preconditions (Task 2)"
```

---

### Task 3: Quota check (session-window, fail-open)

**Files:**
- Modify: `skills/subagent-driven-development/scripts/spawn-handoff-session.sh`
- Modify: `tests/unit/test_spawn_handoff.py`

- [x] **Step 1: Write the failing quota tests.**

Append to `test_spawn_handoff.py`:

```python
from spawn_handoff_helpers import (PACE_OK, PACE_LOW, PACE_MALFORMED,
                                    PACE_MISSING_FIELD, PACE_MISSING_WINDOW, PACE_NONZERO)


def _spawnable(tmp_path, ctx):
    install_bundle(tmp_path, "b1", "valid-manifest.json", ctx["repo_id"])


def test_quota_low_exits_3(tmp_path):
    ctx = setup_worktree(tmp_path); _spawnable(tmp_path, ctx)
    r = run_spawn(ctx, tmp_path, "b1", pace_body=PACE_LOW)
    assert r.returncode == 3 and "quota" in (r.stdout + r.stderr).lower()


@pytest.mark.parametrize("pace_body", [
    PACE_MALFORMED, PACE_MISSING_FIELD, PACE_MISSING_WINDOW, PACE_NONZERO,
])
def test_quota_unchecked_classes_proceed(tmp_path, pace_body):
    ctx = setup_worktree(tmp_path); _spawnable(tmp_path, ctx)
    r = run_spawn(ctx, tmp_path, "b1", "--dry-run", pace_body=pace_body)
    assert r.returncode == 0 and "quota=unchecked" in (r.stdout + r.stderr)


def test_quota_tool_absent_proceeds(tmp_path):
    ctx = setup_worktree(tmp_path); _spawnable(tmp_path, ctx)
    r = run_spawn(ctx, tmp_path, "b1", "--dry-run",
                  env_extra={"SUPERPOWERS_CMUX_QUOTA_TOOL": str(tmp_path / "nope")})
    assert r.returncode == 0 and "quota=unchecked" in (r.stdout + r.stderr)


def test_quota_ok_proceeds(tmp_path):
    ctx = setup_worktree(tmp_path); _spawnable(tmp_path, ctx)
    r = run_spawn(ctx, tmp_path, "b1", "--dry-run", pace_body=PACE_OK)
    assert r.returncode == 0 and "quota=ok" in (r.stdout + r.stderr)
```

> **Timeout note:** the spec pins a 60s wrapper. macOS has no `timeout`; the script uses a background-process-kill pattern, wall-clock overridable via `SUPERPOWERS_CMUX_QUOTA_TIMEOUT` (default 60). Add that env var to the docs list in Task 9. Do not add a `sleep`-based timeout test that would hang CI.

Run → quota tests FAIL (skeleton exits 0 with no `quota=` string).

- [x] **Step 2: Insert the quota check.** _(shipped implementation diverges from the snippet below — see deviations.md; snippet correction owed)_

Replace the `# (Task 3 inserts the quota check here.)` marker with:

```bash
# --- Precondition 5: quota (fail-open; parameters pinned in spec §5.3) ------
QUOTA_TOOL="${SUPERPOWERS_CMUX_QUOTA_TOOL:-$QUOTA_TOOL_DEFAULT}"
QUOTA_TIMEOUT="${SUPERPOWERS_CMUX_QUOTA_TIMEOUT:-60}"
QUOTA_STATUS="unchecked"
check_quota() {
  # Emits ok:<pct> | low:<pct> | unchecked  (never fails the caller).
  if [ ! -x "$QUOTA_TOOL" ]; then echo "unchecked"; return 0; fi
  local out rc pct
  out="$("$QUOTA_TOOL" --json --no-log 2>/dev/null & pid=$!
         ( sleep "$QUOTA_TIMEOUT"; kill -9 $pid 2>/dev/null ) & watcher=$!
         wait $pid 2>/dev/null; rc=$?; kill $watcher 2>/dev/null; exit $rc)"
  rc=$?
  if [ $rc -ne 0 ]; then echo "unchecked"; return 0; fi
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
```

> **Note:** `$out` is passed to python as `sys.argv[1]` (not heredoc-interpolated) — no injection surface; any parse fault → `unchecked` (fail-open).

- [x] **Step 3: Run tests → pass.**

Run: `.venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -k quota -v` → all quota cases PASS.

- [x] **Step 4: Commit.**

```bash
git add skills/subagent-driven-development/scripts/spawn-handoff-session.sh tests/unit/test_spawn_handoff.py
git commit -m "feat(cmux-int): fail-open session-quota check (Task 3)"
```

_Completed: `7131698` (implementation) + `926ab60` (quality-review fix round)._

---

### Task 4: Launch composition A — metadata decode, strip guard, label rule, telemetry

**Files:**
- Modify: `skills/subagent-driven-development/scripts/spawn-handoff-session.sh`
- Modify: `tests/unit/test_spawn_handoff.py`

The block echoes intermediate values (`forwarded`, `label`, `telemetry`) to stderr so Task 4 can assert them before Task 5 adds the final command.

- [x] **Step 1: Write the failing decode/label/telemetry tests.**

Append to `test_spawn_handoff.py`:

```python
from spawn_handoff_helpers import encode_args, install_version


def _meta(version="2.1.218", args_b64=None, label="Proj-Session-2", telem="1", append_b64=None):
    e = {"CLAUDE_CODE_PICKER_VERSION": version}
    if args_b64 is not None: e["CLAUDE_CODE_PICKER_ARGS"] = args_b64
    if label is not None: e["CLAUDE_CODE_PICKER_LABEL"] = label
    if telem is not None: e["CLAUDE_CODE_ENABLE_TELEMETRY"] = telem
    if append_b64 is not None: e["CLAUDE_CODE_PICKER_APPEND_PROMPT"] = append_b64
    return e


def test_decoded_args_and_strip_guard(tmp_path):
    ctx = setup_worktree(tmp_path); _spawnable(tmp_path, ctx)
    install_version(tmp_path, "2.1.218")
    args = ["--append-system-prompt-file", "/tmp/a b.md", "/pickup old-bundle"]
    r = run_spawn(ctx, tmp_path, "b1", "--dry-run", env_extra=_meta(args_b64=encode_args(args)))
    out = r.stdout + r.stderr
    assert "forwarded=" in out
    assert "--append-system-prompt-file" in out and "a b.md" in out
    assert "/pickup old-bundle" not in out          # stale /pickup stripped


def test_telemetry_on_and_off(tmp_path):
    ctx = setup_worktree(tmp_path); _spawnable(tmp_path, ctx)
    install_version(tmp_path, "2.1.218")
    r_on = run_spawn(ctx, tmp_path, "b1", "--dry-run", env_extra=_meta(args_b64=encode_args([])))
    assert "telemetry=on" in (r_on.stdout + r_on.stderr)
    r_off = run_spawn(ctx, tmp_path, "b1", "--dry-run",
                      env_extra=_meta(args_b64=encode_args([]), telem=None))
    assert "telemetry=off" in (r_off.stdout + r_off.stderr)


@pytest.mark.parametrize("in_label,expect", [
    ("", ""),                       # empty stays empty
    ("Proj", "Proj-Session-2"),     # unsuffixed gains -Session-2
    ("Proj-Session-4", "Proj-Session-5"),
    ("!!!", ""),                    # empty-after-sanitize
])
def test_label_rule(tmp_path, in_label, expect):
    ctx = setup_worktree(tmp_path); _spawnable(tmp_path, ctx)
    install_version(tmp_path, "2.1.218")
    r = run_spawn(ctx, tmp_path, "b1", "--dry-run",
                  env_extra=_meta(args_b64=encode_args([]), label=in_label))
    assert f"label=[{expect}]" in (r.stdout + r.stderr)


def test_label_255_boundary(tmp_path):
    ctx = setup_worktree(tmp_path); _spawnable(tmp_path, ctx)
    install_version(tmp_path, "2.1.218")
    r = run_spawn(ctx, tmp_path, "b1", "--dry-run",
                  env_extra=_meta(args_b64=encode_args([]), label="A" * 300))
    import re
    m = re.search(r"label=\[([^\]]*)\]", r.stdout + r.stderr)
    assert m and len(m.group(1)) <= 255 and m.group(1).endswith("-Session-2")


@pytest.mark.parametrize("argv", [
    ["--append-system-prompt-file", "/tmp/gone-temp.md"],   # space form
    ["--append-system-prompt-file=/tmp/gone-temp.md"],      # =-joined form
])
def test_append_prompt_substituted_in_forwarded(tmp_path, argv):
    # APPEND_PROMPT content present -> dead path substituted with rematerialized path.
    import base64
    ctx = setup_worktree(tmp_path); _spawnable(tmp_path, ctx)
    install_version(tmp_path, "2.1.218")
    env = _meta(args_b64=encode_args(argv), append_b64=base64.b64encode(b"prompt body").decode())
    out = (lambda r: r.stdout + r.stderr)(run_spawn(ctx, tmp_path, "b1", "--dry-run", env_extra=env))
    assert "/tmp/gone-temp.md" not in out and "append-prompts/b1-hop1.md" in out


def test_append_prompt_empty_keeps_original_path(tmp_path):
    # Empty-but-flag-present (APPEND_PROMPT absent): cannot rematerialize -> keep path.
    ctx = setup_worktree(tmp_path); _spawnable(tmp_path, ctx)
    install_version(tmp_path, "2.1.218")
    env = _meta(args_b64=encode_args(["--append-system-prompt-file", "/tmp/orig.md"]))  # no APPEND_PROMPT
    r = run_spawn(ctx, tmp_path, "b1", "--dry-run", env_extra=env)
    assert "/tmp/orig.md" in (r.stdout + r.stderr)
```

Run → FAIL (no composition block yet).

- [x] **Step 2: Insert composition part A.**

Replace the `# (Tasks 4-5 insert launch composition here.)` marker with the decode/label/telemetry block (Task 5 appends after it):

```bash
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
  [ "$DRY_RUN" = "1" ] || mkdir -p "$APPEND_TARGET_DIR"
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
```

> **Bash version caveat:** confirm `env bash --version` is ≥ 4.x (Homebrew) on the target and note the requirement in Task 9 docs. The decode does the `/pickup` strip in python (no bash negative indexing), so the array ops here are append + `${FORWARDED[*]}` only — safe on bash 3.2 too.

- [x] **Step 3: Run tests → pass.**

Run: `.venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -k "decoded or telemetry or label" -v` → PASS.

- [x] **Step 4: Commit.**

```bash
git add skills/subagent-driven-development/scripts/spawn-handoff-session.sh tests/unit/test_spawn_handoff.py
git commit -m "feat(cmux-int): metadata decode, strip guard, label rule, telemetry (Task 4)"
```

_Completed: `77537bc`. Bash floor determined **≥ 3.2** (plan's "≥ 4.x" caveat above is wrong — see deviations.md)._

---

### Task 5: Launch composition B — auto preflight + compose-side quoting

**Files:**
- Modify: `skills/subagent-driven-development/scripts/spawn-handoff-session.sh`
- Modify: `tests/unit/test_spawn_handoff.py`

- [ ] **Step 1: Write the failing preflight/compose tests.**

Append to `test_spawn_handoff.py`:

```python
def test_auto_mode_composes_exact_command(tmp_path):
    ctx = setup_worktree(tmp_path); _spawnable(tmp_path, ctx)
    install_version(tmp_path, "2.1.218")
    args = ["--append-system-prompt-file", "/tmp/a b.md"]
    r = run_spawn(ctx, tmp_path, "b1", "--dry-run", env_extra=_meta(args_b64=encode_args(args)))
    out = r.stdout + r.stderr
    assert "launch=auto" in out
    for tok in ["claude-picker", "--non-interactive", "--pick-version 2.1.218",
                "--telemetry on", "--session-label", "/pickup b1"]:
        assert tok in out
    assert "a b.md" in out                    # compose-side quoting preserved the space
    assert "runtime-picker-failure" in out    # embedded residual fallback chain


@pytest.mark.parametrize("env_extra", [{}, {"CLAUDE_CODE_PICKER_VERSION": "9.9.9"}])
def test_picker_manual_when_metadata_degraded(tmp_path, env_extra):
    ctx = setup_worktree(tmp_path); _spawnable(tmp_path, ctx)
    r = run_spawn(ctx, tmp_path, "b1", "--dry-run", env_extra=env_extra)
    assert "launch=picker-manual" in (r.stdout + r.stderr)


def test_picker_manual_when_contract_wrong(tmp_path):
    ctx = setup_worktree(tmp_path); _spawnable(tmp_path, ctx)
    install_version(tmp_path, "2.1.218")
    r = run_spawn(ctx, tmp_path, "b1", "--dry-run", env_extra=_meta(args_b64=encode_args([])),
                  picker_body='if [ "$1" = "--handoff-contract" ]; then echo 2; exit 0; fi\nexit 0')
    assert "launch=picker-manual" in (r.stdout + r.stderr)


def test_bad_codec_degrades_to_picker_manual(tmp_path):
    ctx = setup_worktree(tmp_path); _spawnable(tmp_path, ctx)
    install_version(tmp_path, "2.1.218")
    r = run_spawn(ctx, tmp_path, "b1", "--dry-run", env_extra=_meta(args_b64="not-a-v1-codec"))
    assert "launch=picker-manual" in (r.stdout + r.stderr)


def test_corrupt_v1_body_degrades_to_picker_manual(tmp_path):
    # A valid `v1:` prefix but a garbage base64/JSON body must set ARGS_OK=0 and
    # degrade to picker-manual — never launch=auto with the forwarded args dropped.
    ctx = setup_worktree(tmp_path); _spawnable(tmp_path, ctx)
    install_version(tmp_path, "2.1.218")
    r = run_spawn(ctx, tmp_path, "b1", "--dry-run", env_extra=_meta(args_b64="v1:!!!not-base64!!!"))
    assert "launch=picker-manual" in (r.stdout + r.stderr)
```

Run → FAIL (no preflight/compose yet).

- [ ] **Step 2: Insert composition part B (append after the Task-4 block).**

Append directly after the `echo "[spawn-handoff] forwarded=..."` line:

```bash
# Auto-mode preflight (spec §5.4c). launch=auto only when ALL hold.
LAUNCH_MODE="picker-manual"
preflight_ok() {
  [ -n "${CLAUDE_CODE_PICKER_VERSION:-}" ] || return 1
  [ "$ARGS_OK" = "1" ] || return 1
  # Match the picker's own version discovery predicate (`find -type f -perm -u+x`),
  # not a lenient `-e` — otherwise preflight can pass a version the picker rejects.
  { [ -f "$VERSIONS_DIR/${CLAUDE_CODE_PICKER_VERSION}" ] && [ -x "$VERSIONS_DIR/${CLAUDE_CODE_PICKER_VERSION}" ]; } || return 1
  command -v claude-picker >/dev/null 2>&1 || return 1
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
  [ -n "$LABEL" ] && parts+=("--session-label" "$(shq "$LABEL")")
  local a; for a in "${FORWARDED[@]}"; do parts+=("$(shq "$a")"); done
  parts+=("$(shq "/pickup $BUNDLE_ID")")
  echo "${parts[*]}"
}
if [ "$LAUNCH_MODE" = "auto" ]; then
  PICKER_CMD="$(build_successor_cmd)"
  SUCCESSOR_CMD="$PICKER_CMD || { printf '%s %s runtime-picker-failure hop=%s\n' \"\$(date -u +%Y-%m-%dT%H:%M:%SZ)\" spawn \"$SP_HOP\" >> $(shq "$SPAWN_LOG"); claude-picker $(shq "/pickup $BUNDLE_ID"); }"
else
  SUCCESSOR_CMD="claude-picker $(shq "/pickup $BUNDLE_ID")"
fi
echo "[spawn-handoff] launch=$LAUNCH_MODE" >&2
echo "[spawn-handoff] successor command: $SUCCESSOR_CMD" >&2
```

> **Note:** `$SP_HOP` is expanded at compose time (defined in Task 2 after the hop-limit check), so the workspace's runtime fallback logs the concrete hop number. Only the literal `runtime-picker-failure` token is asserted by tests.
>
> **Precision (append-file exit-3 is non-interactive-only):** the picker validates `--append-system-prompt-file` readability and exits 3 **only under `--non-interactive`**. So the auto command's residual `|| { … }` reliably catches a still-dead append path — but *only because the auto path launches non-interactively*. The `picker-manual` branch launches the picker **interactively**, where a dead passthrough path is NOT validated (it flows straight to `claude`). Acceptable: Task 4's substitution already rematerialized the file for the auto path, and the interactive branch is an attended fallback the user completes.

- [ ] **Step 3: Run tests → pass.**

Run: `.venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -k "auto or picker_manual or contract or codec" -v` → PASS.

- [ ] **Step 4: Commit.**

```bash
git add skills/subagent-driven-development/scripts/spawn-handoff-session.sh tests/unit/test_spawn_handoff.py
git commit -m "feat(cmux-int): auto preflight + compose-side quoting (Task 5)"
```

---

### Task 6: Spawn sequence, reservation ordering, exit codes, --dry-run

**Files:**
- Modify: `skills/subagent-driven-development/scripts/spawn-handoff-session.sh`
- Modify: `tests/unit/test_spawn_handoff.py`

- [ ] **Step 1: Write the failing spawn/reservation/dry-run tests.**

Append to `test_spawn_handoff.py`:

```python
def _reach_spawn(tmp_path, ctx):
    _spawnable(tmp_path, ctx); install_version(tmp_path, "2.1.218")
    return _meta(args_b64=encode_args(["--append-system-prompt-file", "/tmp/x.md"]))


def test_dry_run_spawns_nothing(tmp_path):
    ctx = setup_worktree(tmp_path)
    r = run_spawn(ctx, tmp_path, "b1", "--dry-run", env_extra=_reach_spawn(tmp_path, ctx))
    assert r.returncode == 0
    logged = (tmp_path / "cmux.log").read_text() if (tmp_path / "cmux.log").exists() else ""
    assert "new-workspace" not in logged
    assert not (ctx["reports"] / ".handoff-hops").exists()
    assert not (ctx["reports"] / "handoff-spawn.log").exists()


def test_auto_spawn_success_exit_0(tmp_path):
    ctx = setup_worktree(tmp_path)
    r = run_spawn(ctx, tmp_path, "b1", env_extra=_reach_spawn(tmp_path, ctx))
    assert r.returncode == 0
    logged = (tmp_path / "cmux.log").read_text()
    assert "new-workspace" in logged
    for tok in ["--name", "--cwd", "--command", "--focus false"]:
        assert tok in logged
    assert "notify" in logged and "--title" in logged
    spawnlog = (ctx["reports"] / "handoff-spawn.log").read_text().splitlines()
    kinds = [ln.split()[2] for ln in spawnlog if len(ln.split()) > 2]
    assert kinds.index("intent") < kinds.index("outcome")
    assert (ctx["reports"] / ".handoff-hops").read_text().strip() == "1"


def test_spawn_failure_keeps_hop_exits_3(tmp_path):
    ctx = setup_worktree(tmp_path)
    body = ('if [ "$1" = "ping" ]; then echo PONG; exit 0; fi\n'
            'if [ "$1" = "new-workspace" ]; then echo "$@" >> "$CMUX_LOG"; exit 5; fi\n'
            'echo "$@" >> "$CMUX_LOG"; exit 0')
    r = run_spawn(ctx, tmp_path, "b1", env_extra=_reach_spawn(tmp_path, ctx), cmux_body=body)
    assert r.returncode == 3
    assert (ctx["reports"] / ".handoff-hops").read_text().strip() == "1"
    assert "spawn-failed" in (ctx["reports"] / "handoff-spawn.log").read_text()
    assert "/pickup b1" in (r.stdout + r.stderr)


def test_notify_failure_still_exit_0(tmp_path):
    ctx = setup_worktree(tmp_path)
    body = ('if [ "$1" = "ping" ]; then echo PONG; exit 0; fi\n'
            'if [ "$1" = "notify" ]; then exit 9; fi\n'
            'echo "$@" >> "$CMUX_LOG"; exit 0')
    r = run_spawn(ctx, tmp_path, "b1", env_extra=_reach_spawn(tmp_path, ctx), cmux_body=body)
    assert r.returncode == 0


def test_picker_manual_spawn_uses_interactive_command(tmp_path):
    ctx = setup_worktree(tmp_path); _spawnable(tmp_path, ctx)  # no metadata => picker-manual
    r = run_spawn(ctx, tmp_path, "b1")
    assert r.returncode == 0
    logged = (tmp_path / "cmux.log").read_text()
    assert "new-workspace" in logged and "--non-interactive" not in logged and "/pickup b1" in logged


def test_append_prompt_file_written_on_real_spawn(tmp_path):
    # On a real (non-dry-run) spawn, the append-prompt CONTENT is rematerialized
    # to the stable path and the forwarded --append-system-prompt-file points at it.
    import base64
    ctx = setup_worktree(tmp_path); _spawnable(tmp_path, ctx)
    install_version(tmp_path, "2.1.218")
    content = b"# forwarded system prompt\nBe concise.\n"
    env = _meta(args_b64=encode_args(["--append-system-prompt-file", "/tmp/gone.md"]),
                append_b64=base64.b64encode(content).decode())
    r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
    assert r.returncode == 0
    target = tmp_path / "home" / ".claude-codex-handoff" / "append-prompts" / "b1-hop1.md"
    assert target.read_bytes() == content
    assert "append-prompts/b1-hop1.md" in (tmp_path / "cmux.log").read_text()
```

Run → FAIL (skeleton still exits before the spawn sequence).

- [ ] **Step 2: Insert the spawn sequence + generic core + dry-run short-circuit.**

Replace the `# (Task 6 inserts the spawn sequence + exit here.)` marker AND the skeleton's trailing `echo ... ; exit 0` with:

```bash
# --- Generic, extraction-ready workspace-spawn core (Decision 15) ----------
# spawn_claude_workspace CWD LAUNCH_COMMAND WORKSPACE_NAME NOTIFY_TEXT
# Pure mechanics (no SDD policy). Returns cmux new-workspace's exit code.
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
SPAWN_ID="$("$PYTHON" -c 'import uuid;print(uuid.uuid4())')"
mkdir -p "$REPORTS_DIR"
# 1. Reserve (SP_HOP computed in Task 2 after the hop-limit check).
printf '%s\n' "$SP_HOP" > "$HOPS_FILE"
printf '%s %s intent hop=%s\n' "$(now_iso)" "$SPAWN_ID" "$SP_HOP" >> "$SPAWN_LOG"
# 2. Spawn.
if spawn_claude_workspace "$WORKTREE_ROOT" "$SUCCESSOR_CMD" "SDD resume: $FEATURE_NAME" \
     "Hop $SP_HOP/$MAX_HOPS — successor spawned"; then
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
```

- [ ] **Step 3: Run the full unit suite + regression.**

```bash
.venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -v
python3 tests/ARaymond-skill-regression/validate-all-skills.py
.venv/bin/python3 -m pytest tests/unit/ -q
```
Expected: all green (regression with known advisory WARNINGs only).

- [ ] **Step 4: Commit.**

```bash
git add skills/subagent-driven-development/scripts/spawn-handoff-session.sh tests/unit/test_spawn_handoff.py
git commit -m "feat(cmux-int): spawn sequence, reservation ordering, dry-run (Task 6)"
```
