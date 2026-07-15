---
name: using-superpowers
description: "Use when starting any conversation, before responding to any request including clarifying questions"
---

<subagent-stop>
If you were dispatched as a subagent to execute a specific task, skip this skill.
</subagent-stop>

<important>
When a skill applies to your task, invoke it before responding. When in doubt — even a small chance a skill applies — invoke it to check. If the invoked skill turns out not to fit, you do not need to follow it.
</important>

## How to Access Skills

Use the `Skill` tool. When you invoke a skill, its content is loaded and presented to you — follow it directly. Never use the Read tool on skill files (the Read tool loads file content into context, consuming tokens and bypassing the skill loading mechanism).

# Using Skills

## The Rule

Invoke relevant or requested skills before any response or action — including clarifying questions, exploring the codebase, or checking files. When in doubt — even a small chance a skill applies — invoke it to check. If an invoked skill turns out wrong for the situation, you don't need to use it.

Before entering plan mode: if you haven't already brainstormed, invoke the brainstorming skill first.

Then announce "Using [skill] to [purpose]" and follow the skill exactly. If it has a checklist, create a todo per item.

## When to Invoke Skills

These situations all call for checking skills first:

| Thought | Why skills apply |
|---------|---------|
| "This is just a simple question" | Questions are tasks. Check for skills. |
| "I need more context first" | Skill check comes BEFORE clarifying questions. |
| "Let me explore the codebase first" | Skills tell you HOW to explore. Check first. |
| "I can check git/files quickly" | Files lack conversation context. Check for skills. |
| "Let me gather information first" | Skills tell you HOW to gather information. |
| "This doesn't need a formal skill" | If a skill exists, use it. |
| "I remember this skill" | Skills evolve. Read current version. Skills in this fork are actively maintained based on production incidents — the version in memory may predate a fix for the exact failure mode you're about to encounter. |
| "This doesn't count as a task" | Action = task. Check for skills. |
| "The skill is overkill" | Simple things become complex. Use it. |
| "I'll just do this one thing first" | Check BEFORE doing anything. |
| "This feels productive" | Undisciplined action wastes time. Skills prevent this. |
| "I know what that means" | Knowing the concept ≠ using the skill. Invoke it. |

## Skill Priority

When multiple skills could apply, use this order:

1. **Process skills first** (brainstorming, debugging) - these determine HOW to approach the task (implementation skills applied before process skills produce a local-optimum solution to the wrong problem)
2. **Implementation skills second** (frontend-design, mcp-builder) - these guide execution

"Let's build X" → brainstorming first, then implementation skills.
"Fix this bug" → debugging first, then domain-specific skills.

## User Instructions

User instructions (CLAUDE.md, direct requests) always take precedence: they override Superpowers skills, which in turn override default system prompt behavior. If CLAUDE.md says "don't use TDD" and a skill says "always use TDD," follow the user's instructions — the user is in control. Instructions say WHAT, not HOW: "Add X" or "Fix Y" doesn't mean skip workflows.
