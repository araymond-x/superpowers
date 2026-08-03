# Code Quality Re-Review — Task 15 (Round 3 fix, post-[task 15 fix] round 3)

Range: `85e4190..9b41eda`. Full unit suite independently re-run: **846 passed, 1 xfailed** (447s), targeted file **51 passed**. Repo restored byte-identical (sha256 verified) after all mutation work.

## Strengths

- **C1 and C2 are genuinely closed.** Reproduced both independently rather than trusting the prior reports. MU7 (`_sanitize_exclude_dir` → passthrough) is killed by both `TestGitRealityExcludeDirNormalizesToRoot` tests; MU8 (`realpath`→`abspath`, both sides) is killed by `test_bookkeeping_commit_passes_unresolved_repo_path`. Neither fix is test-shaped.
- **The manifest branch is independently pinned, not merely "calls the same function."** MU4 (manifest branch only: `narrowing_failed = False`) is killed by exactly `test_source_commit_fails_manifest_mode`; MU5 (reports_dir branch only) by exactly `test_source_commit_fails_reports_dir_mode`. Each mode has its own end-to-end CLI test asserting both status and note text.
- **The "non-discriminating" test is not redundant — it is the only thing killing the double mutant.** `test_source_commit_fails_unresolved_repo_path` was kept as a "straightforward fail-closed sanity check" and documented as non-discriminating. But MU9 (MU1+MU8 applied *together* — drop the `".."` guard AND revert `realpath`) survives the bookkeeping test and is killed **only** by the source-commit test. Keeping it was right for a reason the implementer didn't know.
- **The manifest branch's `except Exception: pass` is narrower than it looks — checked and negative.** Expected it to convert a manifest/git failure into a silent Check 9 PASS. It doesn't: `_load_manifest_config` Pydantic-validates the manifest first, so a missing `paths.dispatch_log`/`paths.feature_dir` exits 3 before Check 9 runs, and with `git` removed from `PATH` both manifest and reports_dir modes exit 3.
- **No dead code, no stray artifacts** in `skills/`/`tests/`. Report accuracy verified (file/test counts match the diff; suite figures match prior reports exactly).

## Mutation Log (round-3-scoped)

