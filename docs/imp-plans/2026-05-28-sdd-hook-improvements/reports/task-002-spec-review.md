# Task 2 — Spec Compliance Review

**Verdict:** ✅ PASS (spec + contract compliant)
**Reviewer:** general-purpose spec compliance auditor
**Diff:** 7406de0..59fe125 (2 files, +124)

## Contract constraints — all verified empirically
1. Always-full keywords (refactor|service|security|business logic|auth) — exact list (validate-plan.py:332); warns on minimum tier. ✓
2. **Migration ONLY warns with data keyword; NEVER alone** — verified 4 ways: "Add migration for new column"→no warn (exit 0); "Migration with backfill"→warn; "data migration to delete rows"→warn. Correct nesting (lines 353-356). ✓
3. WARNING not FAIL — appends to `warnings`, never `blockers`; review-tier-only plan exits 2 (not 1). ✓
4. Orthogonal to enforcement_tier — reads only task["review_tier"]; `review_tier: full` never warns even with highest-risk title (early continue). ✓

## Tests — 5 present, meaningful, non-vacuous
TestReviewTierHeuristic (test_validate_plan.py:570-627): 2 positive + 3 negative. Negatives reproduced through CLI → warnings:[] (clean PASS); "review_tier" substring is unique to this heuristic (not ⊂ "enforcement_tier"), so negatives genuinely fail if logic emits spurious warning. test_no_warn_migration_alone guards the critical case.

## Test suite
- test_validate_plan.py → 24 passed (5 new + 19). tests/unit/ → 338 passed (333+5), no regression.

## Substring concern — assessed ADVISORY (correctly classified)
- "data"⊂"database" is a NON-issue (data keywords only apply when "migration" in title). Only "auth"⊂"author" is a real, rare false positive.
- Spec prescribed `kw in title` substring + this keyword list; word-boundary matching would itself be a plan deviation. Advisory gate ("Confirm this is genuinely mechanical") tolerates an occasional false-positive prompt. Implementer right to flag, right not to fix.

## Extra work
None — exactly function + 2 constants + wiring + 5 tests.
