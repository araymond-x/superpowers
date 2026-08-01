---
schema_version: 1
task_id: 0
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "tests/unit/fixtures/spawn-handoff/cmux-verb-shapes.json"
    description: "Live re-capture (same binary): added list_pane_surfaces_multi + selected_row_marker; added capture_note_addendum provenance seam and close_surface.wrong_ref_note; rewrote ref_resolution_scoping.impact to the measured consequence"
  - path: "tests/unit/fixtures/spawn-handoff/cold-start-timing.json"
    description: "Corrected the `derivation` prose to record that the 60s spec floor dominated (2 x p95 = 22s), so 60 is not describable as a measured cold start. Numeric values unchanged."
  - path: "tests/unit/test_spawn_handoff_v2.py"
    description: "Hardened from 3 to 6 tests: error-class pinning, provenance pinning, escalation-trigger value assertions, unconditional cold-start derivation equality, marker-shape and non-invertibility assertions"
tests:
  written: 6
  passing: 6
  command: ".venv/bin/python3 -m pytest tests/unit/test_spawn_handoff_v2.py -v"
  result: PASS
contract_compliance:
  - constraint: "Write scope is exactly three files; no plan/module/deviations edits"
    status: compliant
    detail: "All three modified. cold-start-timing.json's NUMERIC values were left byte-unchanged (they already satisfy the newly encoded rule); only its derivation prose was corrected. No other file touched."
  - constraint: "Live re-capture only if the Step 1 environment check passes"
    status: compliant
    detail: "cmux --version byte-identical to the fixture stamp, ping PONG, CMUX_WORKSPACE_ID set. Re-verified before capture; blocked path not taken."
  - constraint: "Name every cmux artifact task0-*, clean up on exit, verify zero residual"
    status: compliant
    detail: "Single workspace task0-fix-multirow, closed with `cmux workspace close <ref>`; `cmux workspace list` re-asserts the pre-fix baseline of zero task0-* entries."
  - constraint: "Every assertion adversarially mutation-tested before being trusted"
    status: compliant
    detail: "27 fixture mutations + 1 unmutated positive control; all 27 caught, control green. Restored with `git checkout --` only, tree verified clean between every run."
  - constraint: "No git stash; stage explicit paths; handoff_spawn absent from all frontmatter"
    status: compliant
    detail: "Restores used `git checkout -- <paths>`. Commit staged two explicit paths. No frontmatter authored anywhere; handoff_spawn still absent repo-wide."
---

## Implementation Summary

Remediated the Task 0 adversarial quality review (CHANGES_REQUESTED, 17 surviving mutations). All
seven actionable findings are closed. The suite went from 3 tests to 6, and from **17 mutations
surviving** to **0 of 27 surviving**. Committed as `e9aec59`.

Live re-capture was performed and licensed: `cmux --version` returned
`cmux 0.64.20 (100) [14e3400b9]`, byte-identical to the fixture stamp; `cmux ping` returned `PONG`;
`CMUX_WORKSPACE_ID` was set. One workspace `task0-fix-multirow` was created with `--focus false`,
listed before and after `new-surface`, then closed with `cmux workspace close <ref>` (teardown verb
discovered from `cmux workspace --help` on the installed binary, per the repo's installed-binary-
outranks-docs rule). `cmux workspace list` afterwards shows the sidebar identical to before, with
zero `task0-*` residual.

Findings closed, keyed to the review's numbering:

- **1 [BLOCKING] dead disjunct** — the assertion now pins the error *class* on `stderr` **and**
  `exit != 0`. The permanently-False `in stdout` disjunct is gone, with a comment explaining why it
  cannot come back (stdout/stderr are captured separately by design).
- **2 [BLOCKING] unplanned discoveries invertible** — new `test_unplanned_discoveries_pinned`
  asserts `rename-tab`/`close-surface` are in `requires_workspace_flag` *and absent from*
  `resolves_cross_workspace_bare` (a one-sided assertion would survive a copy rather than a move),
  asserts the three cross-workspace-bare verbs, and asserts the trust anchors are non-empty **and
  actually occur in the captured screen**.
- **3 [BLOCKING] escalation triggers unasserted** — `latching is True` and
  `surface_uuid_source.available is True`, each with non-empty evidence/transcript, each with a
  message citing Module 1 Step 2c. Blanking evidence alone (without flipping the boolean) is also
  caught, which is what distinguishes an unrun probe from a run one.
- **4 [IMPORTANT] degenerate single-row capture** — Part A, below.
- **5 [IMPORTANT] wrong mechanism in `impact`** — rewritten to the measured consequence (a missing
  tab title), plus an `impact_correction_note` naming the real cause of the dead fallback so an
  implementer who adds `--workspace` cannot conclude the fallback is fixed.
