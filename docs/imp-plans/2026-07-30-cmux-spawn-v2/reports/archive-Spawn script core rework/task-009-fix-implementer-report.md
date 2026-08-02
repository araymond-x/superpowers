---
schema_version: 1
task_id: 9
status: DONE_WITH_CONCERNS
files_changed:
  - path: skills/subagent-driven-development/scripts/spawn-handoff-session.sh
    description: "M2 — comment marking the fallback precondition as a deliberately retained, currently-tautological belt-and-braces guard. Comment-only; no behavior change."
  - path: tests/unit/spawn_handoff_helpers.py
    description: "Two new env knobs on cmux_v2_stub()'s list-pane-surfaces verb (CMUX_LIST_SURFACES_NO_REF, CMUX_LIST_SURFACES_TWO_ROWS), both guarded before the default printf so the default output is byte-identical."
  - path: tests/unit/test_spawn_handoff_v2.py
    description: "I2 shq-quoting pin; I3 fallback ref-shape refusal; M1 selected-row-vs-first-row; M3 timeout-record suffix fields; M4 the rename-tab test merged to cover both topologies (sibling removed)."
  - path: tests/unit/test_spawn_handoff_hardening.py
    description: "I1 — vacuous `assert _did_not_spawn.__module__` replaced by a delegation pin; the verb-tuple restatement (M5) annotated as a deliberate change-detector."
tests:
  written: 5
  passing: 5
  command: '.venv/bin/python3 -m pytest tests/unit/ -p no:cacheprovider -k "forwarded_knob_values_are_shell_quoted or fallback_refuses_when_no_surface_ref or selected_row_wins_over or timeout_record_keeps_its or delegates_to_the_shared_helper"'
  result: PASS
contract_compliance:
  - constraint: "Write scope limited to the six listed paths"
    status: compliant
    detail: "Four of the six touched; _handoff_support.py, test_handoff_support.py, BACKLOG.md, plan/module files and tests/integration/sdd-e2e-test.sh untouched (git status confirms)."
  - constraint: "I2 — shq on forwarded knob values gets a non-vacuous pin"
    status: compliant
    detail: "test_forwarded_knob_values_are_shell_quoted asserts the quoted form present AND the bare form absent, against the rendered send payload. Mutation-proven."
  - constraint: "I1 — delegation pinned, not provenance"
    status: compliant
    detail: "test_did_not_spawn_delegates_to_the_shared_helper patches the TEST module's `did_not_spawn` to a sentinel. RED under the re-spelling drift; the other 13 stay green."
  - constraint: "I3 — fixed with a stub knob, not another assertion"
    status: compliant
    detail: "CMUX_LIST_SURFACES_NO_REF makes list-pane-surfaces yield zero surface tokens; the gate becomes reachable and mutation-killable."
  - constraint: "I3 — refusal pinned by more than a bare returncode == 3"
    status: partial
    detail: "No stderr message is unique to this refusal (both shape checks return 1 silently), so the pin is an evidence COMBINATION rather than a message. See Deviations."
  - constraint: "M1 — two-row shape added as a knob, default stub output unchanged"
    status: compliant
    detail: "Knob-gated; the three spawn files stayed at 139 passing after the knobs landed and before any test was added."
  - constraint: "M3 — BUDGET_FLAG pinned on the timeout record; TOPOLOGY_FIELD attempted"
    status: compliant
    detail: "Fallback + timeout proved reachable; both fields are now MEASURED, each by its own mutation."
  - constraint: "M2 — fence-prescribed guard not silently deleted"
    status: compliant
    detail: "Structure retained; explanatory comment added, per the preferred option."
  - constraint: "M4 — resulting test name is TRUE of what it covers"
    status: compliant
    detail: "Merged into one test that runs both legs in per-leg tmp dirs; it now dies under M-M, which it previously survived."
  - constraint: "I4 not attempted"
    status: not_applicable
    detail: "Out of scope by instruction; no code, test, or backlog row added for it."
  - constraint: "Bash 3.2 floor; no set -u/-e/pipefail added"
    status: compliant
    detail: "Script change is a comment. `bash -n` passes."
  - constraint: "tests/integration/sdd-e2e-test.sh left red and untouched"
    status: compliant
    detail: "Not opened, not run, not reported as a failure."
