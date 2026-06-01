# Code Quality Review — Task 4

**Verdict: Ready to merge — With fixes** (the sole "fix" is a single-source-of-truth recommendation, NOT a correctness defect; controller dispositioned it Accepted + tracked — see below)

## Strengths
- **Spec adherence exact:** threshold `> 0.3` (3/10, 6/20, 9/30 PASS at 30%; 1/3, 4/13, 7/23 FAIL above); divide-by-zero guarded; FAIL detail names every offending task; empty → PASS.
- **Robustness solid:** reviewer exercised 16 malformed inputs (non-dict frontmatter, scalar/dict tasks, non-dict entries, missing/str/float id, YAML errors, unterminated frontmatter, None) — all returned `set()` without crashing.
- **Phantom-ID intersection works:** `verification_ids & all_task_ids` excludes a frontmatter id with no `### Task N` header (0/3, not 1/3). PASS-branch detail uses post-intersection count.
- **FAIL-branch invariant holds:** FAIL only fires when `verif_count ≥ 1`, so `verif_list` never empty there.
- **Float boundary fine; placement/reuse correct** (reuses `all_plan_contents`/`checks`/`blockers`; key==blocker-name pattern). Tests verify real behavior (376 pass; regression 145/0/3). Python 3.9 compat (comment-style typing only, confirmed via grep + compile).

## Issues
**Critical:** None. **Important:** None blocking.

**Minor:**
- `controller-checkpoint.py:254-275` — bool ids slip past `isinstance(int)` (bool subclasses int): `id: true` → `{True}`. Harmless (intersection with headers filters it; identical to the mirrored `_declared_minimum_task_ids`). No action for parity; if a shared helper is extracted, add `and not isinstance(..., bool)` once.

## Recommendation (controller disposition: ACCEPTED + tracked, not done now)
**Extract a shared frontmatter-task-id helper.** `_verification_task_ids` is a near-verbatim copy of `_declared_minimum_task_ids` (identical frontmatter-walk; differs only in field/value + the `parsed_any` return). Reviewer proposes `_task_ids_where(plan_contents, field, value) -> (set, parsed_any)`; callers become `_task_ids_where(c,"review_tier","minimum")` and `_task_ids_where(c,"task_type","verification")[0]`.
**Controller decision:** the plan deliberately specified mirroring `_declared_minimum_task_ids`; the copy is faithful + both paths fully tested; extracting requires refactoring the existing tested `_declared_minimum_task_ids` (out of Task 4 scope, with a `parsed_any` consumer @976) mid-execution. Reviewer rates it non-blocking ("Recommendation, not Important blocker"). Logged in deviations.md as a tracked single-source-of-truth follow-up (BACKLOG candidate); flagged to the user for a call. NOT blocking Task 4 completion.
- (Minor, optional) Check 8 has no e2e coverage; acceptable given thorough unit coverage + the e2e suite exercises the ratio plumbing via review_tier.

## Assessment
**Ready to merge: With fixes** (judgment call only). Implementation correct, robust, spec-faithful (threshold/no-divide-by-zero/naming/intersection all empirically verified), well-tested (4 new + 376 total; regression 145/0/3), 3.9-compatible. Sole substantive finding is the duplicated helper (single-source-of-truth) — low-risk, accepted-by-spec, tracked as follow-up.
