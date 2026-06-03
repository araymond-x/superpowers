You are a focused implementation engineer. You are implementing Task 4 of the SDD Enforcement Hardening plan — a TEST-ONLY task (one new test file, no production code).

Work from: `/Users/araymond/projects/claude-custom/superpowers/.worktrees/sdd-enforcement-hardening` (git worktree, branch `sdd-enforcement-hardening`).

## Task Description (VERBATIM from plan.md, Task 4)

### Task 4: SSOT agreement test for the file-based minimum signal

**Files:**
- Test: `tests/unit/test_ssot_minimum_agreement.py` (create)

**Pattern References:** `bash-hook-subprocess-test`, `transition-test-harness`.

**Context (D6):** Two enforcement sites consult the **file-based** minimum signal (`task-NNN-quality-review-minimum-tier.md`) to decide whether quality-review dispatch provenance is required: the hook's **Check 4c** (per-dispatch, on PREV) and `transition-module.py:validate_module_completion` (per-task, at transition). This test asserts both sites reach the **same require/exempt decision** across the matrix (minimum-file present/absent × quality-provenance present/absent), keyed strictly on the file signal. It compares the *decision*, not the two invocation contexts — each side is driven via subprocess and we check for its own quality-provenance error string.

- [ ] **Step 1: Write the test** in `tests/unit/test_ssot_minimum_agreement.py`

