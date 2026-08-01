---
schema_version: 1
task_id: 0
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "tests/unit/fixtures/spawn-handoff/cmux-verb-shapes.json"
    description: "Live-captured per-verb stdout/stderr/exit for 10 verbs + 2 negative shapes, the three audit-ordered probe results (A1/A2/A3a), and two bonus findings (ref-resolution scoping, trust-dialog screen)"
  - path: "tests/unit/fixtures/spawn-handoff/cold-start-timing.json"
    description: "5 measured cold-start runs + derived default_seconds, with the measurement-method deviation recorded in-fixture"
  - path: "tests/unit/test_spawn_handoff_v2.py"
    description: "New sibling test file; Task 0 fixture-contract section only (3 tests), verbatim per plan Step 7"
tests:
  written: 3
  passing: 3
  command: ".venv/bin/python3 -m pytest tests/unit/test_spawn_handoff_v2.py -v"
  result: PASS
contract_compliance:
  - constraint: "Per-verb OK parsing — never reuse a generic field-2 parser"
    status: compliant
    detail: "All four pinned shapes CONFIRMED verbatim. Additionally found an UNDOCUMENTED precondition: rename-tab/close-surface need --workspace cross-workspace."
  - constraint: "read-screen on a never-driven surface errors (internal_error)"
    status: compliant
    detail: "Error: internal_error: Failed to read terminal text, exit 1, on stderr (not stdout)"
  - constraint: "A received cmux wait-for token is the ONLY exit-0 path"
    status: compliant
    detail: "Round-trip proven (rc=0, stdout OK). Latching TRUE + one-shot consumption make Task 10's re-wait sound."
  - constraint: "Measurement method pinned; shipped default = measured p95 x 2"
    status: partial
    detail: "Method followed except the matcher, which was defective (matched the command echo). Fixed and reported as a deviation. Floor dominated: max(60, 2x11)=60."
  - constraint: "Screen reading is diagnosis only, never the readiness signal"
    status: compliant
    detail: "Polling used only as the Step-4 measurement instrument, as the plan licenses. No production signal produced by this task."
---

## Implementation Summary
Captured all ten cmux verb shapes live against `cmux 0.64.20 (100) [14e3400b9]`, ran the three
audit-ordered probes (A1/A2/A3a), measured five true-cold-start runs, and seeded the fixture-contract
test section. All seven `task0-*` workspaces were deleted; `cmux workspace list` shows zero residual.
Full unit suite: 638 passed (635 + my 3), no regressions. Committed as `48608fb`.

## Measured Results

- **Runs:** `[11, 10, 11, 8, 8]` seconds, no timeouts. p95 (= max of 5) = **11s**. Derivation:
  `max(60, 2 × 11) = max(60, 22) = 60`, rounded up to nearest 10 = **`default_seconds = 60`** (int).
  - **The measurement did not determine the default — the 60s floor dominated.** The samples
    establish ~5.5× headroom, not the value. Task 9's import assertion will pin `60`; its provenance
    comment should say "spec floor; Task 0 measured 8–11s cold start" rather than implying 60 was
    measured.
  - **Caveat that matters: the timed runs used `-p` headless mode, which is NOT the boot path
    production uses** (see the trust-dialog finding below).

- **`surface_uuid_source`: AVAILABLE.** The parent *can* learn the child's UUID.
  - Recommended: `cmux identify --json --id-format both --workspace <ws> --surface <ref>` → key path
    **`caller.surface_id`** → e.g. `FAA9AA87-BB59-44A5-B33D-843764088D12` for `surface:77`. One verb,
    one key, no row matching.
  - Alternate: `cmux list-pane-surfaces --workspace <ws> --id-format both` (field 2 of the matching row).
  - `--id-format` is documented in **neither** command's `--help` — the CLAUDE.md "`--help` is not a
    manifest" gotcha, reproduced live. Also `tab_id == surface_id` (same UUID).

- **`wait_for_latching`: TRUE.** A token signaled with `-S`, then left with **no waiter alive for 3s**,
  was still consumed by a later wait (`latch_rc=0`). **Task 10's two-call re-wait is sound as designed.**
  Additionally `rewait_rc=1` — the latch is *one-shot*, consumed by the first **successful** wait; a
  first wait that *timed out* cannot have consumed the token, which is precisely what makes the re-wait
  safe. The plan's second (gap) probe corroborates nothing: its signal fires at t≈2s while the second
  wait was already blocking, so `second_rc=0` only proves a live waiter receives a signal. `latching`
  is derived from the first probe alone; the caveat is recorded in the fixture's
  `transcript`/`gap_probe_caveat`.

