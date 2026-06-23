# Task 8 (N25a) — Code Quality Review

**Scope:** Check 10 feature-window fallback. `git diff c06b230..c79531b` — two files: `controller-checkpoint.py`, `tests/unit/test_c2_integration_gate.py`.
**Review type:** Code quality (spec compliance already PASSed).

---

### Strengths

- **Correct core fix, empirically verified.** I reproduced the central claim in a throwaway repo: `git diff --name-only <empty-tree> -- <file>` returns a committed file even with a clean working tree, so the empty-tree Step-3b branch genuinely makes an on-main committed integration test visible. The merge-base path would have silently fallen back to `diff HEAD` and hidden it — the comment at `controller-checkpoint.py:607-611` names exactly that failure mode. Fix is real, not green-for-the-wrong-reason.
- **Fail-closed is preserved and proven.** The counter-fixture (`test_on_main_prewindow_file_still_fails`) commits the IT as the repo ROOT *before* the feature dir, so `_feature_window_base` returns a REAL parent (commit 1) and the empty-tree branch is NOT taken — the pre-window file goes through the normal merge-base path and `diff(parent, HEAD)` is empty → FAIL. I confirmed `diff(real_parent, HEAD) -- <prewindow_file>` is empty in a live repo. The fail-closed guarantee is genuine, not asserted-only.
- **Helpers are clean and well-documented.** `_merge_base_is_head` and `_feature_window_base` each carry a docstring that states the *why* (the merge-base==HEAD blind spot; the tree-object-has-no-merge-base constraint), not just the *what*. The root-commit edge (`rev-parse FIRST^` fails → empty-tree SHA) is handled explicitly and documented inline. `_EMPTY_TREE_SHA` is well-named with the "git's well-known empty tree" comment.
- **`_in_changeset` Step-3b placement is correct.** Placed AFTER the untracked short-circuit (`:604`) and BEFORE the merge-base block (`:615`), so the normal-path union logic is untouched for every non-empty-tree base. The early `return` keeps the special-case self-contained.
- **Both helpers and the constant are actually used** (`grep` confirms references at `:607/:612/:1734/:1735`); no NEW dead code, no unused imports. `Optional` was already imported (`:43`); the new `# type:` comments reference it correctly. No PEP-604 unions added — confirmed by a diff scan and by the regression Category-8 pass.
- **The two implementer deviations are genuine improvements, not weakenings.** (1) Capturing `manifest_feature_dir` BEFORE `_load_all_plan_contents` (`:1392`) is strictly more robust: a raise in that call hits the `except` and would otherwise leave the var `""`, silently disabling the whole N25a fix with no signal. (2) Gating the feature-window lookup on `manifest_feature_dir` being non-empty (`:1734`) prevents the on-base note from misattributing a non-manifest cause, and keeps non-manifest mode byte-for-byte at pre-N25a behavior. Both are logged in `deviations.md` (RobustnessRefinement, ScopeRefinement) with accurate rationale.
- **Tests use real git repos, not mocks.** `_init_main_repo` / `_write_feat_manifest` / `_run_manifest_checkpoint` drive ordered commits against a real `git init -b main` with no origin, and invoke the real checkpoint script via subprocess. The clean-tree assertions (`status --porcelain == ""`) close the untracked-short-circuit escape hatch, so the PASS fixtures genuinely exercise the new path. The 4th test (real-parent, non-root window) is **valuable, not redundant** — it covers the production-shaped `effective_base = real_parent` PASS direction the original 3-test spec left only on the FAIL side. Tests pass (42 incl. pre-completion gates; full Check-10 suite green per report).

### Issues

#### Critical (Must Fix)
None.

#### Important (Should Fix)
None. The implementation is correct, behavior off the on-base path is unchanged, and the fix is covered by real-git tests in both directions.

#### Minor (Nice to Have)

- **`deviations.md:24` (Task 8 "Concern" row) is factually wrong about the `feature_dir="."` edge and mislabels a fail-OPEN case as fail-safe.** The row claims a root-level feature_dir "returns None (caller keeps untracked-only changeset, on-base FAIL note)." That is false. I verified in a live repo: `_feature_window_base(repo, ".")` → `git log --reverse -- .` is non-empty → first commit is the root → `rev-parse <root>^` fails → it returns `_EMPTY_TREE_SHA`, **not None**. The empty-tree branch in `_in_changeset` then treats *every committed tracked file* as in-changeset — i.e. fail-**OPEN**, not the safe "untracked-only / FAIL" the row asserts. The implementer **report's** Concerns section gets this right ("would return the empty tree for ANY first commit"); only the deviations register entry is wrong. **Why it's Minor and does NOT block merge:** the shipped in-scope behavior is correct, and the live invariant holds — the SDD feature dir is always a real `docs/imp-plans/...` subdir (enforced by the output-path convention), so this edge is unreachable in practice. **Fix:** correct the `deviations.md` row text to match the report — name the empty-tree (fail-open) edge, not None/FAIL — so the register doesn't seed a wrong mental model for the next reader. Doc-accuracy only.

- **The `on_base_no_window=True` note-appending branch (`:1753-1758`) has no direct test.** The three PASS/FAIL fixtures all exercise paths where a feature commit exists (real-parent or empty-tree), so the "no commit yet touching the feature dir" diagnostic string is never asserted. **Minor, not Important:** the branch only alters FAIL *diagnostic text* — no gate decision depends on it (the FAIL itself is already produced by `_in_changeset` returning False). Nice-to-have coverage; does not block.

- **`_merge_base_is_head` is only covered indirectly** (through tests 2/3/4, which depend on it returning True on-main). Fine as-is — its branches are reached by the existing fixtures. A direct unit test (True on-main, False off-main) would be nice-to-have, not a gap. Does not block.

### Recommendations

1. Correct the `deviations.md:24` row text to match the implementer report's (accurate) Concerns wording: `feature_dir="."` returns the empty-tree SHA (not None), and the resulting empty-tree diff is fail-**open** for that out-of-scope edge. This is the only actionable item.
2. (Optional, future) When N25 lands its remaining tasks, consider a one-line guard or a direct test pinning the `feature_dir="."` behavior so the documented invariant ("always a real subdir") is enforced rather than assumed — currently it's load-bearing but unchecked. Not for this task.

### Assessment

**Ready to merge?** Yes (with one doc-text correction).
**Reasoning:** The fix is correct and verified against real git in both the PASS (empty-tree visibility) and fail-closed (pre-window FAIL) directions; helpers are clean, well-documented, 3.9-safe, and dead-code-free; both implementer deviations are genuine robustness improvements and are logged. The only finding is a doc-accuracy error in one `deviations.md` row (it mislabels the out-of-scope `feature_dir="."` fail-open edge as fail-safe) — a text fix, not a code fix, on an edge the live output-path invariant makes unreachable.
