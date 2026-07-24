# Deviations Register

> Auto-maintained by controller during subagent-driven-development execution.
> Review all entries before merge.

| Task | Type | Description | Disposition |
|------|------|-------------|-------------|
| Task 2 | ScopeChange | Plan's verbatim `test_hop_limit_exits_3` wrote `.handoff-hops` uncommitted, which trips Task 1's clean-tree Precondition-1 (exit 1) BEFORE the hop-limit check (exit 3) — the test would fail as written. Implementer added `git add -A` + commit after the write (mirrors `test_missing_active_feature_exits_1`), faithful to spec.md L164's "`.handoff-hops` is tracked" invariant. Assertion (exit 3 + "hop") unchanged. Advisor-confirmed. | Accepted (plan test imprecision corrected faithfully; spec reviewer to re-verify the assertion still exercises the hop gate, not the clean-tree gate). |
| Task 0 | IndependentDecision | An environment file-watcher/Python formatter cosmetically reformatted `spawn_handoff_helpers.py` + `test_spawn_handoff.py` post-write (line-wrapping only: PACE_MISSING_WINDOW, run_spawn signature). No identifiers/logic/string-literals/behavior changed; JSON fixtures byte-identical; contract test 1/1 PASS + full unit suite 554 PASS. Controller re-verified committed content (56210f1) — faithful. | Accepted (cosmetic; verified non-breaking). Watch for the same reformatter on Tasks 1–6 which append to these files — benign as long as tests stay green. |

## Deferred Work
[Items deferred from plan scope]

## Independent Decisions
[Decisions made by subagents without plan guidance]

## Scope Changes
[Requirements that changed during execution]
