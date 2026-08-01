# Task 2 Spec Compliance Re-Review (Round 2) — SP1 context-probe attribution

**Verdict: PASS.** The round-1 BLOCKING finding is closed at all six sites; my own independently designed sweep found no seventh. All five "also verify" fix-round items are confirmed landed and correct. Two advisories remain open and one new advisory is raised — none of them blocking, per the round-1 convention that the verdict is driven by blocking findings only (round 1 returned FAIL on its single blocker while carrying two non-verdict-driving advisories). **PASS here does not mean the advisories were closed** — see the carry-forward section, which names an owner for each.

Scope: `e7034bc..HEAD` (`2dbba48`, `48b409d`), read against `a4dc986..HEAD` for changeset accuracy.

---

## FINDING 1 [BLOCKING, round 1] — CLOSED at all six sites

Each site read in the committed tree, not accepted from the fix report.

| # | Site | Current text | Verdict |
|---|---|---|---|
| 1 | SP1 doc, opening summary | "the top-level fields are the sum of the **`type: "message"`** iterations only — a non-`message` iteration such as `advisor_message` is *excluded* from them" | **Correct** |
| 2 | SP1 doc, N76 merge blockquote | "the top-level fields are the sum of the **`type:"message"`** iterations ONLY (a non-`message` iteration such as `advisor_message` is excluded), so the same cached prompt is counted once per `message` iteration" | **Correct** — and the correction reaches the text that is copied into `main` |
| 3 | `context-probe.py` module docstring, parity divergence 2 | "the TOP-LEVEL `usage` fields are the sum of the `type: "message"` iterations ONLY; a non-`message` iteration (e.g. `advisor_message`) is excluded from them" | **Correct** |
| 4 | `tests/unit/test_context_probe_iterations.py` module docstring | same correction, plus "counted once per `message` iteration" | **Correct** |
| 5 | `reports/task-002-implementation.md` Implementation Summary | corrected, with a `[CORRECTED 2026-07-31]` marker preserving the original wording | **Correct** |
| 6 | `reports/task-002-implementer-report.md` Implementation Summary | "**aggregate across the `type: "message"` iterations only**", with a `[CORRECTED]` marker naming the prior "aggregate across those iterations" | **Correct** |

`usage_total`'s own docstring also carries the corrected mechanism ("the top-level fields sum the `type: "message"` iterations"), which is a seventh *correct* statement, not a seventh defect.

### My independent sweep — command and result

I did not reuse the fix round's pattern. Four sweeps, all paraphrase-inclusive:

**Sweep A/B (primary).** Sentence-level scan over every `.md`/`.py`/`.sh`/`.txt`/`.jsonl` file, keeping any sentence that contains `iteration` **and** an aggregation verb **and** a usage-domain anchor:

```
VERB = sum(s|med|ming|mation)? | aggregat\w* | combin\w* | total(s|ed|ling|ing)?
     | add(ed|s|ing)? (up|together) | accumulat\w* | roll(ed|s)? up | tall(y|ies|ied)
     | "counted once" | "once per" | "union of" | N ?[x×]
ANCHOR = usage | top-level | cache_read | cache_creation | input_tokens
       | context-probe | usage_total
```

**Sweep C.** Literal phrasings: `their SUM`, `sum of (the|those|all|its) iterations`, `sums (the|all|those) iterations`, `aggregat* (over|across) … iterations`, `counted once per (call|iteration)`, `per iteration`.

**Sweep D.** Every occurrence of `statusline` co-located with `ctx` / `over-report` / `mirror` / `carr` / `share`.

**File-list correction, important.** My first three sweeps enumerated files with `git ls-files`, which structurally excluded three untracked artifacts in `reports/` (`task-002-fix-implementer-report.md`, `task-002-quality-review.md`, `task-002-spec-review.md`) — files that `transition-module.py` will archive, so not ephemeral. I re-ran the primary sweep over `{ git ls-files; git ls-files --others --exclude-standard; }` — **1,447 files, 51 distinct candidate sentences.**

