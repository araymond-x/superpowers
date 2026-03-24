# Thinking Guidance Assessment — Superpowers Skills

**Audit date:** 2026-03-23
**Standard applied:** Anthropic prompting best practices — "Thinking and Reasoning" section
**Key reference:** `docs/prompting-best-practices.md` — "Overthinking and excessive thoroughness" and "Leverage thinking and interleaved thinking capabilities" sections.
**Prior phases:** All 5 prior area reports reviewed and applied as baseline.

---

## Reference: Key Guidance from Best Practices Doc

**Claude Opus 4.6 does significantly more upfront exploration.** At higher effort settings, it may gather extensive context or pursue multiple threads without prompting. Skills that previously used "Default to [tool]" or "If in doubt, use [tool]" language should be tuned down.

**Canonical constrain-thinking snippet:**
```
When you're deciding how to approach a problem, choose an approach and commit to it. Avoid
revisiting decisions unless you encounter new information that directly contradicts your
reasoning. If you're weighing two approaches, pick one and see it through.
```

**Canonical encourage-reflection snippet:**
```
After receiving tool results, carefully reflect on their quality and determine optimal next
steps before proceeding.
```

**Interaction with user effort settings:** Skills cannot set `effort` directly — that is an API parameter. Skill-level thinking guidance shapes Claude's behavior within whatever effort the user has set. Guidance that says "constrain exploration" will reduce exploration at a given effort level but will not override a user who sets `effort: high`. This is appropriate: skill guidance should be a soft steer, not an API override.

**Skill-level vs. user-level conflict rule:** Thinking guidance in skills should complement the task's natural scope, not fight the user's intent. If a user has engaged fast mode (`effort: low`), skills that encourage deep reflection add friction. If a user has engaged normal mode, constraining guidance prevents runaway exploration. The guiding principle: match guidance intensity to the task's failure mode.

- **Complex reasoning tasks** (debugging, design, planning) — benefit from "pause and reflect" guidance; without it, Opus 4.6 may jump to conclusions before gathering enough signal.
- **Procedural execution tasks** (executing plans, running verifications) — benefit from "choose and commit" guidance; without it, Opus 4.6 may over-explore when it should just follow steps.
- **Simple coordination tasks** (dispatch stubs, skill meta-skills) — thinking guidance is not applicable; the task is mechanical.

---

## Summary Table

| Skill | Action | Type | Rationale |
|-------|--------|------|-----------|
| systematic-debugging | ADD | Encourage reflection after tool results | Root cause investigation requires gathering evidence before committing to a hypothesis — Opus 4.6 may skip ahead |
| brainstorming | ADD | Constrain exploration + commit to approach | Scope decomposition and approach selection are decision points where over-exploration leads to premature closure or endless questioning |
| writing-plans | ADD | Encourage reflection on codebase reads | Plan quality depends on accurately modeling the codebase; early commitment without enough reads causes wrong file paths and missed dependencies |
| subagent-driven-development | ADD | Constrain between-task exploration | Controller context is precious; Opus 4.6 tendency to explore before acting can burn context between tasks |
| handoff-acceptance | ADD | Encourage reflection after each checklist section | Each blocking check requires judgment about whether a finding is truly blocking; reflection before verdict prevents both over-blocking and under-blocking |
| receiving-code-review | ADD | Encourage reflection before verdict | The evaluation phase (step 4 in the Response Pattern) requires assessing technical soundness against the codebase — reflection before responding prevents sycophantic or reflexively defensive replies |
| writing-plans | ADD | Commit-to-approach at task decomposition | Once file ownership and task boundaries are set, Opus 4.6 should not keep second-guessing them mid-plan |
| executing-plans | ADD | Constrain exploration — follow steps, don't explore | Opus 4.6 may read additional context files beyond what the plan specifies; this skill is execution-mode, not research-mode |
| dispatching-parallel-agents | ADD | Constrain domain identification | Agent domain boundaries should be identified quickly; over-analysis of whether failures are truly independent delays dispatch |
| verification-before-completion | NOT APPLICABLE | — | Purely procedural gate function; steps are mechanical (run command, read output). Thinking guidance does not change this. |
| finishing-a-development-branch | NOT APPLICABLE | — | Decision tree is structural (4 fixed options); no complex reasoning is involved |
| requesting-code-review | NOT APPLICABLE | — | Procedural: invoke reviewer, read output, categorize findings. No ambiguous judgment required. |
| using-git-worktrees | NOT APPLICABLE | — | Setup procedure with deterministic steps; reflection guidance would add noise |
| using-superpowers | NOT APPLICABLE | — | Meta-skill about skill invocation; the decision to invoke is binary, not exploratory |
| handoff-acceptance | ADD | See above | — |
| test-driven-development | ADD | Constrain at RED phase | Opus 4.6 may over-engineer the test case before seeing it fail; "write the minimal failing test and run it" keeps RED phase tight |
| writing-skills | NOT APPLICABLE | — | The skill is itself about writing structured content; meta-thinking guidance would be recursive and confusing |