---

## Summary

Fix round for the eight open findings on Task 9's adversarial quality review. The
code was already correct; seven of the eight were **missing pins** — guards no
test could distinguish from their absence — plus one comment-only clarity fix.

Five tests added, one deleted (merged), one vacuous assertion replaced, two stub
knobs added, one comment added to the script. **Every finding's fix is
mutation-proven: six mutations, each producing exactly one RED, and in each case
the RED was the new test.** Full suite 773 → 777 (5 added − 1 merged away).

I4 was not attempted, per instruction.

## Implementation Summary

**I2 — `shq` on forwarded knob values.** `test_forwarded_knob_values_are_shell_quoted`
forwards `SUPERPOWERS_CMUX_TITLE_FORMAT="a b; touch /tmp/PWNED"` — a genuinely
forwarded knob, free text by contract — and asserts against `_sent_text()`, the
only place `INLINE_ENV` appears (the `successor command:` stderr echo carries no
env prefix). The vacuity trap is handled by asserting the **pair**: the quoted
form `SUPERPOWERS_CMUX_TITLE_FORMAT='a b; touch /tmp/PWNED'` present AND the bare
`SUPERPOWERS_CMUX_TITLE_FORMAT=a b; touch /tmp/PWNED` absent. Presence alone
passes under both arms; the absence leg is what discriminates.

**I1 — vacuous claimed pin.** Deleted `assert _did_not_spawn.__module__` and added
`test_did_not_spawn_delegates_to_the_shared_helper`, using the reviewer's supplied
form. The patch target was verified before use: `_did_not_spawn` is defined in the
test module and resolves `did_not_spawn` from that module's globals at call time,
so patching the test module's attribute is what the call site actually reads.

**I3 — the fallback's ref-shape gate.** Fixed with a **stub knob**, per instruction:
`CMUX_LIST_SURFACES_NO_REF` makes `list-pane-surfaces` emit a row carrying no
`surface:N` token. A row rather than empty output, so the test also proves the awk
parser SKIPPED a non-matching token. Reaching the gate needs both conditions:
`CMUX_NEW_SURFACE_RC=1` to demote to the fallback, plus the unparseable listing.

**M1 — `[selected]` vs `END{print first}`.** `CMUX_LIST_SURFACES_TWO_ROWS` emits two
valid `surface:N` rows with the marker on the SECOND, so `first != selected`. Both
knobs are guarded before the default `printf`, leaving the default output
byte-identical — proven, not assumed (see Testing).

**M2 — tautological guard.** Kept the structure; added a comment stating it is
belt-and-braces, currently tautological under the present control flow, retained
deliberately and prescribed by the plan's fence. No deletion, no behavior change.

**M3 — timeout record's suffix fields.** `test_timeout_record_keeps_its_topology_and_budget_suffixes`
reaches fallback + timeout **together** (`CMUX_NEW_SURFACE_RC=1` + `CMUX_WAITFOR_RC=1`)
on an over-expected hop, pinning `topology=workspace-fallback` and
`budget=over-expected` on the one `handshake=timeout` record. **`TOPOLOGY_FIELD` is
therefore now MEASURED, not inferred** — the combination proved reachable.

**M4 — name overclaim.** Chose **option 2 (merge)**, because it makes the fence's
name true and thereby *closes* the undeclared departure rather than declaring a new
one. The merged test runs both legs in per-leg `tmp_path` subdirectories — every
harness path (`stubs/`, `home/`, `cmux.log` and its per-verb argv files) is keyed on
`tmp_path`, so the two runs get independent `.rename-tab.argv` files, which one
shared log could not tell apart. The sibling was deleted.

**M5 — restated verb tuple.** No separate action, as instructed; annotated as a
deliberate change-detector now that the delegation pin sits directly below it.

## Testing

**Baselines re-measured, not inherited.** Full suite **773 passed** (224.88s);
three spawn files **139 passed** (138.57s).

