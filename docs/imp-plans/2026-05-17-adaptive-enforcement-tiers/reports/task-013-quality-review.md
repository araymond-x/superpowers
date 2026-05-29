# Task 13 — Quality Review

**Reviewer:** Senior Code Reviewer (subagent)
**Scope:** `tests/unit/test_transition_module.py`, deviations.md row 13
**Range:** `4001c4b..e16d9d8`
**Verification:** 7/7 tests PASS; full unit suite 321/321 PASS; AST scan confirms zero unused imports.

## Strengths

- **Faithful to plan reference.** All 7 test names, helper signatures, and assertion patterns match the plan's reference code byte-for-byte (modulo the empirically-required `git init`). The plan-prescribed `CRITICAL: Git Root Requirement` block was correctly diagnosed and applied.
- **`TIER_PROFILES` imported, not inlined.** Honors the project's single-source-of-truth rule — the manifest profile (`enforcement` + `process_requirements`) is read live from `sdd_session.py` rather than redeclared. Future tier-config edits will be picked up by this test for free.
- **Real-behavior testing.** Tests invoke the real `transition-module.py` as a subprocess (no mocks), exercising the actual git-root resolution, manifest update, archival, and deviations append. This is the right approach for a CLI script.
- **Reasonable assertion specificity.** Each test asserts on return code AND a substantive observable (stdout/stderr substring, file existence, JSON field, archive contents) rather than just the exit code.
- **Test isolation is sound.** Each test takes a fresh `tmp_path` from pytest; no shared mutable state; no machine-specific paths beyond `tmp_path`.
- **Linter-pass cleanup applied.** The implementer report flagged dormant `tempfile`/`pytest` imports from the plan reference; the pre-commit linter removed them. AST scan of the committed file confirms zero unused imports remain — concern self-resolved before merge.
- **Deviation properly logged.** Row 13 in `deviations.md` is well-written: explains the empirical failure mode (exit 2, "Cannot determine git root"), references the script line range (115–123), justifies the fix, and points at the analogous `setup_manifest_workspace` pattern in `sdd_test_helpers.py`. Status correctly set to "Accepted".
- **Subprocess timeout is reasonable** at 10s — matches `test_controller_checkpoint_stale.py` precedent and is generous for a script that does a few file ops.

## Issues

### Critical
- None.

### Important
- None.

### Minor

- **Helper duplication with `setup_manifest_workspace`** (`tests/unit/test_transition_module.py:36-81` vs `tests/unit/sdd_test_helpers.py:313`). The new `create_manifest` helper duplicates ~80% of what `setup_manifest_workspace` already does: `git init`, feature/reports dir layout, TIER_PROFILES-driven manifest construction, dispatch log seed. The duplication is functionally correct, but it's a second source of truth for "what does a valid SDD workspace look like." A follow-up could refactor `create_manifest` to call `setup_manifest_workspace` and add only the bits specific to transition-module (the `modules` array, the simpler return tuple). Not blocking for Task 13 because the plan reference explicitly inlined this helper and changing it would expand scope, but flag for the same post-Module-4 refactor pass already noted in deviations row 12 (`ForwardConcern: compute_midpoint duplication`).

- **`test_rejects_single_module_plan` asserts only on return code** (`tests/unit/test_transition_module.py:152-159`). Unlike `test_blocks_when_reports_missing` (which checks for `"INCOMPLETE"` in stderr), this test does not verify *why* the script rejected the manifest. If a future regression caused the same return code 1 for a different reason (e.g., a manifest schema-validation failure), this test would still pass. Recommend adding `assert "Not a multi-module plan" in result.stderr` (matches the script's actual stderr at line 111). One-line fix, increases regression-protection precision.

- **`test_deviations_log_updated` could assert on row format, not just substring** (`tests/unit/test_transition_module.py:161-166`). The current `assert "Module transition" in devs` would pass even if the row's pipe-delimited format broke. A stricter assertion like `assert "Module transition: Core → API" in devs` or checking the row starts with `|` would catch format regressions. Low priority — the existing assertion still catches the most likely failure mode (no append at all).

- **No assertion that `module_reports_archived` flag is set to `True`** after transition (the script sets this at line 167). It's part of the manifest state contract and currently untested. Could be added as a one-line assertion in `test_manifest_updated_after_transition`.

### Needs Context

- **`test_dispatch_log_archived_and_truncated` reads the archived log content but doesn't verify the archived content matches what was there before truncation** (`tests/unit/test_transition_module.py:137-143`). The test confirms (a) archive file exists and (b) live log is empty. It does not confirm that the archive preserved the pre-truncation content (`"# sdd-hook-sentinel abc123\n"`). The script uses `shutil.copy2` followed by truncate, so this is the right order — but if a refactor accidentally swapped the order (truncate first, then copy), the archive would be empty and this test would still pass. Adding `assert "sdd-hook-sentinel" in (archive / ".dispatch-log").read_text()` would close that loophole. Whether this counts as Minor or Important depends on how likely such a refactor is — probably Minor in practice.

## Architectural Alignment

- **Single source of truth: PASS.** `TIER_PROFILES` is imported, not redeclared. The `create_manifest` helper duplicates *layout* code with `setup_manifest_workspace`, but not *logic* — both helpers compute the same answer from the same imported constants. Logged as a Minor concern with a deferred-refactor recommendation, consistent with how deviation row 12 handled the `compute_midpoint` duplication.

- **Dead code: PASS.** AST scan confirms zero unused imports. The implementer's pre-commit concern about `tempfile` and `pytest` imports was resolved by the linter pass before the commit landed. No unreachable branches or dead helpers in the test file.

- **`git init` is correct as a test-side fix.** Production usage always operates inside a git repo (the SDD pipeline only invokes `transition-module.py` from a feature directory committed to the repo). Patching the script to handle missing git would add complexity for a non-real scenario. The pattern matches `setup_manifest_workspace` in `sdd_test_helpers.py`. This is the right boundary.

## Assessment

**APPROVE_WITH_MINOR_FIXES**

The implementation is solid, the deviation is well-justified and well-documented, tests pass, full suite is green, and architectural principles are honored. The Minor items above are all polish — none of them block merging.

Optional follow-ups (controller's discretion):
1. Strengthen `test_rejects_single_module_plan` with a stderr substring assertion (one-line fix).
2. Add `module_reports_archived == True` to `test_manifest_updated_after_transition` (one-line fix).
3. Strengthen `test_dispatch_log_archived_and_truncated` to verify archive content survived truncation.

The `create_manifest` / `setup_manifest_workspace` duplication should be tracked alongside the existing `compute_midpoint` duplication (deviations row 12) for the post-Module-4 refactor pass — not addressed in Task 13.