---

## Detailed Proposals

### 1. systematic-debugging

**Why guidance helps:** Systematic debugging is the skill most at risk from Opus 4.6's upfront exploration tendency. The entire skill is structured to prevent premature hypothesis formation — its Iron Law ("no fixes without root cause investigation first") is a direct constraint on rushing. But Opus 4.6's exploration instinct means it may ALSO over-explore: reading file after file without committing to a hypothesis, or revisiting Phase 1 after already forming a hypothesis in Phase 3.

Two distinct guidance needs:

**ADD: Encourage reflection after each phase's evidence gathering**

Placement: After the Phase 1 "Gather Evidence in Multi-Component Systems" subsection (line ~87 in the current file).

```
After running diagnostic instrumentation and gathering evidence, pause before moving to
Phase 2. Ask: Do I know which component boundary is failing? If yes, proceed. If not,
identify what additional evidence is needed — then gather only that before moving on.
```

**ADD: Commit-to-hypothesis guidance at Phase 3**

Placement: Before or within the "Form Single Hypothesis" step in Phase 3.

```
State your hypothesis before testing it. Once stated, commit to testing it fully before
reconsidering. If the hypothesis is wrong, revise based on new evidence — not before.
```

**Rationale vs. prior phases:** Area 1 flagged "ALWAYS" and "Violating the spirit" as over-intensity. This guidance is additive — it shapes exploration behavior at the right moments (after evidence gathering, before hypothesis formation) rather than shouting general compliance. Area 2's positive-framing improvements apply in parallel.

---

### 2. brainstorming (v0.1)

**Why guidance helps:** Brainstorming is a naturally open-ended skill where Opus 4.6's thorough exploration is both an asset and a risk. The asset: more thorough context exploration leads to better designs. The risk: excessive questioning, over-engineering approaches, or failing to commit when enough information has been gathered.

Two distinct guidance needs:

**ADD: Constrain exploration during the clarifying questions phase**

Placement: In the "Asking clarifying questions" section of The Process, after the current guidance about asking one question at a time.

```
After 3-4 clarifying questions, assess whether you have enough to propose approaches. You
do not need complete information to propose — you need enough to identify the main trade-off.
Choose your leading approach based on what you know and propose it. Gaps can be filled
during design review.
```

**ADD: Commit-to-design guidance before writing the design doc**

Placement: In the "Presenting the design" section, before the "Write design doc" step.

```
Once the user has approved the design direction, commit to it. Write the spec from the
approved design — do not re-open architectural questions during the writing phase. If a
new concern emerges while writing, note it as a decision to surface after the spec is
written, not a reason to restart the design.
```

**Rationale:** Brainstorming has a CRITICAL CONSTRAINT gate against implementation, and Area 1 assessed that gate as warranted. The thinking guidance proposed here operates in a different dimension: it shapes how Claude manages the open-ended exploration phase before reaching the gate. These are compatible concerns. The constraint gate prevents premature implementation; the thinking guidance prevents premature closure (too-quick approach selection) AND prevents endless exploration (never committing to a design).

