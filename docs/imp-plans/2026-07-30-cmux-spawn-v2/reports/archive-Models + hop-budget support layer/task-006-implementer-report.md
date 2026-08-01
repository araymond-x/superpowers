---
schema_version: 1
task_id: 6
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/subagent-driven-development/scripts/_handoff_support.py"
    description: "NEW. Plan Step 3 verbatim: HOP_DIVISOR=2.5, CEILING_FLOOR=6, CEILING_FACTOR=2, plus expected_hops, derive_total_tasks, derive_expected_hops, hop_ceiling. Import-only — no CLI, no argparse, no __main__, no tasks_done/stall (Task 7's scope). No annotations at all, so B7 (no PEP-604 unions, no builtin generics) holds by construction."
  - path: "skills/subagent-driven-development/scripts/materialize-manifest.py"
    description: "Imports expected_hops beside the existing _midpoint import (mid-file, now line 60, matching its noqa: E402 form). Builds the handoff block between total_tasks and the SddSession(...) call using `if spawn_policy is None:` (never `or`), passed as handoff=handoff. Formula imported, not reimplemented — no 2.5/6/2 literal anywhere outside _handoff_support.py."
  - path: "tests/unit/test_handoff_support.py"
    description: "NEW. The plan's 9 tests (TestExpectedHops, TestDeriveTotalTasks, TestDeriveExpectedHops, TestHopCeiling) plus the module-level Shared test helpers block (import subprocess, VENV_PY, SUPPORT, _write_report, _log) placed after SCRIPTS — Task 7 requires them to already exist."
  - path: "tests/unit/test_materialize_manifest.py"
    description: "Added an extra_frontmatter param to make_plan (injects a raw, deliberately unquoted YAML line after enforcement_tier) and the plan's 4-test TestHandoffBlockMaterialization class verbatim."
tests:
  written: 13
  passing: 13
  command: ".venv/bin/python3 -m pytest tests/unit/test_handoff_support.py tests/unit/test_materialize_manifest.py -v"
  result: PASS
contract_compliance:
  - constraint: "Python 3.9 scan asymmetry (B7): _handoff_support.py IS scanned by check_python39_compat — no PEP-604 unions, no builtin generics in annotations. Task 5's inverse rule does not apply here."
    status: compliant
    detail: "The module carries no annotations at all, so both forbidden forms are absent by construction. Verified by the gate itself: validate-all-skills.py reports PASS 160 / FAIL 0 / WARNING 2 — 160 rather than the 159 baseline precisely because Task 6 adds one file to the scanned directory, which is the expected post-change count, not drift. Re-run after commit: same result."
  - constraint: "Never normalize handoff_spawn with `or` — PyYAML is YAML 1.1, so bare `off` is boolean False and `False or \"auto\"` turns a refusal into spawn-without-asking. Use `if spawn_policy is None:`."
    status: compliant
    detail: "Implemented with `if spawn_policy is None:` exactly as the amended Step 6 specifies. Proven live by a hand-run mutation control (see Self-Review): reintroducing `or \"auto\"` makes test_off_survives_and_bare_off_is_never_coerced_to_auto FAIL, so the guard is armed rather than vacuous."
  - constraint: "HOP_DIVISOR / CEILING_FLOOR / CEILING_FACTOR are the SSOT defined in _handoff_support.py; import expected_hops rather than reimplementing the formula inline."
    status: compliant
    detail: "materialize-manifest.py imports expected_hops from _handoff_support and contains no 2.5/6/2 literal. Follows the _midpoint.py import-only-helper-ssot precedent, with the import placed beside the _midpoint one."
  - constraint: "Scope fence: Task 6 is import-only. No CLI, no tasks_done counting, no stall streaks — Task 7 writes the same file and is strictly serialized after."
    status: compliant
    detail: "No argparse, no __main__ block, no tasks_done or stall functions. The one sanctioned exception — the Shared test helpers, which include the CLI seams VENV_PY and SUPPORT — lives in the test file, not the module, as instructed."
  - constraint: "Write scope is exactly four files."
    status: compliant
    detail: "Commit 9b32c25 changed exactly the four owned files. git show --numstat is 64/0, 9/0, 74/0, 34/0 — pure insertions, zero deletions."
---

## Implementation Summary
Created `_handoff_support.py` as the single source of truth for the hop-budget formula (`ceil(total/2.5)` standard, `1` micro), the three-step derivation precedence, and the ceiling default — following the `_midpoint.py` precedent so two consumers cannot drift. Wired `materialize-manifest.py` to import the formula and emit a populated `handoff` block. Suite 674 → **687**, exactly the plan's thirteen tests and nothing else. The e2e suite — the first non-unit gate in this module — stayed green, proving the hook, checkpoint and transition all tolerate the new manifest key.

