# Partner review — Task 10 dispatch (`task-010-dispatch-prompt.md`)

**Reviewer:** controller partner, no prior session context.
**Date:** 2026-08-02
**Verdict:** see final line.

---

## Method

**Read in full:**
- `docs/imp-plans/2026-07-30-cmux-spawn-v2/task-010-dispatch-prompt.md` (all 92 lines)
- `module-3-spawn-script.md` — header (Contract Constraints L35, File Map L37-46, Write-Scope Partitioning L47-56), Task 9 Step 4 (L543-545), **Task 10 in full (L547-650)**, Module 3 Acceptance Criteria (L726-735)
- `deviations.md` — every non-`Accepted`/`Fixed` disposition row; rows 18, 60, 61, 80, 101, 119, 127, 164, **165**, 166, 214, 228, 230, **263**, **266**, 267, **271**, 275 read individually
- `spec-distilled.md` — L26, L37, L40-41, L61-63, L84-90, L117, L132
- `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` L45-60, L640-778
- `tests/unit/spawn_handoff_helpers.py` (all 332 lines, esp. `_CMUX_V2_STUB` L151-187)
- `tests/unit/test_spawn_handoff_v2.py` L52-92, L820-880, L1150-1311
- `tests/unit/fixtures/spawn-handoff/cmux-verb-shapes.json` (all keys enumerated; `trust_dialog_screen`, `rc_confirmation_screen`, `read_screen_warm`, `read_screen_cold`, `wait_for_latching` decoded in full), `cold-start-timing.json` (whole file)

