# SP4 — a sanctioned carry-forward fix lane across module transitions

**Written 2026-07-31** by the `cmux-spawn-v2` SDD run, Module 1 Task 3.
**Status: DESIGN DOC. Nothing here is scheduled and nothing here is implemented.** The spike's
deliverable is explicitly *"Design doc + BACKLOG row; NO implementation"* (`spec.md` §6,
`spec-distilled.md` §Spikes). Its job is to let a future reader **decide**, not to hand them a build.
**Files as BACKLOG N81.**

**Confidence labels** follow this directory's convention (`2026-07-29-cmux-mode-option-surface.md`,
`2026-07-30-sp2-workspace-env-probe.md`): **a-run** = exercised against the code as installed;
**a-file** = read from a source file; **inferred** = reasoned, not observed. Per this repo's
`CLAUDE.md` rule, every citation below names a **construct** — a function, a variable, a quoted
string — never a line number. Line numbers rot; `grep` for the anchor.

---

## The question

Carried from the plan:

> A sanctioned carry-forward fix lane across module transitions — a defect found in module N+1
> whose fix belongs to module N's files.

---

## Bottom line

**Recommend design B: formalize the plan-amendment + ledger lane that this sprint already used
twice, and do NOT build a cross-module dispatch class.**

Three findings drive it, all **a-run** or **a-file**:

