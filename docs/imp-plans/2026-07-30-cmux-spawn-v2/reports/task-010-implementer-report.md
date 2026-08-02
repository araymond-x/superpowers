---
schema_version: 1
task_id: 10
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/subagent-driven-development/scripts/spawn-handoff-session.sh"
    description: "Replaced Task 9's placeholder timeout tail with the real handshake: wait_for_token() (one bounded wait), diagnose_target() (enrichment only — never selects the exit code), the `if ! wait_for_token` + exactly-one-re-wait tail with a four-arm operator message case, and the handshake=ok success stanza relocated after the block. Anchor provenance labelled PER ANCHOR in three categories (Step 3b)."
  - path: "tests/unit/spawn_handoff_helpers.py"
    description: "Added the CMUX_READ_SCREEN_RC stub knob — the only way to isolate diagnose_target's rc disjunct from its internal_error disjunct — with the reason documented in the knob table."
  - path: "tests/unit/test_spawn_handoff_v2.py"
    description: "19 new tests: TestHandshakeFixtureProvenance (5 — byte-exact anti-drift pins for the three DERIVED fixtures, plus a synthetic-label pin and its positive control) and TestHandshake (14 — token-only-success, re-wait, all five diagnoses incl. three isolated `unreadable` disjunct cases, ordering, both live captures, notify/hop). Helpers _screen, _wait_for_lines, _timeout_ctx, _diagnose."
  - path: "tests/unit/fixtures/spawn-handoff/screens/trust-dialog.txt"
    description: "DERIVED byte-exact from cmux-verb-shapes.json trust_dialog_screen.screen (live capture)."
  - path: "tests/unit/fixtures/spawn-handoff/screens/banner.txt"
    description: "DERIVED byte-exact from rc_confirmation_screen.rc_screen (live capture of a running Claude session)."
  - path: "tests/unit/fixtures/spawn-handoff/screens/noise.txt"
    description: "DERIVED byte-exact from read_screen_warm.stdout (live capture of a plain shell surface). The plan called this one synthetic; a live capture of exactly its semantic was already in the fixture — declared deviation."
  - path: "tests/unit/fixtures/spawn-handoff/screens/picker-error.txt"
    description: "SYNTHETIC. Says so in the file: the anchor is an INVENTED hypothesis, with its falsifier stated."
  - path: "tests/unit/fixtures/spawn-handoff/screens/both-anchors.txt"
    description: "SYNTHETIC. Composes the two MEASURED anchors (trust + `shift+tab to cycle`) to pin grep ORDERING, which no capture can pin. Says so in the file."
  - path: "docs/imp-plans/2026-07-30-cmux-spawn-v2/deviations.md"
    description: "Rows 18 (trust preflight DECIDED — declined, measured), 165 (ROUTED to Task 13, single owner) and 271 (five inline log-readers DECIDED — declined, measured) flipped off Pending. Three new Task 10 deviation rows added."
tests:
  written: 19
  passing: 19
  command: ".venv/bin/python3 -m pytest tests/unit/ -q -p no:cacheprovider (FULL SUITE: 777 before -> 796 after, 0 failed; the 19 here are this task's new tests)"
  result: PASS
contract_compliance:
  - constraint: "A received token is the ONLY exit-0 path; diagnose_target NEVER selects the exit code"
    status: compliant
    detail: "diagnose_target is called only INSIDE the failed-re-wait branch, after exit 3 is already determined; it only chooses the operator message and the diagnosis= field. test_token_is_only_success drives a full banner with CMUX_WAITFOR_RC=1 and asserts exit 3, and test_token_success_exits_0_handshake_ok asserts `diagnosis` is absent from a success record."
  - constraint: "Bash >= 3.2; NO set -u / set -e / pipefail"
    status: compliant
    detail: "None introduced (grep -nE '^\\s*set -[ue]|pipefail' matches only three explanatory comments). shellcheck --severity=warning --external-sources exits 0. bash -n clean."
  - constraint: "Never pipe a producer into grep -q — use here-strings"
    status: compliant
    detail: "All four new greps use `<<< \"$screen\"`. The single `|| grep -qi` occurrence is a logical OR, not a pipe."
  - constraint: "Fallback fires ONLY before the launch command is accepted; after cmux send rc 0, NEVER spawn again"
    status: compliant
    detail: "The timeout tail creates no target and calls no spawn verb — it waits, diagnoses by read-screen, records, notifies and exits 3. Task 9's test_no_double_spawn_after_accepted_send (send rc 0 then CMUX_WAITFOR_RC=1) still passes."
  - constraint: "Reservation BEFORE spawn; a consumed hop stays consumed"
    status: compliant
    detail: "Untouched. test_timeout_notifies_and_keeps_hop asserts .handoff-hops == '1' on the timeout path."
  - constraint: "Exit codes stay 0/3/1"
    status: compliant
    detail: "The tail exits 3 on every diagnosis; the success stanza exits 0. No new exit code introduced."
  - constraint: "Task 0 fixtures (cmux-verb-shapes.json, cold-start-timing.json) are READ-ONLY source of truth"
    status: compliant
    detail: "Neither modified (absent from git status). All three derived screen fixtures are generated FROM cmux-verb-shapes.json and pinned back to it byte-for-byte."
  - constraint: "Write scope is six paths; _handoff_support.py, test_handoff_support.py, plan/module files and BACKLOG.md are read-only"
    status: compliant
    detail: "Changed: spawn-handoff-session.sh, spawn_handoff_helpers.py, test_spawn_handoff_v2.py, fixtures/spawn-handoff/screens/ (+ deviations.md, which Step 4 commands). test_spawn_handoff.py and test_spawn_handoff_hardening.py were in scope but needed no change and were not touched."
  - constraint: "tests/integration/sdd-e2e-test.sh is RED by design until Task 17 — do not touch or run"
    status: not_applicable
    detail: "Not touched, not run, not reported as a failure."
