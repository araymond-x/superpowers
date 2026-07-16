---
schema_version: 1
task_id: 6
task_type: implementation
status: DONE
files_changed:
  - path: "skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh"
    description: "Added the ctx_fallback_streak() helper (after ctx_log, before ctx_observe_and_log) that counts trailing action=fallback rows in OBS_LOG via awk (macOS has no tac). Added the K-consecutive escalation inside the implementer-tail fallback else-arm: after the byte-proxy fallback ctx_log, compute STREAK_N and exit 2 with a 'run blind' diagnostic when STREAK_N >= CTX_STREAK."
  - path: "tests/unit/test_context_gate_fallback.py"
    description: "New — 6 tests: single fallback allows (advisory), K consecutive fallbacks block with 'blind' in stderr, probe-success row resets the streak, reading-across-compaction resets tier (no fire), retry-after-block still blocks, bypass-after-block allows."
  - path: "tests/ARaymond-hook-baseline/baseline.txt"
    description: "Re-captured the hook sha256 integrity baseline in the same commit as the hook edit (baselined-hook edit requirement)."
tests:
  written: 6
  passing: 6
  command: ".venv/bin/python3 -m pytest tests/unit/test_context_gate_fallback.py -v"
  result: PASS
contract_compliance:
  - constraint: "Byte-proxy fallback is ADVISORY (a single fallback never hard-blocks); K consecutive escalate"
    status: compliant
    detail: "test_single_fallback_allows proves returncode 0 on the first trailing fallback; the exit 2 fires only when STREAK_N >= CTX_STREAK (test_k_consecutive_fallbacks_block, 2 seeded + this = 3)."
  - constraint: "Reuse CTX_STREAK (from SUPERPOWERS_CTX_FALLBACK_STREAK, default 3) — do NOT hardcode 3 or redefine"
    status: compliant
    detail: "The escalation compares against $CTX_STREAK, the global parsed in Task 3. Tests override via the SUPERPOWERS_CTX_FALLBACK_STREAK env var."
  - constraint: "Escalation is ONLY in the implementer fallback else-arm; exit 2 lives only in the implementer path"
    status: compliant
    detail: "The exit 2 sits inside the else-arm nested within `if [ \"$IS_IMPLEMENTER\" = true ]`. Reviewers/partner/fix exit before the gate (Stage 1/Stage 0), so a reviewer whose probe fails logs a fallback row (counting toward the streak) but is never itself blocked."
  - constraint: "Escalation message MUST contain 'blind'"
    status: compliant
    detail: "Message reads 'the context gate has run blind for $STREAK_N consecutive dispatches'; test greps 'blind' in stderr.lower()."
  - constraint: "ctx_fallback_streak counts ALL trailing fallback rows (no type= filter)"
    status: compliant
    detail: "The awk matches /action=fallback/ with no type= condition. Intentional — see Self-Review Findings for the full rationale."
  - constraint: "awk not tac (macOS has no tac); ${STREAK_N:-0} + 2>/dev/null keep it set -u-safe and non-fatal on missing log"
    status: compliant
    detail: "Streak computed with a reverse-scan awk one-liner; `|| echo 0` and `2>/dev/null` handle a missing OBS_LOG; the ${STREAK_N:-0} guard and trailing `2>/dev/null` on the numeric test avoid set -u/non-numeric fatals."
  - constraint: "A probe success resets the streak"
    status: compliant
    detail: "test_probe_success_resets_streak seeds 5 fallbacks then one source=probe action=allow row; the current bad-probe dispatch is only the 1st trailing fallback, so returncode 0."
---

## Implementation Summary

Task 6 adds the Module 2 safety net: when `context-probe.py` has silently failed
for K consecutive dispatches — the two-tier gate has "run blind" on the byte-proxy
fallback — the hook escalates from advisory logging to a hard block, so a broken
probe cannot leave the context gate permanently inert.

Two edits to `sdd-pre-dispatch-hook.sh`:

1. **`ctx_fallback_streak()` helper** — inserted immediately after `ctx_log()`
   closes and before `ctx_observe_and_log()`. It reverse-scans `$OBS_LOG` with a
   single awk one-liner (macOS has no `tac`), counting trailing rows matching
   `/action=fallback/` and stopping at the first non-fallback row. `|| echo 0`
   and `2>/dev/null` make it non-fatal when the log is absent.