1. **The blocker is earlier and blunter than expected.** A `[task N fix]` dispatch naming a task
   outside the active module's `task_range` is refused by the hook's **task-range validation**,
   which runs *before* Checks 4b/4c/5c/5d are ever reached. Measured (§Today's rule). So the
   "carry-forward fix lane" is not a matter of relaxing a review gate — it is a matter of the
   manifest's active range, which is the module boundary itself.
2. **The fix cycle is already excellent — within a module.** `type=fix` is logged, attributed, and
   deliberately excluded from Check 9's window. Seven live `type=fix` rows exist in this feature's
   own dispatch log. Nothing about the in-module lane needs work.
3. **The cross-module case has a working answer that costs nothing and touches no baselined hook:**
   amend the *owning module's plan text* and record the routing in `deviations.md`. This sprint did
   exactly that, twice, and wrote down why (§The observed friction). Design B is the act of making
   that a documented convention with a checked artifact rather than a habit that depends on the
   controller remembering.

**What Design B does not solve, stated up front:** a defect in module N's files that **blocks**
module N+1 right now cannot wait for a later task. §Residual says what to do in that case and why no
candidate here handles it cleanly.

---

## Today's rule, as enforced

The convention is "fixes belong to the module that owns the file." That is a statement of intent.
Here is what the machinery actually does.

### `transition-module.py` archives reports and truncates the dispatch log (a-file)

Both behaviors live in `transition()`:

- **Archive (Step 3).** For each `task_id` in the completing module, it globs `task-<NNN>-*` in the
  reports dir and `shutil.move`s every match into `archive-<module>/`. The move is unconditional
  and covers implementer reports, spec/quality reviews, partner reviews and checkpoints alike.
- **Dispatch log (Step 5).** `shutil.copy2` into `archive-<module>/.dispatch-log`, then
  `open(dispatch_log, "w").close()  # truncate to empty`. The history survives in the archive; the
  **live** log starts empty for the next module.
- It also rewrites `data["task_range"] = [next_mod.task_ids[0], next_mod.task_ids[-1]]` — this is
  the field the hook reads, and it is what makes a completed module's task ids out-of-range.

There is **no inverse operation.** The module's functions are `_find_module`,
`_has_dispatch_provenance`, `_verification_task_ids_from_file`, `validate_module_completion`,
`transition`, `main` — nothing re-opens a transitioned module (a-file; enumerate with
`grep -n '^def ' transition-module.py`).

### The mechanical refusal is the task-range check, and it fires first (a-run)

`sdd-pre-dispatch-hook.sh` handles a `[task N fix]` marker by logging `type=fix`, then setting
`IS_IMPLEMENTER=true` and `MARKED_FIX=true` — i.e. **a marked fix takes the implementer path.** It
then reaches the range guard, whose message text is
`"BLOCKED: Task $TASK_NUMBER is outside the manifest's task_range"`.

Measured rather than reasoned, in a throwaway git fixture with `task_range: [4, 8]` (never the live
repo), one case plus two controls:

| case | description | result |
|---|---|---|
| A — cross-module fix | `[task 2 fix] remediate review findings` | **exit 2**, `BLOCKED: Task 2 is outside the manifest's task_range [4, 8]` |
| B — in-module fix (positive control) | `[task 5 fix] remediate review findings` | passes the range guard; refused later by the pre-execution-audit gate — i.e. it reaches the normal gate stack |
| C — plain implementer, out of range (control) | `Implement task 2 of the plan` | **exit 2**, same task-range message |

Two things follow, and both matter to a designer:

- **The refusal precedes every review gate.** Case B proves the range guard is not what stops an
  in-module fix; case A returns the range message and nothing from Checks 4b/4c/5c/5d. A design that
  loosens dispatch provenance or partner review would not move this at all.
- **The `type=fix` row is written *before* the refusal.** In case A the dispatch log ends up
  carrying `DISPATCH fix task=2 type=fix` for a dispatch that never happened. That is benign today
  (see Check 9 below) but it is a real property: **the dispatch log records fix *attempts*, not fix
  *dispatches*.** Any design that routes cross-module fixes through the hook inherits it.

### What is *not* a constraint — Check 9 (a-file)

`_check_verification_git_reality` in `controller-checkpoint.py` opens with
`if not verification_ids: return []` and iterates only tasks declared `task_type: verification`. Its
timestamp source, `_merged_dispatch_times`, compiles
`r"(\S+)\s+DISPATCH\s+implementer\s+task=(\d+)\s+type=implementer"` and its docstring states it
*"Parses ONLY `type=implementer` lines — the shared dispatch-log contract with N26: type=fix /
type=fix-unattributed lines never open a verification window."*

**So Check 9 does not police ordinary fix dispatches, cross-module or otherwise.** This is worth
stating loudly because it is easy to assume otherwise: the check that "cross-references the dispatch
log against git" sounds like it would care, and it does not. It was confirmed independently earlier
in this sprint for a different reason (`deviations.md`, the Task 3 ProcessNote row auditing two
provenance gaps before the transition).

### The N26 rows, and the exclusion a new design would inherit (a-file)

BACKLOG **N26** is `done` (2026-06-22, `sdd-aggregate-gate-visibility`, `7dc7812`). It is the change
that **created** the artifacts this spike is about: the hook now logs review-driven fix dispatches
and partner re-review rounds as `type=fix` / `type=fix-unattributed` lines, and Check 3b's
allowed-prefix list admits the gate-required report names. Before N26 the fix cycle left *zero*
entries — its original analysis notes that N18's fix plus two reviews were invisible and that
corroborating them required session-jsonl forensics.

The markerless sibling matters too: a non-implementer dispatch whose description matches
`grep -qiE '\bfix\b|remediat'` logs `DISPATCH adhoc type=fix-unattributed` — tamper-evidence with no
task attribution, by design.

**The design constraint for any new cross-module class:** `_merged_dispatch_times` excludes both
`type=fix` and `type=fix-unattributed` on purpose, and its comment names the writer
(*"Writer: sdd-pre-dispatch-hook.sh Stage 2; keep the format in sync"*). A new dispatch type must
decide explicitly whether it inherits that exclusion, and must be added on both sides of that SSOT
in one change.

### Two flat lookups a re-opened task would trip (a-file)

`CLAUDE.md` documents exactly five archive-aware lookups; **every other report glob is intentionally
flat.** Verified for the two gates a carry-forward fix would meet — `grep -n 'archive-'` over the
hook returns a single hit, the Check 5 Task-0 glob (`T0_GLOB`, the N10 fix). Therefore:

- **Check 5c** builds `CHECKPOINT_FILE="${REPORTS_DIR}/checkpoint-pre-dispatch-${TASK_PADDED}.json"`
  with no archive fallback. The completed module's checkpoint was moved into `archive-<module>/`, so
  the controller must write a **fresh** one. This is satisfiable and arguably correct — a new
  dispatch should have a new checkpoint — but a designer should know the archived one is invisible.
- **Check 5d** builds `PARTNER_FILE="${REPORTS_DIR}/partner-review-${TASK_PADDED}.md"`, also flat.
  An archived partner review does **not** satisfy it, so re-opening an archived task demands a
  brand-new partner review *and* a matching `type=partner-review` dispatch-log row — and the live
  log was truncated at the boundary, so the row must be re-earned by a real dispatch.

Check 4c is the exception that already handles the boundary: it skips when
`PREV < MANIFEST_TASK_START` (the N3a guard), with boundary provenance re-verified at transition
time by `validate_module_completion`. But this only matters if a dispatch gets that far, and case A
shows it does not.

---

## The observed friction — real instances from this sprint

None of this is hypothetical. All four instances are in
`docs/imp-plans/2026-07-30-cmux-spawn-v2/deviations.md`.

**1. A finding whose two halves lived in two modules.** Task 0's quality-review finding 4 (the
`list-pane-surfaces` selected-row marker) had a fixture half inside Task 0's write scope and a
**consumer half — the awk parser in Module 3's Task 9 — outside it.** The controller resolved it by
amending the Module 3 plan text (commit `949d310`) and recorded the reason verbatim:

> `transition-module.py` archives Module 1's reports at the boundary, and an instruction a Module 3
> implementer never reads is an instruction that does not exist.

The register's own comment on that row is the sharpest statement of the problem in the repo:
*"That is the exact failure mode finding 4 itself was."*

**2. Findings tagged `0→9` and `0→17`.** Three rows in the register carry a two-number Task column —
findings **originating** in Task 0 but **owned** by Tasks 9 and 17, both in later modules. The `0→N`
notation is an ad-hoc convention invented in-flight precisely because the register had no column for
"found here, fixed there." One of them (`0→17`) was a *re-introduction*: Task 9's stub was amended
for the marker and Task 17's identical stub was not, so the same defect would have landed one module
later against a parser that had just been fixed.

**3. The Deferred Work table.** `deviations.md` carries a whole table whose only purpose is routing
audit orders to owning tasks in later modules — B1, A3b/c+B2, B3, B4, B7, B8a, OP-1 — each with an
explicit "Owning task / gate" column and a "What must land" cell. This is design B already existing
in an under-specified form: it works, it is hand-maintained, and nothing verifies that any row was
honored.

**4. The contrast — the in-module lane works.** A `deviations.md` DeferredWork row routes three
corrections with *"No new dispatch — it rides the fix round that already owes the other two"*
(grep that phrase), and the feature's live
dispatch log carries **seven** `type=fix` rows (`grep -c 'type=fix' <feature>/reports/.dispatch-log`).
Within a module, a review-driven fix is cheap, attributed and reviewable. The gap is precisely and
only at the boundary.

---

## Candidate designs

### A — a cross-module `type=fix` dispatch class in the hook

Admit `[task N fix]` where `N` is below `MANIFEST_TASK_START`, under a narrower gate: log a distinct
type (say `type=fix-carry-forward`), skip the flat Check 5c/5d lookups that cannot be satisfied for
an archived task, and require an explicit ledger row naming the finding.

*Cheapest variant:* rather than admitting out-of-range ids, **reserve a carry-forward task id inside
every module's declared range** at plan time. The range check then passes with no hook change at
all, and the reserved id carries the normal gate stack. This keeps enforcement intact and moves the
whole problem into `writing-plans`.

- **For:** the marker vocabulary and the log format already exist (N26); the fix cycle is a proven
  shape; attribution stays machine-readable.
