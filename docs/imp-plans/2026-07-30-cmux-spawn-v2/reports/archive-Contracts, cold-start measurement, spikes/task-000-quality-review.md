# Task 0 — Code Quality Review (adversarial)

**Verdict: CHANGES_REQUESTED**

Dispatched deliberately despite implementer-green + spec-review-PASS + 638-test-green, because that
exact combination has shipped surviving mutations in this repo before. It did again:
**17 mutations SURVIVED; all 5 positive controls were CAUGHT** (the probe demonstrably works).
Fixtures restored via `git checkout --` after every run; tree confirmed clean, 3/3 green.

Nothing blocks Task 1's *dispatch*. The reason to fix during Module 1: `transition-module.py`
archives Module 1's reports at the boundary, and the `*`-marker finding below exists nowhere else —
not in the plan, not in deviations, not in the fixture. Unwritten now = unfindable by Module 3.

## [BLOCKING] 1 — `read_screen_cold` assertion has a permanently-dead disjunct

`tests/unit/test_spawn_handoff_v2.py`, last line of `test_verb_shapes_fixture_contract`.
The implementer correctly split stdout/stderr (the plan's `2>&1` conflated streams), which makes
`d["read_screen_cold"]["stdout"] == ""`, so `"internal_error" in stdout` is permanently `False`.
The assertion survives only on `exit != 0`.

- Mutation: `read_screen_cold.stderr` → `"Error: banana: something else entirely"` → **3 passed**.
  The error *class* — the whole point of the negative fixture — is unpinned.
- Positive control: `read_screen_cold.exit` → `0` → **1 failed**.

**The one genuine implementer defect here.** The test body is otherwise verbatim from plan Step 7,
so its other weaknesses are plan-owned; changing the capture shape without adapting the assertion it
invalidated was the implementer's call, and the deviations row treated survival as sufficiency.
Fix: `assert "internal_error" in d["read_screen_cold"]["stderr"] and d["read_screen_cold"]["exit"] != 0`

## [BLOCKING] 2 — Neither unplanned discovery is pinned; `ref_resolution_scoping` can be silently INVERTED

Both are correctly routed to deviations ("Pending — Module 3"); the fixture is the problem.
Mutations, all SURVIVED (3 passed): delete `ref_resolution_scoping`; **invert it**
(`requires_workspace_flag: []`, all verbs moved to `resolves_cross_workspace_bare`);
delete `trust_dialog_screen`. The inversion would tell Module 3 the exact opposite of measured
truth, with a green suite.

Fix: assert `rename-tab` and `close-surface` are in `requires_workspace_flag`; assert
`trust_dialog_screen` anchors non-empty.

## [BLOCKING] 3 — Escalation triggers recorded but not asserted; `latching: false` passes

Module 1 Step 2c defines `latching: false` as STOP-and-escalate. Mutation:
`wait_for_latching.latching` → `false` with evidence blanked → **3 passed**. Same for
`surface_uuid_source` reduced to `{"available": false}` with no transcript → **3 passed**.
`isinstance(..., bool)` is defensible as a *presence* check (plan-prescribed), but nothing stops a
re-capture from flipping the value, and an unrun probe recorded as `false` is indistinguishable
from a run one because no evidence field is required.

Fix: assert `latching is True` (message citing Step 2c), assert `evidence` non-empty; same for
`surface_uuid_source.available` / `transcript`.

## [IMPORTANT] 4 — `list_pane_surfaces` captured only the DEGENERATE single-row case; Module 3's awk parser breaks on the real shape

Highest-value finding. Module 3's `create_workspace_target` parses with
`NR==1{first=$1} /\[selected\]/{print $1; f=1; exit} END{if(!f) print first}` then gates on
`surface:*`. Verified by running that exact awk against real inputs:

| Input | awk output |
|---|---|
| `* surface:76  task0-shapes  [selected]` (live) | `*` |
| `surface:11 terminal [selected]` (module-3's planned stub) | `surface:11` |
| live two-row listing | `*` |
| non-selected row alone | `surface:77` |

awk's default FS strips leading whitespace, so the `* ` marker is its own field: the `[selected]`
branch **never** yields a valid ref, only the `END` fallback can — and a freshly-created fallback
workspace has exactly one, selected, surface. **The broken branch wins deterministically on the only
path that reaches this code**, so the workspace fallback is dead in production while green against
the planned stub.

Why this is Task 0's to fix: module-3 says *"copy the exact `list-pane-surfaces` line format from
Task 0's capture"* — and that capture is single-row, because Step 2 ran `list-pane-surfaces`
*before* `new-surface`. The multi-row shape exists only buried inside
`surface_uuid_source.transcript`.

Fix (Task 0): promote a multi-row listing to a first-class key `list_pane_surfaces_multi` with a
`selected_row_marker` note ("`* ` prefixes the selected row; awk `$1` is `*`, NOT the ref;
non-selected rows are 2-space indented so their `$1` IS the ref") + an assertion pinning
`stdout.startswith("* ")`. Then route to **Module 3 Task 9**: stub must carry the marker; parser
must not read `$1` on marker rows.

Note this is the THIRD variant of this bug class — the plan review's round 1 already fixed "an awk
two-line surface-ref bug."

## [IMPORTANT] 5 — `ref_resolution_scoping.impact` reaches the right conclusion by the WRONG mechanism

Prose claims the missing `--workspace` "breaks the workspace-fallback path." Traced: Module 3's
`launch_into_target` treats `rename-tab` failure as cosmetic warn-and-continue, and the fixture's own
`resolves_cross_workspace_bare` says `send` works cross-workspace bare. So the cost is a tab title,
not the launch. `close-surface` is **not called anywhere in Modules 3-4** (grepped) — that
prescription has no consumer. The fallback IS broken, but by finding 4, which aborts
`create_workspace_target` before `launch_into_target` runs. A Module 3 implementer who adds
`--workspace` will believe it is fixed; it will not be.

Fix: correct `impact` to the measured consequence; stop attributing the fallback break to ref scoping.

## [IMPORTANT] 6 — No test pins any per-verb key beyond the four named, nor provenance metadata

All SURVIVED: `new_surface.stdout` → `"OK surface:77 GARBAGE:0 NOTAWORKSPACE"` (only fields 0-1
pinned though the spec pins the whole `OK surface:N pane:M workspace:K` shape); `close_surface.stdout`
→ arbitrary; deleting `send`/`send_key`/`read_screen_warm`/`list_pane_surfaces`/`wait_for` and BOTH
negative keys in one shot; deleting every `argv`; **`captured` → `"matrix-fallback"` and
`cmux_version` → `"unknown"`** — i.e. the file can claim it was never live-captured, and
`captured: "live"` is the plan's own blocked-path discriminator.

Fix (cheap, do now): `assert d["captured"] == "live"`, `assert d["cmux_version"].startswith("cmux ")`.
Broader per-verb coverage is plan-owned — route to whoever amends Module 1.

## [IMPORTANT] 7 — `test_cold_start_default_derivation` is one-directional; an absurd timeout ships silently

Module 3 Task 9's import assertion is a *consistency* check against this fixture, so this test is the
only guard on the value. All SURVIVED: `default_seconds` → `36000`; `measured` → `false` while
`runs_seconds` stays `[900]*5` (the `if d["measured"]` guard disables the only upper-bound check);
`derivation`/`method` blanked. Positive control `runs_seconds` → `[100]*5` → **1 failed**.
The fixture states the rule; the test doesn't encode it. Also `isinstance(x, int)` accepts `True`.

Fix: `expected = max(60, math.ceil(2 * max(runs) / 10) * 10)`; assert equality and
`p95_seconds == max(runs_seconds)`.

## [MINOR] 8-10

- `close_surface`'s wrong-ref property is load-bearing (pinned in spec + plan) but un-annotated;
  discoverable only from `ref_resolution_scoping.evidence` prose. Add a `wrong_ref_note`. Kept MINOR
  because nothing in Modules 3-4 calls `close-surface`.
- Fixture fidelity vs. Step 3's "verbatim — no hand-editing": trailing newlines inconsistent
  (`wait_for.stdout` is the only success stdout without `\n`, so newlines were re-added selectively);
  `argv` not re-runnable (placeholders, embedded prose in `wait_for.argv`, lost quotes in
  `rename_tab_no_workspace_ctx.argv`); `$HOME` unexpanded in one argv but absolute in another;
  `surface_uuid_source["verb"]` holds a command string while every other `["verb"]` holds the
  snake_case key name (generic iteration gets two different things); no container separation between
  metadata / verbs / probes — consider `{"meta", "verbs", "probes"}` before more keys land.
- Volatile identifiers in captured screens (remote-control URL, hostname, tty, login timestamp).
  `rc_anchor`/`rename_anchor` are what Module 3 consumes, so full screens could be trimmed.

## Empirical vs. reasoned boundary

**Verified by execution:** all 17 mutations + 5 positive controls; the dead disjunct evaluated
directly; the `*`-marker awk run against live single-row, live two-row, planned-stub, and isolated
non-selected inputs; fidelity inconsistencies scanned programmatically; `isinstance(True, int)`;
`close-surface` absent from Modules 3-4 by grep.

**Reasoned, not executed:** that `create_workspace_target` returning 1 kills the fallback in
production (Module 3's script does not exist yet — a prediction about unwritten code); that
`wait_for.stdout` was hand-normalized (inconsistency proven, cause inferred); severity ordering
between findings 4 and 5.

**Not reviewed:** spec compliance (passed separately); correctness of the 8-11s measurements (cannot
re-run live cmux).
