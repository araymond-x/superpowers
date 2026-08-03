---
schema_version: 1
task_id: 4
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "tests/unit/test_models/test_plan_model.py"
    description: "Added TestHandoffSpawn.test_literal_is_closed_set, pinning get_args(Plan.model_fields[\"handoff_spawn\"].annotation) == (\"auto\", \"ask\", \"off\") as an exact-tuple equality, plus the top-of-file `from typing import get_args` import the assertion needs. Closes the coverage gap the adversarial quality review found: the prior 4 tests accepted the 3 authorized values and rejected one named invalid value, but never pinned the Literal as a closed set, so widening it to a 4th value left all tests green. The working-tree edit was 8 insertions / 0 deletions; the committed diff is 94 insertions / 28 deletions -- see Deviations for why, and the verification below proving the extra 86 lines are 100% mechanical."
tests:
  written: 1
  passing: 1
  command: ".venv/bin/python3 -m pytest tests/unit/test_models/ -q"
  result: PASS
contract_compliance:
  - constraint: "Write scope is exactly tests/unit/test_models/test_plan_model.py. Do NOT touch plan.py or any other file."
    status: compliant
    detail: "git show --stat HEAD confirms exactly one file changed. skills/scripts/models/plan.py was never staged and the formatting hook (see Deviations) never reached it -- `git status --porcelain` on it is empty throughout this session."
  - constraint: "Match the file's idiom (TestEntryMode/TestReviewTier/TestTaskType/TestHandoffSpawn); reuse existing imports where possible; add typing import at the top the way the file adds imports, not inside a method."
    status: compliant
    detail: "Added `from typing import get_args` as a top-level import alongside the existing `import pytest` / `from pydantic import ValidationError` block (not inside the test method). Used a named import rather than `import typing; typing.get_args(...)`, matching the file's existing style of importing specific names. The new test method lives inside the existing TestHandoffSpawn class, placed directly after test_rejects_invalid_value and before test_schema_version_not_bumped, matching the ordering convention every sibling class already uses (defaults -> accepted values -> rejected value -> [this] -> schema-version pin). This is my authored content; unaffected by the formatting-hook issue below."
  - constraint: "Do not restructure or reformat anything else; this should be a handful of added lines."
    status: partial
    detail: "My own working-tree edit was exactly 8 insertions, 0 deletions (verified via `git diff` immediately after editing, before staging). The COMMITTED diff is 94 insertions / 28 deletions because a global standing hook (`~/.claude/hooks/pre-commit-format.sh`, PreToolUse on any Bash command containing \"git commit\") ran `ruff format` + `ruff check --fix` on the staged file and re-staged it before the commit executed. I did not invoke ruff myself and did not intend the extra changes. See Deviations for full detail and a mechanical proof that none of the extra diff is hand-introduced."
  - constraint: "Do not \"fix\" the second Minor the reviewer raised (test_schema_version_not_bumped as a third verbatim copy)."
    status: compliant
    detail: "test_schema_version_not_bumped was not touched by me; the hook's `ruff format` re-wrapped nothing in that method (it was already short enough), so it is also byte-identical in the commit."
  - constraint: "Evaluate the reviewer's suggested assertion shape rather than pasting it verbatim."
    status: compliant
    detail: "Evaluated the suggested `typing.get_args(...)` form against the file's import idiom and switched to `from typing import get_args` while keeping the equality-against-tuple assertion body, since that shape is what actually discriminates widening/narrowing/reordering (proven empirically below). Note the committed method body's tuple is wrapped across three lines by ruff, not by me -- my authored version was a single line."
---

## Implementation Summary
Added one test method, `TestHandoffSpawn.test_literal_is_closed_set`, that asserts `get_args(Plan.model_fields["handoff_spawn"].annotation) == ("auto", "ask", "off")`. This pins the `Literal` as an exact, ordered 3-tuple rather than merely checking that the three known values are accepted and one named invalid value is rejected -- the shape of coverage the prior four tests already had, and the shape that a widened Literal slips past undetected. Added the single import (`from typing import get_args`) the assertion needs, placed at the top of the file next to the other top-level imports.

After committing, an unrelated global tool (a repo-wide auto-formatter hook, detailed in Deviations) expanded the committed diff well beyond my intended edit. I verified after the fact, and am reporting here, exactly what that tool changed and why none of it is a functional or scope concern -- see Deviations and Self-Review Findings.

