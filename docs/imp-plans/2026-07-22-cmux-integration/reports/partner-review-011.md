# Partner Review — Task 11 dispatch (Docs: CLAUDE.md, manifest, BACKLOG N43(D))

**Model:** opus (deviation from `controller-partner-prompt.md`'s "use haiku for cost efficiency" — see note below).
**Rounds:** 2 (round 1 BLOCKED, round 2 after fixes).

> **Model-choice note.** The template recommends haiku because the partner "reads and compares — it doesn't write code."
> That holds for a normal dispatch. This dispatch's entire payload is ~30 line-number-anchored factual claims about a
> 492-line frozen shell script plus four off-script claims, and the partner's assigned job was to re-verify each one at
> source. Haiku is not demonstrably capable of reliable line-number verification at that density, and the partner gate
> has already caught mis-citation twice on this run. Chose capability over cost for a closed-verification task.
> Recorded rather than silently upgraded.

---

## Round 1 — **BLOCKED**

| Check | Verdict |
|---|---|
| Context Completeness | PASS |
| Context Accuracy | PASS |
| Prior Task Awareness | PASS |
| Escalation Check | PASS |
| Architectural Alignment | PASS |
| Pattern Completeness | PASS (one advisory) |
| **Fact-Sheet Verification** | **FAIL — 2 mis-citations out of ~30 claims** |

### Confirmed by the partner (not re-litigated in round 2)

- Exit-3 ladder, all six sites and notify status: `:125` no notify, `:137` notify (at `:134`), `:195` notify (at `:192`),
  `:464` no notify, `:469` no notify, `:491` notify (at `:488`). **CORRECTION 1 verified TRUE** — `:122` is the `cmux ping`
  reachability test itself and nothing between `:122` and `:125` calls `cmux notify`; the "cannot vs. deliberately" split
  is correct.
- Exit-1 sites `:42, :44, :49, :54, :55, :57, :78, :119`; exit-0 sites `:439, :484` — all exact.
- **CORRECTION 2 verified TRUE**: neither log file exists, neither is in the index, `git check-ignore` exits 1 for both
  (= not ignored). "tracked" is an overclaim; "not gitignored" is the honest form.
- Record shapes: outcome `:480-481`, spawn-failed outcome `:486-487`, runtime-picker-failure `:375` — and field 2 there
  is `"$SPAWN_ID"`, **not** the literal `spawn` that `deviations.md:99` reported. The old gap is closed; the fact sheet
  is right to say all three record types carry the uuid.
- `now_iso()` `:64`; `SPAWN_ID` uuid4 `:359`; `cd`/`WORKTREE_ROOT` `:53`/`:55`/`:54`.
- Env vars: `MAX_HOPS` default 3 `:20`; `QUOTA_TIMEOUT` default 60 `:152-153` with regex `:154`; `QUOTA_TOOL_DEFAULT` `:32`.
- `FORWARDED` sites `:217`, `:278`, `:308`, `:342` — all four exact. `/bin/bash --version` → 3.2.57(1); append syntax 3.1+.
- Append-prompt path `:218-219`, no reaper anywhere in the script.
- Off-script four: repo-2 is its own git toplevel with `verify-install.sh`/`VENDOR.md`/`sync-cmux-skills.sh`/`skills/`;
  `grep -c 'spawn-handoff' tests/ARaymond-hook-baseline/baseline.txt` → `0`; `readlink ~/.claude/skills/superpowers` →
  the main checkout; `--focus false` at `cmux-workspace/SKILL.md:48` and the convention at `README.md:37`.
- Also: `CLAUDE.md` has 0 cmux mentions; BACKLOG N43 `:90` is `done-pending-merge` with the exact merge-annotation
  phrasing; N51 `:98` is `blocked`; script is 492 lines; e2e banner reads 15 steps (`sdd-e2e-test.sh:728`).

### Partner's positive controls (two, both returned non-"confirmed")

1. Deliberately asserted `now_iso()` at `:65`; `sed -n '65p'` returned a non-matching line while `grep -n` returned `:64`
   — the method detects one-line drift. It also independently returned FAIL on the two real errors below.
2. Ran both arms of the bash claim: `/bin/bash -c 'set -u; A=(); echo "${A[*]}"'` → `A[*]: unbound variable`; without
   `set -u` → `[]`.

### Findings (all three independently re-verified by the controller before acceptance)

1. **Intent record mis-cited at `:475`; it is at `:466`.** `:475` is a comment line. Controller re-verified:
   `grep -n 'intent hop='` → `466`. **Controller error.** Fixed.
2. **`SUPERPOWERS_CMUX_QUOTA_MIN_PCT` citations off by one.** Actual: `QUOTA_MIN_PCT_DEFAULT=15` at `:25`, env read at
   `:26`, regex at `:27` (`:24` is the tail of a comment block). Controller re-verified with `sed -n '24,27p' | cat -n`.
   **Controller error.** Fixed. (Adjacent `_TIMEOUT` citations were exact — an isolated miscount, not a systematic offset.)
3. **"component A" is overloaded and would make N43's own row self-contradictory.** Plan Step 3 (`module-2:454`) says to
   "note component A (vendored cmux skills) shipped alongside", but the target row `BACKLOG.md:90` already uses that
   letter for something else — "**Scope = spine only (component A)**" and "**Shipped (component A, spine)**", where
   N43's A is the context-pressure-gate spine. This feature's A-lettering is local to `spec.md:6` / `spec.md:181`
   ("Component A — cmux-custom-skills repo"). Controller re-verified all four citations. **This is a genuine plan
   defect — the fifth factual defect found in this plan's prose this run.** Fixed by adding CORRECTION 3 to the fact
   sheet instructing the implementer to drop the bare letter and name the thing.
4. *(Advisory, controller-side.)* Module acceptance criterion `module-2-protocol-e2e-docs.md:76` (test-debt sweep) is
   still `- [ ]` though Tasks 7–8 are done; the plan file is outside Task 11's write scope, so the controller must tick
   it before the pre-completion checkbox gate. **Controller action: verified the underlying evidence rather than the
   claim** — Task 7's report carries a 7-mutation table across 5 tests with pasted RED assertion text, Task 8's carries
   9 mutations all RED, and the controller independently re-ran Task 7's M3. Criterion 76 is satisfied *on evidence*,
   not on report prose. Ticked with that rationale.

*Advisory also raised:* no pattern reference for the customization manifest's own section conventions — the one target
with no stated house style. Addressed by a new Pattern References bullet telling the implementer to derive the shape
from the file and not invent a new entry format.

### Controller fixes applied before round 2

1. `:475` → `:466`.
2. `QUOTA_MIN_PCT` → `:25` / `:26` / `:27`.
3. Added **CORRECTION 3** (component-A disambiguation) to the fact sheet.
4. Added the customization-manifest house-style bullet to Pattern References.

---

## Round 2 — **BLOCKED** (three further findings, all controller errors)

Edits 1–2 verified landed with **no collateral drift** — the partner re-diffed every other citation in the fact sheet
against its round-1 verified set and found all byte-identical. **CORRECTION 3 verified PASS on every assertion:** both
quoted strings exist verbatim at `BACKLOG.md:90` (`grep -o`); N43's B/C/D are as stated, so **D means the same thing in
both lexicons** and the instruction correctly disambiguates only A; `spec.md:6` and the `spec.md:181` heading confirmed.
Edit 4 judged adequate.

### Findings (all three independently re-verified by the controller)

1. **Stale test count with a live propagation path.** Dispatch said "58-test unit suite" — true as Module-1 history,
   false as a current figure. Controller reproduced: **`72 passed`** across **61 test functions**
   (`.venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -q`). This mattered because the customization manifest
   records per-file counts as a standing convention (`test_transition_module.py` (13 total), `test_c2_integration_gate.py`
   (22), …), so Step 2 would have asked the implementer for a number the dispatch had pre-blessed wrongly.
   **Second surface, found by pulling the same thread — two count-bearing lines are stale because of THIS feature's work:**
   - `docs/ARaymond-customization-manifest.md:389` — "Current real counts (2026-07-07…): unit **509** · e2e **13 steps** …".
     Task 10 took the e2e to **15** (`sdd-e2e-test.sh:728`); the unit total moved with Tasks 7–8.
   - `CLAUDE.md:128` — the e2e Testing bullet still reads "banner step count 13→14".

   `manifest:389` names `CLAUDE.md` "Testing" as *the authoritative running counts*, so left alone these would contradict
   each other **and** the code. Both files are in Task 11's write scope. Resolved into the dispatch rather than left to
   implementer guesswork. **Scope ruling (partner-endorsed round 3): defensible, not creep** — `CLAUDE.md:19`
   ("Documentation Maintenance") makes count accuracy an obligation of any production-deployable update; the `13→14`
   staleness is Task 10's collateral and Task 10's write scope was `sdd-e2e-test.sh` alone, so **Task 11 is the only task
   in this plan that can land it**; and it falls inside acceptance criterion `:81`.
2. **Header still read "TWO CORRECTIONS" after a third was added.** Cosmetic — cannot reach `CLAUDE.md` — but a stale
   internal count in the one document whose thesis is that every number was verified. Fixed.
3. **A date true in a source the implementer cannot check.** CORRECTION 3 said N43's spine "shipped 2026-07-15" — the
   controller's recollection of the *merge* date. The repo consistently says **2026-07-14** (`CLAUDE.md:216`,
   `BACKLOG.md:90`, the feature-dir name); 07-15 appears nowhere. Written next to the existing N43 section the two dates
   would have disagreed **in the same file**. Date dropped entirely ("already shipped") rather than corrected — it
   carried no weight for the instruction.

