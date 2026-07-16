# Task 8 — Spec Compliance Review

**Reviewer:** general-purpose spec compliance auditor (dispatched, accuracy-focused)
**Task:** Operational + troubleshooting documentation
**Verdict:** **PASS** — every documented value verified accurate against source (`sdd-pre-dispatch-hook.sh` + `context-probe.py`).

## Verified Accurate

1. **Env vars + defaults** — SOFT=300000, HARD=400000, FALLBACK_STREAK=3, `_HANDOFF_BYPASS`. Source L43-45 match exactly; bypass L206/831.
2. **Threshold guard** — non-numeric OR `HARD ≤ SOFT` reverts BOTH to 300000/400000 + warning (source L46-48, `-le`).
3. **Metric formula** — 4-field sum, most recent usage block, window-less absolute (matches probe FIELDS + find_latest_total).
4. **Observation-log format + path** — `reports/context-observations.log` (OBS_LOG L125), separate from `.dispatch-log`; format order matches `ctx_log` printf L195; enum values (source/tier/action) confirmed.
5. **Transcript source (load-bearing nuance)** — all 3 doc sites correctly state the HOOK reads `.transcript_path` → hoisted `.session_id`, NEVER `CLAUDE_CODE_SESSION_ID`, AND correctly note the PROBE accepts the env var as last priority but the hook never reaches it. No misstatement in either direction.
6. **Test files** — all 7 listed + exist on disk; "7" is correct ground truth (plan text's "5" was stale).
7. **BACKLOG N43** — flipped in-flight → done-pending-merge (L114); B10 noted unblocked (not resolved).
8. **Troubleshooting runbook** — 4 items + 3 design notes matching the plan's Step 4 verbatim; per-dispatch-cost + observation-log-scope notes confirmed against source.
9. **Manifest inventory** — all 5 entries present (count 14→15, probe row, hook context-gate row, 2 reference rows, observation-log artifact).
10. **Scope** — only the 4 doc files (no hook/probe/test/e2e).

**Note:** the doc has 4 runbook items + 3 design notes (not "5" — the plan specifies exactly those 4 items; the doc matches the plan verbatim). No BLOCKING/ADVISORY/[UNVERIFIED] findings.
