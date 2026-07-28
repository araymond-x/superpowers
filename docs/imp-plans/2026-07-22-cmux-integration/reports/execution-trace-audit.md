# Execution Trace Audit — cmux-integration (N43(D))

**Auditor status: ISSUES_FOUND.** **Controller adjudication: the RUN is clean; two of the five issues are defects in the auditing instrument, one was a false inference the controller disproved, and two are recorded/fixed.**

> **Coverage — stated plainly.** The trace was extracted from **all 15 session `.jsonl` files**, not `ls -t … | head -1`.
> A naive single-file run would have seen Task 11 only and returned "no anomalies" — the exact hollow check this
> feature's whole run has been hunting. Per-session extraction: **15/15 succeeded**.
>
> **The SKILL.md command for this step is wrong.** `SKILL.md` (Pre-Completion Gate step 8) documents
> `extract-execution-trace.py --session-file <f> --feature-dir <dir> --output <out>`. **There is no `--feature-dir`
> flag** — the script takes `--deviations-file` and `--reports-dir`. Copy-pasting the documented command fails with
> `unrecognized arguments`. Same defect class as **N35** (which fixed the *checkpoint* commands for exactly this and
> missed the trace command). Logged as a follow-up below.

## Auditor coverage

Audited all 12 tasks (0–11) from **primary evidence**: both `.dispatch-log` files (Module 1's archived at transition), all 12 implementer reports + 12 spec reviews + 12 quality reviews, 91 deviation rows, and plan checkboxes across all three plan files. Raw session `.jsonl` files were read directly for Task 4.

**Auditor declared NOT checked:** whether reviewer *findings* were actually closed correctly in code; whether fix-round commits match their reports; report bodies read for structure, not claim-by-claim; the run's code correctness.

## Task 4 — attribution artifact, NOT a process gap (resolved)

The extractor attributed task-records for 11 of 12 task numbers; **Task 4 appeared in none**. Investigated rather than reported as clean. Session `72ab7c50` (attributed only `[3]`) contains the complete Task 4 chain:

```
line 295 tool=Agent desc='Partner review for Task 4 dispatch'
line 309 tool=Agent desc='Implement Task 4: Launch composition A'
line 333 tool=Agent desc='Review spec compliance for Task 4'
line 345 tool=Agent desc='Review code quality for Task 4'
```

Matching provenance (`partner-review` 06:48:36Z, `implementer` 06:57:54Z, `spec-review` 07:15:31Z, `quality-review` 07:30:08Z) plus all three archived reports (11015 B / 8904 B / 8498 B). **Task 4 is fully gated.** The extractor's per-session task-record builder dropped it.

## Per-check results

| # | Check | Result |
|---|---|---|
| 1 | Reviews skipped | **None.** All 12 tasks have spec + quality review files *and* matching provenance rows. Task 0's absent partner row is the documented Task-0 exemption (hook Check 5d). **No `*-minimum-tier.md` files exist** — no tier exemptions were claimed anywhere in this run. |
| 2 | Reports missing/hollow | **None.** 12/12 implementer reports, 489–2703 words, 6–11 prose sections. Not stubs. |
| 3 | Concerns not logged | **None.** 10 reports are `DONE_WITH_CONCERNS`; the two thinnest were traced to `deviations.md:51` (Task 0) and `deviations.md:16` (Task 2). |
| 4 | Deviations undispositioned | **0 rows.** One stale *prose* string ("Pending spec re-review") — see Issue 5. |
| 5 | Escalations pushed past | **None.** No `BLOCKED` / `NEEDS_CONTEXT` status in any of the 17 report files. |
| 6 | Fix rounds without re-review | 4 flagged; **all four resolved** — see Issue 3. |
| 7 | Plan checkboxes | **Exactly one unchecked** (`plan.md:217`), and the auditor independently judged the deferral "a genuine deferral, not a completion claim in disguise". |

## Auditor positive control

Ran the provenance method against a falsified premise and a real gap:

```
-- FALSIFIED PREMISE: 'task 10 has no quality review' --
2026-07-25T03:42:24Z DISPATCH reviewer task=10 type=quality-review
-- REAL GAP: 'task 8 has a re-review after its 01:43:13Z fix' --
   (NO ROWS -> gap confirmed, same method returns nothing)
```

One hit, one miss — the method discriminates.

---

## Issues and controller adjudication

### 1. CRITICAL (instrument, not run) — **the trace-audit anomaly gate cannot fail.** CONFIRMED.

All six rules in `detect_anomalies()` (`extract-execution-trace.py:787–887`) gate on `ret["found"]` and `ret["status"]`. **Controller independently verified** against the merged trace:

```
found values: {'False'}   n=13
status values: {'None'}
```

Not one rule can fire. **`"total_anomalies": 0` is vacuous, not clean.** The trace's own fields already contradicted a clean reading: `plan_checkbox_updated: false` on 13/13 while the plan files are ticked, and `code_quality.dispatched: false` for tasks 1, 2, 5, 6, 11 while the dispatch logs show quality-review rows for all five.

**Implication beyond this feature:** the trace audit is a *pre-completion gate*. This run — **and every prior SDD run using this extractor** — passed a check that structurally could not fail. No historical "0 anomalies" trace should be treated as evidence.

**Disposition: recorded as a follow-up (BACKLOG).** Not fixed here — `extract-execution-trace.py` is outside this feature's write scope, and the fix needs its own design (populate `subagent_return`, or re-gate the rules on report-file status, which is available and reliable) plus a self-test asserting a **seeded anomaly actually fires**. This audit's conclusions rest on the dispatch logs, report files, and `deviations.md` — **not** on the extractor's anomaly counters.

### 2. IMPORTANT — the merged trace was produced by an uncommitted wrapper. VALID.

`execution-trace.json` has a top-level `coverage` block and `anomaly_summary_totals`; the checked-in extractor emits neither. A controller-authored merge wrapper produced it, and that wrapper was not in the repo — so the artifact's correctness was unauditable.

**Disposition: fixed.** The wrapper is committed as `reports/merge-execution-traces.py`, alongside the artifact it produced, and this file records that it produced it. It is deliberately **not** in `skills/subagent-driven-development/scripts/` — that directory's row count is asserted by the customization manifest's `## Deterministic Scripts (N active)` heading (which this very run had to correct), and this is a one-off audit aid, not a pipeline script. Its docstring says to delete rather than promote it if multi-session support is ever added natively.

### 2b. IMPORTANT (instrument) — **the extractor attributes tasks by TEXT MATCH, so auditing a task manufactures a record of it.** Discovered while verifying the wrapper.

Re-running the wrapper after the audit produced **14** task records attributing **all 12** task numbers — including the Task 4 that the pre-audit run (13 records) had missed. The new Task 4 record's source:

```
session: e3812350 (THIS session) | dispatch found: True
snippet: "You are the SDD execution trace auditor. You review a completed SDD run's execution trace…"
```

That "dispatch" is **the trace-auditor prompt written to investigate the missing Task 4** — which necessarily discusses Task 4 at length. The extractor text-matched it and created a phantom Task 4 execution record.

**The act of auditing the gap closed the gap in the evidence.** Two consequences, both bad:
- **The instrument cannot distinguish a session that EXECUTED task N from one that merely DISCUSSED it.** Any retrospective, any handoff summary, any audit inflates coverage.
- **A second trace audit will always look cleaner than the first**, because the first one's prompts are now in the corpus. Coverage improves with re-running rather than with evidence.

**The committed `execution-trace.json` is deliberately the PRE-AUDIT extraction** (13 records, Task 4 unattributed), not the flattering post-audit one. The real Task 4 evidence is the archived dispatch log and its three report files — cited above — not a text match. Folded into follow-up 1.

### 3. IMPORTANT — "Task 8's fix round closed a real defect with no re-review." **FALSE INFERENCE — controller disproved it.**

The auditor correctly observed that `.dispatch-log` for `task=8` **ends at the `fix` row** with no subsequent re-review. Its *inference* — that no re-review happened — is wrong. `task-008-quality-review.md` contains:

> `# Round 2 — Quality Re-Review after the fix round (verdict: PASS)`

and its body shows MX1 re-verified, with a `## Controller verification (MX1 independently reproduced)` section confirming the mutation was re-run with a positive control before any fix was dispatched.

**Root cause, and the genuinely useful finding: `SendMessage`-resumed reviews are invisible to `.dispatch-log`.** A re-review conducted by resuming the existing reviewer agent does **not** pass through the `PreToolUse → Agent` hook, so no provenance row is written. This is systemic, not a Task-8 quirk — the same mechanism was used for re-reviews elsewhere in this run (and is the documented recovery when a reviewer dies mid-response). **Consequence: the provenance log both under-records real re-reviews and cannot distinguish "re-review done via resume" from "re-review skipped".** Logged as a follow-up.

### 4. MINOR — three further trailing fix rounds with no logged re-review row. ACCEPTED.

Task 3 (`fix@06:31:14Z`) — the quality verdict was already PASS and both items ADVISORY; the artifact is a *fix report*, not a re-review. Task 9 round B (`deviations.md:77`) — the controller re-ran every load-bearing check itself after two fix implementers **elided** their positive-control output. Task 11 round 2 — re-reviewed (this session; the re-review found and closed a defect round 1 had introduced). Same `SendMessage` invisibility as Issue 3 applies.

### 5. MINOR — stale disposition prose at `deviations.md:46`. **FIXED.**

Task 6's row read `"**Resolved** — … Pending spec re-review."` although that re-review ran at 17:41:04Z. The *disposition* was correctly `Resolved` (which is why the gate's `| Pending |` check correctly reported 0), but the trailing prose was stale. Corrected.

