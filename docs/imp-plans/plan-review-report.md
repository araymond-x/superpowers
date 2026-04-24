# Plan Review Report — Pydantic Phase 1

**Date:** 2026-04-24
**Reviewer:** Plan-document-reviewer subagent (general-purpose)
**Plan files reviewed:** 4 (parent + 3 modules)

## Plan Review

**Status:** Approved (after 1 round of fixes)

**Round 1 — Issues Found:**

1 blocking issue, 5 advisory recommendations.

**Blocking Issue (fixed):**
- [SPEC LOCK / BUILDABILITY]: Task 9, validate-plan.py frontmatter detection would break 22 existing test fixtures. **Resolution:** Restructured Task 9 so validate-plan.py adds Pydantic as an additive check (when frontmatter present) and a warning (when absent), preserving backward compatibility. Hard FAIL for missing frontmatter lives only in validators.py (the Pydantic CLI called by hooks).

**Advisory Recommendations (addressed):**
1. Missing PyYAML in requirements.txt — **Fixed**: Added `pyyaml>=6.0` to Task 1.
2. conftest.py collision risk — **Noted**: Low risk, acceptable. sys.path addition is benign.
3. Task 8 Step 5 vague (handoff-gate-hook.sh) — **Fixed**: Replaced with explicit implementation showing Pydantic validation block placement.
4. Task 8 Step 4 check-handoff.sh path derivation — **Noted**: Acceptable — check-handoff.sh always receives README.md path from its callers.
5. Task 12 `find -newer` syntax wrong for macOS — **Fixed**: Replaced with `ls -lt` and date-pattern glob.
6. Test count discrepancy (spec ~45, plan ~78) — **Noted**: Plan delivers more tests than spec estimated. Not a problem.
7. SDD SKILL.md word count handled in plan — **Noted**: Plan correctly warns about offset.

**Snippet Verification:**
- Snippet 1 (plan.py model, Module 1 Task 3): **VERIFIED** — all field names, types, validators match spec
- Snippet 2 (handoff.py model, Module 1 Task 4): **VERIFIED** — all field names, types, validators match spec
- Snippet 3 (errors.py formatter, Module 1 Task 5): **VERIFIED** — three distinct headers, ctx.expected handling, schema_version hint
- Snippet 4 (validators.py CLI, Module 2 Task 6): **ILLUSTRATIVE** — direct invocation vs -m invocation; both work, plan approach matches existing patterns

**Cross-Document Audit:**
- `Plan.feature_archetype`: spec=`Literal["greenfield","replacement","extension","refactor","migration"]` → plan=identical → code=identical — **MATCH**
- `HandoffPackage.contract_constraints`: spec=`list[FieldType]` → plan=identical → code=identical — **MATCH**
- `SchemaVersionedModel.schema_version`: spec=int pinned via @field_validator → plan=identical → code=identical — **MATCH**

## Validation Results

| File | Status | Blockers | Warnings |
|------|--------|----------|----------|
| Parent plan | PASS | 0 | 0 |
| Module 1 (Models) | WARNING | 0 | 1 (Task 3 at 335 lines) |
| Module 2 (CLI+Hooks) | WARNING | 0 | 3 (Tasks 6-7 slightly over 200 lines) |
| Module 3 (Cutover) | PASS | 0 | 0 |
| Cross-module collision | PASS | 0 | — |

Task size warnings are accepted: Plan model has 5 cross-field validators requiring thorough tests, and CLI subcommands need full test + implementation code. Splitting these would fragment TDD cycles without meaningful benefit.
