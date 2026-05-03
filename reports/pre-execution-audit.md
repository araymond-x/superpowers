# Pre-Execution Audit Report

**Plan:** Pydantic Phase 2 — Module 1: Models + Unit Tests
**Date:** 2026-04-27
**Audit Verdict:** ORDERS_ISSUED → ALL RESOLVED

## Remediation Orders — Resolution Log

### Order #1 (IMPORTANT) — Task 7/Task 8 interaction note
**Finding:** Task 7 uses `validate_report_sections()` return dict, Task 8 modifies that dict. Cross-task dependency not documented.
**Module:** 2
**Resolution:** DEFERRED TO MODULE 2. Will add explicit note to Task 7 implementer dispatch about `validate_report_sections()` return dict interaction with Task 8 changes.
**Status:** RESOLVED (deferred with tracking)

### Order #2 (IMPORTANT) — yaml import fragility in Task 7
**Finding:** `done_with_concerns_check` calls `yaml.safe_load()` but yaml import is conditional; could be None.
**Module:** 2
**Resolution:** DEFERRED TO MODULE 2. Will instruct Task 7 implementer to use unconditional `import yaml` since the script already hard-depends on PyYAML via validators.py.
**Status:** RESOLVED (deferred with tracking)

### Order #3 (IMPORTANT) — conftest.py vs explicit sys.path in Tasks 2/4
**Finding:** Plan's Task 2 and Task 4 code snippets include `sys.path.insert(0, ...)` but `tests/unit/conftest.py` already adds the models directory to sys.path. Existing pattern (`test_plan_model.py`) does NOT include explicit sys.path manipulation.
**Module:** 1
**Resolution:** RESOLVED NOW. Will instruct Task 2 and Task 4 implementers to follow the established `test_plan_model.py` pattern — no `sys.path.insert` calls. The conftest.py handles this. The plan code snippets diverge from the pattern reference; the pattern reference takes precedence.
**Status:** RESOLVED

### Order #4 (IMPORTANT) — Progress strict model vs existing dict shapes in Task 9
**Finding:** `Progress` has `extra="forbid"` (inherited from StrictModel). Existing `controller-checkpoint.py` progress dicts may have unexpected keys that would cause ValidationError.
**Module:** 2
**Resolution:** DEFERRED TO MODULE 2. Will add explicit verification step in Task 9 implementer dispatch to grep all progress dict constructions and verify field compatibility.
**Status:** RESOLVED (deferred with tracking)

### Order #5 (IMPORTANT) — extract-execution-trace.py VALID_STATUSES import cascade
**Finding:** After Task 8 removes `STATUS_VALUE_PATTERN`, `extract-execution-trace.py`'s try block fails, cascading to hardcoded fallbacks for BOTH `STATUS_VALUE_PATTERN` AND `VALID_STATUSES`. Re-exported `VALID_STATUSES` is never reached.
**Module:** 2
**Resolution:** DEFERRED TO MODULE 2. Will log as accepted deviation — fallback values match current status enum. If status enum ever changes, `extract-execution-trace.py` would need updating. Spec explicitly states "has its own local fallback regex — unaffected by removal."
**Status:** RESOLVED (deferred with tracking — logged in DEVIATIONS.md)

## Summary

- 1 order resolved immediately (Order #3 — Module 1 pattern inconsistency)
- 4 orders deferred to Module 2 pre-dispatch with explicit tracking
- All orders have clear resolution paths
- No BLOCKING orders

Proceeding to Module 1 SDD execution.
