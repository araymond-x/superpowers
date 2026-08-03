---
schema_version: 1
task_id: 5
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/scripts/models/sdd_session.py"
    description: "Added SpawnPolicy = Literal['auto','ask','off'] and class Handoff(StrictModel) (expected_hops: int = Field(ge=1); spawn_policy: SpawnPolicy = 'auto') after RequirementLevel, plus handoff: Handoff | None = None on SddSession after dispatch_log_sentinel. Exactly the plan's Step 3 snippet; CURRENT_SCHEMA_VERSION untouched."
  - path: "tests/unit/test_models/test_sdd_session_model.py"
    description: "Added Handoff to the existing top-level selective 'from sdd_session import (...)' list, and added class TestHandoffBlock with the plan's eight verbatim tests (absent-validates, block-validates, policy-defaults, hops-positive, JSON round-trip, partial-rejected, literal-closed-set, extra-key-rejected)."
tests:
  written: 8
  passing: 8
  command: ".venv/bin/python3 -m pytest tests/unit/test_models/test_sdd_session_model.py -v -k TestHandoffBlock"
  result: PASS
contract_compliance:
  - constraint: "Plan and SddSession are extra=\"forbid\" — new fields must be optional with defaults so every existing plan/manifest still validates; CURRENT_SCHEMA_VERSION stays 1."
    status: compliant
    detail: "handoff: Handoff | None = None is optional with a default, so pre-v2 manifests still validate — asserted directly by test_absent_handoff_still_validates. CURRENT_SCHEMA_VERSION remains 1 (unchanged in _base.py). Full unit suite 671 passed, independently re-run by the controller at HEAD f91b94f."
  - constraint: "Deferred order B4: the handoff block is ALL-OR-NOTHING — expected_hops stays required (int = Field(ge=1)); absent entirely is legal, present-but-partial is not."
    status: compliant
    detail: "expected_hops declared required with ge=1. test_partial_block_rejected pins both partial shapes ({} and {\"spawn_policy\": \"ask\"}) as ValidationError; test_absent_handoff_still_validates pins absent-entirely as legal. The pinned reading was implemented as written, not re-litigated."
  - constraint: "Python 3.9 scan asymmetry (deferred order B7): skills/scripts/models/ is NOT scanned by check_python39_compat, so Handoff | None is correct there. Do not harmonize the two directories."
    status: compliant
    detail: "Used PEP-604 Handoff | None, matching the house idiom in this directory (plan.py 6 uses, checkpoint_result.py 5, sdd_session.py itself 3). Not rewritten to Optional[Handoff]. validate-all-skills.py re-run: PASS 159 / FAIL 0 / WARNING 2 (the known soft word-count advisories)."
  - constraint: "Write scope for Task 5 is exactly two files: skills/scripts/models/sdd_session.py and tests/unit/test_models/test_sdd_session_model.py. materialize-manifest.py belongs to Task 6."
    status: compliant
    detail: "Commit f91b94f changed exactly those two files (2 files changed, 54 insertions(+), 1 deletion(-)). materialize-manifest.py untouched despite the known \"handoff\": null serialization side effect, which was reported rather than fixed."
---

## Implementation Summary
Added the manifest-side twin of Task 4's `Plan.handoff_spawn`: an optional `handoff` block on `SddSession`, backed by a new `Handoff(StrictModel)` nested model carrying a required `expected_hops` (`ge=1`) and a defaulted `spawn_policy`. Followed the `IntegrationTest` / `Plan.integration_test` nested-optional-model precedent from `plan.py` (the plan's named `model-field-addition` pattern reference) and Task 4's own diff at `ab1ffd2`/`fe2437e`. No schema-version bump. This unblocks Task 6, which will make `materialize-manifest.py` populate the block.

## Source Files Read
None required — Module 2 declares `Source Contracts: None` (external contracts were frozen into fixtures by Module 1's Task 0 and restated in the module's Contract Constraints). Read as pattern references, not contracts: `skills/scripts/models/plan.py`, `skills/scripts/models/_base.py`, the existing `TestSddSessionGoldenInput` class, and Task 4's diffs `ab1ffd2` / `fe2437e`.

## CLAUDE.md Files Read
- Repository root `CLAUDE.md` — confirmed the Pydantic model inventory and the `CURRENT_SCHEMA_VERSION` pinned-at-1 policy, the additive-optional-field precedent (`review_tier`, `task_type`, `integration_test` all landed without a bump), and the worktree rules restated in the dispatch (never delete/recreate `.venv`, never `git stash`, never `git add -A`).
- No `CLAUDE.md` present in `skills/scripts/models/` or `tests/unit/test_models/`.

