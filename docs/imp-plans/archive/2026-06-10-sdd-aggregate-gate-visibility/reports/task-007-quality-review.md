# Task 7 (N25c) — Code Quality Review

**Ready to merge? Yes.** Behavior-preserving SSOT refactor; no Critical/Important findings.

## Strengths
- **Clean, correct SSOT abstraction.** `_git_run` (controller-checkpoint.py:483-498) captures the shared contract exactly (`capture_output=True, text=True, timeout=10`, swallow `(TimeoutExpired, OSError)` → None). The two inner `_git` helpers collapse from 9-line try/except blocks to one-line delegations; the inline site loses its hand-rolled prepend + try/except. Genuinely eliminates the triplication — one place to change timeout/error semantics now.
- **O4 exclusion correctly honored + documented.** `_resolve_git_root` (:744-771) byte-for-byte untouched — no timeout, no try/except, errors flow to the `parent.parent.parent` fallback. Folding it in would have added an unwanted timeout AND swallowed the error driving its fallback. `_git_run`'s docstring names the exclusion + why.
- **All callers audited — exactly 2 `subprocess.run` remain** (:496 `_git_run`, :751 `_resolve_git_root`). Old inline bodies fully removed (deleted, not commented). No new dead code, no unused imports/vars.
- **Behavior-equivalence at the subtle spot:** OLD inline gated `-C` on `if git_root:` (falsy → bare git); `_git_run` gates on `if cwd else` — identical truthiness. The two inner helpers prepended `-C` unconditionally, but their callers pass `git_root` from `_resolve_git_root` (always non-empty), so the `cwd=""` divergence is unreachable.
- **Type-hint consistency:** `# type: (list, Optional[str], int) -> Optional[subprocess.CompletedProcess]` matches the module's 3.9-safe convention (`Optional` imported at :43; file already uses `# type:` comments). The legacy comment form is the CORRECT deviation from the modernize-hints rule — a PEP-604 `|` would pass pytest-on-3.12 but FAIL the regression Category-8 check.
- **Tests verify real behavior:** `test_git_run_handles_failure` (bad cwd → git exits 128, `CompletedProcess(rc!=0)`; assert covers both None and rc-128 paths); `test_git_run_returns_completed_process` (real repo, rc==0). 65-test green across both touched suites = the behavior-preservation proof.

## Issues
### Critical — None.
### Important — None.
### Minor (Nice to Have)
- **:494 latent `cwd=""` divergence (doc nicety, not a fix).** `_git_run` treats `cwd=""` as "no -C" (else branch), whereas the former inner helpers prepended `-C` unconditionally. Unreachable today (all `git_root` from `_resolve_git_root`, never empty); not a behavior change for any live path. Optional: a docstring clause noting "empty cwd → no -C (same as None)". Re-examine IF Task 8 introduces a caller that could pass empty cwd (Task 8's concern, not Task 7's).

## Recommendations
- Ship as-is. The single Minor is documentation, not a blocker.

## Assessment
**Ready to merge? Yes.** Textbook behavior-preserving SSOT refactor — triplication genuinely eliminated, all callers audited (exactly 2 subprocess.run, both expected), load-bearing O4 exclusion of `_resolve_git_root` correctly preserved + documented, 3.9-safe type comment consistent + intentionally chosen, 2 new tests + 65 unchanged tests prove no semantic drift.

## Controller carry-forward note (Task 8)
The Minor `cwd=""` note: Task 8 adds `_merge_base_is_head`/`_feature_window_base` calling `_git_run` with `git_root` (always truthy from `_resolve_git_root`) — so no empty-cwd issue. Flagged in the Task 8 dispatch as a watch item.
