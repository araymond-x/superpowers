---
name: brainstorming
description: "Use when starting any creative or implementation work — building features, adding functionality, modifying behavior, or designing components — before writing a spec or touching code."
---

# Brainstorming Ideas Into Designs

Help turn ideas into fully formed designs and specs through natural collaborative dialogue.

Start by understanding the current project context, then ask questions one at a time to refine the idea. Once you understand what you're building, present the design and get user approval.

## CRITICAL CONSTRAINT

**Do NOT invoke any implementation skill, write any code, scaffold any project, or take any implementation action until you have presented a design and the user has approved it. This applies to EVERY project regardless of perceived simplicity.** Implementation without a written design produces code that encodes decisions the user hasn't reviewed.

## Every Project Gets a Design

Every project goes through this process. A todo list, a single-function utility, a config change — all of them. "Simple" projects are where unexamined assumptions cause the most wasted work. The design can be short (a few sentences for truly simple projects), but present it and get approval.

## Checklist

Create a task for each of these items and complete them in order:

1. **Explore project context** — check files, docs, recent commits. If the user references external handoff packages, schemas, or code from another agent/team, invoke `superpowers:handoff-acceptance` to verify the package before proceeding with design questions.
2. **Offer visual companion** (if topic will involve visual questions) — this is its own message, not combined with a clarifying question. See the Visual Companion section below.
3. **Ask clarifying questions** — one at a time, understand purpose/constraints/success criteria
4. **Propose 2-3 approaches** — with trade-offs and your recommendation
5. **Present design** — in sections scaled to their complexity, get user approval after each section
6. **Write design doc** — save to `docs/specs/YYYY-MM-DD-<topic>-design.md` and commit
7. **Spec review loop** — dispatch spec-document-reviewer subagent with precisely crafted review context (never your session history); fix issues and re-dispatch until approved (max 3 iterations, then surface to human)
7.5. **Distill spec for implementation** — produce `*-design-distilled.md` alongside the full spec
8. **User reviews written spec** — ask user to review the spec file before proceeding
9. **Set up implementation workspace** — invoke `superpowers:using-git-worktrees` to create an isolated worktree for the implementation work
10. **Transition to implementation** — invoke writing-plans skill to create implementation plan (in the worktree)

## Process Flow

See `references/process-flow.dot` for the complete process flow diagram (Graphviz dot format).

**The terminal state is invoking writing-plans.** After brainstorming, the next skill is always writing-plans — not frontend-design, mcp-builder, or any other implementation skill. Frontend-design, mcp-builder, and other implementation skills each assume the design is settled. Invoking them during brainstorming bypasses the design review step.

## The Process

**Understanding the idea:**

- Check out the current project state first (files, docs, recent commits)
- Before asking detailed questions, assess scope: if the request describes multiple independent subsystems (e.g., "build a platform with chat, file storage, billing, and analytics"), flag this immediately. Don't spend questions refining details of a project that needs to be decomposed first.
- If the project is too large for a single spec, help the user decompose into sub-projects: what are the independent pieces, how do they relate, what order should they be built? Then brainstorm the first sub-project through the normal design flow. Each sub-project gets its own spec → plan → implementation cycle.
- For appropriately-scoped projects, ask questions one at a time to refine the idea
- Prefer multiple choice questions when possible, but open-ended is fine too
- Only one question per message - if a topic needs more exploration, break it into multiple questions
- Focus on understanding: purpose, constraints, success criteria
- After 3-4 clarifying questions, assess whether you have enough to propose approaches. You do not need complete information to propose — you need enough to identify the main trade-off.
- Identify the feature archetype early: Is this greenfield (no existing code affected), replacement (existing code becomes obsolete), extension (adding to existing), refactor (restructuring), or migration (phased transition)? This classification determines what the spec needs to document about existing code impact. Archetype identification determines what the spec needs to document — a replacement archetype requires obsolescence tracking; a refactor requires consumer verification.

**Exploring approaches:**

- Propose 2-3 different approaches with trade-offs
- Present options conversationally with your recommendation and reasoning
- Lead with your recommended option and explain why