**Result: no seventh site.** Every surviving hit is one of:
- a correct statement (the six corrected sites, `usage_total`'s docstring, `context-summary.md`, `task-002-controller-observation.md`);
- a *quotation* of the retracted wording inside a correction marker, a `deviations.md` register row, or a review finding (the untracked spec/quality reviews quote it as the defect they found — legitimate).

One near-miss I examined and am **not** reporting, with reasoning: `docs/process-improvement-findings/2026-07-31-context-measurement-architecture-recommendation.md` reads *"The top-level fields aggregate across the **`message`-type** iterations, so the same `cache_read_input_tokens` is counted once per iteration."* The unqualified "per iteration" is anaphoric to the `message`-type iterations named in the same sentence, and four lines later the doc states the precision explicitly: *"it is the sum of the **`message`-type** iterations, *not* of all iterations — summing all three of that turn's iterations gives `811,442`, which matches nothing."* Not a propagation site.

---

## The five fix-round items — all confirmed

1. **Statusline claim gone from `context-probe.py`; parity scoped to `claude-ctx-check` alone.** The docstring now reads *"claude-ctx-check still carries the uncorrected behavior … The statusline `ctx:` field does NOT carry it — that claim was falsified by pre-registered experiment on 2026-07-31."* Sweep D confirms **no committed file** still asserts the statusline shares the bug; every remaining mention is a retraction or a labelled quotation of the retracted wording.

2. **`iterations` labelled undocumented and version-unstable.** Present in the docstring with the source quotation (*"not a stable contract"*), and echoed in `usage_total`'s docstring and the test module docstring.

3. **Parity-test citation corrected.** The SP1 doc now names `test_differential_parity_with_ctx_check` in `tests/unit/test_context_probe_sessionid.py`, explicitly retracts the `test_context_probe_fixtures.py` citation ("*is not* a differential test: it invokes neither binary"), and adds a **"What parity now certifies, post-divergence"** paragraph scoping the test to the fallback path and stating plainly that nothing pins the two implementations against each other on multi-iteration input.

4. **"Exactly 2.0" corrected at four sites** — SP1 prevalence paragraph, Guidance rule 2, the N76 merge blockquote, and `task-002-implementer-report.md` (with a `[CORRECTED]` marker); the test docstring for `test_three_message_iterations_scale_beyond_2x` carries the range too.

5. **Guidance rule 2 is now operable.** It reads *"a poisoned row sits in the **range 1.94x–2.00x** of its neighbors"* with an explicit "State the discriminator as a range, not a point," the reason the point rule matched none of the 822 turns, and a stated limitation that the band assumes a two-`message` turn. Checked for operability against the doc's own data: min 1.9427 > 1.94 and max 1.9979 < 2.00, so the band covers the full measured population — it is a rule that fires, not one that matches nothing.

   *One derivation note, not a finding:* the band is **measured** as (top-level ÷ last-`message` iteration) but **applied** as (row ÷ neighbours). Those differ by one turn of context growth against a band only ~3% wide. The doc partly absorbs this by pairing the band with "the following row returns to the prior level," and rule 1 (exact recomputation) is preferred throughout, so the guidance is sound as written.

---

## ADVISORY 2 (round 1) — duplicate divergent report: CLOSED

- **Divergence hazard resolved.** `task-002-implementation.md` now opens with a blockquote: *"**NOT THE CANONICAL REPORT.** … The conventional, hook-validated report for Task 2 is `task-002-implementer-report.md` … where the two differ, the canonical file wins."* Both copies now carry the corrected mechanism, so they no longer diverge on substance.
- **`files_changed` is complete and accurate.** Checked path-by-path, not by count: the canonical report declares **14** paths; **all 14 appear in `git diff --name-only a4dc986..HEAD`**, and none is spurious. The seven original `iterations-*.jsonl` fixtures are present with `[ADDED to files_changed 2026-07-31]` markers, plus the four new fix-round fixtures. The eight changeset paths *not* declared are controller-owned artifacts (`deviations.md`, `.dispatch-log`, `context-observations.log`, `context-summary.md`, `task-002-controller-observation.md`, the arch-recommendation doc, and the two report files themselves) — correctly outside an implementer `files_changed`.

---

## Original Task 2 spec requirement — undisturbed

Plan Step 4 required the baseline-grep result in the **durable doc**. It is still there, in the SP1 doc's "Files changed" section, and **both claims reproduce today**: `grep -c 'context-probe' tests/ARaymond-hook-baseline/baseline.txt` → `0`; `grep -n 'probe'` over the same file → no match. The fix round did not disturb it; it strengthened the adjacent table by replacing two hardcoded counts ("8 tests", "7 fixtures") with the commands that compute them.

---

## Collateral-damage check — no garbled or over-reaching edits

Read every hunk of `git diff e7034bc..HEAD`.

- The `d6678ad` fragment round 1 warned about **is repaired**: `task-002-implementation.md` Concern 3 now reads *"It alone over-reports multi-iteration turns by ~2x — the statusline `ctx:` field does NOT"*, with the original garbled fragment preserved verbatim inside a `[CORRECTED]` marker rather than silently deleted.
- No half-edited sentence found anywhere in the diff.
- No correction contradicts a neighbouring passage. Specifically checked the two places round 1 called self-contradictory: the SP1 doc's summary and its evidence section now say the same thing, and the parity paragraph's historical framing ("were both **believed** to over-report") is followed immediately by the retraction.
- **Scope creep check:** the fix round applied black-style reformatting to `test_context_probe_iterations.py` (tuple/kwargs wrapping) and collapsed one wrapped `print` string in `context-probe.py`. Both are inside files the round owned, both are semantically inert, and `context-probe.py`'s functional diff is confined to `usage_total`'s early-return-on-truthy-total plus docstrings. No unrelated file touched.

---

## Independent verification I ran

| Check | Command | Result |
|---|---|---|
| Probe + gate suite | `.venv/bin/python3 -m pytest tests/unit/test_context_probe*.py tests/unit/test_context_gate*.py -q` | **56 passed** |
| Full unit suite | `.venv/bin/python3 -m pytest tests/unit/ -q` | **653 passed**, 1 warning |
| Integration (re-run by me, not inherited) | `bash tests/integration/sdd-e2e-test.sh` | **`E2E PIPELINE PASS - 15 steps`**, including Step 13's live context gate and Step 14's spawn path |
| Stdlib-only under the hook's interpreter | `/usr/bin/python3` (3.9.6) against the triple fixture | exit 0, printed `107802` (the last `message` iteration, not the 315406 top level) |
| Markdown-only claim for `48b409d` | `git show 48b409d --stat` | exactly 2 `.md` files — the fix report's non-regression argument for not re-running e2e holds; I re-ran it anyway |
| Fixture arithmetic | decoded all five new/changed fixtures | `message-triple` top 315406 / iterations 102502, 105102, **107802** → 315406/107802 = **2.9258**; `message-no-fields` message iteration sums **0** against top 250000; `non-dict-entries` carries `int`/`str`/`None` around a valid iteration; `not-a-list` holds the non-iterable scalar `5`; `iterations-string` preserves the old `"nope"` shape |
| Tree state | `git status --porcelain` | only controller/hook-owned artifacts modified or untracked; no source file dirty |

---

## Open items — carry-forward, none blocking

**[ADVISORY 1 — round 1, NOT closed, and marginally enlarged].** The SP1 doc's opening still promises *"each is paired with the command that recomputes it."* The fix round added one recompute command (`python3 -c "print(315406/107802)"`) and two count-commands in the Files-changed table, but **did not soften the promise and did not attach commands to the figures round 1 named**: the monotonicity table (77/132 turns, 2/2 → 0/0), the 80-row match and its positive control, and the live-replay table (`373139 → 189929`, `539691 → 270851`). It also introduced **new** bare figures under the unchanged promise — `min 1.9427 / max 1.9979 / 0 of 822`, and "zero differences across all **273** retained transcripts." Round 1 pre-scoped this as advisory and asked only that I confirm the current state: it is unresolved, and the population of unpaired figures grew. Owner: the SP1 doc's next editor; the cheapest close is softening the opening sentence to describe what the doc actually provides.

**[ADVISORY 3 — NEW, fix-round-introduced, self-consistency].** The doc gives **two different counts of the same population in adjacent sentences** without reconciling them: *"Multi-iteration turns are **793**, every one of them carrying exactly two `message` iterations … re-measured across **822** multi-`message` turns."* If every multi-iteration turn carries exactly two `message` iterations, then "multi-iteration turns" and "multi-`message` turns" are the same set, and 793 ≠ 822. **The 822 figure is the one carried into the N76 merge blockquote copied to `main`.**

I ran the discriminator rather than guessing. Re-executing the doc's own corpus definition (120 largest transcripts under `~/.claude/projects`) today: **33,574 usage rows, 818 multi-iteration turns, 818 turns with ≥2 `message` iterations** — confirming the two labels denote an identical population (818 == 818; over all 275 transcripts, 897 == 897). Today's count sits between 793 and 822, and every other figure has drifted upward the same way (32,705 single-iteration turns today vs the doc's 32,160; 275 transcripts vs "273"), which round 1 already established as expected corpus growth and explicitly *not* a finding. Provenance closes it: the untracked `task-002-quality-review.md` measured *"over **822** multi-`message` turns"* — 822 is the **quality reviewer's** independent measurement, imported into the doc alongside the doc's own earlier 793.

So neither number is fabricated or provably wrong, which is why this is advisory and not blocking. What is missing is one clause of reconciliation. Note the doc already applies exactly that convention one paragraph away, for the ratio: *"two independently built fixtures (the quality review's measured 2.9679; the one committed here measures 2.9258)."* The same treatment applied to the population count would close this. Owner: the merge step, since the unreconciled number is what lands in `main`.

**[ADVISORY 4 — NEW, minor, class recurrence].** `context-probe.py`'s module docstring says *"a three-`message` turn measures **~3x**"*, where the committed fixture measures **2.9258** and the quality review's measured 2.9679 — and the doc's own explanation (the last iteration's `cache_creation` and `output` are not duplicated) makes the ratio *always strictly below* N. The SP1 doc and the test docstring both say ~2.9x. This is the same rounded-ratio class the round existed to correct, surviving in the one artifact that travels downstream via the `~/.claude/skills/superpowers` symlink. A docstring is not a tuning rule and cannot be inoperable, so it stays advisory — but it is a recurrence, not a nit.

**[ADVISORY 5 — bookkeeping, controller-owned].** `deviations.md` row 79 still reads `Pending — [task 2 fix] after quality review`, while **all three of its prescribed corrections are verifiably applied** in `context-probe.py` (statusline dropped, SUM wording corrected, `iterations` labelled version-unstable). Rows 83–87 are already marked `Resolved — [task 2 fix]`. The fix round declined to edit the register to avoid two writers on one artifact and flagged it as its own Concern 6; it is the controller's to close.

---

## Checks I ran that found nothing

Stated explicitly so the negative results are on the record:

- **Seventh-site sweep** — four independently designed patterns including paraphrases (`aggregate`, `combined`, `total of`, `accumulate`, `roll up`, `tally`, `counted once per`, `union of`, `N x`) that a `sum`-keyed regex would miss, over 1,447 tracked **and untracked** files. **No seventh site.** The three-consecutive-sweeps escalation pattern (1/5, 3/5, 5/6) does not continue into round 2.
- **Statusline sweep** — no committed file still asserts the statusline carries the double-count.
- **Garbled-fragment scan** — every hunk of `git diff e7034bc..HEAD` read; the `d6678ad`-class defect the dispatch warned about is repaired and not reproduced elsewhere.
- **Self-consistency of the SP1 doc on the mechanism** — summary, evidence section, fix section, parity section, guidance section and merge blockquote now all state the `type:"message"`-only reading. No section contradicts another. (The population-count inconsistency in Advisory 3 is a different axis and is reported above.)
- **`files_changed` path-by-path against `git diff --name-only a4dc986..HEAD`** — 14/14 present, 0 spurious.
- **Scope creep** — no file outside the fix round's declared set was touched; the code diff is confined to `usage_total` and docstrings.
- **Step 4 baseline-grep** — both grep claims re-executed and reproduced.
- **Regression risk from `48b409d`** — confirmed markdown-only, then the full e2e re-run independently anyway.

---

## Bottom line

The blocker is genuinely closed, not merely reported closed: the false mechanism is gone from all six sites including committed code and the text queued for `main`'s BACKLOG, and my own paraphrase-inclusive sweep over tracked and untracked files found no seventh. The falsified statusline claim is out of committed code, the parity citation now names the test that actually invokes both binaries and honestly scopes what it certifies post-divergence, and Guidance rule 2's discriminator is a range that covers its full measured population instead of a point value that matched nothing. All suites pass under independent re-execution (56 / 653 / 15-step e2e / stdlib-3.9.6). Four advisories remain open — one carried from round 1 and now slightly larger, two newly raised, one bookkeeping — each with an owner named, and none of a kind that should hold the task.
