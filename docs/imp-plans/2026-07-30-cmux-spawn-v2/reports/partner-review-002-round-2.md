# Task 2 — Controller Partner Review, round 2 (rebuilt dispatch)

**Verdict: APPROVED.** The rebuilt dispatch is ready to send as written. F1–F4 are closed, the (e) addition is accurate and correctly bounded, and nothing needed was lost with the scaffolding. Three **controller-side** items below are not dispatch blockers and must not delay it — they are the controller's to handle before Module 1 acceptance.

## Confirmed closed (verified first-hand, not from the draft)

- **F1** — evidence block reproduces the committed log exactly (lines 23–25 of the cmux-transport log; `373139` between `171666` / `210693`). Location, valuation language, and the (i)/(ii)/(iii) scaffolding are gone.
- **F2** — no reward framing survives. "*Leading hypothesis in the durable record*" is a true, cited statement about `main`'s N76/F7, and it is immediately counterweighted by the internal that undercuts N76's own framing and by the "spike shape proves nothing" caution. Balanced, not incentivized.
- **F3** — corpus redirected; zero `cmux-integration` references remain, and the supersede is explicit. Verified the plan's Step 1 does still carry both wrong pointers, so the supersede claim is true (see C1).
- **F4** — hypothesis (d) present with both `git show main:` citations. Both internals verified independently: `context-probe.py` has **zero** `sidechain`/`isSidechain` occurrences; `ctx_observe_and_log` reads `.transcript_path` and the gated path reads the same key, both falling through `ctx_probe_tokens` to `--session-id`. Identical, as stated.
- **Other**: Contract Constraints block is **byte-verbatim** from `module-1-contracts-spikes.md`; `context-probe` = **0** hits in `tests/ARaymond-hook-baseline/baseline.txt`; probe imports are stdlib-only; the 12 transcripts exist. Checkbox ticking is correctly absent — SKILL.md assigns it to the controller.
- **(e) is sound and correctly bounded.** "*Not monotonic*" is established fact (539,691 → 305,208, both instruments agreeing), not the compaction hypothesis; compaction is labelled "residual hypothesis" exactly as the source note does. The do-not-generalize-(a) caution matches the note's own scoping ("this transcript contains zero sidechain entries") and does not overstate it.
- **The not-reproducible floor is closed** — Step 3's binary routes "not a probe bug" (which includes not-reproducible) to "the doc pins the exclusion rule". The plan's "never to silence" gate note is satisfied implicitly. Do not reopen.

## Controller-side items (do not block the dispatch)

**C1 — F3 is only half-closed: the plan text was never amended.** `module-1-contracts-spikes.md` Task 2 Step 1 still reads `grep -rn "tokens=373139" docs/imp-plans/*/reports/context-observations.log` and "*the cmux-integration feature dir's reports narrow the date*", and `deviations.md` has **no** row for it (grepped). Round 1's F3 said both must redirect. The implementer never needs the plan text, so the dispatch is fine — but leaving it violates this sprint's own standing rule that a finding with a consumer half needs a plan edit, not a report-only fix. Needs a net-zero plan amendment **or** a deviations row.

**C2 — the dispatch permits an outcome Module 1 acceptance does not accept.** The criterion is *"SP1 doc committed (with probe fix + green probe/gate test set, **or a pinned exclusion rule**)"*. The dispatch's exclusion-rule section correctly allows a third: *"or explicitly state that it cannot [discriminate] and what a consumer should do about it."* Given (e) that is the right instruction, but pre-authorize it with one deviations row now rather than discovering it at the Module 1→2 transition where `transition-module.py` validates completion.

**C3 — "state the merge action verbatim" supplies the content but nothing routes the merge step to it.** Add one line to `context-summary.md`'s merge-step row — the row already carrying the N67 hazard — naming `2026-07-30-sp1-context-probe-attribution.md` as the source of N76's replacement text. Without it the instruction is findable only by remembering the doc exists.

## Nits (optional, non-blocking)

- "*12 `.jsonl` … dated Jul 29–30*" understates the corpus: last-timestamps run to `2026-07-31T01:55Z`. One clause — *do not filter the corpus by mtime* — prevents the implementer excluding four files.
- "*two such refusals have already been upheld*" is the one remaining incentive-shaped clause — it rewards refusing a premise, the mirror of F2's failure mode. Judgment call.
