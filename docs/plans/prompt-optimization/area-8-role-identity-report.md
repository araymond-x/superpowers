# Role Identity Audit Report — Subagent Prompt Templates

**Audit date:** 2026-03-23
**Reference:** `docs/prompting-best-practices.md` — "Give Claude a role" section
**Key finding from best practices:** "Setting a role in the system prompt focuses Claude's behavior and tone. Even a single sentence makes a difference."
**Subagent context note:** Each subagent starts with zero session history. A role statement does more work here than in any continuing conversation — it is the only prior context the model has before reading its task.

---

## Summary Table

| Template | Has Role | Current Approach | Role Quality |
|----------|----------|-----------------|--------------|
| implementer-prompt-v0.1.md | PARTIAL | Task framing with implicit persona | Weak — describes action, not identity |
| spec-reviewer-prompt-v0.1.md | PARTIAL | Task framing with skepticism cue | Weak — describes the review act, not the reviewer |
| code-quality-reviewer-prompt-v0.1.md | NO | Dispatch stub only | N/A — no prompt text to open |
| agents/code-reviewer.md | YES | Strong role statement | Good — explicit seniority and expertise |
| distillation-reviewer-prompt.md | PARTIAL | Task framing only | Weak — states the verification task, not a reviewer persona |
| spec-document-reviewer-prompt.md | PARTIAL | Job title inline | Weak — "You are a spec document reviewer" is generic |
| plan-document-reviewer-prompt-v0.1.md | PARTIAL | Job title inline | Weak — "You are a plan document reviewer" is generic |

---

## Per-Template Analysis

### implementer-prompt-v0.1.md

**Current opening:**
```
You are implementing Task N: [task name]
```

**Has role:** NO (PARTIAL at best)

**Current approach:** TASK-ONLY. The opening names the specific task being executed. This establishes what the agent is doing, not who it is or what behavioral disposition to bring. The identity — disciplined, scope-bounded implementer — is implicit in the constraint language that follows, but never stated up front.

**Why it matters here:** A fresh subagent reading "You are implementing Task N" receives no framing about how to approach ambiguity, how strictly to follow spec vs. exercise judgment, or what the expected professional standard is. The constraint sections (CLAUDE.md, Source Files, Self-Review) compensate for this, but they arrive many paragraphs later. An early role statement primes the model before those sections load.

**Proposed role statement:**
> You are a focused implementation engineer. Your job is to build exactly what the spec asks — nothing more, nothing less. When requirements are clear, execute them precisely. When they are ambiguous, ask before assuming.

**Redundancy check:** This role statement encodes the YAGNI and ask-before-assuming principles that appear later in "Your Job" and "When You're in Over Your Head." Adding the role does NOT make those sections redundant — the later sections are procedural instructions with specific escalation steps. The role statement is the disposition; the procedural sections are the mechanics. Both should stay.

**Before/After of opening section:**

Before:
```
You are implementing Task N: [task name]

## Task Description
```

After:
```
You are a focused implementation engineer. Your job is to build exactly what the
spec asks — nothing more, nothing less. When requirements are clear, execute them
precisely. When they are ambiguous, ask before assuming.

You are implementing Task N: [task name]

## Task Description
```

---

### spec-reviewer-prompt-v0.1.md

**Current opening:**
```
You are reviewing whether an implementation matches its specification.
```

**Has role:** NO (PARTIAL)

**Current approach:** TASK-ONLY. States the verification act but assigns no professional identity or behavioral disposition. The skepticism that defines this reviewer's value is introduced four paragraphs later in the "CRITICAL: Do Not Trust the Report" block, not at the opening.

**Why it matters here:** The spec reviewer's defining behavioral trait — healthy skepticism toward implementer reports — is currently delayed. A fresh subagent that reads "You are reviewing whether an implementation matches its specification" has no reason to start skeptically. The "Do Not Trust the Report" section does heavy lifting to establish this, but by then the model has already formed an initial frame. A role statement at the top primes the skeptical auditor disposition before any task content loads.

**Proposed role statement:**
> You are a skeptical spec compliance auditor. Your value comes from verifying by reading code, not by accepting reports. Assume the implementer's report is incomplete until the code proves otherwise.

**Redundancy check:** The "CRITICAL: Do Not Trust the Report" section contains detailed DO/DO NOT lists that remain fully necessary — they give actionable instructions. The role statement above is the identity behind those instructions. Neither makes the other redundant.

**Before/After of opening section:**

Before:
```
You are reviewing whether an implementation matches its specification.

## What Was Requested
```

After:
```
You are a skeptical spec compliance auditor. Your value comes from verifying by
reading code, not by accepting reports. Assume the implementer's report is
incomplete until the code proves otherwise.

You are reviewing whether an implementation matches its specification.

## What Was Requested
```

---

### code-quality-reviewer-prompt-v0.1.md

**Current opening:**
```
Task tool (superpowers-code-reviewer):
  Use template at requesting-code-review/code-reviewer.md
```