- **6 [IMPORTANT] provenance unpinned** — `captured == "live"` and `cmux_version.startswith("cmux ")`.
- **7 [IMPORTANT] one-directional cold-start test** — the derivation rule is now encoded as an
  **unconditional equality** (no `if d["measured"]` gate, which was the mutation escape hatch), plus
  `p95_seconds == max(runs_seconds)` and `type(x) is int` instead of `isinstance` (which accepts
  `True`).
- **8 [MINOR] `wrong_ref_note`** — added to `close_surface`, recording that the call targeted
  `surface:77` while the success line reports `surface:80`.

## Source Files Read

- `docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/task-000-quality-review.md` — the specification
  for this round.
- `docs/imp-plans/2026-07-30-cmux-spawn-v2/module-1-contracts-spikes.md` — Task 0 Steps 1/2/2b/2c/3/4
  and the Step 7 test body. Step 2b's prescribed `surface_uuid_source` shape turned out to be
  load-bearing (see Deviations).
- `docs/imp-plans/2026-07-30-cmux-spawn-v2/module-3-spawn-script.md` — `create_workspace_target`,
  `launch_into_target`, and the planned `list-pane-surfaces` stub, to establish which listing shape
  production actually parses.
- `docs/imp-plans/2026-07-30-cmux-spawn-v2/deviations.md` — the Task 0 finding rows and the pending
  dispositions.
- `tests/unit/fixtures/spawn-handoff/cmux-verb-shapes.json`,
  `tests/unit/fixtures/spawn-handoff/cold-start-timing.json`,
  `tests/unit/test_spawn_handoff_v2.py` — the write scope.
- Root `CLAUDE.md` — cmux vocabulary, the installed-binary-outranks-vendored-docs rule, and the
  worktree `.venv` symlink warning.

## Part A: live re-capture

Captured verbatim (byte-exact, verified with `od -c`):

- **State 1**, immediately after `cmux workspace create`:
  `* surface:96  task0-fix-multirow  [selected]\n`
- **State 2**, after `cmux new-surface --focus false` (which returned
  `OK surface:97 pane:37 workspace:37`):
  `* surface:96  task0-fix-multirow  [selected]\n  surface:97  Terminal\n`

**Which row carries `[selected]`:** row 1, `surface:96`, the workspace's auto-created surface. It
kept the marker — a `--focus false` new-surface does **not** take selection. This agrees with the
prompt's prediction and with the earlier `--id-format both` transcript already in
`surface_uuid_source`, so the behavior is stable across both capture sessions. Recorded as measured,
not as predicted.

**Which shape production hits: SINGLE-ROW.** Module 3's `create_workspace_target` runs
`cmux workspace create` and then *immediately* `list-pane-surfaces` on the brand-new workspace, so
the only listing the fallback path ever parses has exactly one row — and that row is selected,
therefore marker-prefixed. This is recorded in `selected_row_marker.production_shape` and asserted.

**Empirical confirmation of finding 4** — Module 3's exact awk run against real inputs:

| Input | awk output |
|---|---|
| live single-row (the production shape) | `*` |
| live two-row | `*` |
| Module 3's planned stub `surface:11 terminal [selected]` (no marker) | `surface:11` |
| isolated non-selected row | `surface:97` |

The parser is green against the marker-less stub and returns `*` against every real shape, which
then fails the `case "$SPAWN_SURFACE_REF" in surface:*)` gate — `create_workspace_target` returns 1
before `launch_into_target` runs. Recorded in `selected_row_marker.measured_awk_behavior`.

**Provenance seam annotated:** `capture_note_addendum` names exactly which two keys came from the
later session, states the binary was re-verified byte-identical beforehand, and explains why
`captured: "live"` therefore stays honest for the whole file — which is what keeps the finding-6 fix
from being a rubber stamp.

**A second-order fact captured while it was free:** the auto-created surface's title is the
*workspace name*, and a new surface's default title is `Terminal`. Titles contain spaces, so no field
index past the ref is stable. Recorded as `list_pane_surfaces_multi.row_titles` — relevant because a
parser tempted to reach for a later field has no safe one.

## Deviations from Plan

