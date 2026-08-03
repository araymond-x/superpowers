---
schema_version: 1
task_id: 15
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/subagent-driven-development/scripts/controller-checkpoint.py"
    description: "reports_dir-mode Check 9 branch now resolves git_root_for_check via _resolve_git_root() before deriving exclude_dir_for_check, and computes the exclude pathspec relative to that resolved root (via os.path.realpath on both sides) instead of the process's actual OS cwd"
  - path: "tests/unit/test_pre_completion_gates.py"
    description: "6 new tests: 2 reports_dir-mode + 2 manifest-mode caller-derivation tests exercising run_pre_completion's real CLI wiring (Finding 1), 1 cwd-independence regression test reproducing the exact fail-open scenario (Finding 2), 1 mutation-discriminating variant of test_no_exclude_dir_keeps_old_behavior (advisory Finding 3)"
tests:
  written: 6
  passing: 841
  command: ".venv/bin/python3 -m pytest tests/unit/ -q -p no:cacheprovider"
  result: PASS
contract_compliance:
  - constraint: "Finding 1 (BLOCKING): caller derivation code (run_pre_completion's own exclude_dir_for_check/git_root_for_check wiring) must be exercised by a test, not just the direct _check_verification_git_reality() helper calls."
    status: compliant
    detail: "TestGitRealityCallerDerivationReportsDirMode and TestGitRealityCallerDerivationManifestMode drive controller-checkpoint.py as a real subprocess against a real temp git repo in both modes (bookkeeping-only commit PASSes, source-file commit FAILs) — 4 new tests."
  - constraint: "Finding 2 (BLOCKING): reports_dir-mode Check 9 must not silently fail-open when the process's OS cwd differs from the repo root."
    status: compliant
    detail: "git_root_for_check is now resolved via _resolve_git_root(Path(args.reports_dir)) before deriving exclude_dir_for_check (realpath on both sides of the relpath call, mirroring the manifest branch). TestGitRealityCwdIndependence reproduces the reviewer's exact scenario (subprocess cwd pinned to an unrelated directory) and asserts Check 9 still FAILs."
  - constraint: "Advisory Finding 3 (optional): test_no_exclude_dir_keeps_old_behavior doesn't discriminate the `if exclude_dir:` guard from a `if True:` mutant."
    status: compliant
    detail: "Added test_no_exclude_dir_does_not_add_exclude_pathspec, which creates a directory literally named 'None' and proves the guard is not stringifying None into the pathspec :(exclude)None. Verified empirically by temporarily mutating the guard and confirming the new test fails while the old one still passes."
---

**Implementation Summary:**

This is the fix round for Task 15 (commit `f2701df`), closing the two BLOCKING findings from `docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/task-015-spec-review.md`.

**Finding 2 (the actual bug) — fixed first**, since Finding 1's tests need to exercise correct behavior. In `run_pre_completion()`'s `elif args.reports_dir:` branch (Check 9 / git reality check), `git_root_for_check` was left `None`, so `_git_run` invoked `git` without `-C` and inherited the *process's* actual OS cwd. The `exclude_dir_for_check` pathspec fragment was computed relative to that same `os.getcwd()`. When the process's cwd was not the repo root — a normal situation for any subprocess test harness or any caller invoked from a subdirectory — the bare `.` pathspec in `git log -- . :(exclude)<dir>` scoped the whole diff to files under the wrong directory. If that directory was outside the git repo entirely, `git log` failed outright (non-zero return code), and `_check_verification_git_reality` treats a failed/errored `git log` identically to "no commits found" (`result.returncode == 0` gate on the finding), so Check 9 silently PASSED — a fail-closed integrity gate going fail-open.

Fix: resolve `git_root_for_check = _resolve_git_root(Path(args.reports_dir))` up front (mirroring what the manifest branch already did correctly via `_resolve_git_root(_mp)`), then compute `exclude_dir_for_check` relative to that resolved root instead of `os.getcwd()`.

