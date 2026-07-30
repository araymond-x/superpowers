---
schema_version: 1
feature_archetype: extension
enforcement_tier: standard
entry_mode: brainstorming
source_contracts: "docs/imp-plans/2026-07-30-cmux-spawn-v2/spec-distilled.md"
integration_test:
  path: tests/integration/sdd-e2e-test.sh
tasks:
  - id: 12
    title: "write-mechanics-card.py + golden-file test"
  - id: 13
    title: "Checked outcome writes (N63) + bookkeeping commit + card invocation"
    depends_on: [12]
  - id: 14
    title: "Hooks trio: session-start signal, stop-hook spawn-outcome WARNING, Check 3b allowlist + one baseline re-capture"
    depends_on: [13]
  - id: 15
    title: "Check 9 :(exclude) pathspec + both-direction tests"
    depends_on: [13, 14]
  - id: 16
    title: "context-handoff-protocol.md rewrite"
    depends_on: [14]
  - id: 17
    title: "e2e Step 14 rewrite (surface topology + handshake + policy dial)"
    depends_on: [14, 15]
  - id: 18
    title: "Full-suite verification + banner counts"
    depends_on: [16, 17]
    task_type: verification
---

# cmux-spawn-v2 — Module 4: Mechanics card, hooks, compatibility, docs, e2e

> **Parent plan:** `docs/imp-plans/2026-07-30-cmux-spawn-v2/plan.md`
> **Module:** 4 of 4
> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first — direct implementation bypasses review enforcement, quality gates, and hooks.

**Module Goal:** Everything downstream of the script core: the mechanics card the successor reads, durable-audit outcome writes (closes BACKLOG N63) + the bookkeeping commit, the three baselined-hook changes with ONE `check-hooks.sh --capture`, the Check 9 pathspec, the protocol-doc rewrite, the e2e Step 14 rewrite, and the closing full-suite verification.

**Source Contracts:** None

_External contracts were frozen into fixtures by Module 1's Task 0 (repo convention: the mechanical Task-0 gate resolves against the module that owns Task 0). The binding facts this module consumes — spec-distilled Decisions 5-6, 12-17 + §5.5-5.7, BACKLOG row N63's fix direction (checked appends must NOT change exit semantics), and the parent plan's Shared Contract Section — are restated under Contract Constraints below._

**Contract Constraints:** Baselined hooks (`hooks/session-start`, `sdd-stop-hook.sh`, `sdd-pre-dispatch-hook.sh`) change ONLY in Task 14, which re-captures `tests/ARaymond-hook-baseline/baseline.txt` in the SAME commit. Stop hooks emit `systemMessage` (never `hookSpecificOutput`), always exit 0. `hooks/session-start` runs under `set -euo pipefail` — the signal must be backgrounded and never affect hook exit. SDD SKILL.md word ceiling: any SKILL-body edit needs `wc -w` before/after and must not grow the body — protocol content belongs in `references/`. The card generator is Python (plan decision: manifest JSON + model imports + golden-file testability; NOT hook-invoked, so the venv is available via `$PYTHON`).

## File Map

| File | Responsibility |
|------|----------------|
| `skills/subagent-driven-development/scripts/write-mechanics-card.py` | NEW — deterministic `reports/handoff-mechanics.md` generator |
| `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` | Task 13 only: checked outcome writes + commit + card invocation |
| `hooks/session-start` | wait-for signal (Task 14) |
| `skills/subagent-driven-development/scripts/sdd-stop-hook.sh` | spawn-outcome WARNING (Task 14) |
| `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` | Check 3b `handoff-` allowlist (Task 14) |
| `tests/ARaymond-hook-baseline/baseline.txt` | re-captured in Task 14's commit |
| `skills/subagent-driven-development/scripts/controller-checkpoint.py` | Check 9 pathspec (Task 15) |
| `skills/subagent-driven-development/references/context-handoff-protocol.md` | rewrite (Task 16) |
| `tests/integration/sdd-e2e-test.sh` | Step 14 rewrite + banner (Task 17) |
| `tests/unit/test_mechanics_card.py` | NEW golden-file + skeleton tests |
| `tests/unit/test_spawn_handoff_v2.py`, `test_spawn_handoff.py` | Task 13 fault-injection + commit tests |
| hook/checkpoint unit test files (locate: `grep -rl "sdd-stop-hook\|check_report_file\|_check_verification_git_reality" tests/unit/`) | Tasks 14-15 additions |
| `docs/process-improvement-findings/BACKLOG.md` | N63 close (Task 13) |

## Write-Scope Partitioning

| Task | Owned Files (write) | Read-Only Files | Depends On |
|------|---------------------|-----------------|------------|
| Task 12 | `write-mechanics-card.py`, `test_mechanics_card.py` | implementer_report.py, _report_utils.py, _handoff_support.py | Task 7 |
| Task 13 | `spawn-handoff-session.sh`, `test_spawn_handoff_v2.py`, `test_spawn_handoff.py`, `BACKLOG.md` | write-mechanics-card.py | Tasks 11, 12 |
| Task 14 | `hooks/session-start`, `sdd-stop-hook.sh`, `sdd-pre-dispatch-hook.sh`, `baseline.txt`, hook test files | — | Task 13 |
| Task 15 | `controller-checkpoint.py`, checkpoint test files | — | Task 13 |
| Task 16 | `references/context-handoff-protocol.md` (+ SDD SKILL.md only if stale refs found) | — | Task 14 |
| Task 17 | `tests/integration/sdd-e2e-test.sh` | — | Tasks 14, 15 |
| Task 18 | — (verification; fixes route back as attributed fix dispatches) | everything | Tasks 16, 17 |