**1. The `surface_uuid_source["verb"]` rename in the MINOR batch was NOT applied — the review
misattributed it.** The fix prompt lists it as a "pure correction". It is not: Module 1 Step 2b
prescribes the shape verbatim as
`{"available": true, "verb": …, "key_path": …, "example": …}` (`module-1-contracts-spikes.md:121`),
where `verb` means *which cmux verb yields the UUID* — necessarily a command string. The implementer
followed the plan exactly. Renaming it would create a fixture that contradicts its own plan section,
and the plan is outside my write scope, so I cannot fix both halves. Surfacing rather than
reconciling, per instructions. Consumer risk is low: the only reader is
`test_audit_ordered_probe_keys_present`, which reads `.get("available")`/`key_path`, and nothing
iterates `["verb"]` generically (grepped). **Controller disposition needed** — either accept the
plan-prescribed shape as correct and close the item, or amend Step 2b and the fixture together.

**2. Refinement to the prompt's framing of finding 4 (not a contradiction).** The prompt says the
multi-row shape "exposes the `* ` selected marker". The existing single-row capture *already*
carried the marker (`* surface:76  task0-shapes  [selected]`), and that single-row shape is the one
production parses. What was genuinely missing was (a) any assertion pinning the marker and (b) the
fact that non-selected rows are two-space indented so their `$1` **is** the ref. The re-capture
supplies (b) and the tests supply (a). I wrote the fixture prose to say this rather than implying the
marker was undiscovered, so Module 3 fixes the single-row case it actually hits without breaking the
second row. Recorded in `selected_row_marker.production_shape`.

**3. The cold-start derivation had no ambiguity to resolve.** The prompt prescribes
`max(60, ceil(2 * max(runs) / 10) * 10)` (round the doubled sample); plan Step 5 and the fixture's
own `derivation` string both say `max(60, 2 x max)` *then* round (round the outer max). I checked
whether these can disagree before choosing: they are **identical for every input**, because 60 is
itself a multiple of 10 and round-up-to-10 is monotone. Verified exhaustively over samples 0–2000s —
zero disagreements. Encoded once with a comment recording the equivalence, so a future re-measure
past 30s cannot resurface the question.

**4. `cold-start-timing.json`: numbers untouched, one prose field corrected.** The newly encoded rule
holds against the stored values exactly as landed (`p95_seconds: 11`, `max(runs_seconds) == 11`, rule
yields 60, `default_seconds: 60`) — the prompt's instruction was to stop rather than adjust the
fixture to fit, and no numeric adjustment was needed.

Its `derivation` prose, however, carried **the same defect class as finding 5**: right value, wrong
implied mechanism. `"max(60, 2 x 11) = 60, rounded up to nearest 10 = 60"` is arithmetically correct
but reads as though the measurement produced 60. It did not — `2 x p95` is 22s, so the **spec floor
set the value and the samples only establish ~5.5x headroom**. `deviations.md` already records this
and states that Task 9's provenance comment "must say 'spec floor; Task 0 measured 8–11s cold start'
rather than implying 60 was measured", but a Module 3 implementer reading only the fixture would not
have learned it. Corrected in place, including the condition under which the floor stops dominating
(a re-measured max sample above 30s). My test pins `derivation` as non-empty, not as any particular
content, so this is a fidelity fix rather than a test-driven one.

**5. MINOR items deliberately deferred, with reasoning** (none silently dropped):

- *Trailing-newline normalization.* The original bytes are unrecoverable — re-capturing all ten verbs
  to restore verbatim fidelity is a full redo of Task 0, not a fix round, and would widen the
  provenance seam from two keys to the whole file. The two keys I captured are byte-exact.
- *`argv` re-runnability / `$HOME` unexpanded / placeholder refs.* These `argv` values are records of
  commands run against refs (`workspace:29`, `surface:77`) that no longer exist. Rewriting them into
  "re-runnable" form would mean publishing argv that was never executed — worse for fidelity than the
  placeholders, and squarely against Step 3's "verbatim, no hand-editing". My new key's `argv` is
  verbatim-accurate.
- *Volatile identifiers in captured screens.* Trimming full screens would destroy the verbatim
  capture, and `test_unplanned_discoveries_pinned` now asserts each trust anchor actually occurs
  *within* the captured screen — a check that only works while the screens are intact. Recommend
  keeping them.
- *`{meta, verbs, probes}` container restructuring.* Explicitly out of scope per the prompt; Module 3
  and other tasks consume the current top-level key paths.

**6. Not attempted (correctly out of scope):** the Module 3 Task 9 plan amendment that finding 4 also
requires — stub must carry the marker, parser must not read `$1` on marker rows. The fixture now
carries everything that amendment needs (`selected_row_marker.consumer` names it explicitly), but the
amendment itself is the controller's. No TODO was left in my files.

## Self-Review Findings