## Source Files Read
- `tests/unit/test_models/test_plan_model.py` (full file) -- read `TestEntryMode`, `TestReviewTier`, `TestTaskType`, and the existing `TestHandoffSpawn` to confirm the class's four-tests-in-a-fixed-order idiom (defaults / accepted values / rejected value / schema-version pin) and the top-of-file import block, before deciding where the new test and import belong.
- `skills/scripts/models/plan.py` (read-only, to confirm the current `handoff_spawn` field declaration and that no change to it was warranted) -- not modified.
- `~/.claude/hooks/pre-commit-format.sh` (read-only, after discovering the discrepancy) -- to understand exactly what the formatting hook does and confirm it always re-stages and always exits 0 (never blocks).

## CLAUDE.md Files Read
- Repository root `CLAUDE.md` -- reconfirmed the worktree rules (`.venv` is a symlink, never `git stash`, never `git add -A`, stage explicit paths only) that this dispatch's standing rules restated, and the Pydantic-model section describing `handoff_spawn` as a Task-4 addition with no schema bump.
- No `CLAUDE.md` present in `tests/unit/test_models/` or `skills/scripts/models/` (checked; none found, consistent with the original Task 4 report's finding).

## Deviations from Plan
**The committed diff is larger than the dispatched "handful of added lines" constraint, due to a global tool outside my control, not a scope decision I made.**

Sequence of events: I edited the file with exactly two changes (one import line, one test method — 8 insertions, 0 deletions, confirmed via `git diff` before staging). I ran `git add tests/unit/test_models/test_plan_model.py` then `git commit -m ...`. The `git commit` Bash command matched a registered global `PreToolUse` hook, `~/.claude/hooks/pre-commit-format.sh`, which runs on every Bash command containing the text "git commit": it collects staged `.py` files, runs `ruff format` then `ruff check --fix` on them, re-stages the result with `git add`, and always exits 0 (it never blocks the commit; the hook has no bypass flag and does not check any escape-hatch env var). This is standing global tooling, not something specific to this worktree or task, and I did not invoke `ruff` myself at any point.

The result: `ruff format` reformatted long single-line dict literals and one `pytest.mark.parametrize` line elsewhere in the file into multi-line form, and re-wrapped my new assertion's tuple across three lines. `ruff check --fix` removed five imports (`Module`, `SharedConstant`, `PatternReference`, `FeatureArchetype` from `plan`; `Tier` from `sdd_session`) as unused (F401). I verified these five were **already** unused before my change -- `git show ab1ffd2:tests/unit/test_models/test_plan_model.py` plus a grep confirms none of them appear anywhere in the file body, only in the import line itself. This was a pre-existing lint condition in the file, not something introduced by this task.

I verified the entire extra diff is mechanically attributable to the hook and nothing else, by replaying it independently: I took the parent commit's version of the file (`git show ab1ffd2:...`), ran `ruff format` then `ruff check --fix` on it directly (same order the hook uses, same `ruff` binary the hook resolves to: `~/Library/Python/3.9/bin/ruff`, since it's absent from PATH but present at that fallback location the hook checks), and diffed the result against the actual committed `HEAD` version. The only difference between "parent + ruff" and the actual commit is exactly my intended addition: the `from typing import get_args` import line and the `test_literal_is_closed_set` method body (itself reformatted by ruff into ruff's multi-line tuple style, since it's new code ruff also touches). No other hand-edit exists anywhere in the diff.

I did not attempt to bypass, disable, or evade this hook (e.g. via git plumbing commands that avoid the literal substring "git commit", or by patching the hook or settings.json). It is a global, standing tool I am not authorized to alter without explicit instruction, this was not a blocking/failing gate to route around, and the resulting file is still correct, tested, and semantically minimal at the level that matters (one new assertion). I am reporting the discrepancy rather than silently treating `compliant` as true, per this dispatch's explicit instruction to report contradictions rather than edit around them.

I considered `git reset --soft` and recommitting to try for a cleaner diff, but confirmed this would not help: the hook re-fires identically on every future `git commit` Bash invocation against this file for as long as it remains non-ruff-clean, so no sequence of resets/recommits through the Bash tool changes the outcome. The file is now ruff-clean going forward, so this specific file will not re-expand on a future commit.

