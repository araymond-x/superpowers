# Task 8 — Spec Compliance Review (STANDARD)

**Verdict:** ✅ PASS
**Reviewer:** general-purpose spec compliance auditor (lean dispatch)
**Diff:** ddf567e..422f007 (hook +3/-1, test +27)

## Items — all verified
1. ✓ Check 4b VALIDATE_EXIT!=0 branch (hook 376-378) adds `VALIDATE_EXCERPT=$(echo "$VALIDATE_OUTPUT" | head -n 12)` and embeds `\n${VALIDATE_EXCERPT}\n\n` in the BLOCKED message.
2. ✓ head -n 12 correct, empirically re-verified: banner is 4 lines + blank; task_id at output line 6, status at line 10. `head -n 5 | grep -c task_id` = 0; `head -n 12 | grep -c task_id` = 1. Do NOT revert to 5.
3. ✓ INCOMPLETE (missing-sections) branch (380-384) byte-for-byte unchanged.
4. ✓ TestValidationErrorSurfacing writes a real broken task-000 report (task_id: not_an_int) past the 50-byte gate, checkpoint + "Implement task 1" dispatch, asserts returncode==2 AND "task_id" in stderr. Asserts task_id specifically (not "status", which would spuriously match the trailing JSON line). task_id reachable only at line 6 → test FAILS under head -n 5, PASSES under head -n 12 = genuine regression guard.

## Verification
- VALIDATE_OUTPUT captured with 2>&1 (combined output); ERRORS emitted via `echo -e` (line 616) → real newlines.
- test_sdd_classification.py → 6 passed (5 + new); full suite → 351 passed, 0 failures.

## Conclusion
The excerpt genuinely surfaces the failing field inline (e.g. "[1] Field: task_id ... Got: 'not_an_int'"), replacing the opaque exit-code-only message; the test ties the behavior to head -n 12.
