# CSO Description Audit Report — Superpowers Skills

**Audit date:** 2026-03-23
**Standard applied:** Description = "When to Use", NOT "What the Skill Does"
**Rule:** Descriptions must start with "Use when..." (or equivalent trigger phrase) and describe triggering conditions only. They must NOT summarize the workflow or describe what the skill produces.

---

## Per-Skill Audit

### brainstorming
**Current:** `You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation. Produces a distilled spec for implementation agents.`
**Length:** 226 chars
**Starts with trigger:** NO — starts with "You MUST use this before..."
**Describes when:** PARTIAL — lists scenarios but buries them after a command
**Summarizes workflow:** YES — "Explores user intent, requirements and design before implementation. Produces a distilled spec for implementation agents." describes what the skill does
**Verdict:** NEEDS_FIX
**Proposed fix:** `Use when starting any creative or implementation work — building features, adding functionality, modifying behavior, or designing components — before writing a spec or touching code.`

---

### dispatching-parallel-agents
**Current:** `Use when facing 2+ independent tasks that can be worked on without shared state or sequential dependencies`
**Length:** 104 chars
**Starts with trigger:** YES
**Describes when:** YES
**Summarizes workflow:** NO
**Verdict:** PASS

---

### executing-plans
**Current:** `Use when you have a written implementation plan to execute in a separate session with review checkpoints`
**Length:** 103 chars
**Starts with trigger:** YES
**Describes when:** YES — the precondition (written plan exists) and context (separate session) are triggering conditions
**Summarizes workflow:** BORDERLINE — "with review checkpoints" hints at workflow, but is brief enough to be acceptable as a qualifying detail
**Verdict:** PASS (minor — "with review checkpoints" could be trimmed)
**Proposed fix (optional):** `Use when you have a written implementation plan ready to execute in a new session`

---

### finishing-a-development-branch
**Current:** `Use when implementation is complete, all tests pass, and you need to decide how to integrate the work - guides completion of development work by presenting structured options for merge, PR, or cleanup`
**Length:** 200 chars
**Starts with trigger:** YES
**Describes when:** YES — the first clause ("implementation is complete, all tests pass, and you need to decide how to integrate") is a solid triggering condition
**Summarizes workflow:** YES — "guides completion of development work by presenting structured options for merge, PR, or cleanup" describes what the skill does
**Verdict:** NEEDS_FIX
**Proposed fix:** `Use when implementation is complete, all tests pass, and you need to decide how to integrate the work (merge, PR, or cleanup)`

---

### handoff-acceptance
**Current:** `Verify external handoff packages before consumption. Use when receiving code, schemas, or documentation from another agent, team, or system that will feed into brainstorming, planning, or implementation.`
**Length:** 204 chars
**Starts with trigger:** NO — starts with an imperative action sentence ("Verify external handoff packages before consumption") before the trigger phrase
**Describes when:** YES — the "Use when..." clause is clear
**Summarizes workflow:** YES — "Verify external handoff packages before consumption" is a workflow summary prepended before the trigger
**Verdict:** NEEDS_FIX
**Proposed fix:** `Use when receiving code, schemas, or documentation from another agent, team, or system that will feed into brainstorming, planning, or implementation`

---

### receiving-code-review
**Current:** `Use when receiving code review feedback, before implementing suggestions, especially if feedback seems unclear or technically questionable - requires technical rigor and verification, not performative agreement or blind implementation`
**Length:** 231 chars
**Starts with trigger:** YES
**Describes when:** YES — "receiving code review feedback, before implementing suggestions" is a clear condition; the qualifier "especially if feedback seems unclear or technically questionable" adds nuance
**Summarizes workflow:** YES — "requires technical rigor and verification, not performative agreement or blind implementation" describes behavior expected of the skill
**Verdict:** NEEDS_FIX
**Proposed fix:** `Use when receiving code review feedback and about to implement suggestions, especially when feedback is unclear, seems technically questionable, or conflicts with your understanding`

---

### requesting-code-review
**Current:** `Use when completing tasks, implementing major features, or before merging to verify work meets requirements`
**Length:** 104 chars
**Starts with trigger:** YES
**Describes when:** YES
**Summarizes workflow:** NO
**Verdict:** PASS

---

### subagent-driven-development
**Current:** `Orchestrates implementation plans by dispatching a fresh subagent per task with two-stage review (spec compliance + code quality) after each. Use when executing a plan with independent tasks in the current session.`
**Length:** 215 chars
**Starts with trigger:** NO — starts with a workflow summary sentence before the trigger phrase
**Describes when:** YES — the "Use when..." clause at the end is clear
**Summarizes workflow:** YES — the first sentence ("Orchestrates implementation plans by dispatching a fresh subagent per task with two-stage review...") fully describes the workflow
**Verdict:** NEEDS_FIX
**Proposed fix:** `Use when executing an implementation plan that has independent tasks and you want each task handled by a dedicated subagent with post-task review in the current session`

---

### systematic-debugging
**Current:** `Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes`
**Length:** 91 chars
**Starts with trigger:** YES
**Describes when:** YES
**Summarizes workflow:** NO
**Verdict:** PASS

---

### test-driven-development
**Current:** `Use when implementing any feature or bugfix, before writing implementation code`
**Length:** 78 chars
**Starts with trigger:** YES
**Describes when:** YES
**Summarizes workflow:** NO
**Verdict:** PASS

---

