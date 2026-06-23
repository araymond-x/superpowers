---
schema_version: 1
task_id: 8
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: skills/subagent-driven-development/scripts/controller-checkpoint.py
    description: "Added _EMPTY_TREE_SHA + _merge_base_is_head + _feature_window_base helpers (above _resolve_base_ref); _in_changeset empty-tree direct-diff special-case; captured manifest_feature_dir in run_pre_completion; applied feature-window effective_base in Check 10 else branch."
  - path: tests/unit/test_c2_integration_gate.py
    description: "Added TestFeatureWindowBase (4 tests) with a manifest-mode run harness: None-when-no-feature-commit, on-main committed IT PASS via empty-tree edge (the fix), on-main pre-window file still FAILs (fail-closed counter-fixture), and on-main real-parent (non-root) window PASS."
tests:
  command: ".venv/bin/python3 -m pytest tests/unit/test_c2_integration_gate.py tests/unit/test_pre_completion_gates.py -v"
  written: 4
  passing: 4
  result: PASS
contract_compliance:
  - constraint: "Fail-closed preserved — a file committed BEFORE the feature window must still FAIL."
    status: compliant
    detail: "test_on_main_prewindow_file_still_fails asserts FAIL + blocker. _feature_window_base returns the REAL parent (commit 1) when the feature dir is not the repo root, so diff(parent, HEAD) for the pre-window IT is empty → FAIL."
  - constraint: "Behavior unchanged off the on-base path (merge-base != HEAD → effective_base == base_ref)."
    status: compliant
    detail: "All 12 pre-existing TestC2Check10 tests + TestGitRunSSOT + test_pre_completion_gates (68 total) pass unchanged. The else-branch only diverges when _merge_base_is_head is True; otherwise effective_base = base_ref."
  - constraint: "3.9-safe `# type:` comments (no PEP-604 unions) for the new helpers."
    status: compliant
    detail: "_merge_base_is_head and _feature_window_base use `# type: (str, str) -> bool` / `-> Optional[str]` line comments; Optional already imported (line 43)."
  - constraint: "Write-scope: only controller-checkpoint.py + test_c2_integration_gate.py."
    status: compliant
    detail: "git status shows exactly those two files modified. _git_run / _review_tiers_per_task / _merged_dispatch_times / frontmatter scan / not-a-file message untouched."
  - constraint: "New helpers pass git_root (truthy) as cwd to _git_run; no empty-cwd."
    status: compliant
    detail: "Both helpers pass cwd=git_root (from _resolve_git_root, always truthy)."
---

# Task 8 — N25a: Check 10 feature-window fallback (on-main false-block fix)

## Implementation Summary

When SDD runs on the base branch in a remoteless repo, `_resolve_base_ref` picks `main` and `merge-base(main, HEAD) == HEAD`, so the diff window vs merge-base is empty and committed feature files are invisible to `_in_changeset` — Check 10 falsely FAILs an integration test that was committed within the feature. N25a fixes this by recomputing an effective base = the parent of the first commit touching the feature dir; the root-commit edge (feature dir IS the repo root) returns git's empty-tree SHA, which `_in_changeset` now special-cases as a direct diff base.

Five changes to `controller-checkpoint.py`:
1. **`_EMPTY_TREE_SHA`** module constant (`4b825dc6...`) above `_resolve_base_ref`.
2. **`_merge_base_is_head(git_root, base_ref)`** — True iff `merge-base(base_ref, HEAD) == HEAD` (the on-base-branch precondition).
3. **`_feature_window_base(git_root, feature_dir)`** — parent of the first commit touching `feature_dir`; root-commit → empty-tree SHA; no feature commit / empty feature_dir → None.
4. **`_in_changeset` Step-3b special-case** — when `base_ref == _EMPTY_TREE_SHA`, diff the empty tree directly against the working tree (a tree object has no merge-base with HEAD, so the existing merge-base path would silently fall back to diff-vs-HEAD and hide committed files). Placed AFTER the untracked check, BEFORE the merge-base block.
5. **`manifest_feature_dir` capture** in `run_pre_completion` + the Check-10 `else` branch computes `effective_base`/`on_base_no_window`, passes `effective_base` to `_in_changeset`, names `effective_base` in PASS/FAIL details, and appends an on-base explanatory note when `on_base_no_window` is True.

TDD: 3 failing tests written first (`TestFeatureWindowBase`), confirmed RED (None test = AttributeError; on-main PASS fixture = the exact "no diff vs main" bug), then GREEN after the implementation. A 4th test (`test_on_main_real_parent_window_passes`) was added post-implementation to assert the real-parent (non-root window) path in the PASS direction — advisor-recommended, closing the loop the original 3-test spec left on the FAIL side only.

Two advisor-driven refinements applied after the first green pass (both non-blocking, both improve correctness):
- **Note accuracy:** the feature-window lookup is now gated on `manifest_feature_dir` being non-empty (`if manifest_feature_dir and _merge_base_is_head(...)`). Previously, in non-manifest mode `manifest_feature_dir == ""` set `on_base_no_window = True` and appended a note ("no commit yet touching the feature dir") that misattributed the cause — the real reason there is "no feature dir known." Now the note only fires when there genuinely IS a feature dir but no commit touches it yet; non-manifest on-main FAILs keep the clean original wording. Gate decisions unchanged.
- **Coverage:** the 4th PASS test above.

## Source Files Read

