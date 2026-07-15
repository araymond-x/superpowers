# Deviations Register

> Auto-maintained by controller during subagent-driven-development execution.
> Review all entries before merge.

| Task | Type | Description | Disposition |
|------|------|-------------|-------------|
| 0 | IndependentDecision | Quality review (Minor): no fixture pins "most recent" reverse-scan preference (all fixtures have ≤1 usage block → forward-scan indistinguishable from reverse-scan). Deferred to Task 1: add `two-usage.jsonl` (older T=200000, newer T=350000) + a probe assertion that reverse-scan returns 350000. Task 0's committed work left intact. | Resolved |
| 1 | IndependentDecision | Added `from typing import Optional` (not in the plan's enumerated import list) because the regression gate (validate-all-skills.py Category 8, Python 3.9 compat) FAILs on `int \| None` PEP-604 union return annotations in the scripts dir. `Optional` is stdlib → stdlib-only / bare-python3 contract preserved. Convention-adherence fix, no behavioral change. | Accepted |
| 1 | IndependentDecision | `import os` + `PROJECTS_DIR` unused in Task 1 (plan Step 3 lists them in the probe top-matter). Quality reviewer adjudicated ACCEPT: plan-directed forward-staging consumed by Task 2's session-id resolver (same file, next commit) — not dead code; no CI risk (no unused-import lint). | Accepted |
| 2 | IndependentDecision | Two doc touch-ups beyond the code diff: updated the probe module docstring's resolution-priority note (drop Task-1 stub language) + the `--session-id` argparse help text (stub→glob). Plan Step 3 explicitly required "keep the module docstring's resolution-priority note accurate" → in-scope, not a divergence. (validate-report.py flagged has_deviations/has_concerns as a heuristic false-positive on the "None." + explanation prose.) | Accepted |
| 2 | DeferredWork | Quality review (Minor): no test sets BOTH `--session-id` and `$CLAUDE_CODE_SESSION_ID` to prove session-id wins the `or` precedence. Deferred: the tiebreak is standalone-CLI-only (the hook never relies on the env var per Contract Constraints — passes exactly one resolver flag), each branch is independently proven, reviewer sanctioned deferral. Off the critical hook path. | Accepted |
| 2 | IndependentDecision | Quality review (Minor): `find_transcript` `is_file`/`is_dir` follow symlinks silently. No change — intentional byte-for-byte parity with `claude-ctx-check` (divergence would break the differential parity test). | Accepted |
| 3 | IndependentDecision | The reviewer-path observation log (`ctx_observe_and_log "$REVIEW_TYPE"`) logs `REVIEW_TYPE` verbatim, so a partner dispatch logs `type=partner-review` and a trace-audit logs `type=trace-audit` — neither matches the contract's enumerated `type=<...|partner|other>`. Inserted the plan's Step-7 code verbatim (plan is authoritative text); only `spec-review` is tested. Cosmetic: the log consumer tunes only on `source=probe` rows, the type label is not parsed for tiering. Enum-vs-emitted-label reconciliation left as a doc-time follow-up (Module 3). | Accepted |

## Deferred Work
[Items deferred from plan scope]

## Independent Decisions
[Decisions made by subagents without plan guidance]

## Scope Changes
[Requirements that changed during execution]

| 2026-07-15T20:22:50Z | Module transition: 1 → 2 | FYI | Accepted |
