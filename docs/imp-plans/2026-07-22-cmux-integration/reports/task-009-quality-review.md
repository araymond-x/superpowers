# Code Quality Review — Task 9 (Rewrite context-handoff-protocol.md steps 3–5)

**Reviewer:** dispatched adversarial code quality reviewer (sonnet), round 1
**Range reviewed:** `fdfef9b..f787039`
**Output budget given:** 800–1400 words
**Returned assessment: PASS** — but with **two Important findings**, one Minor, and one `[NEEDS_CONTEXT]`.

**Controller framing given to this reviewer:** it was told it is the gate that pays (a real defect found on Tasks 6, 7
and 8, each time after a PASSing spec review), told explicitly NOT to re-confirm what the spec review already
established, and given a prose analogue of mutation testing: for each sentence, ask what a reader does wrong if it were
deleted, what the most plausible WRONG reading produces, and which reachable script behavior has no instruction. It was
also warned about the run's recurring conjunction-trap defect class and told not to manufacture findings.

---

## Reviewer output (verbatim, as returned)

**Strengths:**
Steps 3–5 accurately mirror the frozen script's real behavior: the precondition order stated in step 4's prose (clean tree → bundle validate → cmux reachable → hop limit → quota → spawn) matches the script's actual sequence at lines 76–198, 442+. Both authorized deviations (five-cause exit-3 enumeration; the corrected picker-manual notification claim) are independently confirmed true against the script and honestly logged in `deviations.md` rows 69–70 — I re-derived both from the script myself and got the same result the implementer and spec reviewer reported: `:429`'s notify body is mode-agnostic, and `picker-manual` composes a plain interactive `claude-picker $PICKUP_ARG` with no `--non-interactive`. Steps 1–2 and the "Why a block"/"A soft nudge" paragraphs are verified byte-identical (`git status --short` on the target file is clean). No dead or contradicted content from the rewrite.

**Issues:**

- **Important:** `context-handoff-protocol.md:36` — Step 4's exit-0 instruction is "Report the workspace ref and launch mode... Nothing more to do here," but nothing explicitly directs the controller to *relay the action* to the human when `launch=picker-manual`. The script's own `cmux notify` (`:429`) is mode-agnostic and never says "go finish the picker" (confirmed by both reviews). The parenthetical defines what `picker-manual` *means*, but the verb is "report the mode," not "tell the user they must act" — contrast this with the adjacent Exit-3 bullet at line 41, which explicitly says "**Relay** the manual resume instructions." That asymmetry (explicit relay-imperative for exit-3, none for the exit-0/picker-manual sub-case) reads as an authorial oversight, not a deliberate omission. Failure scenario: controller reports "spawned in workspace:8 (launch=picker-manual)" verbatim without adding "go complete the interactive picker there," and no other channel informs the human — the successor sits at the picker prompt indefinitely, which is exactly the "stuck session" class this doc exists to prevent. Fix: add an explicit imperative, e.g. "...and if `picker-manual`, tell the user to go complete the picker in that workspace before pickup runs."

- **Important:** `context-handoff-protocol.md:19` (unchanged) × `:39` (new) interaction — Step 2's scope, "the completed task's code, its reports under `reports/`," was never load-bearing before this rewrite (the old steps 3–5 had no automated clean-tree check). New step 4 makes it load-bearing: `spawn-handoff-session.sh` Precondition 1 (`:76-78`) hard-refuses on ANY `git status --porcelain` output. Per the hook's Check 5c/5d architecture, `reports/checkpoint-pre-dispatch-N.json` and `reports/partner-review-N.md` for the *blocked* task N are written to `reports/` *before* the implementer dispatch attempt that trips the context gate — they are not "the completed task's" (N-1's) reports. Live evidence in this very worktree: `checkpoint-pre-dispatch-009.json` and `partner-review-009.md` currently sit untracked in `reports/` while task 9's code is already committed — the identical pattern, just pre-existing rather than post-block. A controller reading step 2 narrowly, commits only N-1's artifacts, then runs step 4 and gets exit 1 ("worktree not clean — commit pending state first (protocol step 2)"), pointing back to the same ambiguous step 2. This is self-correcting (`git status` immediately reveals the untracked files) rather than a true infinite loop, so I'm not rating it Critical, but it's a real, mechanically-verified round-trip cost the doc could close with one clause: "commit all of `reports/`, including pre-dispatch bookkeeping for the now-blocked task."

