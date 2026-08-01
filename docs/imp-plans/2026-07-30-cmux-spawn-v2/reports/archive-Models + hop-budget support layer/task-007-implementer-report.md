---
schema_version: 1
task_id: 7
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/subagent-driven-development/scripts/_handoff_support.py"
    description: "Added count_tasks_done (frontmatter-verified unique task IDs across reports/ + archive-*/), stall_streak (trailing consecutive equal tasks_done outcome records, 'indeterminate' on a malformed newest record), the _frontmatter helper with a lazily-imported PyYAML whose ImportError propagates, and the _cli entrypoint (tasks-done / expected-hops / stall-streak / spawn-policy) plus the __main__ guard. Hoisted glob/json/os/re/sys one-per-line beside the existing math import."
  - path: "tests/unit/test_handoff_support.py"
    description: "Appended TestTasksDone, TestStallStreak and TestCli (7 tests) exactly as the plan writes them, and applied deferred order R3-1 by adding True to the test_invalid_total_raises garbage tuple. R3-1 strengthens an EXISTING test rather than adding one, so tests.written is 7, not 8."
tests:
  written: 7
  passing: 7
  command: ".venv/bin/python3 -m pytest tests/unit/test_handoff_support.py -q -p no:cacheprovider"
  result: PASS
contract_compliance:
  - constraint: "Python 3.9 scan asymmetry (B7): _handoff_support.py must use no PEP-604 unions and no builtin generics in annotations"
    status: compliant
    detail: "The appended code carries no type annotations at all — no `X | None`, no `dict[str, int]`. check_python39_compat passes in the regression suite (160 PASS / 0 FAIL)."
  - constraint: "tasks_done: unique task IDs whose implementer-report frontmatter parses AND has status DONE/DONE_WITH_CONCERNS; verification reports count under the same statuses; filenames alone never count; scans reports/ AND archive-*/"
    status: compliant
    detail: "count_tasks_done globs both reports/ and reports/archive-*/, requires a parsing frontmatter dict with an int (non-bool) task_id and a status in _DONE_STATUSES, and accumulates into a set so archived duplicates dedupe. task_type is never consulted, so a verification report with empty files_changed counts. Pinned by the two TestTasksDone tests (frontmatter-less task-005 does not count; {1,4} across live+archive == 2)."
  - constraint: "spawn-policy is the SOLE consent gate: an unreadable, missing, or non-object manifest must yield 'ask', never 'auto'"
    status: compliant
    detail: "Implemented verbatim from the plan. Unreadable/absent JSON sets manifest = None in the except branch; valid JSON that is not an object is normalized to None by the isinstance guard; the final expression only reaches the 'auto' arm when `manifest is not None`. Pinned by the missing-file assertion in test_expected_hops_and_policy_cli_on_legacy_and_garbage."
  - constraint: "Never normalize handoff_spawn with `or` (YAML 1.1 bare `off` is False)"
    status: not_applicable
    detail: "The `or`-vs-`is None` hazard lives in materialize-manifest.py, landed by Task 6 and out of this task's write scope. This task added no handoff_spawn normalization; the CLI's spawn-policy path uses an explicit membership test against ('auto','ask','off') rather than truthiness."
  - constraint: "CLI prints unknown / indeterminate as values (exit 0) — degradation is observable, never an exception"
    status: partial
    detail: "expected-hops prints 'unknown' when derive_expected_hops returns None; stall_streak returns 'indeterminate'; all return 0; argparse still exits 2 on usage error. PARTIAL on one measured path: count_tasks_done only reaches the lazy `import yaml` if glob matched at least one report, so on an EMPTY or MISSING reports/ dir under a venv-less python3 the CLI prints '0', not 'unknown' — the 'fake 0 manufactures stalls' case the plan's own comment warns about. Measured, not inferred: with yaml forced unimportable, empty dir -> '0'; one report present -> 'unknown'. Left as-is because the plan's Step 3 body is verbatim what shipped and the dispatch forbids working around a constraint. See Concerns."
  - constraint: "Plan/SddSession extra=forbid, CURRENT_SCHEMA_VERSION stays 1"
    status: not_applicable
    detail: "This task touches no Pydantic model. skills/scripts/models/implementer_report.py was read only, never edited."
---

## Implementation Summary

