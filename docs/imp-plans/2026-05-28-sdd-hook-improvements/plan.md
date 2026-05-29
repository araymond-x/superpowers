---
schema_version: 1
feature_archetype: extension
enforcement_tier: standard
source_contracts: null
shared_constants:
  - path: "skills/scripts/models/sdd_session.py::TIER_PROFILES"
    value: "tier->enforcement/process_requirements profiles"
    reason: "Test-helper migration (Task 5) must emit manifests via TIER_PROFILES, not hand-rolled dicts"
pattern_references:
  - name: "manifest-workspace-helper"
    source_files: ["tests/unit/sdd_test_helpers.py"]
    reason: "setup_manifest_workspace shows the canonical .sdd-session.json layout to mirror"
  - name: "review-tier-counter"
    source_files: ["skills/subagent-driven-development/scripts/controller-checkpoint.py"]
    reason: "_count_review_tiers + Check 7 ratio block is the code Task 3 refactors"
modules:
  - id: 1
    title: "Per-task review_tier declaration"
    task_ids: [1, 2, 3, 4]
    file: module-1-review-tier.md
  - id: 2
    title: "Hook classification and legacy removal"
    task_ids: [5, 6, 7, 8, 9]
    file: module-2-hook-classification.md
tasks:
  - id: 1
    title: "Add review_tier field to Task model"
  - id: 2
    title: "validate-plan.py review_tier heuristic warning"
  - id: 3
    title: "controller-checkpoint.py declared-minimum ratio exclusion"
  - id: 4
    title: "writing-plans SKILL.md review_tier decision table"
  - id: 5
    title: "Migrate SDD test helpers to manifest mode"
  - id: 6
    title: "Restructure hook classification + auto-create log + remove legacy path"
  - id: 7
    title: "Remove dead legacy branches (Item 5 cleanup)"
  - id: 8
    title: "Surface validation errors inline"
  - id: 9
    title: "Verification and documentation"
---

# SDD Hook Improvements — Implementation Plan (Parent)

> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first — direct implementation bypasses review enforcement, quality gates, and hooks.

**Goal:** Fix five SDD enforcement defects — `general-purpose` reviewer/implementer misclassification, opaque validation errors, missing dispatch-log auto-creation, the minimum-tier ratio penalizing legitimately-mechanical tasks, and the weaker legacy (non-manifest) dispatch path — without weakening enforcement rigor.

**Architecture:** Two independent, file-disjoint threads. **Module 1 (review_tier)** adds an optional per-task `review_tier` field to the plan schema and threads it through the validation heuristic and the pre-completion ratio check. **Module 2 (hook)** restructures `sdd-pre-dispatch-hook.sh` into a 3-stage classification pipeline, auto-creates the dispatch log, removes the legacy path entirely, and migrates the test helpers to manifest mode. The two modules touch no common source files; a final verification task reconciles documentation and runs all test layers.

**Tech Stack:** Bash (hook), Python 3.9-compatible (Pydantic models, checkpoint/validate scripts), pytest (unit tests). Enforcement is manifest-driven via `.sdd-session.json`.

**Source Contracts:** None

This plan modifies the superpowers fork's own enforcement scripts, models, and tests — there is no external schema, API, or handoff package. The internal "contracts" (existing code line ranges, the `SddSession`/`Plan` Pydantic models) are version-controlled in this repo. Because Source Contracts is None, no Task 0 (Contract Verification) is required.

**Contract Constraints (non-negotiable invariants):**
- `review_tier` field type is `Literal["minimum", "full"]` with default `"full"`. It is optional per task. It must work with `StrictModel` (`extra="forbid"`) — use a default value, never `Optional`/`None`.
- `review_tier` is **orthogonal** to `enforcement_tier`. Never derive one from the other.
- Adding `review_tier` is **non-breaking** — do **NOT** bump `CURRENT_SCHEMA_VERSION` in `_base.py`.
- The minimum-tier ratio threshold stays at **50%**. Only the denominator changes (declared-minimum tasks are excluded from numerator AND denominator).
- The new manifest-mode classification order is exactly: **reviewer detection → implementer detection → passthrough**.
- The legacy (non-manifest) dispatch path is removed entirely. Manifest mode is required for SDD enforcement.
- Dispatch-log auto-creation uses `mkdir -p "$(dirname "$DISPATCH_LOG")"` + `touch "$DISPATCH_LOG"` (both idempotent).
- Validation-error excerpt uses `head -n 12` (line-based, not `head -c`). **Corrects the spec:** `validate-report.py`'s first 5 lines are a decorative banner (`═══` box + "VALIDATION FAILED" + "N issue(s) found" + `═══` + blank); the first field name appears at line 6. `head -n 12` surfaces the first two failing fields. The spec's "first 5 lines includes field names" (spec.md line 110) was empirically wrong about the output format.
- Reviewer dispatches must be logged **before** any passthrough — the unfixed bug is that `general-purpose` (line 169) exits before reviewer detection (line 174).

