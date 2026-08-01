# Task 0 — Code Quality Re-Review, Round 2 (adversarial)

**Verdict: APPROVED** — with three MINOR items routed forward (none blocking, none reopening Task 0).

Round 1 returned CHANGES_REQUESTED on 17 surviving mutations. **All seven numbered findings are
CLOSED by execution**, and the MINOR batch is dispositioned honestly (one item correctly refused, four
deliberately deferred with reasoning that holds up). I ran **71 fixture mutations** against the fix
round's work: **43 RED, 28 GREEN, zero expectation mismatches**, with **4 negative controls** that
stayed GREEN — proving the probe discriminates rather than being globally sensitive. Every one of the
30-odd mutations round 1 prescribed or implied now goes RED.

The fix round's own claims were spot-checked rather than trusted, and both of the two claims I was
asked to adjudicate independently are **correct**. Half B of finding 4 — the consumer-side plan
amendment in `949d310` — is real, landed, and verified by running the new awk myself against **nine**
inputs (the controller tested five).

Fixtures restored with `git checkout --` after every single run; tree verified clean between runs and
at finish (only the two pre-existing untracked logs `.dispatch-log` and `context-observations.log`
remain, as at session start). No test file, fixture, or plan file was modified by this review.

---

## Per-finding disposition

### Finding 1 [BLOCKING] — dead disjunct in `read_screen_cold` → **CLOSED**

`tests/unit/test_spawn_handoff_v2.py:36-40` now pins the error *class* on `stderr` **and** `exit != 0`,
with a comment (`:33-35`) explaining why the `in stdout` disjunct cannot come back.

