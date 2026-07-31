# Task 2 — Controller Partner Review (dispatch quality)

**Verdict: BLOCKED** — four blocking findings, one controller decision required. The Task 2 implementer dispatch was **not** sent. This report is the specification for rebuilding it.

## Headline: the controller's premise was refuted

The controller's draft dispatch was built around a finding that the plan's Step 1 anchor (`tokens=373139`) did not resolve. The partner **refuted this** and located the row.

### F1 [BLOCKING] — The row exists, and it is committed

`~/projects/claude-custom/claude-codex-handoff/.worktrees/cmux-transport/docs/imp-plans/2026-07-29-cmux-transport/reports/context-observations.log`, in the **committed blob** (`git show HEAD:…`):

```
2026-07-30T00:48:28Z task= type=quality-review tokens=171666 source=probe tier=below action=allow
2026-07-30T00:56:54Z task=5   type=other       tokens=373139 source=probe tier=soft  action=allow
2026-07-30T01:02:54Z task=    type=other       tokens=210693 source=probe tier=below action=allow
```

Neighbors `171666` / `210693` match the spec's "~171k and ~210k" exactly. `source=probe`, `task=5`, `type=other` — precisely what the hook writes on the `MARKED_FIX` path (`ctx_observe_and_log other`). Tracked, committed, durable.

**Why every controller search missed it: wrong repository.** The row is in `claude-codex-handoff`, not `superpowers`. The plan's glob `docs/imp-plans/*/reports/context-observations.log` resolves against cwd and cannot reach another repo; `git log --all -S` in `superpowers` cannot either. BACKLOG **N76 on main** states the location outright — "in the **cmux-transport feature's** `context-observations.log`" — and that row is not on this branch (F3/F4).

A grep that reaches it:

```bash
grep -rn "tokens=373139" \
  ~/projects/claude-custom/*/docs/imp-plans/*/reports/context-observations.log \
  ~/projects/claude-custom/*/.worktrees/*/docs/imp-plans/*/reports/context-observations.log
```

**Consequence:** the entire "the anchor does not resolve" block and the (i)/(ii)/(iii) disposition scaffolding must come out. Disposition (i) is settled by evidence before dispatch. Steps 2–4 proceed as the plan writes them.

**Controller verification:** confirmed independently against both the working copy and `git show HEAD:…`. The partner is correct.

### F2 [BLOCKING] — The draft reward-framed the false disposition

The draft told the implementer that disposition (ii) was "**a *more* valuable outcome** than the original spike", pre-labelled it "**a third false-premise finding**", and warned against "silently picking (iii)". It pointed the incentive at the one conclusion that is factually wrong. Combined with a search recipe that could not reach the file, an implementer reproducing the controller's negative and reaching for the rewarded framing lands on a confidently-wrong finding — written into a durable findings doc, citing this repo's own false-premise history. **Remove all valuation language.** State what was found and where; let evidence decide.

### F3 [BLOCKING] — Step 1's second pointer is also wrong, and the draft inherited it

The plan's Step 1 says "*the cmux-integration feature dir's reports narrow the date*" — wrong feature **and** wrong repo (cmux-integration is 2026-07-24/25/27; the row is 2026-07-29/30 cmux-transport). The draft propagated it: "*the `2026-07-22-cmux-integration` log … is the natural corpus*." It is not. Both must redirect to the cmux-transport log and the retained transcripts under `~/.claude/projects/-Users-araymond-projects-claude-custom-claude-codex-handoff--worktrees-cmux-transport/` (12 `.jsonl`, several multi-MB, dated Jul 29–30 — Step 2 is fully feasible).

*In the draft's favour:* its instruction to extend the search to other repos under `~/projects/claude-custom/` **would** have found this. The failure was corpus misidentification, not insufficient breadth — do not treat that expansion as over-scoping when rewriting.

### F4 [BLOCKING] — Missing context: the origin evidence is unreachable from this branch

Neither artifact that defines the anomaly exists on `cmux-spawn-v2`:

- `docs/process-improvement-findings/2026-07-30-first-live-sdd-auto-spawn-run-analysis.md` — **main only**; its **F7** is the origin finding. Nothing in `spec.md`, `spec-distilled.md` or `plan.md` cites it (grep: zero hits).
- BACKLOG **N76 on main** — the SP1 row, status `in flight (cmux-spawn-v2 SP1)`.