While implementing this I found a second, narrower bug the plan's candidate fix didn't anticipate: `_resolve_git_root()` shells out to `git rev-parse --show-toplevel`, which resolves symlinks (macOS's `/tmp` → `/private/tmp`), but `os.path.abspath()` does not. On a symlinked tmpdir (which is exactly what `tempfile.mkdtemp()` produces on macOS), comparing an `abspath`'d reports_dir against a symlink-resolved `git_root_for_check` via `os.path.relpath` produced a nonsense multi-`../` path instead of the intended `docs/imp-plans/<feature>` fragment — verified empirically with a standalone repro before writing any test. Fixed by using `os.path.realpath()` on both sides of the `relpath` call instead of `os.path.abspath()`, so both operands agree on the same canonical (symlink-resolved) root.

**Finding 1 (caller-derivation coverage gap)** — closed by adding two new test classes that invoke `controller-checkpoint.py --phase pre-completion` as a real subprocess against a real temp git repo, for both invocation modes:
- `TestGitRealityCallerDerivationReportsDirMode` (no `--manifest`) — exercises the `elif args.reports_dir:` branch directly.
- `TestGitRealityCallerDerivationManifestMode` (`--manifest <path>`) — exercises the `if getattr(args, "manifest", ...)` branch, using a git-init'd workspace + `.sdd-session.json` manifest built the same way `setup_checkpoint_workspace()` does in `tests/unit/test_controller_checkpoint_stale.py`.

Each class has two cases: (a) a commit inside the verification window touching only feature-dir bookkeeping (`reports/handoff-spawn.log`, `reports/.handoff-hops`) → Check 9 must PASS; (b) a commit inside the window touching a source file outside the feature dir → Check 9 must FAIL. All four pass against the fixed code.

**`TestGitRealityCwdIndependence`** reproduces the exact scenario used to prove Finding 2 empirically: the (b)-style source-file-outside-feature-dir commit, invoked with the subprocess's `cwd` pinned to a directory that shares no ancestry with the repo at all. Before the fix this spuriously PASSED (confirmed via `git stash` + manual repro before writing the test — see Self-Review); after the fix it correctly FAILs regardless of process cwd.

**Advisory Finding 3** — addressed via `test_no_exclude_dir_does_not_add_exclude_pathspec`, a mutation-discriminating variant of the existing `test_no_exclude_dir_keeps_old_behavior`. The original test can't tell `if exclude_dir:` from a mutated `if True:` because `exclude_dir=None` degrades to the harmless literal pathspec fragment `:(exclude)None`. The new test creates a directory literally named `None`, commits a file inside it, and calls with `exclude_dir=None` — correct code never adds the exclude pathspec (Python `None`, not the string `"None"`) so the commit is still flagged; a `if True:` mutant would stringify `None` into the pathspec and wrongly exclude that directory. Verified empirically by temporarily applying the mutation and confirming the new test fails while the old one keeps passing.

**Source Files Read:**

- `skills/subagent-driven-development/scripts/controller-checkpoint.py` — the Check 9 call site (`run_pre_completion`, `# Check 9: Git reality check` block), `_check_verification_git_reality()`, `_git_run()`, and `_resolve_git_root()` in full, to confirm the exact mechanics of `-C`, pathspec resolution, and the fallback triple-`.parent` depth calculation.
- `docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/task-015-spec-review.md` — the full spec review, both BLOCKING findings verbatim plus the reviewer's candidate fix.
- `tests/unit/test_pre_completion_gates.py` (full file) — existing `TestGitRealityCheck`/`TestCheck9ArchiveAware` test idiom, `_init_temp_git_repo`/`_commit_file_at`/`_commit_files_at`/`_plan_with_task_types` helpers, and `run_pre_completion()`'s own CLI-invocation pattern, all reused rather than reinvented.
- `tests/unit/test_controller_checkpoint_stale.py` — `setup_checkpoint_workspace()` and `run_checkpoint_cli()` for the manifest-mode workspace/git-init pattern; mirrored (not imported) into a smaller `_write_manifest()` helper local to `test_pre_completion_gates.py` to avoid cross-file coupling.
- `tests/unit/conftest.py` — confirmed `skills/scripts/models` is already on `sys.path`, so `from sdd_session import TIER_PROFILES` needs no extra path manipulation in the target file.

**CLAUDE.md Files Read:**

- Project root `CLAUDE.md` — "SDD Cleanup & Integration Gate", "N43", and "cmux Auto-Spawn Handoff" sections for the Check 9 / `_resolve_git_root` / manifest-relative-paths background; "Hook Development Gotchas" for the macOS `/tmp` symlink precedent (already documented for a different script, which is what pointed me at the realpath-vs-abspath issue here).
- No subdirectory `CLAUDE.md` files exist under `skills/subagent-driven-development/` or `tests/unit/`.

**Deviations from Plan:**

- The task brief's Step 1 described the fix as resolving `git_root_for_check` and reusing "the same `os.path.dirname(os.path.abspath(...))` logic ... only the `os.getcwd()` denominator needs to become `git_root_for_check`." Implementing exactly that literally (abspath vs. a git-resolved, symlink-resolved root) produced a broken `relpath` on this macOS sandbox because `tempfile.mkdtemp()` returns a path under the symlinked `/tmp`. I additionally switched both sides of the `relpath` call from `abspath` to `realpath` to keep them on the same canonical root. This is a strict tightening of the prescribed fix (same intent, corrected implementation), not a scope change — logged here per "Finish the authorized scope" / evidence-backed claims, not filed as an open concern since it's fully resolved and tested (both the raw standalone repro and `TestGitRealityCwdIndependence` exercise it).
- Did not touch `docs/imp-plans/2026-07-30-cmux-spawn-v2/deviations.md` or plan checkboxes, per the explicit constraint — leaving that bookkeeping to the controller.

**Self-Review Findings:**

- Reproduced Finding 2 empirically end-to-end (not just reasoned about it) before writing the regression test: ran the fixed CLI against a real git repo with a source-file commit inside a verification window, with subprocess `cwd` set to an unrelated tempdir → correctly FAILs (exit 1, `verification_git_reality: FAIL`). Then `git stash`'d the fix and reran the identical repro against the pre-fix code → spuriously PASSED (exit 1 from other unrelated pre-completion checks, but `verification_git_reality: PASS`) — confirming the bug is real and the fix closes it. `git stash pop` restored the fix cleanly; verified via `git status` that only the intended two source files remained modified afterward.
- Verified the macOS `/tmp` symlink issue is real (not a hunch) with a standalone `os.path.abspath` vs `os.path.realpath` comparison against `_resolve_git_root()`'s actual return value before touching the fix code.
- Verified the advisory Finding 3 test actually discriminates the mutation it claims to, by temporarily mutating `if exclude_dir:` → `if True:` in a copy of the source, confirming the new test fails and the original `test_no_exclude_dir_keeps_old_behavior` still passes, then restoring the original file and confirming via `git diff --stat` that the restore was byte-for-byte (only the intentional fix diff remained).
- Ran the 3 originally-fenced Task 15 tests by name (`test_bookkeeping_commit_in_window_passes`, `test_source_commit_in_window_still_fails`, `test_no_exclude_dir_keeps_old_behavior`) — all still pass unchanged, confirming the fix didn't regress the direct-call test surface Task 15 originally shipped.
- Ran the full unit suite (`.venv/bin/python3 -m pytest tests/unit/ -q -p no:cacheprovider`): 841 passed, 1 xfailed, 0 failed.
- Confirmed `controller-checkpoint.py` is not in `tests/ARaymond-hook-baseline/baseline.txt`'s pinned hook list, so no baseline re-capture is required for this change.
- Confirmed via `git status` before committing that only `skills/subagent-driven-development/scripts/controller-checkpoint.py` and `tests/unit/test_pre_completion_gates.py` were staged with an explicit pathspec — left the pre-existing unrelated dirty bookkeeping files (`.dispatch-log`, `context-observations.log`, `.handoff-hops`, `handoff-spawn.log`) untouched, per the Task 14 fix-round precedent and the CLAUDE.md warning that `deviations.md`/bookkeeping edits can be silently lost around a clean `git status`.

**Concerns:**

None blocking. Two residual notes:

1. This fix round did not re-run `tests/integration/sdd-e2e-test.sh` or the skill-regression/install test suites — the task brief scoped verification to the fenced tests + new tests + full unit suite, and this change touches only `controller-checkpoint.py` internals (not a hook, not a skill, not the manifest schema), so those suites are unlikely to be affected. Flagging as DONE_WITH_CONCERNS rather than DONE strictly because a fix round is inherently a deviation from a clean single-pass implementation, per the report-status convention used in `task-014-fix-report.md`.
2. `tests.written`/`tests.passing` are reported as 6/841 (new tests written / total suite passed), matching this feature's established fix-round convention (`task-014-fix-report.md`: 0/5; `task-015-implementer-report.md`: 3/41 — both report the full relevant-run pass count, not a per-new-test count). This does NOT validate cleanly under `ImplementerReport`'s `passing <= written` model constraint — confirmed by running `validate-report.py` against this report AND against the already-committed `task-014-fix-report.md`, which fails the identical way (`tests.passing (5) cannot exceed tests.written (0)`). This is a pre-existing model/convention mismatch predating this fix round, out of scope for a Task 15 fix, and not something I introduced — surfaced here rather than silently worked around by misreporting either number.