Tasks 14 and 15 touch disjoint files and could run in parallel; the plan serializes them (14 → 15 dispatch order) to keep the dispatch log linear.

## Test harness (top of `tests/unit/test_mechanics_card.py`; used by Task 12)

````python
"""write-mechanics-card.py — deterministic successor mechanics card."""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "skills" / "subagent-driven-development" / "scripts"
CARD = SCRIPTS / "write-mechanics-card.py"
VENV_PY = str(ROOT / ".venv" / "bin" / "python3")


def _fixture_feature(tmp_path):
    """git repo + feature dir + manifest + hop state + observation log + spawn log.
    Manifest content comes from the REAL materializer (drift here is exactly what
    the golden test must catch), then `handoff` and `context_summary_at` are
    pinned for determinism."""
    wt = tmp_path / "wt"
    feat = wt / "docs" / "imp-plans" / "feat"
    reports = feat / "reports"
    reports.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=wt, check=True)
    _materialize_minimal_plan(wt, feat)
    (reports / ".handoff-hops").write_text("1\n")
    (reports / "handoff-spawn.log").write_text(
        "2026-07-30T01:00:00Z u1 intent hop=1 tasks_done=0\n"
        "2026-07-30T01:01:00Z u1 outcome hop=1 workspace=workspace:5 surface=surface:7 "
        "launch=auto bundle=b1 quota=ok tasks_done=0 handshake=ok\n")
    (reports / "context-observations.log").write_text(
        "2026-07-30T01:02:00Z task=3 type=implementer tokens=250000 source=probe tier=below action=allow\n")
    return wt, feat, reports


def _run_card(wt, feat):
    import os
    env = {k: v for k, v in os.environ.items() if not k.startswith("SUPERPOWERS_CMUX_")}
    # ambient knobs (e.g. MAX_HOPS) would skew the card's ceiling line
    return subprocess.run(
        [VENV_PY, str(CARD), "--manifest", str(feat / ".sdd-session.json")],
        cwd=wt, capture_output=True, text=True, env=env)


def _materialize_minimal_plan(wt, feat):
    feat.mkdir(parents=True, exist_ok=True)
    tasks = "\n".join(f"  - id: {i}\n    title: t{i}" for i in range(5))
    (feat / "plan.md").write_text(
        f"---\nschema_version: 1\nfeature_archetype: extension\ntasks:\n{tasks}\n---\n# p\n")
    subprocess.run([VENV_PY, str(SCRIPTS / "materialize-manifest.py"),
                    "--plan-file", str(feat / "plan.md"), "--feature-dir", str(feat)],
                   cwd=wt, check=True)
    mpath = feat / ".sdd-session.json"
    m = json.loads(mpath.read_text())
    m["handoff"] = {"expected_hops": 2, "spawn_policy": "auto"}
    m["enforcement"]["context_summary_at"] = 2
    mpath.write_text(json.dumps(m))
````

## Generator helpers (inside `write-mechanics-card.py`, below its imports; used by Task 12)

```python
def _read(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError:
        return None


def _last_line(text):
    lines = [l for l in (text or "").splitlines() if l.strip()]
    return lines[-1] if lines else None


def _skeleton():
    """Fields mirror ImplementerReport; sections mirror REQUIRED_SECTIONS —
    imported, not retyped, so model drift breaks this file's tests."""
    fm = {"schema_version": 1, "task_id": 999, "task_type": "implementation",
          "status": "DONE",
          "files_changed": [{"path": "path/to/file", "description": "what changed"}],
          "tests": {"written": 1, "passing": 1, "command": "pytest ...", "result": "PASS"}}
    ImplementerReport.model_validate(fm)          # self-check: skeleton is model-valid
    body = "".join(f"\n## {name}\n\n(fill in)\n" for name, _ in REQUIRED_SECTIONS)
    return "---\n" + yaml.safe_dump(fm, sort_keys=False) + "---\n" + body
```

### Task 12: write-mechanics-card.py + golden-file test

**Files:**
- Create: `skills/subagent-driven-development/scripts/write-mechanics-card.py`
- Test: `tests/unit/test_mechanics_card.py`

- [ ] **Step 1: Failing tests** (the module-level harness from the "Test harness" section above must already be in the file):