Every assertion was mutation-tested before being trusted. Mutations edited **fixtures only** — never
the test file, since a mutation that edits the assertion proves nothing. Restores used
`git checkout -- <paths>` exclusively (never `git stash` — shared stack across worktrees), and the
harness asserts a clean tree after each restore before proceeding.

**Result: 27/27 mutations caught; unmutated positive control green.** Full log:

| Mutation | Expected | Got |
|---|---|---|
| F1 `read_screen_cold.stderr` → unrelated error | RED | RED |
| F1 `read_screen_cold.exit` → 0 (positive control from the review) | RED | RED |
| F6 `captured` → `"matrix-fallback"` | RED | RED |
| F6 `cmux_version` → `"unknown"` | RED | RED |
| F2 `ref_resolution_scoping` INVERTED (the review's worst case) | RED | RED |
| F2 delete `ref_resolution_scoping` | RED | RED |
| F2 delete `trust_dialog_screen` | RED | RED |
| F2 trust `candidate_anchors` → `[]` | RED | RED |
| F2 trust anchor replaced with a string absent from the screen | RED | RED |
| F3 `latching` → false + evidence blanked | RED | RED |
| F3 `latching` evidence blanked only (boolean left true) | RED | RED |
| F3 `surface_uuid_source` → `{available: false}` | RED | RED |
| F3 uuid `transcript` blanked only | RED | RED |
| F4 multi stdout: strip the `* ` marker | RED | RED |
| F4 delete `list_pane_surfaces_multi` | RED | RED |
| F4 multi: drop row 2 | RED | RED |
| F4 multi: un-indent row 2 | RED | RED |
| F4 single-row `list_pane_surfaces`: strip the marker | RED | RED |
| F4 `production_shape` → `"MULTI-ROW"` | RED | RED |
| F4 delete `selected_row_marker` | RED | RED |
| A3a `rc_sent_line` made to contain `rc_anchor` (echo-defeat) | RED | RED |
| F7 `default_seconds` → 36000 | RED | RED |
| F7 `measured` → false | RED | RED |
| F7 `p95_seconds` → 99 | RED | RED |
| F7 `runs_seconds` → `[100]*5` | RED | RED |
| F7 `default_seconds` → `True` (bool-as-int) | RED | RED |
| F7 `derivation` blanked | RED | RED |
| CONTROL: unmutated tree | GREEN | GREEN |

Three of these are mutations the review did **not** ask for, added because the assertion they guard
was one I authored and therefore the easiest to write vacuously: un-indenting row 2, blanking
evidence *without* flipping the boolean, and making the `/rc` anchor echo-matchable.

Suite results: `tests/unit/test_spawn_handoff_v2.py` → **6 passed**. Full unit suite → **641 passed**
(baseline 638). Delta **+3**, exactly the three net-new test functions
(`test_verb_shapes_provenance_pinned`, `test_selected_row_marker_shape`,
`test_unplanned_discoveries_pinned`); the other three are the hardened originals. No regressions.

## Concerns

1. **The `surface_uuid_source["verb"]` item needs a controller decision, not an implementer one.**
   See Deviations #1. The review treated a plan-prescribed shape as an implementer inconsistency.
   Fixing it properly means touching the plan, which is outside my scope.

2. **Finding 4's actual fix is still pending in Module 3 and is the item most likely to be lost.**
   Task 0 can only record the fact; the dead workspace-fallback lives in `create_workspace_target`.
   The fixture now names its consumer explicitly and the amendment is tracked in `deviations.md`, but
   `transition-module.py` archives Module 1's reports at the boundary — so if the Module 3 Task 9
   amendment is not made before that transition, the strongest statement of the bug moves into
   `archive-*/`. This is the review's own stated reason for fixing during Module 1.

3. **`close_surface`'s wrong-ref property is documented but has no consumer.** `close-surface` is
   called nowhere in Modules 3–4. `wrong_ref_note` prevents the fact from being lost, but nothing
   tests a behavior that does not exist yet. Intentional; flagged so it is not mistaken for coverage.

4. **The trust-dialog anchor assertion is now coupled to the full captured screens.** Asserting each
   anchor occurs within `trust_dialog_screen.screen` is a genuine strengthening, but it means the
   MINOR "trim volatile identifiers from screens" item can no longer be applied casually — a future
   trim must keep the anchor regions. Deliberate trade-off, recorded here so the coupling is not
   discovered by a surprise failure.

5. **Provenance is now honest but no longer single-session.** `cmux-verb-shapes.json` mixes two
   capture sessions against the same verified binary. `capture_note_addendum` states this precisely.
   If a third capture session is ever needed, extend that addendum rather than restamping
   `captured_at`.