- **Minor:** `context-handoff-protocol.md:55` and `:58-61` — "A soft nudge" (unchanged) and the new "Soft-nudge use" paragraph both assert, almost verbatim, that "handing off at the nudge is preferred to waiting for the block." Not contradictory, just redundant — two adjacent paragraphs restating the same preference. Consider merging the new paragraph's script-invocation guidance ("build the bundle early... run the script... at the nudge") into the existing "A soft nudge" paragraph rather than appending a near-duplicate.

- **[NEEDS_CONTEXT]:** Step 3 invokes the `handoff` skill (external to this repo — a personal skill, not `skills/handoff-acceptance`). If it writes any artifact into the *current repo's working tree* (rather than only `~/.claude-codex-handoff/`), that write would dirty the tree between step 2's commit and step 4's clean-tree check, causing exit 1 on the very first run regardless of how step 2 is read. I did not read the `handoff` skill's instructions (out of this diff's scope and outside my read-only investigation budget) — this would settle by inspecting what `/handoff` actually touches inside a repo checkout.

**Mutation/omission analysis:** Deleting the exit-3 "Relay the manual resume instructions" clause would leave a reader with only a printed script message and no explicit direction to act on it — the doc catches this case correctly. Deleting the equivalent-but-absent imperative for exit-0/picker-manual is the actual state of the doc today, which is the Important finding above. Reading "commit... its reports under `reports/`" in the most plausible wrong way (scoped strictly to N-1) produces the dirty-tree round-trip described above; the script's `git status --porcelain` check and explicit exit-1 message make this self-limiting rather than catastrophic. I checked one plausible false lead and ruled it out: the installed-path-vs-worktree resolution gotcha (CLAUDE.md's documented main-checkout resolution) is *by design* — the protocol doc describes steady-state, post-merge behavior where the installed path is canonical regardless of which branch is checked out; it's correctly out of scope for this doc and is already tracked separately (Task 10's e2e Step 14 comment, spec §7).

**Files mutated and restored (if any):** None. All verification was read-only (`grep`, `Read`, `git status --short`, `git log`); I did not edit or execute `spawn-handoff-session.sh`.

**Assessment:** PASS

---

## Controller disposition

**The reviewer returned PASS, but the controller is NOT accepting that as "done."** Two Important findings describe
concrete paths to the two failure modes this entire feature exists to eliminate — a stuck session and a wasted
round-trip at handoff time. "PASS with Important findings" is not a licence to move on; the skill requires resolving
open review issues before the next task. **A fix round is dispatched.** Disposition per finding:

### Finding 1 (Important) — exit-0/picker-manual has no relay imperative → **FIXING**

**Accepted, and independently verified before acting.** The asymmetry is real and the controller confirmed each premise
rather than accepting the reviewer's chain:
- The exit-3 bullet does say "**Relay** the manual resume instructions the script printed." The exit-0 bullet says only
  "Report the workspace ref and launch mode … Nothing more to do here." CONFIRMED by reading the committed file.
- The success-path notify body is mode-agnostic (`:429` template from `:473`) and never mentions a picker. Already
  established twice this task; that is precisely *why* the doc must carry the instruction — there is no other channel.
- In `picker-manual`, `SUCCESSOR_CMD="claude-picker $PICKUP_ARG"` (`:377`) with no `--non-interactive`, so the successor
  genuinely blocks on human input.

**This is the sharpest finding of the task and it is the same shape as the run's recurring defect class.** The
parenthetical *defines* `picker-manual` correctly, so the bullet **looks** like it covers the case — but the operative
verb is "report the mode," and it is immediately followed by "Nothing more to do here," which actively discourages the
one action that matters. Definition standing in for instruction is the prose form of the conjunction trap: one property
(the reader *could* infer the need) satisfies the appearance of another (the reader is *told* to act). Under the most
plausible reading, a context-exhausted controller prints `launch=picker-manual` and stops, and the successor waits at a
picker nobody knows about.

