You are a focused implementation engineer following TDD strictly (RED → GREEN → verify). You are implementing Task 3 of the SDD Enforcement Hardening plan — the most intricate task in this plan.

Work from: `/Users/araymond/projects/claude-custom/superpowers/.worktrees/sdd-enforcement-hardening` (git worktree, branch `sdd-enforcement-hardening`).

## Task Description (VERBATIM from plan.md, Task 3)

### Task 3: transition-module.py — provenance, verification exemption, context_summary_at recompute

**Files:**
- Modify: `skills/subagent-driven-development/scripts/transition-module.py` (`validate_module_completion` + `transition()`; add two helpers)
- Modify: `tests/unit/test_transition_module.py` (update `create_task_reports` + `create_manifest`; add tests)

**Pattern References:** `verification-task-id-parser` (mirror `controller-checkpoint.py:_verification_task_ids`), `transition-test-harness`.

**Context (N3b + verification exemption + N11):** `validate_module_completion` runs at transition **Step 1**, while the live dispatch log is still intact. Extend it so that, for each completing-module task, it verifies dispatch-log provenance (the same `task=<id> type=<review>` substring Check 4c greps) — refusing to archive/truncate when provenance is missing. Quality-review provenance is **waived when the file `task-NNN-quality-review-minimum-tier.md` exists** (the *file* signal — NOT the `review_tier:minimum` plan declaration). A per-task **`task_type: verification`** exemption (mirroring the hook) skips spec/quality/provenance for verification tasks — they file an implementer report only. **N11 (folded in):** `transition()` also recomputes `enforcement.context_summary_at` for the next module so Check 6b does not fire early in later modules.

- [ ] **Step 1: Write/adjust the failing tests** in `tests/unit/test_transition_module.py`.

First, update the existing `create_task_reports` helper so existing tests keep passing (it must now also write provenance to the live log, since N3b requires it):

```python
def create_task_reports(reports_dir, task_ids):
    """Create implementer, spec-review, quality-review reports AND dispatch-log
    provenance for each task (N3b requires provenance at transition time)."""
    log = reports_dir / ".dispatch-log"
    for tid in task_ids:
        padded = f"{tid:03d}"
        for report_type in ["implementer-report", "spec-review", "quality-review"]:
            (reports_dir / f"task-{padded}-{report_type}.md").write_text(
                f"# {report_type} for task {tid}\n" + "x" * 100)
        with open(log, "a") as f:
            f.write(f"2026-06-01T00:00:00Z DISPATCH reviewer task={tid} type=spec-review\n")
            f.write(f"2026-06-01T00:00:00Z DISPATCH reviewer task={tid} type=quality-review\n")
```

Then add new tests:

```python
def test_blocks_when_provenance_missing(tmp_path):
    manifest_path, reports_dir, feat_dir = create_manifest(tmp_path)
    # Reports present but NO provenance lines (log only has the sentinel).
    for tid in [0, 1, 2, 3]:
        padded = f"{tid:03d}"
        for rt in ["implementer-report", "spec-review", "quality-review"]:
            (reports_dir / f"task-{padded}-{rt}.md").write_text(f"# {rt}\n" + "x" * 100)
    result = run_transition(manifest_path, "Core", "API")
    assert result.returncode == 1
    assert "not provenance-logged" in result.stderr


def test_minimum_tier_file_waives_quality_provenance(tmp_path):
    manifest_path, reports_dir, feat_dir = create_manifest(tmp_path)
    log = reports_dir / ".dispatch-log"
    for tid in [0, 1, 2, 3]:
        padded = f"{tid:03d}"
        (reports_dir / f"task-{padded}-implementer-report.md").write_text("# impl\n" + "x" * 100)
        (reports_dir / f"task-{padded}-spec-review.md").write_text("# spec\n" + "x" * 100)
        # Quality via the FILE signal (minimum-tier), NOT a full quality review.
        (reports_dir / f"task-{padded}-quality-review-minimum-tier.md").write_text("# min\n" + "x" * 100)
        with open(log, "a") as f:
            f.write(f"2026-06-01T00:00:00Z DISPATCH reviewer task={tid} type=spec-review\n")
            # NO quality-review provenance line — the file signal must waive it.
    result = run_transition(manifest_path, "Core", "API")
    assert result.returncode == 0, f"stderr={result.stderr}"


def test_verification_task_exempt_from_reviews(tmp_path):
    manifest_path, reports_dir, feat_dir = create_manifest(tmp_path)
    # Declare task 3 as verification in the completing module's plan file.
    (feat_dir / "m1.md").write_text(
        "---\nschema_version: 1\ntasks:\n"
        "  - id: 0\n  - id: 1\n  - id: 2\n  - id: 3\n    task_type: verification\n---\n# M1\n")
    # Tasks 0-2 full (reports + provenance); task 3 implementer report ONLY.
    create_task_reports(reports_dir, [0, 1, 2])
    (reports_dir / "task-003-implementer-report.md").write_text("# impl\n" + "x" * 100)
    result = run_transition(manifest_path, "Core", "API")
    assert result.returncode == 0, f"stderr={result.stderr}"
```

