# Plan Review Report — SDD Aggregate-Gate Visibility

Plan set reviewed (modular): `plan.md` (parent) + `module-1-aggregate-visibility.md` + `module-2-calibration.md`.
Spec: `spec.md` + `spec-distilled.md`. Source contracts: None external (self-hosting — snippets verified against current repo source).

**Final status: APPROVED** (round 2). Round 1 found 3 blocking issues; all were fixed and confirmed in round 2.

---

## Round 1 — Issues Found (3 BLOCKING, all empirically verified)

**1. [Snippet/Source — internal contradiction] Module 2, Task 6 (N22):** The RED test asserted `securing` must warn, but the prescribed stem regex `securit\w*` does not match `securing` (stem is `securit`, not `secur`). The implementer would write a test the prescribed code can't turn green.
→ **Fix:** test must-match list changed to `("migrations", "caches", "routers", "authentication", "security")` (`security` matches `securit\w*`; `securing` removed), honoring the spec's D8 pattern.

**2. [Snippet/Source — internal contradiction] Module 2, Task 7 (N25c):** The test asserted `_git_run(["status"], cwd="/no/such/dir/xyz") is None`, but git execs and exits rc=128 without raising → `subprocess.run` returns `CompletedProcess(returncode=128)`, never `None`. `_git_run` returns `None` only on `TimeoutExpired`/`OSError`.
→ **Fix:** test renamed `test_git_run_handles_failure`; assertion changed to `result is None or result.returncode != 0` (matches the helper's real behavior; callers gate on returncode).

**3. [Consumer-contract bug] Module 2, Task 8 (N25a):** `_feature_window_base` returns `_EMPTY_TREE_SHA` for the root-commit edge, but its consumer `_in_changeset` computes `merge-base(base, HEAD)` first — and `merge-base(<tree>, HEAD)` FAILS (a tree is not a commit), silently falling back to `diff HEAD`, hiding committed files. The on-main PASS fixture (whose feature-dir commit is the repo root via `TestCheck10._setup_repo`) would therefore FAIL.
→ **Fix:** (a) new **Step 3b** adds a direct-diff special-case to `_in_changeset` (`if base_ref == _EMPTY_TREE_SHA: git diff --name-only <empty-tree> -- <path>`), inserted after the untracked check and before the merge-base block; (b) `_feature_window_base` docstring corrected (no longer claims the empty tree is directly "usable as a diff base"; states the consumer special-cases it); (c) on-main fixture NOTE explains the root-commit/empty-tree path and that the counter-fixture creates a pre-feature commit for a real parent.

### Round 1 — Verified-clean findings
- Snippet verification: M1 Task 1 (`_review_tiers_per_task`), M1 Task 2 (`_merged_dispatch_times` + guard), M1 Task 3 (Stage-0 hook + Check 3b), M1 Task 4 (`validate_module_completion`), M2 Task 5 (`_unfenced_content`) — all VERIFIED (anchors present verbatim, invariants preserved).
- Dispatch-log contract (N26 writer ↔ N27 reader): coherent — marked fix emits only `type=fix`, never `type=implementer`; Check 9 parser matches only `type=implementer`; the test asserts the absence of `type=implementer`.
- Ordering: N20→N22; N25c→N25a→N25b+d+f; inventory-doc (12) → verification (13, non-last) → e2e (14, last) — all correct.
- Size/Source Contracts: both module files carry a `# Module` header (800-exempt); Source Contracts None ⇒ no Task 0 (correct per N7); all tasks ≤200 lines; Write-Scope table present.

### Round 1 — Advisory (non-blocking)
- Citation drift: M1 Task 3 Step 8 cited "line 757" for the `CONTEXT="$CONTEXT | $PROCESS_CONTRACT"` anchor; actual ~772. → Fixed ("~line 772; the anchor text is unique").
- N6 (Task 10) framing additions grow the three sites; the implementer must hold net `wc -w ≤ 4911` (the task's Step 4 trim-if-over guard enforces this — not free headroom).

---

## Round 2 — Re-Review: APPROVED

**Fix 1 (N22): CONFIRMED** — Step 1 must-match list and Step 3 `securit\w*` regex are mutually consistent; empirically `security` matches, `securing` does not; keywords sit in unfenced prose so Step 4's `_unfenced_content` wrap is unaffected.

**Fix 2 (_git_run): CONFIRMED** — bad-cwd git exits rc=128 (empirically `CompletedProcess(returncode=128)`, never None); helper returns None only on `TimeoutExpired`/`OSError`; the rewritten assertion `result is None or result.returncode != 0` matches actual behavior.

**Fix 3 (empty-tree): CONFIRMED** — (a) Step 3b inserts cleanly (anchor: untracked-check return at `_in_changeset` ~516-518, merge-base block ~520-523; special-case slots into the gap, uses the `_git`→`_git_run` delegation from Task 7); (b) docstring corrected; (c) fixture NOTE explains root-commit/empty-tree + counter-fixture parent. Empirically: `git diff --name-only <empty-tree> -- <path>` lists a present file; `merge-base(<empty-tree>, HEAD)` fails rc=128. Trace: PASS fixture (root → empty-tree → Step 3b diff lists committed file → PASS); counter-fixture (pre-window file at C0, feature at C1 → real parent C0 → Step 3b skipped → empty diff → FAIL). Fail-closed preserved.

**New issues introduced by the fixes:** none. `effective_base == _EMPTY_TREE_SHA` only when `_merge_base_is_head` AND the root-commit edge both hold; every normal off-main/PR flow uses a real ref and Step 3b never fires, so existing Check 10 tests are untouched. The pre-existing RISK_PLAN fixture keeps `auth`/`middleware` in unfenced prose, so Step 4's fence-exclusion doesn't flip it.

**Numbering/cross-ref coherence: OK** — module-1 = Tasks 1-4; module-2 = Tasks 5-14 (7=N25c, 8=N25a, 9=N25b+d+f, 13=verification non-last `task_type: verification`, 14=e2e last); strictly sequential `depends_on` chains; the three load-bearing cross-task refs (Task 8 uses Task 7's `_git_run`; Task 9 extends Task 8's not-a-file branch; Task 9 builds on Task 8's frontmatter edits) are intact; no `### Task`/step renumbering broke a cross-reference.

---

## Validation gate status

- `validate-plan.py`: **PASS** on all three files (no blockers, no warnings; every task ≤200 lines).
- Pydantic `validators.py plan`: **PASS** (exit 0) on all three (sequential task IDs, valid dependency refs, module-task consistency).
- Plan-document-reviewer: **APPROVED** (round 2).
