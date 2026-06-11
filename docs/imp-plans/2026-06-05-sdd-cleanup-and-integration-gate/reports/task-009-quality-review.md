# Task 9 Code Quality Review (C2 + Step 0)

> Dispatched 2026-06-10 (provenance: `.dispatch-log` task=9 type=quality-review).
> Reviewed: commits 2db2171 + 14e5906 against module-2-integration-gate.md Task 9 (base 0f26fb4).

### Strengths
- **0a correct and verified live under all four access paths**: bare-python3 import pulls zero pydantic; IMPORT_FROM triggers __getattr__ (3.7+); lazy resolution yields the model's 4 statuses; unknown attrs raise proper AttributeError. `/usr/bin/python3 -S` (no site-packages) runs validate-plan.py end-to-end → the stdlib-only property is genuinely restored; controller-checkpoint.py benefits identically.
- **Converts the gate's fail-open to fail-closed**: old eager import crashed at import under pydantic-less python3 and the hook's `|| echo ""` swallowed it; now validate-plan.py runs and pydantic-subprocess failures become structured blockers.
- **No dead/sloppy exports**: old `Status` module attr had zero consumers; VALID_STATUSES semantics byte-identical.
- **Self-hosting safe**: WARNING/exit 2 cannot block the gate (blocks only on STATUS="FAIL").
- **0b/0c clean**; **C2 wiring reuses parsed frontmatter**; `is not None` early-return uniformly handles None-frontmatter / missing key / explicit null.

### Issues

#### Critical (Must Fix)
None.

#### Important (Should Fix)
1. **[PRE-EXISTING, exposed]** extract-execution-trace.py:39-40 reads `_mod.STATUS_VALUE_PATTERN` BEFORE `VALID_STATUSES` — STATUS_VALUE_PATTERN hasn't existed in _report_utils since 43badb5, so the AttributeError aborts the try block and the hardcoded fallback set is ALWAYS used: the lazy export Task 9 carefully preserved has zero live consumers. No runtime impact today (fallback matches the model). Ledger: fix the dead reference or delete the export per the dead-code rule.

#### Minor (Nice to Have)
2. **sections parity**: neighbors write a named sections entry; C2 appends warnings only. No consumer breaks today (gate reads status/blockers; e2e reads status; tests query sections for other checks). Three lines for consistency.
3. **Regex calibration (plan-prescribed list)**: probed — `routes/` requires a following word char (misses end-of-token); singular-only forms miss "migrations"/"caches"/"routers"; `\bauth\b` misses "authentication"/"authorization". Stem-style pattern would close most. WARNING-only → follow-up, not defect.
4. **_load_script duplicated** (verbatim, acknowledged) — hoist to a shared home next touch.
5. **Coverage gaps**: frontmatter=None-with-risk-content branch untested; explicit `integration_test: null` untested. Raw-content scan (fences + frontmatter included) defensible for an advisory but worth a comment.
6. **[PRE-EXISTING]** Python 3.9 PATH-python3 would FAIL every frontmattered plan via sdd_session.py:33 `int | None` in the pydantic subprocess. Not live-blocking here (PATH python3 = 3.14.5). Ledger note.

### Recommendations
- Land as-is; fold the 3-line sections entry + two cheap tests into Task 10.
- BACKLOG rows: dead STATUS_VALUE_PATTERN reference; regex stemming; 3.9 `int | None` portability.
- Task 10: key Check 10 off the model/frontmatter, not content re-grep.

### Assessment
**Ready to merge?** Yes
**Reasoning:** Both commits do what they claim — verified empirically; the lazy import is correct under all access patterns and the WARNING provably cannot block the live gate. Tests: **10 passed** (C2 file); **446 passed, 1 warning** full suite. All findings minor, advisory, or pre-existing.