- **`rc_confirmation_screen`:**
  - **Recommended Task 11 anchor for `/rc`: `/remote-control is active`.** The sent line is literally
    `/rc` (3 chars), so no echo can contain it. Critically, bare `/remote-control` is **not** safe —
    the composer *expands* the alias, so `❯ /remote-control` appears as the submitted-command line;
    `/remote-control` matches 2 lines, `/remote-control is active` matches exactly 1 (the response region).
  - **Bonus — the same defeat applies to `/rename`, and I captured its fix.** The naive anchor (the
    title text) matched **3 lines including the command echo** — the exact defeat the spec records.
    **Use `Session renamed to:`** (matches exactly 1 line; cannot appear in the sent line
    `/rename <title>`).
  - **`send_after_rc_landed`: TRUE** — operator addendum #3 **did not reproduce at N=1**. The `/rename`
    sent *after* `/rc` was active landed and was confirmed. This fails to replicate the hazard once; it
    does not falsify it (the addendum was itself N=1).

- **NEW, unplanned finding — the directory-trust modal is a live handshake-failure mode.** An
  *interactive* `claude-picker` launch into an untrusted `--working-directory` (`$HOME`) raised the
  trust modal and **sat there — never reaching SessionStart, therefore never signaling the token.**
  That yields `handshake=timeout` + a consumed hop on a session that would have worked with one
  keystroke. The spec's design holds (`diagnosis=trust-dialog`, instructions steer to the existing
  tab), but **Module 3 should consider preflighting trust state for the target worktree path**, since a
  fresh worktree is exactly the untrusted-path case. Verbatim screen and two anchors
  (`Quick safety check: Is this a project you created or`, `1. Yes, I trust this folder`) captured into
  the fixture as `trust_dialog_screen`.

## Source Files Read
- `docs/imp-plans/2026-07-30-cmux-spawn-v2/spec-distilled.md` — Contract Facts; the "screen reading is
  never a success signal" rule and the "shell echo defeating composer verify" precedent, which is what
  let me recognize the Step-4 matcher defect immediately.
- `docs/imp-plans/2026-07-30-cmux-spawn-v2/module-1-contracts-spikes.md` — the authoritative task text;
  confirmed the prompt matched it.
- `docs/process-improvement-findings/2026-07-28-cmux-capability-usage-matrix.md` §4/§4.1/§4.2 — prior
  per-verb shapes (all confirmed); §4.1's `rename-tab --surface surface:46` success was in the
  *caller's* workspace, which is why the scoping trap was never seen before.
- `tests/unit/test_spawn_handoff.py`, `tests/unit/spawn_handoff_helpers.py` — house style (module-level
  `FIX` constant, plain pytest functions, WHY-docstrings). Not modified.
- `/Users/araymond/.local/bin/claude-picker` — verified `--non-interactive`/`--pick-version` exist
  (`--help` is not a flag; it opens the interactive menu).

## CLAUDE.md Files Read
- Repo root `CLAUDE.md` — "cmux Auto-Spawn Handoff" (workspace = sidebar / surface = top tab; `--help`
  is not a complete enumeration; cite constructs not line numbers), "Hook Development Gotchas" (never
  pipe a producer into `grep -q` under pipefail — no pipefail added to the poll loop), "Testing"
  (`.venv/bin/python3 -m pytest`). No CLAUDE.md exists under `tests/unit/`.

## Contract Verification

1. **`rename-tab` field 2** — **CONFIRMED**: `OK action=rename tab=tab:77 workspace=workspace:29`
   (exit 0). Field 2 is `action=rename`, not a ref.
2. **`close-surface` returns a plausible WRONG ref** — **CONFIRMED**: closing `surface:77` returned
   `OK surface:80 workspace:29` (exit 0). `surface:80` did not exist; only `surface:76` remained.
3. **Cold `read-screen` errors** — **CONFIRMED**: `Error: internal_error: Failed to read terminal text`
   (exit 1). Note it lands on **stderr**, not stdout.
4. **`new-surface` shape** — **CONFIRMED**: `OK surface:77 pane:29 workspace:29` (exit 0).
5. **`workspace create` shape** — **CONFIRMED**: `OK workspace:29` (exit 0).

**No pinned shape was contradicted.** But one **additional, undocumented precondition** was discovered —
the most valuable output of this task, and a live bug in the planned fallback path:

> **`rename-tab` and `close-surface` resolve surface/tab refs *within the caller's workspace* unless
> `--workspace` is passed**, failing `not_found: Tab not found` / `not_found: Surface not found`
> (exit 1) otherwise. `send`, `send-key` and `read-screen` resolve cross-workspace with a bare
> `--surface` (all three verified directly against `surface:77` in the non-caller `workspace:29`, not
> inferred).
>
> Four data points: cross-workspace bare rename → FAIL; cross-workspace + `--workspace` → OK;
> caller-workspace bare → OK; and warmth is irrelevant (bare rename failed identically cold and warm,
> so it is ref scoping, not lazy terminal instantiation).
>
> **Impact: this breaks the workspace-fallback path**, where the successor surface is by definition not
> in the caller's workspace. **Module 3 must always pass `--workspace` to `rename-tab` and
> `close-surface`.** Neither the plan, the spec, nor the capability matrix caught this — §4.1's success
> was in the caller's own workspace. Both failures are committed as negative fixture keys
> (`rename_tab_no_workspace_ctx`, `close_surface_no_workspace_ctx`).

## Deviations from Plan

1. **Step 4 matcher was defective; I fixed it.** The plan's `grep -q "READY"` matches the **echoed
   command line** — the prompt `-p 'Reply with exactly READY'` literally contains `READY`. Run 1
   reported **2s** (shell echo latency), not cold start. Evidence: the finished screen had **3**
   `READY` matches — lines 1 and 3 are echoes, line 7 is Claude's answer. Shipping that would have
   derived `default_seconds` from a fabricated 2s. Fixed to the line-anchored
   `grep -qE '^READY[[:space:]]*$'`, validated against the real screen (matches the answer, rejects the
   echo-only region). **Instrument, prompt, fresh-surface protocol and overestimate direction are
   unchanged.** Recorded in-fixture as `method_deviation`. Judged a probe defect already diagnosed with
   primary evidence rather than a contract contradiction warranting a halt — flagged for controller
   confirmation.
2. **stdout and stderr recorded as separate fixture keys** (the plan merged some with `2>&1`). No verb
   wrote error text to stdout, so merging would have conflated streams. The `read_screen_cold`
   assertion still passes via its `exit != 0` disjunct.
3. **`rename_tab` / `close_surface` argv include `--workspace`** — the plan's bare-flag forms *fail*;
   the successful shapes are recorded under the canonical keys and the plan's exact forms preserved as
   negative keys.
4. **One extra transient surface in the caller's own workspace** (`task0-ctx-probe`), created solely to
   isolate caller-vs-cross-workspace scoping, closed within the same call. Only work outside a
   `task0-*` workspace.
5. **Extra fixture keys added** beyond the specified schema: `ref_resolution_scoping` and
   `trust_dialog_screen` (both purely additive).

## Self-Review Findings
- Every fixture value is read from a capture file by a generator script; none was hand-typed. Screens
  with ANSI/box-drawing/embedded newlines went through `json.dump`, so values are byte-exact.
- `default_seconds` verified `int` (test asserts `isinstance`); arithmetic recomputed in code.
- Cleanup verified twice: `grep -c 'task0-'` → 0; the user's five original workspaces intact.
- No scratch files reached the repo — working files stayed in the session scratchpad; `git add` used
  explicit paths only. No `git stash`, no `git add -A`, `.venv` untouched.

## Concerns
1. **The `rename-tab`/`close-surface` workspace-scoping trap** — Module 3's fallback path will fail
   without `--workspace`. Highest-value item to carry forward.
2. **The trust modal blocks the token handshake** on an untrusted worktree path (detailed above).
   Recommend Module 3 consider a trust preflight. Did **not** re-run timing against an interactive
   launch — that is a scope expansion needing controller authorization, and the modal makes it
   unmeasurable without a keystroke anyway.
3. **"No warm claude process anywhere in the run" is unsatisfiable literally** — `pgrep` shows several,
   including the controller session. Interpreted as: no pre-booted claude in the *measured* surface;
   each run boots cold in a fresh workspace + surface. Recorded in-fixture.
4. **`send_after_rc_landed: true` is N=1** — it fails to replicate the operator's N=1 addendum; it does
   not disprove it.

---

## Controller verification (independent of the report's claims)

- Commit `48608fb` contains exactly the three specified files (219 insertions), nothing else.
- `gen_fixtures.py` (the generator) is **not** in the repo and not tracked — it stayed in the session
  scratchpad, as claimed. (Pyright diagnostics surfaced against the scratchpad copy, not a repo file.)
- `cmux list-workspaces` → **zero** `task0-*` entries; cleanup confirmed.
- Full unit suite re-run by the controller: **638 passed** in 150s — matches the claimed 635 baseline
  + 3 new, no regressions.
- Fixture values spot-checked directly: `runs_seconds [11,10,11,8,8]`, `default_seconds 60` (int),
  `surface_uuid_source.available true`, `wait_for_latching.latching true`,
  `send_after_rc_landed true`, and both negative scoping keys present with `exit 1`.
