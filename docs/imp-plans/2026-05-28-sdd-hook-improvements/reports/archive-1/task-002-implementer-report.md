---
schema_version: 1
task_id: 2
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/subagent-driven-development/scripts/validate-plan.py"
    description: "Added check_review_tier_heuristic(frontmatter) + _ALWAYS_FULL_KEYWORDS/_MIGRATION_DATA_KEYWORDS module constants (~line 337); wired into validate_plan after the enforcement-tier block (appends to warnings, records sections['review_tier_heuristic'])."
  - path: "tests/unit/test_validate_plan.py"
    description: "Added TestReviewTierHeuristic (5 tests) + _review_tier_plan builder; reused existing run_validate helper."
tests:
  written: 5
  passing: 5
  command: ".venv/bin/python3 -m pytest tests/unit/ -q"
  result: PASS
contract_compliance:
  - constraint: "warn on review_tier:minimum + refactor|service|security|business logic|auth"
    status: compliant
    detail: "_ALWAYS_FULL_KEYWORDS exact list; substring match per plan's verbatim code."
  - constraint: "warn on migration ONLY with backfill|update|delete|transform|data; never alone"
    status: compliant
    detail: "migration branch only checks _MIGRATION_DATA_KEYWORDS; test_no_warn_migration_alone confirms silent."
  - constraint: "WARNING (exit 2), not FAIL (exit 1)"
    status: compliant
    detail: "Appends to warnings list (not blockers); verified via subprocess exit code."
  - constraint: "review_tier orthogonal to enforcement_tier"
    status: compliant
    detail: "Per-task review_tier check, independent of plan-level enforcement_tier."
---

**Implementation Summary:**
Added a non-blocking review_tier heuristic to validate-plan.py. `check_review_tier_heuristic(frontmatter)` iterates `tasks`, skips non-`minimum` tasks, and warns when a minimum-tier task's lowercased title contains an always-full keyword, or (only if the title contains "migration") a data-manipulation keyword. Wired into validate_plan via the enforcement-tier Pattern Reference idiom (append to `warnings`, record `sections["review_tier_heuristic"]`). TDD: RED showed the 2 positive-test failures; GREEN → 24 in file, 338 in suite (333+5). Python 3.9 compat preserved (legacy `Optional[Dict]`/`List[str]` matching the file). Skill regression 146 PASS.

**Source Files Read:**
- `validate-plan.py` (helper area ~325, enforcement-tier block 531-563) — confirmed in-scope `frontmatter`/`warnings`/`sections` names, legacy typing imports (line 27), Pattern Reference idiom.
- `tests/unit/test_validate_plan.py` — reused existing `run_validate` helper.
- `skills/scripts/models/plan.py:31` — confirmed Task 1's review_tier field so fixtures pass Pydantic.

**CLAUDE.md Files Read:**
- Project + global CLAUDE.md (system context) — Python 3.9 compat, full test paths, explicit two-path git add, Co-Authored-By trailer.
- `skills/subagent-driven-development/scripts/CLAUDE.md`, `tests/unit/CLAUDE.md` — checked, neither exists.

**Deviations from Plan:**
- Reused existing `run_validate` helper (returns `{exit_code, output, stderr}`) instead of the snippet's `_run_validate`/`_plan`; plan builder named `_review_tier_plan` to avoid collision. Exactly as the task instructed ("reuse equivalents"). Not a behavioral divergence.

**Self-Review Findings:**
- All 3 negative tests meaningful (ddl_title silent; migration_alone silent — the contract's core case; full_tier_never_warns proves the minimum gate). Positive migration_with_backfill triggers via the migration data-keyword branch only.

**Concerns:**
- Substring matching (per the plan's verbatim `kw in title` code) means "auth"⊂"author", "data"⊂"database", "delete"⊂... could draw a false-positive WARNING on a minimum-tier task with such a title. Non-blocking (author resolves/accepts) and spec-faithful (the plan prescribed the exact keyword list + substring match). Flagged for a possible future word-boundary improvement; NOT fixed here (would diverge from the plan's exact code).