---

# Task 10 — wait-for handshake, re-wait, read-screen diagnosis

## Implementation Summary

Task 10 replaces Task 9's placeholder timeout tail with a bounded `wait-for` token
handshake, exactly one re-wait at the same duration, and `read-screen` diagnosis
enrichment that classifies *why* a handshake timed out — without ever letting that
classification touch the exit code.

Full unit suite: **777 before → 796 after, 0 failed**. Both numbers measured in this
session, not inherited. The delta is exactly the 19 tests added.

Every factual claim in the plan's `AMENDED` notes was re-measured against the frozen
capture before being built on, with positive and negative controls. All of them held.
Two plan claims did not survive measurement, and both are declared as deviations
below: the plan's inventory of which fixtures are synthetic, and the plan's prescribed
`unreadable` test pair, which could not pin the branch it guarded. A third, minor
fence departure is recorded alongside them.

### Implementation detail

**Step 1 — screen fixtures** (`tests/unit/fixtures/spawn-handoff/screens/`). Written
*programmatically* from `cmux-verb-shapes.json` with explicit `encoding="utf-8"` (the
captures are full of box-drawing characters and `❯`), never hand-authored and then
retro-fitted with an equality test:

| Fixture | Provenance | Source key |
|---|---|---|
| `trust-dialog.txt` | MEASURED | `trust_dialog_screen.screen` |
| `banner.txt` | MEASURED | `rc_confirmation_screen.rc_screen` |
| `noise.txt` | MEASURED | `read_screen_warm.stdout` (deviation — plan called it synthetic) |
| `picker-error.txt` | INVENTED | none — labelled in-file with its falsifier |
| `both-anchors.txt` | SYNTHETIC composite of two MEASURED anchors | labelled in-file |

The three derived files carry byte-exact equality pins back to the capture. No
`.strip()` anywhere in those comparisons — that would convert a byte-exact anti-drift
pin into a fuzzy one, which is a dead pin wearing a live name.

**Step 2 — tests** (19 written; the pre-implementation run measured **13 failed, 62
passed** in this file — the 6 that were green from the start are the 5 fixture-
provenance pins, which test fixtures rather than the new code, plus
`test_token_success_exits_0_handshake_ok`, which pins Task 9's already-correct success
path). **Step 3 — implementation**: `wait_for_token()` and `diagnose_target()`
added beside the other spawn functions; the tail rewritten to
`if ! wait_for_token → message → if ! wait_for_token → diagnose → record → notify →
case → exit 3`, with the `handshake=ok` stanza relocated below the block.

**Step 3b — anchor provenance, per anchor and in three categories.** The `banner`
branch alone holds two anchors of different provenance, so a per-branch label would
have read MEASURED wholesale and silently laundered the inference:

- `unreadable` — **both** disjuncts MEASURED from `read_screen_cold` (`exit 1`;
  stderr `Error: internal_error: Failed to read terminal text`).
- `trust-dialog` — both anchors MEASURED, verbatim from
  `trust_dialog_screen.candidate_anchors`.
- `picker-error` — both anchors **INVENTED**, with the falsifier stated: no capture
  exists, and if the real wording differs this branch degrades to `none`, which is
  honest because it never misreports a *different* diagnosis.
