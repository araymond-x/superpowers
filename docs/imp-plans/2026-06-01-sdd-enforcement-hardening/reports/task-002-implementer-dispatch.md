You are a focused implementation engineer following TDD strictly (RED → GREEN → verify). You are implementing Task 2 of the SDD Enforcement Hardening plan.

Work from: `/Users/araymond/projects/claude-custom/superpowers/.worktrees/sdd-enforcement-hardening` (git worktree, branch `sdd-enforcement-hardening`).

IMPORTANT: you are editing the WORKTREE copy of `sdd-pre-dispatch-hook.sh`. The LIVE hook gating this session resolves to the MAIN checkout, so your change is NOT live until merge, and the tests exercise the worktree copy via relative paths. This is intentional — do not try to make it "live."

## Task Description (VERBATIM from plan.md, Task 2)

### Task 2: Harden sdd-pre-dispatch-hook.sh — Check 4c skip-guard + Check 5 archive glob

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` (Check 4c block; Check 5 Task-0 glob)
- Test: `tests/unit/test_sdd_hook_hardening.py` (create)

**Pattern References:** `early-skip-guard-chain` (compose N3a as a sibling `elif`, NOT nested in the grep), `bash-hook-subprocess-test`.

**Context (N3a + N10):** After a module transition the live dispatch log is truncated, so the previous task's provenance lives in the archived log. Check 4c must **skip** when `PREV < MANIFEST_TASK_START` (the previous task belongs to a prior/archived module, or precedes a no-Task-0 plan's first task). Boundary provenance is re-verified at transition time by `transition-module.py:validate_module_completion` (the sibling enforcement — Task 3). Separately, Check 5's Task-0 lookup (N10) must also glob `archive-*/` so a Source-Contracts plan still finds an archived Task 0 at module 2.

Skip-guard truth table (verified against the code): module-first-task (`TASK_NUMBER==MANIFEST_TASK_START` ⇒ `PREV=START-1<START`) → skip; no-Task-0 plan (start=1, task 1, `PREV=0<1`) → skip; within-module (`PREV>=START`) → check runs; Task-0 plan (start=0, task 1, `PREV=0`, `0<0` false) → check runs.

- [ ] **Step 1: Write the failing tests** in `tests/unit/test_sdd_hook_hardening.py`

```python
"""N3a (Check 4c skip-guard) + N10 (Check 5 archive glob) for sdd-pre-dispatch-hook.sh.
Run: .venv/bin/python3 -m pytest tests/unit/test_sdd_hook_hardening.py -v
"""
import json
import os
import subprocess
from datetime import datetime, timezone

from sdd_test_helpers import make_hook_input, setup_manifest_workspace

HOOK_PATH = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..",
    "skills", "subagent-driven-development", "scripts", "sdd-pre-dispatch-hook.sh",
))
NOW = "2026-06-01T00:00:00Z"


def run_hook(stdin_data):
    return subprocess.run(["bash", HOOK_PATH], input=stdin_data,
                          capture_output=True, text=True, timeout=10)


def _impl(p):
    p.write_text("x" * 80)


def _full_support(reports, task_num, *, partner=True):
    """Create audit + checkpoint (+ partner review & provenance) so that the ONLY
    gate that could fire for `task_num` is Check 4c. Returns nothing."""
    _impl(reports / "pre-execution-audit.md")
    padded = f"{task_num:03d}"
    (reports / f"checkpoint-pre-dispatch-{padded}.json").write_text(
        json.dumps({"status": "PASS", "phase": "pre-dispatch", "detail": "x" * 60}))
    if partner:
        _impl(reports / f"partner-review-{padded}.md")
        with open(reports / ".dispatch-log", "a") as f:
            f.write(f"{NOW} DISPATCH reviewer task={task_num} type=partner-review\n")


def test_check4c_skipped_for_module_first_task(tmp_path):
    # Module 2 active (task_range starts at 2); empty log (post-truncation).
    # Dispatching task 2 must ALLOW: PREV=1 < START=2 -> skip-guard. Non-vacuous:
    # pre-fix Check 4c looks for `task=1 type=spec-review` in the empty log -> BLOCK.
    ws = setup_manifest_workspace(tmp_path, tier="standard", task_range=(2, 3), total_tasks=4)
    reports = ws["reports_dir"]
    (reports / ".dispatch-log").write_text("# sdd-hook-sentinel abc123\n")
    _full_support(reports, 2)
    r = run_hook(make_hook_input(description="Implement task 2",
                                 prompt="You are implementing task 2", cwd=str(ws["root"])))
    assert r.returncode == 0, f"stderr={r.stderr}"


