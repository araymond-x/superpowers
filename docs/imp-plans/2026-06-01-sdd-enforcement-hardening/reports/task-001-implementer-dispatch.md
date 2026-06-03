You are a focused implementation engineer following TDD strictly (RED → GREEN → verify). You are implementing Task 1 of the SDD Enforcement Hardening plan.

Work from: `/Users/araymond/projects/claude-custom/superpowers/.worktrees/sdd-enforcement-hardening` (git worktree, branch `sdd-enforcement-hardening`).

## Task Description (VERBATIM from plan.md, Task 1)

### Task 1: Archive-aware report lookups in controller-checkpoint.py

**Files:**
- Modify: `skills/subagent-driven-development/scripts/controller-checkpoint.py` (`find_report_file`, `find_all_report_files`)
- Test: `tests/unit/test_checkpoint_archive_aware.py` (create)

**Context (N4):** After a module transition, the completed module's reports live under `reports/archive-<module>/`. The pre-completion gate (Check 3 `all_tasks_have_reports`, Check 4 `all_reports_complete`) calls these two functions and currently only globs the flat `reports_dir`, so it FAILs once a module is archived. Make exactly these two functions recurse into `archive-*/`. **Read the "Intentionally Flat" section below — do not touch any other lookup.** `sorted(matches)[-1]` makes the **live** copy win when a report exists in both (`reports/task-000-...` sorts after `reports/archive-*/task-000-...`).

- [ ] **Step 1: Write the failing tests** in `tests/unit/test_checkpoint_archive_aware.py`

```python
"""N4: controller-checkpoint.py find_report_file/find_all_report_files recurse into archive-*/.
Run: .venv/bin/python3 -m pytest tests/unit/test_checkpoint_archive_aware.py -v
"""
import importlib.util
import os

_SPEC = importlib.util.spec_from_file_location(
    "controller_checkpoint",
    os.path.join(os.path.dirname(__file__), "..", "..",
                 "skills", "subagent-driven-development", "scripts", "controller-checkpoint.py"),
)
cc = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(cc)


def _impl(p):
    p.write_text("x" * 80)


def test_find_report_file_in_archive(tmp_path):
    reports = tmp_path / "reports"; reports.mkdir()
    arch = reports / "archive-Core"; arch.mkdir()
    _impl(arch / "task-000-implementer-report.md")
    assert cc.find_report_file(str(reports), 0).endswith("archive-Core/task-000-implementer-report.md")


def test_find_report_file_prefers_live_over_archive(tmp_path):
    reports = tmp_path / "reports"; reports.mkdir()
    arch = reports / "archive-Core"; arch.mkdir()
    _impl(arch / "task-000-implementer-report.md")
    _impl(reports / "task-000-implementer-report.md")
    # Live copy must win (sorts last).
    assert cc.find_report_file(str(reports), 0) == str(reports / "task-000-implementer-report.md")


def test_find_all_report_files_includes_archive(tmp_path):
    reports = tmp_path / "reports"; reports.mkdir()
    arch = reports / "archive-Core"; arch.mkdir()
    _impl(arch / "task-000-implementer-report.md")
    _impl(reports / "task-002-implementer-report.md")
    found = cc.find_all_report_files(str(reports))
    bases = sorted(os.path.basename(f) for f in found)
    assert bases == ["task-000-implementer-report.md", "task-002-implementer-report.md"]


def test_detect_stale_artifacts_stays_flat(tmp_path):
    # Regression: archived reports must NOT trip the pre-execution stale scan.
    reports = tmp_path / "reports"; reports.mkdir()
    arch = reports / "archive-Core"; arch.mkdir()
    _impl(arch / "task-000-implementer-report.md")
    dev = tmp_path / "deviations.md"; dev.write_text("")  # empty = no content
    result = cc.detect_stale_artifacts(str(dev), str(reports))
    assert result["status"] == "OK", result
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python3 -m pytest tests/unit/test_checkpoint_archive_aware.py -v`
Expected: `test_find_report_file_in_archive` and `test_find_all_report_files_includes_archive` FAIL (flat glob misses archive); the other two PASS (already correct).

- [ ] **Step 3: Make the two lookups archive-aware.** Replace `find_report_file` and `find_all_report_files`:

```python
def find_report_file(reports_dir: str, task_number: int) -> str:
    """Return the path to the implementer report for the given task, or "" if not found.

    Searches the live reports dir AND archived module dirs (reports/archive-*/).
    When a report exists in both, the live copy wins (sorts last). N4.
    """
    pattern = report_filename_pattern(task_number)
    matches = glob.glob(os.path.join(reports_dir, pattern))
    matches += glob.glob(os.path.join(reports_dir, "archive-*", pattern))
    return sorted(matches)[-1] if matches else ""


def find_all_report_files(reports_dir: str) -> list:
    """Return all implementer report files, live AND archived (reports/archive-*/). N4."""
    pattern = "task-*-implementer-report*"
    matches = glob.glob(os.path.join(reports_dir, pattern))
    matches += glob.glob(os.path.join(reports_dir, "archive-*", pattern))
    return sorted(matches)
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python3 -m pytest tests/unit/test_checkpoint_archive_aware.py -v`
Expected: all 4 PASS.

- [ ] **Step 5: Confirm no regression in the existing pre-completion suite**

