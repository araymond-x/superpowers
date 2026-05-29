---
schema_version: 1
task_id: 15
review_type: quality
reviewer: senior-code-reviewer
status: APPROVE_WITH_MINOR_FIXES
---

## Strengths

- **All 3 new tests pass deterministically.** Confirmed via `pytest tests/unit/test_controller_checkpoint_stale.py -v` (11/11 PASS) and full suite (324/324 PASS).
- **Both partner-review v2 corrections applied correctly.**
  - `honesty_check_missing` matches the production check key (verified against `controller-checkpoint.py:996, 1009, 1014, 1023`).
  - `git init` in fixture aligns with `_resolve_git_root` (`controller-checkpoint.py:380`) which prefers `git -C <manifest_parent> rev-parse --show-toplevel`; without it, the script falls back to `parent.parent.parent` and double-nests `docs/`.
- **TIER_PROFILES imported from `sdd_session`, not hardcoded** (`test_controller_checkpoint_stale.py:221`). Single source of truth preserved — `enforcement` and `process_requirements` fields in the manifest fixture both flow from `profile`, not literal dicts.
- **`SCRIPT_PATH` aliased rather than duplicated** (`test_controller_checkpoint_stale.py:210`). Sound SSOT decision — both constants would point to the same file; aliasing prevents drift.
- **Test isolation is correct.** Each test receives a fresh `tmp_path` (pytest's per-test fixture). `git init -q` runs in the test's own tmp_path, no cross-test contamination.
- **Subprocess timeout (15s)** matches the plan and is reasonable for these subprocess invocations.
- **Strong assertion in `test_micro_tier_skips_honesty_check`** — verifies `checks["honesty_check_missing"].status == "SKIP"`. This is the test that proves manifest-driven tier dispatch works end-to-end.
- **Helper docstring on `setup_checkpoint_workspace`** explains the `git init` rationale and cross-references the related `test_transition_module.py` precedent. Future maintainers will know why.
- **All 6 deviation rows are justified** with sound reasoning; deviation row 29 (ForwardConcern from Task 14) is marked Resolved.
- **No dead code or scratch files in the diff.** The diff is +135 lines, all functional.

## Issues

### Critical

None.

### Important

None.

### Minor

- **Weak assertions in 2 of 3 tests** (`test_controller_checkpoint_stale.py:307, 338`). Both `test_manifest_overrides_plan_file` and `test_backward_compat_without_manifest` rely on the negative assertion `result["exit_code"] != 3`. This proves the script didn't crash on plan-file resolution, but doesn't actually verify:
  - That the manifest was the source of `plan_file` (not the absent `--plan-file` arg).
  - That `--plan-file` mode produces identical behavior to manifest mode.

  The implementer flagged this in their Concerns section. The plan's reference code specified this shape verbatim, so retaining it is acceptable. A strengthening pass could read `result["output"]["checks"]["plan_file"]["detail"]` and assert it contains the manifest-resolved path, or assert a stale-artifact warning fires in clean workspaces to prove the script reached the relevant check. Log only — recommend follow-up but not blocking.

- **Redundant `sys.path.insert` block** (`test_controller_checkpoint_stale.py:217-220`). `conftest.py` already adds `skills/scripts/models` to `sys.path` (verified — see `tests/unit/conftest.py:6-9`). The duplicate insert is functionally a no-op (idempotent) and the inline comment acknowledges it ("matches test_transition_module.py pattern"). Acceptable for cross-file consistency, but worth flagging for any future cleanup pass that consolidates test-file imports.

- **Plan checklist boxes for Task 15 left unchecked** in `module-3-transitions-and-checkpoint.md:511, 628, 636`. The plan's Step 1/2/3 boxes for Task 15 are still `- [ ]` rather than `- [x]`. Not a code issue, but breaks the plan-state convention used by Tasks 12-14 (all marked `- [x]`). Suggest tightening as a tidy-up.

### Needs Context

None — all observed behavior was verifiable against script source and conftest.

## Architectural Alignment

- **Single source of truth: PASS** — `TIER_PROFILES[tier]` drives `enforcement` and `process_requirements` in the fixture. `SCRIPT_PATH` aliased rather than duplicated. No hardcoded tier dicts.
- **Dead code: PASS** — No unused imports detected. `import pytest` was deliberately omitted from the new section (deviation logged). All new helpers and the `TestManifestMode` class are exercised. The duplicate `sys.path.insert` is idempotent but acknowledged.
- **Audit-all-callers on refactor: N/A** — no production code refactored.
- **Config on entity: N/A** — test-only change.

## Assessment

APPROVE_WITH_MINOR_FIXES

The Task 15 implementation is correct, well-documented, and meets all plan acceptance criteria. Both partner-review v2 mandates (`honesty_check_missing` key correction and `git init` in fixture) were applied properly with detailed deviation justifications. The single substantive concern — weak negative assertions in 2 of 3 tests — was flagged by the implementer and is constrained by the plan's reference code. It is acceptable to merge as-is because the third test (`test_micro_tier_skips_honesty_check`) exercises the manifest-driven tier branch with a strong positive assertion, proving the manifest end-to-end pipeline works.

Recommended (non-blocking) follow-ups:
1. Strengthen the two weak assertions to verify manifest provenance (read `plan_file` from `checks["plan_file"]["detail"]` or assert a stale-artifact warning is produced in the manifest path).
2. Mark Task 15 checkboxes in `module-3-transitions-and-checkpoint.md` as `[x]` for plan-state consistency.
3. (Tracked separately, deferred via deviation row 30) Consolidate `setup_checkpoint_workspace` / `create_manifest` / `setup_manifest_workspace` post-Module-4.