2. **K-consecutive escalation** — inside the implementer-tail fallback `else`
   arm (Task 5's two-tier gate), right after the existing
   `ctx_log implementer byte-proxy ... fallback` row is appended. It reads the
   streak (which now includes the row just written), and if
   `STREAK_N >= CTX_STREAK` it emits a "run blind" diagnostic on stderr and
   `exit 2`. The `${STREAK_N:-0}` default and trailing `2>/dev/null` on the
   `-ge` test keep it safe under `set -u` and against any non-numeric value.

RED→GREEN followed strictly: wrote the 6 tests first, confirmed only
`test_k_consecutive_fallbacks_block` failed (returned 0, no escalation yet) with
the other 5 passing against Task 5's existing behavior, then added the helper +
escalation to turn it green. Re-captured the hook baseline and committed the
hook, the new test, and `baseline.txt` together.

## Source Files Read

- `docs/imp-plans/2026-07-14-sdd-context-aware-handoff/module-2-hook-gate.md` (Task 6, Steps 1–6)
- `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` (helpers block + implementer-tail region)
- `tests/unit/test_context_gate_tier.py` (Task 5 tier tests — run_hook/fixtures conventions)
- `tests/unit/test_context_gate_impl_log.py` (Task 4 impl-log tests)
- `tests/unit/sdd_test_helpers.py` (make_hook_input, setup_full_sdd_workspace, _write_manifest)
- `docs/imp-plans/2026-07-14-sdd-context-aware-handoff/reports/task-005-implementer-report.md` (report format reference)

## Deviations from Plan

None. The `ctx_fallback_streak` helper, the escalation block, and the 6 tests
were implemented verbatim per the Task 6 anchors and Step 1 test source. (A
project linter reformatted the new test file's whitespace/line-wrapping during
commit staging — behavior identical, all 6 tests pass; the committed and
working-tree copies match with no residual diff.)

## Self-Review Findings

- **Streak counts ALL trailing fallbacks, no `type=` filter (the KEY DESIGN
  DECISION):** The awk matches `/action=fallback/` regardless of whether the row
  is `type=reviewer`, `type=passthrough`, or `type=implementer`. This is
  intentional and correct. In normal operation the PreToolUse payload carries
  `.transcript_path` for EVERY dispatch, so a working probe writes a non-fallback
  row (`action=allow`/`nudge`/`block`) that BREAKS the streak. A `fallback` row
  only appears when the probe is genuinely broken — a failure mode that is
  identical across all dispatch types (missing/unresolvable transcript, non-
  stdlib probe crash). So a trailing run of K fallbacks of ANY type IS exactly
  the "the gate has run blind for K dispatches" signal the escalation exists to
  catch, and a single successful implementer probe resets the counter. Adding a
  `type=implementer` filter would UNDERCOUNT the blind window and let a broken
  gate stay inert longer. Verified by `test_probe_success_resets_streak` (a
  `source=probe action=allow` row breaks a 5-deep fallback run).
- Escalation is confined to the implementer path: the `exit 2` is nested inside
  the fallback `else` arm, itself inside `if [ "$IS_IMPLEMENTER" = true ]`.
  Reviewers, partner reviews, marked fixes, re-reviews, and ad-hoc passthroughs
  all `exit 0` earlier via `ctx_observe_and_log`, so they contribute fallback
  rows to the streak but are never themselves blocked.
- Message contains the required "blind" substring; `awk` (not `tac`);
  `${STREAK_N:-0}` + `2>/dev/null` keep it `set -u`-safe; `$CTX_STREAK` reused
  (not hardcoded).
- `check-hooks.sh` reports PASS (7 hooks intact) AFTER the baseline re-capture,
  and the re-capture was committed with the hook edit.

## Concerns

None. Full context suite (`test_context_gate_fallback.py`,
`test_context_gate_tier.py`, `test_context_gate_impl_log.py`,
`test_context_gate_log.py` — 19 tests) and the sanity regression
(`test_sdd_classification.py`, `test_sdd_hook_hardening.py`,
`test_sdd_hard_gates.py` — 49 tests) are all green; `check-hooks.sh` is green
after re-capture; the commit succeeded.

## Fix Cycle

Code-quality review noted that no test exercised a NON-DEFAULT
`SUPERPOWERS_CTX_FALLBACK_STREAK` (every test used `=3`, the default), leaving
the env-override wiring for the escalation threshold unproven. Added two tests to
`tests/unit/test_context_gate_fallback.py`:

- `test_nondefault_streak_threshold_blocks_earlier` — `=2` with 1 seeded
  fallback (streak 2, which under the default 3 would ALLOW) blocks, proving the
  override lowers the threshold.
- `test_nondefault_streak_threshold_allows_below` — `=5` with 3 seeded fallbacks
  (streak 4, which under the default 3 would BLOCK) still allows, proving a
  raised threshold defers the block.

Both tests are discriminating: their asserted outcomes only occur because the
env override changed the threshold away from the default. Only the test file
changed — the hook is untouched (baseline unchanged, `check-hooks.sh` still
PASS, no re-capture). All 8 tests in the file pass.