> **N11 test seed (also in Step 1):** in `create_manifest`, change `"enforcement": profile["enforcement"]` to `"enforcement": {**profile["enforcement"], "context_summary_at": 2}` (a fresh dict so the shared `TIER_PROFILES` is never mutated; `2` = module-1 midpoint). Then add to the **existing** `test_manifest_updated_after_transition`: `assert updated["enforcement"]["context_summary_at"] == 6` (module-2 midpoint — proves the N11 recompute). The verification test writes `m1.md`; the other tests leave it absent, so `_verification_task_ids_from_file` returns an empty set — backward compatible.

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python3 -m pytest tests/unit/test_transition_module.py -v`
Expected: the three new tests FAIL (no provenance enforcement yet; the verification test fails because reviews are still demanded). Existing tests PASS (helper now writes provenance).

- [ ] **Step 3: Add the two helpers** to `transition-module.py` (near `_find_module`):

```python
def _has_dispatch_provenance(dispatch_log_path: str, task_id: int, review_type: str) -> bool:
    """True if the live log has a `task=<id> type=<type>` line (mirrors hook Check 4c).
    Called at transition Step 1, before the Step 5 truncation — live log intact."""
    if not os.path.isfile(dispatch_log_path):
        return False
    needle = f"task={task_id} type={review_type}"
    try:
        with open(dispatch_log_path, encoding="utf-8") as fh:
            return any(needle in line for line in fh)
    except OSError:
        return False


def _verification_task_ids_from_file(plan_file: str) -> set:
    """task_type=='verification' IDs from a plan file's frontmatter
    (mirrors controller-checkpoint.py:_verification_task_ids)."""
    import yaml  # PyYAML available via the .venv python the hook/tests use

    if not os.path.isfile(plan_file):
        return set()
    try:
        content = Path(plan_file).read_text(encoding="utf-8")
    except OSError:
        return set()
    if not content.startswith("---"):
        return set()
    end = content.find("---", 3)
    if end == -1:
        return set()
    try:
        fm = yaml.safe_load(content[3:end])
    except Exception:
        return set()
    tasks = fm.get("tasks") if isinstance(fm, dict) else None
    if not isinstance(tasks, list):
        return set()
    return {
        t["id"]
        for t in tasks
        if isinstance(t, dict)
        and t.get("task_type") == "verification"
        and isinstance(t.get("id"), int)
    }
```

- [ ] **Step 4: Wire provenance + exemption into `validate_module_completion`.** Inside the function, after resolving `module` and `reports_dir`, add the dispatch log path and the verification-id set, then extend the per-task loop:

```python
    reports_dir = os.path.join(git_root, manifest.paths.reports_dir)
    dispatch_log = os.path.join(git_root, manifest.paths.dispatch_log)
    pr = manifest.process_requirements

    # Per-task verification exemption (mirrors sdd-pre-dispatch-hook.sh): read the
    # completing module's own plan file for task_type declarations.
    verif_ids: set = set()
    if module.file:
        module_plan = os.path.join(git_root, manifest.paths.feature_dir, module.file)
        verif_ids = _verification_task_ids_from_file(module_plan)

    for task_id in module.task_ids:
        padded = f"{task_id:03d}"
        impl_report = os.path.join(reports_dir, f"task-{padded}-implementer-report.md")
        if not os.path.isfile(impl_report) or os.path.getsize(impl_report) < 50:
            errors.append(f"Task {task_id}: missing or empty implementer report")

        if task_id in verif_ids:
            continue  # verification task: implementer report only; no spec/quality/provenance

        if pr.spec_review_mode != "skip":
            spec_report = os.path.join(reports_dir, f"task-{padded}-spec-review.md")
            if not os.path.isfile(spec_report) or os.path.getsize(spec_report) < 50:
                errors.append(f"Task {task_id}: missing or empty spec review")
            elif not _has_dispatch_provenance(dispatch_log, task_id, "spec-review"):
                errors.append(f"Task {task_id}: spec review not provenance-logged")

        if pr.quality_review_mode != "skip":
            quality_report = os.path.join(reports_dir, f"task-{padded}-quality-review.md")
            quality_min = os.path.join(reports_dir, f"task-{padded}-quality-review-minimum-tier.md")
            has_full = os.path.isfile(quality_report) and os.path.getsize(quality_report) >= 50
            has_min = os.path.isfile(quality_min) and os.path.getsize(quality_min) >= 50
            if not (has_full or has_min):
                errors.append(f"Task {task_id}: missing or empty quality review")
            elif has_min:
                pass  # file-based minimum signal waives quality-review provenance
            elif not _has_dispatch_provenance(dispatch_log, task_id, "quality-review"):
                errors.append(f"Task {task_id}: quality review not provenance-logged")

    return errors