**Knobs landed first, in isolation:** after adding both stub knobs and before
adding any test, the three spawn files still reported **139 passed**. That
separates "a knob perturbed the default stub" from "a new test is wrong".

**After the fixes:** three spawn files **143 passed** (139 + 5 new − 1 merged away);
full suite **777 passed** (229.38s). The frontmatter `tests` block is scoped to the
five NEW tests (`written: 5 / passing: 5`, with a `-k` command that selects exactly
those five) because the model rejects `passing > written`; the suite-wide numbers are
these — 773 → 777.

Mutation discipline throughout: a Python helper that asserts the anchor matches
**exactly once** before replacing, keeps a byte copy for restore, and prints the
diff (read every time — no `perl`, so no `$`-interpolation accidents). Restore by
file copy + verification that the anchor is back; never `git checkout --`, never
`git stash`. `__pycache__` cleared before every run, `-p no:cacheprovider`, explicit
test paths, nothing in the background.

### Positive controls — six mutations, each exactly one RED

| Finding | Mutation | Result |
|---|---|---|
| I2 | `$(shq "$v")` → `$v` | **1 RED**, the new test; 142 green. Failure output showed the literal unquoted `; touch /tmp/PWNED` on the sent line. `test_sent_command_carries_inline_env` stayed GREEN — the finding, reproduced. |
| I1 | `_did_not_spawn` re-spells the verb tuple locally | **1 RED**, the new delegation test; **the other 13 GREEN** — the attribution proof. |
| I3 | ref-shape gate always passes (`case … in *) : ;; esac`) | **1 RED**, the new refusal test; 142 green. `test_fallback_is_attempted_exactly_once` unaffected (it fails on rc, not the gate). |
| M1 | `if(index($0,"[selected]"))` → `if(0)` | **1 RED**, the new two-row test; 142 green. `test_new_surface_failure_falls_back_to_workspace_once` stayed GREEN on the single-row stub — the masking, demonstrated. |
| M3 | drop `"$BUDGET_FLAG"` from the timeout printf | **1 RED**, the new M3 test; 142 green. |
| M3 | drop `"$TOPOLOGY_FIELD"` from the timeout printf | **1 RED**, the new M3 test; 142 green. |
| M4 | `rename-tab --workspace "$CMUX_WORKSPACE_ID"` (both paths) | **1 RED**, the merged test — which under its pre-merge form SURVIVED this exact mutation. |

Each mutation was restored by file copy and the restoration verified (anchor grep
and/or `git diff --stat` showing only the intended M2 comment). No `.mutbak` residue
remains. `bash -n` passes on the script. No ruff/black in this venv (`which ruff` →
not found); the two lines I introduced over 88 columns were hand-wrapped to match
surrounding style.

**Both directions run where specified** (I1, per instruction): RED under the
mutant, GREEN against landed code — the final 143/777 runs are the GREEN half.

`tests/integration/sdd-e2e-test.sh` was not touched, not run, and is not reported
as a failure — it stays red until Task 17 by instruction.

## Deviations from Plan

1. **M4 — fence at `module-3-spawn-script.md:398` specifies ONE rename-tab test; the
   shipped code had two.** Merging restores the fence's one-test shape and makes its
   prescribed name (`test_rename_tab_carries_workspace_on_both_topologies`) TRUE. This
   **closes** the previously-undeclared departure rather than creating a new one. The
   sibling `test_rename_tab_carries_workspace_on_the_fallback` is deleted; its
   coverage is preserved inside the merged test and mutation-proven (M-M kills it).

2. **M2 — the guard at `module-3-spawn-script.md:501` is retained, not deleted.**
   Preferred option taken; comment added. No deviation in behavior. Recorded because
   the finding invited deletion and I declined it.

3. **Two new stub knobs beyond the Step 1 fence's literal stub body**
   (`CMUX_LIST_SURFACES_NO_REF`, `CMUX_LIST_SURFACES_TWO_ROWS`). The fence shows a
   literal body; the shipped stub already carries knobs beyond it (`CMUX_SEND_FAIL_COUNT`,
   `CMUX_RENAME_RC`, `CMUX_NOTIFY_RC`, argv recording) which passed spec review, so this
   is consistent with the established shape — but declared rather than assumed. Both are
   guarded before the default `printf` and the unchanged-default claim is measured.

