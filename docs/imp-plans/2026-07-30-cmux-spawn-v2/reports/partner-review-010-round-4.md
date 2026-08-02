# Partner review — Task 10 dispatch, ROUND 4 (verifying round 3's fixes)

**Reviewer:** controller partner, round 4, no prior session context. Read-only.
**Date:** 2026-08-02
**HEAD reviewed:** `e08db4b` ("plan(cmux-spawn-v2): Task 10 round 3 — a one-sided edit, and a control the fix dissolved")
**Verdict:** see final line.

---

## Round 3's findings

| # | Round 3 finding | Status |
|---|---|---|
| BLOCKER F | Dispatch `:72` still said "Exactly one is measurable today"; rubric lacked INFERRED; labels counted per-branch | **CLOSED.** Dispatch `:72` now carries the corrected three-MEASURED count naming each fixture key, `:74` adds the K nuance, `:57` and plan `:689` both say **PER ANCHOR, not per branch, in THREE categories**. The two documents agree verbatim on the count and on the rubric |
| MEDIUM K | `shift+tab to cycle` lifted as MEASURED with round 2's calibration dropped; n=1 undeclared | **CLOSED.** Plan `:561` and dispatch `:74` both state same session id + same bypass-permissions statusline → n = one session captured twice, long-running interactive rather than freshly-spawned, generalization declared INFERRED. Present in **both** documents |
| MEDIUM L | Removing `claude code` dissolved the overlap; prescribed positive control can no longer go RED; ordering unpinned | **CLOSED-BUT-DEFECTIVE.** The test-level half landed well: `:595-605` retires the dead control and explains why, `:606-612` adds `test_ordering_trust_beats_banner_on_a_both_anchors_screen` with a control that — **fired, not read** — does go RED (see "Replacement control, fired" below). But round 3's second prescribed half — *"mark the fence comment as defence-in-depth … rather than a currently-tested invariant"* — was **not applied**. The fence comment at `:671-672` still asserts the measured-false claim, and the dispatch repeats it at `:55`. See **NEW BLOCKER N**. The remedy also introduces a fifth fixture that Step 1 does not produce — see **NEW MEDIUM O** |
| MEDIUM M | `banner.txt` derived but never pinned by an equality test | **CLOSED** in the plan: `test_banner_fixture_matches_the_frozen_capture` at `:589-594`, twinning `test_trust_dialog_fixture_matches_the_frozen_capture`. The `:617-623` "Drive both verbatim from the fixture" ambiguity round 3 also asked to resolve is untouched, but the new equality test closes the drift hole under either reading, so this is now a nit (see LOW Q) |
| MEDIUM G | Dispatch 7(b) re-opens the `internal_error` knob the plan closes | **NOT CLOSED.** Dispatch `:78` still reads *"if no stub knob separates them, SAY SO rather than implying both are covered"*; plan `:630-633` still reads *"THE SEPARATING KNOB ALREADY EXISTS … do not re-open it as an open question. **Write BOTH cases.**"* Verbatim unchanged |
| LOW H | Dispatch 7(a) `_argv` misattribution | **NOT CLOSED.** Dispatch `:78` still says *"those helpers resolve only the FIRST matching invocation"*; plan `:575-578` correctly blames `_flag` alone |
| LOW I | Dispatch obligation 6 cites "Step 4(e)" for row 165 | **NOT CLOSED.** Dispatch `:76` still says Step 4(e); plan `:727` is `(d)` = row-165 routing, `:729` `(e)` = Commit |

**The round-3 amendment touched the dispatch prompt in exactly two hunks** (`git show e08db4b -- task-010-dispatch-prompt.md`): the headline bullet at `:57` and obligation 5 at `:72-74`. Obligations 6 and 7 — where G, H and I live — were not touched. **Round 3's stated root cause was a one-sided edit across two documents, and the fix for it was itself applied one-sidedly.** That is the fourth consecutive round in which the defect is in the fix.

---

## Consistency sweep — every cross-document claim, compared

Both documents read from disk at `e08db4b`. Instrument: `/usr/bin/grep -nE`, positive-controlled (`grep -c "Step"` on the dispatch → 12; `grep -cEi banner` → 8, so the instrument reaches the file and the sections in question).

