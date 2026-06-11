# Task 9 Spec Compliance Review (C2 risk-surface WARNING + Step 0)

> Dispatched 2026-06-10 (provenance: `.dispatch-log` task=9 type=spec-review).
> Reviewed: commits 2db2171 + 14e5906 against module-2-integration-gate.md Task 9 (base 0f26fb4).

## Verdict: PASS (one ADVISORY; no blocking findings)

### Commit/diff integrity — PASS
Exactly the four claimed files; split clean (2db2171 = Step 0 only; 14e5906 = feature only; test file legitimately in both). Commit-2 subject exact; commit-1 subject appropriate (separate commit was the only requirement).

### Step 0 — verified by execution
- **0a PASS**: PEP 562 `__getattr__` (_report_utils.py:21-32) with globals() caching. Bare python3 importlib load of validate-plan.py → `pydantic in sys.modules: False`. VALID_STATUSES still resolves lazily (4 statuses). Accessor-over-function rationale checks out (extract-execution-trace.py:40 attribute access works; unknown attrs raise AttributeError).
- **0b PASS**: probed — "" REJECTED, "  " REJECTED, ".." REJECTED, "a/b" ACCEPTED; both pin tests present.
- **0c PASS**: no sys.path.insert remains; module-level imports; conftest.py:9 covers models dir.

### Feature — verified by reading
- `_C2_RISK_PATTERNS` + `check_integration_test_risk` (validate-plan.py:417-443) match prescription character-for-character except partner-approved Optional[Dict]/List[str] annotations.
- Call site (validate-plan.py:705) immediately after the verification-keyword check (695); SAME parsed frontmatter (523-532, no re-parse); appends to the status-driving warnings list.
- 3 tests match prescribed semantics exactly; `_H` guard intact; `_load_script` copied verbatim, module name validate_plan_c2; RED at BASE plausible (warning only the new function produces).

### Test runs (actual)
- test_c2_integration_gate.py + test_validate_plan.py: **39 passed**. Full suite: **446 passed, 1 warning**. Regression: **145/0/3 — PASS (with warnings)**.

### Self-hosting — verified by execution (bare python3)
- module-2-integration-gate.md: **exit 2, status WARNING, blockers []**, integration_test_risk_surface present. Gate unaffected: plan-validation-gate-hook.sh:172 blocks only on STATUS="FAIL".
- module-1-cleanup.md: **exit 0, status PASS, no risk warning**. [ADVISORY] the report's hedged prediction that module-1 "likely warns too" is wrong — explicitly a guess, not a verification claim; controller should NOT log a module-1 warning deviation.

### Report completeness — COMPLETE
All sections substantive; 3 deviations documented, all pre-approved or forced; "warnings-only, no sections entry" matches the plan's prescription (the plan never specified a sections entry) — not a defect.