**Shared Constants:** `TIER_PROFILES` from `skills/scripts/models/sdd_session.py` — the test-helper migration (Task 5) must build manifests from this dict (as `setup_manifest_workspace` already does), not hand-roll enforcement/process-requirements values.

**Pattern References:**
- `tests/unit/sdd_test_helpers.py` (`setup_manifest_workspace`, lines 313-431) — the canonical `.sdd-session.json` workspace layout that Task 5's helper migration mirrors.
- `skills/subagent-driven-development/scripts/controller-checkpoint.py` (`_count_review_tiers` lines 188-212; Check 7 ratio block lines 1054-1098) — the exact code Task 3 refactors.
- `tests/unit/test_pre_completion_gates.py` (`_make_reports_with_minimum_tier`, `run_pre_completion`) — the harness Task 3's new tests extend.

**Feature Archetype:** Extension (adds the `review_tier` axis and restructures the hook; one removal — the legacy dispatch path — handled as part of the hook restructure, not a standalone Replacement).

**Code Footprint:**

| Category | Files / Functions | Action | Dependencies to Verify |
|----------|------------------|--------|------------------------|
| Modified | `skills/scripts/models/plan.py` (`Task` model) | Add `review_tier` field | Consumers: `validators.py plan`, `validate-plan.py`, `controller-checkpoint.py` |
| Modified | `skills/subagent-driven-development/scripts/validate-plan.py` | Add review_tier heuristic warning | Tests: `test_validate_plan.py` |
| Modified | `skills/subagent-driven-development/scripts/controller-checkpoint.py` | Refactor ratio to per-task w/ declared-minimum exclusion | Tests: `test_pre_completion_gates.py` |
| Modified | `skills/writing-plans/SKILL.md` | Add review_tier decision table (~200 words) | Word-count limit 5000 (currently ~4100) |
| Modified | `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` | 3-stage classification, auto-create log, inline errors, remove legacy path + dead branches | Tests: all `test_sdd_*.py` |
| Modified | `tests/unit/sdd_test_helpers.py` | Migrate `setup_sdd_workspace`/`setup_full_sdd_workspace` to manifest mode | Callers: 4 hook test files |
| Modified | `tests/unit/test_sdd_hard_gates.py`, `test_sdd_dispatch_log.py`, `test_sdd_partner_gate.py`, `test_sdd_midpoint_check.py` | Update for manifest mode + legacy removal | — |
| New | `tests/unit/test_sdd_classification.py` | Net-new Item 1/3/5 classification tests | — |
| Modified | `CLAUDE.md`, `docs/ARaymond-customization-manifest.md` | Update test counts + behavior notes | Run all 5 test layers |
| Obsolete | Legacy path in `sdd-pre-dispatch-hook.sh` (lines 123-153, 226-273; dead `else` branches in Checks 5/6/6b; `IS_IMPLEMENTER=false` guard 276-278) | Remove (Task 6) | Verified: only legacy-helper tests reference it; migrated in Task 5 first |

## File Map

```
docs/imp-plans/2026-05-28-sdd-hook-improvements/
  plan.md                       ← this parent (coordination only)
  module-1-review-tier.md       ← Tasks 1-4 (review_tier thread)
  module-2-hook-classification.md ← Tasks 5-9 (hook thread + verification)

Source files touched:
  Module 1: skills/scripts/models/plan.py
            skills/subagent-driven-development/scripts/validate-plan.py
            skills/subagent-driven-development/scripts/controller-checkpoint.py
            skills/writing-plans/SKILL.md
            tests/unit/test_models/test_plan_model.py
            tests/unit/test_validate_plan.py
            tests/unit/test_pre_completion_gates.py
  Module 2: tests/unit/sdd_test_helpers.py
            skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh
            tests/unit/test_sdd_hard_gates.py
            tests/unit/test_sdd_dispatch_log.py
            tests/unit/test_sdd_partner_gate.py
            tests/unit/test_sdd_midpoint_check.py
            tests/unit/test_sdd_classification.py (new)
            CLAUDE.md, docs/ARaymond-customization-manifest.md
```

## Module Inventory

| Module | Goal | File |
|--------|------|------|
| 1 | Per-task `review_tier` declaration (Items 4a-4d) | `module-1-review-tier.md` |
| 2 | Hook classification + legacy removal (Items 1, 2, 3, 5) + verification | `module-2-hook-classification.md` |

## Module Dependency Graph

```
Module 1 (review_tier)        Module 2 (hook)
  Task 1 plan.py field          Task 5 helper migration
    ├── Task 2 validate-plan      └── Task 6 classification+log+guard ← dep 5
    ├── Task 3 checkpoint              └── Task 7 dead-branch removal ← dep 6
    └── Task 4 SKILL.md                    └── Task 8 hook Item 2     ← dep 7
                                  Task 9 verification ← dep 6,7,8 AND Module 1
```

**Module 1 and Module 2 are file-disjoint** (no shared source file) and could in principle run in parallel. They are executed **sequentially (Module 1 → Module 2)** to keep one SDD run active at a time and because the final verification task (Task 9, in Module 2) runs the full suite — including Module 1's tests — and must therefore come last.

