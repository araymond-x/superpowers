# Spec Compliance Review — Task 15

## Verdict: FAIL

Both fenced deliverables (Step 1 tests, Step 2 implementation) are present, match the fence text exactly, and pass (41/41 in `test_pre_completion_gates.py`, independently run). Diff matches `git show f2701df` line-for-line against the plan fence. No CLAUDE.md exists in `skills/subagent-driven-development/scripts/`. Report has all required sections.

However, two hunted risks (identified by the controller before dispatch, from the plan's own gap pattern) are both real — the second confirmed empirically via reproduction, and it's a genuine security-gate regression.

### Findings

**1. [BLOCKING][MISSING] — Caller derivation code is completely untested.**
`skills/subagent-driven-development/scripts/controller-checkpoint.py`, `run_pre_completion()` Check 9 block (manifest-mode `_md.get("paths", {}).get("feature_dir")` and reports_dir-mode `os.path.relpath(os.path.dirname(os.path.abspath(args.reports_dir.rstrip("/"))), os.getcwd())`).
All 3 new tests call `_check_verification_git_reality(..., exclude_dir=...)` directly with a hand-supplied string. No test exercises `run_pre_completion`'s own derivation of `exclude_dir_for_check` in either mode. Same shape as this feature's recurring plan-gap pattern (e.g. Task 13's timeout-leg gap): the fence only specified direct-call tests, so the actual wiring shipped with zero coverage.

**2. [BLOCKING] — reports_dir-mode derivation silently fail-opens Check 9 when the process cwd is not the repo root.**
Empirically reproduced: with a source-file commit at repo root and process cwd inside a subdirectory, the PRE-diff behavior (no pathspec) still finds the commit regardless of cwd. Adding `-- . :(exclude)<relpath>` (POST-diff, unconditionally applied whenever `args.reports_dir` is set) misses the commit entirely — the bare `.` pathspec scopes the scan to files under the actual OS cwd. In `reports_dir` mode `git_root_for_check` stays `None`, so `_git_run` never passes `-C`, meaning git always uses the literal process cwd. The `elif args.reports_dir:` branch sets `exclude_dir_for_check` unconditionally (no guard, no opt-out) — every reports_dir-only pre-completion run now scopes Check 9 to "files under whatever directory the process happened to be invoked from," strictly weaker than the prior full-repo scan. `reports_dir`-only mode (no `--manifest`) is not a rare edge case — it's the mode multiple existing test classes use, and `--manifest` is documented as optional. Compounds with Finding 1: zero test coverage on the caller path means no test would catch a future cwd-dependent invocation regressing further.

**3. [ADVISORY] — `test_no_exclude_dir_keeps_old_behavior` doesn't actually pin the `if exclude_dir:` guard it claims to.**
Verified by mutation: temporarily changed `if exclude_dir:` to `if True:` (pathspec branch always executes, even when `exclude_dir=None`) and re-ran — test still PASSED, because `exclude_dir=None` degrades to the harmless literal fragment `:(exclude)None`, matching no real path. The test is a valid default-behavior smoke check but doesn't discriminate guarded-vs-unguarded as its docstring implies. Restored after the experiment (`git diff` clean).

### Contract Constraints
Confirmed accurate — nothing in this diff touches baselined-hook atomicity, exit-ladder shape, or reservation-ordering; `controller-checkpoint.py` is not among the 7 baselined hook scripts.

### Recommendation
This is a plan gap, not an implementer deviation — the implementer followed the plan's exact formula and even manually verified `:(exclude)` syntax before coding, but neither the implementer's self-review nor the plan anticipated the cwd-dependence of `reports_dir`-mode's `git_root=None` fallback. Needs a controller decision: either (a) add a `git_root_for_check` fallback to the actual repo root (via `_resolve_git_root`) in the `elif args.reports_dir:` branch so the exclude pathspec is always root-relative regardless of process cwd, or (b) explicitly document/enforce that `controller-checkpoint.py` must be invoked from repo root and add a regression test pinning that cwd-drift doesn't silently narrow Check 9. Finding 1 (zero coverage of the caller derivation) should be closed before this is considered safe to rely on in production SDD sessions.
