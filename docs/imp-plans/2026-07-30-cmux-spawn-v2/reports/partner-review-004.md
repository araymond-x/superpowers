# Partner Review — Task 4 dispatch (plan.py: handoff_spawn field)

Dispatched: 2026-08-01, model sonnet, `general-purpose` agent.
Reviews the proposed implementer prompt for Task 4 against the plan, the register, and the tree.

**Status:** APPROVED

**Context Completeness:** PASS — the prompt contains all five required sections: Contract Constraints, Shared Constants, Pattern References, Source Files, and a "Subdirectory CLAUDE.md Files" reminder. Verified by reading the full prompt file top to bottom (`/private/tmp/.../task-004-implementer-prompt.md`).

**Context Accuracy:** PASS

- Contract Constraints: byte-for-byte verbatim match, including the just-amended B7 sentence, against `docs/imp-plans/2026-07-30-cmux-spawn-v2/module-2-models-budget.md:33` and the parent bullet at `plan.md:185`. Diffed by eye against both files after reading them directly.
- B7 claim verified first-hand: `check_python39_compat` in `tests/ARaymond-skill-regression/validate-all-skills.py` (confirmed via `/usr/bin/grep -n "check_python39_compat" -A 20 ...`) builds `sdd_scripts_dir = os.path.join(skills_dir, "subagent-driven-development/scripts")` and does a flat `os.listdir` over only that directory — it never touches `skills/scripts/models/`. The Contract Constraints claim is true.
- Shared Constants "None for this task": confirmed against `plan.md` frontmatter — Task 4's entry (lines 85-89) carries no `shared_constants_used` key, unlike Tasks 6/8/11/12.
- Pattern References: `model-field-addition` correctly reproduced with `source_files: ["skills/scripts/models/plan.py"]` and the exact reason string from the parent frontmatter (`plan.md:36-38`).
- Task description: verbatim match, not truncated, against `module-2-models-budget.md:79-124` (compared line-by-line).
- **The `_minimal_plan()` correction — verified TRUE, not a false premise.** Read `tests/unit/test_models/test_plan_model.py` in full (319 lines): no `_minimal_plan` function exists anywhere. The real idiom is the module-level `MINIMAL_PLAN` dict (line 12) spread via `{**MINIMAL_PLAN, ...}` into `Plan.model_validate(...)`, exactly as `TestEntryMode` (lines 267-281) and `TestReviewTier` (lines 235-264) do. The correction's guidance matches this idiom exactly.
- Sub-claim also verified: `from _base import CURRENT_SCHEMA_VERSION` is already a top-level import at line 9 of that file, and two existing classes (`TestReviewTier.test_schema_version_unchanged` lines 262-264, `TestTaskType.test_schema_version_unchanged` lines 316-318) already assert `CURRENT_SCHEMA_VERSION == 1` — matching the prompt's "two existing classes already assert" claim exactly.

**Prior Task Awareness:** PASS — Read the archived Task 3 reports directly. The original implementer report (`.../archive-Contracts, cold-start measurement, spikes/task-003-implementer-report.md`) was `DONE_WITH_CONCERNS`; the final report after three fix rounds (`task-003-fix-round-3.md`) is `status: DONE`, `files_changed` limited to two `docs/process-improvement-findings/*.md` files plus `BACKLOG.md` — no code files, confirming the "touching no code that Task 4 reads" characterization. Concerns were exhaustively logged in `deviations.md` (extensive Task 3 rows). No pending deviation touches `plan.py` or `test_plan_model.py`.

**Escalation Check:** PASS — No task in Module 1 ended BLOCKED/NEEDS_CONTEXT; all DONE_WITH_CONCERNS items across Tasks 0-3 were run through fix/re-review cycles to APPROVED/DONE (verified via the Task 3 quality-review-round-4 approval and the commit-log "quality r4 APPROVED"). **B4 specifically checked**: `deviations.md`'s Deferred Work table (line 133) states its gate explicitly as `"Module 2, before Task 5 dispatches"`, and the companion ProcessNote row (`| 4 | ProcessNote |`) gives task-specific reasoning for not bundling it with B7 (B7 gates *this* dispatch; B4's substance "depends on nothing Task 4 produces" and instead governs Task 5's `Handoff.expected_hops` optionality). This is defensible — B4 concerns a field in `sdd_session.py` that doesn't exist until Task 5, so it structurally cannot bind Task 4.

**Architectural Alignment:** PASS

- **SpawnPolicy duplication interrogated and found non-violating.** I checked for an existing precedent of sharing vs. duplicating small Literal enums across these two model files. Found one: `implementer_report.py` independently defines its own `TaskType = Literal["implementation", "verification"]` (line 32) with **no import from `plan.py`**, even though `plan.py`'s `Task.task_type` (line 48) declares the identical literal inline. Verified via `/usr/bin/grep -n "^from\|^import" skills/scripts/models/implementer_report.py` — no cross-import exists. This is a real, already-shipped precedent in this exact codebase for declining to share a 3-ish-value Literal across `plan.py` and a sibling model file serving a different lifecycle stage (declared intent vs. materialized/recorded state). The parent plan's own Shared Constants list (which explicitly enumerates `HOP_DIVISOR`/`CEILING_FLOOR`/`CEILING_FACTOR`, `TIER_PROFILES`, etc.) deliberately omits this literal — a plan-author decision, not something the dispatch invented. Given the precedent and the sequencing constraint (Task 4 dispatches before Task 5's `SpawnPolicy` exists, so no import is even possible in the correct direction), this is a defensible, low-risk duplication (3 fixed string values, not algorithmic logic), not a "single source of truth" violation warranting a BLOCK.
- Consumer-update reasoning verified: grepped `validate-plan.py`, `materialize-manifest.py`, `validators.py` for hardcoded field enumerations — none exist that would break on an added optional field. The optional-with-default claim holds.
- Point fix vs. structural: correctly scoped — field lands alone, nothing else changes, consistent with the plan's explicit "Task 4 lands the field and nothing else" design.

**Pattern Completeness:** PASS — Confirmed no subdirectory `CLAUDE.md` files exist under `skills/scripts/models/`, `skills/scripts/`, `skills/subagent-driven-development/`, or `tests/unit/` (only the repo-root `CLAUDE.md`), matching the prompt's own framing. `_base.py:4` confirms `CURRENT_SCHEMA_VERSION = 1`. The pattern reference correctly points at the three real precedent fields and their test classes; nothing else in the target directories was missed.

All six checks pass. The dispatch is ready to send.

---

## Controller note

The partner did more than confirm: its Architectural Alignment check produced a **first-hand
in-repo precedent** the controller's dispatch had argued for only from sequencing —
`implementer_report.py:32` declares its own `TaskType = Literal["implementation", "verification"]`
without importing `plan.py`'s identical literal. That converts "don't share it, Task 5 doesn't
exist yet" from an argument of convenience into an argument from established convention.