**Interaction with user effort:** A user in fast mode may want to skip the extended questioning. The guidance here uses "3-4 questions" as a soft checkpoint, not a hard cutoff — it is compatible with low-effort sessions where fewer questions are appropriate.

---

### 3. writing-plans (v0.1)

**Why guidance helps:** Writing a plan requires reading the codebase to understand existing patterns, file locations, and dependencies. Opus 4.6's upfront exploration tendency can manifest as reading too many files (burning context before writing a single task) or too few (committing to file paths based on assumptions). Both are costly: too many reads delays the plan and may exhaust context; too few reads produces wrong paths that cause subagent failures.

**ADD: Reflect-then-commit during codebase exploration**

Placement: Near the beginning of the plan writing process, before the "Write the tasks" section.

```
Before writing tasks, read the core files your plan will modify. After each read, assess
whether you now understand the relevant interfaces, naming conventions, and file ownership.
When you can answer "where does this logic live and what does it touch?" for each task
in the plan, you have enough context. Do not read more files beyond that — write from
what you know.
```

**ADD: Commit-to-task-boundaries once partitioning is done**

Placement: After the Write-Scope Partitioning section guidance.

```
Once you have written the Write-Scope Partitioning table, treat task ownership as settled.
Do not revise file assignments mid-plan — if a conflict is discovered later, add a
serialization dependency rather than re-partitioning.
```

**Rationale:** Area 3 flagged the "exact file paths always" rule as unmotivated. The thinking guidance proposed here provides the behavioral complement: it explains why Claude should commit to file paths after reading core files, rather than continually second-guessing them. These work together.

---

### 4. subagent-driven-development (v0.1)

**Why guidance helps:** The controller session in SDD has two competing failure modes that Opus 4.6's increased exploration tendency can amplify:

1. **Over-exploration before dispatch:** Reading additional files or context beyond the plan before dispatching the first task.
2. **Over-analysis between tasks:** Re-reading review results multiple times, exploring the codebase between tasks, or second-guessing task boundaries.

The controller's context is finite and precious — unnecessary reads burn it.

**ADD: Constrain pre-dispatch exploration**

Placement: In the Plan Ingestion section, after the read-all-sections instruction.

```
Plan ingestion is a one-pass activity. Read the plan, read the source contracts if present,
extract what you need — then start the task loop. Do not read additional codebase files
beyond what the plan's Contract Constraints reference. Your job in this phase is to
understand the plan, not to verify it against the codebase.
```

**ADD: Commit-and-proceed after each task review**

Placement: In the task loop section, after the two-stage review description.

```
After spec compliance and code quality reviews both pass, mark the task complete and move
to the next one. Do not re-examine completed task output or re-read implementation files
between tasks — the review is the completion gate. Looking at completed work is exploration,
not progress.
```

**Rationale:** Area 1 flagged the Review Enforcement section's intensity. The thinking guidance proposed here does not change what is required (reviews must happen, task must pass both stages) — it shapes WHEN to stop thinking and start executing. These are compatible. The de-escalation work operates on how rules are stated; this guidance operates on exploration behavior between rule applications.

---

### 5. handoff-acceptance