### Finding 2 (Important) — step 2's scope vs. the new clean-tree precondition → **FIXING, but NOT where the reviewer suggested**

**Accepted as a real defect; the suggested fix location is unavailable.** The reviewer proposed amending step 2. **Step 2
is protected**: the plan states "Steps 1–2 stay byte-identical," and the module's Acceptance Criteria pin it —
"`context-handoff-protocol.md` steps 1–2 are byte-identical to the original." Editing step 2 would trade this defect
for an acceptance-criterion violation.

The fix therefore lands in the **exit-1 bullet**, which Task 9 owns outright: it names the blocked task's own
pre-dispatch bookkeeping as the usual dirty-tree cause and points back at step 2's existing "reports under `reports/`"
scope, making the narrow reading unavailable without altering a byte of step 2. Same defect closed, no criterion broken.

The reviewer's evidence here deserves credit: it used **live state in this very worktree** as its positive control —
`checkpoint-pre-dispatch-009.json` and `partner-review-009.md` are untracked in `reports/` right now while Task 9's code
is committed, the exact pattern it predicted. That is an empirical demonstration, not a hypothetical.

### Finding 3 (Minor) — redundancy between "A soft nudge" and the appended "Soft-nudge use" note → **RATIFIED AS-IS, no change**

The observation is accurate: the two adjacent paragraphs restate the same preference. **But the plan explicitly
prescribes exactly this shape** — "Keep the 'Why a block' and 'A soft nudge' paragraphs, and append the closing note" —
and gives the note's text verbatim. Merging them would delete plan-mandated structure to save four lines of prose, in a
doc whose reader is by construction a context-exhausted agent for whom mild repetition is a feature. Choosing
plan fidelity over concision here is a deliberate call, recorded rather than silently ignored. No residual work, so no
checkbox is owed.

### Finding 4 `[NEEDS_CONTEXT]` — does `/handoff` dirty the repo tree? → **RESOLVED BY THE CONTROLLER: it does not. No defect.**

The reviewer correctly declined to guess and named exactly what would settle it. The controller settled it by reading
`~/.claude/bin/claude-codex-handoff`:
- `DEFAULT_ROOT = Path.home() / ".claude-codex-handoff"` (`:22`); `bundle_dir = root/bundles/<id>` (`:863-869`).
- **Every** write target resolves under `bundle_dir` — `manifest.json`, `CONTINUE.md`, and all `artifacts/*` at
  `:964-987`, `findings.md` at `:1196`, the `latest` pointer at `:706-717`, and both artifact copiers, whose
  destinations are `bundle_dir/artifacts/included` (`:733`) and `bundle_dir/artifacts/changed-files` (`:784`).
- The repo is touched **read-only**: `run_git` (`:95-99`) and `capture_repo_state` (`:180`) shell out to `git` for
  state; `copy_path` reads *from* the repo *into* the bundle.
- **Positive control:** the grep surfaced 28 distinct write/copy/mkdir sites, so the search was not blind — and all of
  them land under `bundle_dir`. Corroborating: the bundle this session resumed from exists at
  `~/.claude-codex-handoff/bundles/2026-07-25T02-12-19Z-cmux-integration`, and `git ls-files` matches nothing
  handoff-shaped inside the repo.

Had this gone the other way it would have been a **Critical** — step 4 would exit 1 on its first run in every session,
making the whole wiring inoperative. It is worth stating that the finding was valuable *because* it was raised as
unsettled rather than guessed in either direction.

**Round 1 outcome: fix round dispatched for Findings 1 and 2. Findings 3 and 4 closed with no code change.**

---
---

# Round 2 — Code Quality RE-REVIEW (after fix round A, `2fe7a50`)

**Reviewer:** dispatched adversarial quality reviewer (sonnet), round 2
**Range reviewed:** fix diff `f787039..2fe7a50`; whole task `fdfef9b..2fe7a50`
**Output budget given:** 600–1000 words
**Returned assessment: PASS** — both Important findings CLOSED, fix location judged SOUND, **one honesty caveat raised about text the controller authored.**

