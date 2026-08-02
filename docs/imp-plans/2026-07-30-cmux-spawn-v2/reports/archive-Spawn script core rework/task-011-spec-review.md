# Task 11 Spec Compliance Review — cmux-spawn-v2

**Verdict: PASS** — spec compliant and contract compliant. Two advisory (non-blocking) findings.

## Full suite re-run (independently executed)
```
.venv/bin/python3 -m pytest tests/unit/ -q -p no:cacheprovider
803 passed, 1 warning in 372.19s
```
0 failed. Matches the implementer's final-report claim ("796 → 803, 0 failed") and the controller's prior independent confirmations. The 1 warning is a pre-existing, unrelated `PytestCollectionWarning`.

## Step 1 (7 tests) — all present in `TestPostSpawn`
`test_default_sequence_rename_then_rc`, `test_verify_failure_warns_partial_never_fails_spawn`, `test_knob_disables_all`, `test_knob_subset_and_invalid_token`, `test_title_format_override`, `test_echo_only_screen_does_not_false_positive_either_anchor` (AMENDED), `test_knob_order_rc_before_rename_is_reordered_with_warning` (AMENDED). Count independently confirmed at 7. Read all 7 in full: assertions match their stated intent.

## Step 2 — landed code matches the AMENDED fence near-verbatim
`post_spawn_send_verified` (3-arg, `grep -qiF` fixed-string only, here-string, no `$4`/regex branch survives). Anchors are the exact measured strings from `cmux-verb-shapes.json`. `run_post_spawn`'s `rc,rename → rename,rc` reorder-with-warning matches the fence exactly, including the addendum-#3 citation.

## Contract Constraints — verified against code
No `set -u`/`set -e`/pipefail introduced. Here-string only, no pipe into `grep -q`. `bash -n` clean; validate-warn-revert positive-controlled directly against `/bin/bash` 3.2.57. No new `exit` statement — wiring sits after `handshake=ok` already decided, before the existing unconditional `exit 0`. No spawn verb called. Commit message exact match. Wiring position correct against Task 10's success stanza. Write-scope: only the six declared paths + deviations.md + reports touched; `_handoff_support.py`/`test_handoff_support.py`/`sdd-e2e-test.sh` all empty diffs. `validate-report.py` → COMPLETE, exit 0.

## The 6-test fix — appropriately scoped
Each fixed by adding `SUPERPOWERS_CMUX_POST_SPAWN=""` to that test's own `_reach_gate(...)` call — not a shared-harness change. The vacuous-test claim (`test_unset_knobs_are_not_forwarded_as_empty`) is real and mutation-verified.

## Findings

- **[ADVISORY] [documentation]**: `deviations.md` row 296's post-fix arithmetic ("798 + 7 + 1 = 806") double-counted the 7 new tests already inside the 798 figure. Correct closed form: 798 + 5 = 803, matching the final report and independent re-runs. Isolated to the row's narrative text — controller corrected the row.

- **[ADVISORY] [cross-hop-consistency]**: `spawn-handoff-session.sh:592-598` (pre-existing forwarding loop, unchanged by Task 11) — `[ -n "$v" ]` can't distinguish "explicitly empty" from "unset," so `SUPERPOWERS_CMUX_POST_SPAWN=""` never reaches a spawned successor's environment and silently re-defaults to `rename,rc` on the next hop. Not a fence departure (fence is silent on forwarding), pre-existing code, low severity (cosmetic-only). Logged to deviations.md as an open, non-gating finding.

No BLOCKING or MISSING findings. No undeclared departures from the amended fence beyond the two already-declared deviations.
