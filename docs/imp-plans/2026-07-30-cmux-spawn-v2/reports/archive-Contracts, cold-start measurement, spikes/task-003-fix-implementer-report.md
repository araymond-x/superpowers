---
schema_version: 1
task_id: 3
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "docs/process-improvement-findings/2026-07-30-sp3-non-sdd-context-guard-design.md"
    description: "BLOCKING 1: replaced the under-reaching sweep command with a 7-file form verified to reproduce 539691/621072, added the repo-wide wrapped-grep/.worktrees instrument gotcha, added coverage honesty (the null is largely predetermined for non-SDD sessions), and closed the self-invalidating three-hits $127 count with a time-of-writing clause. Numbers and conclusion unchanged."
  - path: "docs/process-improvement-findings/2026-07-30-sp4-carry-forward-fix-lane-design.md"
    description: "BLOCKING 2: replaced the validate-plan.py pointer in Candidate A with the two binding gates (validate_module_completion, all_tasks_have_reports), stated the unused-vs-always-used cost fork, added a second enforcement-interaction table covering the reserved-slot variant, and corrected the now-stale 'could not be established' bullet. IMPORTANT 3: generalized attempts-not-dispatches to both classes with per-site comment attribution and the Check-9 visibility consequence. MINOR 4/5: archive- count corrected to two; the 0-to-N row count replaced with an anchored command."
  - path: "docs/process-improvement-findings/BACKLOG.md"
    description: "Rows N80 and N81 regenerated from their docs' fenced row blocks so both stay byte-identical. 2 insertions / 2 deletions, no other row touched."
tests:
  written: 0
  passing: 0
  command: "bash tests/ARaymond-installation/verify-symlink-install.sh"
  result: PASS
contract_compliance:
  - constraint: "Write scope is exactly three files; do not fix anything else noticed."
    status: compliant
    detail: "git diff --cached --numstat shows exactly the three paths. Four out-of-scope defects were found and are reported in Concerns rather than fixed."
  - constraint: "Immutable artifacts: reports/* from earlier rounds must not be edited."
    status: compliant
    detail: "No file under reports/ was edited. Two errors found inside immutable artifacts are reported in Concerns for the controller to own."
  - constraint: "Byte-identity between each BACKLOG row and its doc's row block."
    status: compliant
    detail: "Re-verified post-commit with the tail-anchored extractor after a positive control on a mutated copy. N80 4906 bytes, N81 4382 bytes, both IDENTICAL."
  - constraint: "No :NNN line-number citations in either doc."
    status: compliant
    detail: "grep -nE '\\.(sh|py|md):[0-9]+' over both docs returns zero hits, despite grep -n output being in front of me all session. The one quoted hook comment was truncated before its embedded :324."
---

## Implementation Summary

Ran the six review findings as a fix round. The decisive act was refusing to take any premise on
authority: I re-measured the disputed sweep before touching it, and independently re-measured both
of BLOCKING 2's gate claims and the finding 3 comment quote rather than transcribing the review.

**The controller's correction to finding 1 is confirmed, and the reviewer was wrong.** My own
measurement reproduces the controller's numbers exactly. I did not change `539691`, `621072`, or the
conclusion; I fixed the printed command, which was the actual defect.

One correction to the review's own prescription: finding 5 asked for `grep -c '0→'`, which returns
**5** today rather than the 4 it reported, because a deviations row added by the review-round-1
commit *quotes* the `0→N` notation while carrying an ordinary Task id. I used an anchored
`grep -cE '^\| 0→'` instead, which is stable at 4 across both `0e4b420` and HEAD. Writing the
review's literal command into the doc would have shipped a fresh self-invalidating count — the exact
defect finding 6 is about.

## Source Files Read