- `banner` — `shift+tab to cycle` is **MEASURED** (present in both live
  running-session captures, absent from the trust capture), scoped honestly in the
  comment: both captures carry the same session id and statusline, so n = **one**
  session captured twice, and it was a long-running interactive session rather than a
  freshly spawned successor. `esc to interrupt` is **INFERRED** — zero occurrences in
  the entire fixture, covering the busy state neither idle capture exercises.
  `claude code` stays REMOVED: measured to match only the trust screen.

## Testing

Command: `.venv/bin/python3 -m pytest tests/unit/ -q -p no:cacheprovider`
Before: **777 passed**. After: **796 passed**, 0 failed, 1 pre-existing warning.

Measurements, each with a positive control (a pattern that must match) and a negative
control (a string that cannot be present), run against the frozen capture:

| Pattern | trust screen | rc_screen | rename_screen | warm shell | whole fixture |
|---|---|---|---|---|---|
| trust anchors | 2 | 0 | 0 | 0 | 4 |
| `claude-picker: (error\|fatal)\|no matching version` | 0 | 0 | 0 | 0 | **0** |
| `shift+tab to cycle` | 0 | 1 | 1 | 0 | 2 |
| `esc to interrupt` | 0 | 0 | 0 | 0 | **0** |
| `claude code` (removed) | 2 | 0 | 0 | 0 | 2 |

Every plan claim held. Controls: `trust` appears 2× in the trust screen and `Opus` 2×
in `rc_screen` (instrument works); `zzq-not-present` appears 0× (instrument can also
return zero honestly).

**Five mutation positive controls, all RED, all restored by file copy with `diff -q`
verified identical** (never `git checkout --`, never `git stash`). Each anchor was
asserted to occur exactly once before mutating:

1. Re-wait duration — mutated the **second call site**, not `wait_for_token` (editing
   the function changes *both* waits, the test stays green, and the SURVIVED reading
   manufactures a false finding). `test_timeout_rewaits_once_same_duration` → RED.
2. Grep ordering — physically swapped the trust and banner blocks.
   `test_ordering_trust_beats_banner_on_a_both_anchors_screen` → RED.
3. Deleted the rc disjunct (`[ $rc -ne 0 ] ||`).
   `test_diagnosis_unreadable_on_nonzero_rc_with_clean_output` → RED.
   And symmetrically, deleted the grep disjunct (leaving `if [ $rc -ne 0 ]`):
   `test_diagnosis_unreadable_on_internal_error_text_with_rc_zero` → RED, while case
   (a) correctly stayed green (it is driven by the rc, which survives that mutation).
   Both disjuncts are therefore independently pinned — the twin of the hole I found in
   the plan's own pair, checked rather than assumed.
4. Reverted the banner pattern to the pre-fix `claude code|esc to interrupt`.
   `test_both_live_session_captures_diagnose_banner` → RED.

The re-wait test parses **both** `wait-for` lines out of the flat `cmux.log` rather
than using `_flag(_argv(...), "--timeout")`. The `.argv` sidecar is
`printf '%s\n' "$@"` — one line per *token*, appended across both calls with no
separator — and `_flag` resolves only the first occurrence, so that spelling would
have asserted one value once and left the re-wait half vacuous.

`tests/integration/sdd-e2e-test.sh` was not touched and not run (RED by design until
Task 17).

## Source Files Read

- `docs/imp-plans/2026-07-30-cmux-spawn-v2/task-010-dispatch-prompt.md` — the dispatch.
- `docs/imp-plans/2026-07-30-cmux-spawn-v2/module-3-spawn-script.md` — the whole of
  Task 10 (ROUTING note, Steps 1/2/3/3b/4(a)-(e), every `AMENDED 2026-08-02` note),
  the module header (Contract Constraints, File Map, Write-Scope Partitioning), Tasks
  8-9 for the landed state, and the Module 3 Acceptance Criteria.
- `CLAUDE.md` (worktree root). No subdirectory `CLAUDE.md` exists — verified with
  `find . -name CLAUDE.md -not -path "./.git/*"`, which returned exactly one path.
- `tests/unit/fixtures/spawn-handoff/cmux-verb-shapes.json` (READ-ONLY) — the binding
  capture: `trust_dialog_screen`, `rc_confirmation_screen`, `read_screen_cold`,
  `read_screen_warm`. And `cold-start-timing.json` (READ-ONLY).
- `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` — the spawn
  sequence, `print_manual_instructions`, the Task 9 handshake stanza it replaces.
- `tests/unit/spawn_handoff_helpers.py`, `tests/unit/test_spawn_handoff_v2.py`, and
  the inline log-reader sites in `tests/unit/test_spawn_handoff.py` (read only —
  that file was not modified).
