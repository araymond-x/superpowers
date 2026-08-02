---
schema_version: 1
task_id: 9
task_type: implementation
status: DONE
files_changed:
  - path: "tests/unit/test_spawn_handoff_v2.py"
    description: "Minor 1: test_fallback_refuses_when_no_surface_ref_can_be_resolved gains the `list-pane-surfaces in verbs` discriminator, hoisted ABOVE the `returncode == 3` pin (the `verbs = _verbs(...)` binding moved up with it), plus a docstring paragraph recording what the discriminator separates and why it is asserted first. Minor 2: test_forwarded_knob_values_are_shell_quoted's VACUITY paragraph replaced with the empirically correct account — the `KNOB=` anchor is what defeats the substring trap, and BOTH legs independently kill the mutant. No assertion changed for Minor 2."
tests:
  written: 1
  passing: 1
  command: ".venv/bin/python3 -m pytest -p no:cacheprovider 'tests/unit/test_spawn_handoff_v2.py::TestSurfaceTopology::test_fallback_refuses_when_no_surface_ref_can_be_resolved'"
  result: PASS
contract_compliance:
  - constraint: "Change ONLY what the two Minor findings require; report anything else rather than fixing it"
    status: compliant
    detail: "One file touched. One assertion added, one assertion re-ordered (the same assertion the finding named), two docstrings edited. No production code changed — spawn-handoff-session.sh is byte-identical to f76e047 (verified `diff -q` against a pre-work file copy, and `git status` lists it as unmodified)."
  - constraint: "Write scope: the listed test files, fixtures, and spawn-handoff-session.sh only"
    status: compliant
    detail: "Only tests/unit/test_spawn_handoff_v2.py modified. _handoff_support.py, test_handoff_support.py, plan/module files and BACKLOG.md untouched."
  - constraint: "tests/integration/sdd-e2e-test.sh RED until Task 17 — do not touch, run, or report"
    status: compliant
    detail: "Not touched, not run, not reported."
  - constraint: "Mutation restore by FILE COPY + diff -q; never git checkout --, never git stash"
    status: compliant
    detail: "All four probes backed up with `cp` to the scratchpad and restored with `cp` + `diff -q` (echoing SCRIPT_RESTORED_OK / TEST_RESTORED_OK). No git stash and no git checkout of any working-tree path at any point."
  - constraint: "Assert the mutation anchor matches EXACTLY ONCE before mutating"
    status: compliant
    detail: "Counted every anchor. `[ $rc -eq 0 ] || return 1` appears THREE times (lines 630/639/654) — a bare string mutation would have hit the wrong function and read as SURVIVED, so Probe A was applied by line index with an equality assertion on line 654's content. The I3 `case` gate and the I2 `shq` site each asserted count == 1 in-process."
  - constraint: "Attribute every RED to a single assertion"
    status: compliant
    detail: "Every probe run used an explicit single nodeid with -x and the failure block was read verbatim; the firing assertion is quoted per probe in Testing below."
  - constraint: "Bash floor 3.2 — no set -u / set -e / pipefail"
    status: not_applicable
    detail: "No shell script was modified."
  - constraint: "Grep via /usr/bin/grep (the shell's grep skips .worktrees/)"
    status: compliant
    detail: "All searches used /usr/bin/grep with -F/-E as appropriate."
---

## Implementation Summary

Closed the two Minor findings from `task-009-quality-review-round-2.md`. Both live in
`tests/unit/test_spawn_handoff_v2.py`; neither required a behavior change, and none was
made.

**Minor 1** — `test_fallback_refuses_when_no_surface_ref_can_be_resolved` named the
ref-shape refusal but every leg of its evidence combination (including `rc == 3`) is
equally true of any abort earlier in `create_workspace_target`. Added the one assertion
that becomes FALSE in that world — `"list-pane-surfaces" in verbs` — and placed it
first, so a regression attributes to the discriminator rather than to the bare rc.

**Minor 2** — the I2 test's docstring declared its presence assertion vacuous. That is
false: under the `$(shq "$v")` → `$v` mutation the presence assertion is exactly what
fires. Rewrote the paragraph to state what actually discriminates (the `KNOB=` anchor)
and that both legs are independently load-bearing.

## Changes Made

`test_fallback_refuses_when_no_surface_ref_can_be_resolved`: the `verbs = _verbs(tmp_path)`
binding moved from the middle of the assertion block to immediately after `run_spawn`,
followed by the new discriminator, followed by the pre-existing `assert r.returncode == 3`.
The remaining assertions are unchanged and in their original relative order. The
discriminator's message names the failure mode (aborted earlier in
`create_workspace_target`) and renders `verbs` so a future RED is self-explaining.