```

Replace the existing per-task loop body with the above (it supersedes the old spec/quality file-only checks).

- [ ] **Step 5: Recompute `context_summary_at` on transition (N11).** In `transition()`'s Step 4 manifest-update block, immediately after the `data["midpoint"] = compute_midpoint(...)` line, add:

```python
    # N11: recompute context_summary_at for the new module's range. Without this
    # it stays pinned to the completed module's midpoint and Check 6b fires early
    # in later modules. Only when the tier uses it (non-null; micro leaves None).
    if data.get("enforcement", {}).get("context_summary_at") is not None:
        data["enforcement"]["context_summary_at"] = data["midpoint"]
```

- [ ] **Step 6: Run to verify pass**

Run: `.venv/bin/python3 -m pytest tests/unit/test_transition_module.py -v`
Expected: all tests PASS (existing + the 3 new provenance/verification tests + the N11 assertion on `test_manifest_updated_after_transition`).

- [ ] **Step 7: Commit**

```bash
git add skills/subagent-driven-development/scripts/transition-module.py tests/unit/test_transition_module.py
git commit -m "feat(sdd): transition provenance + verification exemption (N3b) + context_summary_at recompute (N11)"
```

## CRITICAL GUARDRAILS

1. **Step 4 REPLACES the existing per-task loop body** in `validate_module_completion` (the current loop checks impl-report + spec-review + quality-review file existence with a minimum-tier waiver). Your replacement keeps those file checks AND adds: (a) the `verif_ids` exemption (`continue` for verification tasks), (b) spec-review provenance via `_has_dispatch_provenance`, (c) quality-review provenance UNLESS the `-minimum-tier.md` FILE exists. Preserve the `pr.spec_review_mode != "skip"` / `pr.quality_review_mode != "skip"` gating exactly.
2. **The minimum waiver keys on the FILE** (`task-NNN-quality-review-minimum-tier.md` exists), NOT on `review_tier:minimum` plan declaration. Do not conflate.
3. **N11 recompute goes immediately AFTER the existing `data["midpoint"] = compute_midpoint(...)` line** (currently line ~157), guarded by `context_summary_at is not None` (micro tier leaves it None). Do NOT change the midpoint line itself.
4. **`_verification_task_ids_from_file` mirrors `controller-checkpoint.py:_verification_task_ids`** — read that function first (pattern reference) to match its frontmatter-parsing style. `import yaml` is local to the function (PyYAML is available via the .venv python that runs transition-module.py + the tests).
5. **Backward compatibility:** the verification test writes `m1.md`; the other tests do NOT, so `_verification_task_ids_from_file` returns `set()` for them — existing tests must still pass. The `create_task_reports` helper update (adding provenance) is what keeps existing transition tests green after N3b.
6. Read `transition-module.py` and `test_transition_module.py` fully before editing. Confirm: `validate_module_completion` signature `(manifest, module_name, git_root)`; `module.file`, `manifest.paths.feature_dir`, `manifest.paths.dispatch_log` exist; the `create_manifest`/`create_task_reports`/`run_transition` test harness signatures. If anything differs, STOP and report BLOCKED.
7. **N3a comment confirmation (controller request):** Task 2 added a comment in `sdd-pre-dispatch-hook.sh` stating that `validate_module_completion` "re-verifies boundary provenance at transition time." Your change (adding `_has_dispatch_provenance` checks to that function) is what makes that claim true. In your report's Self-Review, explicitly confirm that after your change, `validate_module_completion` DOES verify dispatch-log provenance for spec-review (always) and quality-review (unless minimum-tier file) — so the Task 2 comment is now accurate.

## Context (scene-setting)
`transition-module.py` manages multi-module boundary lifecycle. `validate_module_completion` (transition Step 1, BEFORE the Step 5 dispatch-log truncation — so the live log is intact) currently checks only that report FILES exist. N3b adds dispatch-log provenance verification (the sibling enforcement to Task 2's Check 4c skip-guard: when the hook skips boundary provenance because PREV is in a prior module, THIS function catches it at transition time). The verification exemption mirrors the hook's `task_type: verification` handling. N11 fixes a separate gap: `transition()` recomputes `midpoint` for the next module but NOT `context_summary_at`, so Check 6b would fire early in later modules.

## Contract Constraints (verbatim — non-negotiable)
- Dispatch-log provenance line format: `<ts> DISPATCH reviewer task=<N> type=<spec-review|quality-review|partner-review|trace-audit>`. Provenance grep keyed on substring `task=<N> type=<review_type>` (timestamp irrelevant). `_has_dispatch_provenance`'s needle `task={task_id} type={review_type}` must match this EXACTLY.
- Two distinct "minimum" signals — do not conflate: FILE `task-NNN-quality-review-minimum-tier.md` (what N3b's waiver consults) vs PLAN-DECLARATION `review_tier: minimum` (controller-checkpoint ratio only — NOT this).
- Manifest is git-root-relative; all paths resolve via git root. `MANIFEST_TASK_START = task_range[0]`.
- Module boundary lifecycle: Step 1 `validate_module_completion` (live log intact) → Step 3 archive task-NNN-* → archive-<module>/ → Step 4 manifest advance → Step 5 copy + truncate live `.dispatch-log`. Provenance MUST be checked at Step 1 (your validate_module_completion), before truncation.
- Tier review modes: `process_requirements.spec_review_mode` / `quality_review_mode` may be `"skip"` ⇒ that review type is not required (existing branching — preserve it).
- Block convention: exit 1 for validation failure (transition refuses), message `INCOMPLETE: Task N: <review> review not provenance-logged` (the `transition()` wrapper prefixes `INCOMPLETE:`; your errors append `Task N: ... not provenance-logged`).

## Source Files
None external (Source Contracts: None). READ before editing:
- `skills/subagent-driven-development/scripts/transition-module.py` (the file you modify — confirm structure per guardrail #6).
- `skills/subagent-driven-development/scripts/controller-checkpoint.py` → `_verification_task_ids` (pattern reference — mirror its YAML-frontmatter parsing).
- `tests/unit/test_transition_module.py` (the test file you modify — confirm `create_manifest`/`create_task_reports`/`run_transition` and the existing `test_manifest_updated_after_transition`).

## Shared Constants
None. (compute_midpoint is imported from `_midpoint`; TIER_PROFILES from `sdd_session` — do NOT mutate TIER_PROFILES; the N11 test seed uses a fresh dict `{**profile["enforcement"], ...}`.)

## Pattern References (read before writing)
- `verification-task-id-parser` → `skills/subagent-driven-development/scripts/controller-checkpoint.py:_verification_task_ids` — mirror the frontmatter parse for `_verification_task_ids_from_file`.
- `transition-test-harness` → `tests/unit/test_transition_module.py` — `create_manifest`/`create_task_reports`/`run_transition` multi-module subprocess setup.

## Subdirectory CLAUDE.md Files
None in the touched dirs. Governing conventions: root CLAUDE.md (single source of truth — `_midpoint.compute_midpoint` and `_verification_task_ids` patterns are the canonical references; mirror, don't reinvent). Coding style: Python type hints, snake_case, Google docstrings on public functions.

## Before You Begin
Read `transition-module.py`, `controller-checkpoint.py:_verification_task_ids`, and `test_transition_module.py` fully. If the structure differs from guardrail #6's assumptions, STOP and report BLOCKED — do not improvise.

## Your Job (TDD)
1. Read the three files above (parallel).
2. Step 1: update `create_task_reports` + `create_manifest` (N11 seed) + add the 3 new tests + the N11 assertion.
3. Step 2: run → confirm RED (3 new fail; existing pass).
4. Steps 3–5: add the two helpers; replace the validate_module_completion loop body; add the N11 recompute.
5. Step 6: run → all pass.
6. Step 7: commit both files with the exact message.
7. Clean up scratch files. Self-review (incl. guardrail #7 N3a-comment confirmation). Report.

## Report Format
Standard YAML frontmatter (schema_version, task_id: 3, status, files_changed, tests {written, passing, command, result}, contract_compliance [list]) then prose sections: Implementation Summary, Source Files Read, CLAUDE.md Files Read, Deviations from Plan, Self-Review Findings (include the guardrail #7 N3a-comment confirmation), Concerns. Your final message IS the report. DONE_WITH_CONCERNS if any deviations/concerns; BLOCKED if you cannot complete.