The reviewer was explicitly told the controller had relocated Finding 2's fix away from where round 1 suggested, was
asked to verify the byte-identical acceptance criterion actually exists, and was told to **say plainly if it thought the
relocation dodged the defect rather than closing it.** It was also told not to manufacture round-2 findings just because
round 1 found real ones.

## Reviewer output (verbatim, as returned)

**Finding 1 — closed?** CLOSED — Mutation probe: deleting the new sentence ("**If `picker-manual`, tell the user in so many words…** — the notification will not tell them.") leaves exactly the round-1 text ("...does not name the mode). Otherwise nothing more to do here.") — that reversion is the bug that was found, so the sentence is load-bearing, not cosmetic. Wrong-reading probe: the new text reads "…notification will not tell them. **Otherwise** nothing more to do here." The "Otherwise" now explicitly scopes "nothing more to do" to the non-`picker-manual` (auto) case — a reader in the `picker-manual` branch cannot reach "nothing to do" without stepping past an imperative sentence that says the opposite. This is a genuine instruction (imperative mood, names the actor "the user," names the consequence "successor never starts"), not a restated definition — it passes the round-1 defect-class test the dispatch asked me to apply.

**Finding 2 — closed?** CLOSED, with one honesty caveat worth surfacing — The exit-1 bullet now explicitly says: "commit all of `reports/`, not just the last completed task's files," and names the two concrete filenames (`checkpoint-pre-dispatch-NNN.json`, `partner-review-NNN.md`). That instruction is unambiguous on its own — a reader hitting exit 1 no longer needs to correctly parse step 2 at all, because the correction is delivered inline. Read literally, though, the preceding clause "Step 2 covers them" overstates what step 2 (unchanged, verified below) actually says: "Ensure **the completed task's** code, **its** reports under `reports/`…" — "its" possessively ties "reports" back to "the completed task," i.e. N-1, not to the blocked task N whose bookkeeping is the actual dirty-tree cause. So "Step 2 covers them" is a generous, not strictly honest, characterization of step 2's grammar. It doesn't matter in practice — the very next clause overrides it with the correct action regardless of how the reader parsed step 2 — but I'm flagging it because you asked me to say so if the cross-reference wasn't honest, and this one is optimistic rather than accurate.

**Fix-location judgment (Finding 2):** SOUND — `grep -n 'byte-identical'` confirms the constraint is real: module-2-protocol-e2e-docs.md:78 ("steps 1–2 are byte-identical to the original") and :221 ("Steps 1–2 stay byte-identical"). Given that constraint, relocating the fix to the exit-1 bullet is not a dodge: it delivers the same corrective content at the point the reader actually needs it (when the script has already told them the tree is dirty), colocated with the concrete filenames step 2 could never have named generically. This is at least as good a location as step 2 would have been, not a weaker substitute.

**New issues introduced by the fix round:** None found.

**Verified independently:**
- Exactly one file changed, `fdfef9b..2fe7a50` → `git diff --name-only` → CONFIRMED (single line of output: `context-handoff-protocol.md`).
- Frozen files untouched (`spawn-handoff-session.sh`, `sdd-pre-dispatch-hook.sh`, `tests/ARaymond-hook-baseline/baseline.txt`) → `git diff fdfef9b..2fe7a50 --stat` scoped to those three paths → CONFIRMED (empty output).
- Steps 1–2 byte-identical → two checks: (a) `git diff fdfef9b..2fe7a50` on the target file — the diff's first hunk header is `@@ -19,15 +19,37 @@`, meaning every line before old-line 19 (all of steps 1–2) is untouched across the *entire* task, not just the fix round; (b) **positive control**: diffed lines 1–20 of `fdfef9b`'s copy against lines 1–20 of the current file with plain `diff` — before trusting a "no difference" result I confirmed the same command correctly reports a difference when run on the whole file (it does, showing the step-3–5 hunk), then narrowed to 1–20 and got no output → CONFIRMED.
- Exit-3 bullet unchanged → visible directly in the diff: the `- **Exit 3**...` lines appear only as unmodified context, never as a `-`/`+` pair → CONFIRMED.
- Line-wrap discipline held → `awk '{print length}'` over the new lines: max 80 chars (lines 40, 64), consistent with the pre-existing file's range (up to 83–85 for unrelated existing lines, 105 for the one code-block command line which is expected to be unwrapped) → CONFIRMED.
- Finding 4 (`/handoff` repo-dirtying): taken on trust from the controller's disposition — not independently re-verified against `~/.claude/bin/claude-codex-handoff`; the dispatch said not to spend budget on it and I didn't. NOT CHECKED (deliberately, per instructions).
- Regression suite `159/0/2`: taken on trust per the dispatch's instruction not to re-run it. NOT CHECKED.