4. **I3's pin is an evidence combination, not a message.** The instruction asked for the
   refusal MESSAGE rather than a bare `returncode == 3`. I verified no such message
   exists: both `capture_cmux_ref`'s shape check and the fallback gate `return 1`
   silently, and `"spawn failed AFTER reservation"` is emitted on *every* post-reservation
   failure — including `test_fallback_is_attempted_exactly_once` — so it does not name
   this refusal. The pin used instead is strictly stronger than an rc: the workspace WAS
   created (`workspace create` in the log), the launch never happened (`rename-tab` and
   `send` both absent from the recorded verbs), the outcome names no surface
   (`surface == "-"`, the `${SPAWN_SURFACE_REF:--}` sentinel), plus topology and the
   consumed hop. Stated here rather than claiming a message pin I did not have.

## Self-Review Findings

- **Did I reproduce the vacuity trap I was warned about?** No. The I2 test's absence
  leg is what fails under the mutant; I confirmed the exact failure text shows the
  unquoted payload rather than merely a missing string.
- **Is any new assertion satisfiable without the guard it names?** Each was mutation-
  tested individually and each produced exactly one RED. A whole-file RED would have
  proved nothing about which assertion is load-bearing, so every run's pass count was
  read (142 green alongside each RED), not just the pass/fail line.
- **Known-remaining, deliberately not chased:** `END{if(!f)print first}` in the awk
  parser stays unpinned — both stub shapes carry a selected row, so the END branch is
  only reachable via a marker-less listing, which is a different shape again. Noted so
  a later reviewer does not file it as a new finding.
- **I4** (the double-spawn guard's unmeasured `cmux send` rc premise) is untouched and
  remains an accepted risk owned by merge; it needs live cmux.
- **Instrument checks:** every recursive sweep used `/usr/bin/grep` (the shell's `grep`
  is a `ugrep` wrapper that honors `.gitignore` and silently skips `.worktrees/`).
  Full-suite runs were given a 600s timeout — the ~230s suite would read as a failure
  under the 120s default.

## Source Files Read

- `docs/imp-plans/2026-07-30-cmux-spawn-v2/module-3-spawn-script.md` — Task 9 (Steps 1–3, the fences at the rename-tab test and the fallback guard)
- `docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/task-009-quality-review.md` — the eight findings, in full
- `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` — knob-forwarding loop, `shq`, `capture_cmux_ref`, `create_workspace_target`, `launch_into_target`, the spawn sequence and all three outcome records
- `tests/unit/spawn_handoff_helpers.py` — `cmux_v2_stub`, `SPAWN_VERBS`/`did_not_spawn`, `run_spawn`, `setup_worktree`
- `tests/unit/test_spawn_handoff_v2.py` — `run_spawn` shadow, `_reach_gate`, `_argv`/`_flag`/`_verbs`/`_outcome`/`_sent_text`, `TestSurfaceTopology`
- `tests/unit/test_spawn_handoff_hardening.py` — `_did_not_spawn` and its two positive controls
- `CLAUDE.md` (worktree root) — cmux auto-spawn section, hook/bash gotchas, testing conventions

## Concerns

1. **I3's pin is an evidence combination, not a message** (Deviation 4). It is
   strictly stronger than the `returncode == 3` the instruction warned against, but it
   is not the message pin the instruction asked for, because no such message exists.
   Adding a distinct stderr line for the unresolvable-ref refusal would be a behavior
   change to the script and is outside this fix round's remit — flagged rather than
   taken unilaterally.
2. **`END{if(!f)print first}` remains unpinned** — reachable only via a listing with
   surface rows but no `[selected]` marker, a third stub shape. Not added: no finding
   asked for it, and the reviewer's M1 framing is satisfied by the two-row shape.
   Recorded so it is not re-filed as a new finding.
3. **I4 is untouched** and remains an accepted risk owned by merge (needs live cmux).
