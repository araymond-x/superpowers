# Task 17 Quality Re-Review (Round 2) — APPROVED

Both prior findings resolved, the anchored assertion is a proven discriminator, fidelity preserved, suite green, no regression. Both code files pristine; both mutations restored exactly (file-copy + `diff -q`, never git).

## Finding #1 (Important) — misleading fallback-coverage comment — RESOLVED
Rewritten comment above `list-pane-surfaces)` (`tests/integration/sdd-e2e-test.sh:707–719`) now accurate:
- States both verbs are the workspace-FALLBACK topology not the surface-topology success path this e2e's three Step-14 sub-runs take (new-surface always succeeds, so the script never falls back here).
- States the marker is kept for test-double fidelity, NOT because Step 14 asserts against it.
- Routes fallback coverage to the unit suite; verified the cited knobs are real: `CMUX_LIST_SURFACES_NO_REF`/`CMUX_LIST_SURFACES_TWO_ROWS` in `spawn_handoff_helpers.py:137,146,212,213`, driven via `test_spawn_handoff_v2.py:1150,1184` (paired with `CMUX_NEW_SURFACE_RC="1"`).
- Fidelity preserved: diff touches only comment lines; stub OUTPUT unchanged — `printf '* surface:7  SDD resume: demo  [selected]\n'` (720) and `workspace) … echo "OK workspace:9"` (705) byte-identical to `fd672ed`.

## Finding #2 (Minor) — unanchored `--focus false` assertion — RESOLVED and PROVEN
New assertion (`sdd-e2e-test.sh:781`): `grep -q "^new-surface .*--workspace TEST-WS .*--type terminal .*--focus false"`.
(a) Anchored to `^new-surface` — a foreign-verb `--focus false` can no longer satisfy it.
(b) Order matches the script's real emission: `spawn-handoff-session.sh:646–648` `create_surface_target()` emits `new-surface --workspace … --type terminal --working-directory … --focus false`; the stub logs full argv per line, so `.*` between `--type terminal` and `--focus false` correctly spans `--working-directory`.

Mutation evidence (both run, both restored by file-copy + `diff -q`):
- Mutation A — reorder `--focus false` before `--type terminal` in the script → RED at this assertion (`FAIL: new-surface line missing … in expected order`).
- Mutation B — emit `--focus false` from `rename-tab` instead of `new-surface` → RED at the same assertion. The old unanchored `grep -q -- "--focus false"` would have matched the rename-tab line and false-passed; the anchored form rejects it. Proven discriminator.

## Regression & Scope
- Full suite green: `E2E PIPELINE PASS - 15 steps composed correctly` (baseline and after restore).
- Fix commit `800000e` touches only `tests/integration/sdd-e2e-test.sh` (19+/7−). Both reviewed code files pristine vs `800000e`. Working-tree dirt is only SDD flight-recorder bookkeeping (`.dispatch-log`, `context-observations.log`, untracked `task-017-*` reports).
- No new dead code or vacuous assertion; the tightening added discrimination.

**Verdict: APPROVED.**

_(Quality reviewer: opus, round 2 re-review. Saved verbatim by controller.)_