Appended the remaining `_handoff_support.py` surface — `count_tasks_done`, `stall_streak`, the `_frontmatter` parser, and the `_cli` entrypoint with its four subcommands — plus the seven tests the plan supplies, following the plan's TDD ordering (red at 7 failed / 19 passed, then green at 26). The implementation body and the test bodies are the plan's text verbatim; the only judgement calls were mechanical ones the dispatch pre-authorized: hoisting the five new imports one-per-line beside `import math` in the file's own header style (dropping the plan's now-false `# noqa: E401`), and splitting the plan's two `print(...); return 0` one-liners onto separate lines.

## Source Files Read

- `skills/scripts/models/implementer_report.py` (read-only) — confirmed the `Status` literal set that `_DONE_STATUSES` must mirror (`DONE`, `DONE_WITH_CONCERNS`, `BLOCKED`, `NEEDS_CONTEXT`) and that `files_changed_non_empty_for_done` exempts `task_type == "verification"`, which is why the test helper's `files_changed="[]"` case is a legitimate DONE.
- `skills/subagent-driven-development/scripts/_handoff_support.py` — Task 6's existing formula/precedence half, whose header import style and comment density this task matches.
- `tests/unit/test_handoff_support.py` — Task 6's tests, including the module-level `_write_report` / `_log` helpers and the `HOP_DIVISOR` / `CEILING_FACTOR` imports pinned by Task 6's deviation record.
- `tests/unit/conftest.py` — checked for fixture interference before trusting isolation; the only autouse fixture scrubs picker env vars session-wide and does not touch this file's surface.
- `docs/imp-plans/2026-07-30-cmux-spawn-v2/module-2-models-budget.md` (Task 6 + Task 7 + module header) and `deviations.md` (rows R3-1, R3-2).

## CLAUDE.md Files Read

