# Task 12 — Quality Review (Code Review)

**Reviewer:** Senior Code Reviewer (general-purpose)
**Task:** 12 — Transition-Module Script
**File under review:** `skills/subagent-driven-development/scripts/transition-module.py`
**Git range:** `d21df59..a01cab2`
**Plan reference:** `docs/imp-plans/2026-05-17-adaptive-enforcement-tiers/module-3-transitions-and-checkpoint.md`, Task 12
**Implementer report:** `reports/task-012-implementer-report.md` (status: DONE_WITH_CONCERNS)

## Strengths

- **Bug-fix discipline.** The plan reference code contained a midpoint bug (`range_size = end - start + 1`) that would have produced midpoints outside `task_range` for single-task ranges, failing `SddSession.midpoint_in_range`. The implementer caught it, corrected to Module 1's authoritative formula, logged a deviation row (row 14) with cross-references to the earlier occurrences (Tasks 4 and 11), and pulled the formula into a named `compute_midpoint(start, end)` helper with a docstring. This is exactly the right behaviour — fixing the bug, documenting it, and making the fix legible to future readers.
- **Defensive error handling improves on plan.** The plan reference code called `json.loads(...)` and `SddSession.model_validate(...)` bare. The implementer wrapped each in try/except mapped to the documented exit codes (2 for JSON/IO parse failure, 1 for Pydantic validation failure). This aligns the runtime with the docstring exit-code contract instead of letting tracebacks leak.
- **Helper extraction.** `_find_module(modules, name_or_id)` deduplicates a three-times-repeated loop in the plan reference (lines 115-119, 183-186, 197-200). This is sensible without being over-engineered.
- **Modern type syntax.** Uses `list[ModuleState]`, `ModuleState | None`, `list[str]` per the project's coding-style rules. No legacy `typing.List` / `typing.Optional` imports.
- **All imports used.** `datetime`, `timezone`, `ModuleState` (type hint), `SddSession` (type hint + validator), `subprocess`, `shutil`, `json`, `argparse`, `sys`, `os`, `Path` — verified via grep. No dead imports.
- **Path semantics correctly honored.** The `ArtifactPaths` model documents paths as git-root-relative. The script consistently joins them with `git_root` derived via `git -C <manifest_dir> rev-parse --show-toplevel`. Tracing `manifest.paths.dispatch_log` (git-root-relative) → `os.path.join(git_root, ...)` → `shutil.copy2(...)`/`open(...)` to absolute targets is type-consistent.
- **End-to-end smoke test verified during review.** Reviewer reproduced the happy path on a temp git repo: manifest transitioned Core→API, all 12 reports archived to `archive-Core/`, dispatch log copied + truncated, deviations.md row appended, manifest's `active_module_id=2`, `task_range=[4,7]`, `midpoint=6`, `completed_modules=["Core"]`, `module_reports_archived=true`. Validation failure path also verified (exit 1, `INCOMPLETE: ...` rows on stderr).
- **Midpoint correction verified empirically.** `compute_midpoint(1,1)=1` (in range); buggy formula would have produced 2 (out of range, Pydantic failure). All other tested ranges `(0,1), (3,4), (1,5), (1,6), (4,7), (0,3)` produce in-range values.
- **Executable bit set** (`-rwxr-xr-x`), matching the script convention of sibling files.

## Issues

### Critical
- None.

### Important
- None.

### Minor

- **`completed_module == next_module` is not rejected.**
  `transition-module.py:91-187`
  When the same module name is passed for both arguments, the script archives Core's reports, then leaves the manifest with `active_module_id=1`, `active_module_file="m1.md"`, `completed_modules=["Core"]`, and `module_reports_archived=true` — i.e., the active module is also in `completed_modules` and its reports have all been archived away. This is a self-contradictory state that the user can put the manifest into by typo'ing the arguments. Reviewer verified this on /tmp/transition-test (exit 0). A one-line guard before archival would prevent it:
  ```python
  if completed_module == next_module:
      print(f"completed-module and next-module must differ", file=sys.stderr)
      return 1
  ```
  Not blocking — this is an operator-error edge case, not a contract violation — but a low-cost guard.