`list-pane-surfaces` is a valid probe: the v2 stub records `echo "$@" >> "$CMUX_LOG"`
BEFORE its verb dispatch, so the call appears in `cmux.log` regardless of what the
`CMUX_LIST_SURFACES_NO_REF` branch then prints, and `_verbs` reads first tokens — the
verb is its own first token.

`test_forwarded_knob_values_are_shell_quoted`: docstring only. The old "VACUITY" claim
was replaced by a "SUBSTRING TRAP" paragraph (a bare `in` on the *value* would be
vacuous; anchoring on `KNOB=` is what makes each leg discriminate) plus a MEASURED
paragraph recording which assertion fires under the mutation and that the other leg
would have fired too. Assertions untouched.

## Testing

Full unit suite, `.venv/bin/python3 -m pytest -p no:cacheprovider tests/unit/ -q`,
`__pycache__` cleared before each run:

- **BEFORE** (pristine `f76e047:tests/unit/test_spawn_handoff_v2.py` copied in):
  `777 passed, 1 warning in 228.02s`
- **AFTER** (both fixes): `777 passed, 1 warning in 229.62s`

Both numbers were measured in this round; neither was inherited. Count is unchanged
because no test function was added. The three spawn files alone: `143 passed in 144.67s`,
matching the stated baseline.

### Probe A — Minor 1's own reproduction (the required positive control)

Mutation: `return 1  # MUTATION PROBE A` inserted immediately after line 654's
`[ $rc -eq 0 ] || return 1` in `create_workspace_target`, so the fallback aborts before
`list-pane-surfaces` is invoked. Diff printed and read (`655d654 < return 1 …`).

Result: **RED, attributed to the NEW assertion** — not to `rc == 3`:

```
E  AssertionError: never reached the ref-resolve step — this run aborted earlier in
   create_workspace_target, so the ref-shape gate was never exercised:
   ['new-surface', 'workspace', 'notify']
E  assert 'list-pane-surfaces' in ['new-surface', 'workspace', 'notify']
tests/unit/test_spawn_handoff_v2.py:1119
```

Restored by file copy; `diff -q` clean.

### Probe B — the original I3 mutation must still be caught

Mutation: the ref-shape gate made unconditional —
`case "$SPAWN_SURFACE_REF" in *) : ;; esac`. Anchor asserted to occur exactly once.

Result: **still RED**, so the discriminator did not weaken what the test already killed.
The RED attributes to `assert r.returncode == 3` (`assert 0 == 3`) — correct and
expected: under I3 the run *does* reach `list-pane-surfaces`, so the discriminator
passes and the next assertion is the one that fires. Minor 1 asked only that a
*pre-resolve abort* attribute to the discriminator, which Probe A proves. See Self-Review
for why I did not reorder further.

Restored by file copy; `diff -q` clean.

### Probe C — the second world named in the new docstring

The docstring says the pre-fix test is also green under `CMUX_WS_CREATE_RC=1`. The
reviewer argued this but did not report measuring it, so I measured both halves rather
than ship an unrun "MEASURED":

- **C1** (pre-fix shape: discriminator removed, `CMUX_WS_CREATE_RC="1"` added to
  `_reach_gate`): `1 passed in 1.69s` — confirms every remaining leg is satisfied by a
  create-failure abort.
- **C2** (fixed shape, same knob): **RED on the discriminator**, same message and verb
  list as Probe A. The discriminator generalizes beyond the single probe it was written
  against.

Both restored from a pre-edit copy of my own file; `diff -q` clean.

### Probe D — Minor 2's premise, verified rather than inherited

Mutation: `INLINE_ENV="$INLINE_ENV $knob=$v"` (drop `shq`). Anchor count asserted == 1.

Result: **RED on the PRESENCE assertion**, confirming the reviewer and refuting the old
docstring:

```
E  AssertionError: forwarded knob value is not shell-quoted:
   'export SUPERPOWERS_SPAWN_ID=… SUPERPOWERS_CMUX_TITLE_FORMAT=a b; touch /tmp/PWNED; claude-picker …'
```

The rendered output also contains the bare `SUPERPOWERS_CMUX_TITLE_FORMAT=a b; touch
/tmp/PWNED`, so the absence leg would have fired independently — both legs are
load-bearing, exactly as the new docstring now states.