- `skills/subagent-driven-development/scripts/controller-checkpoint.py` — `_git_run` (:483), `_resolve_base_ref` (:501), `_in_changeset` (:550), the manifest-load block in `run_pre_completion` (:1335-1350 pre-edit), the Check-10 `else` branch (:1650-1706 pre-edit), `_resolve_git_root` (:744), and the argparse (`--plan-file`/`--manifest` both accepted; pre-completion reads `args.plan_file`/`--deviations-file`/`--reports-dir` from CLI even in manifest mode).
- `tests/unit/test_c2_integration_gate.py` — `TestC2Check10` harness (`_git`/`_setup_repo`/`_run_checkpoint`), `_c2_plan` fixture builder, `IT_PATH`, `_GIT_ENV`, `CHECKPOINT_SCRIPT`, and `test_merge_base_committed_on_branch_clean_tree_passes` (clean-tree assertion pattern).
- `tests/unit/sdd_test_helpers.py` — `_write_manifest` (writes `.sdd-session.json` + `.active-feature`; `paths.feature_dir`).
- `docs/imp-plans/2026-06-10-sdd-aggregate-gate-visibility/module-2-calibration.md` — Task 8 (7 steps) + the Step-1 NOTE on fixture properties.

## CLAUDE.md Files Read

- Repo-root `CLAUDE.md` — Check 10 (`integration_test_present`), `_resolve_base_ref` (newest-merge-base base ref), `_in_changeset` (untracked ∪ diff changeset), the C2 gate, and the documented "stale unpushed origin/HEAD is fail-open otherwise — found live in this repo" rationale.

## Deviations from Plan

1. **`manifest_feature_dir` captured BEFORE `_load_all_plan_contents`, not after (Step 4).** The plan's Step 4 snippet places `manifest_feature_dir = _md.get(...)` AFTER `all_plan_contents = _load_all_plan_contents(...)` inside the try. I captured it immediately after `_md = json.loads(...)` and before `_load_all_plan_contents`. Rationale: if `_load_all_plan_contents` raises, the `except` swallows it and `manifest_feature_dir` would silently stay `""`, disabling the entire N25a fix with no signal. Capturing first makes the feature-window base robust to a plan-load failure. This was the advisor's explicit defensive alternative; behavior is identical on the happy path. No contract impact.

2. **Test harness: dedicated manifest-mode run helper, not the existing `_run_checkpoint`.** The plan's Step-1 NOTE says "run pre-completion with `--manifest`." The existing `TestC2Check10._run_checkpoint` passes only `--plan-file`, which leaves `manifest_feature_dir == ""` (fix disabled). I added `TestFeatureWindowBase._run_manifest_checkpoint` (passes `--manifest` AND `--plan-file`/`--deviations-file`/`--reports-dir`) plus `_init_main_repo` and `_write_feat_manifest` rather than reusing `_setup_repo`/`setup_manifest_workspace` — both do a single all-in-one commit, which would destroy the commit ordering the fix depends on (feature-dir-first vs IT-first). I drive my own ordered commits.

3. **Feature dir is a real subdir (`docs/imp-plans/feat`), not `"."`.** `_feature_window_base` runs `git log -- <feature_dir>`; with `"."` every root commit is the feature window, so the counter-fixture would wrongly PASS and lose fail-closed. Used a real subdir in the manifest.

4. **Remove `.active-feature` after `_write_manifest`.** `_write_manifest` drops a root-level `.active-feature` (a hook input). `controller-checkpoint.py` loads the manifest by explicit `--manifest` path and never reads `.active-feature`, so I unlink it in the fixture to keep the working tree clean — required so `_in_changeset`'s untracked short-circuit does NOT mask the new empty-tree path being exercised.

## Self-Review Findings

- **Green-for-the-wrong-reason guard:** In both new fixtures the declared IT is COMMITTED and the tree is asserted CLEAN (`status --porcelain == ""`). If the IT were left untracked, `_in_changeset`'s untracked check would short-circuit to True and the test would pass WITHOUT exercising the new empty-tree Step-3b branch. The clean-tree assertions ensure the PASS fixture genuinely tests the fix (verified: pre-fix RED showed "no diff vs main", proving the untracked path was not firing).
- **Counter-fixture genuinely fail-closed:** committing the IT as the repo ROOT (pre-window) gives `_feature_window_base` a real parent (commit 1); `diff(commit1, HEAD)` for the IT is empty → FAIL. Confirmed FAIL post-fix.
- **Off-path behavior unchanged:** the `else` branch only diverges when `_merge_base_is_head` is True; all 12 pre-existing `TestC2Check10` cases (several already on-main with merge-base==HEAD but run WITHOUT `--manifest` → `manifest_feature_dir == ""` → `_feature_window_base` → None → `on_base_no_window=True` → `effective_base == base_ref`) pass unchanged.
- **3.9 compat:** new helpers use `# type:` line comments, no PEP-604 unions. `Optional` already imported.
- **Scope:** kept the existing `"missing on disk"` not-a-file message (the `is_dir()` detail is Task 9). `_git_run`/`_review_tiers_per_task`/`_merged_dispatch_times`/frontmatter scan untouched.

## Concerns

None blocking. One forward note: `_feature_window_base` keys on `feature_dir` from the manifest `paths.feature_dir`; if a future manifest stores `feature_dir` as `"."` (root-level feature), the root-commit edge would return the empty tree for ANY first commit. That is out of scope here (Task 8 only fixes the real-subdir on-base case), and the live feature dir is always a real subdir per the output-path convention.