- `CLAUDE.md` (repo root) — the only `CLAUDE.md` in the tree (`find . -name CLAUDE.md` returns exactly one; no subdirectory files exist on the path to either owned file). Binding conventions applied: pytest not unittest; hook scripts must use `$PYTHON` because system `python3` lacks PyYAML (which is why `_frontmatter`'s ImportError must propagate rather than be swallowed); `skills/subagent-driven-development/scripts/` is the flat-globbed Python-3.9-compat directory; `_midpoint.py` is the SSOT precedent this module follows; never `git add -A`, never `git stash`.

## Deviations from Plan

- **Deferred order R3-1 applied** (authorized by its row in `deviations.md`): `test_invalid_total_raises` now iterates `(0, -3, "7", None, True)`. Test-only; `expected_hops` itself is unchanged.
- **Import placement**: the plan's Step 3 shows `import glob, json, os, re, sys  # noqa: E401` inline. Hoisted one-per-line to the file header beside `import math`, per the dispatch instruction and the file's own style. The `# noqa: E401` was dropped because it no longer suppresses anything real.
- **Two statement splits**: the plan writes `print(...); return 0` on one line in two places (`stall-streak`, and the final `spawn-policy` print). Split onto separate lines. Behaviour is identical.
- **The commit was made twice.** The first `git commit` ran through the pre-commit format hook, which black-reformatted both files (311 insertions / 33 deletions, churning Task 6's untouched lines) and **deleted the `HOP_DIVISOR` and `CEILING_FACTOR` imports the dispatch required be preserved**. I `git reset`-ed that commit, restored both files from the pre-task HEAD, re-applied the four edits, and re-committed with `--no-verify`. The landed commit is **177 insertions / 1 deletion**, and both imports plus the R3-1 tuple are verified present at HEAD (`git show HEAD:tests/unit/test_handoff_support.py | grep HOP_DIVISOR`).
- **R3-2 was already folded into the plan text and the plan's version is the correct one — the register row is not.** `deviations.md` R3-2 prescribes `if not isinstance(manifest, dict): manifest = {}`. The plan's Step 3 uses `manifest = None`. These are **not** equivalent at the consent gate: with `{}`, `spawn-policy` on valid-but-non-object JSON (`5`, `null`, `[1,2]`) reaches `manifest is not None` → prints **`auto`**; with `None` it prints **`ask`**. R3-2's literal token would fail-**open** the sole consent gate for automated spawning. I implemented the plan (`None`), as the dispatch requires. **Recommend the R3-2 register row be corrected** so a future reader does not "restore" the prescribed token.

## Self-Review Findings

- **Red step verified, and the plan mis-predicts it.** Step 2 says "CLI exits 2"; the CLI subprocesses actually exited **0 with empty stdout**, because the module had no `__main__` guard yet — so `test_tasks_done_cli` failed on the `stdout.strip() == "1"` half of its conjunction rather than on `returncode`. Still a valid red (7 failed / 19 passed, all seven new tests failing); noting it so a reviewer does not read the discrepancy as a skipped step.
- **Stale-bytecode hazard controlled**: every measurement in this task was taken after `find . -name __pycache__ -type d -print0 | xargs -0 rm -rf` and with `-p no:cacheprovider`. The sweep covers `skills/subagent-driven-development/scripts/__pycache__`, which is where a stale `_handoff_support` `.pyc` would live given the test file's `sys.path.insert`.
- **`stall_streak`'s "indeterminate" is position-sensitive by design**: a malformed record only yields the string when it is the *newest* outcome (`streak == 0`); deeper in the log it truncates the streak at whatever was already counted. That matches the docstring and the plan's test, but only the newest-record case is pinned.
- **Candidate deferred row — cross-task CLI contract gap (Module 3 surface, not a Task 7 defect):** `tasks-done` can legitimately print `unknown` (PyYAML missing), but `stall-streak --tasks-done` is declared `type=int`, so a shell caller piping one into the other would hit an argparse **exit 2**. The plan pins the CLI as written, so I did not change the argparse type. `spawn-handoff-session.sh` must treat `unknown` as a skip signal before calling `stall-streak`. Recording it here so it survives the module-boundary archive.
- **Candidate deferred row — untested consent branch:** the plan's CLI tests pin missing-file → `ask` but do **not** pin valid-non-object JSON (`5` / `null` / `[1,2]`) → `ask`, which is precisely the branch R3-2 got wrong. I did not add the assertion, because departing from the plan's test bodies on the branch a partner review already blocked once is not mine to decide unilaterally. Recommend a one-line addition in review.

## Concerns

- **MEASURED GAP — `tasks-done` degradation is not observable on an empty reports dir.** `count_tasks_done` only executes the lazy `import yaml` inside the glob loop, so when `reports/` is empty or missing the loop body never runs, the ImportError never fires, and the CLI prints `0`. A venv-less caller is therefore indistinguishable from a genuinely-zero-progress session — precisely the "fake 0 manufactures stalls" outcome the plan's inline comment forbids. **Reproduction (run from the worktree):** write a `yaml.py` containing `raise ImportError` into a temp dir, then `PYTHONPATH=<tmp> .venv/bin/python3 skills/subagent-driven-development/scripts/_handoff_support.py tasks-done --reports-dir <empty-dir>` → `0`; add one report to that dir and re-run → `unknown`. **I did not fix it**: the shipped body is the plan's Step 3 verbatim, and the dispatch is explicit that a constraint conflict is surfaced, not worked around. The minimal fix a reviewer could authorise is one line — probe the yaml import once at the top of `count_tasks_done`, before the glob — but it is a production change to a plan-pinned body and belongs to whoever owns that decision. Consumer note for Module 3: `spawn-handoff-session.sh` cannot treat `0` as trustworthy progress unless it independently knows PyYAML is present.
- The **`--no-verify` commit** means the pre-commit formatter did not run on either file. This was deliberate and dispatch-authorized (the hook deletes the pinned imports), but it leaves both files in the repo's hand-written style rather than black's. Naming the mechanism so the follow-up is actionable: **a `# noqa` marker will not help** — the imports were removed by the *formatter*, not by a linter, so the only durable protections are a formatter exclusion for these paths or an assertion test that fails when the names are absent from the module namespace. I implemented neither: both are repo-wide tooling changes outside this task's write scope.
- **Reported numbers, all measured on the landed commit:** `tests/unit/test_handoff_support.py` → **26 passed** (19 pre-task + 7 new). `tests/unit/ -q` → **704 passed**, 0 failed (the dispatch quoted 697 as the baseline; 697 + 7 = 704, so this is the expected figure, not a regression). `python3 tests/ARaymond-skill-regression/validate-all-skills.py` → **PASS 160 / FAIL 0 / WARNING 2**, exactly as specified.
- The **e2e suite was not run** — Task 7's Step 4 does not call for it (Task 6's Step 7 did, since Task 6 changed `materialize-manifest.py`). Task 7 touches no consumer of the manifest, only an import-and-CLI module with no existing callers of the new functions.
- This **report file is untracked and unstaged** — the plan's Step 5 stages only the two implementation paths, which is correct. `docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/context-observations.log` is also dirty in the tree; it is hook-written and outside my write scope, so I left it alone.