Both carry a hypothesis the plan's Step 2 does not list: *"the value matches the **PREDECESSOR** session's end-of-session total, suggesting the probe read the wrong transcript (or the wrong usage block) on the fix-marked path."* The plan offers only (a) sidechain, (b) inflated `cache_creation`, (c) genuine. **The leading hypothesis in the durable record is a fourth.** Quote it into the dispatch and cite both paths (`git show main:…` for the analysis doc).

Two internals to hand over, verified by the partner but to be confirmed first-hand by the implementer:

- `context-probe.py` `find_latest_total` has **no sidechain filtering** — it scans from the end for the most recent assistant `usage` block. Hypothesis (a) is live.
- `ctx_observe_and_log` (fix path) and the gated path resolve the transcript **identically** (`.transcript_path`, falling back to `SESSION_ID`). There is no distinct fix-path resolution code — which partially undercuts N76's "on the fix-marked path" framing and should be stated rather than left for the implementer to trip over.

### F5 [Controller decision required before re-dispatch] — BACKLOG: one decision, two symptoms

The draft never mentioned BACKLOG. That is **half** wrong; the other half is a merge hazard the controller owns.

- The plan authorises a conditional Task 2 write. The Write-Scope **table** row for Task 2 omits `BACKLOG.md`, but the File Map (*"New rows: … and SP1 if exclusion-rule outcome"*) and the prose below the table (*"three potential writers … Task 2 (conditionally …)"*) both include it. The draft dropped it silently.
- **N-id collision, verified against the merge-base** (`fa2d482`, ending at N75): main added **N76 = SP1 misattribution**, **N77**, **N78**; this branch added its own **N76 = SP2 disposition** (Task 1). The branch's N76 ≠ main's N76, and "next free id" on this branch resolves to **N77 — also taken on main**. Task 3 would compound it. Precedent: Sprint 4's upstream-v6 collision, N29/N30 → N33/N34.

Since main's N76 **is already the SP1 row**, a Task 2 exclusion-rule outcome should update that row at merge, not append a duplicate. Do not hand the implementer the id-selection decision.

### Missing escalation

**The evidence lives in a different git repository.** The dispatch must state that the cmux-transport log and the `~/.claude/projects/…` transcripts are **read-only** — no edits, no commits, no git state changes outside this worktree — and that if the investigation appears to require touching `claude-codex-handoff`, the implementer STOPs and reports.

## Verified correct — do not re-check

- **stdlib-only**: `context-probe.py` imports only `argparse`, `json`, `os`, `sys`, `pathlib.Path`, `typing.Optional`.
- **Python 3.9**: `check_python39_compat` scans `skills/subagent-driven-development/scripts/*.py`, so the file is in scope; the `X | None` / `skills/scripts/models/` asymmetry is stated correctly.
- **Baseline**: `context-probe` appears **0 times** in `tests/ARaymond-hook-baseline/baseline.txt` — no `check-hooks.sh --capture` needed.
- Contract Constraints block verbatim from the plan header; task-text reproduction otherwise faithful; report-format, no-`git stash` / no-`git add -A` / `.venv`-symlink constraints all match `context-summary.md`; the test command matches real files (`test_context_probe*.py` ×3, `test_context_gate*.py` ×4).
- **No Deferred Work order is owned by Task 2 or by "Module 1".** B7's py39 line is scoped to Modules 2 and 4, so applying it here is a correct-by-fact addition, not an order being discharged.

## Controller actions taken in response

1. **F1 verified independently** against the working copy *and* the committed blob. Premise refuted; the controller's finding was wrong. Recorded rather than quietly dropped.
2. **F5's id collision resolved before re-dispatch.** The branch's SP2 row was renumbered **N76 → N79** (first id free on both branches) in commit `a3c8661`, with all in-branch references retargeted and `reports/` deliberately left reading N76 as contemporaneous record. `context-summary.md` was additionally retargeted in `b2f8883` because, unlike the review reports, it is *forward-consumed* — its pointers would have misdirected a successor session.
3. **F5's BACKLOG-write decision made:** Task 2 appends **no** BACKLOG row. Main's N76 *is* the SP1 row, so an exclusion-rule outcome updates that row at merge. Task 2's doc states the merge action verbatim; the implementer is not handed id selection. Task 3's two rows take **N80/N81**, enumerated against `main` at execution time.
4. **The N67 merge hazard** the renumber surfaced (main and this branch both edited N67 since the merge-base; a "take theirs" resolution would drop the `DISPOSITIONED BY N79` clause) is recorded in `context-summary.md` under the merge step.
5. **F1–F4 are carried into the rebuilt dispatch**, which was NOT sent this session — the controller hit the context-pressure HARD threshold first. The rebuild specification is this report plus the handoff's next-action block.
