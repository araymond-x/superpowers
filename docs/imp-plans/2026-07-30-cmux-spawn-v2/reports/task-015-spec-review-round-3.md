# Spec Compliance Re-Review — Task 15 (Round 3, post-[task 15 fix] round 3)

## Verdict: PASS

Task 15 round-3 fix (`d5b966b`, `9b41eda`) genuinely closes both Critical findings (C1, C2) from `task-015-quality-review.md` (the first quality review for this task, run against the round-2 fix). Independently reproduced every mutation claim rather than trusting the report, and found one new minor coverage gap plus a report-accuracy inaccuracy — both advisory, neither blocking.

### Independent verification performed

**C2 (`.` fail-open)**: Reduced `_sanitize_exclude_dir` to a passthrough (`return candidate`) — both new `TestGitRealityExcludeDirNormalizesToRoot` tests went red with exactly the described symptom (`status: PASS` on a real `src/feature.py` commit). Restored, confirmed `git status --porcelain` clean on the file. Also drove the real CLI directly (not pytest) against the exact reproduction scenario and confirmed `checks['verification_git_reality']` returns `FAIL` with the narrowing-failed note text present, in both reports_dir and manifest mode.

**C1 (realpath coverage)**: Reverted the round-2 `realpath`→`abspath` correction. Confirmed the implementer's specific (non-obvious, easy-to-get-backwards) claim: `test_source_commit_fails_unresolved_repo_path` stays green under the mutant (does NOT discriminate — because the malformed `..`-prefixed candidate gets caught by `_sanitize_exclude_dir` and Check 9 falls back to unnarrowed, which still correctly flags a source commit), while `test_bookkeeping_commit_passes_unresolved_repo_path` goes red (correctly flags the C1 regression, since the unnarrowed fallback now wrongly FAILs a bookkeeping-only commit). The three-way C1×C2 interaction claim is accurate.

**Full suite**: independently ran `.venv/bin/python3 -m pytest tests/unit/ -q -p no:cacheprovider` — **846 passed, 1 xfailed, 0 failed**, matching both the implementer's and controller's figures exactly. All 3 originally-fenced Task 15 tests and both round-2 caller-derivation/cwd-independence tests still pass.

**`git status --porcelain`** at the end matches the session-start state (same modified bookkeeping files, same untracked set plus the two review report files) — no evidence of the documented silent-wipe/stranded-index incident class recurring.

### Findings

- **[ADVISORY][MISUNDERSTANDING]** `task-015-fix-round-3-report.md` Concerns item 2 claims "4 ≤ 846, so this report validates cleanly, unlike round 2's." This is backwards — running `validate-report.py` against it **FAILs** identically to round 2's (`tests.passing (846) cannot exceed tests.written (4)`), same Pydantic constraint, same underlying convention mismatch round-2 spec review already dispositioned as pre-existing ADVISORY (confirmed against `task-014-fix-report.md` too). The underlying pattern is not blocking; the affirmative false verification claim is a report-accuracy slip worth correcting.

- **[ADVISORY][UNVERIFIED]** `_sanitize_exclude_dir` rejects `"."`, `""`, and leading `".."`, but not an absolute-path candidate escaping the repo. Confirmed empirically that `git log -- . ':(exclude)/etc'` exits rc=128 for a candidate outside the repo, which `_check_verification_git_reality`'s `if result.returncode == 0` guard silently treats as "no findings" (PASS) — this is I1's already-deferred swallow, reachable through a second route: `materialize-manifest.py`'s `git_root_relative()` leaves an absolute `feature_dir` in the manifest with only a stderr warning when the path isn't under git root. Not driven end-to-end; flagged for the next reviewer, not blocking this round (C2's literal requirement — "."/""/leading ".." — is met exactly). Related minor nit: `normalized.startswith("..")` also over-matches a literal directory name like `..hidden` (not a parent-traversal); the fail direction there is safe (narrowing skipped → unnarrowed → possible false-positive FAIL, never a fail-open).

- **[ADVISORY][MISSING]** No test pins the *negative* of `exclude_dir_narrowing_failed`. Hardcoding it to `True` unconditionally leaves the entire `test_pre_completion_gates.py` (51 tests) green — every passing bookkeeping-commit test now carries a spurious narrowing-failed note in `detail` with nothing objecting. Cosmetic-only (advisory JSON text, no status/blocker change), same severity class as the original quality review's own M4/M5/M8/M9 survivors. Restored and confirmed clean.

### Report completeness

All 5 required prose sections present. Frontmatter is otherwise Pydantic-valid; the one failure is the pre-existing `tests.passing`/`tests.written` convention issue noted above, not a missing-sections problem — REPORT_INCOMPLETE does not apply.