### Controller fixes applied before round 3

1. Header "TWO CORRECTIONS" → "THREE CORRECTIONS".
2. CORRECTION 3: "(shipped 2026-07-15)" → "(already shipped)".
3. Context section: "58-test unit suite" reframed as end-of-Module-1 history, with a pointer forward.
4. **New:** a "Test counts — derive them, never copy them" block in the fact sheet, carrying the two stale-line refreshes
   and the rule *if a count you observe disagrees with a doc, the run wins — and say so.*

---

## Round 3 — **APPROVED**

Scoped deliberately to the ~20 lines of **new controller-authored fix text**, on the Task-9 precedent that a fix round
can close two findings and introduce its own false claim. Rounds 1–2 findings were treated as settled and not re-checked.

- **Every factual assertion in the new block — PASS.** 72/61 reproduced; the per-file count convention real and correctly
  characterized (both cited exemplars verbatim); `manifest:389` quoted accurately including its "authoritative running
  counts" tail; `CLAUDE.md:128` confirmed as the e2e bullet still carrying "13→14"; `CLAUDE.md:19` confirmed to read
  "Run both test suites to verify the documented check counts are still accurate".
- **Scope call — defensible, not creep.** Reasoning recorded under finding 1 above.
- **"Leave the per-feature narrative rows below untouched" — faithful** to what `:389` says about itself.
- **No contradictions** with rounds 1–2; no citation elsewhere in the fact sheet moved.

**One observation, no action required — acted on anyway.** The partner noted that the new block's phrase "`:389`
*explicitly says* … which is precisely why the header line **is** the one that must stay current" splits a source
statement from a controller inference: `:389` does say the rows below are not updated in place, but the conclusion about
its *own* header is the controller's reasoning, not the source's. That is the same attribute-to-the-wrong-source class
this review has caught three times, so it was fixed rather than waved through: the block now separates what `:389`
states from the inference, and labels the inference as such.

**Verdict: the dispatch is ready to send.**

---

## Tally

**Three rounds. Six blocking findings, all controller errors**, plus one genuine plan defect (the "component A" collision
— the fifth factual defect found in this plan's prose this run) and two advisories, both acted on. The partner ran two
positive controls and independently re-verified ~30 line-anchored claims; the controller independently re-verified every
finding before accepting it rather than taking the reviewer's word.

