# Partner review — Task 10 dispatch, ROUND 2 (verifying round 1's fixes)

**Reviewer:** controller partner, round 2, no prior session context.
**Date:** 2026-08-02
**HEAD reviewed:** `5586a9a` ("plan(cmux-spawn-v2): Task 10 amendments — partner round 1 BLOCKED on invented anchors")
**Verdict:** see final line.

---

## Method

**Read in full:**

- `git show 5586a9a` — the whole amendment diff. **File list confirmed:** `module-3-spawn-script.md` (+57/−6), `reports/checkpoint-pre-dispatch-010.json` (+47), `reports/partner-review-010.md` (+176), `task-010-dispatch-prompt.md` (+111). **`deviations.md` is NOT in the diff** — see NEW MEDIUM C.
- `docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/partner-review-010.md` — round 1, all 177 lines.
- `module-3-spawn-script.md` — header (Contract Constraints `:35`, File Map, Write-Scope Partitioning `:47-56`), Task 9 Step 4 (`:543-545`), **Task 10 in full (`:547-687`)**, Module 3 Acceptance Criteria (`:763-772`, now shifted from round 1's `:726-735` by the amendment).
- `task-010-dispatch-prompt.md` — all 112 lines.
- `deviations.md` — rows 18, 164, 165, 192, 214, 228, 230, 262, 263, 264, 266, 267, 271, 275 read individually; every `Pending`/`Open` disposition enumerated.
- `reports/checkpoint-pre-dispatch-010.json` — the fourth file in the amendment commit, read in full (all 47 lines).
- `tests/unit/fixtures/spawn-handoff/cmux-verb-shapes.json` — decoded in full: top-level provenance keys, `trust_dialog_screen`, `rc_confirmation_screen` (both `rc_screen` and `rename_screen`), `read_screen_cold`, `read_screen_warm`.
- `tests/unit/spawn_handoff_helpers.py` `_CMUX_V2_STUB` (`:151-187`); `tests/unit/test_spawn_handoff_v2.py` `_argv`/`_flag` (`:818-836`) and the landed import assertion (`:1265-1275`).

**Ran** (every recursive sweep via `/usr/bin/grep` or `find -print0 | xargs -0`, never the shell's ugrep wrapper):

| Probe | Result |
|---|---|
| Decoded `trust_dialog_screen.candidate_anchors` from the frozen JSON myself | **Exactly** `"Quick safety check: Is this a project you created or"` and `"1. Yes, I trust this folder"` — the amendment's quotation is verbatim-correct |
| Wrote all five live captures to files, ran the **amended** fence in plan order (`internal_error` → trust → picker-error → banner) with real `grep -qiE` here-strings | `trust_dialog_screen`→**`trust-dialog`** ✅ · `read_screen_cold`(2>&1)→`unreadable` · `rc_screen`→**`none`** ⚠ · `rename_screen`→**`none`** ⚠ · `read_screen_warm`→`none` |
| **Control (must match):** `araymond\|remote-control\|task0` per capture | fired on 4/5. The 5th (`read_screen_cold`) is a one-line error string; its own must-match (`internal_error`) fired. Instrument proven live |
| **Control (must NOT match):** old invented phrase `do you trust the files` vs the real trust capture | **ABSENT** — round 1's BLOCKER 1 independently reconfirmed |
| **Control (ordering is load-bearing):** banner regex `claude code\|esc to interrupt` vs the real trust capture | **MATCHES** — so the amendment's "trust must precede banner" claim is TRUE and its pinning test is non-vacuous |
| Candidate-anchor discrimination matrix across all four screen captures (8 patterns × 4 screens) | see NEW BLOCKER A — `esc to interrupt` fires on **zero** captures; `claude code` fires on the **trust** screen only |
| `find . -path ./.git -prune -o -type f -print0 \| xargs -0 /usr/bin/grep -l -i "do you trust the files"` | 3 hits, **all explanatory prose** (plan `:555`, dispatch `:43`, round-1 report). No fence or instruction still carries it. Positive control `"quick safety check"` returned 6 files incl. the fixture — instrument confirmed |
| `/usr/bin/grep -nE '^SPAWN_WAIT_TIMEOUT_DEFAULT=' spawn-handoff-session.sh` | `54:SPAWN_WAIT_TIMEOUT_DEFAULT=60` — **column 0**, confirmed |
| `pytest tests/unit/ -q --collect-only` | **777** — dispatch baseline confirmed |
| `pytest` collect on the three spawn files | **143** — dispatch baseline confirmed |
| `pytest -k wait_timeout_default -q` | **1 passed** — the "already landed" assertion still resolves and passes |
| `/usr/bin/grep -nF '(tmp_path / "cmux.log").read_text()' test_spawn_handoff.py` | **exactly 5** (686, 840, 867, 957, 996) — Step 4(c)'s "count VERIFIED at 5" confirmed |
| `/usr/bin/grep -cF '[ $rc -eq 0 ] \|\| return 1' spawn-handoff-session.sh` | **3** — the dispatch's mutation-hygiene scar is accurate |
| Read `_CMUX_V2_STUB` `read-screen`: `[ -n "$CMUX_SCREEN_FILE" ] && { cat "$CMUX_SCREEN_FILE"; exit 0; }` | a screen file containing `internal_error` yields **rc 0 + literal** → the two `unreadable` disjuncts ARE separable with an existing knob. See NEW MEDIUM B |
| Register sweep for every row whose disposition names Task 10 | rows **18/263, 266, 271, 165** — exactly four, all four carried by the dispatch. No sixth |
| `/usr/bin/grep -c -i "esc to interrupt" cmux-verb-shapes.json` (whole file, not my four extracts) | **0**. Controls on the same instrument: `esc to cancel` → 1, `claude code` → 1. So "appears nowhere in the frozen fixture" is the whole-file claim, not a sampling artifact |
| **The mechanical gate** — `validate-plan.py --plan-file module-3-spawn-script.md`, raw JSON read (my first invocation failed in argparse and taught nothing; rerun with the required flag) | **`status: WARNING`, `blockers: []`.** **Task 10 = 142 lines, `OK`** — comfortably under the 200-line cap despite the amendment's +57. The two warnings are pre-existing Task 8 (266) and Task 9 (223), both already executed; `deviations.md:192` (OP-1) records that cap history. **The amended plan still passes the gate — the dispatch is not blocked mechanically** |
| Read `reports/checkpoint-pre-dispatch-010.json` (the 4th file in the amendment commit, +47) | Machine-generated by `controller-checkpoint.py`, `status: PASS`, `blockers: []`, one WARNING (context load ~182k tokens). **No controller-authored claim in it contradicts anything I measured.** Two oddities are known tool artifacts, not false claims: `pending_deviations: "0 pending"` despite ~13 `Pending`/`Open` rows (its `PENDING_DEVIATION_PATTERN` matches a specific disposition-cell shape, not free-text "Pending —"), and `progress: tasks_total 4 / tasks_completed 9` (manifest-scoped range vs. absolute task id). Flagged as observations only |

---

## Round 1's six findings

| # | Round 1 finding | Status |
|---|---|---|
| BLOCKER 1 | Invented screen anchors; trust modal misclassified as `banner` | **CLOSED-BUT-DEFECTIVE** — the trust half is closed correctly and well; the **banner half is closed with a false claim**. See NEW BLOCKER A |
| BLOCKER 2 | Anchor provenance was prose inside Step 3, no producer | **CLOSED** — promoted to a real checkbox, `- [ ] **Step 3b:**` at `:647`, carried as dispatch obligation 5. The old Step 3 parenthetical (`:645`) was correctly *reduced* to constraints only, leaving no stale twin. Its content is nonetheless partly false — NEW BLOCKER A / MEDIUM B |
| MEDIUM 3 | Banner-steering AC half-covered, no test | **CLOSED** — `test_diagnosis_banner_steers_to_tab_and_omits_manual_block` added at `:588`, with the discriminator named (manual-block ABSENT). *Caveat:* it will be green against a synthetic fixture — see NEW BLOCKER A |
| MEDIUM 4 | `deviations.md:165` dual routing, no producer | **CLOSED** — Step 4(e) at `:685`, dispatch obligation 6; correctly framed as "resolve the ROUTING, not necessarily the fix" |
| LOW 5 | `internal_error` disjunct not independently exercised | **CLOSED-BUT-DEFECTIVE** — carried into Step 2's fence (`:596-600`) and dispatch 7(b), but it **re-opens as a question what round 1 answered with evidence**. See NEW MEDIUM B |
| LOW 6 | `_flag` first-occurrence vacuity in the re-wait test | **CLOSED** — `:571-576` names the trap, forbids `_flag`, prescribes parsing both `cmux.log` lines, and adds a positive control. One wording imprecision (LOW D) |

Round 1's "what would clear this review" item 1 also asked that `:626`'s operator message be fixed as the twin site. **Done** — `:661` now quotes `'Quick safety check: ... 1. Yes, I trust this folder'`. No one-sided edit there.

**Claims I checked for falsehood and found TRUE:** the candidate-anchor quotation; "the banner regex matches the real trust screen"; the `trust` positive-control claim; the 777 and 143 baselines; the column-0 `SPAWN_WAIT_TIMEOUT_DEFAULT=60`; the five inline log-readers; the three `[ $rc -eq 0 ] || return 1` sites; the Module AC last-bullet quotation at `:772`; that the landed import assertion exists and passes.

---

## NEW findings

### NEW BLOCKER A — The banner half of BLOCKER 1 was closed by asserting a live capture does not exist. It does. The banner branch is still dead against every live capture of a running Claude session, and one of its two anchors matches nothing at all.

**The claim, at two consistent sites** (so this is not a one-sided edit — it is uniformly wrong):

- plan `:559` — "The other three are synthetic by necessity **(Task 0 captured no live screen for them)**"
- plan `:647` (Step 3b) — "`banner`, `picker-error` and the `internal_error` disjunct have **no live capture**… Today exactly one is measurable: `trust-dialog`."
- dispatch `:52` / `:67` — the same two sentences.

**The fixture's own provenance metadata contradicts this.** `cmux-verb-shapes.json` carries top-level `"captured": "live"`, `captured_at: 2026-07-30`, against `cmux 0.64.20 (100) [14e3400b9]`, and its `capture_note_addendum` states every key is live. `rc_confirmation_screen` holds **two live screen captures of a running Claude Code session** — `rc_screen` and `rename_screen` — showing `Using Opus 5 (1M context) (from .claude/settings.json) · /model`, `/remote-control is active`, `rep:`/`tel:` statusline, `⏵⏵ bypass permissions on (shift+tab to cycle)`. That is precisely the `banner` branch's semantic: *"a Claude session IS visible in `$SPAWN_SURFACE_REF` but no readiness token arrived"* (`:663`).

Round 1 named this capture explicitly and prescribed the fix: *"re-derive the banner anchor from a running-session capture (`rc_confirmation_screen.rc_screen` → `banner.txt`)"*. The amendment neither did it nor recorded a reasoned decline; it asserted the evidence does not exist.

**Measured consequence.** I ran the amended fence in plan order against every live capture:

```
trust_dialog_screen  -> trust-dialog     (correct; the fix works)
rc_screen            -> none             <-- a real running session
rename_screen        -> none             <-- a real running session
read_screen_warm     -> none             (correct)
```

An 8-pattern × 4-screen discrimination matrix:

```
pattern                  rc  rename  trust  warm
bypass permissions        Y     Y      n     n
shift+tab to cycle        Y     Y      n     n
/model                    Y     Y      n     n
Using Opus                Y     Y      n     n
rep: / tel:               Y     Y      n     n
claude code               n     n      Y     n     <-- current anchor: fires ONLY on the trust screen
esc to interrupt          n     n      n     n     <-- current anchor: fires on NOTHING
```

So of the two shipped banner anchors, **`esc to interrupt` matches nothing anywhere in the frozen fixture** (whole-file count 0, with `esc to cancel`→1 and `claude code`→1 as controls on the same instrument), and **`claude code` matches only the screen the branch must never claim** — a false-positive generator that the new ordering pin now (correctly) neutralises, not a detector.

**Calibration on the matrix — do not lift an anchor straight out of it.** Those five patterns discriminate perfectly *across these captures*, but `bypass permissions`, `shift+tab to cycle`, `· /model` and `Using Opus` are **mode- and settings-dependent chrome**: they are present because of how that particular session was configured, not because they are invariant across Claude Code sessions. They are candidates to evaluate, not validated anchors. The point of the matrix is narrower and safer than "here is the fix": measured evidence about the banner case **exists and was not consulted**, and it already falsifies both current anchors. Choosing the replacement — and declaring the residual inference in whatever is chosen — is the implementer's work under Step 3b, not something this review should pre-decide.

**Why this is a blocker and not a nit.**

1. **It commands a false statement into shipped code.** Step 3b tells the implementer to label `banner` INVENTED and "say what would falsify it". The falsifying evidence is already sitting in the frozen fixture and already falsifies it. Writing "no live capture exists" into a code comment is a durable factual error, and it is squarely against the amendment's own new rule at `:647`: *"Measured and inferred are not the same evidence, and a comment that blurs them is worse than no comment."* An amendment must obey the rule it introduces.
2. **It reproduces the antipattern the amendment's own headline decries.** MEDIUM 3's new `test_diagnosis_banner_steers_to_tab_and_omits_manual_block` will be authored against a hand-written `banner.txt` containing `Claude Code v2` (`:559`) — green, while the only real capture of that situation routes to `none`. The dispatch says it at `:47`: *"A fixture authored to match the code under test proves only that you can spell the same string twice."* That is what Step 1 still prescribes for `banner.txt`.
3. **The operator outcome is wrong in the direction the module AC forbids.** AC `:770` requires *"trust-dialog/**banner** instructions steer to the existing tab"*. A real stuck-but-running successor diagnoses `none`, falls to `*)` at `:667`, and gets `print_manual_instructions` — the manual-resume block the trust and banner branches deliberately withhold. Less severe than the trust misroute (the `*)` text does say "check that tab first"), but it is the same failure mode and it is now the *only* remaining one.

**What would close it:** amend Step 1 to derive `banner.txt` from `rc_confirmation_screen.rc_screen` (as round 1 asked), replace or extend the banner anchors with patterns measured against that capture, correct both "no live capture" sentences, and pin the banner diagnosis against the real capture the same way `test_real_trust_capture_diagnoses_trust_not_banner` pins trust. If the controller instead judges `rc_screen` unrepresentative of a *stalled* successor, that is a defensible call — but it must be **written as a reasoned decline with what would falsify it**, not as "no capture exists."

### NEW MEDIUM B — `internal_error` is labelled "no live capture" when `read_screen_cold` **is** its live capture, and the amendment re-opens as an open question a knob round 1 had already located.

Same sentence as BLOCKER A (plan `:647`, dispatch `:67`), separate consequence.

**On the ranking, explicitly:** A is ranked above B on **impact** — it ends in a real operator misroute, B ends in a wrong code comment. B is the higher-**certainty** half: `read_screen_cold` is unarguably the source of the `internal_error` literal, so there is no reading of the fixture under which B's label is correct, whereas a controller could at least argue that `rc_screen` does not represent a *stalled* successor. If only one is accepted, B is the one that cannot be argued with.

`read_screen_cold` is a live capture: `argv: "cmux read-screen --surface surface:77 --scrollback"`, `stderr: "Error: internal_error: Failed to read terminal text\n"`, `exit: 1`. Since `diagnose_target` reads with `2>&1` (`:630`), the `internal_error` literal at `:631` is **derived directly from that measured stderr** — it is the second-best-evidenced anchor in the whole fence. Round 1's LOW 5 named this fixture by key. Step 3b instructs the implementer to mark it INVENTED.

Second half: Step 2 `:596-600` and dispatch 7(b) say *"If a stub knob can separate them, add the second case; if not, SAY SO… An untestable disjunct needs a KNOB, not another assertion."* Round 1 answered this with evidence — the knob already exists. I re-verified against `_CMUX_V2_STUB`: `read-screen)   [ -n "$CMUX_SCREEN_FILE" ] && { cat "$CMUX_SCREEN_FILE"; exit 0; }`. A fifth screen fixture containing `internal_error` yields **rc 0 plus the literal**, separating the two disjuncts with no new knob and no stub change. The amended wording is strictly weaker than the finding it carries and invites an implementer to conclude "no knob → say so" and skip coverage that costs one file.

**Close it by:** stating the answer instead of the question — the knob is `CMUX_SCREEN_FILE` pointed at a file containing `internal_error`; and labelling `internal_error` MEASURED, quoting `read_screen_cold`.

### NEW MEDIUM C — Round 1's BLOCKED and its fixes reached the plan and a report, but **not the register**, breaking this feature's own established precedent.

`git show 5586a9a --stat` shows `deviations.md` is untouched. Task 9's two partner rounds each got a durable register row — `deviations.md:262` ("partner round 1 BLOCKED — FIVE more producer-less obligations…", `Resolved`) and `:264` ("ROUND 2 FOUND FOUR DEFECTS IN ROUND 1's FIXES…", `Resolved`). Task 10's round 1 — which found a whole class of defect (anchors invented against a frozen fixture, shipping green) — has no equivalent row.

This is the lesson already recorded for this feature: a finding that lives only in `reports/` is lost at the module boundary, because `transition-module.py` archives `reports/` while `deviations.md` survives. Controller work, not implementer work, and not a reason on its own to withhold approval — but it should land before Task 10 closes, and it is the fourth obligation source doing exactly what it is there to do.

### NEW LOW D — "`_argv`/`_flag` resolve only the FIRST matching invocation" is imprecise about `_argv`.

Plan `:572-573` and dispatch `:71`. Measured: `_argv` (`test_spawn_handoff_v2.py:818-829`) returns **the whole file, splitlines** — every invocation, concatenated. Only `_flag` (`:832-836`) is first-occurrence (`argv.index(flag)`). The operative instruction (do not reach for `_flag`; parse both `cmux.log` lines) is correct and the trap is real; the attribution is not. An implementer could wrongly conclude `_argv` is unusable here. One clause.

### NEW NIT E — Step 4's sub-items are lettered `(a) (b) (c) (e) (d)`.

`:679`, `:681`, `:683`, `:685`, `:687`. `(e)` was inserted before `(d) Commit`. The dispatch cites "Step 4(e)" and it resolves, so nothing breaks; it just reads as a missing item on a first pass.

---

## Obligation audit — all four sources against the one execution source (the step list)

| Source | Obligation | Carried by dispatch? | Produced by a step? |
|---|---|---|---|
| Write-Scope table (`:47-56`) | 6 writable paths ("same set" → Task 9's row) | Yes, exact, same order | Yes — Step 4(d) |
| Register — row 18 / 263 | trust-preflight DECISION + flip row 18 | Yes (obl. 3) | Yes — Step 4(b) `:681` |
| Register — row 266 | FULL suite, not "both unit files" | Yes (obl. 2) | Yes — Step 4(a) `:679` |
| Register — row 271 | five inline log-readers DECISION | Yes (obl. 4) | Yes — Step 4(c) `:683` |
| Register — row 165 | orphaned fallback workspace ROUTING | Yes (obl. 6) | Yes — Step 4(e) `:685` ← round 1's MEDIUM 4, now closed |
| Register — all other `Pending`/`Open` rows (60, 61, 80, 101, 119, 127, 164, 192, 214, 228, 230, 267, 275) | none name Task 10 (they route to Module 4, Task 13, Task 16, merge, or the post-merge live smoke check) | n/a | n/a |
| Register — partner-round record | *(no row for Task 10 round 1)* | n/a | **No** → NEW MEDIUM C |
| Module AC `:770` | timeout / one re-wait / `diagnosis=` / notify / no "nothing spawned" | Yes | Yes — Step 2 |
| Module AC `:770` | "…/**banner** instructions steer to the existing tab" | Yes | Yes — `:588` ← round 1's MEDIUM 3, closed (but green-against-synthetic: BLOCKER A) |
| Module AC `:772` | FULL unit suite green | Yes (obl. 2) | Yes — Step 4(a) |
| Prose in a step — ROUTING `:549` | trust preflight | Yes | Yes — Step 4(b) |
| Prose in a step — Step 2 `:608` | VERIFY-don't-re-add the import assertion | Yes (obl. 1) | Yes — inside Step 2 |
| Prose in a step — Step 1 `:557` | "add a test asserting the fixture still equals the frozen value" | Yes (`:50`) | Yes — `:581` |
| Prose in a step — Step 1 `:559` | state the synthetic limitation in each file/loader comment | Yes (`:52`) | Yes — inside Step 1, and Step 3b |
| Prose in a step — Step 3 `:645` | (reduced to constraints only — no work commanded) | n/a | n/a — correctly de-fanged |
| Frozen fixture (the declared tiebreaker) | live anchors per diagnosis branch | **trust: yes. banner + `internal_error`: NO — asserted absent** | Step 1/3b prescribe synthetic + a false provenance label → **NEW BLOCKER A / MEDIUM B** |

**No sixth producer-less obligation exists.** Every prose imperative added by the amendment sits inside a checkbox, and all four register rows naming Task 10 now have producing steps. The producer-less class round 1 opened is genuinely closed. What replaced it is a *truth* defect rather than a *routing* defect — and it lives in the one place the amendment declared authoritative.

---

## Drafted and withdrawn (recorded rather than deleted)

- I drafted a finding that Step 4's `(e)`-before-`(d)` lettering had orphaned the commit step. Reading the artifact rather than the letters, `(d) Commit` is present and complete at `:687` and the dispatch's Deliverable §1 commands it. Withdrawn to NIT E.
- I drafted a finding that `picker-error` was also mislabelled. It is not: I found no live capture of a picker error anywhere in `cmux-verb-shapes.json`, and my must-match control on the same instrument fired. `picker-error` is the one anchor the amendment labels correctly — which is why the other two labels stand out.
- I drafted a finding that `test_real_trust_capture_diagnoses_trust_not_banner` might be vacuous (if the banner regex missed the trust screen, ordering could not matter). I measured it: the banner regex **does** match the real trust capture, so the ordering pin is load-bearing and the prescribed positive control (reorder the greps → expect RED) will genuinely go RED. Withdrawn.

---

## Summary

Round 1's routing findings are all genuinely closed, and closed well: Step 3b is a real checkbox, row 165 is routed, the banner-steering test exists, both vacuity traps are named with positive controls attached, and the twin operator message at `:661` was fixed alongside the fence. The trust half of BLOCKER 1 is fixed correctly — I re-derived the anchors from the frozen fixture myself and the amended fence classifies the real capture as `trust-dialog`, with the ordering pin proven non-vacuous. Every number, quotation and count I could check came out true, and the amended plan still clears the mechanical gate (`validate-plan.py`: WARNING, no blockers; Task 10 at 142 lines despite +57).

What blocks is one sentence, repeated identically at four sites, which closes the remaining half of BLOCKER 1 by asserting that evidence does not exist when it is in the same frozen file: `rc_confirmation_screen` is a live running-session capture, `read_screen_cold` is a live `internal_error` capture, and the plan tells the implementer to label both branches as guesses and to hand-author a fixture for the first. That is the same shape as the finding it is fixing — an anchor set that will ship green while disagreeing with the only measurement available.

**BLOCKED**