**Has role:** NO

**Current approach:** This is a dispatch stub, not a direct prompt template. It tells the controller how to invoke the `superpowers-code-reviewer` agent rather than containing a prompt text itself. The actual role statement lives in `agents/code-reviewer.md`.

**Implication:** No role statement needs to be added here — but the additional checks appended in the stub (dead code, contract compliance, file responsibility) are injected via the `IMPLEMENTER_REPORT` parameter and the supplemental bullet list. Those bullets do not currently open with a role statement either; they are a list of "also check" items.

**Proposed change:** None to this file directly. The behavioral identity for this reviewer is owned by `agents/code-reviewer.md`. If that agent's role is strengthened (see below), the v0.1 stub inherits the improvement.

**Redundancy check:** N/A — no opening prompt text in this file.

---

### agents/code-reviewer.md

**Current opening:**
```
You are a Senior Code Reviewer with expertise in software architecture, design
patterns, and best practices. Your role is to review completed project steps
against original plans and ensure code quality standards are met.
```

**Has role:** YES

**Current approach:** ROLE. This is the strongest role statement of all audited templates. It establishes seniority ("Senior"), domain ("software architecture, design patterns, best practices"), and mission ("review completed project steps against original plans"). The opening is followed immediately by structured behavioral sections (Plan Alignment, Code Quality, Architecture, etc.).

**Assessment:** This template already follows the best practice. The role statement is specific, behavioral, and places the reviewer in a professional context before any task detail.

**Proposed role statement:** No change needed. The existing opening is a well-formed role statement.

**Minor observation:** The proposed role in the audit plan was "Experienced code reviewer — focused on maintainability, test quality, clean architecture." The existing statement already exceeds this: "Senior Code Reviewer with expertise in software architecture, design patterns, and best practices" is more specific and establishes higher seniority. No regression needed.

**Redundancy check:** The role statement does not make any of the numbered behavioral sections redundant. Those sections translate the role into concrete review actions.

---

### distillation-reviewer-prompt.md

**Current opening:**
```
You are verifying that a distilled spec accurately represents the decisions
from a full design document.
```

**Has role:** NO (PARTIAL)

**Current approach:** TASK-ONLY. States the verification objective but establishes no professional identity. The word "verifying" implies care, but not the specific disposition needed here: a precision editor who catches fidelity losses without re-litigating the decisions that were made. Without that framing, a fresh subagent may drift toward suggesting improvements to the underlying decisions rather than checking whether the distillation faithfully preserved them.

**Why it matters here:** The distillation reviewer has a narrow, specific job: check fidelity, not quality. That constraint is not obvious from the opening. The "Artifact removal" and "Decision preservation" sections establish what to look for, but the meta-instruction — "do not re-litigate decisions" — only appears in the plan's proposed role, not in the template itself.

**Proposed role statement:**
> You are a precision editor verifying distillation fidelity. Your job is to check whether decisions were preserved accurately — not to re-evaluate them. A decision you disagree with is not a finding; a decision that was lost or inverted is.

**Redundancy check:** The proposed role introduces the "do not re-litigate" constraint explicitly. This constraint does not currently appear anywhere in the template's instruction sections, so adding it via the role statement fills a gap rather than duplicating existing content.

**Before/After of opening section:**

Before:
```
You are verifying that a distilled spec accurately represents the decisions
from a full design document.

**Full design spec:** [FULL_SPEC_PATH]
```

After:
```
You are a precision editor verifying distillation fidelity. Your job is to check
whether decisions were preserved accurately — not to re-evaluate them. A decision
you disagree with is not a finding; a decision that was lost or inverted is.

You are verifying that a distilled spec accurately represents the decisions
from a full design document.

**Full design spec:** [FULL_SPEC_PATH]
```

---

### spec-document-reviewer-prompt.md

**Current opening:**
```
You are a spec document reviewer. Verify this spec is complete and ready for planning.
```

**Has role:** PARTIAL

**Current approach:** PARTIAL ROLE. "You are a spec document reviewer" is a job title without behavioral content. It names the role but does not tell the model what disposition, expertise, or standard to bring. The critical calibration instruction — "Only flag issues that would cause real problems during implementation planning" — appears three paragraphs later under the Calibration section.

**Why it matters here:** The calibration instruction is doing significant behavioral work: it tells the reviewer to be a gatekeeper for planning-readiness, not a general editor. That calibration is the defining behavioral trait of this reviewer. Front-loading it in the role statement would prime the model before it encounters the checklist, reducing the risk of over-flagging minor issues.

**Proposed role statement:**
> You are a design quality auditor evaluating whether a spec is ready for implementation planning. Your standard is planning-readiness, not perfection — flag gaps that would cause a planner to build the wrong thing, not gaps that are merely incomplete or stylistically imperfect.

**Redundancy check:** The Calibration section ("Only flag issues that would cause real problems during implementation planning") currently carries this instruction. With the role statement added, the Calibration section becomes reinforcing rather than primary. It should be kept — it adds the "Approve unless there are serious gaps" guideline which is a concrete threshold the role statement doesn't cover.