**Why guidance helps:** Each blocking check requires a judgment call: is this package actually failing the check, or is it technically compliant in an unusual way? Opus 4.6 may over-explore (reading all referenced code before reaching a verdict on check #1) or under-think (rubber-stamping each check without careful evaluation). The per-check structure of this skill is already good; thinking guidance at the right junctures adds the reflection prompt.

**ADD: Reflect after each blocking check before recording verdict**

Placement: As a general instruction after the Acceptance Checklist intro, before the numbered checks.

```
For each blocking check, read the relevant section of the handoff, then pause before
recording your verdict. Ask: If I were an implementer consuming this handoff tomorrow,
would this gap cause me to write wrong code? If yes, it is blocking. If the gap is
present but would not change the implementation, note it as recommended — not blocking.
```

**Rationale:** Handoff-acceptance already has the best motivation density of any skill (Area 3 finding). The thinking guidance is a behavioral complement: it shapes the quality of judgment at each check, not the structure of the checklist. Area 2 found no significant positive-framing gaps here; this is additive only.

---

### 6. receiving-code-review

**Why guidance helps:** The Response Pattern in this skill has a distinct EVALUATE step (step 4: "Technically sound for THIS codebase?") that requires genuine assessment against the actual codebase, not just the reviewer's claim. Opus 4.6's increased instruction-following can manifest as reflexive implementation ("reviewer said it, I'll do it") OR reflexive rejection ("I know better"). Both bypass the evaluation step.

**ADD: Reflect before responding to feedback**

Placement: In The Response Pattern section, near steps 3-4 (VERIFY/EVALUATE).

```
Before writing your response, pause to evaluate the feedback technically. Is the reviewer
correct given the actual codebase patterns? Is there a case where the reviewer is right
in principle but wrong for this specific context? Commit to a position — agree, push back
with reasoning, or ask a clarifying question — before typing your response. Do not respond
with "I'll implement that" before reaching your own verdict.
```

**Rationale:** Area 2 proposed rewriting the Forbidden Responses section to lead with "Do" rather than "NEVER." The thinking guidance here operates at a higher level — it shapes the evaluation behavior that determines which response pattern is appropriate. Area 2 tells Claude what to say; this guidance shapes how Claude reaches the decision about what to say.

---

### 7. test-driven-development

**Why guidance helps:** The RED phase is where Opus 4.6's thoroughness most risks the TDD cycle. "Write a failing test" can trigger exploration: reading existing test patterns, examining what tests already exist, considering all edge cases before writing the first assertion. The RED phase should be minimal and fast — the test should be the simplest possible statement of the intended behavior.

**ADD: Constrain RED phase test writing**

Placement: In the RED phase instructions, before or after the "Write failing test" step.

```
Write the simplest test that captures the intended behavior — not the most comprehensive
test. One assertion is often correct for the RED step. If you find yourself planning
multiple test cases before running the first one, stop: write the first test, run it,
confirm it fails for the right reason, then proceed to GREEN. You can add more test
cases in subsequent RED-GREEN cycles.
```

**Rationale:** Area 1 flagged "MANDATORY. Never skip." in the RED verification step as overblown. The thinking guidance here addresses the upstream issue: it prevents the situation where Claude writes such an elaborate test case that it becomes unclear what the test is asserting. A minimal RED test is easier to verify for the right failure reason. These are compatible improvements.

---

## What Was Assessed as NOT APPLICABLE

### verification-before-completion

This skill is a purely mechanical gate function: identify the verification command, run it, read the output, make the claim. There is no ambiguity in how to proceed — each step has one correct action. Thinking guidance would not change the behavior. The skill's existing structure (numbered steps, explicit "if NO / if YES" branching) already encodes the procedural correctness without leaving room for exploration.

### finishing-a-development-branch

The decision tree in this skill is structural: four options, one chosen based on what the human wants to do. No complex judgment is required — Claude presents the options, receives a choice, executes it. Reflection guidance would add noise to what is a simple interaction protocol.

### requesting-code-review

This is an invocation skill: invoke the code reviewer, receive its output, triage findings by severity. The triage categories (Critical/Important/Minor) are defined in the skill. Exploration is not a failure mode here.

### using-git-worktrees

Setup procedure with deterministic steps. The only decision point (whether the worktree directory is in .gitignore) has a binary answer resolved by running a command.

### using-superpowers

The decision to invoke a skill is binary (does a skill apply?). The skill already addresses this decision pattern directly. Adding thinking guidance to a skill about skill-invocation would be recursive and confusing.

### writing-skills

This skill instructs Claude how to write structured content following TDD principles. The task is inherently structured and sequential. Thinking guidance would not meaningfully change how the RED-GREEN-REFACTOR cycle is applied to skill writing.

### dispatching-parallel-agents

Mild candidate (domain boundary identification could benefit from "commit after initial analysis"), but the skill's when-to-use decision tree already handles the main failure mode. The three criteria (independent? no shared state? can work in parallel?) are explicit enough that over-analysis is unlikely to be a common problem. Leaving as NOT APPLICABLE, with low-priority consideration noted.

---

## Implementation Priority

| Priority | Skill | Guidance Type | Value |
|----------|-------|---------------|-------|
| 1 | systematic-debugging | Reflect post-evidence + commit hypothesis | Directly prevents the core failure mode (premature hypothesis, or endless re-investigation) |
| 2 | subagent-driven-development | Constrain pre-dispatch + between-task exploration | Controller context is finite; exploration between tasks is expensive |
| 3 | brainstorming | Constrain clarifying questions + commit to design | Prevents both under-commitment (endless questions) and premature commitment (jumping to approaches) |
| 4 | writing-plans | Reflect during codebase reads + commit to partitioning | Wrong file paths are the most common plan failure; early commit prevents re-partitioning |
| 5 | test-driven-development | Constrain RED phase | Prevents over-engineered test setup before seeing a failure |
| 6 | receiving-code-review | Reflect before verdict | Prevents reflex implementation or reflex rejection |
| 7 | handoff-acceptance | Reflect before each check verdict | Prevents rubber-stamping or over-blocking |

---

## Relationship to Prior Phase Reports

**Area 1 (De-escalation):** The de-escalation work reduces intensity of existing constraints. This area's thinking guidance additions are new content — they do not modify existing constraint language. No conflicts.

**Area 2 (Positive framing):** This area proposed changing "Never" lists to "Required practices." Thinking guidance operates at a higher level — it shapes exploration behavior before rules apply, not the rules themselves. No conflicts.

**Area 3 (Motivation):** Several Area 3 motivation additions explain WHY a rule exists. The thinking guidance here explains WHEN to stop exploring and commit. These are complementary — motivation gives Claude reason to follow the rule; thinking guidance gives Claude a behavioral cue for when "following the rule" means stopping and acting.

**Area 5 (XML tags):** Thinking guidance snippets proposed here use plain prose, not XML tags. If the implementer chooses to wrap them in tags for structural clarity (e.g., `<thinking-guidance>`), that would be new tag vocabulary requiring the naming convention (`<thinking-guidance>` in lowercase-with-hyphens) per Area 5's standard.

**Area 7 (CSO descriptions):** No interaction. Thinking guidance is internal to skill body content, not the frontmatter description.

**Area 8 (Role identity):** Role statements prime behavioral disposition. Thinking guidance shapes mid-task behavior. For systematic-debugging and brainstorming specifically, a role statement that reads "You are a methodical investigator" would naturally amplify the thinking guidance's effect — the identity reinforces the reflection pause. Implementer should consider coordinating role statement additions (if any are proposed for skill files rather than prompt templates) with thinking guidance placement.

---

## Cross-Skill Pattern

A repeating pattern across skills worth noting: most Superpowers skills have well-defined **entry points** (when to use, how to start) and well-defined **exit points** (gates, checklists) but under-specified **decision points** in the middle — moments where Claude must assess whether it has enough information to proceed or needs more. Opus 4.6's default behavior at these decision points is to gather more. Thinking guidance fills this gap by naming these mid-skill decision points explicitly and giving Claude a behavioral cue ("do you have enough to proceed? if yes, proceed; if not, identify exactly what's missing and gather only that").

This pattern suggests a reusable guidance template for any future skill:

```
After [gathering-activity], assess whether you have enough to [next-step]. If yes, proceed.
If not, identify the specific gap and address only that before continuing.
```

This template is more useful than a blanket "don't over-explore" instruction because it ties the constraint to a specific decision point, making it actionable rather than atmospheric.
