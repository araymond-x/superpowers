# Spec Review Report — Pipeline Flexibility

**Reviewer**: spec-document-reviewer (general-purpose subagent)
**Passes**: 3
**Final Status**: Approved

## Pass 1 — Issues Found

1. **[C3]: Hook parsing mechanism unspecified.** Token estimation reads markdown task headers via grep, not YAML frontmatter. Reading `task_type` per task requires parsing the YAML `tasks:` array — different mechanism. **Fixed**: Spec now specifies `$PYTHON` with PyYAML for YAML frontmatter parsing.

2. **[C4]: Git reality check timestamp source fragile.** File mtime is unreliable (git checkout, editor auto-save can change it). Report mtime is task END time, not start. **Fixed**: Spec now uses dispatch log timestamps (hook-written, reliable). Required adding implementer dispatch logging to C3's scope.

**Advisory (pass 1)**:
- `entry_mode` field is informational-only — consider if it earns its keep. (Kept — lightweight audit trail.)
- `sdd-skill-enforcement-hook.sh` listed in audit scope but not active in settings.json. **Fixed**: Narrowed to 4 active hooks.
- Add `delete`/`remove` to keyword list. **Fixed**.

## Pass 2 — Issues Found

1. **[C4]: Dispatch log lacks implementer timestamps.** Dispatch log only records reviewer dispatches. Implementer dispatches pass through without logging. **Fixed**: C3 now adds implementer dispatch logging (`task=N type=implementer ts=ISO-8601`).

**Advisory (pass 2)**:
- SDD SKILL.md at 4753 words (5000-word limit). **Noted** in C6.

## Pass 3 — Approved

No issues found. Reviewer verified key claims against codebase:
- Plan model extension follows `review_tier` precedent
- 4-branch conflict detection matches brainstorming exactly
- Dispatch log currently only records reviewer entries; adding implementer entries is non-breaking
- Git reality check with dispatch log timestamps is sound
- validate-plan.py WARNING pattern is consistent with existing heuristic checks
- SDD SKILL.md word count confirmed at 4753 (247 words headroom)
- 4 active hooks correctly identified

**Advisory (pass 3)**:
- First-task edge case for git check (no previous timestamp). Unlikely in practice (Task 0 is always implementation). Planning-level detail.
- `check-distillation.sh` takes a path argument — planner should verify interface compatibility. Confirmed compatible.