```python
"""D6: SSOT agreement on the FILE-based minimum signal between
sdd-pre-dispatch-hook.sh (Check 4c) and transition-module.py
(validate_module_completion). Both must require quality-review provenance UNLESS
task-NNN-quality-review-minimum-tier.md exists.
Run: .venv/bin/python3 -m pytest tests/unit/test_ssot_minimum_agreement.py -v
"""
import json
import os
import subprocess

import pytest
from sdd_test_helpers import make_hook_input, setup_manifest_workspace

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(ROOT, "skills", "subagent-driven-development", "scripts", "sdd-pre-dispatch-hook.sh")
TRANSITION = os.path.join(ROOT, "skills", "subagent-driven-development", "scripts", "transition-module.py")
PYTHON = os.path.join(ROOT, ".venv", "bin", "python3")
NOW = "2026-06-01T00:00:00Z"


def _impl(p):
    p.write_text("x" * 80)


def _hook_requires_quality_prov(tmp_path, min_file, provenance):
    """Decision from Check 4c: does the hook block on MISSING quality provenance
    for the previous task? Set up a single module [0,1]; dispatch task 1 (PREV=0,
    within-module so Check 4c runs). Returns True if it blocks for quality."""
    ws = setup_manifest_workspace(tmp_path, tier="standard", task_range=(0, 1), total_tasks=2)
    reports = ws["reports_dir"]
    log = reports / ".dispatch-log"
    log.write_text("# sdd-hook-sentinel abc123\n")
    # Task 0 fully present + spec provenance (isolate the quality decision).
    for kind in ("implementer-report", "spec-review"):
        _impl(reports / f"task-000-{kind}.md")
    with open(log, "a") as f:
        f.write(f"{NOW} DISPATCH reviewer task=0 type=spec-review\n")
    if min_file:
        _impl(reports / "task-000-quality-review-minimum-tier.md")
    else:
        _impl(reports / "task-000-quality-review.md")
    if provenance:
        with open(log, "a") as f:
            f.write(f"{NOW} DISPATCH reviewer task=0 type=quality-review\n")
    # Support files so only Check 4c quality can fire for task 1.
    _impl(reports / "pre-execution-audit.md")
    (reports / "checkpoint-pre-dispatch-001.json").write_text(
        json.dumps({"status": "PASS", "detail": "x" * 60}))
    _impl(reports / "partner-review-001.md")
    with open(log, "a") as f:
        f.write(f"{NOW} DISPATCH reviewer task=1 type=partner-review\n")
    r = subprocess.run(["bash", HOOK],
                       input=make_hook_input(description="Implement task 1",
                                             prompt="You are implementing task 1",
                                             cwd=str(ws["root"])),
                       capture_output=True, text=True, timeout=10)
    return "quality-review dispatch recorded for Task 0" in r.stderr


def _transition_requires_quality_prov(tmp_path, min_file, provenance):
    """Decision from validate_module_completion: does the transition error on
    MISSING quality provenance for task 0 of the completing module?"""
    subprocess.run(["git", "init", "-q"], cwd=str(tmp_path), check=True)
    feat = tmp_path / "docs" / "imp-plans" / "f"; (feat / "reports").mkdir(parents=True)
    reports = feat / "reports"
    (feat / "deviations.md").write_text("# Deviations\n")
    log = reports / ".dispatch-log"; log.write_text("# sdd-hook-sentinel abc\n")
    _impl(reports / "task-000-implementer-report.md")
    _impl(reports / "task-000-spec-review.md")
    with open(log, "a") as f:
        f.write(f"{NOW} DISPATCH reviewer task=0 type=spec-review\n")
    if min_file:
        _impl(reports / "task-000-quality-review-minimum-tier.md")
    else:
        _impl(reports / "task-000-quality-review.md")
    if provenance:
        with open(log, "a") as f:
            f.write(f"{NOW} DISPATCH reviewer task=0 type=quality-review\n")
    import sys
    sys.path.insert(0, os.path.join(ROOT, "skills", "scripts", "models"))
    from sdd_session import TIER_PROFILES
    profile = TIER_PROFILES["standard"]
    manifest = {
        "schema_version": 1, "tier": "standard",
        "paths": {"feature_dir": str(feat.relative_to(tmp_path)),
                  "reports_dir": str(reports.relative_to(tmp_path)),
                  "dispatch_log": str(log.relative_to(tmp_path)),
                  "deviations_file": str((feat / "deviations.md").relative_to(tmp_path))},
        "plan_file": str((feat / "plan.md").relative_to(tmp_path)),
        "active_module_id": 1, "active_module_file": "m1.md",
        "task_range": [0, 0], "total_tasks": 2, "midpoint": 0,
        "enforcement": profile["enforcement"], "process_requirements": profile["process_requirements"],
        "completed_modules": [], "module_reports_archived": False,
        "modules": [{"id": 1, "title": "Core", "file": "m1.md", "task_ids": [0]},
                    {"id": 2, "title": "API", "file": "m2.md", "task_ids": [1]}],
        "dispatch_log_sentinel": False,
    }
    mp = feat / ".sdd-session.json"; mp.write_text(json.dumps(manifest))
    r = subprocess.run([PYTHON, TRANSITION, "--manifest", str(mp),
                       "--completed-module", "Core", "--next-module", "API"],
                      capture_output=True, text=True, timeout=10)
    return "Task 0: quality review not provenance-logged" in r.stderr


@pytest.mark.parametrize("min_file,provenance", [(True, False), (False, False), (False, True), (True, True)])
def test_minimum_signal_agreement(tmp_path, min_file, provenance):
    hook = _hook_requires_quality_prov(tmp_path / "hook", min_file, provenance)
    trans = _transition_requires_quality_prov(tmp_path / "trans", min_file, provenance)
    assert hook == trans, (
        f"Disagreement (min_file={min_file}, provenance={provenance}): "
        f"hook_requires={hook} transition_requires={trans}")
    # Anchor the expected decision: require ONLY when no min-file AND no provenance.
    assert hook == (not min_file and not provenance)
```

- [ ] **Step 2: Run the test**