**Presenting the design:**

- Once you believe you understand what you're building, present the design
- Scale each section to its complexity: a few sentences if straightforward, up to 200-300 words if nuanced
- Ask after each section whether it looks right so far
- Cover: architecture, components, data flow, error handling, testing
- For replacement, refactor, and migration archetypes: explicitly document which existing code/components become obsolete and what dependencies must be verified before removal
- Be ready to go back and clarify if something doesn't make sense
- Once the user has approved the design direction, commit to it. Write the spec from the approved design — do not re-open architectural questions during the writing phase.

**Design for isolation and clarity:**

- Break the system into smaller units that each have one clear purpose, communicate through well-defined interfaces, and can be understood and tested independently
- For each unit, you should be able to answer: what does it do, how do you use it, and what does it depend on?
- Can someone understand what a unit does without reading its internals? Can you change the internals without breaking consumers? If not, the boundaries need work.
- Smaller, well-bounded units are also easier for you to work with - you reason better about code you can hold in context at once, and your edits are more reliable when files are focused. When a file grows large, that's often a signal that it's doing too much.

**Working in existing codebases:**

- Explore the current structure before proposing changes. Follow existing patterns.
- Where existing code has problems that affect the work (e.g., a file that's grown too large, unclear boundaries, tangled responsibilities), include targeted improvements as part of the design - the way a good developer improves code they're working in.
- Don't propose unrelated refactoring. Stay focused on what serves the current goal.

## After the Design

**Documentation:**

- Write the validated design (spec) to `docs/specs/YYYY-MM-DD-<topic>-design.md`
  - (User preferences for spec location override this default)
- Use elements-of-style:writing-clearly-and-concisely skill if available
- Commit the design document to git

**Spec Review Loop:**
After writing the spec document:

1. Dispatch spec-document-reviewer subagent (see spec-document-reviewer-prompt.md)
2. If Issues Found: fix, re-dispatch, repeat until Approved
3. If loop exceeds 3 iterations, surface to human for guidance

**User Review Gate:**
After the spec review loop passes, ask the user to review the written spec before proceeding:

> "Spec written and committed to `<path>`. Please review it and let me know if you want to make any changes before we start writing out the implementation plan."

Wait for the user's response. If they request changes, make them and re-run the spec review loop. Only proceed once the user approves.

**Implementation:**

- Invoke the writing-plans skill to create a detailed implementation plan. Provide the DISTILLED spec path (not the full design) as the primary reference.
- Do NOT invoke any other skill. writing-plans is the next step.

## Spec Distillation

After the spec document is written and has passed the spec review loop, produce a **distilled spec** — a companion document that contains ONLY what an implementation agent needs.

**Why distill**: Full design specs mix definitive decisions with exploration history (options considered, rationale, rejected alternatives). An implementation agent that reads a 1347-line spec must summarize it to write a plan, introducing drift. A distilled spec of <500 lines eliminates this.

### Two-Document Model

| Document | Audience | Contains | Target Size |
|----------|----------|---------|-------------|
| `*-design.md` | Humans, brainstorming, future reference | Full decision log with alternatives, rationale, history | 500-1500 lines |
| `*-design-distilled.md` | Plan writer, implementation agents | Definitive decisions only, contract facts first | <500 lines |

The plan writer consumes the **distilled spec**, NOT the full design. The full design is retained for human reference.

### Distillation Rules

1. **Decision log -> Decision summary**: Strip "Options Considered" and "Rationale" columns. Keep only "Decision" and "Chosen" columns. Implementation agents need WHAT was decided, not WHY.

2. **Historical references removed**: Prior art, earlier designs, "we considered but rejected" text is stripped. Only the current design remains.

3. **Contract facts promoted**: Any field types, format constraints, data shapes, or invariants are moved to a "Contract Facts" section at the TOP of the distilled spec — not buried in decision rationale.

4. **Ambiguity resolved or flagged**: Anything in the original spec that was ambiguous or had multiple valid interpretations is either:
   - Resolved in the distilled version with a definitive statement, OR
   - Flagged as "OPEN DECISION — plan writer must resolve" in a visible table

5. **Component specifications preserved**: Technical details about what each component does, its inputs/outputs, and its behavior are preserved verbatim. These are implementation instructions, not exploration artifacts.

6. **Size target**: Distilled spec should be <40% of original spec line count. A 1347-line spec -> ~400-500 lines distilled.

### Distilled Spec Template

Save to: same directory as the full spec, with `-distilled` suffix.

```markdown
# [Feature Name] — Distilled Implementation Spec

> **Source**: `[path-to-full-design.md]` (v[X.Y], [N] decisions)
> **Distilled**: [date]
> **For**: Plan writer and implementation agents ONLY. For full rationale, see source.

## Contract Facts

[Field types, format constraints, data shapes, invariants — everything that is non-negotiable about external interfaces. This section is consumed by the writing-plans skill's Contract Constraints header.]

## Open Decisions

| # | Decision | Options | Resolution Required By |
|---|----------|---------|----------------------|

(Empty if all decisions are resolved)

## Decision Summary

| # | Decision | Chosen |
|---|----------|--------|
| 1 | [decision] | [chosen option] |

## Component Specifications

### [Component Name]
[What it does, inputs, outputs, behavior — preserved from full spec]

## Acceptance Criteria

- [ ] [Testable criterion from spec]
```

### Distillation Review

After producing the distilled spec, dispatch a distillation reviewer subagent (see `distillation-reviewer-prompt.md`) to verify:

1. Every definitive decision from the original spec appears in the distilled version
2. No decision was lost, inverted, or reinterpreted during distillation
3. No historical/alternative text remains (no "Options Considered", no "Rationale", no "we considered")
4. Contract facts are promoted to the top
5. Total size is under 500 lines (or under 40% of original, whichever is smaller)

Use the same dispatch pattern as the spec review loop — fix issues and re-dispatch until approved.

After the distillation reviewer approves, run the artifact checker:
```bash
bash ~/.claude/skills/superpowers/brainstorming/scripts/check-distillation.sh <distilled-spec.md>
```
This greps for exploration artifact patterns ("Options Considered", "rationale", "we considered", etc.). Fix any findings before proceeding.

## Key Principles

- **One question at a time** - Don't overwhelm with multiple questions
- **Multiple choice preferred** - Easier to answer than open-ended when possible
- **YAGNI ruthlessly** - Remove unnecessary features from all designs
- **Explore alternatives** - Always propose 2-3 approaches before settling
- **Incremental validation** - Present design, get approval before moving on
- **Be flexible** - Go back and clarify when something doesn't make sense

## Visual Companion

A browser-based companion for showing mockups, diagrams, and visual options during brainstorming. Available as a tool — not a mode. Accepting the companion means it's available for questions that benefit from visual treatment; it does NOT mean every question goes through the browser.

**Offering the companion:** When you anticipate that upcoming questions will involve visual content (mockups, layouts, diagrams), offer it once for consent:
> "Some of what we're working on might be easier to explain if I can show it to you in a web browser. I can put together mockups, diagrams, comparisons, and other visuals as we go. This feature is still new and can be token-intensive. Want to try it? (Requires opening a local URL)"

**This offer should be its own message.** Do not combine it with clarifying questions, context summaries, or any other content. The message should contain ONLY the offer above and nothing else. Wait for the user's response before continuing. If they decline, proceed with text-only brainstorming.

**Per-question decision:** Even after the user accepts, decide FOR EACH QUESTION whether to use the browser or the terminal. The test: **would the user understand this better by seeing it than reading it?**

- **Use the browser** for content that IS visual — mockups, wireframes, layout comparisons, architecture diagrams, side-by-side visual designs
- **Use the terminal** for content that is text — requirements questions, conceptual choices, tradeoff lists, A/B/C/D text options, scope decisions

A question about a UI topic is not automatically a visual question. "What does personality mean in this context?" is a conceptual question — use the terminal. "Which wizard layout works better?" is a visual question — use the browser.

If they agree to the companion, read the detailed guide before proceeding:
`skills/brainstorming/visual-companion.md`