**Ran (all sweeps via `/usr/bin/grep` or `find -print0 | xargs -0`, never the shell's ugrep wrapper):**

| Probe | Result |
|---|---|
| `diff` of module L35 Contract Constraints vs dispatch L21 (leading `> ` stripped) | **IDENTICAL**; positive control against a dummy file correctly reported "differ" |
| `pytest tests/unit/test_spawn_handoff_v2.py -k wait_timeout_default_matches -q` | **1 passed** |
| `pytest tests/unit/ -q --collect-only` | **777 tests collected** |
| `pytest` on the three spawn files | **143 passed in 144.33s** |
| `pytest tests/unit/ -q` (full suite) | **777 passed, 1 warning in 226.12s** — confirms both the 777 baseline and the dispatch's "~200-240s" timing |
| `/usr/bin/grep -nF 'cmux.log' tests/unit/test_spawn_handoff.py` | inline `(tmp_path / "cmux.log").read_text()` at **686, 840, 867, 957, 996 = exactly 5** (923/931 are `.log-at-spawn`/`.hops-at-spawn`, different files) |
| `find . -path ./.git -prune -o -type f -print0 \| xargs -0 /usr/bin/grep -l -i "do you trust the files"` | **one hit: `module-3-spawn-script.md` only.** Positive control on the same instrument with `"Quick safety check"` returned 3 files — instrument confirmed working |
| Python regex harness: each of the three `diagnose_target` fence patterns vs all four live screen captures in `cmux-verb-shapes.json`, with two must-match controls | see Finding 1 |

---

## Verified TRUE (the controller's claims that hold)

These are load-bearing: the BLOCKED below is not a reflex, it is what survived after everything checkable checked out.

1. **All four claimed plan amendments are real and correct.** Obligation 1 → `module-3-spawn-script.md:579` ("AMENDED 2026-08-02 … Task 9 PRE-EMPTED it and it is ALREADY LANDED"). Obligation 2 → `:644` Step 4(a). Obligation 3 → ROUTING note `:549` **and** Step 4(b) `:646` (both sites, so the routing prose now has a producing step). Obligation 4 → Step 4(c) `:648`. No claim-without-amendment.

2. **The "already landed" import assertion genuinely exists and passes.** `tests/unit/test_spawn_handoff_v2.py:1262-1275` — `test_wait_timeout_default_matches_the_frozen_fixture`, loading `cold-start-timing.json` at `:1265` and searching `r"^SPAWN_WAIT_TIMEOUT_DEFAULT=(\d+)$"` with `re.M` at `:1273`, asserting `int(m.group(1)) == d["default_seconds"]` at `:1275`. `import re` at `:13`, `FIX` at `:34`. Script side: `spawn-handoff-session.sh:54` `SPAWN_WAIT_TIMEOUT_DEFAULT=60` — **column 0, confirmed**, with the `deviations.md:22`-prescribed provenance comment verbatim at `:46-53`. The test passes standalone. The dispatch's instruction to VERIFY-not-re-add is correct; following the original plan wording would indeed have shipped a duplicate.

3. **Contract Constraints are verbatim, not paraphrased.** `diff` byte-identical, with a positive control proving `diff` would have reported a difference.

4. **The six writable paths are correct.** Task 10's Write-Scope row (`:53`) reads "same set", which resolves through Task 9's row (`:52`) — "first five above + `test_spawn_handoff_hardening.py` (B1)" — and Task 9's Step 4 (`:543`) spells the same resolution out explicitly as **SIX**. Dispatch L30-35 lists exactly those six, in the same order. The dispatch's READ-ONLY list is *stricter* than the table (it re-pins `_handoff_support.py` and `test_handoff_support.py`, correct per "returns to read-only after Task 8") — stricter is fine.

5. **777 is accurate**, and it is accurate as a *passing* count, not merely a collected one: `--collect-only` reports 777 collected and the full run reports **777 passed**. The "143" three-file baseline is also accurate (143 passed).

6. **"Five inline log-readers" is accurate** — exactly 5, at the lines listed above.

7. **Every one of Step 2's nine named tests IS producible from `cmux_v2_stub()`'s existing knobs.** Answering the question asked, plainly, in the negative: `CMUX_WAITFOR_RC` (`_CMUX_V2_STUB` L172, `wait-for) exit "${CMUX_WAITFOR_RC:-0}"`) drives success/timeout; `CMUX_SCREEN_FILE` (L173-174, `read-screen` cats the file / errors `internal_error` + rc 1) drives every diagnosis branch including the unset-→-`unreadable` case; the unconditional `echo "$@" >> "$CMUX_LOG"` (L157) makes the two-`wait-for`-lines assertion observable; `notify` (L175) is logged. **No test in Step 2 is untestable by construction.** No new knob is required.

---

## Findings

### BLOCKER 1 — Every screen anchor the Task 10 fence greps for is invented, and the frozen READ-ONLY fixture contradicts them. The dispatch quotes the tiebreaker rule and then loses to it.

**Where the obligation lives:** the Task 0 fixture `tests/unit/fixtures/spawn-handoff/cmux-verb-shapes.json`, cited by the dispatch itself at L25 as **"READ-ONLY source of truth… If a stub's shape disagrees with the frozen fixture, the fixture wins."** Also `deviations.md:18` — the row Task 10 must flip — which ends *"Screen + two anchors captured as `trust_dialog_screen`."*

**What the plan prescribes:**
- `module-3-spawn-script.md:553` — Step 1: `trust-dialog.txt` **"(contains `Do you trust the files in this folder?`)"**
- `:605` — `if grep -qi "do you trust the files" <<< "$screen"; then printf 'trust-dialog'`
- `:607` — `if grep -qiE "claude code|esc to interrupt" <<< "$screen"; then printf 'banner'`
- `:606` — `if grep -qiE "claude-picker: (error|fatal)|no matching version" … 'picker-error'`
- `:626` — the operator message quotes the same invented phrase back at the user: *"sitting on Claude's FOLDER-TRUST DIALOG (**'Do you trust the files in this folder?'**)"*

**What Task 0 actually measured.** `trust_dialog_screen` (`observed: true`, cmux 0.64.20, picker 2.1.220) contains **no such phrase**. Its own `candidate_anchors` are:

```
"Quick safety check: Is this a project you created or"
"1. Yes, I trust this folder"
```

I ran all three fence patterns against all four live captures (`trust_dialog_screen`, `rc_confirmation_screen.rc_screen`, `.rename_screen`, `read_screen_warm.stdout`), with two must-match controls:

```
TRUST fence  "do you trust the files"                        -> NO MATCH IN ANY LIVE CAPTURE
PICKER fence "claude-picker: (error|fatal)|no matching version" -> NO MATCH IN ANY LIVE CAPTURE
BANNER fence "claude code|esc to interrupt"                  -> ['trust_dialog_screen']     <-- the WRONG screen
[control] "trust this folder"                                -> ['trust_dialog_screen']     OK
[control] "/remote-control is active"                         -> ['rc_confirmation.rc_screen', 'rc_confirmation.rename_screen']  OK
```

Both controls fired, so the three NO-MATCH results are real absences, not a dead instrument.

**Why this is a blocker and not a nit — it fails in the compounding direction.** `diagnose_target` tests trust-dialog *before* banner. Against a real trust modal: the trust test misses (0 matches), execution falls through to the banner regex, which **does** match — because the only occurrence of "Claude Code" in any live capture is inside the trust dialog screen itself (`Launching Claude Code 2.1.220`, `Claude Code'll be able to read, edit…`). So a real trust dialog is classified **`diagnosis=banner`**, and the operator is told *"a Claude session IS visible… Attach to that tab and continue there"* (`:628`) instead of *"answer the folder-trust dialog"*. That is precisely the failure `deviations.md:18` was written to prevent and that Task 0 measured live — a consumed hop that one keystroke would have fixed. Symmetrically, a genuinely-running successor (both `rc_confirmation_screen` captures) matches **neither** banner anchor and lands on `diagnosis=none`.

And all of this ships **green**, because Step 1 tells the implementer to author `trust-dialog.txt` containing the invented phrase — a synthetic fixture built to match a detector built from memory. This is the identical shape to the `$1` surface-ref parser Task 9 shipped ("a `$1` parser fails 100% of the time in production while passing green against a marker-less stub", `spawn-handoff-session.sh:656-658`) and to `deviations.md:127`'s drift class. The cause is the same one this project already has rules against: `"Do you trust the files in this folder?"` is *plausible recalled wording*, not a measurement.

**What the dispatch should have done:** flag this as an escalation. Its L25 already states the tiebreaker; it does not apply it. Concretely the dispatch should instruct the implementer to **derive all four `screens/*.txt` fixtures from the live captures in `cmux-verb-shapes.json`** (`trust_dialog_screen.screen` → `trust-dialog.txt`; `rc_confirmation_screen.rc_screen` → `banner.txt`; `read_screen_warm.stdout` → `noise.txt`), to **replace the trust anchor with one of the two captured `candidate_anchors`**, and to re-derive the banner anchor from a running-session capture — with an explicit note that `picker-error` has no capture behind it and so must be declared as an unverified anchor in "Deviations from Plan" rather than silently shipped. Per Contract Constraints these fence changes are plan deviations the implementer must declare, so the dispatch must authorize them up front or the implementer will (correctly, under "the plan is the source of truth") implement the broken anchors.

---

### BLOCKER 2 — A fifth producer-less obligation: Step 3's anchor-provenance instruction is PROSE INSIDE A STEP, and the dispatch's four-item list omits it.

**Source:** `module-3-spawn-script.md:612`, the parenthetical under Step 3:

> (pattern constants may be hoisted; every grep uses here-strings, never a pipe. **The banner regex is finalized against Task 0's live captures if they contain a better anchor — record the choice in the code comment.**)

This commands two distinct pieces of work — *consult the live captures* and *record the choice in a code comment* — and it sits outside any checkbox. Grep confirms no step, no acceptance criterion, and no register row repeats it. The dispatch does not carry it: its "Four obligations" section (L41-51) has no fifth item, and nothing elsewhere in the 92 lines mentions anchors, captures, or a provenance comment.

This is the exact class the dispatch's own framing names. **Stated precisely, because the precise version is weaker than the tempting one:** `:612` is conditional ("*if* they contain a better anchor") and it commands work on the **banner** anchor only — trust-dialog (`:605`) and picker-error (`:606`) are stated flatly and are not covered by it. So this obligation would have caught roughly one third of Blocker 1, not all of it. It is a blocker on the accurate ground rather than the rhetorical one: **`:612` is the only place in the whole plan where anchor provenance is required at all**, in a task whose three anchors all fail against the captures — and the dispatch drops it. My probe also answers `:612`'s condition in the affirmative, so the work it commands is live, not vacuous.

---

### MEDIUM 3 — Acceptance-criterion half-covered: the **banner** steering behavior has no test.

**Source:** Module 3 Acceptance Criteria, `module-3-spawn-script.md:733`:

> Timeout → one re-wait → exit 3 `handshake=timeout` with `diagnosis=` enrichment; a stubbed banner with no token is NOT success; **trust-dialog/banner instructions steer to the existing tab**; every timeout notifies; no message claims nothing was spawned.

Step 2 produces the trust-dialog half — `test_diagnosis_trust_dialog_names_dialog_and_steers_to_tab` (`:565-567`) asserts stderr names the dialog, carries the surface ref, and omits the manual-instructions block. The **banner** half has no producer: `test_token_is_only_success` (`:559-562`) asserts only `exit 3` and `diagnosis=banner`; its stated coverage is "a full banner never selects success", not the steering message. So the property that the banner branch (`:628`) must *not* call `print_manual_instructions` and must say "do NOT start a fresh session" is unpinned — and it is a branch a future edit could route into the `*)` default without any test going red.

The dispatch inherits the gap silently. It should either name the missing assertion or tell the implementer to extend `test_token_is_only_success` with the same three stderr assertions the trust-dialog test makes.

---

### MEDIUM 4 — `deviations.md:165` is a register row whose disposition names Task 10, with no producing step in Task 10 *or* Task 13, and the dispatch does not mention it.

Row 165 (Task 9, `Concern (DONE_WITH_CONCERNS)`), disposition: **`Open — surfaced for Task 10/13 (which already revisit the record)`**. Content: a fallback workspace created but never launched into is orphaned and named in no field; and on the more visible half — `test_send_failure_on_surface_falls_back`, which exits **0** — a stray surface is left in the user's own workspace while the outcome record names only the fallback's refs.

I swept Module 3, Module 4 and `plan.md` for any step commanding this (`orphan|stray surface|left behind|workspace=spawn-failed`): the only hit outside `deviations.md` is the grammar line at `plan.md:257`. **No task's steps command it.** This is structurally the same shape as row 18 — a disposition naming a scope rather than a step — which the controller correctly caught this round and routed. Row 165 is the one it did not.

I am *not* asking for the fix. The row itself says "Cleanup is out of scope here", the field set is grammar-fixed and shared with Module 4's e2e assertions, and Task 13 ("Checked outcome writes (N63) + bookkeeping commit") is the more natural owner. What the dispatch should do is **resolve the dual routing** — one line telling the implementer either "this is Task 13's, leave it" or "re-route it to Task 13 in the register" — so it stops being a row that two tasks each assume the other owns.

---

### LOW 5 — The `internal_error` disjunct is not independently exercised by any of the four prescribed screen fixtures.

`diagnose_target` (`:602`): `if [ $? -ne 0 ] || grep -qi "internal_error" <<< "$screen"`. The only prescribed path to `unreadable` is `test_diagnosis_unreadable_on_cold_surface` (no `CMUX_SCREEN_FILE`), where the stub (`_CMUX_V2_STUB:174`) both prints `internal_error…` **and** exits 1 — so both legs always fire together and no assertion distinguishes them from `[ $? -ne 0 ]` alone.

Deliberately **not** the prior round's untestable-by-construction class: `CMUX_SCREEN_FILE` accepts any path, so a fifth fixture containing `internal_error` with rc 0 separates the legs trivially. Advisory only — worth one line in the dispatch so the implementer either adds that fixture or records the disjunct as deliberate belt-and-braces (the shape the frozen `read_screen_cold` documents: `stderr: "Error: internal_error: …", exit: 1`).

---

### LOW 6 — `_flag(_argv(tmp_path, "wait-for"), "--timeout")` returns only the FIRST wait's value; reaching for it in the re-wait test makes the "both" claim vacuous.

The stub appends per call (`_CMUX_V2_STUB:156`, `printf '%s\n' "$@" >> "$CMUX_LOG.$1.argv"`), so after a re-wait `cmux.log.wait-for.argv` holds two concatenated argv blocks. `_argv` (`test_spawn_handoff_v2.py:820-829`) returns the whole flattened file, and `_flag` (`:832-836`) is `argv[argv.index(flag) + 1]` — **first occurrence only**. The four existing callers (`:1241`, `:1247`, `:1260`, plus `:1153` for `send`) are all single-call success paths, so they are safe. But `test_timeout_rewaits_once_same_duration` is specified as "both `--timeout <same value>`", and an implementer reaching for `_flag` out of habit would write an assertion that reads wait #1 twice and cannot fail. The plan's own wording (parse `cmux.log` **lines**) avoids the trap; the dispatch, which is otherwise generous with scars, could name it.

Also worth one line in the dispatch: the three-file "fast" run measures **144.33s** against the full suite's **226.12s** — 64%, so "much faster for iteration" (L71) is optimistic enough that an implementer might bound it at 120s and get exactly the truncated-run false RED that L71's own 300s warning exists to prevent. Not a finding — the dispatch's "~200-240s" figure is accurate — just a number worth stating outright.

*(A LOW 7 on that timing wording was drafted and then withdrawn: once the full suite was measured at 226s, the dispatch's timing claim proved accurate and "much faster" reduced to a vague adjective rather than a false factual claim. Recorded here rather than deleted silently, since a withdrawn finding is evidence about the review.)*

---

## Summary of the obligation audit, by source

| Source | Obligations found | Carried by the dispatch? | Produced by a step? |
|---|---|---|---|
| Write-Scope Partitioning table (`:47-56`) | 6 writable paths ("same set" → Task 9's Step 4 resolution) | **Yes, exactly and correctly** | Yes (Step 4d) |
| Register (`deviations.md`) | Row 263 (trust preflight) | Yes (obl. 3) | Yes — Step 4(b) `:646` |
| | Row 266 (stale "both unit files") | Yes (obl. 2) | Yes — Step 4(a) `:644` |
| | Row 271 (five inline log-readers) | Yes (obl. 4) | Yes — Step 4(c) `:648` |
| | **Row 165 (orphaned fallback workspace)** | **No** | **No — in any task** → MEDIUM 4 |
| Module Acceptance Criteria (`:726-735`) | timeout/re-wait/diagnosis/notify/no-"nothing spawned" | Yes | Yes (Step 2) |
| | **"…/banner instructions steer to the existing tab"** | **No** | **No test** → MEDIUM 3 |
| | full unit suite, not "both unit files" | Yes | Yes |
| Prose inside a step | Step 2's VERIFY-don't-re-add (`:579`) | Yes (obl. 1) | Yes |
| | ROUTING note (`:549`) | Yes (obl. 3) | Yes |
| | **Step 3's anchor-provenance parenthetical (`:612`)** | **No** | **No checkbox** → BLOCKER 2 |
| Frozen Task 0 fixture (cited by the dispatch as the tiebreaker) | live anchors for all three diagnosis branches | **No — contradicted** | Step 1/3 prescribe invented anchors → BLOCKER 1 |

Four obligation sources plus the fixture; items found in three of them that the dispatch's single pass missed.

## What would clear this review

1. Authorize and instruct the anchor correction (BLOCKER 1) — derive `screens/*.txt` from `cmux-verb-shapes.json`'s live captures, replace the trust anchor with a captured `candidate_anchor`, re-derive the banner anchor from `rc_confirmation_screen`, declare `picker-error` as unverified. Fix `:626`'s quoted phrase too — two sites, one cause.
2. Add the fifth obligation (BLOCKER 2): consult Task 0's live captures for every diagnosis anchor and record the provenance in the code comment.
3. Add the banner-steering assertion (MEDIUM 3) and resolve row 165's dual routing (MEDIUM 4).
4. Optionally fold in LOW 5-6.

Everything else in this dispatch is accurate, well-scoped, and unusually careful — the four claimed amendments are all real, the verbatim quote is verbatim, the counts are all correct, and the stub genuinely supports every test Step 2 names.

**BLOCKED**