### using-git-worktrees
**Current:** `Use when starting feature work that needs isolation from current workspace or before executing implementation plans - creates isolated git worktrees with smart directory selection and safety verification`
**Length:** 199 chars
**Starts with trigger:** YES
**Describes when:** YES — the triggering conditions are clear
**Summarizes workflow:** YES — "creates isolated git worktrees with smart directory selection and safety verification" describes what the skill does
**Verdict:** NEEDS_FIX
**Proposed fix:** `Use when starting feature work that needs isolation from the current workspace, or before executing implementation plans in a dedicated directory`

---

### using-superpowers
**Current:** `Use when starting any conversation - establishes how to find and use skills, requiring Skill tool invocation before ANY response including clarifying questions`
**Length:** 159 chars
**Starts with trigger:** YES
**Describes when:** YES — "starting any conversation" is the trigger
**Summarizes workflow:** YES — "establishes how to find and use skills, requiring Skill tool invocation before ANY response including clarifying questions" describes the skill's behavior
**Verdict:** NEEDS_FIX
**Proposed fix:** `Use when starting any conversation, before responding to any request including clarifying questions`

---

### verification-before-completion
**Current:** `Use when about to claim work is complete, fixed, or passing, before committing or creating PRs - requires running verification commands and confirming output before making any success claims; evidence before assertions always`
**Length:** 225 chars
**Starts with trigger:** YES
**Describes when:** YES — "about to claim work is complete, fixed, or passing, before committing or creating PRs" is a precise triggering condition
**Summarizes workflow:** YES — "requires running verification commands and confirming output before making any success claims; evidence before assertions always" describes the skill's enforcement behavior
**Verdict:** NEEDS_FIX
**Proposed fix:** `Use when about to claim work is complete, fixed, or passing, before committing or creating PRs`

---

### writing-plans
**Current:** `Use when you have a spec or requirements for a multi-step task, before touching code. Supports modular plans for large features.`
**Length:** 129 chars
**Starts with trigger:** YES
**Describes when:** YES — the precondition (spec or requirements exist, multi-step task) is the trigger
**Summarizes workflow:** BORDERLINE — "Supports modular plans for large features" hints at capability, but reads more as a qualifying note about scope than a workflow summary
**Verdict:** NEEDS_FIX (minor)
**Proposed fix:** `Use when you have a spec or requirements for a multi-step task, before touching code`

---

### writing-skills
**Current:** `Use when creating new skills, editing existing skills, or verifying skills work before deployment`
**Length:** 97 chars
**Starts with trigger:** YES
**Describes when:** YES
**Summarizes workflow:** NO
**Verdict:** PASS

---

## Summary Table

| Skill | Length | Starts w/ Trigger | Describes When | Summarizes Workflow | Verdict |
|---|---|---|---|---|---|
| brainstorming | 226 | NO | PARTIAL | YES | NEEDS_FIX |
| dispatching-parallel-agents | 104 | YES | YES | NO | PASS |
| executing-plans | 103 | YES | YES | BORDERLINE | PASS |
| finishing-a-development-branch | 200 | YES | YES | YES | NEEDS_FIX |
| handoff-acceptance | 204 | NO | YES | YES | NEEDS_FIX |
| receiving-code-review | 231 | YES | YES | YES | NEEDS_FIX |
| requesting-code-review | 104 | YES | YES | NO | PASS |
| subagent-driven-development | 215 | NO | YES | YES | NEEDS_FIX |
| systematic-debugging | 91 | YES | YES | NO | PASS |
| test-driven-development | 78 | YES | YES | NO | PASS |
| using-git-worktrees | 199 | YES | YES | YES | NEEDS_FIX |
| using-superpowers | 159 | YES | YES | YES | NEEDS_FIX |
| verification-before-completion | 225 | YES | YES | YES | NEEDS_FIX |
| writing-plans | 129 | YES | YES | BORDERLINE | NEEDS_FIX |
| writing-skills | 97 | YES | YES | NO | PASS |

**PASS: 6 / 15**
**NEEDS_FIX: 9 / 15**

---

## Overall Assessment

The majority of skill descriptions (9 of 15) violate the CSO rule in some way. The violations cluster into three patterns:

**Pattern A — Workflow sentence prepended before trigger (3 skills):** `brainstorming`, `handoff-acceptance`, `subagent-driven-development`. These place a description of what the skill does *before* the "Use when..." clause. The fix is straightforward: delete the prepended sentence.

**Pattern B — Workflow clause appended after trigger with a dash (5 skills):** `finishing-a-development-branch`, `receiving-code-review`, `using-git-worktrees`, `using-superpowers`, `verification-before-completion`. These start correctly with "Use when..." but append a second clause after a dash that describes the skill's behavior or mechanism. The fix is to truncate at the dash.

**Pattern C — Minor capability note appended (1 skill):** `writing-plans` appends "Supports modular plans for large features." This is lower severity but still deviates from pure triggering-condition language.

**No length violations:** All descriptions are well under the 1024-character limit.

**Trigger language quality:** The 6 passing skills demonstrate the right pattern — a single clause starting with "Use when" that states the observable situation prompting invocation, with no trailing workflow description. `systematic-debugging` (91 chars) and `test-driven-development` (78 chars) are the clearest exemplars.

**Triggering reliability:** The violations in Pattern A are the most consequential for correct auto-invocation. When the description opens with a workflow summary, Claude must parse past it to find the actual trigger condition, increasing the chance the skill is missed in implicit scenarios. The "Use when..." clause should always come first.