- `docs/imp-plans/2026-07-30-cmux-spawn-v2/deviations.md` rows 18, 165, 271.
- `docs/process-improvement-findings/2026-07-29-handoff-hardening-recommendations.md`
  §1-2 — the primary source for the trust-preflight decision, read rather than
  summarized from the plan.


## Deviations from Plan

Three, all recorded as rows in `deviations.md`.

1. **`noise.txt` is DERIVED from a live capture, not synthetic.** The plan's
   inventory line says the remaining three fixtures are synthetic. But
   `read_screen_warm` is a live capture (`exit 0`) of a plain shell surface — exactly
   `noise.txt`'s semantic — and it scores 0 against every pattern in the ladder,
   including `internal_error`. So it diagnoses `none` from measured reality instead of
   from text authored to agree with the code. It gets the same byte-exact anti-drift
   pin as its two siblings. This is the same defect class as BLOCKER 1 and BLOCKER A
   showing up a third time: a capture was sitting in the fixture while the plan
   asserted none existed.
2. **Added the `CMUX_READ_SCREEN_RC` stub knob**, because the plan's two prescribed
   `unreadable` cases cannot isolate the rc disjunct — see Self-Review.
3. **`diagnose_target` reads `$?` into a named `rc`** rather than the fence's bare
   `if [ $? -ne 0 ]`. Behaviourally identical here; recorded because it departs from a
   prescribed fence, and because `$?` is destroyed by any statement later inserted
   between the assignment and the test.

## Self-Review Findings

**The seven obligations, with the evidence actually gathered.**

1. **Wait-timeout import assertion — VERIFIED, not re-added.** It is already landed at
   `tests/unit/test_spawn_handoff_v2.py:1262–1275`
   (`test_wait_timeout_default_matches_the_frozen_fixture`), inside
   `TestSurfaceTopology`. I ran that node id alone: **1 passed in 0.02s**. Its path
   resolves (`parent.parent.parent`), it loads `cold-start-timing.json`
   (`default_seconds = 60`), and the script side is a column-0
   `SPAWN_WAIT_TIMEOUT_DEFAULT=60` at `spawn-handoff-session.sh:54`. Adding the
   plan's shape would have shipped a duplicate. Not added.
2. **Step 4(a) full suite, re-measured.** 777 → 796. I did not inherit the plan's 777;
   I ran the suite before touching anything and got 777 independently.
3. **Step 4(b) trust preflight — DECIDED: declined, with measurement.** Row 18 flipped.
   I read the primary source (`2026-07-29-handoff-hardening-recommendations.md` §1)
   rather than reasoning from the plan's summary. Measured on this machine:
   `~/.claude.json` tracks **36** project paths (30 accepted, 6 not) and **zero** of
   them is a `.worktrees/` path, while `~/.claude/projects/` holds session directories
   for **13** distinct worktrees — 27 session files for *this* worktree alone. So the
   exact-path `hasTrustDialogAccepted` preflight that source derives would return
   `untrusted` for **13/13** worktrees that demonstrably ran Claude sessions: a 100%
   false-positive rate on the exact population this feature targets. Building it would
   turn a rare real hazard into a universal spurious refusal. **This is explicitly not
   the forbidden argument** — I do not claim `$WORKTREE_ROOT` is trusted because the
   parent runs there. What is measured is that the *proposed instrument* misclassifies
   the target population. The coherent explanation is ancestor inheritance
   (`/Users/araymond` is tracked `false` and *is* Task 0's captured modal, having no
   trusted ancestor), but I did not exercise Claude's resolution algorithm, so that
   remains INFERRED and the decline does not rest on it. What would have to be true to
   build it: a preflight would need the actual trust-*resolution* algorithm, not the
   file's exact-path keys. Falsifier: launch into a freshly created, never-seen
   worktree under a trusted ancestor and observe the modal. Task 10 ships the
   detection half regardless — `diagnosis=trust-dialog` names the hazard and steers to
   the tab instead of to a double-spawn.
4. **Step 4(c) five inline log-readers — DECIDED: declined, with measurement.** Row 271
   flipped. Count re-verified at **5**, all in `test_spawn_handoff.py` (686, 840, 867,
   957, 996). Positive control: the shared helper is used 8× in that same file and the
   other two spawn test files hold 0 inline readers, so the instrument sees both
   shapes. The decisive finding is one the row did not state: **two of the five carry
   NEGATIVE assertions** — `assert "--non-interactive" not in logged` (from the read
   at 840) and `assert "{workspace}" not in (tmp_path / "cmux.log").read_text()` (996).
   For a negative assertion the helper's `return ""`-on-missing is strictly
   **fail-open**: a run where the stub never executed would PASS. That is precisely the
   B1 shape `did_not_spawn` was created to close, so swapping these would reintroduce
   it in a new spelling. The other three are positive assertions where the inline raise
   is merely better diagnostics. Declined, and the row now says the inline shape is
   *correct* here rather than merely tolerated.
