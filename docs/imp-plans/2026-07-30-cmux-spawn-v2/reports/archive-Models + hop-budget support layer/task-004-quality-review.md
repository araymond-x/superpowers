# Code Quality Review — Task 4 (plan.py: handoff_spawn field) — ROUND 1

Dispatched: 2026-08-01, model sonnet, `general-purpose` agent, read-only, adversarial.
Subject: commit `ab1ffd2` (parent `cf867be`). Upstream state at dispatch: implementer DONE,
spec review PASS (with its own three mutations), 166-test model suite green.

**Strengths**

- The one-line field addition is placed exactly where the plan specified (`plan.py:62`, directly under `entry_mode`), uses the exact `Literal["auto","ask","off"] = "auto"` signature, and matches the in-class inline-Literal style of its siblings `review_tier`/`task_type`/`entry_mode` — no stray type alias, no premature cross-module import (verified by direct read of `skills/scripts/models/plan.py:58-68`).
- Write scope is exactly the two files the plan assigned (`git show ab1ffd2 --stat`: `plan.py` +1, `test_plan_model.py` +22, `2 files changed, 23 insertions(+)`), independently re-confirmed here.
- `TestHandoffSpawn` (`test_plan_model.py:321-340`) is a faithful, idiomatically-consistent copy of `TestEntryMode`'s `MINIMAL_PLAN`-dict-spread construction (verified there is genuinely no `_minimal_plan()` helper in the file — `/usr/bin/grep -rn "_minimal_plan" tests/ skills/` found none), and its rejection test uses the stronger `errors()[0]["type"] == "literal_error"` assertion matching every sibling class, not a bare `pytest.raises`.
- Full model suite reproduced green independently: `.venv/bin/python3 -m pytest tests/unit/test_models/ -q` → `166 passed, 1 warning` (the warning is the pre-existing unrelated `TestSummary.__init__` collection warning in `implementer_report.py`, not new).
- `handoff_spawn` has zero consumers anywhere else in the tree yet (`find . -name "*.py" -not -path "*/.venv/*" | xargs /usr/bin/grep -l "handoff_spawn"` → only `plan.py` and its own test file), so the "optional-with-default keeps `extra="forbid"` safe" claim is trivially true for this task — there is nothing yet to break.
- The deliberate non-sharing of the Literal with Task 5's future `SpawnPolicy` alias is a real, previously-established in-repo convention (`implementer_report.py`'s independent `TaskType` Literal, with no import from `plan.py`), not an ad hoc implementer decision — confirmed by reading `partner-review-004.md`'s Architectural Alignment section, which interrogated this exact question before the dispatch was sent. I also traced the forward risk this creates: Task 6's plan-specified code passes the plan's `handoff_spawn` value straight into `Handoff(spawn_policy=...)`, whose own `SpawnPolicy` Literal will reject a value the two Literals disagree on — so a future drift between the two declarations fails loudly at manifest-materialization time rather than silently, which is an acceptable bound on the risk (not eliminated, but not a silent-corruption path either).

**Issues**

*Critical*: none.

*Important*: none.

*Minor*

- `tests/unit/test_models/test_plan_model.py:321` (class `TestHandoffSpawn`) — no test pins the Literal as a *closed* set of exactly `{"auto","ask","off"}`; it only tests that the three specified values are accepted and one specific invalid value (`"prompt"`) is rejected. I verified this is an actual, exploitable gap, not a theoretical one: in a scratch copy of `plan.py` + the test file (outside the repo, imported via `PYTHONPATH`), changing the field to `Literal["auto", "ask", "off", "manual"] = "auto"` (an unauthorized 4th value) left all 51 collected tests passing — 0 failures. I sanity-checked the harness wasn't vacuous by running two positive controls first (baseline unmodified run collected and passed all 51; then deleting the field, and separately renaming it to `handoff_spawns`, both correctly failed 3 of `TestHandoffSpawn`'s 4 tests). This mirrors a pattern already called out for this sprint: both the implementer's self-review and the spec review's three mutations (`Literal→str`, default `auto→off`, dropping `"off"`) were exclusively subtractive/restrictive — none tested the over-permissive direction. Suggested fix (does not require touching production code): add one assertion such as `assert typing.get_args(Plan.model_fields["handoff_spawn"].annotation) == ("auto", "ask", "off")` to `TestHandoffSpawn`, guarding against silent widening as Modules 2-4 come to depend on this being a strict 3-way switch.
- `tests/unit/test_models/test_plan_model.py:338` — `test_schema_version_not_bumped` is now the third verbatim copy of the same static assertion (`TestReviewTier:262`, `TestTaskType:316`). This is prescribed verbatim by the plan's own Step 1 template (not an implementer invention), so it's not this task's defect to fix, but the pattern is pure repetition-by-convention at this point and adds no new discriminating power per copy — worth a note for whoever eventually consolidates plan-model tests, not a blocker here.

Both items above are test-suite observations only; the production line (`plan.py:62`) itself has no defect I could find or induce.

**Assessment:** APPROVED

Verification performed directly (not taken from the implementer or spec-review reports): read `plan.py` in full and diffed it against `ab1ffd2`/`cf867be`; read all of `test_plan_model.py`'s sibling classes (`TestEntryMode`, `TestReviewTier`, `TestTaskType`) for idiom comparison; ran the real model test suite (166 passed) and the isolated `HandoffSpawn` selection (4 passed) from this worktree's own `.venv`; swept the whole tree with `/usr/bin/grep`/`find -print0 | xargs -0` (not the ugrep-wrapped `grep`) for any other `handoff_spawn`/`model_dump`/`model_fields` consumer and found none besides the two Task-4 files; independently reran `git show ab1ffd2 --stat` and `validate-report.py` against the implementer report; and built and executed my own mutation battery (4 mutations + 1 positive-control baseline + 2 positive-control breakages) in a scratch copy outside the repo, confirming one genuine, previously-unflagged coverage gap (Literal-widening is untested) while confirming the field's default-optionality, name, and Literal-restriction are all soundly pinned by the existing tests. No files in the repo were modified.

---

## Controller disposition — APPROVED was NOT taken as the stopping signal

The reviewer graded the widening gap **Minor** and returned APPROVED. The controller **actioned
it anyway** and dispatched a `[task 4 fix]` round. Reasoning, recorded so it is not re-litigated:

The stopping rule carried into this session is "stop when a round's findings are **cosmetic AND**
the reviewer says approve." This round satisfies the second conjunct and not the first. A
demonstrated, positive-controlled coverage gap is not cosmetic — and the controller
**independently reproduced it before dispatching**, per the standing rule that reviewer premises
are claims to verify:

```
BASELINE (unmutated):           51 passed
CONTROL field-deleted:          3 failed, 48 passed     <- harness discriminates
MUTATION widened to 4 values:   51 passed               <- the gap
```

Substantively it matters because the sprint's consent dial is meant to be a strict three-way
switch that Modules 2–4 all read, and Task 5 lands a **second, deliberately independent**
`SpawnPolicy` Literal over the same three values. Two independent declarations is exactly the
shape in which silent widening on one side goes unnoticed.

The second Minor (the third copy of `test_schema_version_not_bumped`) was **deliberately not
fixed** — the reviewer correctly identified it as prescribed by the plan's own Step 1 template
rather than an implementer choice, and churning it would edit the plan's intent under a
quality-review banner.

Round 2 (`task-004-quality-review-round-2.md`) re-reviews the fix.