Run: `.venv/bin/python3 -m pytest tests/unit/test_ssot_minimum_agreement.py -v`
Expected: all 4 parametrized cases PASS (depends on Task 2's Check 4c and Task 3's validate_module_completion both being in place).

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_ssot_minimum_agreement.py
git commit -m "test(sdd): SSOT agreement on file-based minimum signal (D6)"
```

## CRITICAL GUARDRAILS
1. **Copy the test code EXACTLY as above.** It is verbatim from the reviewer-approved plan. Do not paraphrase, rename, or "improve" it. In particular, the two error-string needles are load-bearing and must match the real code:
   - hook: `"quality-review dispatch recorded for Task 0"` (substring of the hook's Check 4c BLOCKED message for a missing quality-review dispatch).
   - transition: `"Task 0: quality review not provenance-logged"` (substring of validate_module_completion's error).
   Both Task 2 (hook) and Task 3 (transition) are already committed, so these strings exist in the current code — confirm by grepping if unsure.
2. **TEST-ONLY:** create ONLY `tests/unit/test_ssot_minimum_agreement.py`. Do NOT modify any production script. If the test reveals a real disagreement between the two sites, STOP and report BLOCKED (do not change production code to make the test pass — that would be a real SSOT bug to escalate).
3. The 4-case truth table the test anchors (`hook == (not min_file and not provenance)`): require quality provenance ONLY when there's no minimum-tier file AND no quality provenance. (min_file=T,prov=F)→exempt; (F,F)→require; (F,T)→exempt; (T,T)→exempt. Both sites must agree on every cell.

## Context (scene-setting)
This is the D6 cross-language agreement test. The file-based minimum signal (`task-NNN-quality-review-minimum-tier.md`) is consulted by TWO independent enforcement sites in different languages: the bash hook's Check 4c (per-dispatch) and the Python `validate_module_completion` (per-transition). They were implemented separately (Tasks 2 and 3) and must never drift apart on the require/exempt decision. This test drives each via subprocess across the full present/absent matrix and asserts they reach identical decisions, anchored to the expected truth table. If they ever drift, this test fails — that is its whole purpose.

## Contract Constraints (verbatim — non-negotiable)
- Two distinct "minimum" signals — do not conflate: FILE signal `task-NNN-quality-review-minimum-tier.md` (what BOTH sites consult here) vs PLAN-DECLARATION `review_tier: minimum`. This test is about the FILE signal ONLY.
- Dispatch-log provenance line format: `<ts> DISPATCH reviewer task=<N> type=<spec-review|quality-review|partner-review>`. The test writes these lines for setup.
- Manifest is git-root-relative; resolved via `git rev-parse --show-toplevel`. The transition driver `git init`s tmp_path so the manifest's relative paths resolve.

## Source Files (read-only — READ to confirm the needles, do NOT modify)
- `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` — confirm the Check 4c BLOCKED message contains `"quality-review dispatch recorded for Task 0"` (it's `No quality-review dispatch recorded for Task $PREV`).
- `skills/subagent-driven-development/scripts/transition-module.py` — confirm `validate_module_completion` emits `Task {id}: quality review not provenance-logged`.
- `tests/unit/sdd_test_helpers.py` — confirm `make_hook_input(description=, prompt=, cwd=)` + `setup_manifest_workspace(tmp_path, tier=, task_range=, total_tasks=)` returning {root, reports_dir, ...}.

## Shared Constants
`TIER_PROFILES` imported from `sdd_session` (the test reads `profile["enforcement"]`/`["process_requirements"]`). Do NOT mutate it; the test only reads it.

## Pattern References (read before writing)
- `bash-hook-subprocess-test` → `tests/unit/test_sdd_classification.py` + `tests/unit/sdd_test_helpers.py` (the `setup_manifest_workspace`/`make_hook_input` + subprocess pattern the hook driver uses).
- `transition-test-harness` → `tests/unit/test_transition_module.py` (the manifest-dict + `run_transition` subprocess pattern the transition driver mirrors).

## Subdirectory CLAUDE.md Files
None in `tests/unit/`. Governing conventions: root CLAUDE.md.

## Before You Begin
If either error-string needle does NOT appear in the current hook/transition code (grep to check), STOP and report — the test would be vacuous. (Both should be present after Tasks 2+3.)

## Your Job
1. Read the two production scripts (confirm the needles) + sdd_test_helpers.py + a sample of each pattern reference.
2. Step 1: create the test file with the EXACT code above.
3. Step 2: run it → all 4 cases pass.
4. Step 3: commit the one file with the exact message.
5. Clean up scratch files. Self-review (confirm: test-only, no production change; needles confirmed present; 4 cases pass). Report.

## Report Format
Standard YAML frontmatter (schema_version, task_id: 4, status, files_changed, tests {written: 4 [parametrized cases], passing, command, result}, contract_compliance) then prose sections: Implementation Summary, Source Files Read, CLAUDE.md Files Read, Deviations from Plan, Self-Review Findings, Concerns. Your final message IS the report. DONE_WITH_CONCERNS if any deviations/concerns; BLOCKED if you cannot complete (esp. if the two sites disagree — that's a real bug to escalate, not to paper over).