| Mutation | Result |
|---|---|
| `read_screen_cold.stderr` → `"Error: banana: something else entirely"` (round 1's surviving mutation) | **RED** |
| `read_screen_cold.exit` → `0` (round 1's positive control) | **RED** |

The exact mutation that survived round 1 is now caught.

### Finding 2 [BLOCKING] — unplanned discoveries deletable / invertible → **CLOSED**

`test_unplanned_discoveries_pinned` (`:91-119`).

| Mutation | Result |
|---|---|
| `ref_resolution_scoping` **INVERTED** (`requires_workspace_flag: []`, every verb moved to `resolves_cross_workspace_bare`) — round 1's worst case | **RED** |
| delete `ref_resolution_scoping` | **RED** |
| **COPY** `rename-tab` into `resolves_cross_workspace_bare` (leaving it in `requires`) — the one-sided-assertion escape | **RED** |
| drop `send` from `resolves_cross_workspace_bare` | **RED** |
| `scoping.evidence` → `{}` | **RED** |
| delete `trust_dialog_screen` | **RED** |
| `candidate_anchors` → `[]` | **RED** |
| anchor replaced with a string absent from the screen | **RED** |
| `trust.observed` → `False` | **RED** |

The `verb not in bare` half (`:108`) and the `anchor in trust["screen"]` half (`:119`) are the two the
implementer authored rather than the review dictating — I mutation-tested both specifically, since
self-authored assertions are the vacuity risk. Both hold.

### Finding 3 [BLOCKING] — escalation triggers recorded but not asserted → **CLOSED**

`test_audit_ordered_probe_keys_present` (`:154-199`).

| Mutation | Result |
|---|---|
| `latching` → `false` + evidence blanked | **RED** |
| `latching` evidence blanked **only** (boolean left `true`) — distinguishes unrun from run | **RED** |
| `surface_uuid_source` → `{"available": false}` | **RED** |
| uuid `transcript` blanked **only** | **RED** |
| uuid `key_path` blanked | **RED** |

See "Are the escalation-trigger assertions right?" below for my judgment on `is True` — short answer:
correct as a mechanism, one mis-citation in a message (NEW-3).

### Finding 4 [IMPORTANT] — degenerate single-row capture + broken awk → **CLOSED, both halves**

**Half A (fixture) — verified.** `cmux-verb-shapes.json:21-30` adds `list_pane_surfaces_multi`;
`:31-39` adds `selected_row_marker`. `test_selected_row_marker_shape` (`:59-89`) pins the shape.

| Mutation | Result |
|---|---|
| multi row 1: strip the `* ` marker | **RED** |
| delete `list_pane_surfaces_multi` | **RED** |
| multi: drop row 2 | **RED** |
| multi: un-indent row 2 (self-authored assertion `:81`) | **RED** |
| multi: remove row 2's ref, leaving a title (self-authored `:82`) | **RED** |
| **single-row** `list_pane_surfaces`: strip the marker | **RED** |
| `production_shape` → `"MULTI-ROW"` (inversion) | **RED** |
| delete `selected_row_marker` | **RED** |
| `awk_consequence` blanked | **RED** |

**Half B (consumer, `949d310`) — verified BY EXECUTION, not by reading.** I extracted the awk
programmatically from `module-3-spawn-script.md:375-376` (not from the diff) and ran it, plus the old
parser, against nine inputs:

| Input | NEW awk | OLD awk |
|---|---|---|
| live single-row — **the production shape** | `surface:76` | `*` |
| live two-row | `surface:96` | `*` |
| new stub, `module-3-spawn-script.md:275` (`* surface:11  SDD resume: demo  [selected]`) | `surface:11` | `*` |
| old marker-less stub (`surface:11 terminal [selected]`) | `surface:11` | `surface:11` |
| lone non-selected row | `surface:77` | `surface:77` |
| selected **not** first | `surface:76` | `*` |
| empty input | `""` (bare `\n`) | `""` |
| selected row with no `surface:N` token, non-selected first | `surface:77` | `*` |
| title *containing* a `surface:99`-shaped token | `surface:76` | `*` |

**The controller's claim is confirmed in both directions**: the new awk yields a valid `surface:N` on
all five of its cited cases; the old awk returned `*` on the first two (the live shapes). Every output
was **exactly one line** — the `break`/`exit` structure plus a single `END{print}` makes multi-line
output unreachable, so the newline-globs-`surface:*` hazard the original comment guarded is preserved.
Empty input yields a bare newline that command substitution strips to `""`, which correctly fails the
`case surface:*` gate at `:377` → `return 1`. Two robustness properties the controller did not claim
but which hold: the first-match `break` makes the parse immune to a `surface:N`-shaped *title* token,
and a selected row with no ref degrades to the earlier row's ref rather than emitting garbage (not
reachable in real output).

**Bug class closure — grepped, and it is closed.** `list-pane-surfaces` has exactly **one** parsing
call site in Modules 3–4 (`module-3-spawn-script.md:374-376`; the awk program itself is `:375-376`,
`:374` being the `cmux list-pane-surfaces` pipe). The only other field-position parses
are `awk '/^OK[ \t]/{print $2; exit}'` at `:352` and `:366`, applied to `new-surface`
(`OK surface:N pane:M workspace:K`) and `workspace create` (`OK workspace:N`) — field 2 is the ref in
both, correct. The two verbs whose field 2 is a *trap* are handled without field parsing: `rename-tab`
is success-checked with `case "$rt_out" in OK*)` (`:383`, with an explanatory parenthetical at `:387`),
and `close-surface` is called nowhere in Modules 3–4. See NEW-2 for the one stub instruction the
amendment did not reach.

### Finding 5 [IMPORTANT] — `impact` right conclusion, wrong mechanism → **CLOSED (prose), residual noted**

`cmux-verb-shapes.json:157` now states the measured consequence (a missing tab title, because
`launch_into_target` warns-and-continues on rename-tab failure and `send` reaches cross-workspace
bare), and `:158` adds `impact_correction_note` naming `selected_row_marker` as the *real* cause of
the dead fallback so an implementer who adds `--workspace` cannot conclude it is fixed. I verified the
claim independently: `module-3-spawn-script.md:382-383` is indeed warn-and-continue, and
`close-surface` has no caller.

Residual (expected, not a defect): reverting `impact` to `"Breaks the workspace-fallback path."` and
deleting `impact_correction_note` **survives GREEN**. Prose correctness is not mechanically pinnable
in general, and round 1 asked for a correction, not an assertion. Recorded so it is not mistaken for
coverage.

### Finding 6 [IMPORTANT] — provenance unpinned → **CLOSED as scoped**

`test_verb_shapes_provenance_pinned` (`:43-56`).

| Mutation | Result |
|---|---|
| `captured` → `"matrix-fallback"` | **RED** |
| `cmux_version` → `"unknown"` | **RED** |

Round 1 explicitly routed the broader per-verb coverage as plan-owned ("route to whoever amends
Module 1"), so the following surviving mutations are **in-scope residuals, not regressions** — I ran
them to quantify what remains: `new_surface.stdout` → `"OK surface:77 GARBAGE:0 NOTAWORKSPACE"`;
`close_surface.stdout` → arbitrary; deleting `send`/`send_key`/`read_screen_warm`/`wait_for` and both
negative keys in one shot; deleting every `argv`; `captured_at` → `1999-01-01`;
`cmux_version` → `"cmux 0.1.0 (1) [deadbeef]"` (only the `"cmux "` prefix is pinned);
`capture_note_addendum` deleted. All GREEN. Still plan-owned.

### Finding 7 [IMPORTANT] — one-directional cold-start test → **CLOSED**

`test_cold_start_default_derivation` (`:122-151`) now encodes the rule as an **unconditional
equality** (`:145`), asserts `p95_seconds == max(runs)` (`:139`), and uses `type(x) is int` (`:132-133`,
`:138`) rather than `isinstance`.

| Mutation | Result |
|---|---|
| `default_seconds` → `36000` | **RED** |
| `measured` → `false` (round 1's escape hatch) | **RED** |
| `p95_seconds` → `99` | **RED** |
| `runs_seconds` → `[100]*5` | **RED** |
| `default_seconds` → `True` (bool-as-int) | **RED** |
| `derivation` blanked / `method` blanked | **RED** / **RED** |
| **stale default**: `runs → [40]*5`, `p95 → 40`, `default_seconds` left at 60 | **RED** |
| `runs_seconds` → `[]` | **RED** |
| `runs_seconds` → `["11", …]` (strings) | **RED** |
| `p95` left at 11 while a run becomes 99 | **RED** |
| **NEGATIVE CONTROL** — legitimate re-measure: `runs [40,41,42,43,45]`, `p95 45`, `default 90` | **GREEN** ✅ |

That last row is the important one: the assertion is a *rule*, not a frozen value, so a genuine
re-measure passes while an inconsistent one fails.

### MINOR batch (8–10) → **dispositioned; one refused correctly, four deferred defensibly**

- **`wrong_ref_note` on `close_surface`** — added (`cmux-verb-shapes.json:95`). Deleting it survives
  GREEN, which is fine: it documents a property with no consumer (`close-surface` is called nowhere
  in Modules 3–4), and the fix report flags exactly that in Concern 3.
- **`surface_uuid_source["verb"]` rename** — **refused, and the refusal is correct.** See adjudication
  below.
- **Trailing-newline normalization** — deferred. Defensible: re-capturing all ten verbs is a redo of
  Task 0 and would widen the provenance seam from two keys to the whole file. Two supporting facts I
  checked: the plan's Step 2 capture used `$(...)` command substitution, which strips trailing
  newlines, so *every* recorded `\n` was re-added — `wait_for.stdout: "OK"` is the honest outlier, not
  the anomaly; and nothing in Modules 3–4 parses `wait_for` stdout (it is exit-code-only,
  `module-3-spawn-script.md:486-488`). The stated reason ("original bytes unrecoverable") is slightly
  overbroad for that single field, but the disposition is right.
- **`argv` re-runnability / `$HOME` / placeholders** — deferred. Correct: those refs no longer exist,
  and rewriting them would publish argv that was never executed, which is worse under Step 3's
  "verbatim — no hand-editing".
- **Screen trimming** — deferred, with a genuine new reason: `:119` now asserts each trust anchor
  occurs *within* the captured screen, so trimming would have to preserve the anchor regions. The fix
  report records this coupling as Concern 4 rather than letting it surface as a mystery failure later.
- **`{meta, verbs, probes}` restructuring** — deferred; explicitly out of scope and consumers use the
  current top-level paths.

Nothing was deferred that should not have been.

---

## Adjudication of the two claims

### Claim 1 — the `surface_uuid_source["verb"]` refusal: **CORRECT, not a rationalization**

`module-1-contracts-spikes.md:121` prescribes verbatim:

> Record `surface_uuid_source` as `{"available": true, "verb": …, "key_path": …, "example": …}` …

In that sentence `verb` means *which cmux verb yields the UUID* — necessarily a command string. The
implementer followed the plan exactly; renaming would put the fixture in conflict with its own plan
section, and the plan is outside Task 0's write scope. **Round 1 misattributed a plan-owned shape to
the implementer.** The refusal is upheld.

The *underlying* inconsistency is nonetheless real and remains: the fixture's key `verb` now carries
two incompatible meanings — a snake_case key name in the per-verb records (Step 3's `{"verb", "argv",
"stdout", "exit"}`) and a command string in `surface_uuid_source` (Step 2b). The plan itself
introduced the collision. The controller's disposition — accept the plan-prescribed shape, record that
generic iteration over `["verb"]` is unsafe for this fixture, route it as a Module 3 note — is the
right call. I confirmed by grep that nothing iterates `["verb"]` generically today.

### Claim 2 — the fix round's correction to finding 4's framing: **CORRECT, and it makes the finding stronger**

Verified against the pre-fix blob, not the current file:

```
$ git show 48608fb:tests/unit/fixtures/spawn-handoff/cmux-verb-shapes.json
list_pane_surfaces.stdout == '* surface:76  task0-shapes  [selected]\n'
list_pane_surfaces_multi present: False
selected_row_marker present:     False
```

The `* ` marker was **already** in the original single-row capture. And single-row is the shape
production parses: `create_workspace_target` (`module-3-spawn-script.md:359-378`) runs
`cmux workspace create` and then *immediately* `list-pane-surfaces` on the brand-new workspace, which
has exactly one surface, and that surface is selected — so it is marker-prefixed. The real defect was
therefore (a) no assertion pinning the marker and (b) a marker-less stub, **not** a missing multi-row
capture.

This makes the finding stronger, exactly as claimed: the broken `$1` branch was hit **100% of the
time** on the only path that reaches it, not merely in a multi-surface edge case. Round 1's own awk
table already implied this (`* surface:76 … → *`), but the framing said otherwise. Surfacing the
correction rather than silently reconciling it was the right behavior.

### Are the escalation-trigger assertions right? — **Yes, as a mechanism**

Asserting `is True` does **not** make a negative unrecordable. It makes a future legitimate `false`
turn the suite RED, and in this repo a RED gate *is* the escalation channel — a fixture whose value
silently flipped is precisely round 1's finding 3. The alternative (`isinstance(..., bool)`) is what
let the inversion pass. The assertion messages carry the escalation instruction to whoever hits the
failure (`:171-172`, `:182-183`), which is the property that matters: the reader is told to STOP and
amend the plan, not to edit the fixture until green.

One precision defect in that framing, though — see NEW-3.

### `cold-start-timing.json` — arithmetic and prose both check out

- **Arithmetic**: `max(runs) = 11`; `2 × 11 = 22`; `max(60, 22) = 60`; `ceil(60/10) × 10 = 60` =
  `default_seconds: 60`. ✅ And `p95_seconds: 11 == max(runs_seconds)`. ✅
- **Equivalence claim verified exhaustively, not asserted**: `ceil(max(60, 2m)/10)*10` vs
  `max(60, ceil(2m/10)*10)` over `m ∈ [0, 5000]` → **0 disagreements**. (Reason: for `m ≤ 30` both pin
  to 60; for `m > 30` the outer max is inert.) The comment at `:141-144` is accurate.
- **Prose**: `cold-start-timing.json:18` no longer reads as though 60 were measured. It states the
  floor dominated, gives `2 × p95 = 22s`, quantifies the headroom (~5.5×), tells consumers the exact
  provenance wording for Task 9, and names the condition under which the floor stops dominating
  (a re-measured max above 30s). Correct and useful.

---

## New findings (severity-ranked; none blocking)

### NEW-1 [MINOR] — the marker ↔ `[selected]` correlation, the very fact finding 4 is about, is not pinned

`test_spawn_handoff_v2.py:78` asserts `rows[0].startswith("* ")` and its *message* says "row 1 is the
selected row and carries the `* ` marker" — but **no assertion checks that `[selected]` is on that
row**, or present at all. Mutations that survived GREEN:

- move `[selected]` to row 2 while keeping `* ` on row 1 — inverts the measured fact
- delete `[selected]` from both rows
- delete `[selected]` from the single-row `list_pane_surfaces` capture
- invert `selected_row_marker.fact` to claim `* ` prefixes the **non**-selected rows
- invert `list_pane_surfaces_multi.selected_row` to claim row 2 took selection

By the fix round's own stated principle (`test_spawn_handoff_v2.py:5-8`: "a fixture that can be
silently inverted is worse than one that is absent"), this is the last invertible statement of
finding 4's content. Impact is bounded — the landed Half-B parser matches by pattern and does not
depend on the correlation, and the amended stub at `module-3-spawn-script.md:275` already carries both
tokens on the same row — so this is MINOR, not a reopen. **Fix when the file is next touched** (one
line): `assert "[selected]" in rows[0] and "[selected]" not in rows[1]`, plus the same on the
single-row capture. Route to Module 3 Task 9's test step.

### NEW-2 [MINOR] — Task 17's cmux stub instruction was not amended alongside Task 9's

`module-4-card-hooks-docs.md:602` still says the e2e stub's `list-pane-surfaces` should emit "the Task
0 shape". Task 0 now records **two** shapes, and `949d310` amended only Task 9's parenthetical
(`module-3-spawn-script.md:281`) to *require* the marker and name `selected_row_marker`. An
implementer writing Task 17's stub from that vaguer instruction can reproduce the marker-less stub —
the exact fidelity gap that made the old parser look green. Low impact (the parser is now
pattern-based, so a marker-less e2e stub produces a false *pass*, not a false failure) but it means
the e2e would not guard a regression back to `$1`. Route: mirror Task 9's wording into Task 17 Step 1.

### NEW-3 [MINOR] — `surface_uuid_source.available` assertion cites the wrong plan step, and calls a plan-declared-legitimate outcome an escalation

`test_spawn_handoff_v2.py:171-172` says *"Step 2c escalation trigger: available=false …"*. But
`available` is defined in **Step 2b** (`module-1-contracts-spikes.md:121`), which states plainly:
**"Unavailable is a legitimate documented outcome, not a failure."** Step 2c
(`module-1-contracts-spikes.md:133`) is the `latching` probe, and *it* is the one that says "If false:
STOP and report to the controller" — so the sibling assertion at `:182-183` cites correctly.

The mechanism is still defensible (a legitimate `false` should reach the controller, which is what
Step 2b's "the controller converts operator addendum #1 into a recorded refusal" requires, and RED is
how it gets there). What is wrong is the *citation*: a future reader sent to Step 2c will find nothing
about `available` and may conclude the assertion is spurious.

**Ownership — read this before routing.** This mis-citation originated in **round 1's own finding 3**,
which conflated Steps 2b and 2c; the fix round faithfully implemented what the review asked for. It is
**not a fix-round defect and must not be bounced back as a re-dispatch.** The remedy is a comment/
message edit owned by whoever next touches the test file: cite Step 2b and say "a legitimate `false`
must reach the controller as a recorded refusal, not pass silently".

### NEW-4 [MINOR] — `len(rows) == 2` encodes an accidental capture value, not a contract

`test_spawn_handoff_v2.py:77`. Verified: a legitimate 3-surface re-capture goes **RED**, and for the
wrong reason (row count, not shape). `>= 2` still catches the "drop row 2" mutation — which I
confirmed by running that mutation — while surviving a re-measure. Bundle with NEW-1's one-line edit.

Also observed and *not* raised as findings, for completeness: `list_pane_surfaces.exit` is unpinned
while `list_pane_surfaces_multi.exit` is (`:75`) — a harmless asymmetry; and
`wait_for_latching.one_shot` prose plus the numeric rcs (`signal_then_wait_rc`, `rewait_rc`) can be
inverted to contradict the pinned boolean. The decision variable (`latching`) is pinned and that is
what Task 10 consumes.

---

## Empirical vs. reasoned

**Verified by execution (primary evidence):**

- All 71 fixture mutations and their pass/fail outcomes, each with a `git checkout --` restore and a
  `git status --porcelain` clean assertion between runs.
- 4 negative controls held GREEN: unmutated baseline (run twice), an unasserted field mutated
  (`workspace_create.argv` → garbage), and a legitimate cold-start re-measure. The probe discriminates.
- Half B's awk: 9 inputs × 2 parsers = 18 executions, program extracted programmatically from
  `module-3-spawn-script.md:375-376` rather than transcribed.
- Claim 2, against the pre-fix blob `48608fb` — the marker was already present, and neither new key
  was.
- The rounding-rule equivalence, exhaustively over `m ∈ [0, 5000]`.
- Full unit suite: **641 passed** (baseline 638, delta +3 = the three net-new test functions).
- Plan gate on all five manifest files: **exit 0, PASS, 0 warnings** each.
- Task 9 spans exactly **200 lines** (`module-3-spawn-script.md:253-452`) — the controller's
  net-zero-delta claim under the 200-line limit is true.
- Bug-class grep: one `list-pane-surfaces` parse site; `rename-tab` uses `case OK*`; `close-surface`
  has no caller.

**Reasoned, not executed:**

- That the landed Half-B parser fixes the fallback *in production* — `spawn-handoff-session.sh` v2 does
  not exist yet, so this remains a prediction about unwritten Module 3 code, exactly as in round 1. I
  proved the awk's behavior on real inputs; I did not prove the script that will embed it.
- NEW-1's and NEW-2's impact ratings (that a marker-less e2e stub yields a false pass rather than a
  false failure) — derived from the parser's verified behavior, not from running the e2e.
- That the capture-time `$(...)` stripping explains the trailing-newline inconsistency (the
  inconsistency is proven; the cause is inferred from the plan's Step 2 snippet).
- Severity ordering among NEW-1..4.

**Not checkable here:**

- Whether the live re-capture actually happened as described, and whether `task0-fix-multirow` was
  truly cleaned up — I cannot re-run live cmux or inspect the user's sidebar. The recorded shapes are
  internally consistent with the earlier `--id-format both` transcript in `surface_uuid_source`, which
  is corroboration, not proof.
- Correctness of the 8–11s cold-start measurements themselves (same limitation as round 1).
- Spec compliance (passed separately in round 1's spec review).

---

## Mutation / control tally

| | Count |
|---|---|
| Total fixture mutations run | **71** |
| Caught (RED) | **43** |
| Survived (GREEN) | **28** |
| Expectation mismatches | **0** |
| Round-1-derived mutations expected RED | **38 / 38 caught** |
| Negative controls expected GREEN | **4 / 4 held** |
| awk executions (Half B verification) | **18** (9 inputs × 2 parsers) |
| Tree-clean assertions after restore | **71** (one per mutation) |

Of the 28 survivors: **2** are the deliberate negative controls; **7** are the per-verb /
provenance-breadth items round 1 explicitly routed as plan-owned (`new_surface.stdout`,
`close_surface.stdout`, bulk verb-key deletion, bulk `argv` deletion, `captured_at`, a wrong
`cmux …` build string, `capture_note_addendum`); **8** are the NEW-1 cluster (the marker ↔
`[selected]` correlation and the prose fields describing it); and the remaining **11** are
documentation strings with no consumer, most of which the fix round itself disclosed as non-pinned
(`impact`, `derivation`, `measured_awk_behavior`, `consumer`, `wrong_ref_note`, `picker_version`,
`method_deviation`, `send_after_rc_landed`, `one_shot`, the `wait_for_latching` numeric rcs, and
`list_pane_surfaces.exit`). 2 + 7 + 8 + 11 = 28.

**Round 1: 17 surviving mutations. Round 2: 0 surviving mutations among those round 1 identified.**
The fix round did the work it claimed, verified it the way it claimed, and told the truth about what
it refused and deferred.