**Files mutated and restored:** none — all verification was read-only (`git diff`, `git show`, `sed`, `awk`, `grep`). `git status --short` on the four files of interest (target file + three frozen files) shows no changes attributable to this review; the pre-existing untracked/modified SDD bookkeeping files in `docs/imp-plans/2026-07-22-cmux-integration/reports/` and `deviations.md`/`module-2-protocol-e2e-docs.md` predate this review session (they are task 9's own in-flight artifacts) and were not touched by me.

**Assessment:** PASS

## Controller disposition of round 2

**PASS accepted for Findings 1 and 2. The honesty caveat was FIXED, not accepted** — see fix round B (`19096af`).

**The caveat is the most valuable thing in this round, and it was aimed at the controller's own text.** Round A's fix
introduced the sentence "Step 2 covers them." The controller verified step 2's exact wording (`sed -n '18,21p'`):
"Ensure the completed task's code, **its** reports under `reports/`…". The possessive binds to *the completed task*, so
the claim was **false**.

The re-reviewer noted it "doesn't matter in practice" because the next clause supplies the correct action anyway. The
controller fixed it regardless, for a reason specific to this task: **Task 9 exists in part to correct a false claim the
plan made** about what the spawn notification says. Correcting the plan's false claim and then shipping the controller's
own false claim in the same file would apply two different standards to the same kind of error. Round B replaced it with
an accurate characterization — which also reads as better guidance, since it names the narrow reading of step 2 as the
trap instead of asserting step 2 already handles it.

Two further notes on this round:

1. **The fix-location challenge was answered at the source, not deferred.** The controller asked to be told plainly if
   relocating Finding 2's fix out of step 2 was a dodge. The reviewer went and confirmed the byte-identical criterion
   exists at two independent sites in the plan (`:78` Acceptance Criteria and `:221` Step 2 instruction) before judging
   it SOUND. That is the difference between ratifying a controller's rationale and checking it.
2. **The reviewer named exactly what it did NOT verify** — Finding 4's `/handoff` disposition and the regression-suite
   numbers, both of which the dispatch told it to skip. Declaring "NOT CHECKED (deliberately, per instructions)" rather
   than quietly implying coverage is the standard this run requires; the controller had already verified both directly.

# Round 3 — verification of fix round B (`19096af`)

No further reviewer dispatch. Round B changed **one sentence-and-a-half inside a single bullet** to remove a false
statement; it added no behavior, no new claim about the script, and no new instruction. The controller verified it
directly:

- `git diff 2fe7a50..19096af` → a single hunk at `@@ -48,8 +48,9 @@`, exit-1 bullet only. Exit-0 and exit-3 bullets
  appear as unmodified context.
- `git diff --name-only fdfef9b..19096af` → **exactly one file** across all three Task 9 commits.
- Same scoped to the three frozen paths → **empty**.
- Steps 1–2 byte-identical, **with the lines-1–40 positive control confirming the comparison is not blind**.
- `validate-all-skills.py` run by the controller: **`PASS: 159  FAIL: 0  WARNING: 2`**, matching the pre-task baseline.

**Task 9 final state: PASS.** Spec review PASS (round 1). Quality review PASS with 2 Important findings → fix round A →
re-review PASS with 1 honesty caveat → fix round B → controller-verified. Exit ladder unchanged (0/3/1), steps 1–2
byte-identical, `spawn-handoff-session.sh` freeze intact.