Restored by file copy; `diff -q` clean. `git status` confirms
`spawn-handoff-session.sh` unmodified.

## Source Files Read

- `docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/task-009-quality-review-round-2.md` — the two Minor findings and the Observations block.
- `tests/unit/test_spawn_handoff_v2.py` — both target tests plus `_verbs` / `_outcome` / `cmux_log_text` helpers.
- `tests/unit/spawn_handoff_helpers.py` — the v2 stub, to confirm `list-pane-surfaces` is logged before its verb dispatch and that `CMUX_LIST_SURFACES_NO_REF` / `CMUX_WS_CREATE_RC` behave as the probes assume.
- `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` — `create_workspace_target`, `launch_into_target`, and the `INLINE_ENV` composition, to locate and count every mutation anchor. Read only; not modified.
- `docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/task-009-implementer-report.md` — report format reference.
- Worktree root `CLAUDE.md`.

## Deviations from Plan

None from the fix instructions. Two departures from what the instructions *assumed*,
both surfaced rather than absorbed:

1. **The instructions' sample assertion used a variable that did not yet exist at that
   point in the test.** `verbs` was bound *after* the `returncode` assertion, so
   satisfying "place it before the bare `returncode` assertion" required hoisting the
   binding. That is the minimal way to honor the instruction; no other statement moved.

2. **The instructions' Probe A anchor is not unique.** `[ $rc -eq 0 ] || return 1`
   occurs three times in `spawn-handoff-session.sh` (630, 639, 654); only 654 is in
   `create_workspace_target`. A naive string mutation would have landed in
   `create_surface_target`, been a no-op for this test, and read as SURVIVED — a
   manufactured false finding of precisely the kind this round exists to avoid. Probe A
   was therefore applied by line index with an equality assertion on the line's content.

3. **Frontmatter `tests.written` reads 1, not 0.** This round added NO new test
   function — it amended one existing test with one assertion and rewrote two
   docstrings. The schema has no representation for "amended" (`tests.passing` may not
   exceed `tests.written`, so `written: 0` is rejected outright), so `written: 1` counts
   the amended test and `command` names that single nodeid. The full-suite figure that
   actually matters is in Testing above: **777 before, 777 after.**

4. **Added an unrequested measurement (Probe C).** The instructions did not ask for the
   `CMUX_WS_CREATE_RC=1` world, but my new docstring names it as MEASURED, so I measured
   it. This adds no code — it is evidence for a claim the docstring makes.

## Self-Review Findings

**Did I change behavior?** No. `spawn-handoff-session.sh` is byte-identical to
`f76e047`, verified by `diff -q` against a copy taken before any probe and by
`git status` listing only the one test file as modified. The instruction's warning
("if you find yourself editing spawn-handoff-session.sh, stop") held — every edit to it
was a probe, applied and reverted within a single tool call pair.

**Is the new assertion itself vacuous?** No — Probe A and Probe C2 both show it going
FALSE, in two different pre-resolve-abort worlds, while Probe B shows it staying TRUE in
the world the test already covered. It discriminates in the direction claimed and only
in that direction.

**What I deliberately did NOT do.** Under Probe B the RED attributes to `rc == 3`
rather than to a semantic assertion. Making I3 attribute semantically would mean hoisting
`assert "send" not in verbs` above the rc pin — a second, unrequested reordering of a
test the reviewer already approved, on a round whose stated risk is defects introduced by
fixes. I left it and record it here as an observation: **the I3 world's first-firing
assertion is still the bare rc.** If a future round wants that attribution too, the
change is one more line move, and it is independent of anything here.

**Residual, out of scope, not chased.** The three reviewer Observations (the delegation
test's inert `tmp_path`, the cosmetic line-wrap in `test_spawn_handoff_hardening.py`, and
the unpinned `END{if(!f)print first}`) were explicitly recorded as non-findings and are
untouched. I4 remains an accepted risk owned by merge.

**Docstring honesty.** Every "MEASURED" in the two edited docstrings corresponds to a
probe run in this session, quoted above. Nothing was carried over from the review report
on the report's authority alone — including the Minor 2 premise, which I re-ran (Probe D)
rather than cite.

## Concerns

None. Status is DONE: the Deviations section records how the fixes were applied (anchor
non-uniqueness, the hoisted binding, the schema's lack of an "amended test" count) and
one measurement added beyond instruction — none of these is an unresolved risk to the
change.
