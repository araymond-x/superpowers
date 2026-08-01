# Spec Compliance Review — Task 4 (plan.py: handoff_spawn field)

Dispatched: 2026-08-01, model sonnet, `general-purpose` agent, read-only.
Subject: commit `ab1ffd2` (parent `cf867be`).

## PASS

Task 4 (`docs/imp-plans/2026-07-30-cmux-spawn-v2/module-2-models-budget.md` "### Task 4") is spec-compliant and contract-compliant. Every headline claim in `docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/task-004-implementer-report.md` was independently reproduced from code and command output, not taken on trust.

### What I verified, and how

**Field placement, type, default, position** — Read `skills/scripts/models/plan.py:56-64`: `handoff_spawn: Literal["auto", "ask", "off"] = "auto"` sits at line 62, directly under `entry_mode` (line 61), inside `class Plan`. Same in-class inline `Literal[...] = default` declaration style as `review_tier`/`task_type` (`Task` class, lines 39-47) and `entry_mode` (line 61) — no separate type alias, no cross-module import. Matches plan Step 3 verbatim.

**The authorized departure, verified not assumed** — `/usr/bin/grep -rn "_minimal_plan" tests/ skills/` (real grep, not the ugrep wrapper) returns zero matches for the helper function; it genuinely does not exist. The file's real idiom is the module-level `MINIMAL_PLAN` dict (`tests/unit/test_models/test_plan_model.py:12-16`) spread into `Plan.model_validate({**MINIMAL_PLAN, ...})`, which is exactly what `TestEntryMode` and `TestTaskType` (same file) already do, and exactly what the implementer used. `CURRENT_SCHEMA_VERSION` is imported once at file top (`test_plan_model.py:9`) and reused, not re-imported inside `test_schema_version_not_bumped` — matches the sibling `TestTaskType.test_schema_version_unchanged`. Both authorized-departure claims confirmed.

**All four test intentions preserved** — read `test_plan_model.py:317-339` (`TestHandoffSpawn`): default `auto`; both `ask`/`off` accepted; invalid value raises `ValidationError` (checked more strongly than the plan's sketch — asserts `errors()[0]["type"] == "literal_error"`, matching sibling classes' style); `CURRENT_SCHEMA_VERSION == 1`. All four match plan Step 1's intent.

**"3 of 4 failed" claim, reproduced empirically, not reasoned about** — copied `skills/scripts/models/` and the test file to a scratch dir outside the repo, removed the `handoff_spawn` line to simulate pre-Task-4 state, and ran `PYTHONPATH=<scratch>/models .venv/bin/python3 -m pytest <scratch>/tests/test_plan_model.py -k HandoffSpawn -v`. Result: **3 failed, 1 passed** — `test_defaults_to_auto` → `AttributeError`; `test_accepts_ask_and_off` → uncaught `ValidationError` (`extra_forbidden`); `test_rejects_invalid_value` → `AssertionError` (`'extra_forbidden' == 'literal_error'` fails, since the pre-implementation extra-field error escapes as the wrong error type, not the expected one); `test_schema_version_not_bumped` → passes trivially (invariant unrelated to the field, same pattern as the sibling `TestTaskType` class). This exactly matches the report's claim and is legitimate, not a sign of a non-discriminating test.

**Does each test actually discriminate? Ran three mutations, did not just reason about it:**

- Widened `Literal["auto","ask","off"]` → bare `str`: `test_rejects_invalid_value` FAILED (`DID NOT RAISE ValidationError`) — the Literal constraint, not mere field presence, is what's pinned.
- Changed default `"auto"` → `"off"`: `test_defaults_to_auto` FAILED (`assert 'off' == 'auto'`).
- Dropped `"off"` from the Literal (`Literal["auto","ask"]`): `test_accepts_ask_and_off` FAILED (`literal_error` on `'off'`).

All three mutations were caught by exactly the test designed to catch them.

**Full suite** — `.venv/bin/python3 -m pytest tests/unit/test_models/ -q` → `166 passed, 1 warning` (the warning is a pre-existing, unrelated `PytestCollectionWarning` about `TestSummary` in `implementer_report.py`). Matches the report exactly.

