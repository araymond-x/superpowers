---
schema_version: 1
task_id: 15
status: DONE_WITH_CONCERNS
files_changed:
  - path: "tests/unit/test_controller_checkpoint_stale.py"
    description: "modified — added manifest-mode tests (helpers, fixture, TestManifestMode class)"
  - path: "docs/imp-plans/2026-05-17-adaptive-enforcement-tiers/deviations.md"
    description: "modified — added Task 15 deviation rows"
tests:
  written: 3
  passing: 3
  command: ".venv/bin/python3 -m pytest tests/unit/test_controller_checkpoint_stale.py -v"
  result: PASS
---

**Implementation Summary:**

Extended `tests/unit/test_controller_checkpoint_stale.py` with the new
`TestManifestMode` class covering Task 14's `--manifest` argument on
`controller-checkpoint.py`. Three new tests:

1. `test_manifest_overrides_plan_file` — verifies pre-execution with `--manifest`
   resolves `plan_file` from the manifest (exit code != 3).
2. `test_micro_tier_skips_honesty_check` — verifies micro-tier manifest sets
   `checks["honesty_check_missing"].status == "SKIP"` in pre-completion phase.
3. `test_backward_compat_without_manifest` — verifies `--plan-file` (no
   manifest) still works as before.

Added a `setup_checkpoint_workspace(tmp_path, tier)` fixture helper that builds
a git-initialized workspace with feat dir, reports dir, plan, deviations, and a
fully-populated `.sdd-session.json` (paths via `TIER_PROFILES[tier]`). Added a
`run_checkpoint_cli` helper that invokes the checkpoint script as a subprocess
and parses JSON output. Existing 8 tests in `TestStaleArtifactDetection` are
untouched.

Two CRITICAL fixes from the implementer prompt were applied:

- **Key correction (deviations row 29 ForwardConcern from Task 14):** Plan's
  Step 1 reference code reads `checks.get("honesty_check", {})`, but Task 14's
  implementation uses `honesty_check_missing` (and `trace_audit_missing`). Test
  updated to look up `"honesty_check_missing"` so the assertion matches the
  actual check key.

- **`git init` in fixture (precedent from Task 13, deviations row 23):**
  `_load_manifest_config` resolves git root via
  `git -C <manifest_parent> rev-parse --show-toplevel`. Without a git repo in
  `tmp_path`, the call exits non-zero and the script falls back to
  `parent.parent.parent`, which lands at `tmp_path/docs/` (one dir short),
  double-nesting `docs/` when joined with the git-root-relative `plan_file`.
  Added `subprocess.run(["git", "init", "-q"], cwd=str(tmp_path), check=True)`
  to the fixture before writing the manifest. Empirically verified all three
  tests pass with this addition.

**Source Files Read:**

- `tests/unit/test_controller_checkpoint_stale.py` (full file, 204 lines —
  existing imports, structure, naming)
- `skills/subagent-driven-development/scripts/controller-checkpoint.py` (full
  file — confirmed `_load_manifest_config` git-root resolution, micro-tier
  SKIP logic at lines 995-1047, `honesty_check_missing` / `trace_audit_missing`
  check keys)
- `skills/scripts/models/sdd_session.py` (`TIER_PROFILES`, `SddSession`
  validators — confirmed `midpoint=1` is within `task_range=[0,1]`)
- `tests/unit/conftest.py` (sys.path setup — `skills/scripts/models` already
  added)
- `tests/unit/test_transition_module.py` (Task 13 precedent — `create_manifest`
  pattern with `git init` and `TIER_PROFILES` import)
- `docs/imp-plans/2026-05-17-adaptive-enforcement-tiers/deviations.md` (Task 14
  row 29 ForwardConcern context, Task 13 row 23 `git init` precedent)
- `docs/imp-plans/2026-05-17-adaptive-enforcement-tiers/reports/task-014-implementer-report.md`
  (Task 14 implementation summary for context)

