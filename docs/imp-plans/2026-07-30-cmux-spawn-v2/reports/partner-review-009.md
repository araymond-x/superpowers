# Partner Review — Task 9 (three rounds)

**Final verdict: APPROVED (round 3). Task 9 is dispatchable.**

Rounds 1 and 2 both BLOCKED. This file records the sequence; the per-round
detail and its generalized lessons are in `deviations.md` (three Task-9 rows).

## Round 1 — BLOCKED

Controller's own pre-dispatch audit found THREE producer-less obligations
(B1's second clause, the `test_spawn_handoff.py` migration, Steps 4/5).
The partner found FIVE more plus a routing gap:

- **F1** `rename-tab` needs `--workspace` (`deviations.md:17`, measured by Task 0);
  Task 9 writes the only call site. Row 39 narrows the impact, does not retire it.
- **F2** two `test_spawn_handoff_hardening.py` tests break under Step 3 (default
  stub emits no `OK surface:`); each is a precision fence on a fail-closed guard.
- **F3** three `"new-workspace" not in …` assertions go silently VACUOUS — the
  identical B1 fail-open in a file B1's row never named. Worse than a break:
  a break goes RED and gets fixed; these stay green forever.
- **F4** `test_mktemp_failure_preserves_spawn_failure_rc` survives vacuously —
  the test the plan itself waved through as "survives naturally".
- **F5** `SPAWN_WAIT_TIMEOUT_DEFAULT`'s provenance wording is prescribed
  (`deviations.md:22`): the floor dominated, so 60 was NOT measured.
- Step 1c needed TWO positive controls, not one; routing gap on `deviations.md:18`.

## Round 2 — BLOCKED

Found four defects in round 1's fixes, **two introduced by the controller
while fixing that very class**:

- **N1** the F1 fix edited the implementation fence but not the test spec
  pinning its argv — plan self-contradiction, failing in the bad direction.
- **N2** F1's test obligation had NO PRODUCER — the same producer-less shape
  that had just generated Steps 1c/1d in this task.
- **N3** the controller wrote a FALSE severity claim; the ranking was inverted.
- **N4** the spawn-verb list would ship twice in two files with nothing binding
  them, in a task whose entire subject is a verb change.
- N5–N7 minors. A self-inflicted duplicated clause was caught in the same pass.

## Round 3 — APPROVED

Scoped to the round-2 delta. All of N1–N7 verified landed, correct, and
non-breaking, each against source rather than against the commit message:

- **N7 checked hardest** (it changed a stub's stdout shape): the new string is
  byte-identical to the frozen fixture's `rename_tab.stdout`; `case "$rt_out"
  in OK*)` still matches; nothing anywhere depends on the old `target=surface:7`
  (positive control: `action=rename` returns 15 hits).
- **N4's substring verified non-fail-open**: the stub's single-space argv join
  makes `workspace create` adjacent, positive-controlled against three existing
  `"new-workspace" in logged` assertions that pass today by the same mechanism.
- **N3's replacement claim verified TRUE** against source (two direct anti-spawn
  legs at ~636; the hop IS consumed at ~1201, per that file's own comment).
- **N2 is well-specified**: `test_spawn_handoff_v2.py` already has a `_verb_shapes()`
  consumption precedent thirty lines above where the new test lands — a better
  precedent than the hand-restated `CMUX_NEW_WORKSPACE_FLAGS`.

New-defect sweep clean. Two non-blocking observations handed forward (Task 10's
Step 4 "both unit files"; module-4's truncated `rename-tab` shape) — both
recorded in `deviations.md` with owners.
