---
schema_version: 1
task_id: 3
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "docs/process-improvement-findings/2026-07-30-sp4-carry-forward-fix-lane-design.md"
    description: "BLOCKING A: added the hook's Checks 4b/4c on the FOLLOWING task as the third and earliest-firing blocking gate (re-measured from scratch with a passing positive control), added a scenario column to the reserved-slot table, named PLACEMENT (interior vs last-in-range) and PLAN SHAPE (headered vs manifest-only) as open design axes without resolving either, and extended Candidate A's test checklist to require a live-hook successor dispatch. IMPORTANT B: replaced both printed 'seven type=fix rows' counts with the command plus one revision-anchored figure. MINOR C: the two-keys claim is now shape-conditioned. MINOR D: two provenance rows corrected to three, with Check 5d's minimum-tier zero-row branch noted."
  - path: "docs/process-improvement-findings/BACKLOG.md"
    description: "Row N81 regenerated from SP4's fenced row block so the two stay byte-identical: three-gate enumeration, placement and plan-shape axes, corrected 'blocks BOTH gates' and 'two provenance rows', and the successor-dispatch checklist item. 1 insertion / 1 deletion; N80 untouched."
tests:
  written: 0
  passing: 0
  command: "bash tests/ARaymond-installation/verify-symlink-install.sh"
  result: PASS
contract_compliance:
  - constraint: "Write scope is exactly three files; do not fix anything else noticed."
    status: compliant
    detail: "git diff --cached --numstat showed only the two files that needed changes (SP4, BACKLOG); SP3 was in scope but required no edit. Out-of-scope defects found are reported in Concerns, not fixed."
  - constraint: "Immutable artifacts: reports/* files from earlier rounds must not be edited."
    status: compliant
    detail: "No pre-existing file under reports/ was touched. This report is a new file. Errors found in earlier artifacts are reported in Concerns."
  - constraint: "Verify the reserved-slot measurement yourself, in a scratchpad fixture, with a positive control."
    status: compliant
    detail: "Built an isolated git fixture repo under the session scratchpad (never the live repo), passing-first: reached rc=0 with slot 6 used BEFORE deleting slot 6's artifacts, so the five BLOCKED strings are a delta from a known-good baseline. Also measured the last-in-range case and both plan shapes."
  - constraint: "Byte-identity between each BACKLOG row and its doc's row block."
    status: compliant
    detail: "Regenerated the rows FROM the doc fences with a tail-anchored extractor (SP3 has two fences), positive-controlled on a mutated copy first. Post-commit: N80 IDENTICAL 4872 bytes, N81 IDENTICAL 6199 bytes."
  - constraint: "No :NNN line-number citations in either doc."
    status: compliant
    detail: "grep -cnE '\\.(sh|py|md):[0-9]+' over both docs returns 0 and 0."
---

## Implementation Summary

Ran the round-2 findings as fix round 2. The decisive act was again refusing to take a premise on
authority: I rebuilt the reserved-slot measurement from scratch in my own fixture before writing a
word of it, and I built it **passing-first** — reaching `rc=0` with the reserved slot used, then
deleting that slot's artifacts — so the five `BLOCKED` strings are a delta attributable to the
empty slot rather than an `exit 2` that might have come from anywhere in the gate stack.