5. **Step 3b anchor provenance — recorded per anchor, three categories.** See
   Implementation above; the labels are code comments beside each pattern.
6. **Step 4(d) routing of row 165 — RESOLVED to a single owner: Task 13.** The
   discriminator: naming an orphaned workspace requires a **new field** in the outcome
   record, i.e. a field-grammar change shared with Module 4's e2e assertions — not
   diagnosis enrichment. Task 10 touches only the *timeout* record; both halves of the
   orphan finding live on the `handshake=none` spawn-failed record and on an exit-0
   success record, neither of which Task 10 edits. Task 13 is "Checked outcome writes
   (N63)", which edits every outcome write site and owns the e2e assertions. The
   disposition now names one task; "Task 10/13" is gone, because a row naming two is
   owned by nobody.
7. **The two vacuity traps inside Step 2's fence** — both honoured. The `_flag`/`_argv`
   trap is handled by `_wait_for_lines` (documented in its docstring). The two-disjunct
   `unreadable` condition is split into three tests, and the plan's own pair turned out
   to be insufficient: the stub's natural failure emits `internal_error` **and** exits
   1, and the script reads with `2>&1`, so the plan's case (a) fires *both* disjuncts
   and case (b) isolates only the second. **Neither reaches the rc disjunct**, so
   deleting `[ $rc -ne 0 ] ||` left every prescribed assertion green — it would have
   shipped unpinned inside tests that read as its guard. I added the
   `CMUX_READ_SCREEN_RC` knob (in-scope) and a third case that drives `noise.txt`
   (which diagnoses `none` at rc 0) at rc 3; mutation control 3 above confirms it goes
   RED when the disjunct is removed.

**Instrument discipline.** Every recursive search used `/usr/bin/grep`, never the
shell's `ugrep`-wrapping function that honours `.gitignore` and would silently skip
`.worktrees/`. Every negative claim in this report is backed by a positive control run
in the same command. No `git add -A`, no `git stash`, no `git checkout --` at any
point; the worktree `.venv` symlink was not touched.

**Not claimed.** The `banner` anchor's generalization to "any running Claude session"
is inference, not measurement (n = one session, captured twice, and not a freshly
spawned successor) — stated as such in the code comment rather than laundered into the
MEASURED label. `picker-error` is invented and says so. The trust-inheritance model is
inferred and the decline does not rest on it. `diagnose_target` has never been run
against a live cmux surface; coverage is unit-level against frozen captures.

## Concerns

Status is `DONE_WITH_CONCERNS`. Nothing here blocks the task; each is a limit on the
evidence, stated so a reviewer does not have to rediscover it.

1. **The `banner` anchor rests on n = 1 session.** `shift+tab to cycle` is genuinely
   MEASURED, but both live captures carry the same session id and the same
   `bypass permissions` statusline, so they are one long-running interactive session
   captured twice — not a freshly spawned successor, which is the population this
   feature actually cares about. If a spawned successor's statusline differs, `banner`
   degrades to `none`: the operator still learns a spawn was attempted and is pointed
   at the surface, but loses the "attach and continue" steer. Recorded in the code
   comment rather than laundered into the label. Only a capture of a real spawned
   successor settles it.
2. **`esc to interrupt` is INFERRED and currently pins nothing.** Zero occurrences in
   the fixture; it covers the busy state neither idle capture exercises. It is carried
   because a busy successor is plausible, but no test drives it and no capture
   supports it.
3. **`picker-error` is INVENTED end to end.** Its failure mode is benign (it degrades
   to `none`, never to a *wrong* diagnosis), but the branch is a hypothesis.
4. **`diagnose_target` has never run against a live cmux surface.** All coverage is
   unit-level against frozen captures through a stub. The live path is exercised for
   the first time whenever this ships — the same caveat Module 3 carries generally.
5. **Report section names.** The dispatch prescribes Summary / Implementation /
   Testing / Deviations from Plan / Self-Review; `validate-report.py` requires
   Implementation Summary / Source Files Read / Self-Review Findings / Deviations from
   Plan / Concerns. Per the dispatch's instruction I followed the validator and am
   declaring the departure here. `validate-report.py` now exits 0.

