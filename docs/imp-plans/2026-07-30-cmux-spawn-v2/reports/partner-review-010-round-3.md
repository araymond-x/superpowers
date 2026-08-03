# Partner review — Task 10 dispatch, ROUND 3 (verifying round 2's fixes)

**Reviewer:** controller partner, round 3, no prior session context.
**Date:** 2026-08-02
**HEAD reviewed:** `14bbe12` ("plan(cmux-spawn-v2): Task 10 round 2 — the fix for the invented anchor was itself false")
**Verdict:** see final line.

---

## Round 2's five findings

| # | Round 2 finding | Status |
|---|---|---|
| BLOCKER A | Banner half closed by asserting a live capture does not exist; banner regex matched neither live running session | **CLOSED-BUT-DEFECTIVE** — closed correctly and completely **in the plan** and in the dispatch's HEADLINE. The identical false claim **survives verbatim in the dispatch's Obligations section** (`task-010-dispatch-prompt.md:72`, *"Exactly one is measurable today"*), which is the site that actually commands the provenance labels. See NEW BLOCKER F |
| MEDIUM B | `internal_error` mislabelled un-captured; separating knob re-opened as an open question | **CLOSED-BUT-DEFECTIVE** — both halves fixed in the plan (Step 3b names `read_screen_cold`; Step 2 states *"THE SEPARATING KNOB ALREADY EXISTS … do not re-open it as an open question. Write BOTH cases."*). Dispatch 7(b) at `:76` still says *"if no stub knob separates them, SAY SO"* — re-opening what the plan closes. See NEW MEDIUM G |
| MEDIUM C | Partner rounds recorded only in `reports/`, not the register | **CLOSED** — two rows added to `deviations.md` (`:282` round 1, `:283` round 2), both `Resolved`, table shape intact (4 cells against the `Task \| Type \| Description \| Disposition` header; `:282`'s 5-cell split is an embedded pipe in prose, not a malformed row). **Read `:283` to its end, not sampled:** it carries the substantive decisions, not merely "a round happened" — which anchor was chosen and why, that `claude code` was REMOVED because it fires only on the trust screen, and that `esc to interrupt` is retained as a LABELLED INFERENCE. That is what survives `transition-module.py` archival, which was the point of the finding |
| LOW D | `_argv`/`_flag` misattribution | **CLOSED-BUT-DEFECTIVE** — plan `:575-578` corrected exactly right (I re-read the helpers: `_argv` at `test_spawn_handoff_v2.py:820-829` returns `read_text().splitlines()`, i.e. every line; `_flag` at `:832-834` is the `argv.index(flag)` first-occurrence half). Dispatch 7(a) `:76` still reads *"those helpers resolve only the FIRST matching invocation."* See NEW LOW H |
| NIT E | Step 4 lettered `(a)(b)(c)(e)(d)` | **CLOSED-BUT-DEFECTIVE** — plan re-lettered cleanly to `(a)(b)(c)(d)(e)` with `(d)` = row-165 routing and `(e)` = Commit. But the dispatch's obligation 6 still cites **"Step 4(e)"** for row 165, which now resolves to *Commit*. The fix for a NIT created a stale cross-reference. See NEW LOW I |

**Root cause of A/B/D/E's residue is single and mechanical:** `git show 14bbe12 -- task-010-dispatch-prompt.md` is **one hunk, `@@ -46,10 +46,15 @@`** — the HEADLINE section only. The "Obligations the plan carries that are easy to miss" section (`:60-76`), where three of round 2's five findings live, was never touched. This is the one-sided-edit shape the plan itself names twice (N1, Step 4(a)).

---

## Measurements — re-derived from the frozen fixture, not from the amendment's quotations

Fixture decoded with `json.load`; patterns run with Python `re` at `re.I`, mirroring `grep -qiE`. Every negative claim carries a positive control on the same instrument.

| Claim in the plan | My measurement | Control |
|---|---|---|
| `shift+tab to cycle` in BOTH `rc_screen` and `rename_screen`, ABSENT from `trust_dialog_screen.screen` | **TRUE.** rc=1, rename=1, trust=0 | Must-match on trust: `quick safety check` → 1. Must-NOT-match on trust: `shift` (any) → 0. Instrument proven both directions |
| `esc to interrupt` occurs **zero** times in the entire fixture | **TRUE.** 0 over the whole raw file (not a key subset) | Same instrument, same file: `esc to` → 1 (`Esc to cancel`), `interrupt` → 0. So it is a real absence, not a sampling artifact |
| `claude code` matches **only** the trust screen, neither running session | **TRUE.** trust=2, rc=0, rename=0 | `claude` (bare) → rc=2, rename=2. The instrument reaches those strings; the two-word phrase genuinely is not there |
| `read_screen_cold` is the live capture behind `internal_error` | **TRUE.** `stderr: "Error: internal_error: Failed to read terminal text\n"`, `exit: 1`, `stdout: ""`. `diagnose_target` reads `2>&1`, so the anchor is derived directly from that measured stderr | — |
| With the amended fence, both live sessions → `banner`, trust → `trust-dialog` | **TRUE.** `rc_screen`→`banner`, `rename_screen`→`banner`, `trust`→`trust-dialog` | **Reverted-pattern control:** with the old `claude code\|esc to interrupt`, rc→`none`, rename→`none`. So round 2's diagnosis was right and the prescribed positive control for `test_both_live_session_captures_diagnose_banner` **will** go RED |

Other re-derivations: `validate-plan.py` on the amended module → `blockers: []`, two pre-existing warnings (Task 8 = 266, Task 9 = 223); **Task 10 is not flagged, so still under the 200-line cap.** `deviations.md:282/283` exist with disposition `Resolved`.

---

## NEW findings

### NEW BLOCKER F — The exact false claim round 2 blocked on survives verbatim at the one dispatch site that commands the provenance labels, and it contradicts the same document 15 lines earlier.

`task-010-dispatch-prompt.md:72`, obligation 5:

> Label each anchor MEASURED (quote the fixture key) or INVENTED (say what would falsify it). **Exactly one is measurable today.**

`task-010-dispatch-prompt.md:57`, headline:

> **THREE anchors are MEASURED** (trust-dialog, banner, the `internal_error` disjunct); only `picker-error` is genuinely un-captured.

Both are in the implementer's dispatch. They cannot both be true, and **the false one sits in the numbered obligation that actually issues the instruction.** Round 2's stated reason this was a blocker — *"it commands a false statement into shipped code"* — applies unchanged at `:72`: an implementer working the obligation list will label `banner` and `internal_error` INVENTED, which is exactly the durable factual error in a code comment that round 2 blocked to prevent, and a direct violation of the plan's own new rule.

Line 72 also still carries the sentence *"Measured and inferred are not the same evidence"* immediately after asserting the count that blurs them. The amendment set that rule and this line disobeys it.

**Close it by:** replacing "Exactly one is measurable today" with the plan's corrected count (three MEASURED, `picker-error` alone INVENTED, `esc to interrupt` a labelled inference), and admitting **INFERRED** into obligation 5's rubric. The rubric currently offers only MEASURED/INVENTED, and both it and plan Step 3b `:669` count per *branch* — but the `banner` branch holds two anchors of different provenance (`shift+tab to cycle` measured, `esc to interrupt` inferred, per the fence comment at `:658-659`). Labelled per-branch, banner reads MEASURED wholesale and the inference label the fence requires is lost. Say the label is **per-anchor**, and admit the third category.

### NEW MEDIUM G — Dispatch 7(b) re-opens as an open question the knob the plan explicitly closes, and tells the implementer that "say so" is an acceptable outcome.

Plan Step 2 `:609-613`: *"THE SEPARATING KNOB ALREADY EXISTS: CMUX_SCREEN_FILE pointing at a file whose CONTENT carries `internal_error` gives rc 0 + the literal … Round 1 established this with evidence; do not re-open it as an open question. **Write BOTH cases.**"*

Dispatch `:76` 7(b): *"if no stub knob separates them, SAY SO rather than implying both are covered."*

The dispatch offers an exit the plan forbids. An implementer who reads the obligations list as the authoritative digest (which is what it is presented as) may write one case and a note, skipping coverage that costs one fixture file. Same one-sided-edit origin as F.

### NEW MEDIUM K — `shift+tab to cycle` is lifted straight out of round 2's matrix as MEASURED, with the calibration round 2 attached to it dropped, and the residual inference undeclared.

Round 2 wrote, explicitly: *"do not lift an anchor straight out of the matrix … `bypass permissions`, `shift+tab to cycle` … are mode- and settings-dependent chrome … candidates to evaluate, not validated anchors."* The amendment took `shift+tab to cycle` and carried none of that.

**What I can establish from the fixture:** the string is present in both running-session captures and absent from the trust screen and from `read_screen_warm`. That much is genuinely measured, and the plan's wording ("present in BOTH live running-session captures") is literally accurate.

**What I can establish that weakens it:** the two captures are **not two sessions.** Both `rc_screen` and `rename_screen` carry the same session id `session_01HRLuW8K` and the identical statusline `⏵⏵ bypass permissions on (shift+tab to cycle)`. So n = **one** session, captured twice, in bypass-permissions mode on Opus. The anchor is a substring of the permission-mode statusline hint.

**What I cannot establish either way:** whether that hint renders in other permission modes, other Claude Code versions, or a successor that has not finished drawing its statusline. I am not asserting it is configuration-dependent — I am asserting the fixture cannot tell us, and nothing in the plan says so.

One further gap in the same direction: both captures are of the **controller's own long-running session**, not a freshly-spawned successor. A successor stalled seconds after launch is the population this anchor must actually discriminate, and the fixture contains no capture of one.

This is not a wrong classification (both captures do route to `banner`), so it is not a blocker. But it is precisely the MEASURED-vs-INFERRED discipline Step 3b introduces one paragraph away: the measured fact is "present in one bypass-permissions session"; the operative assumption is "present in a running Claude session generally", and that generalization is currently unlabelled. **Close it by** stating the n=1-session provenance beside the anchor and declaring the generalization as the residual inference it is — or by adding a second, differently-configured capture, which is out of scope here.

### NEW MEDIUM M — The anti-drift guard was applied to `trust-dialog.txt` and not to `banner.txt`, leaving round 1's original hole open on the branch round 2 just fixed.

Round 1's BLOCKER 1 remedy was twofold: derive the fixture from the frozen capture, **and** pin it with an equality test, because *"a fixture authored to match the code under test proves only that you can spell the same string twice."* Trust got both — plan `:557` ("add a test asserting the fixture still equals that frozen value") and `test_trust_dialog_fixture_matches_the_frozen_capture` at `:586-588`.

`banner.txt` got only the first half. Measured — `/usr/bin/grep -nF "banner.txt"` over the plan returns exactly two hits: `:559` (the amendment prose telling you to derive it from `rc_confirmation_screen.rc_screen`) and `:570` (a test comment using it as a `CMUX_SCREEN_FILE` value). **No equality test is prescribed for it anywhere.** Positive control: the same sweep for `trust-dialog` finds the derivation instruction *and* the named pinning test.

The new `test_both_live_session_captures_diagnose_banner` does not fill the gap, and its wording ("Drive both verbatim from the fixture", `:602`) is ambiguous between two readings that both leave the hole:

- the test reads `cmux-verb-shapes.json` directly → `screens/banner.txt` is an unpinned hand-copy that nothing guards, and it is what `test_token_is_only_success` at `:570` actually loads;
- the test reads `banner.txt` → then `banner.txt` itself has no guard tying it to `rc_screen`, which is exactly the round-1 defect.

Either way, `banner.txt` can drift from the capture it claims to be derived from and every test stays green. Same one-sided-edit shape as F/G/H/I — but this one is in the **plan**, not just the dispatch, and it re-opens the specific hole this whole three-round sequence exists to close. **Close it by** prescribing a `test_banner_fixture_matches_the_frozen_capture` twin, and disambiguating `:602` to say which artifact the diagnosis test loads.

### NEW MEDIUM L — Removing `claude code` from the banner pattern made the trust-ordering pin vacuous, and the plan still prescribes a positive control that can no longer go RED.

Round 2 verified that `test_real_trust_capture_diagnoses_trust_not_banner` was **non-vacuous** because the then-current banner regex `claude code|esc to interrupt` matched the real trust capture. Correctly removing `claude code` removed exactly that overlap. Nothing in the amendment revisited the pin that depended on it.

Measured, per-pattern, against the real `trust_dialog_screen.screen`:

```
internal_error                       -> 0
quick safety check|yes,i trust…      -> 2
claude-picker:(error|fatal)|no match -> 0
shift+tab to cycle|esc to interrupt  -> 0     (amended banner)
claude code|esc to interrupt         -> 2     (old banner)
```

Running the fence in plan order gives `trust-dialog`. Running it with **banner hoisted above trust — the exact mutation the plan prescribes** — also gives `trust-dialog`, because no other branch matches the trust screen at all. Under the old pattern the same mutation gave `banner`.

Two consequences:

1. **Plan `:590-592` commands an impossible verification.** *"Positive-control it by reordering the two greps in `diagnose_target` and confirming this test goes RED."* It will go GREEN. An implementer following the instruction faithfully will hit a control that does not fire and must either report a deviation or — the risk this sprint keeps hitting — quietly conclude the pin is fine.
2. **The ordering constraint is now unpinned.** The fence comment at `:651-652` still says *"The trust test MUST precede the banner test … reordering these silently misroutes a trust modal."* Against the amended pattern that sentence is no longer true, and no test constrains the order. Harmless today; it becomes a live misroute the moment anyone widens the banner pattern (e.g. adding `bypass permissions`, which the round-2 matrix lists and which does **not** appear on the trust screen — but the next widening might).

This is a defect the round-2 amendment introduced, and it is invisible unless you re-measure the control rather than reading it.

**Close it honestly, not by substitution.** A replacement control that mutates the *trust* pattern to something absent will fire — but it pins that the test reads the real capture, **not** that ordering matters, which is what the test's name (`..._diagnoses_trust_not_banner`) and the fence comment (`:651-652`, *"The trust test MUST precede the banner test"*) both assert. Against the amended patterns the ordering claim is unfalsifiable by any fixture that exists. Swapping in a control that fires on a different proposition while leaving the name and comment asserting the old one reproduces exactly the measured/inferred blur the amendment's own rule forbids. So: re-scope or rename the test to what it now pins, and mark the fence comment as **defence-in-depth against a future pattern widening** rather than a currently-tested invariant — saying so plainly is the fix.

### NEW LOW H — Dispatch 7(a) still carries the `_argv` misattribution the plan corrected.

`:76` — *"those helpers resolve only the FIRST matching invocation."* Measured: `_argv` (`test_spawn_handoff_v2.py:820-829`) returns `p.read_text().splitlines()` — all lines. Only `_flag` (`:832-834`) is first-occurrence. The operative instruction (parse both `cmux.log` lines) is right either way, and the plan's `:575-578` is now exactly right; this is the uncorrected twin.

### NEW LOW I — Dispatch obligation 6 cites "Step 4(e)" for row 165, which the NIT E re-lettering made *Commit*.

Plan: `(d)` = resolve routing of `deviations.md:165`; `(e)` = Commit. Dispatch `:74` says *"Step 4(e): resolve the ROUTING of `deviations.md:165`."* The obligation text names the row unambiguously so the work will still be done, but the pointer now misresolves — a citation-rot instance created by a cosmetic fix, the same class as `deviations.md:218`.

---

## Claims I checked for falsehood and found TRUE

All five anchor claims above (independently re-derived, each with a control); `read_screen_cold`'s shape; the reverted-pattern control going RED as prescribed; `_argv`/`_flag` bodies as the plan now describes them; Step 4's `(a)-(e)` lettering; the two new `deviations.md` rows and their `Resolved` disposition; `validate-plan.py` clean of blockers with Task 10 under the cap; `trust_dialog_screen.candidate_anchors` quoted verbatim in both the plan fence and the operator message at `:683`.

## Drafted and withdrawn (recorded rather than deleted)

- I drafted the ordering-pin item as a soft "flag for the implementer's reviewer" rather than a finding, on the reasoning that the vacuity was created by *correctly* removing a bad anchor and the plan's own control would expose it. Then I ran the prescribed mutation instead of reasoning about it, and the control comes out GREEN — so the plan commands a verification that cannot succeed. Promoted to **MEDIUM L** rather than softened. Recording the reversal because the first draft is the mistake this review exists to catch: reading a control instead of firing it.
- I drafted a finding that `deviations.md:283` is a malformed 4-cell row against a 5-cell table. Counted the header (`:6`, four columns) and the whole-file distribution (199 rows at 4 cells): 4 is the correct shape and `:282`'s 5 is an embedded pipe. Withdrawn.
- I drafted a finding that the plan still contained "synthetic by necessity". It does at `:559`, but only as a **quotation of the false claim being corrected**, correctly framed. Withdrawn; sweep confirmed no live instance survives in the plan.

---

## Summary

Round 2's substantive work landed, and landed well **in the plan**. I re-derived all five anchor claims from the frozen fixture myself with controls in both directions, and every one is true: `shift+tab to cycle` discriminates the two live sessions from the trust screen, `esc to interrupt` really does occur zero times in the whole file, `claude code` really did fire only on the screen the branch must never claim, `read_screen_cold` really is the `internal_error` source, and the amended fence classifies all three real captures correctly where the old one classified neither running session. The register rows are there. The lettering is fixed.

What blocks is that the amendment edited the dispatch prompt in **one hunk covering only its headline**, while three of round 2's five findings lived in the Obligations section below it. The result is a dispatch that states the corrected count at `:57` and the false one at `:72`, tells the implementer at `:76` to consider "no knob exists" an acceptable answer that the plan forbids, repeats the `_argv` misattribution the plan fixed, and points obligation 6 at the wrong sub-item. The false-count sentence is not a stale echo in prose — it sits inside the numbered obligation that issues the provenance-labelling instruction, so the wrong labels are still the ones the dispatch commands.

Three rounds, three times the defect was in the fix. Most of this round's residue is narrower than its predecessors' — every fix is correct, they were just applied to one of the two documents that carry them.

**L and M are the exceptions, and both are one-sided in the plan itself.** L: correctly deleting a bad anchor silently voided the positive control the plan prescribes for the ordering pin, so the plan now instructs the implementer to confirm a RED that will come back GREEN — visible only if you fire the control rather than read it. M: the anti-drift equality test that was round 1's whole remedy was written for `trust-dialog.txt` and never for `banner.txt`, so the fixture the round-2 amendment introduced can drift from the capture it claims to derive from with every test green. M re-opens, on the banner branch, the exact hole all three rounds have been closing.

**BLOCKED**