def test_check4c_enforced_within_module(tmp_path):
    # Within-module dispatch (PREV >= START) still requires provenance.
    # task_range (2,3); dispatch task 3; PREV=2 >= START=2 -> check runs; no
    # task=2 provenance in log -> BLOCK.
    ws = setup_manifest_workspace(tmp_path, tier="standard", task_range=(2, 3), total_tasks=4)
    reports = ws["reports_dir"]
    (reports / ".dispatch-log").write_text("# sdd-hook-sentinel abc123\n")
    # Task 2 reports exist (so N-1 file checks pass) but NO spec/quality provenance.
    for kind in ("implementer-report", "spec-review", "quality-review"):
        _impl(reports / f"task-002-{kind}.md")
    _full_support(reports, 3)
    r = run_hook(make_hook_input(description="Implement task 3",
                                 prompt="You are implementing task 3", cwd=str(ws["root"])))
    assert r.returncode == 2
    assert "spec-review dispatch recorded for Task 2" in r.stderr


def test_check4c_skipped_for_no_task0_single_module(tmp_path):
    # Acceptance criterion #3: no-Task-0 single-module plan starting at Task 1
    # (no transition, no archive). task_range (1,2); dispatch task 1; PREV=0 <
    # START=1 -> skip-guard -> ALLOW. Non-vacuous: pre-fix Check 4c greps the
    # empty log for `task=0 type=spec-review` and BLOCKS, forcing a forged task=0
    # entry. (Check 6b is inert here: TASK_NUMBER=1 is not > 1.)
    ws = setup_manifest_workspace(tmp_path, tier="standard", task_range=(1, 2), total_tasks=2)
    reports = ws["reports_dir"]
    (reports / ".dispatch-log").write_text("# sdd-hook-sentinel abc123\n")
    _full_support(reports, 1)
    r = run_hook(make_hook_input(description="Implement task 1",
                                 prompt="You are implementing task 1", cwd=str(ws["root"])))
    assert r.returncode == 0, f"stderr={r.stderr}"


def test_check5_finds_archived_task0(tmp_path):
    # N10: Source-Contracts plan, Task 0 report archived; dispatching task 2 must
    # NOT block on the Task-0 gate (Check 5 globs archive-*/).
    ws = setup_manifest_workspace(tmp_path, tier="standard", task_range=(2, 3), total_tasks=4)
    root, reports, feat = ws["root"], ws["reports_dir"], ws["feat_dir"]
    # Give the plan real Source Contracts so Check 5 activates.
    plan = feat / "plan.md"
    plan.write_text(plan.read_text().replace("**Source Contracts:** None",
                                             "**Source Contracts:** docs/spec.md"))
    (reports / ".dispatch-log").write_text("# sdd-hook-sentinel abc123\n")
    arch = reports / "archive-Core"; arch.mkdir()
    _impl(arch / "task-000-implementer-report.md")     # archived Task 0
    _full_support(reports, 2)
    r = run_hook(make_hook_input(description="Implement task 2",
                                 prompt="You are implementing task 2", cwd=str(root)))
    # Must not block for the Task-0 reason (skip-guard handles Check 4c via PREV<START).
    assert "no Task 0 report found" not in r.stderr.lower()
    assert r.returncode == 0, f"stderr={r.stderr}"