Run: `.venv/bin/python3 -m pytest tests/unit/test_pre_completion_gates.py tests/unit/test_controller_checkpoint_stale.py -v`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add skills/subagent-driven-development/scripts/controller-checkpoint.py tests/unit/test_checkpoint_archive_aware.py
git commit -m "feat(sdd): archive-aware implementer-report lookups in controller-checkpoint (N4)"
```

## CRITICAL GUARDRAIL — "Intentionally Flat" (VERBATIM from plan; scope boundary)

The spec scopes archive-awareness to **EXACTLY TWO** lookups: this task's `find_report_file`/`find_all_report_files` (N4). **Every other report glob stays flat BY DESIGN.** Making any of the following archive-aware is **expanding scope past the approved spec and introducing a bug** — do NOT touch them:

- `controller-checkpoint.py` → `detect_stale_artifacts` (pre-execution stale scan — must NOT see archived reports, or it would warn forever). **There is a regression test (`test_detect_stale_artifacts_stays_flat`) proving this stays flat — it must keep passing.**
- `controller-checkpoint.py` → `_review_tiers_per_task` (Check 7 minimum-tier ratio — flat by spec).
- `controller-checkpoint.py` → `_check_verification_git_reality`'s dispatch-log read (Check 9 — reads the live log only).
- `sdd-pre-dispatch-hook.sh` → Check 3b and Check 7 (NOT your file anyway).

Change ONLY `find_report_file` and `find_all_report_files`. Nothing else in controller-checkpoint.py.

## Context (scene-setting)
`controller-checkpoint.py` is the controller's discipline checkpoint (pre-execution / pre-dispatch / pre-completion). `find_report_file(reports_dir, task_number)` and `find_all_report_files(reports_dir)` are called by Check 3 (`all_tasks_have_reports`), Check 4 (`all_reports_complete`), and `estimate_context_load`. Today they glob only the flat `reports_dir`. After a multi-module transition, completed-module reports are archived to `reports/archive-<module>/`, so these lookups miss them and the pre-completion gate FAILs. N4 makes exactly these two recurse into `archive-*/`, with the LIVE copy winning when a report exists in both.

## Contract Constraints (verbatim — non-negotiable)
- Dispatch-log provenance line format: reviewer `<ts> DISPATCH reviewer task=<N> type=<...>`; implementer `<ts> DISPATCH implementer task=<N> type=implementer`.
- Two distinct "minimum" signals — do not conflate (FILE `task-NNN-quality-review-minimum-tier.md` vs PLAN-DECLARATION `review_tier: minimum`).
- Manifest is git-root-relative; `MANIFEST_TASK_START = task_range[0]`.
- Module boundary lifecycle: Step 1 validate → Step 3 archive `task-NNN-*` → `reports/archive-<module>/` → Step 4 advance → Step 5 truncate. Live log intact during Step 1.
- Tier review modes: spec_review_mode / quality_review_mode may be "skip".
- Block convention: exit 2 + stderr. Bypass mirrors SUPERPOWERS_VALIDATOR_BYPASS.
- **Archive-awareness applies to EXACTLY two lookups** — this task's two functions (N4). All other globs stay flat (see Intentionally Flat above).

If your implementation contradicts any constraint, STOP and report BLOCKED.

## Source Files
None (Source Contracts: None). But READ `skills/subagent-driven-development/scripts/controller-checkpoint.py` before editing — confirm the current `find_report_file`/`find_all_report_files` bodies, that `glob` and `os` are already imported, and that `report_filename_pattern(task_number)` exists and returns the pattern used by `find_report_file`. Also confirm `detect_stale_artifacts` exists (the regression test calls it). Verify by reading — do not assume.

## Shared Constants
None.

## Pattern References
None specific to this task. Mirror the existing style of the surrounding functions in `controller-checkpoint.py` (the replacement snippets above already match that style — `glob.glob(os.path.join(...))`, `sorted(...)`).

## Subdirectory CLAUDE.md Files
None in `skills/subagent-driven-development/scripts/` or `tests/unit/`. Governing conventions: root CLAUDE.md. Note especially: `_report_utils.py` is the single source of truth for report parsing — do NOT duplicate report-parsing logic; and the architectural principle "single source of truth."

## Before You Begin
If `report_filename_pattern` doesn't exist or behaves differently than the snippet assumes, or if `glob`/`os` aren't imported, STOP and report (do not silently restructure). Ask if anything is unclear.

## Your Job (TDD)
1. Read `controller-checkpoint.py` (the two target functions + `detect_stale_artifacts` + confirm `report_filename_pattern`, `glob`, `os`).
2. Step 1: write the 4 tests exactly as above.
3. Step 2: run → confirm RED (2 fail, 2 pass).
4. Step 3: replace ONLY the two functions with the archive-aware versions.
5. Step 4: run → 4 pass.
6. Step 5: run the regression suites (`test_pre_completion_gates.py`, `test_controller_checkpoint_stale.py`) → all pass.
7. Step 6: commit BOTH files with the exact message.
8. Clean up scratch files. Self-review (esp. that you touched NOTHING outside the two functions). Report.

## Report Format
Standard YAML frontmatter (schema_version, task_id: 1, status [DONE|DONE_WITH_CONCERNS|BLOCKED|NEEDS_CONTEXT], files_changed, tests {written, passing, command, result: PASS|FAIL}, contract_compliance [list of {constraint, status, detail}]) then prose sections: Implementation Summary, Source Files Read, CLAUDE.md Files Read, Deviations from Plan, Self-Review Findings, Concerns. Your final message IS the report (saved + validated). Use DONE_WITH_CONCERNS if any deviations/concerns; BLOCKED if you cannot complete.
