# Task 1 — Adversarial Code-Quality Re-Review (Round 3)

**Verdict: APPROVED**

Reviewed `a71dfba` (implementer, 2 files) + `24661a9` (controller: report, deviations register) against `48322a9`, on `cmux 0.64.20 (100) [14e3400b9]` — re-pinned live (`cmux --version` exact match, `cmux ping` → `PONG`).

All six round-2 findings are closed, verified by my own execution rather than by reading the fix report. The BLOCKING finding was closed **better than asked**: the implementer's occurrence sweep found five sites where the review named three, corrected the two it owned plus the one the review named, and the controller closed the fourth (`deviations.md`) in the same window — I confirmed both halves independently. One MINOR completeness gap survives in `N76`; it is incomplete rather than false, sits at a site the round-2 review did not name, and does not justify a round 4. It needs an owner, not another round — see the disposition at the end.

---

## Do NOT redo these — verified closed this round

- **All three mechanical gates re-run against the committed tree, not read from the report.** Pipe counts: header **8**, N67 **8**, N76 **8**, controls N72/N75/N51 **8**; N54 **9** and N57 **11**, neither fixed nor propagated (add/remove count **0**). BACKLOG hunks exactly two: `@@ -114` (N67), `@@ -123` (N76). `a71dfba` touches exactly the two in-scope files.
- **Axis 4 independently re-derived** on the live binary: `command count = 127`, `ENV-FLAG: new-workspace` — the only hit.
- **Two of the three reviewer-sourced imports were independently re-derived by me, and the third read verbatim.** All seven alternation siblings (`enable-browser`, `browser-status`, `logout`, `previous-window`, `last-window`, `unbind-key`, `copy-mode`) → exit 0, zero `--env`. The full `cmux rpc` param table reproduces exactly, including the `workspace_id`-honored / `workspaceId`-ignored split. `cmux ssh --help` prose is verbatim, zero `env` mentions. **The provenance labels are not merely present — they are accurate.** A round 4 must not re-verify these.
- **H2 / H3 byte-identical** to live `--help` (29 and 26 lines, `diff` → empty).
- **Flip condition: clean non-regression.** The N76 flip-condition clause is **byte-identical** to `48322a9` (957 chars), as is N76's methodology-note tail (1860 chars) and N67's pre-`UPDATE` prefix (1931 chars). The doc's flip-condition blockquote is untouched; the only §Disposition edit was NEW-4's qualifier in the downstream branch summary, which makes it strictly more accurate.
- **Fence hygiene**: 52 markers, balanced, closed at EOF, **zero** left/up-arrow annotations inside any fence (blockquote-aware scan).
- **`verify-symlink-install.sh` → 104 passed, 0 failed, 0 warnings.**
- **Repo-wide inference sweep**: no live assertion of the withdrawn inference survives anywhere. Hits are the doc's deliberate self-disavowal, `deviations.md` row 64 (corrected in place), row 68 (the finding record), the round-2 review itself, and `task-001-fix-implementer-report.md` — immutable, correctly acknowledged in Concerns 1.

---

## Per-finding disposition

### NEW-1 (BLOCKING) → **CLOSED**

**Completeness — occurrence set reconstructed independently.** I swept the doc, `BACKLOG.md` and `deviations.md` for `never recorded | not merely unexported | third leg | consumed and discard | discarded`, plus a `\bthird (leg|observation|signal)\b` pass and a repo-wide `--include='*.md'` pass, then read §Step E, §Disposition, §"What could not be established" and the Bottom line in full rather than trusting grep. **No assertion of "never recorded / not merely unexported / consumed and discarded" survives as a live claim anywhere.**

**Correctness.** The replacement claim is true and strictly narrower. Step B proves the configured view *does* report workspace-level configured keys; SP2_SURF's absence after `new-surface --env SP2_SURF=gamma` therefore does rule out a covert workspace-env setter — and nothing more. The non-adjudication statement is correct and correctly hedged: the implementer changed a first draft's "by construction" to "as measured", which is the right call, since implementation knowledge was not available.

**Cross-reference — a determination, not a nit.** The brief asked whether it works in both directions. **It does not.** §"Per-surface env channels" carries **zero** occurrences of "Step C", "§Step" or "Re-capture" — the link is one-directional, Step C → layout finding. The fix report's self-review claim that they "now cite each other in both directions" is **inaccurate as written**. But one-directional is **sufficient**, because the risk is asymmetric: the reader in danger of over-reading silence is standing in Step C, and Step C is the end that carries the pointer. Nothing in the layout section asserts anything about `new-surface --env`. Recorded as a report-accuracy slip, not a defect in the durable artifact.

**Controller-owned half.** `deviations.md` row 64 now states the true observation, marks `[CORRECTED round 3, controller-owned half of NEW-1]` in place, quotes the withdrawn wording only inside an explicit withdrawal, and names Step D as what carries the conclusion. **A reader cannot quote the withdrawn inference as live** — every surviving instance of the phrase in that row is inside the disavowal. Two register rows record the round-3 outcome and this ownership split.