- **`shutil.move` collides if archive already contains a same-named report.**
  `transition-module.py:155`
  `shutil.move(str(f), os.path.join(archive_dir, f.name))` raises `shutil.Error` (script crashes with uncaught traceback, exit 1 via Python's default uncaught-exception behavior, but not the documented "validation failure" semantics) if the destination file exists — e.g., if a previous transition partially completed and left files in `archive-Core/`. The plan does not require idempotency, and `os.makedirs(archive_dir, exist_ok=True)` (line 151) is the existing accommodation. Flag for future hardening rather than a Task 12 fix.

- **No defensive check that `next_mod` follows `completed_mod` in module order.**
  `transition-module.py:133-145`
  The script accepts any next module name that exists in the manifest's `modules` list — including modules earlier than the completed one, or completed modules. This is intentional flexibility but unguarded. A `next_mod.id > completed_mod.id` (or `next_mod not in completed_modules`) assertion would catch a controller misdirection. Acknowledge-and-defer is fine here; flagging for future review.

- **Top-level docstring exit-code list is missing exit-code 1 sub-cases.**
  `transition-module.py:8-12`
  Exit 1 happens for (a) missing/empty reports, (b) `manifest.modules is None`, (c) `next_module` not found, (d) `completed_module` not found post-validation, AND (e) Pydantic validation failure on existing manifest. The docstring mentions only "missing reports, module not found". Documentation polish, not a bug.

- **`_find_module` permits string-or-int comparison ambiguity for synthetic IDs.**
  `transition-module.py:29-34`
  `m.title == name_or_id or str(m.id) == name_or_id` correctly matches both title and stringified ID. Edge case: a module with `title="2"` and a module with `id=2` would both match `name_or_id="2"`, and `_find_module` returns the first. Not a real-world concern given the manifest schema, but flag for awareness.

### Needs Context

- **Should `compute_midpoint` be imported from `materialize-manifest.py` instead of duplicated?**
  `transition-module.py:37-46` vs `materialize-manifest.py:58-65`
  Both functions are identical in formula and intent. Per Aaron's architectural rule "single source of truth for logic," this is duplication. Two competing considerations:
  - (a) Importing across `scripts/` siblings would require either a shared `_helpers.py` module or sys.path gymnastics; both add coupling for a 2-line function.
  - (b) The midpoint formula has *already* been the source of three regressions (Tasks 4, 11, 12 deviation rows). If a fourth caller needs the formula and copies it again, the bug count rises with `O(N)` instead of `O(1)`.
  Resolution would benefit from input from whoever owns Module 1's authoritative compute_midpoint. Reasonable options: extract to `skills/subagent-driven-development/scripts/_helpers.py` and import from both; or move to `skills/scripts/models/sdd_session.py` as a module-level helper (it is intrinsically tied to `task_range` semantics defined there). Either is a small, separate refactor.

- **`Path.glob('task-{padded}-*')` boundary.**
  `transition-module.py:154`
  Implementer correctly noted in the report that `task-001-*` will not match `task-0010-*` due to the dash boundary. This is correct for task IDs < 1000. The codebase appears to assume task IDs fit `:03d` padding (i.e., < 1000) throughout — confirmed by `f"{task_id:03d}"` usage in `validate_module_completion` and elsewhere. If the project ever exceeds 999 tasks per feature, the padding (and this glob) need a re-think.

## Architectural Alignment

- **Single source of truth for logic: PARTIAL (see Needs Context).** `compute_midpoint` is duplicated in `materialize-manifest.py:compute_midpoint` and `transition-module.py:compute_midpoint`. The implementer's docstring explicitly notes the duplication and points to Module 1's "authoritative" version, which is honest but does not resolve the principle violation. The midpoint formula has triggered three deviation rows already, which is empirical evidence that duplication has cost.
- **Dead code: PASS.** All imports used (verified). No commented-out code. No unreachable branches (the implementer's "should not happen" comment at line 140 is a defensive guard that correctly returns exit 1; not unreachable, just unlikely).
- **Fix the architecture, not just the symptom: PARTIAL.** The implementer fixed the midpoint bug in *this* file and logged a deviation row noting that the plan source contains the bug — but the buggy plan reference code remains in `module-3-transitions-and-checkpoint.md` line 211 and (per deviation rows) in module-2 lines 40-42. A future regen or copy from those plan files will produce the bug again. Out of scope for Task 12, but the plan author should mass-correct.
- **Migrations and code deploy together: N/A.** No schema or migration concerns; new file with no callers (will be invoked by hooks/controllers in subsequent tasks).
- **Automated gate FAILs are never "expected": N/A.** No validator/linter gate failures encountered.

## Plan Alignment

| Plan Requirement | Status | Notes |
|---|---|---|
| Validate completion (impl/spec/quality reports >=50 bytes, honor tier skip flags) | PASS | `validate_module_completion` honors both `spec_review_mode != "skip"` and `quality_review_mode != "skip"`; quality check accepts either standard or `-minimum-tier` suffix variant. |
| Archive reports to `reports/archive-{module-name}/` | PASS | `os.makedirs(..., exist_ok=True)` + `shutil.move` for each task glob. Verified end-to-end. |
| Update manifest: `active_module_id`, `active_module_file`, `task_range`, `midpoint`, `completed_modules` (append), `module_reports_archived=True` | PASS | All six fields updated. `setdefault("completed_modules", []).append(...)` guards duplicate appends. |
| Archive dispatch log (copy + truncate live) | PASS | `shutil.copy2` to `archive_dir/.dispatch-log`, `open(..., "w").close()` to truncate. Verified end-to-end. |
| Append transition row to `deviations.md` with timestamp | PASS | ISO-8601 UTC timestamp, `Module transition: X → Y` row. Verified end-to-end. |
| Use Pydantic `SddSession` model | PASS | `SddSession.model_validate(data)` wraps the raw dict, validation failures caught and routed to exit 1. |
| Exit codes: 0/1/2 | PASS | All three paths exercised. |
| Argparse `--manifest`, `--completed-module`, `--next-module` | PASS | All required. |

## Production Readiness

- **No backward-compatibility issues.** New file, no existing callers.
- **No migration concerns.** No schema/data changes.
- **Documentation.** Module docstring with exit codes (good). `compute_midpoint` has a useful docstring referencing the precedent. `validate_module_completion` and `transition` have one-line docstrings (acceptable for internal helpers; could be expanded for `transition` since it is the script's main entry point — minor).
- **Test coverage.** Zero automated tests in this commit. Per the plan, tests are Task 13. Reviewer ran a comprehensive smoke test that confirmed: happy path, validation-failure path (exit 1 + stderr `INCOMPLETE:` rows), archive contents, dispatch log truncation, deviations row format, manifest mutation correctness. This stands in until Task 13 lands.

## Assessment

**APPROVE_WITH_MINOR_FIXES**

The implementation is correct, faithfully follows the plan (with one justified, well-documented bug fix), uses the right Pydantic model, honors path conventions, and has clean error handling. The smoke-test evidence is solid: reviewer independently reproduced all six steps and verified the corrected midpoint formula on edge cases.

The two recommended minor fixes are:
1. Guard `completed_module == next_module` with an explicit error path (3 lines).
2. Resolve the `compute_midpoint` duplication with Module 1 — either extract to a shared helper or import. The midpoint formula already has three deviation rows; one more reinforces the case for de-duplication. Even a brief follow-up task with explicit owner would close out the "single source of truth" concern.

Neither blocks Task 13 or downstream module work. The current code is safe to land; the fixes can ship as a small follow-up.