**Write scope** — `git show ab1ffd2 --stat`: exactly `skills/scripts/models/plan.py` (+1) and `tests/unit/test_models/test_plan_model.py` (+22), `2 files changed, 23 insertions(+), 0 deletions`. Matches the report exactly. `git status --short` post-commit shows only pre-existing untracked/modified SDD process artifacts (`.dispatch-log`, `context-observations.log`, `checkpoint-pre-dispatch-004.json`, `partner-review-004.md`) — none of which are code and none staged in `ab1ffd2`.

**"No frontmatter" contract, re-swept with the correct instrument** — `type grep` confirms `grep` here is the shell-function ugrep wrapper. Ran `/usr/bin/find . -name '*.md' ... | xargs -0 /usr/bin/grep -nE '^handoff_spawn:'` and a JSON sweep with `/usr/bin/find`/`/usr/bin/grep` — zero matches for `handoff_spawn` as a literal frontmatter key anywhere in the repo. A broader `/usr/bin/grep -rn "handoff_spawn" .` (52 hits) shows all occurrences are in prose (spec/plan bodies, reports) or in the two Task-4 code files — none inside a YAML frontmatter block. Cross-checked `plan.md`'s actual frontmatter (`docs/imp-plans/2026-07-30-cmux-spawn-v2/plan.md:1-13`) — no `handoff_spawn:` key present.

**`CURRENT_SCHEMA_VERSION` unchanged** — `/usr/bin/grep -n "CURRENT_SCHEMA_VERSION" skills/scripts/models/_base.py:4` → `= 1`.

**Every pre-existing plan still validates** — ran `validate-plan.py --plan-file` over every `docs/imp-plans/*/plan.md` and `module-*.md` (28 files). One pre-existing BLOCKER surfaced in `2026-05-17-adaptive-enforcement-tiers/plan.md` ("Source Contracts is present but Task 0 is missing") — this is a `validate-plan.py` structural heuristic unrelated to the `Plan` Pydantic model; confirmed by directly running `Plan.model_validate()` against that file's parsed frontmatter, which succeeded (`handoff_spawn = auto`, default applied cleanly). So the new optional field introduces **zero** Pydantic-level regressions across the repo's existing plans; the one blocker is pre-existing and orthogonal to this change.

**CLAUDE.md check** — `/usr/bin/find skills/scripts/models tests/unit/test_models -iname "CLAUDE.md"` → none found, confirming the report's "None found" claim.

**Report completeness** — ran `validate-report.py --report-file .../task-004-implementer-report.md` → `status: COMPLETE`, all 5 required sections present (`Implementation Summary`, `Source Files Read`, `Deviations from Plan`, `Self-Review Findings`, `Concerns`), none missing. One non-blocking advisory: the validator emits `WARNING: status is DONE but report has non-empty Deviations`; the "deviations" recorded are the two authorized-mechanics departures (already verified above as legitimate and directed by the controller), not defects, so `DONE` (not `DONE_WITH_CONCERNS`) is a reasonable call — flagging for visibility, not as a finding.

### Findings

None. No `[BLOCKING]`, no `[ADVISORY]`, no `[UNVERIFIED]` items survive verification.

---

## Controller note

Two things make this review load-bearing rather than a rubber stamp, and both are worth
keeping as method for the rest of the sprint:

1. It **reconstructed the pre-implementation state in a scratch directory** rather than
   accepting the implementer's account of Step 2's failure — and its reconstruction found the
   *reason* the fourth test passed pre-implementation (`test_schema_version_not_bumped` pins an
   invariant unrelated to the field), which is the difference between a legitimately trivial
   test and one that pins nothing.
2. It **ran three mutations** against the shipped field. The `Literal → str` widening is the
   one that matters: without it, "the test rejects `prompt`" could have been satisfied by
   `extra_forbidden` rather than by the Literal, and the field's whole constraint would have
   been untested. It failed correctly.

The `DONE` vs `DONE_WITH_CONCERNS` advisory is logged to `deviations.md` by the controller
rather than bounced back — see the `| 4 | ProcessNote |` row.
