# Deviations Register

> Auto-maintained by controller during subagent-driven-development execution.
> Review all entries before merge.

| Task | Type | Description | Disposition |
|------|------|-------------|-------------|
| Ingestion | ScopeChange | Spec-internal discrepancy adjudicated at ingestion: the distilled spec's Acceptance Criteria say `off` refuses with `reason=policy`, while its Contract Facts and Decision 14 say `reason=policy-off`. Contract Facts are binding (per plan Contract Constraints), so the implementation ships `reason=policy-off`. Not re-litigated. | Accepted |
| Ingestion | ScopeChange | Pre-execution auditor returned ORDERS_ISSUED (3 Block-A + 8 Block-B). All 11 accepted. Block A (A1 surface-UUID probe, A2 `wait-for` latching probe, A3a `/rc` confirmation capture) landed as Task 0 plan amendments before dispatch — Task 0 is the sprint's only live-cmux window. B5 (`depends_on` encoding), B6 (import-assertion definitions + column-0 requirement) and B8b (blocked-path step target) also resolved pre-dispatch. Remaining 6 orders scheduled to their owning tasks — see Deferred Work below. Plan gate state re-verified after amendments: `validate-plan.py` PASS, zero warnings, zero blockers on all 5 files (a first pass overran the 200-line task limit and was compressed, not accepted). Full record: `reports/pre-execution-audit.md`. | Accepted |
| Ingestion | ScopeChange | Operator addendum relayed in the handoff bundle (CONTINUE.md "OPERATOR ADDENDUM", 2026-07-30) — three amendments folded into EXISTING tasks, no new tasks: (1) add `surface_uuid=` (or `ref (uuid)` pair) to the outcome record so refs stay resolvable across cmux app restarts; (2) make the two post-spawn `outcome` appends CHECKED writes using the reservation-write `if ! printf` pattern (closes BACKLOG N63); (3) post-spawn ordering hazard — `cmux send` injection was observed (N=1, mechanism unproven) to stop landing after `/remote-control` activation, so ALL terminal driving must precede `/rc`, `/rc` is sent LAST, and no post-`/rc` send step may be designed. Amendments are applied at the task that owns each change (13, 13, 11/16 respectively). | Accepted |

## Deferred Work

Pre-execution audit orders scheduled to their owning task. Each MUST clear its gate before that
task dispatches; see `reports/pre-execution-audit.md` for full findings and definitions of done.

| Order | Owning task / gate | What must land |
|-------|--------------------|----------------|
| B1 | Module 3, before Task 8 dispatches | Add `tests/unit/test_spawn_handoff_hardening.py` to Module 3's Write-Scope (Tasks 8, 9) + the parent's Module-3 row. Task 8 pins `SUPERPOWERS_CMUX_MAX_HOPS=3` (its premise "3 is the default" dies when the derived default becomes ≥6). Task 9 rewrites `_did_not_spawn` to assert absence of EVERY spawn verb (`new-surface`, `workspace create`, `new-workspace`) **plus a positive control** — today it is `"new-workspace" not in log`, which after Task 9 returns True even when the script spawned, voiding 7 assertions in a fail-open regression guard. |
| A3b/c + B2 | Task 11 dispatch | Post-spawn verification must anchor on a string the sent line cannot contain (anchor comes from Task 0 Step 4b's capture); drop the loose `remote.control` alternation; add a negative fixture containing only the echoed command. Canonicalize `SUPERPOWERS_CMUX_POST_SPAWN` so `rc` is always LAST (validator currently accepts `rc,rename`, the ordering operator addendum #3 forbids); add an ordering test + a code comment citing the addendum. |
| B3 | Task 13 dispatch — **conditional on A1** | If Task 0's `surface_uuid_source.available` is true: emit `surface_uuid=<value\|->` in all three outcome records; update parent §2 grammar, Module 3 assertions, e2e Step 14. If false: replace with an explicit deviations row declining operator addendum #1, citing A1's evidence. Not to be silently dropped either way. |
| B4 | Module 2, before Task 5 dispatches | Pin ONE reading of `Handoff.expected_hops` and apply it in both places — either `int \| None = None` (partial block legal, with a Task 5 test) or `write_manifest` always emits it (with a Task 5 test asserting a partial block is rejected). Model currently declares it required while Task 8's helper omits it. |
| B7 | Modules 2 and 4 dispatch | One Contract Constraints line each: new `.py` under `skills/subagent-driven-development/scripts/` is scanned by `check_python39_compat` — no PEP-604 unions, no builtin generics in annotations. Note the asymmetry: `X \| None` IS correct in `skills/scripts/models/` (not scanned), so Task 5's `Handoff \| None` is right while the same syntax in `_handoff_support.py` would FAIL. |
| B8a | Task 13 dispatch | Citation fix: `test_intent_write_failure_exits_3` → `test_intent_write_failure_exits_3_without_spawning`. |

## Independent Decisions
[Decisions made by subagents without plan guidance]

## Scope Changes
[Requirements that changed during execution]
