---
schema_version: 1
task_id: 9
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/subagent-driven-development/scripts/spawn-handoff-session.sh"
    description: "Surface topology: capture_cmux_ref (single ref-capture path, SSOT), create_surface_target, create_workspace_target (one-shot fallback on the canonical `workspace create` verb), launch_into_target (shared rename-tab + send wrapper for BOTH topologies). cmux new-workspace and spawn_claude_workspace() removed from executable text (one explanatory comment retains the name). rename-tab now carries --workspace (deviations.md:17). TITLE_FORMAT/TAB_TITLE config, INLINE_ENV prefix, SPAWN_WAIT_TIMEOUT config with the prescribed provenance comment, rewritten spawn sequence with the double-spawn guard, updated dry-run echo."
  - path: "tests/unit/spawn_handoff_helpers.py"
    description: "cmux_v2_stub(extra='') — env-driven v2 stub with per-subcommand argv recording built in (the bespoke recording stub in test_spawn_handoff.py was deleted rather than duplicated). SPAWN_VERBS + did_not_spawn() as the SINGLE source of the spawn vocabulary (N4)."
  - path: "tests/unit/test_spawn_handoff_v2.py"
    description: "21-test TestSurfaceTopology incl. test_rename_tab_carries_workspace_on_both_topologies (N2). run_spawn shadowed by a wrapper defaulting cmux_body=cmux_v2_stub(). Three Task-0 residuals closed (marker<->[selected] correlation pinned both directions, len(rows) >= 2, Step 2c citation corrected to Step 2b). M3 narrowed pin."
  - path: "tests/unit/test_spawn_handoff.py"
    description: "Step 1d classes (i)-(v): migrations to the v2 stub, three premises rewritten to the load-bearing-ref contract, all three vacuous `new-workspace not in` sites (~636/~1179/~1201) rewritten to the shared helper, test_mktemp_failure_preserves_spawn_failure_rc repointed. CMUX_NEW_WORKSPACE_FLAGS split into two fixture-derived sets with --command asserted absent from both."
  - path: "tests/unit/test_spawn_handoff_hardening.py"
    description: "B1 second clause: _did_not_spawn delegates to the helper; both required positive controls (surface spawn + CMUX_NEW_SURFACE_RC=1 fallback spawn) re-run AFTER Step 3. The two outright-breaking tests switched to the v2 stub with original invariants intact. 10 -> 13 tests."
  - path: "docs/imp-plans/2026-07-30-cmux-spawn-v2/deviations.md"
    description: "Step 5 commands the deviations.md:17 flip. Five deferred rows flipped; seven Task 9 rows added."
tests:
  written: 25
  passing: 25
  command: ".venv/bin/python3 -m pytest tests/unit/ -p no:cacheprovider -q"
  result: PASS
contract_compliance:
  - constraint: "rename-tab field 2 is action=rename, NOT a ref — success-check with case ... in OK*), never ref-parse"
    status: compliant
    detail: "launch_into_target success-checks with `case \"$rt_out\" in OK*)`; no ref parsing of rename-tab output anywhere."
  - constraint: "SPAWN_WAIT_TIMEOUT_DEFAULT provenance comment wording is PRESCRIBED (deviations.md:22)"
    status: compliant
    detail: "Literal taken from cold-start-timing.json default_seconds; comment states 'spec floor; Task 0 measured 8-11s cold start' rather than implying 60 was measured."
  - constraint: "test_handoff_support.py and _handoff_support.py are READ-ONLY for Tasks 9-11"
    status: compliant
    detail: "Both read only. M4's fix routes TO the KNOWN RESIDUAL ESCAPES block as SSOT rather than editing it."
  - constraint: "Do not 'fix' \"$SENT_CMD\\n\" or clean up BUDGET_FLAG"
    status: compliant
    detail: "Literal backslash-n preserved. BUDGET_FLAG consumed by both outcome printfs; SC2034 resolved by consumption, not deletion."
  - constraint: "Bash floor 3.2 — no set -u / set -e / pipefail"
    status: compliant
    detail: "None added. `bash -n` and `shellcheck --severity=warning` clean."
---

## Implementation Summary

`spawn-handoff-session.sh` now spawns the successor as a **surface in the caller's own cmux workspace**, with `cmux workspace create` demoted to a one-shot fallback on the canonical verb. `cmux new-workspace` and `spawn_claude_workspace()` are gone from executable text. Both topologies converge on one `launch_into_target` wrapper (rename-tab → `cmux send`), and `capture_cmux_ref` is the single ref-capture path. The `wait-for` token is the only exit-0 path.

The central behavioral change: **the ref is now load-bearing.** The old core degraded an empty capture to a `(spawned)` placeholder; rename and send both *address* the ref, so a fabricated one creates a target nobody can drive while the run reports success. Empty/garbled ref, or `mktemp` failure, is now a failure — one fallback attempt, then `spawn-failed` with the hop consumed.

**Unit suite 748 → 773, all green.** Commits `b3ca14f` (code) + `61ba1f4` (register).

## Changes Made