**N76 read end to end, cold.** The self-contradiction NEW-1 item 2 was filed for is genuinely gone: clause (1) now *cites* clause (3) as the reason the configured view cannot adjudicate, and the row's closing "Consequence: … shows no layout per-surface env — never treat the configured view as ground truth" is now consistent with rather than a refutation of clause (1).

### NEW-2 (IMPORTANT) → **CLOSED in the doc; see MINOR-1 for N76**

The `workspace`-key-ignored statement is accurate — I reproduced the whole table read-only: `{}`, `{"workspace":"workspace:2"}`, `{"workspace":"workspace:9999"}`, `{"workspace":"totally-bogus-not-a-ref"}` all return `workspace_ref: workspace:42` today; `{"workspace_id":"<uuid>"}` returns `workspace:2`; `{"workspaceId":"<uuid>"}` is ignored; a bogus extra param yields a byte-identical payload. It is provenance-labeled as round-2-reviewer-measured. The doc **correctly declines to assert a mechanism** for the volatile no-param default, and correctly declines to import the reviewer's stronger "not the caller's workspace" claim — which its own transcript (showing the caller's workspace as that session's default) would have contradicted. That restraint is the right call.

The residual is upgraded at **both doc sites** — §Axis 3's bullet ("requires **three** things, not two") and §"What could not be established" item 1 — each naming the param-name obstacle, the silent-failure indistinguishability, and the CLI-vs-RPC vocabulary divergence, and each framing it as *strengthening* do-not-adopt. Option 1 was foreclosed by the docs-only constraint; option 2 shipped, as instructed. **Not filed:** "you never ran the honored form."

### NEW-3 (MINOR) → **CLOSED**

Scope limit 3 present, naming the extraction artifact, all seven collapsed siblings, and the reviewer-sourced provenance. Every "all 127" phrasing qualified: §Axis 4 headline ("127 probed command *names*" + parenthetical), Bottom line item 3, doc deviations row 10, N76 Residual. §Disposition's "the 127-verb sweep in §Axis 4" was deliberately left — it cites the section that now carries the limit. Correct.

### NEW-4 (MINOR) → **CLOSED**

Branch summary now reads "no env channel any *documented CLI verb* reaches". The other branch needed no qualifier.

### NEW-5 (MINOR) → **CLOSED**

N67's UPDATE now names the `new-workspace`-only re-capture (`workspace:41` / `surface:107`), marks `workspace create`'s inherited-process half as resting solely on the first session's un-re-verifiable capture, and states that only the evidence *label* was wrong. Matches §Step E exactly.

### NEW-6 (MINOR) → **CLOSED**

Heading retitled; the SSH half disposed of as a **negative** claim at declared a-help strength, with the reviewer-sourced label spelling out that the prose was read and `cmux ssh` was not run. I confirmed the quoted prose verbatim and zero `env` mentions. Bottom line item 3's cross-reference updated to match. The self-review's account of correcting a first draft's unearned *positive* claim ("creation-time only") into the measured negative one is exactly the discipline this round existed to install.

### Provenance integrity → **SOUND, in both directions**

Three reviewer-sourced data, three explicit labels, all accurate. **No downgrade either:** keeping **a-run** on §Axis 2's `SP2_SURF`-absent observation is **right**. Provenance tracks who measured the datum, not whether the inference drawn from it was sound; the datum is the doc's own Step C capture. Downgrading it would have been a second error, symmetric with laundering.

---

## New findings

### MINOR-1 — N76's Residual still understates what closing the `rpc` residual requires

**Where (construct):** `BACKLOG.md` row **N76**, the `**Residual, stated because the doc's original bound was wrong:**` clause — the sentence *"Closing it needs a create plus a read-back."*

**Evidence.** Both doc sites now say three requirements; N76 still says two. The round-2 review named the **understated residual** as NEW-2's "defensible core", and the fix report's own NEW-2 section says the residual was upgraded at "**both** sites (§Axis 3 bullet and §'What could not be established' item 1)" — i.e. no sweep of N76 was run for this finding.

**Failure mode, spelled out.** N76 is the standalone durable artifact — that standalone-ness is the whole reason NEW-1 item 2 was graded BLOCKING. A future picker-upper reading N76 alone plans a two-step probe, runs `cmux rpc surface.create` with a guessed param name, gets exit 0 + a normal payload + an empty read-back, and closes the residual as "no env param exists." That is a **wrong closure** of exactly the N56/N57 class this document exists to prevent.

**Why MINOR and not higher.** The statement is **incomplete, not false** — a create and a read-back genuinely are both necessary. N76 already carries the information needed to avoid the trap (*"an exit code cannot either (`cmux rpc` silently ignores unknown params — a-run)"*); it is simply not wired to the "closing it needs" sentence. And the row's first sentence points at the full doc.

**Fix (one clause, no restructuring):** change to *"Closing it needs a correctly-guessed parameter name, a create, and a read-back — a wrong name is silently ignored and is indistinguishable from the feature not existing."*

**Root cause, and the instruction that matters more than the clause.** MINOR-1 and the clause-(3) nit below are the same defect: the occurrence sweep was scoped to **NEW-1's markers** across both files (excellent — five found where three were named), while NEW-2 and NEW-6 were fixed only at the doc sites the review named, with no equivalent sweep of N76. **Run the propagation sweep per finding across both in-scope files, not only for the blocking one.**

