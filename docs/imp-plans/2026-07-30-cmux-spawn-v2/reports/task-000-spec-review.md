# Task 0 — Spec Compliance Review

**Verdict: PASS** — spec compliant and contract compliant, confirmed by reading the artifacts
rather than the report.

## Fabrication affirmatively excluded (three independent cross-checks)

1. **Chronology.** The `wait_for_latching` transcript's token suffix `task0-latch-21499-1785442362`
   decodes to 2026-07-30 14:12:42 MDT — between the shapes capture (`read_screen_warm`:
   `Last login: Thu Jul 30 14:08:48`), the trust-dialog capture (14:17:15), and the commit
   (14:24:09). A synthesized fixture does not carry a coherent embedded clock.
2. **UUID cross-reference.** `FAA9AA87-BB59-44A5-B33D-843764088D12` appears independently in the
   `identify --id-format both` transcript AND the `list-pane-surfaces --id-format both` transcript,
   bound to `surface:77` in both. Ref numbers (`workspace:29`, `surface:76/77`, `pane:29`, `tab:77`)
   agree across every key captured in that session.
3. **Arithmetic + preconditions.** Recomputed independently: `max(runs)=11 == p95_seconds`;
   `max(60, 2x11)=60`, round-up-to-10 `=60 == default_seconds`, a true `int`. Poll-granularity
   residue (8/10/11 against a 2s poll) is consistent with real accumulated latency, not round-number
   synthesis. `picker_version 2.1.220` on disk since Jul 24, so "download excluded from timing"
   genuinely held and `ls -t | head -1` would have selected it.

## Spec coverage (line by line)

All 10 Step-2 verbs captured; Step 3's `cmux_version` + `captured: "live"` present; all three
audit-ordered probe keys carry real (not placeholder) answers; Step 5 schema complete; Step 6
cleanup confirmed live (`cmux list-workspaces` → zero `task0-*`, 5 pre-existing user workspaces
intact); Step 7's test file byte-identical to the plan except a dropped fence comment and one blank
line (diffed programmatically); Step 8's 3 tests pass. Commit is exactly the 3 specified files;
`gen_fixtures.py` absent from `git ls-files`.

## Contract constraints — each read at its encoding site

- **All five pinned shapes confirmed, none contradicted**, so the escalation duty never triggered:
  `rename_tab.stdout` field 2 = `action=rename`; `close_surface` returned `surface:80` when closing
  `surface:77` (plausible wrong ref); `read_screen_cold` → `internal_error`, exit 1; `new_surface` →
  `OK surface:77 pane:29 workspace:29`; `workspace_create` → `OK workspace:29`.
- **Token-only exit-0 honored.** Nothing in this commit produces a production readiness signal;
  screen polling appears solely as the Step-4 instrument, which the plan licenses.
- **`wait_for_latching = true` is real, and the reasoning is better than the plan's.** The
  implementer correctly identified that the plan's second (gap) probe proves nothing — its signal
  fires while the second wait is already blocking — and derived `latching` from the first probe
  alone. The one-shot finding (`rewait_rc=1`, consumed only by a *successful* wait) is what actually
  makes Task 10's re-wait sound. Strongest work in the task.
- **Anchor claims verified empirically.** In `rc_screen`, bare `/remote-control` occurs 2x (echo +
  response) while `/remote-control is active` occurs 1x and is absent from the sent line `/rc`.
  `Session renamed to:` is present in `rename_screen`, absent from `/rename task0-rename-probe`.

## The Step-4 matcher deviation was correctly classified

`grep -q "READY"` matched the echoed command line (the prompt text contains `READY`), yielding a
fabricated 2s. Fixing it to `grep -qE '^READY[[:space:]]*$'` is a plan-*instrument* defect corrected
with primary evidence — not a contract-shape contradiction, so it did not trigger the STOP rule. It
made the data more conservative, and `default_seconds` is unaffected because the 60s floor dominates.

## Advisory notes (non-blocking; nothing here gates Task 1)

- `[ADVISORY] [EXTRA]` Extra fixture keys (`ref_resolution_scoping`, `trust_dialog_screen`, the two
  `*_no_workspace_ctx` negatives) — **justified, not scope creep.** The File Map explicitly asks for
  negative shapes, and the scoping discovery refutes a premise the workspace-fallback path depends
  on. Checked for a stale green test: `test_spawn_handoff.py`, `spawn_handoff_helpers.py` and
  `spawn-handoff-session.sh` contain ZERO references to `rename-tab`/`close-surface`/`--surface` —
  the v1 suite is entirely the `new-workspace` path, so no existing test asserts the refuted form.
- `[ADVISORY] [MISUNDERSTANDING]` Reproducibility gap in `argv`: four keys use placeholders rather
  than the executed string (`rename_tab.argv`, `close_surface.argv`, `wait_for.argv`,
  `workspace_create.argv` with unexpanded `$HOME`). Step 3 said "verbatim — no hand-editing";
  Deviation 3 discloses the `--workspace` addition but not the substitution. Load-bearing `stdout`
  values are verbatim and mutually consistent → documentation fidelity, not a data concern.
- `[ADVISORY] [MISUNDERSTANDING]` Thin provenance on the `/rc` capture: no workspace/surface ref
  recorded, and the trust modal must have been dismissed to reach the booted session — an
  intervening manual step neither fixture nor report states. Anchors unaffected.
- `[ADVISORY]` Hygiene, not a secret: `session_01HRLuW8KmevEP7Seqmu4chK` (a claude.ai
  remote-control link) is committed inside `rc_screen`/`rename_screen`. Account-gated, not a
  credential; worth redacting if these values are touched again.
- `[ADVISORY]` **Forward note for Module 3:** `read_screen_cold.stdout` is `""` with the error on
  `stderr`, so the plan test's first disjunct is dead and the assertion passes via `exit != 0`.
  Diagnosis code must read `stderr` or the exit code, never grep `stdout` for `internal_error`.
- `[ADVISORY]` Plan gaps the implementer copied faithfully (NOT implementer defects): the Step-7
  tests do not assert `close_surface`'s wrong-ref property, nor pin `rename_screen` /
  `send_after_rc_landed`. Route to the Module 3/4 test matrix.

## Report completeness

All required sections present and substantive. Not REPORT_INCOMPLETE. `deviations.md` carries 10
dispositioned Task-0 rows, including two `Pending — Module 3` items the controller must not lose.
