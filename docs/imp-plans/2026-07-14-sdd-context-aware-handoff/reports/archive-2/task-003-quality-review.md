# Task 3 — Code Quality Review

**Reviewer:** general-purpose senior code reviewer (dispatched)
**Task:** Hoist session_id + helpers + thread into non-implementer exit paths (highest-risk hook surgery)
**Verdict:** **Ready to merge: Yes**

## Strengths (empirically verified)

- **`set -u` hygiene correct throughout.** Every var the helpers reference is initialized in var-init (L84-114) and re-set in the manifest block before helpers are callable (defined L164, first call L231, both after the `MANIFEST_MODE=false` exit L158). `ctx_log` guards `${TASK_NUMBER:-}`. Stress-tested `ctx_probe_tokens`'s declared-but-unassigned `out` when both `tpath` and `SESSION_ID` empty — the `[ "$rc" -eq 0 ] && [[ "$out" =~ ]]` short-circuit means `$out` is never dereferenced while unset. Clean.
- **No SIGPIPE fail-open introduced.** Only new pipes are `echo "$INPUT" | jq -r … 2>/dev/null` (jq consumes all stdin, no `grep -q` early-exit). Helpers otherwise use `[[ =~ ]]`, `wc -c`, arithmetic, `>>`.
- **Best-effort append genuinely cannot abort.** Hook runs `set -uo pipefail` with **no `set -e`** (verified); `ctx_log`'s `{ … } 2>/dev/null || echo WARNING >&2` returns 0 on either branch. `test_append_failure_never_breaks_dispatch` (dir-as-logfile) proves rc=0.
- `ctx_probe_tokens` numeric guard (`[[ "$out" =~ ^[0-9]+$ ]]`) + `ctx_tier` integer guard both present/correct — non-numeric probe stdout falls back to byte-proxy, not garbage.
- Check 7 fully retired, SSOT preserved (`grep CONTEXT_LOAD_WARNING` → 0; constant + injection gone; byte-sum only in `ctx_byte_estimate`).
- SESSION_ID hoist replaces the L109 re-initializer (clobber-proof); local reviewer reassignment deleted, sentinel guarded `${SESSION_ID:-unknown}`.
- 23 tests pass; `bash -n` clean; `check-hooks.sh` PASS (baseline re-captured in-commit).

## Issues

**Critical:** None. **Important:** None.

**Minor (both plan-prescribed, non-blocking):**
1. **`CTX_SOURCE` is a write-only global** (L51/189/191 assign; never dereferenced — call sites pass the source literal to `ctx_log`). Plan-prescribed verbatim; Tasks 5-6 also pass literals, so it stays write-only feature-wide. Removing now would be a plan deviation. Recommend a later cleanup (drop the assignments, or have `ctx_log` read `$CTX_SOURCE` instead of `$2`).
2. **Re-review rows log `task=` empty** (L231 calls `ctx_observe_and_log other` while `TASK_NUMBER=""`; id is in `RR_TASK`). Cosmetic — tuning consumer keys on `source=probe`, not `task=`. Module 3 doc-time note.

## Recommendations
- Reviewer type-label deviation (`partner-review`/`trace-audit` vs `partner`/`other`): correctly logged (Task 3 row); no consumer parses `type=` for tiering. **Agree with deferring enum reconciliation to Module 3.**
- Broadened probe cost (informational): `ctx_observe_and_log` now spawns `context-probe.py` on every reviewer/re-review/passthrough dispatch + a 2nd `jq` parse. By design (observe all); marginal cost acceptable given each dispatch already forks subprocesses.

## Assessment
**Ready to merge? Yes.** Careful, correct surgery on a `set -u`/`pipefail` hook — every documented hook bug class specifically checked, none present; Check 7 cleanly retired with byte-sum SSOT; tests + baseline green. Only findings are two Minor plan-prescribed polish items, neither affecting correctness or the dispatch path.

## Controller Disposition
- **Minor #1 (CTX_SOURCE write-only):** ACCEPTED — plan-prescribed; stays write-only feature-wide. Logged as a candidate cleanup. Not fixed in Module 2 (removing now deviates from the plan; harmless).
- **Minor #2 (re-review task= empty) + reviewer type-label enum:** ACCEPTED — cosmetic, consumer tunes on `source=probe`. Enum reconciliation deferred to Module 3 (Task 8 docs), consistent with the plan-review-report's pre-accepted divergence.
