# Subagent CLAUDE.md Enforcement — Prompt Template Modifications

**Version**: 1.1
**Last Updated**: 2026-03-17
**Source**: Custom fork at `~/projects/claude-custom/superpowers` (migrated from `superpowers@claude-plugins-official` plugin)
**Original Plugin Version at Time of Edit**: `4.3.1`
**Current Edit Location**: `~/projects/claude-custom/superpowers/skills/subagent-driven-development/`

---

## Summary

Two prompt templates in the `superpowers:subagent-driven-development` skill were modified to enforce that implementer and spec-reviewer subagents read subdirectory CLAUDE.md files before writing or reviewing code.

## Rationale

During Phase 8 (Statement Reconciliation, Mar 1 2026), the `subagent-driven-development` skill dispatched 12+ frontend subagents. Only 2 of 12 frontend-touching prompts included instructions to read `frontend/CLAUDE.md`. The subagent that built `StatementCreateForm.tsx` (Task 13) never read the frontend design system docs, producing 9 design system violations that required a full rewrite.

Root causes identified:
1. **Subagents don't inherit parent context** — the orchestrator's knowledge of CLAUDE.md files is not passed to spawned subagents
2. **Inconsistent prompt construction** — the orchestrator included the instruction in some prompts but not others
3. **Post-hoc design review** — the `ar-design-reviewer` caught violations after code was written, not during

These prompt template edits address cause #1 at the skill level, making CLAUDE.md discovery a default behavior for all subagents regardless of what the orchestrator includes.

---

## Modification 1: `implementer-prompt.md`

**What**: Added a `## Subdirectory CLAUDE.md Files` section between `## Context` and `## Before You Begin`.

**Insert after line 17** (after `[Scene-setting: where this fits, dependencies, architectural context]`):

```
    ## Subdirectory CLAUDE.md Files

    **CRITICAL**: Before writing any code, check if the directories you will modify
    contain their own CLAUDE.md files. Read them first. These contain design systems,
    UI primitives, naming conventions, and anti-patterns specific to that part of the
    codebase. Subagents do NOT inherit the parent session's knowledge of these files.

    Skipping this step has caused full rewrites in the past — agents used native HTML
    inputs, wrong typography variants, and inline styling because they never read the
    local CLAUDE.md that documented the correct patterns.
```

---

## Modification 2: `spec-reviewer-prompt.md`

**What**: Added a CLAUDE.md verification check under the `**Missing requirements:**` section.

**Insert after line 44** (after `- Did they claim something works but didn't actually implement it?`):

```
    - Did they look for and read any CLAUDE.md files in directories containing modifications?
```

---

## How to Apply (Custom Fork)

As of 2026-03-17, superpowers is installed from a custom fork (`~/projects/claude-custom/superpowers`) via symlinks to `~/.claude/skills/superpowers/`. Edits are made directly in the fork repo — no plugin cache re-apply needed.

1. Edit the prompt templates directly:
   ```bash
   vim ~/projects/claude-custom/superpowers/skills/subagent-driven-development/implementer-prompt.md
   vim ~/projects/claude-custom/superpowers/skills/subagent-driven-development/spec-reviewer-prompt.md
   ```

2. Changes take effect immediately (symlinked).

3. When pulling upstream updates (`git pull upstream main`), resolve merge conflicts to preserve these modifications.

**Status**: These modifications have NOT yet been applied to the fork's current v5.0.5 templates. The modifications above were written against v4.3.1. Review the current template structure before applying — the templates may have changed significantly.

---

## Complementary Safeguards

These prompt template edits work alongside two other safeguards:

| Layer | Location | What It Does |
|-------|----------|-------------|
| **Project CLAUDE.md rule** | `CLAUDE.md` > "Subagent Frontend Context Rule" | Tells the orchestrator to include `frontend/CLAUDE.md` read instructions in every frontend subagent prompt |
| **Implementer template** | This modification (Mod 1) | Tells the subagent itself to look for CLAUDE.md files in target directories |
| **Spec reviewer template** | This modification (Mod 2) | Tells the reviewer to verify the subagent actually read CLAUDE.md files |

All three layers are needed because any single layer can fail (orchestrator forgets, subagent ignores, reviewer doesn't check).

---

## Modification Log

| Date | Version | Change |
|------|---------|--------|
| 2026-03-08 | 1.0 | Initial creation. Added CLAUDE.md enforcement to implementer and spec-reviewer prompts in superpowers 4.3.1. |
| 2026-03-17 | 1.1 | Updated for custom fork migration. Plugin cache paths replaced with fork repo paths. Re-apply instructions updated. Modifications not yet applied to v5.0.5 templates. |