```

> Note for the implementer: `setup_manifest_workspace` initializes git on a feature branch and writes `.active-feature` + manifest + a plan with `### Task N` headers and `**Source Contracts:** None`. `make_hook_input` is imported from `sdd_test_helpers` (already on `sys.path` via `conftest.py`).

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python3 -m pytest tests/unit/test_sdd_hook_hardening.py -v`
Expected: `test_check4c_skipped_for_module_first_task`, `test_check4c_skipped_for_no_task0_single_module`, and `test_check5_finds_archived_task0` FAIL (hook blocks); `test_check4c_enforced_within_module` PASSES (already enforced). (4 tests total.)

- [ ] **Step 3: Add the Check 4c skip-guard (N3a).** In `sdd-pre-dispatch-hook.sh`, extend the existing short-circuit chain in Check 4c. After the `elif [ "$PREV_TASK_TYPE" = "verification" ]; then` branch and before the final `else`, insert a sibling `elif`:

```bash
  elif [ "$PREV" -lt "$MANIFEST_TASK_START" ] 2>/dev/null; then
    # N3a: PREV belongs to a prior (archived) module, or precedes the module's
    # first task (no-Task-0 plan, start=1). The live dispatch log was truncated
    # at the module boundary, so PREV's provenance lives in the archived log.
    # The completing module's boundary provenance is re-verified at transition
    # time by transition-module.py:validate_module_completion (sibling enforcement).
    : # Skip — boundary provenance verified at transition, not here
```

- [ ] **Step 4: Make Check 5's Task-0 lookup archive-aware (N10).** In Check 5, replace the `T0_GLOB=$(task_report_glob "0" "implementer-report")` line with a local glob covering live + archive (do NOT modify the shared `task_report_glob` helper):

```bash
    # N10: cover both the live reports dir and archived module dirs. A multi-
    # module plan with Source Contracts archives Task 0's report under
    # reports/archive-<module>/ at the first transition; Check 5 must still find
    # it. check_report_file runs `ls $pattern`, so space-separated globs work.
    T0_GLOB="${REPORTS_DIR}/task-000-implementer-report* ${REPORTS_DIR}/archive-*/task-000-implementer-report*"
