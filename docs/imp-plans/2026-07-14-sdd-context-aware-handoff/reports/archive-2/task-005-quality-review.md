# Task 5 — Code Quality Review

**Reviewer:** general-purpose senior code reviewer (dispatched)
**Task:** Nudge/block tier in the implementer new-task path (semantic core)
**Verdict:** **Ready to merge: Yes** (optionally harden 2 test assertions first — controller elected to harden Finding #1).

## Strengths (empirically verified)

- Faithful minimal execution — ~29-line change matches the plan's Step 3/4 code (incl. the exact block message); 9 delivered tests are exactly the 9 prescribed; baseline re-captured same commit.
- **`set -u` safety clean** — every referenced var initialized-or-guarded: `IS_IMPLEMENTER`(L214)/`MARKED_FIX`(L222)/`CTX_T`,`CTX_SOURCE`(L51)/`CTX_HARD`,`CTX_SOFT`(L43-44)/`CTX_NUDGE`(L114, use site L872 also `${CTX_NUDGE:-}`)/`TASK_NUMBER`(L217)/`INPUT`(L54)/`SUPERPOWERS_CTX_HANDOFF_BYPASS`(`${...:-}` L827). Stage 2 always sets TASK_NUMBER on the non-fix implementer path.
- **`exit 2` correctly nested** — `IS_IMPLEMENTER=true` → not-fix → not-bypass → probe-success → hard. Reviewers exit 0 at Stage 1; marked-fix takes the first branch; neither reaches it. **Byte-proxy fallback (L844) only logs — a probe failure never hard-blocks** (correct fail-open for a safety gate).
- Single probe, no collision — `TPATH` (L830) fresh global; `ctx_observe_and_log` uses `local tpath` and is NOT called on the new-task implementer path → probes exactly once.
- Good reuse — composes `ctx_probe_tokens`/`ctx_tier`/`ctx_log`; no duplication. Nudge appended after TOKEN_WARNING; whole CONTEXT `json.dumps`-encoded (test_soft_nudges parses additionalContext JSON successfully).

## Issues

**Critical:** None. **Important:** None.

**Minor:**
1. **`test_verification_task_is_eligible_for_block` (test_context_gate_tier.py) asserts only `returncode == 2`** — weakest possible assertion; would false-pass if the plan-rewrite ever caused an earlier gate to exit 2 for an unrelated reason. Reviewer reproduced the scenario and confirmed the exit-2 IS the context block today (`BLOCKED (context): ... ~450000 tokens`), but the test doesn't pin it. Fix: add `assert "context" in r.stderr.lower()`. Same weakness in `test_env_override_lowers_threshold` (lower risk). → **Controller: HARDENING via [task 5 fix].**
2. **No direct single-fallback fail-open assertion** on the implementer path (probe failure → rc 0, never block). Structurally evident (L843-844 only logs). Reviewer: acceptable to defer to Task 6. → **Controller: DEFERRED — Task 6's `test_single_fallback_allows` asserts exactly rc 0 + source=byte-proxy.**

## Recommendations
- Forward reference verified legitimate: both messages point to `references/context-handoff-protocol.md` (Task 7 deliverable, confirmed plan.md:142 + module-3). Ensure Module 3 lands before shipping so the pointer doesn't dangle.
- `CTX_STREAK` (parsed L45/L50, unused here) is NOT dead code — consumed by Task 6. `CTX_SOURCE` write-only is a pre-existing Task-3 artifact (outside this diff; already logged Task 3 deviations).

## Assessment
**Ready to merge? Yes.** Tier logic correct, safe under `set -uo pipefail`, faithful to the plan, 9/9 tests pass, baseline re-captured. Only findings are test-assertion hardening nits + a forward-reference doc a later module supplies.

## Controller Disposition
- **Finding #1:** HARDEN — dispatch `[task 5 fix]` to add `assert "context" in r.stderr.lower()` to both `test_verification_task_is_eligible_for_block` and `test_env_override_lowers_threshold` (pins the exit-2 cause on the semantic-core eligibility contract). Test-only change → no baseline re-capture. Followed by a quality re-review.
- **Finding #2:** DEFERRED/ACCEPTED — covered by Task 6's `test_single_fallback_allows`.

## Fix-Cycle Outcome
`[task 5 fix]` commit `df56255` (test-only) added `assert "context" in r.stderr.lower()` to both `test_verification_task_is_eligible_for_block` and `test_env_override_lowers_threshold`, preserving the existing `returncode == 2` checks. **Quality re-review (`[task 5 re-review:quality]`): PASS** — diff is +4/-1 on the test file only, both existing checks preserved, assertions genuinely pin the `BLOCKED (context)` stderr (not vacuous), 9/9 tests pass, hook untouched, `check-hooks.sh` PASS (baseline correctly unchanged). Finding #1 RESOLVED, no regression.
