# Plan Document Header Template

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first — direct implementation bypasses review enforcement, quality gates, and hooks.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

**Source Contracts:** [List of external schemas, APIs, handoff packages this plan consumes. Write "None" if this plan is self-contained.]

**Contract Constraints:** [Non-negotiable facts from source contracts — types, formats, invariants. Write "None" if no external contracts.]

**Shared Constants:** [Constants, type definitions, enum values, and canonical value lists that subagents must import -- not redefine. Format: `CONSTANT_NAME` from `path/to/file.py`. Write "None" if no shared constants apply.]

**Pattern References:** [Existing files that demonstrate established patterns subagents should follow. Format: `path/to/file` — what pattern it demonstrates. Write "Greenfield — conventions defined in this plan" if no existing patterns apply. See Pattern Discovery section.]

**Feature Archetype:** [Greenfield | Replacement | Extension | Refactor | Migration]

**Code Footprint:**

| Category | Files / Functions | Action | Dependencies to Verify |
|----------|------------------|--------|----------------------|
| New | `path/to/new/file` | Create | — |
| Obsolete | `path/to/old/function` | Remove after verification | Check: [consumers] |
| Retained | `path/to/kept/function` | Keep | — |
| Modified | `path/to/changed/file` | Extend/modify | [existing consumers] |

---
```
