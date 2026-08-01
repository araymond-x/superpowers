---
schema_version: 1
task_id: 5
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "tests/unit/test_models/test_sdd_session_model.py"
    description: "Added three mutation-killing tests to class TestHandoffBlock, closing quality-review findings 1-3: test_expected_hops_accepts_one (pins the valid ge=1 boundary, which is micro tier's production value), test_rejects_invalid_spawn_policy (behavioral literal rejection, symmetric to Task 4's test_rejects_invalid_value), test_expected_hops_must_be_an_integer (pins int-ness; 2.5 must raise). +16 lines, test-only."
tests:
  written: 3
  passing: 3
  command: ".venv/bin/python3 -m pytest tests/unit/test_models/ -q"
  result: PASS
contract_compliance:
  - constraint: "Fix round is test-only — no production code change. All three assertions must already pass against sdd_session.py exactly as committed at f91b94f."
    status: compliant
    detail: "Commit d1741e0 touches exactly one file (+16 lines), the test file. sdd_session.py sha256 in the working tree equals `git show f91b94f:skills/scripts/models/sdd_session.py | shasum -a 256` (3d134179...525282fe), re-checked after EACH of the three mutation restores, not only at the end. git status --porcelain does not list sdd_session.py."
  - constraint: "Contract Constraints: expected_hops = ceil(total_tasks / 2.5) standard, 1 micro."
    status: compliant
    detail: "test_expected_hops_accepts_one pins the micro-tier value 1 as ACCEPTED — the half of the conjunction the original test_expected_hops_must_be_positive omitted, which is why ge=1 -> ge=2 previously survived the whole suite."
  - constraint: "Write scope: exactly one file, tests/unit/test_models/test_sdd_session_model.py."
    status: compliant
    detail: "git show --name-only d1741e0 lists only that file. No production model, script, or plan document touched."
---

## Implementation Summary
Closed the three surviving mutations found by the round-1 adversarial quality review by adding three tests to the existing `class TestHandoffBlock`. No production code changed: all three assertions pass against `sdd_session.py` exactly as committed, so the fix carries zero behavioral risk. Suite moved 671 → 674 (`tests/unit/`) and 175 → 178 (`tests/unit/test_models/`).

## Source Files Read
None as contracts — Module 2 declares `Source Contracts: None`. Read as references: `tests/unit/test_models/test_plan_model.py` (Task 4's `test_rejects_invalid_value`, the style the new `test_rejects_invalid_spawn_policy` mirrors) and `skills/scripts/models/sdd_session.py` (read-only; mutated and restored for discrimination proofs).

## CLAUDE.md Files Read
- Repository root `CLAUDE.md` — worktree rules (never delete/recreate the symlinked `.venv`, never `git add -A`, never `git stash`) and the pytest-not-unittest preference.
- No `CLAUDE.md` in `tests/unit/test_models/`.

## Deviations from Plan
- These three tests are **not in the plan text** — they are round-1 quality-review findings, prescribed verbatim by the reviewer and dispatched by the controller. This is a `[task 5 fix]` round, not new plan scope.
- The fix subagent used `git checkout --` rather than the scratchpad backup to restore `sdd_session.py` between mutations (more reliable); the backup was still taken and retained.

## Concerns
1. **Test-to-test coupling between the two new tests, visible only under mutation.** Mutation 1 (`ge=1` → `ge=2`) failed `test_expected_hops_accepts_one` (the intended target) **and** `test_rejects_invalid_spawn_policy`. Mechanism: the latter hardcodes `expected_hops: 1`, so under `ge=2` Pydantic collects two errors, and because `expected_hops` is declared before `spawn_policy`, `errors()[0]["type"]` is `greater_than_equal` rather than the asserted `literal_error`. **This cannot occur against unmutated code** — there `expected_hops: 1` is valid and `literal_error` is the only error. A one-token decoupling exists (use `expected_hops: 3` in the second test; same guard, no coupling). The fix subagent deliberately did NOT take it, on the grounds that a fix round should not unilaterally deviate from reviewer-prescribed code — escalated to the controller instead. **Controller disposition: routed to the round-2 quality review to adjudicate** rather than decided unilaterally; the coupling degrades mutation-diagnosis signal (which this feature leans on heavily) while being inert in production.
2. **The pre-commit format hook did not fire again** (second consecutive commit). `git diff HEAD` on the test file is empty and the commit is exactly +16 lines. Consistent with the Task 5 implementer's observation; the partner-verified prediction that it would fire has now failed twice.

## Self-Review Findings
- **Each new test was proven to discriminate** — added, then the guarded property was mutated and the suite re-run, with `__pycache__` cleared between every run and `-p no:cacheprovider` (the round-1 reviewer's battery was corrupted by exactly this staleness, so the precaution was carried forward):
  - `ge=1` → `ge=2` → `2 failed, 672 passed` — `test_expected_hops_accepts_one` plus the coupled second test (Concern 1).
  - `mode="before"` validator coercing unknown `spawn_policy` → `"auto"` → `1 failed, 673 passed`, **only** `test_rejects_invalid_spawn_policy`.
  - `expected_hops: int` → `float` → `1 failed, 673 passed`, **only** `test_expected_hops_must_be_an_integer`.
- **Mutation 2 was chosen to be strictly stronger than the obvious one.** Widening `SpawnPolicy` to `str` would also kill the pre-existing `test_spawn_policy_literal_is_closed_set`, and so would not demonstrate the finding. The coercing validator leaves the annotation — and therefore `get_args` — untouched, so the annotation guard stayed **green** while only the new behavioral guard fired. The finding is proved, not asserted.
- **Collateral bounding measured, with a positive control.** `/usr/bin/grep -rn "expected_hops" tests/ --include='*.py'` matches `test_sdd_session_model.py` only; the unfiltered grep was run first and did fire (listing that file plus its `.pyc`), so the narrow result is a measurement rather than a silent miss. This is what makes "sole new failure" meaningful for mutations 1 and 3.
- **Final restore verified two ways:** `git status --porcelain` does not list `sdd_session.py`, and its working-tree sha256 equals the committed blob's.
- Suite counts from clean post-restore runs: `tests/unit/test_models/` **178 passed** (was 175), `tests/unit/` **674 passed** (was 671) — exactly +3 in both, so no test silently failed to collect.