| # | Mutation | Result | Killed by |
|---|---|---|---|
| MU1 | Drop `normalized.startswith("..")` from `_sanitize_exclude_dir` | **SURVIVED** (51/51) | — |
| MU2 | Drop `normalized == "."` from `_sanitize_exclude_dir` | KILLED | both `…NormalizesToRoot` tests |
| MU3 | Force `exclude_dir_narrowing_failed = True` unconditionally | **SURVIVED** (51/51) | — (confirms spec reviewer's claim) |
| MU4 | Manifest branch only: `narrowing_failed = False` | KILLED | `test_source_commit_fails_manifest_mode` |
| MU5 | reports_dir branch only: `narrowing_failed = False` | KILLED | `test_source_commit_fails_reports_dir_mode` |
| MU6 | `_sanitize_exclude_dir` returns `normalized` not `candidate` | SURVIVED — verified *equivalent* | — |
| MU7 | `_sanitize_exclude_dir` → passthrough (C2 control) | KILLED | both `…NormalizesToRoot` tests |
| MU8 | `realpath`→`abspath` both sides (C1 control) | KILLED | `test_bookkeeping_commit_passes_unresolved_repo_path` |
| MU9 | MU1 **+** MU8 together | KILLED | `test_source_commit_fails_unresolved_repo_path` only |

## Issues

### Critical (Must Fix)

None. Both round-3 Critical fixes hold under independent mutation.

### Important (Should Fix)

**I-A — An absolute, out-of-repo `feature_dir` still reaches the pathspec and silently certifies a modified repo as clean.**
`_sanitize_exclude_dir`'s docstring says it rejects "a candidate that would fail to narrow the Check 9 git pathspec." An absolute path outside `git_root` does exactly that and worse — `git log -- . ':(exclude)/abs/outside'` exits 128, and `_check_verification_git_reality`'s `result.returncode == 0` guard turns that into zero findings. Verified end-to-end through the real CLI with a real `src/feature.py` commit inside the verification window:
```
CONTROL  feature_dir='docs/imp-plans/feat'   -> FAIL, blocked=True
BUG      feature_dir='/nonexistent/outside/feat' -> PASS, blocked=False, no note, no warning
```
Reachability: `materialize-manifest.py`'s `git_root_relative()` only WARNS (doesn't reject) when a manifest's `feature_dir` ends up absolute/outside git root; `ArtifactPaths` has no validator rejecting it. Strongest reach: materialize the manifest in the main checkout, run the checkpoint from a worktree — the absolute `feature_dir` is outside the worktree's git root, and Check 9 goes permanently fail-open for the rest of the session. (Controller note: this session's own `.sdd-session.json` has a relative `feature_dir`, so not live here — but the reachability is real.) Not Critical because the writer does warn.

**Fix:** one-line — reject `os.path.isabs(normalized)` in `_sanitize_exclude_dir`.

**I-B — The `".."`-prefix guard in `_sanitize_exclude_dir` is load-bearing and has zero shipped-code coverage — the C1 pattern recurring one level down.**
No test in the file ever produces a `".."`-prefixed candidate under *shipped* code (only under an already-reverted mutant), so dropping the clause leaves 51/51 green. Positive control: `feature_dir='../outside-the-repo/feat'` — shipped code FAILs (rejected, runs unnarrowed, still sees the source commit); dropping the `".."` check → PASS (rc=128 swallowed).

**Fix:** one manifest-mode test with a `".."`-prefixed `feature_dir`, asserting FAIL.

### Minor (Nice to Have)

- The narrowing-failed note always says "the feature/reports dir resolves to the git root itself" regardless of the actual rejection cause (also fires — falsely — for the absolute-path and `..`-prefix cases). Fix alongside I-A: return a reason string and interpolate it.
- Empty-string `feature_dir` is rejected silently (`bool("")` is False) — runs Check 9 unnarrowed with no note, while `"."` gets one.
- MU3: nothing pins the negative of `exclude_dir_narrowing_failed`. One `assert "resolves to the git root" not in detail` on an existing happy-path test closes it.
- `..hidden` over-match: a literal directory named `..hidden` is rejected as parent-traversal. Fail-closed direction (verified FAIL, not PASS) — harmless.
- MU6: validates `normalized`, returns `candidate` — verified equivalent, but checking one string and returning another is a latent footgun for a future edit.
- Two unrelated formatting hunks in the diff (`_EMPTY_TREE_SHA`, `_feature_window_base`) — harmless black churn.

## Recommendations

1. Fold I-A and the note-cause Minor into one small edit: `_sanitize_exclude_dir` returns `(value, reason)`, reject on `"."`/`""`/`".."`/`isabs`, interpolate `reason` into the note.
2. Add the I-B test (`".."`-prefixed manifest `feature_dir`) and, in the same commit, the MU3 negative assertion.
3. Consider a `feature_dir`/`reports_dir` validator on `ArtifactPaths` (non-absolute, no `..`), mirroring `IntegrationTest` — kills I-A at both the writer and the reader. Larger change — BACKLOG candidate, not this round.
4. Unchanged from prior rounds and the structural root of all of this: `_check_verification_git_reality`'s `if result is not None and result.returncode == 0 ...` gate cannot distinguish "git failed" from "found nothing." Every finding above is a different door into that one swallow.

## Assessment

**Ready to merge?** With fixes.

**Reasoning:** Round 3 did what it claimed — C1 and C2 are genuinely closed, independently reproduced, the manifest branch is pinned separately from reports_dir, and the three-way C1×C2 interaction the implementer described is accurate. What this round found is one gap in the *new* function rather than the old one (I-A: absolute-path escape) plus zero coverage on a guard that does work (I-B). Both are small (one line, one test respectively). The structural root cause (the git-failure swallow) remains and is the shared mechanism behind C2, I-A, and I-B alike — worth closing once rather than continuing to patch individual candidate shapes.
