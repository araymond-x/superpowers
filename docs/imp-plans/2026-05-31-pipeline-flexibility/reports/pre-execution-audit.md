# Pre-Execution Audit — Verdict & Remediation Record

**Feature:** pipeline-flexibility
**Date:** 2026-05-31
**Auditor:** general-purpose subagent (binding authority), dispatched per `pre-execution-audit-prompt.md`
**Auditor verdict:** ORDERS_ISSUED (5 orders) → all RESOLVED below
**Controller disposition:** CLEARED for execution after remediation

> **⚠ RENUMBERING NOTE (post-audit):** After this audit, all tasks were renumbered **1-10 → 0-9** (user-approved; see deviations.md) to satisfy the hook's "first task = Task 0" contract. The Order references below use the **original** numbering. Add −1 to map to current task numbers: Order 1 → now Task 8 (e2e); Order 2 → now Task 1 (validate-plan); Order 3 → now Tasks 2/3 (hook); Order 4 → now Task 5 (git-reality); Order 5 → now Task 7 (SDD SKILL.md). The remediation edits live in the renumbered plan files at the correct (current-numbered) locations.

The auditor independently read all 4 plan files, the distilled spec, and the real source/test files, and *empirically verified* its findings by running code (e.g., confirmed `validate-plan.py` exits 2 on WARNING; confirmed the test helpers write frontmatter-less plans; confirmed `run_pre_completion` passes no `--manifest`). The controller re-verified each blocking order against the real files before editing the plan (see evidence per order).

## Remediation Orders & Resolutions

### Order 1 — Task 9 e2e snippets abort under `set -e` (HIGH) — RESOLVED
**Finding:** `tests/integration/sdd-e2e-test.sh` runs under `set -e` (line 4) + an ERR trap (line 5); existing steps neutralize non-zero script exits with `|| true` (lines 102/155/264). Task 9's `RESULT=$($PYTHON ...validate-plan.py... 2>&1)` snippets omitted `|| true`. `validate-plan.py` exits 2 on WARNING, so Step 10 (a deliberate WARNING case) would abort before its `STATUS` check.
**Controller verification:** Read the e2e test — confirmed `set -e`, ERR trap, and the `|| true` convention on lines 102/155/264. Confirmed `validate-plan.py` WARNING→exit 2 (module-1 Task 2 tests assert `exit_code == 2`).
**Fix:** Appended `|| true` to BOTH `RESULT=$(...)` command substitutions in module-3 Task 9 Steps 2 and 3, with explanatory comments tying them to the existing convention.

### Order 2 — Task 2 RED failure-mode misdescribed; hidden Task 1 prerequisite (MEDIUM) — RESOLVED
**Finding:** Before Task 1's `task_type` field lands, `validate-plan.py` on the `FRONTMATTER_PLAN` fixture FAILs with a Pydantic `task_type: Extra inputs are not permitted` blocker (exit 1), not the keyword-absence (exit 2) the step describes. Safe only because `depends_on: [1]`, but a misleading RED if run out of order.
**Controller verification:** Confirmed `Task` model uses `StrictModel` (`extra="forbid"`) and lacks `task_type` pre-Task-1 (read `plan.py`). The dependency graph (Module 1 → 2 → 3, Task 2 `depends_on: [1]`) enforces order within SDD.
**Fix:** Added a prerequisite callout to module-1 Task 2 Step 1/2 stating the Task-1 dependency and the two distinct RED modes (exit 1 Pydantic if Task 1 absent; correct keyword-absence RED with Task 1 present). No snippet/assertion change needed — fixtures are correct post-Task-1.

### Order 3 — Tasks 3/4 verification tests pass vacuously without frontmatter plan (MEDIUM) — RESOLVED
**Finding:** Both `setup_sdd_workspace()` and `setup_manifest_workspace()` write plans WITHOUT YAML frontmatter and set `active_module_file: None`; `get_task_type()` reads `task_type` from frontmatter, so default fixtures yield `"implementation"` universally → verification tests pass without exercising the path. Task 4 stubs were empty comments.
**Controller verification:** Read `sdd_test_helpers.py` — confirmed frontmatter-less plans (lines 210-211, 489-492) and `active_module_file: None`. Confirmed the dispatch-log reviewer format `{ts} DISPATCH reviewer task=N type=<type>` (line 306) — new `type=implementer` entries are additive.
**Fix:** Expanded Task 3 Step 1's "Important" callout into a concrete 3-step recipe (write frontmatter plan with `tasks:`+`task_type:`; point the manifest's `plan_file`/`active_module_file` at it via the hook's `$GIT_ROOT/<plan_file>` resolution; require a positive control). Strengthened Task 4's "Remember" note to bind verification tests to that recipe and require the `test_implementation_task_still_requires_reviews` positive control be built from the SAME setup differing only in `task_type`.

