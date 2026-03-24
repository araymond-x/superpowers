# Final Audit Results — All v0.1 Skill Files

**Date**: 2026-03-23
**Audited**: 9 skill/prompt files + 4 Python scripts (13 files, 3700 lines)
**Reference**: "The Complete Guide to Building Skills for Claude" (Anthropic)

---

## Audit Summary

| Category | Files | Overall |
|----------|-------|---------|
| SKILL.md files (4) | brainstorming, writing-plans, SDD, handoff-acceptance | GOOD — 1 at borderline size |
| Prompt templates (5) | implementer, spec-reviewer, quality-reviewer, plan-reviewer, distillation-reviewer | GOOD — cross-template consistency needs work |
| Python scripts (4) | estimate-tokens, validate-report, controller-checkpoint, context-summary | GOOD — shared logic duplication is critical fix |

---

## CRITICAL Fixes (Fix Before Promoting to Production)

### C1. Script path resolution bug in SDD SKILL
**File**: `subagent-driven-development/SKILL-v0.1.md`
**Issue**: Scripts referenced as `python scripts/estimate-task-tokens.py` but live in the skill's `scripts/` directory, not the project root. Controller will get "file not found."
**Fix**: Reference via full skill-relative path (`~/.claude/skills/superpowers/subagent-driven-development/scripts/...`) or instruct controller to copy scripts to project during Plan Ingestion.

### C2. Extract shared logic into `_report_utils.py`
**Files**: All 4 scripts
**Issue**: Section validation logic duplicated in validate-report.py AND controller-checkpoint.py. Placeholder detection duplicated in validate-report.py AND context-summary.py. Status extraction duplicated in both. Will diverge on update.
**Fix**: Create `scripts/_report_utils.py` with shared functions: `extract_status()`, `find_section_headers()`, `section_is_present()`, `extract_section_content()`, `is_placeholder_text()`. All scripts import from it.

### C3. Remove `-v0.1` from frontmatter `name` fields
**Files**: brainstorming, writing-plans, SDD SKILL-v0.1.md
**Issue**: Guide requires `name` matches folder name in kebab-case. `-v0.1` suffix violates this.
**Fix**: Remove suffix when promoting to production SKILL.md.

### C4. Cite `distillation-reviewer-prompt.md` in brainstorming
**File**: `brainstorming/SKILL-v0.1.md`
**Issue**: Distillation review section says "dispatch a reviewer subagent" but never cites the existing prompt file.
**Fix**: Add explicit reference: `see distillation-reviewer-prompt.md`.

---

## IMPORTANT Fixes (High Priority)

### I1. SDD SKILL is at 97% of 5000-word limit
**Fix**: Move Example Workflow (~100 lines), Advantages (~37 lines), and condense Red Flags to `references/`. Saves ~600 words.

### I2. "Tests" regex too broad in validate-report.py
**Issue**: `r"tests?"` matches "Contract", "Attestation".
**Fix**: Change to `r"\btests?\b"`.

### I3. `section_contains_content` only handles bold headers
**File**: validate-report.py
**Issue**: `## Deviations from Plan` (ATX-style) not detected.
**Fix**: Extend pattern to match both `**bold**` and `## ATX` headers.

### I4. `count_plan_tasks` always returns >= 1 in context-summary.py
**Issue**: `if max_task >= 0` is always true. No-reports case returns 1 instead of 0.
**Fix**: Change to `if report_files`.

### I5. Spec reviewer needs BASE_SHA/HEAD_SHA
**Issue**: Spec reviewer told to "read the actual code" but has no git range placeholder.
**Fix**: Add `[CONTROLLER: BASE_SHA and HEAD_SHA, or changed file list]` placeholder.

### I6. Code quality reviewer missing implementer report placeholder
**Issue**: Additional checks reference implementer's "Deviations section" but no placeholder to receive it.
**Fix**: Add `[CONTROLLER: Paste implementer's full report here]`.

### I7. SDD description is WHEN-only, no WHAT
**Fix**: "Orchestrates implementation plans by dispatching a fresh subagent per task with two-stage review (spec + quality) after each. Use when executing a plan with independent tasks in the current session."

### I8. Worktree creation gap
**Issue**: writing-plans says "run in a dedicated worktree (created by brainstorming)" but brainstorming never creates one.
**Fix**: Add worktree creation to brainstorming checklist before invoking writing-plans, or remove assumption.