````python
def test_card_deterministic_with_contents(tmp_path):
    wt, feat, reports = _fixture_feature(tmp_path)
    assert _run_card(wt, feat).returncode == 0
    card = (reports / "handoff-mechanics.md").read_text()
    assert _run_card(wt, feat).returncode == 0
    assert (reports / "handoff-mechanics.md").read_text() == card    # deterministic
    assert "controller-checkpoint.py" in card and "--phase pre-dispatch" in card \
        and "--phase pre-completion" in card and "--manifest" in card \
        and "--deviations-file" in card and "--reports-dir" in card   # N35: both hard-required even in manifest mode
    assert "docs/imp-plans/feat/plan.md" in card and "deviations.md" in card
    assert re.search(r"hops used:\s*1", card) and re.search(r"expected:\s*2", card) \
        and re.search(r"ceiling:\s*6", card)
    assert "tokens=250000" in card                       # last observation line
    assert "context summary due at task 2" in card       # Check 6b midpoint status
    assert "workspace:5" in card and "surface:7" in card
    assert "/rename" in card and "/rc" in card and "context-handoff-protocol.md" in card


def test_report_skeleton_passes_validate_report(tmp_path):
    wt, feat, reports = _fixture_feature(tmp_path)
    _run_card(wt, feat)
    card = (reports / "handoff-mechanics.md").read_text()
    fence = "`" * 3          # composed, so this test can live inside fenced plan docs
    m = re.search(fence + r"markdown\n(---\n.*?)\n" + fence, card, re.S)
    assert m, "card must fence the report skeleton"
    skel = tmp_path / "task-999-implementer-report.md"
    skel.write_text(m.group(1) + "\n")
    r = subprocess.run([VENV_PY, str(SCRIPTS / "validate-report.py"), "--report-file", str(skel)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_missing_inputs_degrade_not_crash(tmp_path):
    wt, feat, reports = _fixture_feature(tmp_path)
    (reports / "context-observations.log").unlink()
    (reports / "handoff-spawn.log").unlink()
    assert _run_card(wt, feat).returncode == 0
    assert "(none recorded)" in (reports / "handoff-mechanics.md").read_text()


def test_byte_proxy_interference_invariant():
    """Spec: card IS counted by the byte-proxy (real context), matched by NO
    task-report glob or stale-artifact scan. Mirror the ACTUAL hook patterns —
    grep sdd-pre-dispatch-hook.sh for `ctx_byte_estimate` + the stale-scan
    prefixes and pin them here, citing the hook construct in a comment."""
    import fnmatch
    name = "handoff-mechanics.md"
    assert fnmatch.fnmatch(name, "*.md")                      # byte-proxy counts it
    assert not any(fnmatch.fnmatch(name, p) for p in
                   ("task-*", "pre-execution-audit*", "context-summary*"))
````

- [ ] **Step 2: Run to verify failure**, then **Step 3: Implement** `write-mechanics-card.py`:

````python
#!/usr/bin/env python3
"""write-mechanics-card.py --manifest <path> [--output <path>]

The successor's mechanics card (reports/handoff-mechanics.md): everything a
fresh SDD controller needs for its first checkpoint. Deterministic for fixed
inputs (no timestamps of its own). Invoked by spawn-handoff-session.sh via
$PYTHON, and standalone by the manual-fallback path. NOT hook-invoked, so the
venv (PyYAML + pydantic) is a hard dependency — exit 2 if imports fail."""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))                    # _handoff_support
sys.path.insert(0, str(Path(__file__).resolve().parent / "../../scripts/models"))

from _handoff_support import derive_expected_hops, hop_ceiling  # noqa: E402

try:
    import yaml  # noqa: E402
    from implementer_report import ImplementerReport  # noqa: F401,E402  (skeleton mirrors its fields)
    from _report_utils import REQUIRED_SECTIONS  # noqa: E402
except ImportError as exc:  # pragma: no cover
    print(f"write-mechanics-card.py requires the venv (PyYAML/pydantic): {exc}", file=sys.stderr)
    sys.exit(2)

CHECKPOINT = str(Path(__file__).resolve().parent / "controller-checkpoint.py")
F = "`" * 3   # markdown fence, composed so this source embeds cleanly in fenced docs