| Claim | Plan | Dispatch | Verdict |
|---|---|---|---|
| Real trust anchors are `Quick safety check…` / `1. Yes, I trust this folder`; `Do you trust the files…` appears nowhere | `:555` | `:43` | **AGREE** |
| `trust-dialog.txt` derived verbatim + pinned by an equality test | `:557`, `:586` | `:54` | **AGREE** |
| `banner.txt` derived from `rc_confirmation_screen.rc_screen`; both live captures pin to `banner` | `:559`, `:617` | `:54` | **AGREE** |
| `banner.txt` **also** pinned by an anti-drift equality test (MEDIUM M) | `:589-594` | *absent* | **GAP, not conflict** — see LOW P |
| Trust grep precedes banner; **"the banner regex MATCHES the real trust screen / reordering silently misroutes a trust modal"** | `:671-672` asserts it; `:597-605` refutes it | `:55` asserts it | **CONFLICT — and the assertion is measured FALSE.** BLOCKER N |
| `shift+tab to cycle` MEASURED, `esc to interrupt` INFERRED, `claude code` REMOVED | `:561`, `:675-682` | `:56` | **AGREE** |
| n = one session captured twice; generalization INFERRED (MEDIUM K) | `:561` | `:74` | **AGREE** |
| THREE anchors MEASURED, only `picker-error` un-captured | `:689` | `:57`, `:72` | **AGREE** |
| Label PER ANCHOR, three categories MEASURED/INFERRED/INVENTED | `:689` | `:57`, `:72` | **AGREE** |
| `internal_error` separating knob: exists, write BOTH cases | `:630-633` — closed | `:78` — "SAY SO" is acceptable | **CONFLICT** (MEDIUM G, carried) |
| `_argv` vs `_flag` first-occurrence blame | `:575-578` — `_flag` alone | `:78` — "those helpers" | **CONFLICT** (LOW H, carried) |
| Sub-item owning `deviations.md:165` routing | `:727` = **(d)** | `:76` = **Step 4(e)** | **CONFLICT** (LOW I, carried) |
| Import assertion already landed — verify, do not re-add | `:643` | `:64` | **AGREE** |
| Full unit suite, baseline 777, re-measure | `:721` | `:66` | **AGREE** |
| Five inline log-readers, different shape, decision not cleanup | `:725` | `:70` | **AGREE** |
| Trust-preflight decision; declining on "already trusted" forbidden | `:549`, `:723` | `:68` | **AGREE** |
| Write scope = six paths | Task 9 `:543` / Task 10 "same set" | `:29-35` | **AGREE** |
| Synthetic fixture inventory | `:563` says the set is closed at four, "the remaining **two** ARE synthetic"; `:606-612` requires a fifth, synthetic | *absent* | **INTERNAL PLAN CONFLICT** — MEDIUM O |
| **Module 3 AC** — "trust-dialog/banner instructions steer to the existing tab" (`:812`) | `test_diagnosis_trust_dialog_names_dialog_and_steers_to_tab` `:582`, `test_diagnosis_banner_steers_to_tab_and_omits_manual_block` `:613`; tail `:702-705` steers both, `print_manual_instructions` fires only on `picker-error`/`*` | `:17` (token is the only success signal) | **AGREE** — both branches covered, discriminator asserted |
| **Module 3 AC** — full unit suite green, **not "both unit files"** (`:814`) | Step 4(a) `:721` | `:66` | **AGREE** |
| **Module 3 AC** — timeout → one re-wait → exit 3 `handshake=timeout` + `diagnosis=`; stubbed banner is not success; every timeout notifies; no message claims nothing was spawned (`:812`) | tail `:694-715`; tests `:569`, `:573`, `:636` | `:15`, `:17` | **AGREE** |

### Replacement control, fired

MEDIUM L's remedy is credited on measurement, not on reading. Synthetic both-anchors screen = `trust_dialog_screen.screen` + `rc_confirmation_screen.rc_screen`, run through the amended fence:

```
branch counts on the composed screen:  internal_error 0 | trust 2 | picker-error 0 | banner 1
plan order (trust, picker, banner)  -> trust-dialog
banner hoisted above trust          -> banner          <-- the control FIRES
```

No earlier branch is tripped in transit — in particular the trust capture's `claude-picker --non-interactive --pick-version 2.1.220` line does **not** satisfy `claude-picker: (error|fatal)|no matching version` (0 matches), so the composed screen reaches the ordering decision rather than short-circuiting to `picker-error`. The test the amendment prescribes can therefore do what the one it replaces can no longer do.

---

## NEW findings

### NEW BLOCKER N — The plan's implementation fence still states, as fact, the claim round 3 measured false; the implementer will copy it verbatim into shipped code, and the dispatch repeats it.

Plan `:671-672`, inside the `diagnose_target` bash fence the implementer is told to implement:

```
# The trust test MUST precede the banner test: the banner regex MATCHES the real
# trust screen, so reordering these silently misroutes a trust modal to "banner".
```

Dispatch `:55`: *"The trust grep **must precede** the banner grep … Reordering them silently misroutes a trust modal."*

**Re-derived independently from the frozen fixture** (`json.load`, Python `re` at `re.I`, mirroring `grep -qiE`), not from any quotation:

```
pattern                                 trust  rc_screen  rename_screen
shift\+tab to cycle|esc to interrupt      0        1            1     (amended banner, plan :682)
claude code|esc to interrupt              2        0            0     (old banner)
quick safety check|yes, i trust…          2        0            0
claude-picker: (error|fatal)|no match     0        0            0
internal_error                            0        0            0
```

Controls, both directions on the same instrument: must-match `safety` on trust → 1; must-not-match `shift` on trust → 0, while `shift` on both live captures → 1; bare `claude` reaches all three screens (4/2/2), so the two-word `claude code` genuinely is absent from the running sessions. Running the fence in plan order and with banner hoisted above trust:

```
trust  -> trust-dialog   | reordered: trust-dialog
rc     -> banner         | reordered: banner
rename -> banner         | reordered: banner
```

**The banner regex on line 682 does not match the real trust screen.** The comment two lines above it says it does. It was true of the pattern the round-2 amendment deleted, and the round-3 amendment — which diagnosed exactly this in the test comment at `:597-605` ("removing `claude code` … DISSOLVED the very overlap that made ordering load-bearing") — corrected the test and left the fence. The two sit 70 lines apart in one file and contradict each other; `grep -Ei "defen[cs]e-in-depth"` finds the honest framing at `:607` only, never in the fence.

Why this is a blocker and not a nit: the fence is the implementation, and its comments ship. Round 2 blocked on the principle that the plan *"commands a false statement into shipped code"* — this is the same thing, in the same file, one round later. An implementer who reads the fence (the authoritative artifact for Step 3) will write a false justification into `spawn-handoff-session.sh`, and a later reader deciding whether to widen the banner pattern will believe an overlap exists that does not, and will trust an invariant no captured fixture exercises.

**Close it by** rewriting `:671-672` to say what is now true — ordering is defence-in-depth against a *future* pattern widening, no captured screen carries both anchors, and it is pinned by the synthetic both-anchors test — and applying the same correction to dispatch `:55`. Round 3 prescribed exactly this wording; it is a two-line edit in each document.

### NEW MEDIUM O — MEDIUM L's remedy requires a fifth fixture that Step 1 does not produce, and it falsifies Step 1's own inventory.

Step 1 (`:563`) closes the fixture set: *"The **remaining two** ARE synthetic — `picker-error.txt` … and `noise.txt` … and that limitation must be stated in each file or its loader comment."* Four fixtures, two of them synthetic.

Step 2's new test (`:606-612`) requires *"an explicitly SYNTHETIC fixture containing BOTH a trust anchor and a banner anchor, labelled synthetic where it lives."* That is a **fifth** fixture and a **third** synthetic one. Step 1 — the checkbox that produces fixtures — neither names it nor extends the synthetic-labelling instruction to it, and "the remaining two" is now false.

