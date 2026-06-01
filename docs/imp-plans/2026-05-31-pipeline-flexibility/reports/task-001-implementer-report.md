---
schema_version: 1
task_id: 1
status: DONE
files_changed:
  - path: "skills/subagent-driven-development/scripts/validate-plan.py"
    description: "Added _VERIFICATION_WRITE_KEYWORDS tuple, compiled _VERIFICATION_KEYWORD_RE, check_verification_keyword_heuristic() function after check_review_tier_heuristic(), and its call site in validate_plan() after the review_tier heuristic block."
  - path: "tests/unit/test_validate_plan.py"
    description: "Added module-level FRONTMATTER_PLAN fixture and TestVerificationKeywordWarning class (5 tests) after TestReviewTierHeuristic."
tests:
  written: 5
  passing: 5
  command: ".venv/bin/python3 -m pytest tests/unit/test_validate_plan.py -v"
  result: PASS
contract_compliance:
  - constraint: "Task extends StrictModel; Plan extends SchemaVersionedModel."
    status: not_applicable
    detail: "No model files touched — only validate-plan.py and its test. Heuristic reads parsed YAML frontmatter dicts directly."
  - constraint: "No schema version bump."
    status: compliant
    detail: "CURRENT_SCHEMA_VERSION untouched; no models/ files modified."
  - constraint: "WARNING keywords (case-insensitive, word-boundary): create, add, implement, fix, modify, write, update, refactor, migrate, delete, remove."
    status: compliant
    detail: "All 11 keywords present in _VERIFICATION_WRITE_KEYWORDS; regex uses \\b...\\b boundaries and re.IGNORECASE."
  - constraint: "WARNING not FAIL."
    status: compliant
    detail: "Call site appends to warnings (not blockers); section status='WARNING'; exit_code asserted == 2 by test."
---

**Implementation Summary**
Added a plan-time WARNING heuristic to `validate-plan.py` that mirrors the existing `check_review_tier_heuristic`. When a task in the plan frontmatter declares `task_type: verification` but its title contains a write-suggesting keyword (create, add, implement, fix, modify, write, update, refactor, migrate, delete, remove), the validator emits a `verification_keyword_warning` and exits with code 2 (WARNING). The check is gated on `task_type == "verification"`, so the default `implementation` type never triggers it. Multiple keywords in one title are aggregated into a single warning string. Followed strict TDD: wrote 5 tests, confirmed correct RED (2 failures — the "warning present" assertions failed because the heuristic was absent; 3 "no warning" tests passed trivially; no Pydantic `extra inputs` error, confirming Task 0's `task_type` field parses), implemented, confirmed GREEN.

**Source Files Read**
- `skills/subagent-driven-development/scripts/validate-plan.py` (full) — confirmed `re` @23 and `Dict, List, Optional, Tuple` @27 already imported; `check_review_tier_heuristic` def @337; call-site block @602-610.
- `tests/unit/test_validate_plan.py` (head + tail) — `run_validate` helper @32 returns `{exit_code, output, stderr}`; reused it. `TestReviewTierHeuristic` last class.
- `skills/scripts/models/plan.py` (grep) — verified Task 0 added `task_type: Literal["implementation", "verification"] = "implementation"` @32 (commit 53c00bd).

**CLAUDE.md Files Read**
- Repo-root `CLAUDE.md` (loaded in context) — Python 3.9 compat requirement for SDD scripts, `.venv/bin/python3` for tests, regression-suite expectations.
- Checked `skills/subagent-driven-development/scripts/CLAUDE.md`, `tests/CLAUDE.md`, `tests/unit/CLAUDE.md` — none exist; no subdirectory overrides apply.

**Deviations from Plan**
None. Implemented exactly as specified. (The Edit tool initially matched the 3-line assertion snippet 3 times since it's a shared pattern; I re-anchored on the unique `test_full_tier_never_warns` body to insert after the correct final occurrence — no functional deviation.)

**Self-Review Findings**
- Completeness: all 6 steps executed (RED, implement, GREEN, full file suite 29/29 PASS, regression 145 PASS/0 FAIL/3 advisory WARNING unchanged, commit).
- Contract compliance: all 4 constraints satisfied (see frontmatter).
- No dead code: new function is called; no orphaned helpers.
- Python 3.9 style: uses `typing.Optional/Dict/List` per the SDD-script requirement (regression suite confirms 0 FAIL). Note this intentionally departs from the global modern-typing preference because the repo CLAUDE.md mandates 3.9 compat for this directory and the regression suite enforces it.
- Edge case verified: "Verify orphaned code is removed" produces no warning — `\bremove\b` does not match "removed" (word boundary). Confirmed by passing test.
- No scratch files created (untracked `.venv` and `docs/imp-plans/...` are pre-existing workspace artifacts).

**Concerns**
None.