- **Against:** it modifies `sdd-pre-dispatch-hook.sh`, which is in
  `tests/ARaymond-hook-baseline/baseline.txt` — **the implementing task owes a same-change
  `bash tests/ARaymond-hook-baseline/check-hooks.sh --capture` plus a committed `baseline.txt`**, a
  standing obligation this repo enforces. It must also settle the `_merged_dispatch_times` exclusion
  question on both sides of that SSOT, and it weakens the one guard that currently makes module
  boundaries mean something. The reserved-slot variant avoids all of this and should be costed
  first.

### B — a deviations-ledger lane (formalize what already happens)

Make the carry-forward explicit and checkable: a named table in `deviations.md` (the Deferred Work
table, promoted from ad-hoc to specified), **paired with the mandatory plan-text amendment in the
owning module's file** — because the plan is what the future implementer reads and the archive is
not. Add a mechanical check that every carry-forward row names a task inside a not-yet-completed
module's range, and that the owning task's plan text mentions it.

- **For:** zero hook changes, zero baseline re-capture, no enforcement weakened. It is the shape
  this sprint used twice successfully, so it is proven rather than proposed. It puts the instruction
  where instructions get read.
- **Against:** it is a *routing* lane, not a *dispatch* lane — it defers the fix rather than
  enabling it now. It also adds a checked artifact to a file three writers already share, so the
  check must be append-tolerant.

### C — re-open the archived module

Reverse the transition: restore `archive-<module>/` contents into `reports/`, restore the dispatch
log, reset `task_range`, then re-run the transition afterwards.