- **Step 1** — `cmux_v2_stub(extra="")` in helpers, env-driven (`CMUX_NEW_SURFACE_RC`, `_WS_CREATE_RC`, `_SEND_RC`, `_SEND_FAIL_COUNT`, `_RENAME_RC`, `_NOTIFY_RC`, `_WAITFOR_RC`, `_SCREEN_FILE`, `_PING_FAIL`) with per-subcommand argv recording built in, so the bespoke recording stub in `test_spawn_handoff.py` was deleted rather than duplicated. `list-pane-surfaces` carries the `* ` marker per fixture key `selected_row_marker`. Three Task-0 residuals closed: marker↔`[selected]` **correlation** pinned in both directions on all three captures; `len(rows) == 2` → `>= 2`; the "Step 2c" misattribution corrected to Step 2b (which calls `available: false` legitimate, not an escalation).
- **Step 1b/M3** — narrowed to `invalid SUPERPOWERS_CMUX_MAX_HOPS`.
- **Step 1b/M4** — the false sentence now states the guard's real reach and gives `E="$EXPECTED_HOPS"; CEIL=$((E * 2))` as the counter-example, routing to `KNOWN RESIDUAL ESCAPES` as SSOT.
- **Step 1c/B1** — `SPAWN_VERBS` + `did_not_spawn()` live in helpers only; `_did_not_spawn` delegates. The two outright-breaking tests (`test_absent_and_empty_hop_counter…`, `test_feature_dir_name_containing_dots…`) switched to the v2 stub with their original invariants (must SPAWN and reserve) intact. Hardening file 10 → 13 tests.
- **Step 1d** — (i)/(ii) migrated; `CMUX_NEW_WORKSPACE_FLAGS` split into two sets **derived from the fixture argv** rather than restated, with `--command` asserted absent from both. (iii) three premises rewritten to the new contract. (iv) all three vacuous sites rewritten to the shared helper, with the discriminator recorded at the weakest site (~1201). (v) `test_mktemp_failure_preserves_spawn_failure_rc` **repointed**, not deleted — repointing it to rc-propagation would have duplicated its sibling, so it now pins that mktemp failure aborts *before any verb runs*.
- **Step 2** — 21-test `TestSurfaceTopology`. Beyond the fence, two vacuousness closures: the inline-env test asserts **identity** with the intent record's spawn id (the specified `startswith` passes on an empty value), and `TAB_TITLE`'s rendered value is pinned (`hop1 SDD feat`) since rename failure is warn-and-continue.
- **Step 3** — (a)–(d) landed; dry-run line updated; `bash -n` and `shellcheck --severity=warning` clean.
- **Steps 4/5** — full unit suite 773 passed; six write-scope paths staged plus `deviations.md` as a seventh (Step 5 commands the row-17 flip).

## Source Files Read

`module-3-spawn-script.md` (Task 9 + File Map + Write-Scope + Contract Constraints), `plan.md` (Shared Contract Section), `spawn-handoff-session.sh`, all four spawn test files, `spawn_handoff_helpers.py`, the frozen fixtures `cmux-verb-shapes.json` and `cold-start-timing.json`, and `test_handoff_support.py` (read-only, for M4's routing).

## Deviations from Plan

- **`run_spawn` is SHADOWED** in `test_spawn_handoff_v2.py` by a wrapper defaulting `cmux_body=cmux_v2_stub()`. Reason: ~16 of Task 8's *own* v2 tests break under Step 3 and **no step enumerated them** — a per-site edit is a per-site chance to miss one. Recorded as a ScopeChange.
- 17 no-op `_commit(ctx)` calls removed from the new class (`_commit` uses `check=True` and fails on a clean tree); the two tests that genuinely write fixture state keep theirs.
- `test_reservation_precedes_new_surface` satisfied by **migrating in place**, not duplicating — it appears on both Step 2's fence and Step 2's migration paragraph, and a literal reading yields two tests for one invariant.
- **OP-1 pre-empted:** the `SPAWN_WAIT_TIMEOUT_DEFAULT` import assertion was explicitly deferred to Task 10 Step 2. Task 9 landed it. Declared in the register so Task 10 verifies rather than re-adds it.

## Self-Review Findings

**Two mutations proving the new pins bite.** Dropping `--workspace` from `rename-tab` → **3 tests RED**. Reverting the awk parser to the broken `$1` form → **5 tests RED**, including B1's fallback control. Both restored by file copy + `diff -q`.

**Step 1b/M3 positive control run TWICE** — first pre-Step-3, then re-run against the landed code (the test now drives the v2 stub). Anchor `grep -cF` = 1 both times, restore by file copy + `diff -q`. Both times the *narrowed* assertion was the failing line (v2 file:506) — not vacuous.

**Step 1c both required positive controls re-run AFTER Step 3**: (a) surface spawn, (b) `CMUX_NEW_SURFACE_RC=1` fallback spawn — both return `False`. Control (a) also permanently asserts the *old* predicate is True on that same log, so the fail-open cannot return quietly.

## Concerns

1. **`--workspace TEST-WS` on `new-surface` is inferred, not measured.** Task 0 measured the `workspace:N` shape; the bare-ID form is inferred from `new-surface --workspace` accepting it. Cost if wrong is a cosmetic rename failure on the path where the flag is redundant anyway — but F1's hazard is precisely that rename failures stay green, so it is recorded. Falsifiable in one live call at the post-merge smoke check.
2. **Orphaned targets.** A fallback workspace created but never launched into is unnamed (`workspace=spawn-failed` is grammar-fixed). The more visible half is on an **exit-0** run: a surface created in the user's own workspace whose send failed is left behind. Surfaced for Tasks 10/13.
3. **A live run at this commit always takes `handshake=timeout`.** Nothing signals `sdd-hop-$SPAWN_ID` yet — the signaller is `hooks/session-start`, owned by **Module 4**. Every test passes because the stub's `wait-for` returns 0 by default; the signal side is invisible to the unit suite by construction. Not a gap, but **"Task 9 DONE" must not be read as "the script can succeed live."**
4. **`tests/integration/sdd-e2e-test.sh` is RED** (its `new-workspace` grep) and stays so until **Task 17**, which owns that rewrite. Outside write scope, not touched, not a Task 9 failure.

## Status

DONE_WITH_CONCERNS