### Order 4 — Task 6 git-reality test reads host repo; format-drift false-PASS risk (MEDIUM-HIGH) — RESOLVED
**Finding:** `run_pre_completion` invokes the checkpoint with `--plan-file`+`--reports-dir`, no `--manifest`, and no `cwd=`. So `dispatch_log_path` resolves to `<reports_dir>/.dispatch-log` and `_check_verification_git_reality` (git_root=None) runs `git log` in the host superpowers repo → potential false FAIL. The writer/reader format must match exactly or the check silently PASSes (false negative — the plan's #1 risk).
**Controller verification:** Read `test_pre_completion_gates.py` — confirmed no `--manifest`, no `cwd=` (lines 141-145, 449-453). Confirmed Task 3 writer format and Task 6 reader regex match.
**Fix:** Replaced Task 6 Step 1's vague "Note" with 5 concrete requirements: (1) log at `<reports_dir>/.dispatch-log`; (2) build the log line verbatim in Task 3's writer format; (3) run the checkpoint subprocess with `cwd=` an isolated `git init` temp repo (or pass explicit `git_root`); (4) make `test_clean_window_passes` non-vacuous (PASS *because* of isolation, despite host commits); (5) control commit dates via `GIT_AUTHOR_DATE`/`GIT_COMMITTER_DATE` for the file-modifying case and assert the blocker names `Task N`.

### Order 5 — "Restricted prompt" defense layer is advisory, not enforced (LOW) — RESOLVED
**Finding:** Spec D3 lists 4 defense layers; layer 4 ("restricted prompt") is delivered only as SKILL.md prose (Task 8) with no mechanical enforcement — a potential silent gap between the spec's claim and the implementation.
**Controller verification:** Confirmed plan has no separate prompt file / `implementer-prompt.md` change / prompt-inspecting gate. Consistent with spec D2 ("dispatch subagent, skip reviews").
**Fix:** Added a disposition note to module-3 Task 8 documenting that the read-only auditor prompt is controller-delivered via SKILL.md and intentionally NOT mechanically enforced, with the Task 6 git-reality check as its mechanical backstop. This is the intended design, not a dropped layer.

## Self-Assessment Cross-Reference (auditor confirmations)
- Dispatch-log writer (Task 3) / reader (Task 6) formats **match exactly**; existing reviewer entries are genuinely additive (nothing greps `type=implementer`). ✔ verified
- `task_type`/`entry_mode` insertion points match the real `plan.py` (`review_tier` line 31, `enforcement_tier` line 43). ✔ verified
- Task 4 hook insertion points (Checks 4b/4c/5d) exist where claimed. ✔ (auditor confirmed)
- Python 3.9 compat: snippets use comment-style `# type:` annotations; `controller-checkpoint.py` already imports `os/re/subprocess/json/Path/Optional`. ✔
- Fixture task-number collision avoidance (91-95) correct; `TASK_HEADER_RE` is fence-blind. ✔
- Parent `tasks: []` → aggregated-10 deviation is consistent with the `Plan` model validators and multi-module convention. ✔

## Post-Remediation Validation
- `validate-plan.py` on all 4 plan files: **0 FAIL** (parent/module-2 WARNING — benign, unchanged class; module-1/module-3 PASS).
- Manifest materialized: `total_tasks=10`, active module 1, standard tier.

## Known Accepted Anomaly (not an order)
- `controller-checkpoint.py --phase pre-execution` reports `source_contracts: FAIL` on prose "Source Contracts: None" — documented false positive (project CLAUDE.md). Dispositioned **Accepted** in `deviations.md`; tool-improvement candidate flagged for the Task 10 SSOT audit. `validate-plan.py` = 0 FAIL; plan-validation-gate passed.

**Gate status: CLEARED.** All blocking orders resolved in the plan before any task dispatch. Proceeding to the task loop (Module 1, Task 1).