- **For:** conceptually clean — the module genuinely is not done.
- **Against:** **no inverse operation exists** (a-file, §Today's rule), so today this is a manual
  sequence of file moves plus a hand-edited manifest, performed under an enforcement system designed
  to detect exactly that kind of hand-editing. It also invalidates `validate_module_completion`'s
  earlier verdict without recording that it did. Building the inverse is a larger change than either
  A or B and buys the least.

---

## Enforcement interactions, summarized

| gate | where | interaction with a cross-module fix |
|---|---|---|
| task-range validation | hook, before all checks | **The actual blocker.** Refuses out-of-range ids, `exit 2` (a-run) |
| Check 4c — dispatch provenance | hook | Already boundary-aware: skips when `PREV < MANIFEST_TASK_START` (N3a); re-verified at transition by `validate_module_completion`. Not reached in case A |
| Check 5c — checkpoint file | hook | Flat lookup; archived checkpoint invisible; a fresh checkpoint is required and is satisfiable |
| Check 5d — partner review | hook | Flat lookup; archived partner review does **not** satisfy it, and the provenance row it also demands was truncated at the boundary |
| Check 9 — git reality | `controller-checkpoint.py` | **No interaction.** `if not verification_ids: return []`, and `_merged_dispatch_times` parses only `type=implementer` |
| N26 fix rows | hook writes, checkpoint reads | `type=fix` / `type=fix-unattributed` deliberately excluded from Check 9's window; a new type must decide whether it inherits that, on both sides of the SSOT |

---

## Recommendation and rollout risk

**Adopt B. Cost A's reserved-slot variant as the follow-on if B proves too slow. Do not build C.**

Rollout risk for B is low but not zero:

- **It changes a shared file's contract.** `deviations.md` already has multiple writers in a module;
  a specified table plus a mechanical check must be append-tolerant, and the check must not fire on
  the historical rows that used the ad-hoc `0→N` notation.
- **It is guidance, and guidance is skippable.** The check is what makes it more than a habit; ship
  the check with the convention or expect the convention to decay.
- **Where the guidance lives matters.** If B's convention needs controller-facing protocol text, it
  goes in `skills/subagent-driven-development/references/` — **not** in `SKILL.md`, which is at its
  word ceiling (this sprint's plan carries that as a binding Contract Constraint).
  `references/context-handoff-protocol.md` is the precedent for a runtime-facing protocol doc.

**What would change the recommendation:** if a future sprint hits a module-N defect that genuinely
blocks module N+1 more than once, B's defer-and-route shape stops being sufficient and A's
reserved-slot variant becomes the cheaper answer. One occurrence is an anecdote; two is a signal.

---

## Residual — the case no candidate handles

A defect in module N's files that **blocks** module N+1 immediately. B defers it; A's out-of-range
form needs a hook change; C needs an inverse that does not exist. Today's least-bad answer is a
controller-owned direct edit recorded as a deviation — and this sprint deliberately **declined** to
do that twice, on the grounds that *"the controller editing implementer output directly would both
pollute context and bypass the review cycle"* (grep that phrase in `deviations.md`; the sibling row
scoping an implementer out of a controller-owned file states the same rule). That reasoning is sound and is
exactly why the residual is real rather than solved. **Naming it is the honest outcome here; do not
read B's recommendation as covering it.**

## What could not be established

- **Whether the reserved-slot variant survives `validate-plan.py`.** A reserved id with no steps
  might trip the plan validator's task-structure checks. Not tested — it is an implementation
  question and this spike ships no implementation. A future task should run it before costing A.
- **Whether the `type=fix`-row-before-refusal property has ever mattered in practice.** Observed in
  the fixture (a-run); no live instance was searched for.
- **Frequency.** Four instances in one sprint is the entire evidence base. Whether cross-module
  carry-forward is common enough to justify any tooling is unmeasured.

---

## BACKLOG row

Filed as **N81**, appended verbatim to `docs/process-improvement-findings/BACKLOG.md`. The id was
allocated at execution time against **both** `main` and this branch — `main`'s highest is N78 and
this branch adds N79, so N80/N81 are the first pair free on both. Enumerating this branch alone is
what produced the earlier N76 collision (`deviations.md`, "Cross-branch BACKLOG id collision").

```
| N81 | Sanctioned carry-forward fix lane across module transitions | SP4 design spike, `cmux-spawn-v2` Module 1 Task 3, 2026-07-31 | friction, quality | M | open | **Design doc: `2026-07-30-sp4-carry-forward-fix-lane-design.md`. Spike deliverable was design-only; nothing implemented.** Problem: a defect found in module N+1 whose fix belongs to module N's files has no dispatch lane. **Measured blocker (a-run, isolated fixture with `task_range` [4,8]):** a `[task N fix]` dispatch naming an out-of-range task id is refused by the hook's task-range validation (`BLOCKED: Task N is outside the manifest's task_range`) **before** Checks 4b/4c/5c/5d are reached — an in-range fix control passes that guard and reaches the normal gate stack, and a plain out-of-range implementer control returns the same message. So this is a module-boundary question, not a review-gate question. Note the `type=fix` row is written *before* the refusal, so the dispatch log records fix *attempts*. **Not a constraint:** Check 9 `_check_verification_git_reality` short-circuits on `if not verification_ids: return []` and `_merged_dispatch_times` parses only `type=implementer`, so N26's `type=fix` / `type=fix-unattributed` rows never open a window — any new dispatch type must decide explicitly whether it inherits that exclusion, on both sides of that SSOT. **Also flat (not archive-aware):** Check 5c's checkpoint lookup and Check 5d's partner-review lookup, so an archived partner review does not satisfy 5d and the provenance row it also wants was truncated by `transition-module.py` (which `shutil.move`s `task-<NNN>-*` into `archive-<module>/` and truncates the live dispatch log after copying it). **Recommendation: design B** — formalize the plan-amendment + deviations-ledger routing lane this sprint already used twice (Task 0 finding 4's consumer half became a Module 3 plan amendment at `949d310`; findings tagged `0→9` and `0→17`; the Deferred Work table), because it touches no baselined hook and puts the instruction where the future implementer reads it. **Costed alternative:** reserve a carry-forward task id inside every module's declared range at plan time — the range check then passes with no hook change; verify it survives `validate-plan.py` first. **Rejected:** re-opening an archived module (`transition-module.py` has no inverse). **If any variant edits `sdd-pre-dispatch-hook.sh` it is baselined — the implementing task owes a same-change `check-hooks.sh --capture` plus committed `baseline.txt`.** Residual stated in the doc and NOT solved by B: a module-N defect that blocks module N+1 immediately still has no lane. Evidence base is four instances in one sprint; frequency is unmeasured. |
```