**Every claim in this dispatch reproduced.** The reviewer's BLOCKING A measurement is correct, its
structural half is correct, MINOR C reproduces exactly, and MINOR D is source-backed (I read Check
5d's construct rather than inheriting the claim). Finding B's count had moved again by the time I
measured it — which is the argument for dropping the number, not for updating it.

I resisted the pull to resolve the placement question. The dispatch is right that naming the axis is
the deliverable; SP4 now carries interior-vs-last-in-range as an open bullet in §What could not be
established alongside a third axis the measurement exposed (headered vs manifest-only), and
explicitly declines to recommend either.

## Source Files Read

- `docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/task-003-quality-review-round-2.md` — the four new findings, the controller's confirmations, and the "what held up" list I must not regress.
- `docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/task-003-fix-implementer-report.md` — round 1's claims and its five Concerns, so I would not re-trip closed items.
- Both design docs in full, and `docs/process-improvement-findings/BACKLOG.md` rows N80/N81.
- `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` — manifest resolution, the 3-stage classifier, the range guard, Check 4's N-1 file-existence sub-block and its `TASK_NUMBER -eq MANIFEST_TASK_START` skip, Check 4c and its N3a guard, Checks 5/5b/5c/5d, Check 6/6b, and the context-pressure gate (read specifically to keep it from contaminating the fixture).
- `skills/subagent-driven-development/scripts/controller-checkpoint.py` — `all_tasks_have_reports` and its `TASK_HEADER_PATTERN` / `_unfenced_content` keying.
- `skills/subagent-driven-development/scripts/transition-module.py` — `validate_module_completion`'s `for task_id in module.task_ids:` loop and its per-task error strings.
- `skills/subagent-driven-development/scripts/_report_utils.py` — `REQUIRED_SECTIONS`, to make the fixture's slot-6 implementer report pass `validate-report.py` so Check 4b would be genuinely satisfied in the positive control.

## CLAUDE.md Files Read

- `CLAUDE.md` (repo root) — the only one in the tree. Load-bearing here: **cite the construct, never a line number** (the new text quotes `elif [ "$PREV" -lt "$MANIFEST_TASK_START" ]` and `for task_id in module.task_ids:`, never a coordinate); **give the command that computes a number, not the number** (finding B, and re-applied to the sweep counts in this report); the `handoff-spawn.log` vs `context-observations.log` non-conflation, re-checked as a no-regression item; and the hook-baseline obligation, which is why MINOR E stays untouched.

## Claims Verified

### The reserved-slot measurement — built passing-first, with a positive control

Fixture: an isolated `git init` repo under the session scratchpad (never the live repo), manifest
`task_range: [4, 8]`, module 2 = tasks 4–8, slot 6 reserved. Tasks 4–5 complete; **all of task 7's
own artifacts pre-satisfied** (partner review + its `type=partner-review` provenance row, checkpoint
file, `### Task 7` plan header, pre-execution audit, dispositioned deviations, `Source Contracts:
None`, `context_summary_at: null`) so Checks 4b/4c were the only variable. `SUPERPOWERS_CTX_HANDOFF_BYPASS=1`
so the context-pressure gate could not contribute an `exit 2` of its own — and the assertion is on
the **BLOCKED text**, not on `rc` alone.

**Positive control first — slot 6 USED:**

```
rc=0
WARNING: SUPERPOWERS_CTX_HANDOFF_BYPASS set — context gate skipped.
{ "hookSpecificOutput": { ... "additionalContext": "SDD REMINDER: ..." } }
```

**Then delete slot 6's three reports and its two `task=6` provenance rows — nothing else:**

```
rc=2
BLOCKED: No implementer report found for Task 6 …
BLOCKED: No spec review found for Task 6 …
BLOCKED: No quality review found for Task 6 …
BLOCKED: No spec-review dispatch recorded for Task 6 …
BLOCKED: No quality-review dispatch recorded for Task 6 …
```

**The reviewer's measurement reproduces exactly**, and because the `rc=0` baseline came first the
five errors are attributable to the removal alone. Structural half confirmed independently: Check
4's N-1 file-existence sub-block skips only on `TASK_NUMBER -eq MANIFEST_TASK_START` (7 ≠ 4), and
Check 4c's N3a guard is `elif [ "$PREV" -lt "$MANIFEST_TASK_START" ]` (6 ≥ 4) — neither arms.

### Placement — measured, not reasoned

Same fixture, dispatching the successor that would test a **last-in-range** slot 8:

```
BLOCKED: Task 9 is outside the manifest's task_range [4, 8]. …
rc=2
```

Nothing about task 8 appears. So the range guard refuses the successor before Checks 4b/4c can
inspect the slot — a last-in-range unused slot is caught only by the two terminal gates. That is the
whole content of the placement axis, and it is why the doc now names it rather than assuming the
interior case.

### MINOR C — reproduced exactly, plus a negative control

`all_tasks_have_reports`, run against the same fixture (task 7 and 8 reports added first, so slot 6
is the only variable — without them the result is polluted by future tasks, which is how I caught
that my first run of this was measuring the wrong thing):

```
slot 6 WITH a '### Task 6' header    : {'pass': False, 'missing': [6]}
slot 6 with NO header (manifest-only): {'pass': True,  'missing': []}
negative control (task 5 report gone): {'pass': False, 'missing': [5, 6]}
restored (back to slot-6-only)       : {'pass': False, 'missing': [6]}
```

And the counterpart, `validate_module_completion`, run on **both** plan shapes:

```
slot 6 unused, plan header present : ['Task 6: missing or empty implementer report', …]
slot 6 unused, NO plan header      : ['Task 6: missing or empty implementer report', …]
```

Identical — it is manifest-keyed. So the two keys catch the same slot only in the both-populated
shape, exactly as the finding says. This is the cross-product the doc now states rather than
flattening.

### MINOR D — source-backed before writing "three"

Read Check 5d's construct rather than inheriting the count: it builds
`PARTNER_FILE="${REPORTS_DIR}/partner-review-${TASK_PADDED}.md"` and, when that file exists, greps
`task=$TASK_NUMBER type=partner-review` in the dispatch log. So the third row is real. Its
minimum-tier branch is keyed on a `partner-review-NNN-minimum-tier.md` **file** — not on any
`review_tier` plan declaration — and satisfies the check with no provenance row at all; the doc says
so with that mechanism, not the plan-declaration one.

### Finding B — the count, run rather than trusted

```
live grep -c 'type=fix'    : 9
committed at HEAD          : 8
at 0e4b420                 : 7
```

It had already moved past the review's 8 — my own `[task 3 fix]` dispatch appended the 9th. **This
is the argument for dropping the number, not for updating it.** SP4 now prints the command and one
revision-anchored figure (7 at `0e4b420`). The printed command was executed **as printed** and
returns 9. Confirmed not in N81: `grep` for `seven`, a numeric `type=fix` count, and `Seven` over
the N81 row all return 0, so no copy-forward mirror was needed — checked rather than trusted.

### Byte-identity, with a positive control on the extractor

Positive control first: copied all three files to a scratch tree, mutated SP3's fenced N80 row
(`| N80 | Context guard` → `| N80 | MUTATED-CANARY guard`), and confirmed the tail-anchored
extractor reports **DIFFER (doc 4879 bytes, backlog 4872 bytes)** — the +7 delta matches the
mutation exactly. Only then did I trust a clean result. The extractor takes the **last** fenced
block per doc (SP3 has two; a first-fence extractor is wrong on it by construction) and asserts
exactly one matching BACKLOG row per id.

Rather than hand-editing two copies, I **regenerated** the rows from the doc fences. Post-commit:
**N80 IDENTICAL (4872 bytes), N81 IDENTICAL (6199 bytes).**

### Propagation sweep — the command, as a deliverable

Swept the whole tree with `/usr/bin/grep -rn` (**not** the wrapped `grep`, which honors `.gitignore`
and skips `.worktrees/`), `--include='*.md'`, tracked and untracked, using paraphrase-inclusive
alternations rather than one keyword per claim:

```
/usr/bin/grep -rniE '(both|two|2) (binding |terminal )?gates|gates that (do bite|actually bind)|both catching|both catch|the two gates' --include='*.md' .
/usr/bin/grep -rlniE 'reserved (in-range )?slot|reserve a carry-forward|carry-forward task id' --include='*.md' .
/usr/bin/grep -rniE 'seven|[0-9]+ +.?type=fix|type=fix.? rows' --include='*.md' .
/usr/bin/grep -rniE 'two provenance|provenance rows|two .?type=(spec|quality|partner)' --include='*.md' .
/usr/bin/grep -niE 'validate_module_completion|all_tasks_have_reports' <both docs>
```

**Result: every in-scope site is inside SP4 and N81; all remaining hits are immutable
`reports/`/`deviations.md` artifacts or unrelated documents.** Specifically:

- The `validate_module_completion|all_tasks_have_reports` co-occurrence sweep caught the Candidate A
  **"Against" bullet** — *"the cost … lands instead on `validate_module_completion` and
  `all_tasks_have_reports`"* — a site **no finding named** and which none of the "two gates" patterns
  matched. Corrected.
- SP4's surviving *"the two gates a carry-forward fix would meet"* is a **different, correct** claim
  — it means Checks 5c and 5d in the archive-awareness section, not the reserved-slot gates. Left
  alone deliberately.
- The sweep also caught a contradiction **I created**: my new positive-control sentence said
  "restoring … its two provenance rows" two paragraphs above the corrected "three provenance rows".
  Both are right (Check 5d's row is owed by the *dispatched* task, not the previous one), so I added
  the disambiguating clause rather than changing either number.
- SP3's `seven` hits (`seven files`, `seven logs`, `seven paths`) are either a static source count or
  already carry the "as of that sweep" qualifier round 1 added. Not a regression; left unchanged.

**Re-swept after the final edit**, because the disambiguation clause introduced exactly the strings
the provenance-count pattern hunts. S4 returns 3 hits in SP4 (the disambiguated positive-control
sentence, the corrected three-row cost bullet, the N81 fence) plus the BACKLOG mirror; S1 returns
the correct-as-is Check-5c/5d sentence, the correct "both terminal gates" phrase, the corrected
"gates that actually bind" sentence, and the N81 pair. **No new site.**

### No-regression checks against round 2's "what held up" list

| item | check | result |
|---|---|---|
| zero `:NNN` citations | `grep -cnE '\.(sh\|py\|md):[0-9]+'` both docs | **0 / 0** |
| no `handoff-spawn.log` conflation | `grep -c` over all four SP docs | **0** everywhere |
| BACKLOG table integrity | `awk -F'\|'` header / N80 / N81 | **NF=9** on all three |
| N54/N57 untouched | `git diff -U0 \| grep -cE '^[+-]\| N5[47] '` | **0** |
| BACKLOG numstat | `git diff --numstat` | **1 / 1** |
| SP4 table column uniformity | `awk -F'\|' NF` over both tables | case-A table **NF=5** on all rows; new 4-column table **NF=6** on all rows |
| SP4's "grep that phrase" promises | ran both against `deviations.md` | **1 / 1** — resolve as printed |
| SP4's anchored `0→N` command | `grep -cE '^\| 0→' deviations.md` | **4**, as printed |
| SP3 untouched | `git status` | no diff — N80 byte-identical |
| install suite | `verify-symlink-install.sh` | **104 passed / 0 failed / 0 warnings, PASSED** |

## Deviations from Plan

- **The reserved-slot table gained a fourth column rather than a prose label.** The dispatch asked me
  to "label the table's scenario column"; the table had no such column, so labelling required adding
  one (`applies when`). A prose sentence above the table would have left each row individually
  ambiguous, which is the defect the finding describes. The 7-column BACKLOG table is untouched — the
  NF=9 integrity check still passes.
- **A third axis was named that no finding asked for.** MINOR C's shape distinction (headered vs
  manifest-only) is not merely a clause: it changes which gates fire, so leaving it as a parenthetical
  while promoting placement to a design variable would have made the two corrections inconsistent —
  a manifest-only interior slot is caught by 4b/4c and `validate_module_completion` but **not** by
  `all_tasks_have_reports`. It is stated as an open axis alongside placement, not resolved.
- **SP3 was in the authorized write scope and received no edit.** No round-2 finding touches it; its
  own point-in-time counts were swept and are already qualified. Not editing it is the correct
  outcome, recorded here so its absence from the diff is not read as an oversight.

## Self-Review Findings

- **Caught during measurement, before writing:** my first `all_tasks_have_reports` run returned
  `missing: [6, 7, 8]` because the fixture had no reports for the not-yet-executed tasks 7 and 8.
  Writing that down would have shipped a measurement of the wrong thing. Added their reports so slot
  6 was the only variable, then re-ran with a negative control.
- **Caught by building passing-first:** had I built the failing case first, an `exit 2` from the
  context-pressure gate, the pre-execution-audit gate, or Check 5d would have been indistinguishable
  from the 4b/4c block I was trying to demonstrate. The `rc=0` baseline is what makes the five
  strings evidence rather than a coincidence.
- **Caught by the propagation sweep:** the Candidate A "Against" bullet, which no finding named and
  which the obvious "two gates" pattern does not match — only a sweep on the two **construct names**
  found it. This is the third consecutive round in this task where the named findings were a subset
  of the real sites.
- **Caught by re-sweeping my own output:** the "two provenance rows" phrase I introduced in the
  positive-control sentence, sitting two paragraphs above the corrected "three". Disambiguated
  rather than silently changed.
- **Applied finding B's rule consistently, not locally:** both `seven` sites are gone, and the
  replacement text explicitly says the count grows *including from the rounds that edit this
  sentence* — which is now demonstrably true, since it went 7 → 8 → 9 across three consecutive fix
  rounds of this one task.

## Concerns

1. **Errors inside immutable artifacts — reported, not edited; the controller owns these.**
   (a) `task-003-quality-review-round-2.md` finding B records the live `type=fix` count as **8**; it
   is **9** as of this round. The finding is still correct — that drift is its own thesis — but the
   figure on the record is stale.
   (b) The same review's MINOR C block prints `{'pass': False, 'missing': [6]}` without stating that
   the fixture must contain reports for the tasks *after* the reserved slot; run naively the same
   check returns `missing: [6, 7, 8]` and the shape difference is obscured. A reader reproducing it
   from the review text alone will not get the printed result.
   (c) `task-003-fix-implementer-report.md` records N80 as **4906 bytes**; my extractor measures
   **4872** for the same unchanged row. The discrepancy is a byte-counting convention (trailing
   newline), not a content difference — N80 is byte-identical and untouched — but the two reports
   now disagree numerically on the record.

2. **MINOR E left in place as instructed, and it is worth a BACKLOG row.** `sdd-pre-dispatch-hook.sh`'s
   Stage 0 marked-fix comment still ends `— :324)`, naming a Stage 2 write that is nowhere near
   there. I re-confirmed the mismatch while reading the classifier. Fixing it edits a **baselined**
   hook and so obliges a same-change `check-hooks.sh --capture` plus committed `baseline.txt` — out
   of a three-file documentation scope. The dispatch says it is already routed to a merge-time row;
   flagging only that it survived another round of being read by three agents without being fixed.

3. **The `--ignore-files` sweep gotcha is still documented only in SP3, and it bit again this
   round.** Every recursive sweep I ran needed `/usr/bin/grep` explicitly. This is a repo-wide
   instrument property that has now produced one false BLOCKING finding, one false corroboration, and
   a standing instruction in every dispatch — it belongs in `CLAUDE.md`, not in one design doc.
   Round 1 raised this as its Concern 3; it is unresolved, so I am re-raising it rather than letting
   it decay.

4. **A design question the measurement raises and the doc does not answer.** Check 4's N-1
   file-existence sub-block skips on `TASK_NUMBER -eq MANIFEST_TASK_START`, while Check 4c skips on
   `PREV < MANIFEST_TASK_START`. For the first task in a module these coincide, but they are
   *different* conditions and a reserved slot is precisely the case that could separate them. Nothing
   is wrong today — I measured both firing together — but any implementation of the reserved-slot
   variant should treat that as two guards to keep in sync, not one. Out of scope for a design doc
   that is explicitly not a build; noted so it is not rediscovered at implementation time.

5. **`.dispatch-log` and `context-observations.log` show as modified** in the worktree from live hook
   activity during this round (my own dispatch appended to both). I did **not** stage them — exactly
   the authorized paths were staged. They are flight-recorder artifacts the controller normally
   commits.

6. **Fixture retained and disclosed.** The fixture repo, its builder and its runner live in the
   session scratchpad, outside the repo, so every measurement above can be re-run: the `rc=0`
   positive control, the five-error delta, the last-in-range range-guard refusal, both
   `all_tasks_have_reports` shapes with a negative control, and both `validate_module_completion`
   shapes. Nothing was written to the live repo to obtain them.