Within Module 1: Task 1 blocks Tasks 2 and 3 (both need the `review_tier` field to exist before frontmatter using it validates). Task 4 (docs) is independent. Tasks 2 and 3 are parallel candidates after Task 1.

Within Module 2: Task 5 (helper migration) blocks Task 6 (hook restructure relies on migrated manifest-mode tests staying green). Tasks 6→7→8 are serial on the hook file. Task 9 depends on 6, 7, 8 and all of Module 1.

## Cross-Module Write-Scope Partitioning

No source file is written by more than one task in parallel. The hook file is edited by Tasks 6, 7, 8 — all strictly serial (6→7→8), so no parallel conflict. `test_sdd_hard_gates.py` is owned by Task 5; `test_sdd_classification.py` is created by Task 6 and appended by Task 8 (serial).

| Task | Module | Owned Files (write) | Depends On |
|------|--------|---------------------|------------|
| 1 | 1 | `skills/scripts/models/plan.py`, `tests/unit/test_models/test_plan_model.py` | — |
| 2 | 1 | `skills/subagent-driven-development/scripts/validate-plan.py`, `tests/unit/test_validate_plan.py` | 1 |
| 3 | 1 | `skills/subagent-driven-development/scripts/controller-checkpoint.py`, `tests/unit/test_pre_completion_gates.py` | 1 |
| 4 | 1 | `skills/writing-plans/SKILL.md` | — |
| 5 | 2 | `tests/unit/sdd_test_helpers.py`, `tests/unit/test_sdd_hard_gates.py`, `tests/unit/test_sdd_dispatch_log.py`, `tests/unit/test_sdd_partner_gate.py`, `tests/unit/test_sdd_midpoint_check.py` | — |
| 6 | 2 | `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`, `tests/unit/test_sdd_classification.py` (new) | 5 |
| 7 | 2 | `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` | 6 |
| 8 | 2 | `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`, `tests/unit/test_sdd_classification.py` | 7 |
| 9 | 2 | `CLAUDE.md`, `docs/ARaymond-customization-manifest.md` | 6, 7, 8 |

> **Note on the hook file shared by Tasks 6/7/8:** strictly serial. Task 6 = classification pipeline + auto-create log + manifest guard (Items 1, 3, and the dispatch-detection part of 5). Task 7 = dead-branch removal in the enforcement checks (rest of Item 5). Task 8 = Item 2 inline validation errors (Check 4b). Splitting keeps each task focused and under the 200-line limit.

## Spec Coverage Note (read before execution)

The distilled spec's "Test Files" table named only 3 hook-test files. During planning, the legacy-removal blast radius was found to be **~3× larger**:
- `test_sdd_midpoint_check.py` tests the legacy plan-globbing midpoint logic (hook lines 737-775) that Item 5 deletes — **must be reworked** (Task 5).
- `test_sdd_hard_gates.py`'s `TestFeatureDirLayout` (6 tests, legacy `feature_dir_workspace` fixture) and `TestBackwardsCompatFallback` break under the new guard clause — **migrated/rewritten** (Tasks 5/6).
- The shared helpers `setup_sdd_workspace`/`setup_full_sdd_workspace` build non-manifest workspaces; after Item 5 they exit the guard clause without enforcing, silently inverting block tests — **migration is the linchpin** (Task 5).
- `test_honesty_log_capture.py` is a confirmed false positive (it tests `sdd-stop-hook.sh` with its own local helper) — **out of scope**.

The execution order (migrate helpers to manifest mode first, against the *unchanged* hook; then remove the legacy path) keeps each step tractable.

## Acceptance Criteria (whole feature)

All criteria from `spec.md` lines 285-301, summarized:
- [ ] Reviewer dispatches with `subagent_type: "general-purpose"` are logged (not passthrough'd)
- [ ] Implementer dispatches with `subagent_type: "general-purpose"` are enforced
- [ ] Non-reviewer/non-implementer dispatches during SDD are allowed without enforcement
- [ ] Validation errors include the first 5 lines of `validate-report.py` output
- [ ] First reviewer dispatch creates `reports/` + dispatch log if missing
- [ ] Declared `review_tier: minimum` tasks excluded from ratio denominator (quality + partner)
- [ ] Undeclared minimum-tier reviews still trigger the >50% blocker
- [ ] Modular plans: all module plan files read for the exclusion set
- [ ] Plan-parse failure → current behavior + WARNING
- [ ] `validate-plan.py` warns on suspicious `review_tier` + high-risk keywords (not "migration" alone)
- [ ] No manifest + SDD artifacts → BLOCKED; no manifest + no artifacts → ALLOWED
- [ ] Dead legacy branches removed
- [ ] All existing tests pass with updates; new tests cover changed behavior
- [ ] `CLAUDE.md` + customization manifest updated with new test counts and behavior

## Validation Sequence (Plan Completion Gate)

1. `validate-plan.py` on parent + both module files (parent additionally with `--additional-plan-files` for cross-module collision check).
2. Dispatch `plan-document-reviewer` for the complete set.
3. Save review to `plan-review-report.md`.
4. Write `plan-manifest.txt` listing all three plan files.