**Before/After of opening section:**

Before:
```
You are a spec document reviewer. Verify this spec is complete and ready for planning.
```

After:
```
You are a design quality auditor evaluating whether a spec is ready for implementation
planning. Your standard is planning-readiness, not perfection — flag gaps that would
cause a planner to build the wrong thing, not gaps that are merely incomplete or
stylistically imperfect.

Verify this spec is complete and ready for planning.
```

---

### plan-document-reviewer-prompt-v0.1.md

**Current opening:**
```
You are a plan document reviewer. Verify this plan is complete and ready for implementation.
```

**Has role:** PARTIAL

**Current approach:** PARTIAL ROLE. Same pattern as the spec reviewer: a job title without behavioral content. The important calibration — that type mismatches are always blocking, that the reviewer must read source contracts independently — appears in the body of the instructions, not at the opening.

**Why it matters here:** The plan reviewer has a more technical mandate than the spec reviewer: it must verify code snippets against source contracts and trace fields across documents. That technical rigor should be established at the top. A fresh subagent that reads "You are a plan document reviewer" has no reason to approach this as a technically demanding cross-reference task. The detail about a "single wrong type caused 3 production bugs" appears deep in the What to Check table — that stakes-setting context would work better as part of the role framing.

**Proposed role statement:**
> You are an implementation readiness auditor. Your job is to catch plan defects before they reach subagents — type mismatches, wrong field names, unverified code snippets, and gaps that would cause an implementer to build the wrong thing. A single type mismatch that looks minor can propagate to production bugs; treat contract accuracy as the highest-stakes check in this review.

**Redundancy check:** The "type mismatches against source contracts are ALWAYS blocking, regardless of how minor they appear" sentence in the What to Check intro currently carries the stakes framing. With the role statement introducing this context, that sentence becomes reinforcing. Keep it — it applies the standard to the specific check table entry for Contract Accuracy. The role statement is the disposition; the table entry is the specific instruction.

**Before/After of opening section:**

Before:
```
You are a plan document reviewer. Verify this plan is complete and ready for implementation.

**Plan to review:** [PLAN_FILE_PATH]
```

After:
```
You are an implementation readiness auditor. Your job is to catch plan defects before
they reach subagents — type mismatches, wrong field names, unverified code snippets,
and gaps that would cause an implementer to build the wrong thing. A single type
mismatch that looks minor can propagate to production bugs; treat contract accuracy
as the highest-stakes check in this review.

Verify this plan is complete and ready for implementation.

**Plan to review:** [PLAN_FILE_PATH]
```

---

## Cross-Template Findings

### Pattern: "You are [doing task]" vs "You are [a professional who does task]"

Five of seven templates open with task framing rather than identity framing. The distinction matters for subagents:

| Pattern | Example | Effect |
|---------|---------|--------|
| Task framing | "You are reviewing whether..." | Model understands the objective but has no identity anchor — behavioral drift is more likely |
| Identity framing | "You are a Senior Code Reviewer..." | Model has a professional persona to inhabit — expertise, standards, and dispositions are implied by the role |

The `code-reviewer.md` agent is the exemplar. Its opening does not describe the task; it describes the professional. The task follows from the identity, not the other way around.

### Pattern: Calibration delayed past the checklist preamble

In both the spec document reviewer and plan document reviewer, the most important behavioral calibration (what counts as a real issue vs. a minor one, what is always blocking) is introduced after the checklist. Role statements that incorporate this calibration at the top fix the sequencing problem without requiring restructuring of the body.

### Pattern: The distillation reviewer's "do not re-litigate" constraint is missing entirely

The proposed role for the distillation reviewer introduces a constraint — "do not re-litigate decisions" — that does not appear anywhere in the current template. This is the highest-value addition of the seven templates: it fills a behavioral gap, not just a framing gap.

---

## Priority Order for Implementation

1. **distillation-reviewer-prompt.md** — Adds a constraint that currently doesn't exist anywhere in the template ("do not re-litigate decisions"). Highest behavioral delta.
2. **spec-reviewer-prompt-v0.1.md** — Moves the skepticism framing to the opening where it primes behavior before the task content loads. Currently the "Do Not Trust the Report" block does this work but arrives late.
3. **implementer-prompt-v0.1.md** — Establishes focused, scope-bounded identity. The existing constraint sections compensate for the missing role, but an explicit identity statement at the top is cleaner.
4. **plan-document-reviewer-prompt-v0.1.md** — Replaces generic job title with stakes-aware identity. The "single wrong type caused bugs" framing belongs in the role.
5. **spec-document-reviewer-prompt.md** — Same pattern as plan reviewer; planning-readiness calibration should be in the role.
6. **agents/code-reviewer.md** — Already has a strong role statement. No change needed.
7. **code-quality-reviewer-prompt-v0.1.md** — Dispatch stub; role owned by the agent. No change needed here.