# (_read / _last_line / _skeleton from the "Generator helpers" section above go here)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--output")
    a = ap.parse_args()
    mp = Path(a.manifest)
    try:
        manifest = json.loads(mp.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot read manifest: {exc}", file=sys.stderr)
        return 2
    git_root = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                              capture_output=True, text=True,
                              cwd=str(mp.parent)).stdout.strip() or str(mp.parent)
    paths = manifest.get("paths", {})
    feature_dir = paths.get("feature_dir", str(mp.parent))
    reports = os.path.join(git_root, paths.get("reports_dir", os.path.join(feature_dir, "reports")))
    hops = (_read(os.path.join(reports, ".handoff-hops")) or "0").strip()
    expected = derive_expected_hops(manifest)
    ceiling = os.environ.get("SUPERPOWERS_CMUX_MAX_HOPS") or hop_ceiling(expected)
    obs_line = _last_line(_read(os.path.join(reports, "context-observations.log"))) or "(none recorded)"
    spawn_log = _read(os.path.join(reports, "handoff-spawn.log")) or ""
    outcome = _last_line("\n".join(l for l in spawn_log.splitlines() if " outcome " in l)) or "(none recorded)"
    csum_at = (manifest.get("enforcement") or {}).get("context_summary_at")
    csum = ("not required (micro tier)" if csum_at is None else
            f"context summary due at task {csum_at} — "
            + ("present" if os.path.isfile(os.path.join(reports, "context-summary.md"))
               else "ABSENT (write before the midpoint dispatch)"))
    manifest_abs = os.path.join(git_root, feature_dir, ".sdd-session.json")
    deviations_abs = os.path.join(git_root, paths.get("deviations_file", os.path.join(feature_dir, "deviations.md")))
    module_line = (f"- Active module plan: `{os.path.join(git_root, feature_dir, manifest['active_module_file'])}`\n"
                   if manifest.get("active_module_file") else "")
    card = f"""# SDD Handoff Mechanics Card

Generated by write-mechanics-card.py for the successor session. Paths are
absolute for THIS machine; regenerate standalone with:
`$PYTHON {Path(__file__).resolve()} --manifest {manifest_abs}`

## Checkpoint invocations (copy verbatim)

{F}bash
{sys.executable} {CHECKPOINT} --phase pre-dispatch --task-number <N> --manifest {manifest_abs} --deviations-file {deviations_abs} --reports-dir {reports}/
{sys.executable} {CHECKPOINT} --phase pre-completion --manifest {manifest_abs} --deviations-file {deviations_abs} --reports-dir {reports}/
{F}

## Paths

- Manifest: `{manifest_abs}`
- Plan: `{os.path.join(git_root, manifest.get("plan_file", "plan.md"))}`
{module_line}- Deviations: `{os.path.join(git_root, paths.get("deviations_file", ""))}`
- Reports: `{reports}`

## Hop state

- hops used: {hops}
- expected: {expected if expected is not None else "unknown"}
- ceiling: {ceiling}

## Context status

- Last observation: `{obs_line}`
- Check 6b: {csum}

## cmux location

- Last spawn outcome: `{outcome}`

## Session setup

`/rename` + `/rc` recipe: see `references/context-handoff-protocol.md`
(post-spawn setup normally ran automatically; verify the tab name and
`/remote-control is active` before trusting them).

## Implementer report skeleton (validate-report.py-clean)

{F}markdown
{_skeleton()}{F}
"""
    out = Path(a.output) if a.output else Path(reports) / "handoff-mechanics.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(card, encoding="utf-8")
    print(f"mechanics card written: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
````

Verify the composed invocations against `run_pre_dispatch`/`run_pre_completion`'s REQUIREMENTS, not argparse — argparse marks `--deviations-file`/`--reports-dir` optional but both functions hard-require them (the N35 incident). Proof = running both composed commands verbatim against the fixture and getting a checkpoint result, not an argument error.

- [ ] **Step 4: Run** — `.venv/bin/python3 -m pytest tests/unit/test_mechanics_card.py -v` — all PASS. **Step 5: Commit** — `"feat(cmux-spawn-v2): mechanics-card generator + golden tests"`.

### Task 13: Checked outcome writes (N63) + bookkeeping commit + card invocation

**Files:**
- Modify: `skills/subagent-driven-development/scripts/spawn-handoff-session.sh`
- Modify: `docs/process-improvement-findings/BACKLOG.md` (N63 → done)
- Test: `tests/unit/test_spawn_handoff_v2.py` (+ any `test_spawn_handoff.py` alignment)

- [ ] **Step 1: Failing tests:**

```python
class TestDurableOutcome:                       # N63: warn, notify, NEVER change exit
    def test_unwritable_log_on_success_path_warns_still_exit_0(self, tmp_path):
        # after reservation, make SPAWN_LOG unwritable the way the existing
        # test_intent_write_failure_exits_3 does it for the intent write —
        # BUT arrange the failure to begin only after the intent append
        # (e.g. replace SPAWN_LOG with a symlink to a read-only file between
        # runs is impossible in one invocation; instead: pre-create the log,
        # then chmod 444 it AND chmod 555 reports/ via a cmux stub side effect
        # on `wait-for` — the stub runs between intent and outcome)
        # assert: exit 0; stderr contains "outcome could not be recorded";
        # cmux.log contains a notify with "not recorded"
    def test_unwritable_log_on_spawn_failed_path_still_exit_3(self, tmp_path): ...

class TestBookkeepingCommit:
    def test_success_commits_three_artifacts(self, tmp_path):
        # exit 0 -> `git log -1 --format=%s` in fixture wt == "chore(sdd): record handoff hop 1"
        # and `git show --name-only` lists .handoff-hops, handoff-spawn.log, handoff-mechanics.md
        # and `git status --porcelain` is clean (N64: successor starts clean)
    def test_no_commit_flag_skips(self, tmp_path):
        # --no-commit -> exit 0, dirty tree with the three artifacts, stderr notes the skip
    def test_commit_failure_warns_never_fails(self, tmp_path):
        # sabotage: fixture repo with pre-commit hook that exits 1 -> exit STILL 0 + warning
    def test_timeout_path_does_not_commit(self, tmp_path):
        # CMUX_WAITFOR_RC=1 -> exit 3; no "chore(sdd)" commit
    def test_card_generated_before_commit(self, tmp_path):
        # committed handoff-mechanics.md content contains "Mechanics Card"
    def test_card_failure_warns_commits_rest(self, tmp_path):
        # point SUPERPOWERS_ROOT at a tree whose write-mechanics-card.py is absent
        # (or chmod it) -> warning + commit still contains hops+log
```

The wait-for-stub side-effect trick: extend the v2 stub — when `CMUX_SABOTAGE_ON_WAITFOR=1`, the `wait-for` branch runs `chmod 444 "$SABOTAGE_TARGET"` before exiting 0. This flips the log read-only between the intent append and the outcome append, inside one script run.

- [ ] **Step 2: Implement.** Arg parse gains `--no-commit) NO_COMMIT=1 ;;` (init `NO_COMMIT=0`). Then in the spawn sequence:

(a) Wrap ALL THREE outcome appends (success, timeout, spawn-failed) in checked writes. Shape (success-path shown; the other two identical but keep their `exit 3`):

```bash
  if ! printf '…outcome format…\n' … >> "$SPAWN_LOG"; then
    # N63: the successor EXISTS — a lost audit record must never look like a
    # retryable failure. Warn + notify; the exit code of this branch is unchanged.
    cmux notify --title "SDD handoff" --body "Successor spawned but outcome NOT recorded (audit log unwritable) — check $SPAWN_LOG" 2>/dev/null || true
    echo "[spawn-handoff] warn: outcome could not be recorded in $SPAWN_LOG — successor is running; fix the log before the next hop (stall check will read stale history)." >&2
  fi
```

(b) After the success outcome append (still before the stdout line / exit 0): card + commit:

```bash
  CARD_SCRIPT="$SCRIPT_DIR/write-mechanics-card.py"
  if [ -f "$MANIFEST_FILE" ] && [ -f "$CARD_SCRIPT" ]; then
    if ! "$PYTHON" "$CARD_SCRIPT" --manifest "$MANIFEST_FILE" >/dev/null 2>&1; then
      echo "[spawn-handoff] warn: mechanics card generation failed — successor must derive paths from the manifest itself." >&2
    fi
  else
    echo "[spawn-handoff] warn: mechanics card skipped (manifest or generator missing)." >&2
  fi
  if [ "$NO_COMMIT" = "1" ]; then
    echo "[spawn-handoff] --no-commit: leaving hop bookkeeping uncommitted (successor's clean-tree checks will see it)." >&2
  else
    git add "$HOPS_FILE" "$SPAWN_LOG" 2>/dev/null
    [ -f "$REPORTS_DIR/handoff-mechanics.md" ] && git add "$REPORTS_DIR/handoff-mechanics.md" 2>/dev/null
    if ! git commit -m "chore(sdd): record handoff hop $SP_HOP" >/dev/null 2>&1; then
      echo "[spawn-handoff] warn: bookkeeping commit failed — commit reports/ manually (successor's clean-tree precondition will refuse otherwise)." >&2
    fi
  fi
```

(Explicit paths only — NEVER `git add -A`; the worktree may be shared. Timeout and spawn-failed branches do NOT commit: the operator is already being routed to that tab/manual flow with an un-clean tree as a signal.)

- [ ] **Step 3: Close N63** — edit its BACKLOG row status to `done (cmux-spawn-v2 Task 13, 2026-07-30)` with one line naming the checked-append + unchanged-exit design.

- [ ] **Step 4: Run both unit files + commit** — `"feat(cmux-spawn-v2): durable outcome writes (N63) + hop bookkeeping commit + card invocation"`.

### Task 14: Hooks trio + one baseline re-capture

**Files:**
- Modify: `hooks/session-start`, `skills/subagent-driven-development/scripts/sdd-stop-hook.sh`, `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`
- Modify: `tests/ARaymond-hook-baseline/baseline.txt` (re-capture, SAME commit)
- Test: locate the existing hook test files first (`grep -rln "sdd-stop-hook\|session-start\|NON_STANDARD" tests/unit/`) and extend them; create `tests/unit/test_session_start_signal.py` if session-start has no unit file.

All three hook edits + the re-capture land in ONE commit — a split leaves `check-hooks.sh` failing between commits.

- [ ] **Step 1: Failing tests:**

```python
# session-start signal
def test_signal_fires_when_spawn_id_set(tmp_path):
    # PATH-stub cmux logging argv; run: SUPERPOWERS_SPAWN_ID=abc CLAUDE_PLUGIN_ROOT=x bash hooks/session-start
    # assert exit 0, stdout is the normal JSON, and cmux log contains "wait-for -S sdd-hop-abc"
    # (poll briefly: the call is backgrounded)
def test_no_spawn_id_no_signal(tmp_path): ...
def test_cmux_absent_never_breaks_hook(tmp_path):
    # PATH without cmux + SUPERPOWERS_SPAWN_ID set -> exit 0, valid JSON (set -e survival)

# stop-hook Decision 15
def test_warns_on_unmatched_bundle(tmp_path):
    # fixture: HOME with bundles/<id>/manifest.json (bundle_type work, entry_skill SDD,
    # repo_id = fixture repo), bundle dir mtime after session start (transcript first-line
    # timestamp), spawn log WITHOUT bundle=<id> -> stdout systemMessage contains the id
def test_outcome_record_suppresses_warning(tmp_path):   # log has "bundle=<id>" outcome
def test_decline_record_suppresses_warning(tmp_path):   # log has "decline bundle=<id>"
def test_unrelated_repo_bundle_ignored(tmp_path):       # repo_id mismatch -> silent
def test_composes_with_checkpoint_fail_message(tmp_path):
    # checkpoint FAIL fixture + unmatched bundle -> ONE systemMessage containing both

# Check 3b
def test_handoff_prefix_reports_allowed(tmp_path):
    # reports/handoff-mechanics.md present -> dispatch NOT blocked by Check 3b
def test_junk_reports_still_blocked(tmp_path):          # reports/notes.md -> still blocked
```

- [ ] **Step 2: Implement `hooks/session-start`** — immediately after the `PLUGIN_ROOT` resolution (top of file, so the token fires even if later checks are slow):

```bash
# cmux-spawn-v2 handshake (spec §5.2): when spawned by spawn-handoff-session.sh,
# signal the parent's wait-for token. Backgrounded subshell + discarded output:
# this hook runs under `set -euo pipefail` and the signal must NEVER affect hook
# exit or stdout (the JSON contract below).
if [ -n "${SUPERPOWERS_SPAWN_ID:-}" ] && command -v cmux >/dev/null 2>&1; then
    ( cmux wait-for -S "sdd-hop-${SUPERPOWERS_SPAWN_ID}" >/dev/null 2>&1 & )
fi
```

- [ ] **Step 3: Implement the stop-hook check** — after the SDD-detection block (`REPORTS_DIR`/`DEVIATIONS_FILE` exist), before the checkpoint run; collect messages instead of emitting immediately:

```bash
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
    if [ -f "$SPAWN_LOG_FILE" ] && grep -qE "( outcome .*bundle=$BID( |\$))|( decline bundle=$BID( |\$))" "$SPAWN_LOG_FILE"; then
      continue
    fi
    SPAWN_WARN="WARNING: handoff bundle $BID was created this session but reports/handoff-spawn.log has no outcome or decline record for it. Either run spawn-handoff-session.sh $BID (protocol step 4), or record the decline: printf '%s - decline bundle=%s reason=<word>\\n' \"\$(date -u +%Y-%m-%dT%H:%M:%SZ)\" $BID >> $SPAWN_LOG_FILE"
    break
  done
fi
```

then merge into the emission: if the checkpoint result is FAIL, append `\n\n$SPAWN_WARN` to `CONTEXT_MSG` when non-empty; if the checkpoint passes but `SPAWN_WARN` is non-empty, emit a systemMessage with just the warning (replace the silent `:` branch with that conditional). Keep the guaranteed `exit 0`. Note the bundle-id regex uses a `grep -qE` on a FILE (no pipe — no SIGPIPE hazard) and `$BID` is charset-safe (`^[A-Za-z0-9_.-]+$` by construction of bundle ids; still, quote it).

- [ ] **Step 4: Implement Check 3b** — in `sdd-pre-dispatch-hook.sh`, extend the allowlist alternation (quoted here as it must read after the edit):

```bash
if ! echo "$BASENAME" | grep -qE '^(task-[0-9]+-|pre-execution-audit|context-summary|partner-review|checkpoint-pre-dispatch|honesty-check-|handoff-|execution-trace-audit\.md|final-code-review\.md)'; then
```

(one token added: `handoff-|` — covers `handoff-mechanics.md`; `handoff-spawn.log` and `.handoff-hops` were never scanned, the glob is `*.md`.)

- [ ] **Step 5: Re-capture the baseline IN THE SAME COMMIT:**

```bash
bash tests/ARaymond-hook-baseline/check-hooks.sh --capture
bash tests/ARaymond-hook-baseline/check-hooks.sh          # verify: PASS, no drift
```

- [ ] **Step 6: Run** — new hook tests + the FULL unit suite (the pre-dispatch hook has a wide existing matrix) — all PASS. **Step 7: Commit** (all three hooks + baseline.txt + tests together) — `"feat(cmux-spawn-v2): session-start handshake signal + stop-hook spawn-outcome warning + Check 3b handoff- allowlist (baseline re-captured)"`.

### Task 15: Check 9 :(exclude) pathspec

**Files:**
- Modify: `skills/subagent-driven-development/scripts/controller-checkpoint.py`
- Test: the existing checkpoint git-reality test file (locate via `grep -rln "_check_verification_git_reality\|verification_git_reality" tests/unit/`)

- [ ] **Step 1: Failing tests** (in that file's idiom — it already builds git fixtures with dispatch logs):

```python
def test_bookkeeping_commit_in_window_passes(...):
    # verification task window contains ONE commit touching ONLY
    # docs/imp-plans/feat/reports/handoff-spawn.log + .handoff-hops
    # -> _check_verification_git_reality(..., exclude_dir="docs/imp-plans/feat") == []
def test_source_commit_in_window_still_fails(...):
    # window contains a commit touching src-file.py -> finding present WITH exclude_dir set
def test_no_exclude_dir_keeps_old_behavior(...):
    # exclude_dir=None + bookkeeping commit -> finding present (backward-compat pin)
```

- [ ] **Step 2: Implement.** Signature: `def _check_verification_git_reality(verification_ids, dispatch_log_path, git_root=None, exclude_dir=None):`. After `git_args.extend(["--diff-filter=ACDMR", "--name-only"])`:

```python
    if exclude_dir:
        # cmux-spawn-v2 Decision 17: hop bookkeeping (handoff-spawn.log,
        # .handoff-hops, handoff-mechanics.md, reports) lands as commits inside
        # the feature dir during verification windows — exclude the feature dir
        # so only SOURCE modifications trip the check.
        git_args.extend(["--", ".", f":(exclude){exclude_dir}"])
```

Caller (Check 9 block): in manifest mode, `exclude_dir = _md.get("paths", {}).get("feature_dir")` (captured in the same `try` that reads the dispatch log); in `args.reports_dir` mode, `exclude_dir = os.path.relpath(os.path.dirname(os.path.abspath(args.reports_dir.rstrip("/"))), git_root_or_cwd)` — mirror however the file resolves relative paths elsewhere; read it first. Pass `exclude_dir=exclude_dir` at the call site.

- [ ] **Step 3: Run** — the checkpoint test files + full unit suite — PASS. **Step 4: Commit** — `"feat(cmux-spawn-v2): Check 9 excludes feature-dir bookkeeping via :(exclude) pathspec"`.

### Task 16: context-handoff-protocol.md rewrite

**Files:**
- Modify: `skills/subagent-driven-development/references/context-handoff-protocol.md`
- Possibly: SDD `SKILL.md` ONLY if `grep -n "workspace" skills/subagent-driven-development/SKILL.md` shows spawn-topology claims (then `wc -w` before/after; body must not grow).

- [ ] **Step 1: Rewrite step 4 and the exit-code guidance** — the current text says "spawns the successor in a new cmux workspace" and enumerates workspace-topology causes; it must instead describe:
  - Surface default: successor = **top tab in the caller's workspace** (left-sidebar entry only on `topology=workspace-fallback`); tab named by the title format.
  - Exit 0 = spawned AND token received (`handshake=ok`); `launch=` caveat text unchanged in spirit (picker-manual still needs the human, notify still doesn't name the mode).
  - Exit 3 causes now: not-in-cmux, `reason=policy-off`, `reason=policy-ask` (retryable, no hop consumed — re-run with `--user-approved` after asking the user), `reason=stall` (progress-bearing message; raise `SUPERPOWERS_CMUX_MAX_STALL_HOPS` via inline env), ceiling reached, quota low, malformed hop counter, reservation write failed, spawn-failed-after-reservation, and `handshake=timeout` with `diagnosis=` (trust-dialog/banner → GO TO THE EXISTING TAB, never a fresh session; a spawn happened).
  - Exit 1 causes unchanged + the N64 note: a SUCCESSFUL spawn commits its own bookkeeping (`chore(sdd): record handoff hop N`); with `--no-commit` the successor's step-2 commit must fold those artifacts in.
- [ ] **Step 2: Add the new sections:** the `/rename`+`/rc` recipe (what the script does post-handshake; how to redo it by hand: `cmux send --surface <ref> "/rename <title>"` → `send-key enter` → verify; same for `/rc` expecting "/remote-control is active"); "`--session-label` is telemetry; `/rename` is the phone-visible session name"; "`settings.local.json` is NOT read by a running session — raise knobs via inline env on the spawn invocation"; the decline one-liner (exact printf from Task 14's warning text); the new env knobs with defaults (SPAWN_WAIT_TIMEOUT + its Task-0 provenance, MAX_STALL_HOPS, POST_SPAWN, TITLE_FORMAT, derived MAX_HOPS ceiling); mechanics card: what it is, where it lands, the standalone regeneration command for the manual-fallback path; hop-budget scoping (per-feature, expected vs ceiling vs stall).
- [ ] **Step 3: Verify + commit** — `python3 tests/ARaymond-skill-regression/validate-all-skills.py` PASS (references/ files are size-exempt but cross-refs are checked); if SKILL.md was touched, `wc -w` before/after recorded in the commit message. Commit: `"docs(cmux-spawn-v2): protocol rewrite — surface topology, handshake states, policy dial, post-spawn recipe"`.

### Task 17: e2e Step 14 rewrite

**Files:**
- Modify: `tests/integration/sdd-e2e-test.sh` (Step 14 block + closing banner)

- [ ] **Step 1: Rewrite the Step 14 stub + fixture:** keep the existing fixture scaffolding (repo, bundle, picker version, ARGS) and:
  - cmux stub gains the v2 verbs (same shapes as the unit helper: `new-surface` → `OK surface:7 pane:2 workspace:5`; `workspace create` → `OK workspace:9`; `rename-tab` → `OK action=rename`; `send`/`send-key` → `OK`; `wait-for` → exit 0; `read-screen` → emits a file whose content includes the tab title and `/remote-control is active` so post-spawn verification passes; `list-pane-surfaces` → the Task 0 shape; `ping` → PONG).
  - Fixture feature dir gains a committed `.sdd-session.json` (standard tier, `total_tasks: 5`, `task_range: [0,4]`, `handoff: {expected_hops: 2, spawn_policy: auto}`) — written with the SAME shape `materialize-manifest.py` emits (generate it by running the real script against a tiny plan fixture if easier).
- [ ] **Step 2: Assertions** (replacing the workspace-era ones):
  - `launch=auto` first (unchanged trap note), then: `new-surface` argv carries `--workspace TEST-WS --type terminal --focus false`; `rename-tab --surface surface:7`; the `send` line carries `export SUPERPOWERS_SPAWN_ID=` + the composed picker command; TWO `wait-for` lines never occur on the success path (exactly one); outcome record matches `handshake=ok`, `surface=surface:7`, `workspace=TEST-WS`, `tasks_done=0`; intent precedes outcome; hop == 1; the bookkeeping commit exists (`git -C "$SPAWN_WT" log --format=%s -1` == `chore(sdd): record handoff hop 1`) and the tree is clean.
  - Policy sub-run: rewrite the manifest with `spawn_policy: ask` (commit it), run WITHOUT `--user-approved` → rc 3, stderr `reason=policy-ask`, hop file still `1`, no second intent record.
  - Over-expected sub-run: append a prior outcome with `tasks_done=0`, add one committed DONE report (tasks_done becomes 1 → no stall), set manifest `expected_hops: 1` → run with `--user-approved`... (manifest back to `auto` is simpler: rewrite policy to auto) → rc 0 and the cmux log contains a notify whose body mentions `expected`.
- [ ] **Step 3: Update the closing banner** to the new step total — run the suite and read the count from the run, then pin it: `bash tests/integration/sdd-e2e-test.sh` → all steps PASS. **Step 4: Commit** — `"test(cmux-spawn-v2): e2e Step 14 — surface topology, handshake, policy dial, bookkeeping commit"`.

### Task 18: Full-suite verification + banner counts (task_type: verification)

**Files:** none (read-only; any fix found routes back as an attributed fix dispatch, committed BEFORE this task's final re-dispatch — Check 9 keys on the latest implementer timestamp).

- [ ] **Step 1:** `.venv/bin/python3 -m pytest tests/unit/ -q` — 0 failures (record the count).
- [ ] **Step 2:** `bash tests/integration/sdd-e2e-test.sh` — PASS with the Task 17 banner count.
- [ ] **Step 3:** `python3 tests/ARaymond-skill-regression/validate-all-skills.py` — PASS (advisory warnings allowed); `bash tests/ARaymond-installation/verify-symlink-install.sh` — PASS.
- [ ] **Step 4:** `bash tests/ARaymond-hook-baseline/check-hooks.sh` — PASS, no drift (proves Task 14's capture landed with the edits).
- [ ] **Step 5:** Contract greps, each with expected outcome recorded in the report:
  - `grep -n "new-workspace" skills/subagent-driven-development/scripts/spawn-handoff-session.sh` → NO live call sites (comments referencing history are fine; the fallback uses `workspace create`).
  - `grep -rn "set -u\|set -e\|pipefail" skills/subagent-driven-development/scripts/spawn-handoff-session.sh` → none.
  - `wc -w skills/subagent-driven-development/SKILL.md` → at or under the pre-sprint count (protocol content stayed in references/).
  - `grep -c "exit 3" skills/subagent-driven-development/scripts/spawn-handoff-session.sh` → record the new site count with `grep -nE '^[[:space:]]*exit 3'` (the CLAUDE.md "enumerate the sites" rule — the number goes in the report, not in docs).
- [ ] **Step 6:** Verification report (`task-018-implementer-report.md`, `task_type: verification`, `files_changed: []`) listing every command + verbatim tail of its output.

## Module 4 Acceptance Criteria

- [ ] Mechanics card is deterministic, contains the checkpoint invocations/paths/hop state/context status/cmux refs/recipe pointer, and its skeleton passes `validate-report.py`.
- [ ] All three outcome appends are checked; failures warn + notify and never change the branch's exit code (N63 closed in BACKLOG).
- [ ] A successful spawn leaves the fixture tree CLEAN with commit `chore(sdd): record handoff hop N`; `--no-commit` skips; timeout/spawn-failed branches never commit.
- [ ] `SUPERPOWERS_SPAWN_ID` + cmux on PATH → session-start signals `sdd-hop-<id>`; hook exit/stdout unaffected in all cases.
- [ ] Stop hook warns (systemMessage) on a this-session SDD bundle with no outcome/decline record, matched by bundle id; suppressed by either record type; composes with the checkpoint FAIL message.
- [ ] `handoff-mechanics.md` passes Check 3b; junk names still blocked.
- [ ] Check 9 ignores feature-dir bookkeeping commits and still fails on source commits; legacy no-exclude behavior pinned.
- [ ] Protocol doc describes the surface default, fallback, handshake states, policy dial, knobs, decline one-liner, and the card — no stale workspace-only claims.
- [ ] e2e Step 14 proves the composed surface flow end-to-end (incl. policy + over-expected sub-runs) and the banner count matches the run.
- [ ] Task 18's verification report shows every suite green.