**Deviations from Plan:**

- **Reused existing `SCRIPT_PATH` constant via alias `CHECKPOINT_SCRIPT = SCRIPT_PATH`**
  rather than introducing a duplicate `os.path.join(...)` constant as the plan
  showed. Both point to the same file; aliasing avoids divergence (Single
  Source of Truth principle, `~/.claude/rules/architectural-principles.md`).
- **Skipped `import pytest`** — the plan's reference code includes
  `import pytest` but the new tests use only the `tmp_path` fixture (auto-
  injected by pytest, no explicit import required) and no `pytest.raises`,
  marks, or fixtures requiring the import. Avoids an unused-import lint flag.
- **Renamed helper function from `run_checkpoint` to `run_checkpoint_cli`** to
  avoid collision with the file's existing top-level `run_checkpoint` helper
  (used by `TestStaleArtifactDetection`). The existing helper has a different
  signature (plan content + dict of report files) and creates its own tmpdir;
  unifying them would require non-trivial refactoring of existing tests.
  Deviation logged as `IndependentDecision` in `deviations.md`.
- **Added explanatory docstring on `setup_checkpoint_workspace`** documenting
  why `git init` is required (cross-references deviation row 13 and the
  fallback bug). Strictly additive — no logic change vs. plan reference.

**Self-Review Findings:**

- All 3 new tests PASS in isolation and in the full unit suite (324/324 PASS).
- 8 existing tests in `TestStaleArtifactDetection` still PASS unchanged.
- `honesty_check_missing` key matches the production script's actual key name
  (verified by reading `run_pre_completion` lines 996, 1009, 1014, 1023).
- Fixture's `midpoint=1` is within `task_range=[0, 1]` — Pydantic
  `midpoint_in_range` validator (`sdd_session.py:114-120`) accepts it.
- `TIER_PROFILES` imported from `sdd_session` — not hardcoded; matches Task 13's
  precedent.
- `git init` placed BEFORE manifest creation in fixture — required so the
  `git rev-parse` call succeeds before any test exercises the script.
- Regression test (`validate-all-skills.py`) shows 9 FAILs, all pre-existing in
  `materialize-manifest.py` / `transition-module.py` (documented in deviations
  row 28). My changes touch only a test file and introduce zero new violations.
- No scratch files or debug prints left in the modified file.

**Concerns:**

- **Helper duplication between `setup_checkpoint_workspace` (this file) and
  `create_manifest` (`test_transition_module.py`) and `setup_manifest_workspace`
  (`sdd_test_helpers.py`).** The same git-init-plus-manifest-construction
  pattern is now in three places, each slightly different (different default
  `task_range`, `total_tasks`, `midpoint`, `modules` shape per the script under
  test). Deviations row 24 (Task 13 ForwardConcern) already tracks this for a
  post-Module-4 refactor. No action requested for Task 15 — log only.

- **`test_manifest_overrides_plan_file` and `test_backward_compat_without_manifest`
  use a negative assertion (`exit_code != 3`).** This passes if the script
  produces any non-error outcome (PASS=0, FAIL=1, WARNING=2), so it's a weak
  contract — it proves the manifest plumbing didn't crash, not that the
  manifest was actually used to resolve `plan_file`. The plan specified this
  shape, so retained verbatim. A future strengthening could read
  `result["output"]["checks"]["plan_file"]["detail"]` and assert it contains
  the manifest-resolved path. Acceptable for Task 15 since
  `test_micro_tier_skips_honesty_check` exercises the manifest-driven `tier`
  branch directly (strong assertion), demonstrating manifest data flows
  end-to-end.

- **`test_backward_compat_without_manifest` doesn't strictly verify "without
  manifest behaves the same as before."** It only checks `exit_code != 3`. A
  parallel assertion could compare against running the existing
  `TestStaleArtifactDetection::test_clean_workspace_no_warning` shape. Plan
  signature retained as-is to avoid scope creep.