## Self-Review Findings
Ran the mutation-testing protocol the dispatch required, in a scratch copy outside the repo (`models/` + the modified test file copied to a temp dir under the session scratchpad, not `/tmp` directly), all runs via `PYTHONPATH=<scratch>/models pytest`. These mutation runs were performed on my pre-format working copy (before the hook fired), so I separately re-ran the real suite against the actual committed (post-format) state afterward — see item 5.

1. **New assertion fails against the controller's widening mutation.** Reproduced `Literal["auto", "ask", "off", "manual"]` in the scratch copy. Result: `1 failed, 51 passed` -- only `test_literal_is_closed_set` failed (`AssertionError: ... Left contains one more item: 'manual'`). Direct evidence the new test closes the exact gap described in the dispatch: the other 51 tests (including the pre-existing `TestHandoffSpawn` tests) stayed green under the same mutation that fooled the whole suite before this fix.
2. **Positive control in the other direction (field deleted).** Baseline scratch run (unmutated): `52 passed`. Field-deleted mutation: `4 failed, 48 passed` (the 3 the controller predicted plus the new test, now that it exists) -- confirms the harness still discriminates a real breakage and that my new test is one of the four sentinels tripped by outright removal, not a vacuous assertion.
3. **Narrowing and reordering mutations, both exercised (the dispatch only required this "if your assertion is an equality check" -- it is, so both were run):**
   - Narrowing (`Literal["auto", "ask"]`, dropping `"off"`): `2 failed, 50 passed` -- both `test_accepts_ask_and_off` (pre-existing) and the new `test_literal_is_closed_set` failed.
   - Reordering (`Literal["off", "auto", "ask"]`, same 3 values, different order): `1 failed, 51 passed` -- **only** `test_literal_is_closed_set` failed. This is the discriminating case: no pre-existing test in the file would have caught a silent reorder, because a `set`-based equality check would be order-insensitive. The tuple-equality form the reviewer suggested is what catches it.
4. **Real suite green, run twice.** First run (pre-format, working tree): `167 passed, 1 warning in 0.17s`. Second run (post-format, against the actual committed HEAD, after discovering the reformatting): `.venv/bin/python3 -m pytest tests/unit/test_models/ -q` -> `167 passed, 1 warning in 0.18s`, identical count. This second run is the one that matters as evidence -- it directly confirms none of the five ruff-removed imports were load-bearing (a genuinely-used import removed by `--fix` would surface as a collection-time `NameError`, and none did) and that the real suite passes against exactly what's in git, not a version that no longer exists.
5. **Full unit suite green.** `.venv/bin/python3 -m pytest tests/unit/ -q` (run before the reformat was discovered, so re-verified narrowly above rather than re-run in full): `663 passed, 1 warning in 154.82s`.
6. **Mechanical-diff proof for the reformatting.** Detailed in Deviations: replaying `ruff format` + `ruff check --fix` on the parent commit's file reproduces the committed `HEAD` file exactly, modulo my intended addition. This rules out any hand-edit hiding inside the large diff.

After each mutation the scratch copy of `plan.py` was restored from a saved original and diffed byte-identical before the next mutation ran, so mutations did not compound. Both scratch directories used for this task (mutation testing, and the ruff-replay proof) were deleted after use. `skills/scripts/models/plan.py` in the actual worktree was never touched by any of this.

No contradiction found between my measurements and the dispatch's stated premises: the controller's widening-mutation numbers (51 passed before the fix) and field-deleted control (3 failed before the fix, 4 failed after adding this test) both reproduced exactly as described.

## Concerns
- **The commit's diff (94 insertions / 28 deletions) is larger than the dispatch's "handful of added lines" expectation**, entirely due to the global `~/.claude/hooks/pre-commit-format.sh` formatting hook described in Deviations, not a scope decision. A reviewer scanning the raw diff size without reading this report could mistake it for scope creep. I recommend the quality reviewer read this Concerns/Deviations section before judging the diff, and treat the mechanical-replay proof above as the load-bearing evidence that nothing beyond my one test method was hand-authored.
- **This will recur for any other non-ruff-clean `.py` file this sprint stages.** Task 5 is stated to touch `sdd_session.py`'s test file; if that file is not already ruff-clean, the same one-time whole-file reformatting will happen on its first commit through this hook. Flagging for the controller's awareness -- not something I fixed or scoped into this task.
