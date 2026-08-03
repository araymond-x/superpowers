# Spec Compliance Re-Review — Task 15 (Round 2, post-[task 15 fix])

## Verdict: PASS (with advisory notes)

Re-review of the [task 15 fix] round (commits `710c40f`, `85e4190`) against the two BLOCKING findings from the round-1 review (`task-015-spec-review.md`).

Independently re-verified every claim in `task-015-fix-report.md` against the actual diff (`git diff ddebe69..85e4190`) and by running the code — not just reading the report's prose.

### Finding 1 (BLOCKING — caller derivation untested): CLOSED, verified

`tests/unit/test_pre_completion_gates.py` gained `TestGitRealityCallerDerivationReportsDirMode` (2 tests) and `TestGitRealityCallerDerivationManifestMode` (2 tests), which drive `controller-checkpoint.py --phase pre-completion` as a real subprocess against a real git repo in both invocation modes. Ran all 4 — pass. This genuinely exercises `run_pre_completion`'s own `elif args.reports_dir:` / `if getattr(args, "manifest", ...)` wiring, not just the direct `_check_verification_git_reality()` helper the original 3 fenced tests called.

### Finding 2 (BLOCKING — reports_dir-mode fail-open on cwd drift): CLOSED, verified with an independent positive control

The fix, at `controller-checkpoint.py`'s `elif args.reports_dir:` branch (Check 9):

```python
git_root_for_check = _resolve_git_root(Path(args.reports_dir))
exclude_dir_for_check = os.path.relpath(
    os.path.realpath(os.path.dirname(args.reports_dir.rstrip("/"))),
    os.path.realpath(git_root_for_check),
)
```

Did not just trust the implementer's `git stash` claim — copied `ddebe69`'s pre-fix `controller-checkpoint.py` over the live file, reran `TestGitRealityCwdIndependence` and `TestGitRealityCallerDerivationReportsDirMode::test_source_commit_fails`, and both **failed** (spuriously reported PASS for a real source-file commit with subprocess cwd pinned to an unrelated directory — reproducing the exact fail-open bug). Restored the fixed file and confirmed the tree was byte-identical to the committed state. Against the fixed code, both tests pass. Genuine, empirically-confirmed closure.

The `realpath` vs `abspath` correction (macOS `/tmp` → `/private/tmp` symlink resolution) is real and necessary — the caller-derivation tests use `tmp_path`, which lands under the symlinked `/tmp` on this machine, so they organically exercise this path.

### Advisory Finding 3: CLOSED, verified

`test_no_exclude_dir_does_not_add_exclude_pathspec` (a directory literally named `None`) passes and discriminates the `if exclude_dir:` → `if True:` mutant the original test could not (construction verified sound by inspection: a `True` mutant would stringify `None` into `:(exclude)None` and wrongly exclude the directory).

### Commit `85e4190` ("revert formatter drift"): verified inert for its target

`git diff ddebe69 85e4190 -- controller-checkpoint.py` shows only the intentional Check 9 fix remains — `_EMPTY_TREE_SHA` and `_feature_window_base` formatting confirmed reverted to `ddebe69`'s exact form.

## Advisory findings (non-blocking)

- **[ADVISORY][EXTRA]** `tests/unit/test_pre_completion_gates.py` — the same autoformatter drift that `85e4190` explicitly reverted in the source file was NOT reverted here; ~3 unrelated pre-existing tests near `TestReviewTiersArchiveAware` got their `dict()` calls collapsed from multi-line to single-line. Harmless (pure line-wrap, no semantic change), but contradicts the implementer's own stated scoping discipline.
- **[ADVISORY][MISUNDERSTANDING]** Test count: independently ran `tests/unit/ -q -p no:cacheprovider` — **842 passed, 1 xfailed, 0 failed**, not 841 as recorded in the report's frontmatter (`tests.passing: 841`) and Self-Review prose. No hidden failures (more passed than claimed, not fewer) — doesn't affect the verdict, just report accuracy. (Controller note: independently re-confirmed 842/1-xfail/0-fail via a separate full-suite run — see deviations.md.)
- **[ADVISORY][UNVERIFIED]** `tests.passing (841) cannot exceed tests.written (6)` — ran `validate-report.py` against both `task-015-fix-report.md` and the already-merged `task-014-fix-report.md`; both fail identically on this Pydantic constraint. The implementer's claim that this is a pre-existing convention mismatch, not introduced by this round, is confirmed accurate.
- **[ADVISORY][UNVERIFIED]** `_resolve_git_root`'s fallback (`manifest_path.resolve().parent.parent.parent`, used only when `git rev-parse --show-toplevel` fails) lands one directory too shallow for the `docs/imp-plans/<feature>/...` convention — confirmed by direct computation that both a manifest file path and `reports_dir` resolve to `docs`, not the true repo root, under this fallback. NOT a new regression — identical pre-existing behavior already present (and never fixed) in the manifest branch this fix round mirrors; `transition-module.py:115-123` (cited in the docstring as a match) only mirrors the primary `git rev-parse` call, has no equivalent fallback at all (hard-fails instead). Only reachable when git itself is unavailable or the path is outside a repo; no test exercises it in either branch. Worth a backlog item, not a blocker for this round.

## Bottom line

Both BLOCKING findings from the round-1 spec review are genuinely closed — verified by running the tests, and by reproducing Finding 2 against the actual pre-fix code as a positive control (not merely trusting the implementer's account). No new regressions introduced. Report is complete (all required sections present); representations accurate except the minor 841-vs-842 count, flagged advisory. Recommend proceeding to quality review.

Files reviewed: `docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/task-015-spec-review.md`, `docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/task-015-fix-report.md`, `skills/subagent-driven-development/scripts/controller-checkpoint.py`, `tests/unit/test_pre_completion_gates.py`, `skills/subagent-driven-development/scripts/transition-module.py`.
