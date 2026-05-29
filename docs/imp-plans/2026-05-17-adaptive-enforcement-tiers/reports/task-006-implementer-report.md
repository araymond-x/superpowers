---
schema_version: 1
task_id: 6
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh"
    description: "Added manifest-based path resolution block after cd $CWD (lines 63-99), initialized all new variables (MANIFEST, MANIFEST_MODE, GIT_ROOT, FEAT, DEVIATIONS_FILE, REPORTS_DIR, DISPATCH_LOG, MANIFEST_TIER, MANIFEST_TASK_START, MANIFEST_TASK_END, MANIFEST_PLAN_FILE, MANIFEST_MODULE_FILE) before any conditional read, and wrapped the existing legacy CWD-relative path resolution block in an if [ MANIFEST_MODE = false ] guard."
tests:
  written: 0
  passing: 0
  command: ".venv/bin/python3 -m pytest tests/unit/test_sdd_hard_gates.py -v -x"
  result: PASS
contract_compliance:
  - constraint: "Hook resolves .active-feature from git rev-parse --show-toplevel (CWD-stable)"
    status: compliant
    detail: "GIT_ROOT set via `git rev-parse --show-toplevel 2>/dev/null || echo \"\"`. .active-feature is then read from $GIT_ROOT/.active-feature, not from $CWD."
  - constraint: "Hook reads manifest from $GIT_ROOT/$FEAT/.sdd-session.json"
    status: compliant
    detail: "MANIFEST set to $GIT_ROOT/$FEAT_FROM_ROOT/.sdd-session.json after confirming the file exists."
  - constraint: "All artifact paths come from manifest's paths object"
    status: compliant
    detail: "DEVIATIONS_FILE, REPORTS_DIR, and DISPATCH_LOG all read via jq from .paths.deviations_file, .paths.reports_dir, and .paths.dispatch_log respectively, prefixed with $GIT_ROOT/."
  - constraint: "Legacy regex path preserved behind manifest-absence check"
    status: compliant
    detail: "Entire legacy block (FEAT from .active-feature, feat_path helper, artifact resolution with old-layout fallbacks) is preserved unchanged inside if [ \"$MANIFEST_MODE\" = false ]; then ... fi."
---

**Implementation Summary:**
Added a manifest-based path resolution block to `sdd-pre-dispatch-hook.sh` immediately after `cd "$CWD" || exit 0`. When a `.sdd-session.json` manifest exists in the feature directory (located via `git rev-parse --show-toplevel`), all artifact paths are read from the manifest's `paths` object using CWD-stable git-root-relative resolution. The existing legacy CWD-relative path resolution is preserved unchanged behind a `MANIFEST_MODE=false` guard. All new variables are initialized at the top of the new block to satisfy `set -uo pipefail` semantics.

**Regression Test Result:** No new tests written for this task (manifest-mode tests live in Task 11). Verified all 16 pre-existing `test_sdd_hard_gates.py` tests still PASS — these exercise the legacy branch and would catch any regression in the wrapping. `tests.written=0` and `tests.passing=0` in the schema reflect new-test count; the regression-verification command and PASS result are captured in the `tests` block.

**Source Files Read:**
- `skills/scripts/models/sdd_session.py` — Confirmed manifest field names: `SddSession.tier`, `SddSession.paths.{feature_dir,reports_dir,dispatch_log,deviations_file}`, `SddSession.plan_file`, `SddSession.active_module_file` (bare filename per Module 1 deviation #2), `SddSession.task_range` (tuple[int,int]). Also confirmed `TIER_PROFILES` dict structure for future tasks.
- `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` — The legacy path resolution occupied lines 63-90. `FEAT`, `feat_path()`, `DEVIATIONS_FILE`, `REPORTS_DIR`, `DISPATCH_LOG` are consumed throughout the rest of the script (dispatch provenance logging at line ~132, enforcement checks from line ~195 onward). Wrapping the legacy block requires ensuring all these variables are still set (which they are — the manifest branch sets them all at the top of the new block).
- `tests/unit/sdd_test_helpers.py` — The legacy workspace uses a flat structure: `tmpdir/reports/`, `tmpdir/DEVIATIONS.md` (old layout) or `tmpdir/<feat>/reports/` (new feature-dir layout). Tests pass `cwd=tmpdir` via hook input. No `.sdd-session.json` is created, so `MANIFEST_MODE` stays false and the legacy branch fires.

**CLAUDE.md Files Read:**
- None found in `skills/subagent-driven-development/` or `skills/subagent-driven-development/scripts/`
- Root project `CLAUDE.md` was loaded in session context — consulted "Hook Development Gotchas" section re: `set -u` initialization requirements and piped-command restrictions.

**Deviations from Plan:**
- **Required Modification applied: `$GIT_ROOT/$FEAT/$MANIFEST_MODULE_FILE` instead of `$GIT_ROOT/$MANIFEST_MODULE_FILE`.** The plan's reference code reconstructs `active_module_file` as `"$GIT_ROOT/$MANIFEST_MODULE_FILE"`. This is incorrect because Module 1 stores `active_module_file` as a bare filename (e.g., `"m2.md"`) with no directory prefix (Module 1 deviation #2 in `deviations.md`). Using the plan's reference would produce `$GIT_ROOT/m2.md` instead of the correct `$GIT_ROOT/<feature-dir>/m2.md`. The fix uses `"$GIT_ROOT/$FEAT/$MANIFEST_MODULE_FILE"` — `$FEAT` is set on the immediately preceding line and equals `$FEAT_FROM_ROOT`.
- **Extra variable initializations at outer scope.** The plan's reference code only shows variables initialized inside the manifest `if` block. To satisfy `set -uo pipefail` (all variables must be initialized before any read), I initialized `FEAT`, `DEVIATIONS_FILE`, `REPORTS_DIR`, `DISPATCH_LOG`, `MANIFEST_TIER`, `MANIFEST_TASK_START`, `MANIFEST_TASK_END`, `MANIFEST_PLAN_FILE`, `MANIFEST_MODULE_FILE` to empty string at the top of the new block, before either conditional branch. The legacy branch then overwrites these in its own scope. This is strictly additive — no plan logic is changed.

**Self-Review Findings:**
- Confirmed `FEAT_FROM_ROOT` is set and immediately consumed inside the same `if` block — never referenced outside it — so no `set -u` exposure.
- Confirmed `feat_path()` helper inside the legacy branch is defined inside the `if [ "$MANIFEST_MODE" = false ]` block. This is a shell function definition, so it's scoped to the current shell (not to the block). If `MANIFEST_MODE=true`, the function is never defined. I verified that `feat_path()` is only called from within the legacy block, so this is safe.
- Double-checked all six `jq -r` calls against `sdd_session.py` model field names — all match exactly.
- `bash -n` syntax check: PASS.
- Test suite: 16/16 PASS.

**Concerns:**
- The `feat_path()` helper function is defined inside the `if [ "$MANIFEST_MODE" = false ]` block. In bash, function definitions inside `if` blocks are still global to the shell process — there is no block scoping for functions. So `feat_path()` is only defined when `MANIFEST_MODE=false`, but any code that calls `feat_path()` after line 131 would produce "command not found" if `MANIFEST_MODE=true`. I verified that no post-line-131 code calls `feat_path()` — it's only called at lines 119-121 inside the legacy block itself. This is safe for Task 6 but is worth noting for Task 7-10 authors: do not call `feat_path()` from manifest-mode code paths.