**This needs an owner, not report prose.** Tasks 2 and 3 also write `BACKLOG.md` in this module, but N76 is outside their write scope, so "fold it into a later edit" is not available. Recommend the controller either authorize the one-clause N76 amendment as part of closing Task 1, or file a `deviations.md` row with an owning task and gate. This repo's own standing lesson is *Disposition ≠ done — every residual became a plan checkbox*; a MINOR that lands only in a review report evaporates.

---

## Considered and not filed

- **N76 clause (3), "the one real per-surface channel".** Adjacent to NEW-6, but N76 quotes no two-channel contract sentence, so it does not self-contradict; "real" reads defensibly as "demonstrated". Fold into the MINOR-1 edit if that edit happens; not worth its own round.
- **`deviations.md` row 65, "an exhaustive sweep of all 127 documented top-level verbs".** A round-2 register record at a site NEW-3 did not name, and row 70 two lines later records the imprecision. Self-correcting.
- **§"The primary path"'s bare `**Answer: there is no env channel…**`.** Unchanged, with its adjacent read-the-limit instruction. The round-2 reviewer explicitly declined to file it; not re-opened.
- **Foreclosed by the docs-only constraint, therefore not graded:** re-running the `cmux rpc` transcript with the honored `workspace_id` form; first-hand re-derivation of the three reviewer imports; upgrading NEW-6's SSH disposition above a-help strength.
- **Cosmetic line-wrap artifacts** at the §Axis 4 and §Disposition insertion points. Not filed — the docs-only round did not create a defect there.

**Nits, explicitly non-blocking:** the fix report's "cite each other in both directions" self-review claim (see NEW-1 above). **OP-1** is otherwise coherently recorded — owning gate, scope, the "compression and a semantic change in one diff makes both unreviewable" separation, and the instruction to re-measure the 200 at execution time rather than trust it — but it is dated **2026-07-31** while every sibling artifact in the same commit is 2026-07-30; plausibly a UTC slip off the 18:38 -0600 commit time.

---

## Empirical vs. reasoned

**Verified by execution (read-only, this review):** binary pin and `ping`; all three mechanical gates; commit file scope; Axis 4 re-derivation (127 / one hit); all seven alternation siblings; H2/H3 byte-completeness; the full `cmux rpc` param table plus the bogus-param byte-identity; `cmux ssh --help` prose and zero `env` mentions; fence hygiene; the install suite (104/0/0); the multi-pattern and repo-wide inference sweeps; the byte-identity of N76's flip condition, N76's methodology tail and N67's pre-`UPDATE` prefix.

**Concluded by reading:** that NEW-1's replacement claim is *narrower* (a logical judgment about the two statements); that one-directional cross-referencing suffices (a judgment about which reader is at risk); MINOR-1's severity and its failure mode; that keeping **a-run** on §Axis 2 is the right provenance call; OP-1's coherence.

**Could not check at all:** every value inside both probe sessions' in-surface read-backs — `SP2_SURF_MARK=|alpha`, `SP2_WS_MARK=…`, `SP2_RES=…`, `SP2_LAYOUT=delta`, the `surface:103`/`:107`/`:108` inheritance reads — and all `--env`/`--env-file` acceptance, the four `--env-file` semantics, both negative-control exit codes, `--mask` rendering, and `--layout surfaces[].env`. Reproducing any of them requires creating cmux state. This is inherent and unchanged across all three rounds; it is precisely why the reasoning around those data is what a reviewer can police, and why NEW-1 mattered.

---

## Review hygiene

Every command was read-only: `cmux --version`, `ping`, `--help` (top-level and per-verb, including the seven siblings), `cmux rpc workspace.env` — **a read method** — `cmux workspace env --json`, plus `git show`/`diff`/`grep`, two Python scanners, and one repo test script. **I created, modified and destroyed no cmux workspace or surface**, ran no `git stash`, and wrote **no repository file**. One draft was written to the session scratchpad, outside the repository. `git status --short` is unchanged from session start: the same two modified controller artifacts (`reports/.dispatch-log`, `reports/context-observations.log`).

---

## Controller disposition of MINOR-1

**Closed inside Task 1 rather than deferred.** The reviewer offered two routes — authorize the one-clause N76 amendment as part of closing Task 1, or file a register row with an owning task and gate. The first was taken, for the reason the reviewer itself gave: N76 is outside Tasks 2 and 3's write scope, so there is no later edit to fold it into, and a MINOR that lands only in a review report evaporates. Dispatched as a scoped round-4 fix (`[task 1 fix]`) rather than edited by the controller, preserving the dispatch-provenance discipline. The reviewer's suggested clause was applied verbatim, the adjacent clause-(3) nit folded in as the reviewer suggested, and the reviewer's **root-cause instruction** — sweep per finding, not per severity — was executed as a NEW-2/NEW-6 propagation sweep of `BACKLOG.md`. Verdict remains APPROVED; this amendment does not reopen the review gate.