---

## Follow-ups raised by this audit (for BACKLOG)

1. **`extract-execution-trace.py` anomaly detectors are inert** (Issue 1) — every rule gates on a `subagent_return` the extractor never populates. Fix + a self-test that seeds an anomaly and asserts it fires. **Until then, no trace audit's "0 anomalies" means anything.** Highest value of the three.
2. **Dispatch provenance does not record `SendMessage`-resumed reviews** (Issue 3) — re-reviews via agent resume bypass the `PreToolUse → Agent` hook, so `.dispatch-log` shows a fix with no closing re-review even when one happened. Affects Check 4c and `transition-module.py:validate_module_completion` reasoning, and makes "fix round without re-review" undetectable from the log alone.
3. **`SKILL.md`'s trace-extract command cites a non-existent `--feature-dir` flag** — the N35 fix corrected the checkpoint commands and missed this one. One-line doc fix.

## Verdict

**The run's execution is clean on every check that could actually be evaluated:** 12/12 tasks fully reviewed and provenanced, no hollow reports, no unlogged concerns, no escalations bypassed, no minimum-tier exemptions claimed, and exactly one checkbox left unchecked with an honest, mechanism-level deferral. **This is recorded as `ISSUES_FOUND` rather than "trace audit clean"**, because two defects in the auditing instrument itself are real and must not be buried under a passing feature.
