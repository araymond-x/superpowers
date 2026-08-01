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
   deliberately excluded from Check 9's window. This feature's own dispatch log carries a run of
   live `type=fix` rows — **count them with the command in §The observed friction rather than
   reading a number here**; the log is append-only and every fix round appends to it. Nothing about
   the in-module lane needs work.
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
- **The dispatch-log row is written *before* the refusal — for both dispatch classes, by design.**
  In case A the log ends up carrying `DISPATCH fix task=2 type=fix` for a dispatch that never
  happened. Case C, the plain out-of-range implementer, is the sibling that matters more: it leaves
  `DISPATCH implementer task=2 type=implementer`. So the general property is **the dispatch log
  records dispatch *attempts*, not dispatch *dispatches*** — not a `type=fix` quirk.

  The placement is deliberate, and the hook says so at the Stage 2 implementer-logging site:
  *"Written here in Stage 2 — BEFORE the enforcement gate below — so the timestamp is recorded even
  when the dispatch is ultimately blocked."* **That comment governs the `type=implementer` write
  specifically.** The `type=fix` write happens at a different, earlier site — the Stage 0 marked-fix
  branch — whose own comment addresses a different question entirely: *"Marked fix → log type=fix
  ONLY (skip Stage 2's type=implementer write so Check 9's window isn't moved"*. Both writes precede
  the range guard; only one of them carries the "recorded even when blocked" rationale.

  **The two classes are not equally benign, and this is the consequential half.** `type=fix` is
  invisible to Check 9 (below), so a stale fix row costs nothing. `type=implementer` is exactly what
  `_merged_dispatch_times` compiles, so a row left by a *refused* implementer **can open or shift a
  Check 9 verification window** — a real, if unquantified, effect on a gate that cross-references
  the log against git. Any design that routes cross-module fixes through the hook inherits the
  attempts-not-dispatches property; a design that reuses the plain implementer path inherits the
  Check-9 visibility too.

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

### Three flat lookups a re-opened task would trip (a-file)

`CLAUDE.md` documents exactly five archive-aware lookups; **every other report glob is intentionally
flat.** Verified for the three gates a carry-forward fix would meet — `grep -c 'archive-'` over the
hook returns two hits, and they are one explanatory comment plus one line of code, the Check 5
Task-0 glob (`T0_GLOB`, the N10 fix). So there is exactly **one** archive-aware lookup in the hook,
carried by a single construct. Therefore:

- **Check 4's N-1 report globs** — the one that fires *earliest*, and the one this section
  originally missed. `task_report_glob` builds
  `"${REPORTS_DIR}/task-${padded}-${report_type}*"` with **no `archive-*` term**, and all three of
  Check 4's N-1 lookups go through it (`IMPL_GLOB`, `SPEC_GLOB`, `QUAL_GLOB`). For a task whose
  predecessor was archived, all three miss, and the dispatch collects three file-existence errors
  before either 5c or 5d is consulted.
- **Check 5c** builds `CHECKPOINT_FILE="${REPORTS_DIR}/checkpoint-pre-dispatch-${TASK_PADDED}.json"`
  with no archive fallback. The completed module's checkpoint was moved into `archive-<module>/`, so
  the controller must write a **fresh** one. This is satisfiable and arguably correct — a new
  dispatch should have a new checkpoint — but a designer should know the archived one is invisible.
- **Check 5d** builds `PARTNER_FILE="${REPORTS_DIR}/partner-review-${TASK_PADDED}.md"`, also flat.
  An archived partner review does **not** satisfy it, so re-opening an archived task demands a
  brand-new partner review *and* a matching `type=partner-review` dispatch-log row — and the live
  log was truncated at the boundary, so the row must be re-earned by a real dispatch.

Check 4c is the only one that handles the boundary, and only on its own keying: it skips when
`PREV < MANIFEST_TASK_START` (the N3a guard), with boundary provenance re-verified at transition
time by `validate_module_completion`. **Its sibling sub-block inside Check 4 does not share that
keying** — the N-1 file-existence block skips on `TASK_NUMBER -eq MANIFEST_TASK_START`, which covers
the module's *first* task and no other below-range id. Over today's reachable domain the two are
equivalent, because the range guard runs first, so every dispatch arriving at Check 4 already has
`TASK_NUMBER >= MANIFEST_TASK_START`, where `-eq START` ⟺ `PREV -lt START`. They diverge only under
Candidate A, which is precisely the design that admits ids below the start. But all of this only
matters if a dispatch gets that far, and under today's rule case A shows it does not.

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

**2. Findings tagged `0→9` and `0→17`.** Count them with `grep -cE '^\| 0→' deviations.md` rather
than trusting a number written here — these rows carry a two-number Task column, findings
**originating** in Task 0 but **owned** by Tasks 9 and 17, both in later modules. (Anchor the
pattern to the start of the Task column. A bare `grep -c '0→'` over-counts, because later rows
*quote* the `0→N` notation in prose while carrying an ordinary single-number Task id — the same
self-invalidation that afflicts any count of a string this sprint keeps writing about.) The `0→N`
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
(grep that phrase), and the feature's live dispatch log carries one `type=fix` row per review-driven
fix round. **Count them; do not read a count here:**

    /usr/bin/grep -c 'type=fix' <feature-dir>/reports/.dispatch-log

That log is live and append-only, and **every fix round appends to it — including the rounds that
edited this very sentence** — so any number written down here is stale before it is committed. The
one figure safe to record is revision-anchored: **7 at commit `0e4b420`**, and it has grown at each
fix round since. Within a module, a review-driven fix is cheap, attributed and reviewable. The gap
is precisely and only at the boundary.

---

## Candidate designs

### A — a cross-module `type=fix` dispatch class in the hook

Admit `[task N fix]` where `N` is below `MANIFEST_TASK_START`, under a narrower gate: log a distinct
type (say `type=fix-carry-forward`), skip the flat lookups that cannot be satisfied for an archived
task — Check 5c's checkpoint, Check 5d's partner review, **and Check 4's N-1 report globs
(`IMPL_GLOB`/`SPEC_GLOB`/`QUAL_GLOB` via `task_report_glob`), which fire first and which the
existing skip does *not* cover**: that skip keys on `TASK_NUMBER -eq MANIFEST_TASK_START`, whereas
Check 4c keys on `PREV -lt MANIFEST_TASK_START`. Admitting a below-range id is exactly what pulls
those two apart, so Check 4 would block on archived files while Check 4c waved the same task
through — and require an explicit ledger row naming the finding.

*Variant, and it needs re-costing before it is called cheapest:* rather than admitting out-of-range
ids, **reserve a carry-forward task id inside every module's declared range** at plan time. The
range check then passes with no hook change at all, and the reserved id carries the normal gate
stack. This keeps enforcement intact and moves the whole problem into `writing-plans`.

**The gate that does *not* police this — measured, and the obvious place to look is the wrong
one.** `validate-plan.py` accepts a plan carrying a reserved slot: `blockers: []`, `status:
WARNING`. It is not a weak validator; a negative control on the same fixture
(`enforcement_tier: bogus`) produces 2 blockers. It simply does not gate this. **Do not use it to
sanity-check the variant** — it will report PASS and tell you nothing.

**Three gates bite, and the earliest one is not terminal.** All three measured against an isolated
fixture (`task_range` [4,8], slot 6 reserved, module 2 = tasks 4–8), each with a passing control:

- **The hook's Checks 4b/4c, on the *following* task.** The earliest and bluntest of the three, and
  the one a reader is least likely to predict — an unused slot is the *previous* task for the next
  in-module dispatch, and the N3a boundary skip-guard, `elif [ "$PREV" -lt "$MANIFEST_TASK_START" ]`,
  does **not** arm for it, because the slot sits inside the active range. So both the N-1
  file-existence sub-block and the dispatch-provenance sub-block run against an empty slot.
  Measured with tasks 4–5 complete and every one of task 7's own artifacts pre-satisfied, so 4b/4c
  were the only variable: dispatching task 7 returns `exit 2` carrying five simultaneous errors — no
  implementer report, no spec review and no quality review found for Task 6, plus no spec-review and
  no quality-review dispatch recorded for Task 6. **Positive control:** restoring slot 6's three
  reports and its two Check-4c provenance rows returns `rc=0` on the same fixture, so the five
  errors are a delta attributable to the empty slot and nothing else. (Two, not three, because
  Check 5d's `type=partner-review` row is owed by the *dispatched* task, not by the previous one —
  see the always-used cost below.) **This gate is placement-dependent** — see below.
- **`transition-module.py:validate_module_completion`** — terminal (module close). It iterates
  `for task_id in module.task_ids:` and appends `"Task {task_id}: missing or empty implementer
  report"`. An **unused** reserved slot therefore **hard-blocks the module transition** — the module
  cannot close. Because it keys on the *manifest*, it fires at any placement and in any plan shape:
  measured identically with and without a `### Task N` section for the slot.
- **`controller-checkpoint.py:all_tasks_have_reports`** — terminal (pre-completion), a blocker (its
  failure appends `all_tasks_have_reports` to `blockers`). Measured on a fixture whose reserved slot
  went unused: `{'pass': False, 'missing': [6]}`, against a positive control returning
  `{'pass': True, 'missing': []}` once the slot's report exists, and a negative control that also
  removes task 5's report and returns `{'pass': False, 'missing': [5, 6]}`. **It keys on the plan's
  `### Task N` headers, while `validate_module_completion` keys on the manifest's `module.task_ids`
  — two different keys, and the difference is not cosmetic.** A slot declared *only* as a widened
  manifest `task_ids` range, with **no `### Task N` section**, is invisible to this gate: measured on
  the same fixture with the header removed, `{'pass': True, 'missing': []}`. The two keys catch the
  same unused slot only in the shape where both are populated.

**Placement is a design variable, and this doc deliberately does not settle it.** Where the reserved
slot sits in the module's range changes which gates can see it at all:

- **Interior** (any position but the last id in `task_range`) — caught **three** ways *when the slot
  carries a `### Task N` section*, and **two** when it is manifest-only. The next in-module dispatch
  hits Checks 4b/4c, and both terminal gates fire later — except that `all_tasks_have_reports` drops
  out of the manifest-only shape (below). The failure surfaces early and loudly, mid-module.
- **Last-in-range** — caught only by the **two terminal** gates *in the headered shape*, and by
  `validate_module_completion` alone when it is manifest-only. The dispatch that *would* test the
  slot is the one for the next task id, and that id is outside `task_range`, so the range guard
  refuses it first. Measured on the same fixture: dispatching task 9 against `task_range` [4,8]
  returns `BLOCKED: Task 9 is outside the manifest's task_range [4, 8]` and says nothing about task
  8. The failure surfaces late, at module close.

Neither placement is recommended here. They trade *when you find out* against *how much of the
module you have already built*, and that trade belongs to whoever costs the variant. Placement also
interacts with the plan-shape axis above: a manifest-only, last-in-range unused slot is caught by
`validate_module_completion` alone.

**So the variant forks, and no branch is free:**

- **Slot left unused** (the whole point of reserving it) — blocked, but by *which* gates depends on
  placement and plan shape: all three for an interior slot carrying a `### Task N` section, down to
  `validate_module_completion` alone for a manifest-only last-in-range slot. In every combination at
  least one gate blocks, so it is never a no-op.
- **Slot always used** — every module now owes an extra implementer report, spec review, quality
  review, partner review, checkpoint file and **three** provenance rows: `type=spec-review` and
  `type=quality-review` for Check 4c, plus `type=partner-review` for Check 5d, which greps
  `task=$TASK_NUMBER type=partner-review` in the dispatch log itself. (Check 5d's minimum-tier
  branch — keyed on a `partner-review-NNN-minimum-tier.md` file rather than on any plan declaration
  — satisfies the check with **no** provenance row at all, a cheaper shape that itself needs
  costing.) That is a recurring per-module tax, incurred whether or not a carry-forward defect
  exists.

**Conclusion: "cheapest variant" is an unsupported cost claim as written.** A future task costing
this must first decide **three** things — always-used vs may-be-unused, interior vs last-in-range,
and headered vs manifest-only — then price the combination it picks. Its test checklist must include
a **live-hook dispatch of the successor task** (the earliest-firing gate, and the one the terminal
gates hide), alongside `validate_module_completion` and `all_tasks_have_reports`. Not
`validate-plan.py`.

- **For:** the marker vocabulary and the log format already exist (N26); the fix cycle is a proven
  shape; attribution stays machine-readable.
- **Against:** it modifies `sdd-pre-dispatch-hook.sh`, which is in
  `tests/ARaymond-hook-baseline/baseline.txt` — **the implementing task owes a same-change
  `bash tests/ARaymond-hook-baseline/check-hooks.sh --capture` plus a committed `baseline.txt`**, a
  standing obligation this repo enforces. It must also settle the `_merged_dispatch_times` exclusion
  question on both sides of that SSOT, and it weakens the one guard that currently makes module
  boundaries mean something. The reserved-slot variant avoids the hook edit and the baseline
  re-capture — but not the cost, which lands instead on the hook's Checks 4b/4c at the next
  in-module dispatch, `validate_module_completion`, and `all_tasks_have_reports` as shown above.
  Cost it first, but cost it honestly.

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

**Scope warning.** This table analyses the **out-of-range form** only — case A, where the dispatch
names a task id below `MANIFEST_TASK_START`. The reserved-slot variant inverts most of it, so it
gets its own table below rather than a footnote. Reading the first table as if it covered the
variant is the mistake this section exists to prevent.

### Out-of-range form (case A)

| gate | where | interaction with a cross-module fix |
|---|---|---|
| task-range validation | hook, before all checks | **The actual blocker.** Refuses out-of-range ids, `exit 2` (a-run) |
| Check 4c — dispatch provenance | hook | Already boundary-aware: skips when `PREV < MANIFEST_TASK_START` (N3a); re-verified at transition by `validate_module_completion`. Not reached in case A |
| Check 5c — checkpoint file | hook | Flat lookup; archived checkpoint invisible; a fresh checkpoint is required and is satisfiable. Not reached in case A |
| Check 5d — partner review | hook | Flat lookup; archived partner review does **not** satisfy it, and the provenance row it also demands was truncated at the boundary. Not reached in case A |
| Check 9 — git reality | `controller-checkpoint.py` | **No interaction with `type=fix`.** `if not verification_ids: return []`, and `_merged_dispatch_times` parses only `type=implementer` — but see the attempts-not-dispatches finding: a *refused plain implementer* does leave a `type=implementer` row this check reads |
| N26 fix rows | hook writes, checkpoint reads | `type=fix` / `type=fix-unattributed` deliberately excluded from Check 9's window; a new type must decide whether it inherits that, on both sides of the SSOT |

### Reserved-slot variant (in-range id, may go unused)

The range guard **passes**, so every gate it short-circuits in case A is now genuinely reached — and
the **three** gates that decide this variant are ones the first table never lists.

**The `applies when` column is load-bearing.** The rows split into a *slot-used* group and a
*slot-unused* group. Reading a slot-used row as though it described the unused case is exactly what
makes Check 4c look benign here — it is benign when the slot is used, and it is the earliest-firing
blocker when the slot is interior and unused.

| gate | where | applies when | interaction with a reserved in-range slot |
|---|---|---|---|
| task-range validation | hook | either | **Passes** — that is the entire point of the variant |
| Check 4c — dispatch provenance | hook | **slot USED** | **Reached.** Ordinary in-module provenance applies; no boundary skip involved |
| Check 5c — checkpoint file | hook | **slot USED** | **Reached and satisfiable** — the reserved task belongs to the *current* module, so nothing was archived and the flat lookup is correct |
| Check 5d — partner review | hook | **slot USED** | **Reached and satisfiable** for the same reason — but it means a real partner review plus a real `type=partner-review` provenance row, every time the slot is used |
| **Checks 4b/4c on the *following* task** | hook | **slot UNUSED, INTERIOR placement** | **BLOCKS — and this is the earliest-firing of the three.** The unused slot is the previous task for the next in-module dispatch, and N3a's `elif [ "$PREV" -lt "$MANIFEST_TASK_START" ]` skip-guard does not arm inside the range. Measured: `exit 2` with five errors — no implementer report, no spec review, no quality review for the slot, plus no spec-review and no quality-review dispatch recorded — against an `rc=0` positive control with the slot used. **Does not apply to a LAST-IN-RANGE slot:** the successor dispatch is out of range and the range guard refuses it first |
| `validate_module_completion` | `transition-module.py` | **slot UNUSED**, any placement, any plan shape | **BLOCKS** at module close. `for task_id in module.task_ids:` → `"Task {task_id}: missing or empty implementer report"`. The module cannot transition. Manifest-keyed — measured identically with and without a `### Task N` section for the slot |
| `all_tasks_have_reports` | `controller-checkpoint.py` | **slot UNUSED *and* the slot has a `### Task N` section** | **BLOCKS** at pre-completion. Measured `{'pass': False, 'missing': [6]}`; positive control `{'pass': True}` once the report exists; negative control also removing task 5's report → `{'pass': False, 'missing': [5, 6]}`. Keys on `### Task N` headers, not manifest ids — so a **manifest-only slot is invisible here** (measured `{'pass': True}`) |
| `validate-plan.py` | plan-validation gate | either | **No interaction — measured `blockers: []`.** Named here only to retire it: it is the gate a reader reaches for, and it does not police this |

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

- ~~**Whether the reserved-slot variant survives `validate-plan.py`.**~~ **Now measured, and the
  question was aimed at the wrong gate.** It survives — `blockers: []`, with a negative control
  (`enforcement_tier: bogus` → 2 blockers) proving the validator can block and simply does not block
  this. The gates that actually bind are the hook's **Checks 4b/4c on the following task**,
  `validate_module_completion`, and `all_tasks_have_reports` (§Candidate A). Recorded as a
  correction rather than deleted, because "run `validate-plan.py` first" was this doc's own advice
  and a future reader may have taken it.
- **Whether the reserved slot is intended always-used or may-be-unused.** This is the open question
  that replaces the one above, and it decides the cost: an unused slot is blocked by one to three
  gates depending on the two axes below, while an always-used slot levies a per-module review tax.
  The variant cannot be costed until it is answered.
- **Where in the module's range a reserved slot should sit — interior or last.** A second,
  independent axis, deliberately left open. In the **headered** shape, an **interior** unused slot
  is caught three ways and fails **early**, at the next in-module dispatch, while a
  **last-in-range** one is caught only by the two terminal gates and fails **late**, at module
  close. A **manifest-only** slot subtracts `all_tasks_have_reports` from both counts (the plan-shape
  axis below), leaving two and one. Both placements measured (§Candidate A). Naming the axis
  is this doc's job; choosing it belongs to the costing task, because the choice trades early
  detection against how much of the module is already built when the block lands.
- **Whether a reserved slot should carry a `### Task N` section at all.** A third axis: the slot can
  be declared as a widened manifest `task_ids` range alone. Measured — that shape is invisible to
  `all_tasks_have_reports`, and is caught by `validate_module_completion` alone **only when it is
  also last-in-range**; a manifest-only *interior* slot is still caught by the hook's Checks 4b/4c on
  the following task, so two gates, not one. Cheaper to write, weaker to police.
- **Whether the attempts-not-dispatches property has ever mattered in practice.** Observed in the
  fixture for both `type=fix` and `type=implementer` (a-run); the `type=implementer` case is
  Check-9-visible in principle, but **no live instance of a perturbed Check 9 window was searched
  for.** Mechanism proven, incidence unmeasured.
- **Frequency.** Four instances in one sprint is the entire evidence base. Whether cross-module
  carry-forward is common enough to justify any tooling is unmeasured.

---

## BACKLOG row

Filed as **N81**, appended verbatim to `docs/process-improvement-findings/BACKLOG.md`. The id was
allocated at execution time against **both** `main` and this branch — `main`'s highest is N78 and
this branch adds N79, so N80/N81 are the first pair free on both. Enumerating this branch alone is
what produced the earlier N76 collision (`deviations.md`, "Cross-branch BACKLOG id collision").

```
| N81 | Sanctioned carry-forward fix lane across module transitions | SP4 design spike, `cmux-spawn-v2` Module 1 Task 3, 2026-07-31 | friction, quality | M | open | **Design doc: `2026-07-30-sp4-carry-forward-fix-lane-design.md`. Spike deliverable was design-only; nothing implemented.** Problem: a defect found in module N+1 whose fix belongs to module N's files has no dispatch lane. **Measured blocker (a-run, isolated fixture with `task_range` [4,8]):** a `[task N fix]` dispatch naming an out-of-range task id is refused by the hook's task-range validation (`BLOCKED: Task N is outside the manifest's task_range`) **before** Checks 4b/4c/5c/5d are reached — an in-range fix control passes that guard and reaches the normal gate stack, and a plain out-of-range implementer control returns the same message. So this is a module-boundary question, not a review-gate question. **Attempts, not dispatches — and it is not a `type=fix` quirk:** the dispatch-log row is written BEFORE the refusal for BOTH classes, deliberately — the hook's Stage 2 comment reads *"Written here in Stage 2 — BEFORE the enforcement gate below — so the timestamp is recorded even when the dispatch is ultimately blocked"* (that comment governs the `type=implementer` write; the `type=fix` write sits at the earlier Stage 0 marked-fix branch under a comment about a different concern). The two are NOT equally benign: `type=fix` is invisible to Check 9, but a refused plain implementer leaves `DISPATCH implementer task=N type=implementer`, which is exactly what `_merged_dispatch_times` compiles — so a stale row CAN open or shift a Check 9 window. Mechanism proven in a fixture; no live instance searched. **Not a constraint:** Check 9 `_check_verification_git_reality` short-circuits on `if not verification_ids: return []` and `_merged_dispatch_times` parses only `type=implementer`, so N26's `type=fix` / `type=fix-unattributed` rows never open a window — any new dispatch type must decide explicitly whether it inherits that exclusion, on both sides of that SSOT. **THREE flat (not archive-aware) lookups, and the first is the one most easily missed:** Check 4's N-1 report globs (`IMPL_GLOB`/`SPEC_GLOB`/`QUAL_GLOB`, all built by `task_report_glob` with no `archive-*` term — so all three miss for an archived predecessor, and they fire BEFORE 5c/5d), Check 5c's checkpoint lookup, and Check 5d's partner-review lookup, so an archived partner review does not satisfy 5d and the provenance row it also wants was truncated by `transition-module.py` (which `shutil.move`s `task-<NNN>-*` into `archive-<module>/` and truncates the live dispatch log after copying it). Check 4's N-1 skip keys on `TASK_NUMBER -eq MANIFEST_TASK_START` while Check 4c keys on `PREV -lt MANIFEST_TASK_START` — equivalent over today's reachable domain because the range guard runs first, but DIVERGENT under any design admitting below-range ids, where Check 4 blocks on archived files while Check 4c waves the same task through. **Recommendation: design B** — formalize the plan-amendment + deviations-ledger routing lane this sprint already used twice (Task 0 finding 4's consumer half became a Module 3 plan amendment at `949d310`; findings tagged `0→9` and `0→17`; the Deferred Work table), because it touches no baselined hook and puts the instruction where the future implementer reads it. **Alternative that still needs re-costing (do NOT call it the cheapest yet):** reserve a carry-forward task id inside every module's declared range at plan time — the range check then passes with no hook change. **`validate-plan.py` is the WRONG gate to check it against — measured `blockers: []`, with a negative control (`enforcement_tier: bogus` → 2 blockers) proving the validator can block and simply does not block this.** **THREE gates bind, and the earliest one is NOT terminal:** (1) the hook's **Checks 4b/4c on the FOLLOWING task** — an unused slot is the previous task for the next in-module dispatch and N3a's `elif [ "$PREV" -lt "$MANIFEST_TASK_START" ]` skip-guard does not arm inside the range, so measured `exit 2` with five simultaneous errors (no implementer report, no spec review, no quality review for the slot, plus no spec-review and no quality-review dispatch recorded), against an `rc=0` positive control with the slot used; (2) `transition-module.py:validate_module_completion` (terminal, module close; iterates `for task_id in module.task_ids:` and appends `Task N: missing or empty implementer report`, so an UNUSED slot hard-blocks the transition — manifest-keyed, therefore placement- and plan-shape-independent); (3) `controller-checkpoint.py:all_tasks_have_reports` (terminal, pre-completion blocker; measured `pass: False, missing: [6]` for an unused slot, positive control `pass: True` once the report exists). **Placement is a DESIGN VARIABLE and is deliberately NOT settled (counts below are for the HEADERED shape; a manifest-only slot subtracts `all_tasks_have_reports` from each):** an INTERIOR unused slot carrying a `### Task N` section is caught all three ways and fails early at the next dispatch (a manifest-only interior slot: two, the hook plus `validate_module_completion`); a LAST-IN-RANGE headered one is caught only by the two terminal gates and fails late at module close (manifest-only last-in-range: `validate_module_completion` alone), because the successor dispatch that would test it is refused first by the range guard (measured: task 9 against `task_range` [4,8] returns the task-range message and nothing about task 8). **Plan shape is a second axis:** `all_tasks_have_reports` keys on `### Task N` headers while `validate_module_completion` keys on manifest ids, so a slot declared ONLY as a widened manifest `task_ids` range is invisible to the former (measured `pass: True`) and caught by the latter alone ONLY when it is also LAST-IN-RANGE — a manifest-only INTERIOR slot is still caught by the hook's Checks 4b/4c on the following task, so two gates, not one. **Cost fork:** an unused slot is blocked by one to three gates depending on those two axes — never a no-op — while an always-used slot makes every module owe an extra implementer report, spec + quality + partner review, checkpoint file and THREE provenance rows (`type=spec-review` + `type=quality-review` for Check 4c, plus `type=partner-review` for Check 5d, which greps `task=N type=partner-review` in the dispatch log itself; Check 5d's minimum-tier branch, keyed on a `partner-review-NNN-minimum-tier.md` file, satisfies it with NO provenance row at all) — a recurring per-module tax. Decide always-used vs may-be-unused, interior vs last-in-range, and headered vs manifest-only BEFORE costing, and make the test checklist include a live-hook dispatch of the successor task rather than only the two terminal gates. **Rejected:** re-opening an archived module (`transition-module.py` has no inverse). **If any variant edits `sdd-pre-dispatch-hook.sh` it is baselined — the implementing task owes a same-change `check-hooks.sh --capture` plus committed `baseline.txt`.** Residual stated in the doc and NOT solved by B: a module-N defect that blocks module N+1 immediately still has no lane. Evidence base is four instances in one sprint; frequency is unmeasured. |
```
