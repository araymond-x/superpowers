# Code Quality Review: Task 2 — sdd-pre-dispatch-hook.sh hardening (N3a + N10)

## Assessment: APPROVED-WITH-MINOR

Commit fe52b67 (parent d8cf7e9). 57/57 tests pass (test_sdd_hook_hardening + 4 sibling suites); bash -n clean; glob/null behaviors empirically reproduced.

## Strengths
- **N3a skip-guard fail-safe + correctly placed** (`:505`): after verification + provenance-disabled branches, before the enforcement `else`. Both operands set before this point (PREV :413, MANIFEST_TASK_START :112). Malformed-manifest path verified: non-numeric START → `[ -lt ]` errors to suppressed `2>/dev/null` → test false → falls through to enforcement `else`. A bad manifest can never wrongly SKIP a gate.
- **No wrong-skip of within-module tasks:** task_range guard at :205 exit-2s any TASK < START; `test_check4c_enforced_within_module` confirms PREV>=START still BLOCKs. Skip reachable only when PREV is the prior module's last task (or PREV=0 no-Task-0).
- **N10 glob correct + robust:** archived-only → found (the real bug fixed); live+archived → both found (check_report_file sorts + tail -1, harmless); empty → ls errors suppressed. Single Task-0 glob site (no drift). Word-split of the two-glob string intentional/safe (REPORTS_DIR has no spaces).
- **Tests real + non-vacuous:** `_full_support` isolates the gate-under-test; `test_check5_finds_archived_task0` activates Source Contracts (replaces "**Source Contracts:** None" → "docs/spec.md" → HAS_SOURCE_CONTRACTS=true), genuinely exercising Check 5; would BLOCK pre-fix.

## Issues
- **Minor — skip-guard comment (:509-510) is a forward-reference.** It states PREV's provenance "is re-verified at transition time by transition-module.py:validate_module_completion." As of THIS commit, that function checks only report-file existence, not dispatch-log provenance. **Controller disposition: KEEP the comment as written.** Task 3 (N3b, the very next task) adds exactly the dispatch-log provenance check to `validate_module_completion`, making the comment accurate for the merged feature. The reviewer's suggested reword ("report files, not provenance") would itself be WRONG after Task 3, so adopting it would introduce a new inaccuracy. The comment is a deliberate N3a↔N3b pairing (spec D1=M2). Tracked in deviations.md; Task 3's dispatch is instructed to confirm the comment's claim holds after its change; Task 4's cross-language SSOT test pins the hook↔transition agreement. Additional backstop: the pre-completion trace audit (extract-execution-trace.py detect_anomalies Rule 1) parses the raw session jsonl for actual dispatches, working across module boundaries.
- No Critical/Important. No dead code. No regressions. No other call sites need update.

## Assessment
APPROVED-WITH-MINOR. Both fixes correct, in-scope, fail-safe, well-tested. The single Minor is a forward-referencing comment that Task 3 makes accurate — kept intentionally rather than reworded to a soon-to-be-wrong statement.
