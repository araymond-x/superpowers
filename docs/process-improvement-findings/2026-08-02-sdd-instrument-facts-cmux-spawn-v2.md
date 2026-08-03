# SDD instrument facts verified during cmux-spawn-v2 (2026-08-02)

Cross-cutting "verify the instrument" facts confirmed empirically while running the
cmux-spawn-v2 SDD execution (Module 3 close + Module 3→4 transition, session 14).
Recorded here because they affect **every** SDD feature's gates, not just this one —
the bundle is transport, this file is the durable record.

## 1. `controller-checkpoint.py` `pending_deviations` check is BLIND to trailing-text dispositions — HIGH IMPACT

The pre-dispatch (and pre-completion) `pending_deviations` check reported **`0 pending`**
while `deviations.md` literally contained **17 rows** whose Disposition column read
`Pending — N72 absorption`, `Pending — N70 / N58`, `Pending — task-2-fix`, etc.

- The check matches a bare/exact `Pending` disposition, NOT a `Pending — <trailing text>` form.
- **Consequence for the Pre-Completion Gate:** the SDD skill requires "no undispositioned
  entries (every row has a Disposition other than Pending)." The mechanical checkpoint will
  report clean while rows are still open. **Whoever runs pre-completion must READ the rows,
  not trust the checkpoint's `pending_deviations` field.**
- Reproduce: `grep -cE 'Pending' <deviations.md>` (raw count) vs the checkpoint's
  `pending_deviations` detail. They disagreed 17 vs 0 this session.

## 2. `transition-module.py: validate_module_completion` gates on report-presence + provenance ONLY

Measured by reading the function (not inferred from docs). For each task in the completing module it checks:
- implementer report present (>50 bytes),
- spec review present + dispatch-provenance logged (unless `task_type: verification` or `spec_review_mode: skip`),
- quality review present (full **or** `-minimum-tier`) + provenance logged.

It does **NOT** gate on: deviations.md `Pending` rows, Module AC checkboxes, or task step checkboxes.
So a module boundary transition can proceed with open deviations and unticked AC boxes — those
are a **final Pre-Completion Gate** concern (last module), not a transition blocker.

## 3. `validate-report.py` rejects `tests.passing > tests.written`

The `ImplementerReport` model enforces `passing <= written`. The feature convention (seen across
task-008/009/010/011 reports): `tests.written`/`tests.passing` = **this task's NEW tests**; the
full-suite total goes in the `command` string. A fix report that put the full-suite count (805)
in `tests.passing` was rejected until corrected to per-task (2/2).

## 4. `validate-plan.py` `checkboxes` field is `--plan-file`-scoped only

(Already in CLAUDE.md; restated because it recurs.) The printed `checkboxes` JSON field counts ONLY
the primary `--plan-file` (plan.md), never the `--additional-plan-files` (module files). It reads a
constant small total (10 here) regardless of module-level task progress. Grep the module file directly.

## 5. Post-transition aggregate-gate limitation (known, accepted — BACKLOG)

After module transitions, the pre-completion AGGREGATE gates (Check 7 min-tier ratio, Check 9
git-reality) only see the FINAL module — archived reviews leave the flat glob and the dispatch log
is truncated into the archive. Per-task existence/provenance IS boundary-verified by
`validate_module_completion`; only cross-module policy aggregates lose visibility.
**Specific caution for cmux-spawn-v2 pre-completion:** the Task 11 fix dispatch was logged as
`type=fix`, and that dispatch log is now truncated into `archive-Spawn script core rework/.dispatch-log`.
Whoever runs pre-completion should verify how Check 9 (git-reality) treats task 11 rather than assuming
it resolves — the code change is real (commits `7a224ff`+`532c7b6`) but its log entry is archived.

## Provenance
All five confirmed 2026-08-02 during the cmux-spawn-v2 Module 3 close-out. Suite baseline at that
point: 805 passed / 0 failed, independently re-measured four times (implementer, controller ×2, reviewer).
