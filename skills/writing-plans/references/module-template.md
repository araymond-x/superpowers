# Module Template

> Part of the writing-plans skill. Referenced from SKILL.md.

Use this template when a plan is decomposed into modules (plan exceeds 800 lines or decomposes cleanly by boundary).

**Parent plan registration:** Each module is registered in the parent plan's YAML frontmatter `modules:` array. Include a `file:` field pointing to the module file path (relative to the feature dir):

```yaml
modules:
  - id: N
    title: "Module Name"
    task_ids: [0, 1, 2]
    file: module-N-name.md  # path to this module file (relative to feature dir)
```

```markdown
# [Feature Name] — Module N: [Module Name]

> **Parent plan:** `<feature-dir>/plan.md`
> **Module:** N of M
> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first — direct implementation bypasses review enforcement, quality gates, and hooks.

**Module Goal:** [One sentence describing what this module delivers independently]

**Source Contracts:** [External schemas, APIs, or handoff packages this module consumes. Write "None" if self-contained.]

**Contract Constraints:** [Non-negotiable facts from source contracts — types, formats, invariants. Write "None" if no external contracts.]

**Feature Archetype:** [Greenfield | Replacement | Extension | Refactor | Migration]

## File Map

| File | Responsibility |
|------|----------------|
| `exact/path/to/file.py` | [what it does] |

## Write-Scope Partitioning

| Task | Owned Files (write) | Read-Only Files | Depends On |
|------|---------------------|-----------------|------------|
| Task 0 | tests/fixtures/... | contracts/... | — |
| Task 1 | src/... | config.py | Task 0 |

## Acceptance Criteria

- [ ] [Specific, testable criterion — behavior, not just "tests pass"]
- [ ] [Another specific criterion]

---

## Tasks

### Task 0: Contract Verification (BLOCKING)
[Include only if this module has Source Contracts. Use the Task 0 template from the Ground-Truth Fixtures section.]

### Task 1: [Name]
[Follow the Task Structure format]

### Task 2: [Name]
[Follow the Task Structure format]
```
