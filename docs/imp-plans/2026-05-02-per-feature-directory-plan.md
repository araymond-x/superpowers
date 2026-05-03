---
schema_version: 1
feature_archetype: migration
source_contracts: "docs/specs/2026-05-02-per-feature-directory-design-distilled.md"
shared_constants: []
pattern_references:
  - name: "superpowers-root-resolution"
    source_files: ["skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh"]
    reason: "SUPERPOWERS_ROOT self-resolution preamble pattern (lines 27-34)"
  - name: "hook-feat-prefix"
    source_files: ["tests/poc-feature-directory/sdd-pre-dispatch-hook-patched.sh"]
    reason: "POC demonstration of feature-dir prefix for artifact paths"
modules:
  - id: 1
    title: "Infrastructure & Testing Foundation"
    task_ids: [0, 1, 2, 3]
  - id: 2
    title: "Hook Script Migration"
    task_ids: [4, 5, 6, 7, 8, 9]
  - id: 3
    title: "Skills, Templates & Documentation"
    task_ids: [10, 11, 12, 13, 14]
tasks:
  - id: 0
    title: "Contract Verification"
  - id: 1
    title: "Add .active-feature to .gitignore and create test helpers"
    depends_on: [0]
    module_id: 1
  - id: 2
    title: "Unit tests for .active-feature resolution and conflict detection"
    depends_on: [1]
    module_id: 1
  - id: 3
    title: "Unit tests for feature name validation"
    depends_on: [2]
    module_id: 1
  - id: 4
    title: "Migrate sdd-pre-dispatch-hook.sh path resolution"
    depends_on: [2]
    module_id: 2
  - id: 5
    title: "Migrate plan-validation-gate-hook.sh"
    depends_on: [2]
    module_id: 2
  - id: 6
    title: "Migrate sdd-stop-hook.sh"
    depends_on: [2]
    module_id: 2
  - id: 7
    title: "Update sdd-report-guard.sh regexes"
    depends_on: [2]
    module_id: 2
  - id: 8
    title: "Add --feature-dir to controller-checkpoint.py and context-summary.py"
    depends_on: [2]
    module_id: 2
  - id: 9
    title: "Update unit tests for hook migrations"
    depends_on: [4, 5, 6, 7, 8]
    module_id: 2
  - id: 10
    title: "Update entry-point skills (brainstorming, writing-plans, handoff-acceptance)"
    depends_on: [4]
    module_id: 3
  - id: 11
    title: "Update execution skills (SDD, executing-plans, finishing-a-development-branch)"
    depends_on: [4]
    module_id: 3
  - id: 12
    title: "Update prompt templates and references"
    depends_on: [11]
    module_id: 3
  - id: 13
    title: "Update regression tests and POC tests"
    depends_on: [9, 12]
    module_id: 3
  - id: 14
    title: "Update CLAUDE.md and documentation"
    depends_on: [13]
    module_id: 3
---

# Per-Feature Directory Migration — Implementation Plan

> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first — direct implementation bypasses review enforcement, quality gates, and hooks.

**Goal:** Consolidate all Superpowers execution artifacts into self-contained `docs/imp-plans/YYYY-MM-DD-<feature-name>/` directories, with `.active-feature` file for hook discovery and automated lifecycle management.

**Architecture:** Introduce `.active-feature` file at project root as canonical pointer to active feature directory. All hooks read this file and prefix artifact paths with its content. Entry-point skills prompt for feature name and create the directory. Finishing skill cleans up. Hooks fall back to root-level paths when `.active-feature` absent (backwards compat).

**Tech Stack:** Bash (hooks), Python 3.9+ (scripts), Markdown (skills/templates)

**Source Contracts:** `docs/specs/2026-05-02-per-feature-directory-design-distilled.md`