This is the producer-less shape the plan has already BLOCKED a partner round over (round 1's BLOCKER 2: *"prose inside Step 3 that commanded work no checkbox produced"*). It is a MEDIUM rather than a BLOCKER because the requirement does live inside a Step 2 checkbox and states the labelling obligation inline, so a careful implementer will create it — but the fixture inventory an implementer reads first says the set is closed, and the "state the synthetic limitation in each file" rule is scoped to the wrong two files.

**The escape reading, answered in advance:** "the test can compose the both-anchors screen inline in `tmp_path`, so Step 1 needs no change." Even granting that, `:563`'s *"that limitation must be stated in each file **or its loader comment**"* is written against a closed set of two, and *"the remaining two ARE synthetic"* is false either way — there are now three synthetic screens in this task regardless of where the third one is written. The inventory is wrong independently of the fixture's storage form.

**Close it by** adding the both-anchors screen to Step 1's enumeration and correcting "the remaining two".

### NEW MEDIUM R — Task 10's round 3 is not in the register.

`deviations.md` carries `:282` (Task 10 partner round 1) and `:283` (Task 10 partner round 2), both `Resolved`. There is no Task 10 round-3 row. **Measured, with the negative controlled:** `/usr/bin/grep -c "partner round 3"` returns 2, but both hits (`:266`, `:267`) belong to **Task 9's** review series and are `DeferredWork` observations, not Task 10 round-3 rows. Positive controls on the same instrument: `"partner round 2"` → 4, `"partner round 1"` → 3, so the grep does find round rows when they exist.

Round 3's own MEDIUM C established this convention precisely because `reports/` is archived by `transition-module.py` while `deviations.md` survives, and round 3 carries the most transferable lesson of the three — *a correct fix can retire the subject of a companion test, leaving a test that still reads as a guard*. Recorded only in `reports/partner-review-010-round-3.md`, that lesson is the one most likely to be lost. Not implementer-facing, so it does not gate the dispatch on its own.

### LOW P — The dispatch says `banner.txt` "likewise derives" but never mentions its new equality pin.

Dispatch `:54` gives trust-dialog the derivation *and* the pinning test, then says `banner.txt` "likewise derives". Not false — the plan is authoritative and now has `test_banner_fixture_matches_the_frozen_capture` — but the asymmetry in the digest is exactly the reading that let MEDIUM M survive round 2. One clause.

### LOW Q — `:617-623` still ambiguous about which artifact the diagnosis test loads.

Round 3 asked for "Drive both verbatim from the fixture" to be disambiguated (does the test read `cmux-verb-shapes.json` or `screens/banner.txt`?). Untouched. Now harmless — the new equality test pins the two together under either reading — so this is downgraded from part of MEDIUM M to a wording nit.

---

## Claims I checked for falsehood and found TRUE

All five anchor measurements, independently re-derived with controls in both directions (table above); `read_screen_cold`'s `internal_error` stderr + exit 1 as the direct source of the `unreadable` disjunct; the amended fence classifying all three real captures correctly (trust→trust-dialog, both live→banner); the old pattern classifying both live captures as `none`; `trust_dialog_screen.candidate_anchors` quoted verbatim in the plan fence, in the operator message at `:703`, and in the dispatch at `:43`; the per-anchor three-category rubric present and identically worded in both documents; the n=1 scoping present in both; Step 4's `(a)-(e)` lettering in the plan; `validate-plan.py --plan-file` on the amended module → `"blockers": []`, warnings only for Task 8 (266) and Task 9 (223) — **Task 10 is still under the 200-line cap after the amendment.**

## Drafted and withdrawn

- I drafted BLOCKER N as a LOW ("stale comment"), on the reasoning that the plan already explains the dissolution at `:597-605` so the implementer will see both and pick the right one. Then I checked where each sentence *lands*: the honest version lives in a test comment, the false version lives in the bash fence that becomes shipped source. A reader of the shipped script sees only the false one. Promoted to BLOCKER. Recording the reversal because the first draft is the mistake — judging a claim by whether it is contradicted somewhere rather than by where it ends up.
- I drafted a finding that dispatch `:55`'s "a test pins that ordering" was false. It was true of `e08db4b`'s predecessor and is now true again, because the amendment adds `test_ordering_trust_beats_banner_on_a_both_anchors_screen`. Only the second half of that bullet ("reordering silently misroutes") is false. Withdrawn as a separate item; folded into N.
- I drafted a finding that the amendment pushed Task 10 over the 200-line cap. Ran `validate-plan.py`; Task 10 is not flagged. Withdrawn.
- I initially credited MEDIUM L's replacement test on inference — the reasoning ("a screen with both anchors must obviously flip under reordering") is sound, and round 3's finding was that the *old* control was dead, which I had measured. Then I noticed I was about to repeat, in the review of that finding, the exact error round 3 recorded against itself: reading a control instead of firing it. Composed the screen and ran it. It fires. Credit stands, but it is now measured; the reasoning would also have missed a short-circuit into an earlier branch, which I checked and which does not happen.
- I drafted finding R as "no round-3 row exists", from an `awk NR>=280` tail — a bounded view, which cannot establish an absence. Re-ran it as a whole-file count and found two hits for "partner round 3" that belong to *Task 9's* series. The finding survives with its scope corrected; the first phrasing would have been right by luck.

---

## Summary

Round 3's four substantive findings against the *plan* were fixed, and two of them well: the provenance count and the per-anchor three-category rubric now appear in **both** documents in agreement — the first time this sequence has produced a genuinely two-sided edit — and MEDIUM K's n=1 calibration likewise. MEDIUM M got its twin test. MEDIUM L got the better half of its remedy: the dead control is retired with its reasoning intact, and a control that can actually fire replaces it.

What blocks is that the amendment was **again** applied to one side. Three of round 3's seven findings (G, H, I) live in the dispatch's Obligations section, which the round-3 hunk did not touch at all — so the dispatch still offers the implementer an exit the plan forbids on the `internal_error` knob, still misattributes `_argv`, and still points obligation 6 at *Commit*. And MEDIUM L's second prescribed half — correcting the fence comment that justified the ordering — was applied to neither document, leaving a measured-false factual claim inside the bash fence the implementer copies into shipped source, contradicted by a test comment 70 lines above it in the same file.

The one-sided-edit pattern is now four rounds old and is no longer a discovery; it is the mechanism. The remaining work is small and entirely mechanical — two comment rewrites (plan `:671-672`, dispatch `:55`), three dispatch sentences already written correctly in the plan (`:78` twice, `:76`), and one line in Step 1's fixture inventory. None of it requires new measurement. But dispatching now ships a false comment in the deliverable and hands the implementer a permission the plan revokes, so it is not ready.

**BLOCKED**