## Source Files Read
None as contracts — Module 2 declares `Source Contracts: None`. Read as references: `skills/subagent-driven-development/scripts/_midpoint.py` (the `import-only-helper-ssot` pattern reference), `skills/scripts/models/sdd_session.py` (Task 5's landed `Handoff` model), and `tests/unit/test_materialize_manifest.py`'s existing `make_plan` / `run_materialize` idiom.

## CLAUDE.md Files Read
- Repository root `CLAUDE.md` — the `_midpoint.py` SSOT convention ("future SDD scripts that need it MUST import from here"), the Pydantic model inventory, and the worktree rules (never delete/recreate the symlinked `.venv`, never `git add -A`, never `git stash`).
- No `CLAUDE.md` in `skills/subagent-driven-development/scripts/` or `tests/unit/`.

## Deviations from Plan
- **None in the implementation.** The Step 3 and Step 6 code bodies are byte-for-byte the plan's. Step 6's compressed fence — which contains two destinations and is not valid Python as a unit — was split as the dispatch instructed: the import to module scope beside `_midpoint`, the four indented lines into `materialize()`.
- `make_plan(extra_frontmatter=...)` was added by the implementer (the plan requires it; the param did not exist). It injects a **raw, deliberately unquoted** YAML line, which is what lets `handoff_spawn: off` reach PyYAML as bare `off` (boolean `False`) and makes the YAML-1.1 test meaningful. Callers must quote when they want a string.
- Plan checkboxes not ticked — the plan file is outside the four-file write scope (controller-owned).

## Concerns
_The implementer returned `DONE`; the controller upgraded to `DONE_WITH_CONCERNS` when persisting, because the report routes a substantive item to the quality reviewer. The implementation itself is clean and matches the plan verbatim._

1. **`test_off_survives_and_bare_off_is_never_coerced_to_auto` pins `exit_code != 0`, not WHY.** Any unrelated future materialization failure would keep the test green while the consent bypass silently regressed. The implementer deliberately did **not** add a stderr-reason assertion, on the grounds that the plan text is deliberate and has been corrected three times — flagging for the quality reviewer instead, with its own mutation-control result as evidence the gate currently works. **This is the right escalation shape** (same as Task 5's fix round declining to deviate from reviewer-prescribed code) and is routed to the quality review to adjudicate.
2. **The pre-commit ruff hook produced no changes for the third consecutive commit**, despite the partner review establishing it IS wired (`$HOME/Library/Python/3.9/bin/ruff` exists) and despite this commit giving it three unused names to delete (`subprocess`, `HOP_DIVISOR`, `CEILING_FACTOR`). All three survived — which is the outcome Task 7 needs — but the prediction that it would fire has now failed three times, and the reason is no longer "it found nothing."

## Self-Review Findings
- **Step 2 red state verbatim:** `ERROR tests/unit/test_handoff_support.py` … `E ModuleNotFoundError: No module named '_handoff_support'` / `collected 0 items / 1 error` — the collection error the dispatch predicted, not a test FAIL. The Step 5 materialize red was 4 FAILs, all `TypeError: 'NoneType' object is not subscriptable`, i.e. the pre-existing `"handoff": null`.
- **The implementer ran a mutation control the plan did not ask for, because it noticed its red state was incomplete.** The Step 5 red run died on the *first* assertion of the bare-`off` test, so the consent-bypass half was never observed failing — a red state that does not exercise the assertion you care about proves nothing about it. It therefore hand-mutated `materialize-manifest.py` back to `or "auto"` and re-ran: **the test FAILED** (`assert (0 == 0) is False` — materialization succeeded and silently rewrote the refusal to `auto`). Hand-reverted (explicitly not `git stash`), re-ran to 4 passed, `git diff --stat` back to 9 insertions. **The consent gate is live, not vacuous.**
- **Arithmetic self-check passed:** 674 + 9 + 4 = **687 passed**, matching exactly. Targeted trio (support + materialize + models) = 199 passed. No test silently failed to collect, and no test was added beyond the plan's thirteen.
- **e2e closing banner verbatim:** `E2E PIPELINE PASS - 15 steps composed correctly` (exit 0), Steps 1-14 all PASS including Step 14's spawn end-to-end. **No assertion was loosened** — the new manifest key disturbed no consumer.
- **`"handoff": null` is discharged.** A live materialize of a 5-task standard plan with `handoff_spawn: ask` now emits `"handoff": {"expected_hops": 2, "spawn_policy": "ask"}`.
- **All three at-risk names survived the commit**, verified by grep: `import subprocess` (line 13), `HOP_DIVISOR` and `CEILING_FACTOR` (line 9 import block), plus `VENV_PY`, `SUPPORT`, `_write_report`, `_log`. Task 7 depends on these.