**Contract Constraints:**
- `.active-feature` is single-line plaintext, gitignored, contains relative path
- Feature dir format: `docs/imp-plans/YYYY-MM-DD-<feature-name>/`
- `deviations.md` is lowercase (was `DEVIATIONS.md`)
- Hooks fall back to root-level paths when `$FEAT` is empty
- `SUPERPOWERS_ROOT` self-resolution must be added to hooks that lack it

**Shared Constants:** None

**Pattern References:**
- `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` lines 27-34 — `SUPERPOWERS_ROOT` self-resolution preamble and `$PYTHON` derivation
- `tests/poc-feature-directory/sdd-pre-dispatch-hook-patched.sh` — POC feature-dir prefix pattern for artifact paths

**Feature Archetype:** Migration

**Code Footprint:**

| Category | Files / Functions | Action | Dependencies to Verify |
|----------|------------------|--------|----------------------|
| Modified | `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` | Add `.active-feature` reading, prefix all paths | settings.json hook reference |
| Modified | `skills/writing-plans/scripts/plan-validation-gate-hook.sh` | Add `.active-feature` gate, SUPERPOWERS_ROOT | settings.json hook reference |
| Modified | `skills/subagent-driven-development/scripts/sdd-stop-hook.sh` | Add `.active-feature` reading, SUPERPOWERS_ROOT | settings.json hook reference |
| Modified | `skills/subagent-driven-development/scripts/sdd-report-guard.sh` | Update suspicious-pattern regexes | settings.json hook reference |
| Modified | `skills/subagent-driven-development/scripts/controller-checkpoint.py` | Add `--feature-dir` argument | Hook scripts that invoke it |
| Modified | `skills/subagent-driven-development/scripts/context-summary.py` | Add `--feature-dir` argument | SKILL.md references |
| Modified | `skills/brainstorming/SKILL.md` | Feature name prompt, spec output path | Command stub description |
| Modified | `skills/writing-plans/SKILL.md` | Feature name prompt, plan output paths | Command stub description |
| Modified | `skills/handoff-acceptance/SKILL.md` | Feature name prompt on ACCEPTED | Command stub description |
| Modified | `skills/subagent-driven-development/SKILL.md` | All artifact path references | Prompt templates |
| Modified | `skills/executing-plans/SKILL.md` | Artifact path references | — |
| Modified | `skills/finishing-a-development-branch/SKILL.md` | Add cleanup step | — |
| Modified | 4 prompt templates | Path references in controller-partner, pre-execution-audit, trace-auditor, report-naming-convention | SKILL.md dispatch instructions |
| Modified | `.gitignore` | Add `.active-feature` | — |
| Modified | `tests/unit/test_sdd_hard_gates.py` | Update fixture paths | Hook script changes |
| Modified | `tests/ARaymond-skill-regression/validate-all-skills.py` | Add `.active-feature` checks | — |
| Obsolete | `tests/poc-feature-directory/sdd-pre-dispatch-hook-patched.sh` | Delete after real hooks support feature dirs | POC tests reference it |

## Module Dependency Graph

```
Module 1 (Infrastructure & Testing Foundation)
  └── Module 2 (Hook Script Migration) ← depends on Module 1
      └── Module 3 (Skills, Templates & Documentation) ← depends on Module 2
```

**No parallel candidates** — each module builds on the prior one. Module 2 needs the test helpers from Module 1. Module 3 needs the hooks from Module 2 to be working before updating the skills that reference them.

## Module Inventory

| Module | File | Goal | Tasks |
|--------|------|------|-------|
| 1 | `docs/imp-plans/2026-05-02-per-feature-directory-module-1-infrastructure.md` | `.gitignore`, test helpers, unit tests for `.active-feature` resolution and conflict detection | 0-3 |
| 2 | `docs/imp-plans/2026-05-02-per-feature-directory-module-2-hooks.md` | Migrate all 4 hook scripts + 2 Python scripts to use `.active-feature` | 4-9 |
| 3 | `docs/imp-plans/2026-05-02-per-feature-directory-module-3-skills.md` | Update SKILL.md files, prompt templates, references, regression tests, CLAUDE.md | 10-14 |