### I9. `find_report_file` non-deterministic in controller-checkpoint.py
**Issue**: Multiple matching files return in filesystem order.
**Fix**: Sort results, pick latest or highest-numbered.

---

## MEDIUM Priority Improvements

### M1. Inconsistent status vocabularies across templates
- Implementer: DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT
- Spec reviewer: PASS / FAIL / REPORT_INCOMPLETE
- Quality reviewer: Ready to merge? Yes/No/With fixes
- Plan reviewer: Approved / Issues Found
- Distillation reviewer: Approved / Issues Found
**Recommendation**: Standardize blocking/non-blocking dimension: APPROVED / BLOCKED / NEEDS_REVISION

### M2. Add `CLAUDE.md Files Read` to implementer report
Currently only `Source Files Read` is tracked. CLAUDE.md reading is equally critical.

### M3. Plan reviewer: move calibration to top
"Approve unless there are serious gaps" appears after all 42 lines of checks. Put it first per skills guide: "Put critical instructions at the top."

### M4. Plan size checks should be a script
800-line plan, 200-line task, 10+ tasks, missing Task 0 — all are `wc -l` and `grep` operations.
**Recommendation**: Create `scripts/validate-plan.py`.

### M5. Handoff acceptance "50-line" check should be a script
`head -50 README.md | grep -c "Contract"` is deterministic. Add `scripts/check-handoff.sh`.

### M6. Distillation artifact detection should be a script
`grep "Options Considered\|Rationale\|We considered"` in the distilled spec is deterministic.

### M7. Spec reviewer: add severity gradation to FAIL
Currently all findings are equal. Add BLOCKING vs ADVISORY to match quality reviewer's Critical/Important/Minor.

### M8. Large inline templates → references/
Move Task 0 template, Obsolescence Verification template, Module Template from writing-plans to `references/`.

### M9. Move Graphviz flowcharts to references/
SDD process flowchart is 106 lines. Brainstorming has one. Handoff-acceptance has one. Move to `references/process-diagram.dot`.

### M10. `<HARD-GATE>` XML tags in brainstorming
Replace with `## Critical Constraint` header to match guide's "No XML tags anywhere" checklist.

---

## LOW Priority (Polish)

- L1. Implementer: move "Work from: [directory]" to first item under "Your Job"
- L2. Implementer: replace vague "Verify implementation works" with concrete command placeholder
- L3. Spec reviewer: reframe "finished suspiciously quickly" to "assume incomplete until verified"
- L4. Spec reviewer: move CLAUDE.md check from "Missing requirements" to "Process Compliance"
- L5. Distillation reviewer: add check for decisions introduced (not just deleted/altered)
- L6. Distillation reviewer: classify size violations as BLOCKING vs advisory
- L7. Code quality reviewer: add scope note for task-level vs full-implementation review
- L8. Standardize `[CONTROLLER: ...]` annotations across all templates
- L9. Add model selection guidance to each template header
- L10. Context-summary.py: raise 5-item cap to 10 for Concerns section
- L11. Validate-report.py: fix misleading docstring on `find_sections`

---

## New Scripts Recommended

| Script | Purpose | Priority |
|--------|---------|----------|
| `scripts/_report_utils.py` | Shared library for section parsing, status extraction, placeholder detection | CRITICAL |
| `scripts/validate-plan.py` | Mechanical plan structure checks (task count, line counts, section presence) | MEDIUM |
| `scripts/check-handoff.sh` | Contract summary within first 50 lines of handoff README | MEDIUM |
| `scripts/check-distillation.sh` | Grep for exploration artifacts in distilled spec | MEDIUM |

---

## Positive Findings

- **Deterministic enforcement is strong**: The SDD skill excels at using scripts for critical validations — exactly what the guide recommends
- **Terminology is consistent**: "Contract Constraints", "Source Contracts", "DEVIATIONS.md", "Task 0" used uniformly across all skills
- **Pipeline composes correctly**: brainstorming → writing-plans → SDD chain is internally coherent
- **Handoff-acceptance is the best-structured skill**: Focused, appropriately sized, correct frontmatter
- **Progressive disclosure already used well**: brainstorming's `visual-companion.md` demonstrates the pattern
- **All scripts are Python 3.9 compatible** with no violations
