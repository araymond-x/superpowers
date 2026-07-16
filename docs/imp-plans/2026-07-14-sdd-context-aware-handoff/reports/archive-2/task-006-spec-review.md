# Task 6 — Spec Compliance Review

**Reviewer:** general-purpose spec compliance auditor (dispatched)
**Task:** K-consecutive-fallback escalation
**Verdict:** **PASS** — full contract compliance; count-all-types design decision independently assessed SOUND.

## Verified against source (9 checks)

1. **Helper `ctx_fallback_streak`** (L199-203): awk counts trailing `action=fallback` rows, breaks at first non-fallback, `2>/dev/null || echo 0`. **No `type=` filter** (regex `/action=fallback/` only).
2. **Escalation placement + scope** (L850-854): strictly inside the implementer-tail byte-proxy `else`-arm (L848) → inside not-BYPASS/not-MARKED_FIX `else` (L834) → inside `if IS_IMPLEMENTER` (L828). Its own `exit 2` (not ERRORS[]). Cannot fire for non-implementer (reviewers exit L280, passthrough L315), MARKED_FIX (L829 branch), or BYPASS (L831). A reviewer/passthrough probe-fail logs a fallback row (counts toward streak) but is never itself blocked.
3. **Message contains "blind"** (L852).
4. **CTX_STREAK reuse** (L851): compares `${STREAK_N:-0}` vs `$CTX_STREAK` (parsed L45/50 from SUPERPOWERS_CTX_FALLBACK_STREAK, default 3). No hardcoded 3, no reparse.
5. **set -u safety**: `${STREAK_N:-0}` guard; awk `2>/dev/null || echo 0`; the `[ ]` test `2>/dev/null` suppresses non-integer arithmetic error.
6. **awk not tac** (comment notes macOS).
7. **6 tests genuine** (re-run, all pass): single→rc0; seed-2+this=3→rc2+"blind"; probe-success-resets (interposed allow row → trailing count 1 → rc0); compaction (below→rc0); retry-after-block (hard×2→rc2,rc2); bypass-after-block (rc2 then bypass rc0).
8. **Full context suite** (fallback/tier/impl_log/log) → 19 passed; `check-hooks.sh` PASS.
9. **No scope leak**: diff touches only the helper (5 lines) + escalation (5 lines) + test + baseline.

## Design decision — SOUND (reviewer's independent assessment)
The probe reads the controller's `transcript_path` — the same session-state input for every dispatch type. Probe success/failure is a property of session state, not dispatch type: a broken probe fails uniformly. A working probe writes a non-fallback row on every dispatch → breaks any streak; a fallback row appears only when broken, for all types. So K trailing fallbacks reliably means "gate ran blind for K dispatches." A `type=implementer` filter would be strictly worse (interposed reviewer dispatches would neither break nor increment, delaying detection). Reviewer concurs with the no-filter design.

No BLOCKING/ADVISORY findings; nothing [UNVERIFIED].
