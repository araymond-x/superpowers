# Task 8 (N25a) — Spec Compliance Review

**Verdict: PASS** — spec-compliant and fail-closed-compliant. Verified by reading code and running the counter-fixture + off-path suites, not by accepting the report.

Scope: BASE `c06b230` (Task 7) → HEAD `c79531b` (Task 8). Exactly 2 files committed: `controller-checkpoint.py`, `tests/unit/test_c2_integration_gate.py`.

---

## Fail-closed verification (the critical bar) — CONFIRMED, not a false PASS

I reasoned through WHY the counter-fixture FAILs the gate and reproduced it in a scratch repo (not just trusting the green test):

- `test_on_main_prewindow_file_still_fails` PASSES. The IT is committed as the ROOT (pre-window); the feature dir is committed as commit 2. `_feature_window_base` returns commit 1's REAL SHA (parent of the first feature-dir commit). I confirmed in a scratch repo that `git diff --name-only <root_sha> -- <IT>` is **genuinely empty** (the IT predates the feature window), so `_in_changeset` returns False → `integration_test_present` FAILs and is appended to `blockers`. This is a real fail-closed FAIL, not a fixture artifact: the feature's own `plan.md` IS in `diff(root_sha, HEAD)` while the pre-window IT is not. A file committed BEFORE the feature window still FAILs. ✔

- `test_on_main_committed_integration_test_passes` PASSES (the fix). Feature dir committed as ROOT → `rev-parse FIRST^` fails (no parent) → `_feature_window_base` returns `_EMPTY_TREE_SHA`. I confirmed in a scratch repo that `git merge-base 4b825dc6… HEAD` errors with "is a tree, not a commit" (rc 128), so the OLD merge-base path silently fell back to `diff HEAD` which is empty and hid the committed IT — exactly the documented bug. The new Step-3b `git diff --name-only <empty-tree> -- <path>` correctly returns the IT. The fixture commits the IT and asserts a clean tree (`status --porcelain == ""`), so `_in_changeset`'s untracked short-circuit does NOT fire — the empty-tree path is what produces the PASS. ✔

- `test_on_main_real_parent_window_passes` (the 4th, implementer-added) PASSES — the non-root window where `effective_base` is a REAL parent (not the empty tree), in the PASS direction. Closes the loop the plan's 3-test spec left only on the FAIL side. ✔

All 4 `TestFeatureWindowBase` tests pass.

## Step-by-step code verification

- **Step 3 helpers** (controller-checkpoint.py:501–537): `_EMPTY_TREE_SHA = 4b825dc6…` (git's well-known empty tree). `_merge_base_is_head` returns True iff `merge-base(base,HEAD)==HEAD`, both via `_git_run`, fail-CLOSED on any None/non-zero rc and on empty HEAD. `_feature_window_base` returns the parent of the first commit touching `feature_dir`, `_EMPTY_TREE_SHA` at the root-commit edge (`rev-parse FIRST^` fails), `None` when `feature_dir` is falsy or no commit touches it. 3.9-safe `# type:` comments; `Optional` is imported (line 43). ✔
- **Step 3b** (`_in_changeset`, :607–613): the empty-tree direct-diff is placed AFTER the untracked check (:603–605) and BEFORE the merge-base block (:615) — exactly as specified. Gates correctly on `diff is not None and rc==0 and stdout.strip()`. ✔
- **Step 4** (manifest_feature_dir, :1385–1395): captured BEFORE `_load_all_plan_contents` (deviation 1, see below). ✔
- **Step 5** (Check-10 else, :1724–1780): `effective_base` defaults to `base_ref`; only diverges when `manifest_feature_dir` truthy AND `_merge_base_is_head`; passes `effective_base` (not `base_ref`) to `_in_changeset`; names `effective_base` in both PASS and FAIL details. ✔

## The two implementer deviations — both SOUND, neither weakens fail-closed

1. **`manifest_feature_dir` captured BEFORE `_load_all_plan_contents`** (:1389, with explanatory comment). I read the order: `_md = json.loads(...)` (:1388) → `manifest_feature_dir = _md.get("paths",{}).get("feature_dir","")` (:1389) → `_gr = _resolve_git_root(...)` → `_load_all_plan_contents(...)`. A `_load_all_plan_contents` failure now lands in `except` WITHOUT silently leaving `manifest_feature_dir=""` and disabling the fix. Behavior-equivalent on the happy path, strictly more robust on the failure path. This is a hardening, not a weakening. ✔
2. **Feature-window lookup gated on `manifest_feature_dir` non-empty** (`if manifest_feature_dir and _merge_base_is_head(...)`, :1734). This does NOT weaken fail-closed: in non-manifest mode `effective_base` stays `base_ref` — the exact pre-N25a behavior. The gate decision is unchanged; only the on-base explanatory note is suppressed in non-manifest mode (where it would misattribute the cause). The N25a fix is a strict relaxation that only fires on the genuine on-base manifest path; non-manifest mode is byte-for-byte the old code path. ✔

## Behavior unchanged off the on-base path

`tests/unit/test_c2_integration_gate.py` + `tests/unit/test_pre_completion_gates.py`: **69 passed**. The pre-existing `TestC2Check10*` cases (several on-main, merge-base==HEAD, run WITHOUT `--manifest` → `manifest_feature_dir==""` → fix never fires → `effective_base==base_ref`) all pass unchanged. ✔

## Scope

Diff hunks touch only: helper insertion after `_git_run` (its def line is the hunk anchor; body unchanged), `_in_changeset` Step-3b, and four `run_pre_completion` edits. `_git_run` / `_review_tiers_per_task` / `_merged_dispatch_times` definitions are UNTOUCHED (grep confirmed none appear as +/- def lines). The not-a-file branch still says `"{}: missing on disk"` (single occurrence, :1747) — the `is_dir()` message is correctly deferred to Task 9. Exactly 2 files committed. ✔

## Report completeness

All 5 prose sections present (Implementation Summary, Source Files Read, Deviations from Plan, Self-Review Findings, Concerns). Frontmatter valid; `status: DONE_WITH_CONCERNS` with a non-blocking forward note (`feature_dir == "."` edge, explicitly out of scope and matching the documented output-path convention — accepted, not a defect). ✔

---

## Findings

None blocking. None advisory.

The single `Concern` (DONE_WITH_CONCERNS) — `_feature_window_base` assumes a real-subdir `feature_dir`; a `"."` feature_dir would hit the empty-tree edge for any first commit — is correctly scoped out (the SDD output-path convention always uses a real subdir like `docs/imp-plans/...`) and is already recorded as a forward note in deviations.md. It is not a fail-closed weakening: a `"."` feature_dir is not a configuration the live pipeline produces, and the test fixtures deliberately use a real subdir to keep the counter-fixture honest.

**PASS.**