```

- [ ] **Step 5: Run to verify pass**

Run: `.venv/bin/python3 -m pytest tests/unit/test_sdd_hook_hardening.py -v`
Expected: all 3 PASS. (i.e. all 4 tests now pass.)

- [ ] **Step 6: Confirm no regression in the existing hook suites**

Run: `.venv/bin/python3 -m pytest tests/unit/test_sdd_classification.py tests/unit/test_sdd_hard_gates.py tests/unit/test_sdd_partner_gate.py tests/unit/test_sdd_dispatch_log.py -v`
Expected: all PASS.

- [ ] **Step 7: Commit**

```bash
git add skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh tests/unit/test_sdd_hook_hardening.py
git commit -m "feat(sdd): Check 4c skip-guard (N3a) + Check 5 archive glob (N10)"
```

## CRITICAL GUARDRAILS

1. **Compose N3a as a SIBLING `elif`, not nested in the grep.** Read the existing Check 4c structure first (in the live dispatch-provenance block). The real chain is `if [ "$NEED_PROV" = "false" ] / elif [ "$PREV_TASK_TYPE" = "verification" ] / else <provenance grep>`. Your new `elif [ "$PREV" -lt "$MANIFEST_TASK_START" ]` goes AFTER the verification branch and BEFORE the final `else`, as a third sibling. Do NOT put it inside the grep logic. Preserve the existing `else` provenance block exactly.
2. **N10 is a LOCAL glob only.** Replace ONLY the `T0_GLOB=...` assignment inside Check 5. Do NOT modify the shared `task_report_glob` helper (other checks depend on it). `check_report_file` runs `ls $pattern` (unquoted), so the space-separated two-glob string works.
3. **Intentionally Flat — do NOT touch:** Check 3b (non-standard-naming scan) and Check 7 (context-load `for rf in "${REPORTS_DIR}"/*.md` loop) stay flat. Only Check 4c (add skip-guard) and Check 5 (T0_GLOB) change. Nothing else in the hook.
4. **Do NOT add `set -u`** (the hook uses `set -uo pipefail` already — wait: verify. Actually it has `set -uo pipefail` at the top; respect existing settings, do not change them). Match existing bash style.
5. Read the hook fully before editing; verify the exact location of the Check 4c chain and the Check 5 `T0_GLOB` line. If the structure differs from this description, STOP and report BLOCKED.

## Context (scene-setting)
`sdd-pre-dispatch-hook.sh` is the PreToolUse Agent-tool hook that enforces the SDD per-task review cycle (manifest mode). Check 4c verifies the PREVIOUS task's reviewers were actually dispatched (provenance in the dispatch log). N3a: when PREV belongs to a prior/archived module (or precedes the module's first task), its provenance was truncated at the boundary, so Check 4c must skip and let transition-time validation (Task 3) cover it. N10: Check 5 (Source-Contracts → require Task 0 report) must also look in `archive-*/` so a multi-module Source-Contracts plan finds an archived Task 0.

## Contract Constraints (verbatim — non-negotiable)
- Dispatch-log provenance line format: reviewer `<ts> DISPATCH reviewer task=<N> type=<spec-review|quality-review|partner-review|trace-audit>`; implementer `<ts> DISPATCH implementer task=<N> type=implementer`. Grep keyed on substring `task=<N> type=<review_type>`.
- Two distinct "minimum" signals — do not conflate (FILE vs PLAN-DECLARATION).
- Manifest is git-root-relative; `MANIFEST_TASK_START = task_range[0]`. (Already a variable in the hook — confirm by reading.)
- Module boundary lifecycle: Step 1 validate → Step 3 archive `task-NNN-*` → `reports/archive-<module>/` → Step 4 advance → Step 5 truncate live `.dispatch-log`.
- Tier review modes: spec_review_mode / quality_review_mode may be "skip".
- Block convention: exit 2 + stderr.
- Archive-awareness applies to EXACTLY two lookups: controller-checkpoint.py's two functions (Task 1, done) and THIS task's Check 5 Task-0 lookup (N10). All other globs flat.

## Source Files
None (Source Contracts: None). READ `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` before editing — confirm: `MANIFEST_TASK_START` and `PREV` variables exist and are in scope at Check 4c; the Check 4c `if NEED_PROV / elif PREV_TASK_TYPE==verification / else` chain; the `T0_GLOB=$(task_report_glob "0" "implementer-report")` line in Check 5; that `check_report_file` runs `ls $pattern`. Read `tests/unit/sdd_test_helpers.py` (read-only) to confirm `make_hook_input(description=, prompt=, cwd=)` and `setup_manifest_workspace(tmp_path, tier=, task_range=, total_tasks=)` signatures, and what `setup_manifest_workspace` returns (keys: root, reports_dir, feat_dir).

## Shared Constants
None.

## Pattern References (read before writing)
- `early-skip-guard-chain` → `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` (the existing Check 4c `if/elif/else` short-circuit chain — your sibling `elif` must match its style).
- `bash-hook-subprocess-test` → `tests/unit/test_sdd_classification.py` + `tests/unit/sdd_test_helpers.py` (the `run_hook` subprocess pattern + the manifest-mode helpers `setup_manifest_workspace`/`make_hook_input`).

## Subdirectory CLAUDE.md Files
None in the touched dirs. Governing conventions: root CLAUDE.md "Hook Development Gotchas" (avoid `set -u` pitfalls; jq pipe chains; `$PYTHON` for python calls in hooks if any — N/A here).

## Before You Begin
Read the hook + the two pattern-reference files first. If the Check 4c chain or the Check 5 `T0_GLOB` line differs from the description above, STOP and report BLOCKED — do not improvise placement.

## Your Job (TDD)
1. Read the hook, `sdd_test_helpers.py`, and a sample subprocess test.
2. Step 1: write the 4 tests exactly as above.
3. Step 2: run → confirm RED (3 fail, 1 passes — test_check4c_enforced_within_module).
4. Steps 3–4: insert the Check 4c sibling `elif` and the Check 5 local `T0_GLOB`. Touch nothing else.
5. Step 5: run → 4 pass.
6. Step 6: run the 4 regression suites → all pass.
7. Step 7: commit both files with the exact message.
8. Clean up scratch files. Self-review (esp. that you added a SIBLING elif and a LOCAL glob, touched no other check). Report.

## Report Format
Standard YAML frontmatter (schema_version, task_id: 2, status, files_changed, tests {written, passing, command, result}, contract_compliance [list]) then prose sections: Implementation Summary, Source Files Read, CLAUDE.md Files Read, Deviations from Plan, Self-Review Findings, Concerns. Your final message IS the report. Use DONE_WITH_CONCERNS if any deviations/concerns; BLOCKED if you cannot complete.
