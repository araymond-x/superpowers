# Task 6 — Code Quality Review

**Reviewer:** general-purpose senior code reviewer (dispatched)
**Task:** K-consecutive-fallback escalation
**Verdict:** **Ready to merge: Yes** (controller hardens Finding #1 via [task 6 fix]).

## Strengths (empirically verified)

- **awk trailing-count logic correct.** Traced: `[allow,fallback,fallback]`→2; `[fallback,allow,fallback]`→1 (breaks at middle allow); empty→0; missing/unreadable→`|| echo 0`→0.
- **Substring match safe** — lines fully controlled by `ctx_log`'s printf; `action` is the last field ∈ {allow,fallback,nudge,block}; no user content.
- **set -u / pipefail safe** — `${STREAK_N:-0}` guard; `CTX_STREAK` validated `^[0-9]+$` (L50) so both `-ge` operands always integers; the test `2>/dev/null` is belt-and-suspenders (no `set -e`, fails open — acceptable defensive path).
- **Log-then-count ordering right** — `ctx_log … fallback` writes the current row before `ctx_fallback_streak` reads, so the current fallback is included (seed 2 + this = 3 = block).
- **Scope tight** — escalation only in the implementer byte-proxy else-arm, its own `exit 2`; probe-success/bypass/marked-fix paths untouched.
- No duplication (reuses CTX_STREAK/ctx_log/OBS_LOG). Baseline re-captured same commit (check-hooks.sh PASS). Block message actionable. Tests genuine + non-flaky (`test_probe_success_resets_streak` truly proves reset; `_seed` correctly simulates prior state; all 6 pass).

## Issues

**Critical:** None. **Important:** None.

**Minor:**
1. **No test exercises a non-default `CTX_STREAK`.** All tests set `SUPERPOWERS_CTX_FALLBACK_STREAK=3` (= default) or rely on it. The "env-override changes the threshold" wiring is unproven for this escalation; a test at `=2` (seed 1 → block) would close it. Acceptance criteria explicitly lists `_FALLBACK_STREAK` override. → **Controller: HARDEN via [task 6 fix].**
2. awk buffers whole file (`a[NR]=$0`) for a streamable count — `awk '/ action=fallback$/{c++;next}{c=0}END{print c}'` is O(1). Tiny log → no practical impact. Cosmetic.
3. `/action=fallback/` unanchored — correct today; ` action=fallback$` would be exact if the format grows. Minor hardening.

## Recommendations
- Semantic note (not a defect): the streak counts trailing fallbacks from ALL dispatch types (marked-fix/other/reviewer also write fallback rows) — the intended, more-robust "gate ran blind for K dispatches" reading, but it means the trip can be primed by non-implementer fallbacks. The helper comment + report already document this.

## Assessment
**Ready to merge? Yes.** awk streak logic correct across all traced cases, escalation tightly scoped and set-u-safe with proper guards, log-then-count ordering right, baseline re-captured + intact. Only gaps are a minor test-coverage hole (non-default threshold) + two cosmetic awk nits.

## Controller Disposition
- **Finding #1:** HARDEN — dispatch `[task 6 fix]` to add a non-default `SUPERPOWERS_CTX_FALLBACK_STREAK` test (e.g. `=2`: seed 1 + bad probe → block; and/or `=5`: seed 3 → allow) proving the override changes the escalation threshold. Test-only → no baseline re-capture. Quality re-review after.
- **Findings #2 + #3:** ACCEPTED, no change — the awk is the plan's verbatim prescribed code (changing it deviates from the plan; correct today given the controlled log format; the log is tiny so streaming is moot). Anchoring noted as a future hardening candidate.

## Fix-Cycle Outcome
`[task 6 fix]` commit `8d3e3e0` (test-only) added `test_nondefault_streak_threshold_blocks_earlier` (`=2`, seed 1 → block) + `test_nondefault_streak_threshold_allows_below` (`=5`, seed 3 → allow). **Quality re-review (`[task 6 re-review:quality]`): PASS** — commit touches only the test file (+27, no hook/baseline); both tests additive and genuinely discriminating (neither passes at the default 3 — proven in both threshold directions); 8/8 pass; `check-hooks.sh` PASS. Finding #1 RESOLVED, no regression.