## Deviations from Plan
- **None in the implementation** — Steps 1 and 3 were applied verbatim from the plan text.
- **The pre-commit format hook did NOT fire, contrary to the dispatch's prediction.** The dispatch predicted a one-time whole-file `ruff format` reformat plus removal of two unused imports (`ArtifactPaths`, `ModuleState`). Neither happened: the commit is exactly the edit (+54/-1) and both imports remain imported-and-unused. The implementer did not run `ruff` manually to force the predicted state; `git status --porcelain` on both files is empty, so the committed bytes are byte-identical to what the 175/671 runs exercised. Routed to the controller as a separate change if wanted. (Controller note: this is a partner-verified premise that did not hold at execution time — the eighth such premise reversal in this sprint.)
- **Three plan-verbatim choices that resemble weaknesses but are deliberate**, flagged so a quality review does not re-file them as findings: (1) `test_expected_hops_must_be_positive` and `test_partial_block_rejected` use bare `pytest.raises(ValidationError)` without the surrounding file's `errors()[0]["type"]` assertion; (2) `import json` and `from typing import get_args` sit inside test methods, against `test_plan_model.py`'s top-level style; (3) the `Handoff` docstring forward-references `_handoff_support.derive_expected_hops`, which Task 6 has not yet created. All three are exactly as the plan specifies.
- **Known side effect deliberately left for Task 6:** newly materialized manifests will now serialize `"handoff": null`, because `materialize-manifest.py` dumps via `model_dump_json()` with no `exclude_none`. No unit test broke. `materialize-manifest.py` is outside this task's write scope and was not touched; the e2e suite was not run for the same reason.
- Plan checkboxes not ticked — the plan file is outside the implementer's write scope (controller-owned).

## Concerns
_The implementer returned status `DONE`. The controller upgraded it to `DONE_WITH_CONCERNS` when persisting the report — the implementation itself is clean and matches the plan verbatim, but the report routes three items to the controller, and routed items that are not logged are routed items that are lost. Nothing here questions the correctness of the committed code._

1. **A partner-verified premise did not hold: the pre-commit format hook never fired.** The partner review measured the hook as registered (`~/.claude/settings.json`, PreToolUse/Bash), resolved the exact `ruff` binary, and predicted a whole-file reformat plus removal of `ArtifactPaths` and `ModuleState`. At execution the commit was exactly the edit (+54/-1) and both unused imports survive. The committed bytes are byte-identical to what the 175/671 runs exercised, so nothing is unverified — but the divergence is worth recording, because the same prediction was carried into both reviewer dispatches. Disposition: no action on Task 5; the unused-import cleanup, if wanted, is a separate change.
2. **`materialize-manifest.py` now emits `"handoff": null` in every newly materialized manifest**, because it serializes via `model_dump_json()` with no `exclude_none`. This is a direct consequence of Task 5's optional field appearing on a file Task 5 does not own. No unit test broke (full suite 671 passed). Correctly left untouched; Task 6 fills the block in.
3. **Three plan-verbatim stylistic choices deviate from the surrounding file's conventions** — bare `pytest.raises(ValidationError)` without the sibling classes' `errors()[0]["type"]` assertion; method-level `import json` / `from typing import get_args`; and a docstring forward-reference to `_handoff_support.derive_expected_hops`, which does not exist until Task 6. All three are exactly as the plan specifies, so a quality review flagging them is flagging the plan, not the implementation.

## Self-Review Findings
- **Step 2 red state was a collection-time `ImportError`, and it was kept that way.** With `Handoff` in the top-level import list (per the pinned facts) and the model not yet changed, pytest could not collect the file at all: `ImportError: cannot import name 'Handoff' from 'sdd_session'` → `Interrupted: 1 error during collection`. The dispatch explicitly warned that the tidy-looking remedy — deferring the import into a test method to manufacture eight per-test failures — would violate pinned facts #2 and #3 while still passing every test afterward. The import was left top-level.
- **Discriminating control run and it behaved exactly as predicted.** Swapping `Handoff`'s base from `StrictModel` to `BaseModel` produced `1 failed, 174 passed`, the single failure being `TestHandoffBlock::test_extra_key_rejected` (`DID NOT RAISE ValidationError`) with no other test changing. Reverted from a scratchpad backup; confirmed `class Handoff(StrictModel)` restored with no stray `BaseModel` import; re-ran to `175 passed`. This is the guard the controller added to the plan precisely because the other seven tests cannot distinguish the two base classes.
- **Arithmetic self-check passed:** 663 (suite at `fe2437e`) + 8 new tests = 671, and the full suite reports exactly `671 passed, 0 failed`. No test silently failed to collect.
- Backward-compat CLI invocation had no target: `docs/imp-plans/2026-07-22-cmux-integration/.sdd-session.json` confirmed absent, as pre-verified in the dispatch. No substitute manifest was constructed; `test_absent_handoff_still_validates` carries the assertion instead.
- `validate-all-skills.py` was run unprompted because a file under `skills/` changed: PASS 159 / FAIL 0 / WARNING 2 (the known soft word-count advisories). The docstring's forward reference to the not-yet-existing `_handoff_support.derive_expected_hops` tripped no cross-reference check.