- `docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/task-003-quality-review.md` — the six findings and the controller's adjudication.
- `docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/task-003-spec-review.md` — the PASS verdict and its independently-run mechanical checks, so the fix would not regress them.
- `docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/task-003-implementer-report.md` — round 1's claims, including the byte-identity false alarm not to re-trip.
- Both design docs in full, and `docs/process-improvement-findings/BACKLOG.md` rows N80/N81.
- `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` — Stage 0 marked-fix branch, Stage 2 implementer-logging site and its comment, the range guard, and the `archive-` occurrences.
- `skills/subagent-driven-development/scripts/transition-module.py` — `validate_module_completion`'s `for task_id in module.task_ids:` loop and its error string.
- `skills/subagent-driven-development/scripts/controller-checkpoint.py` — `all_tasks_have_reports` and its blocker registration.
- `docs/imp-plans/2026-07-30-cmux-spawn-v2/deviations.md` — the `0→` rows, read to phrase the anchored count honestly.

## CLAUDE.md Files Read

- `CLAUDE.md` (repo root) — the only one in the tree. Three of its rules were directly load-bearing here: **cite the construct, never a line number**; **give the command that computes a number, not the number** (applied to findings 5 and 6, and extended to SP3's own point-in-time token readings); and the `handoff-spawn.log` vs `context-observations.log` non-conflation, re-checked as a no-regression item.

## Claims Verified

### Re-measurement of both sweeps — the controller is right, the reviewer is wrong

Measured directly, not taken from either party:

| sweep | two largest readings |
|---|---|
| 4-file (wrapped `grep`, the doc's printed instrument) | `513612` `523426` `621072` |
| 7-file (`/usr/bin/grep -r`) | `523426` **`539691`** **`621072`** |
| 7-file (the `find`/`xargs` pipeline, below) | identical to the row above |

The third form, written out so no one copies an escaped pipe out of a table cell:

```
find ~/projects/claude-custom/ -name context-observations.log -print0 | xargs -0 /usr/bin/grep -hoE 'tokens=[0-9]{6,}' | sort -t= -k2,2n -u | tail -2
```

`523426` is the **truncated** sweep's answer; the corrected sweep's top two are `539691` and
`621072` — **exactly what SP3 already said.** The reviewer's claim that the full sweep yields
`523426` is backwards. `539691` is a genuine hook-written row
(`2026-07-31T01:08:20Z task=1 type=other tokens=539691 source=probe tier=hard action=allow`) living
only in this feature's own worktree log — one of the three files the printed command could not see —
so the "laundered citation" reading is refuted too. **I did not change the numbers, the attribution,
or the conclusion.**

Root cause confirmed three ways: `find` reaches **7** logs, wrapped `grep -rl` reaches **4**,
`/usr/bin/grep -rl` reaches **7**; the 3 skipped are all under `.worktrees/`. `type grep` confirms
the shell function wrapping `ugrep … --ignore-files`.

Conclusion positive control: `tokens=56[0-9]{4}` over all seven files returns **nothing**, while the
unrestricted pipeline returns 478 rows and locates `621072`. (The review recorded 477 — the log is
live and has grown by one row since. I wrote neither number into the doc; the doc gives the command.)

Both replacement commands were executed **as printed** after being written down, and each reproduces
`539691` / `621072`.

### BLOCKING 2's gates, independently measured

- **`validate-plan.py` does not gate the variant.** Built a fixture plan with a reserved in-range slot: `blockers: []`. **Negative control** on the same fixture (`enforcement_tier: bogus`) → **2 blockers**. The validator can block and simply does not block this.
- **`transition-module.py:validate_module_completion`** — read the construct: `for task_id in module.task_ids:` → `errors.append(f"Task {task_id}: missing or empty implementer report")`. An unused reserved id is inside `module.task_ids`, so it hard-blocks the transition.
- **`controller-checkpoint.py:all_tasks_have_reports`** — executed against the fixture: unused slot → `{'pass': False, 'missing': [5]}`; **positive control** after adding a task-005 report → `{'pass': True, 'missing': []}`. Also noted (and written into the doc) that it keys on `### Task N` headers while `validate_module_completion` keys on manifest ids — two different keys, same catch.

### Stage-2 comment wording, verified before quoting — and it does not say what the review implies

The comment is verbatim: *"Written here in Stage 2 — BEFORE the enforcement gate below — so the
timestamp is recorded even when the dispatch is ultimately blocked."* **But it sits above
`if [ "$IS_IMPLEMENTER" = true ] && [ "$MARKED_FIX" = false ] && [ -n "$TASK_NUMBER" ]` — it governs
the `type=implementer` write only.** The `type=fix` write happens at an earlier, separate site (the
Stage 0 marked-fix branch) under a comment about a different concern: *"Marked fix → log type=fix
ONLY (skip Stage 2's type=implementer write so Check 9's window isn't moved"*. Both writes precede
the range guard, but only one carries the "recorded even when blocked" rationale. I wrote the fix to
match that, rather than quoting the implementer-site comment as evidence for the fix-site behavior.

### Findings 4/5/6 counts

- `grep -c 'archive-'` over the hook → **2** (one comment line, one `T0_GLOB=` line). Conclusion (one archive-aware lookup) unaffected; corrected the count and said which is which.
- `grep -c '0→'` over `deviations.md` → **5** today, **4** at `0e4b420`. Anchored `grep -cE '^\| 0→'` → **4** at both. Used the anchored form and explained in the doc why a bare count over-counts.
- `$127` now returns **20** hits across 8 files (the review measured 15 across 7). Closed with the time-of-writing clause plus an explicit instruction to re-run rather than trust the recorded count.

### Byte-identity, with a positive control on the extractor

Positive control first: mutated a copy of SP3 (`| N80 | Context guard` → `| N80 | MUTATED-CANARY guard`)
and confirmed the tail-anchored extractor **reports the difference**. Only then did I trust a clean
result. Rather than hand-editing both copies, I regenerated the BACKLOG rows *from* the doc blocks
(asserting exactly one matching row replaced per id), which makes divergence structurally impossible.

Post-commit: **N80 IDENTICAL (4906 bytes), N81 IDENTICAL (4382 bytes)**. SP3 still has 2 fenced
blocks and SP4 1, with the row block last in each — I used an indented code block for the new
command so the fence structure is unchanged.

### Propagation sweep — the command, as a deliverable

Swept with `/usr/bin/grep -rn` (not the wrapped `grep`) over the whole tree, **tracked and
untracked**, `--include='*.md'`, using paraphrase-inclusive alternations rather than one keyword per
claim:

```
/usr/bin/grep -rniE '(single|one|1) hit|returns a single|exactly one hit' --include='*.md' .
/usr/bin/grep -rniE 'two-number|three rows|0→N notation|carry a two' --include='*.md' .
/usr/bin/grep -rniE 'validate-plan\.py' --include='*.md' docs/process-improvement-findings/
/usr/bin/grep -rniE 'benign|attempts, not|fix \*attempts\*|records fix' --include='*.md' .
/usr/bin/grep -niE 'cheapest|costed|cost.{0,3}(it |the )?first|costs nothing' <both docs>
/usr/bin/grep -niE '539691|621072|523426|grep -rhoE' <both docs>
```

**Result: every in-scope site was inside the two docs; all other hits were immutable
`reports/`/`deviations.md` artifacts.** The sweep caught one site no finding named — SP4's
§What could not be established still said the reserved-slot variant was untested against
`validate-plan.py`, which would have contradicted the corrected §Candidate A two sections later. It
also caught the Candidate A "Against" bullet's "avoids all of this", now qualified. Post-edit
re-sweep confirms no stale phrasing remains.

### No-regression checks against the review's "held up" list

`grep -nE '\.(sh|py|md):[0-9]+'` over both docs → **zero**. `handoff-spawn.log` mentions in either
doc → **0** (no conflation). Table integrity `awk -F'|'`: header **NF=9**, N80 **NF=9**, N81
**NF=9**. N54/N57 untouched: `git diff -U0 | grep -cE '^[+-]\| N5[47] '` → **0**. BACKLOG numstat
**2 / 2** (two rows rewritten in place, nothing else). `verify-symlink-install.sh` →
**104 passed / 0 failed / 0 warnings, PASSED**.

## Deviations from Plan

- **Finding 5's prescribed command was not used verbatim.** The review asked for `grep -c '0→'` (reporting 4); that command returns 5 today. I used the anchored `grep -cE '^\| 0→'`, stable at 4 across both revisions. Deviating was necessary to satisfy the finding's own intent — the `CLAUDE.md` give-the-command rule is worthless if the command given is the one that rots.
- **The N80 row uses a pipe-free command form** (`/usr/bin/grep -rhoE … --include=context-observations.log …`, verified to reach all 7 and return the identical result set) because a `find … | xargs` form would break the table cell at its unescaped `|`. The doc prose keeps the `find`/`xargs` pipeline.
- **Scope extended within the authorized files** to two sites no finding named: SP4's §What could not be established bullet and the Candidate A "Against" bullet. Both were direct contradictions created by the prescribed fixes; leaving them would have shipped a self-inconsistent doc.

## Self-Review Findings

- **Caught before writing:** the review's finding 3 implies the Stage-2 comment documents both classes. It does not — it sits at the `type=implementer` site. Quoting it as evidence for the `type=fix` site would have been exactly the overclaim shape this sprint keeps catching. Verified the two sites separately and wrote the distinction into the doc.
- **Caught before writing:** finding 5's own command is unstable. See Deviations.
- **Caught by the propagation sweep:** the §What could not be established contradiction, which no finding named.
- **Applied finding 6's treatment consistently rather than locally:** SP3's "the largest readings are 539691 and 621072" is itself a point-in-time claim on a growing log, so it now carries an "as of that sweep" clause. Fixing the self-invalidating count in one paragraph and leaving the same defect two paragraphs up is the propagation failure this sprint keeps repeating.
- **Structurally eliminated the byte-identity risk** by generating the rows from the docs instead of editing two copies, with an asserted one-row-per-id replacement.

## Concerns

1. **Errors inside immutable artifacts — reported, not edited; the controller owns these.**
   (a) `task-003-quality-review.md` finding 1's central claim ("the full 7-file sweep's second-largest is `523426`, not `539691`") is **false**, as my independent measurement confirms; the controller's adjudication already re-scopes it, but the finding text itself remains wrong on the record.
   (b) The same review's finding 5 prescribes `grep -c '0→'` → 4; that command returns 5 today.
   (c) Its positive-control count of 477 is now 478.
   (d) `task-003-implementer-report.md` Concern 3 still calls the pre-gate row "benign today (Check 9 ignores `type=fix`)" — now known to be class-dependent, since the `type=implementer` sibling is Check-9-visible.
   (e) `task-003-spec-review.md` reports the sweep as *"Exact match … It holds up"* — that was corroboration through the **same truncated instrument**, not verification. It is the clearest instance of the review's own "independence of reviewer is not independence of instrument" point, and it is worth carrying forward as a process lesson: two agents in one shell reproduce the same truncation indefinitely.

2. **Out-of-scope defect found in the hook, not fixed — and it has already rotted, demonstrably.** `sdd-pre-dispatch-hook.sh`'s Stage 0 marked-fix comment carries a hard-coded line-number citation, `— :324`, naming the Stage 2 `type=implementer` write. **That write is at lines 297/300 today** — the citation is off by ~27 lines and points at unrelated code. This is exactly the rot the repo's no-line-numbers rule exists to prevent, now living inside the enforcement machinery that rule is meant to protect. I truncated the quote before it rather than reproducing it in either doc. Fixing it edits a **baselined** hook and so requires a same-change `check-hooks.sh --capture` plus committed `baseline.txt`; out of this task's three-file scope. Worth a BACKLOG row, and the demonstrated mismatch (not the category argument) is the reason.

3. **The wrapped-`grep`/`.worktrees` gotcha is repo-wide and is now documented only in SP3.** Every recursive `grep` any agent has run from this repo root has silently skipped every worktree — and worktrees are where this repo executes SDD work. This has already produced one false BLOCKING finding and one false corroboration in a single task. It belongs in `CLAUDE.md` under Hook Development Gotchas or a sweep-method note, not buried in one design doc. Out of scope here; flagging it as the most transferable thing this round produced.

4. **`.dispatch-log` and `context-observations.log` show as modified** in the worktree from live hook activity during this round. I did not stage them (staged exactly the three authorized paths). They are flight-recorder artifacts the controller normally commits.

5. **Fixture retained and disclosed:** the reserved-slot plan, its `enforcement_tier: bogus` negative control, and the reports dir used for the `all_tasks_have_reports` positive control live in the session scratchpad, outside the repo, so the two BLOCKING-2 measurements can be re-run.
