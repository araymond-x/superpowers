# Motivation Audit Report — Superpowers Skills

**Audit date:** 2026-03-23
**Standard applied:** Anthropic prompting best practices — "Add context to improve performance"
**Key principle:** "Providing context or motivation behind your instructions... can help Claude better understand your goals and deliver more targeted responses." Motivation is especially valuable where compliance is most expensive to fail on — the motivation helps Claude generalize, not just pattern-match.

**Scope:** 15 SKILL files (v0.1 where available) + 3 prompt templates

**Methodology:** Rules are flagged only when (a) the "why" is non-obvious from context, AND (b) adding a motivation would meaningfully change how a future Claude applies or prioritizes the rule. Rules with existing motivation, rules where context makes the reason self-evident (e.g., "don't commit without tests"), and rules that are already well-explained elsewhere in the same file are not flagged.

---

## Per-File Audit

### executing-plans/SKILL.md
**Unmotivated rules found:** 5

| Rule (quoted) | Why Obvious? | Proposed Motivation |
|---------------|-------------|-------------------|
| `Never start implementation on main/master branch without explicit user consent` | Partially — the risk of polluting main is general knowledge, but the consequence in a plan-execution context (no easy rollback, mixed partial work) is not obvious | "A failed plan execution mid-stream on main leaves the repo in a partial state with no clean rollback path." |
| `Don't skip verifications` | No — it says to do them but not why they're in the plan in the first place | "Verifications in the plan are the only objective confirmation that a step produced the expected artifact — skipping them means proceeding with unverified state." |
| `Reference skills when plan says to` | No — could be misread as "ceremonial" if the reader doesn't know skills carry their own guardrails | "Skills encode additional guardrails the plan author relied on — invoking them is how those guardrails apply." |
| `Don't force through blockers — stop and ask` | Partially obvious, but reason is absent | "Forcing through a blocker in a plan means every subsequent task builds on a broken foundation — the cost of not stopping compounds with each additional task." |
| `Follow plan steps exactly` (from Remember section) | Not fully — could seem overly rigid | "Plan steps were written with full codebase context. Deviating mid-execution without consultation introduces assumptions the plan author couldn't anticipate." |

---

### finishing-a-development-branch/SKILL.md
**Unmotivated rules found:** 4

| Rule (quoted) | Why Obvious? | Proposed Motivation |
|---------------|-------------|-------------------|
| `Present exactly 4 options` | No — the count feels arbitrary without explanation | "Fewer than 4 options omits real workflows; more than 4 triggers decision paralysis. The 4 options cover every real completion path." |
| `Don't add explanation — keep options concise` | No — brevity here seems arbitrary | "At completion the human already knows what was built. Explanation restates what they know; the decision is the only new information needed." |
| `Require typed 'discard' confirmation` | Partially obvious (destructive action), but the specific "typed" requirement is not explained | "Typed confirmation prevents accidental discard from ambiguous affirmations like 'yes' or 'ok' that could be leftover from a prior question." |
| `Only cleanup worktree for Options 1 and 4` (implicit in Quick Reference table) | No — the keep/remove logic is presented as a lookup table without rationale | "Options 2 and 3 both leave the branch alive — the worktree may still be needed for additional commits or investigation after the PR is created." |

---

### dispatching-parallel-agents/SKILL.md
**Unmotivated rules found:** 2

This skill has good explanatory density overall. Two gaps:

| Rule (quoted) | Why Obvious? | Proposed Motivation |
|---------------|-------------|-------------------|
| `Constraints: Don't change other code` (in agent prompt structure section) | No — the reason this constraint must appear explicitly in every agent prompt is not stated | "Subagents have no session context. Without an explicit constraint, a subagent that needs to refactor shared code will do so, creating conflicts with other parallel agents writing to the same files." |
| `Return: Summary of what you found and fixed` (required in agent output) | No — the output format seems like a suggestion | "The controller must synthesize multiple agent results and verify no conflicts. Summaries without a consistent structure cannot be compared reliably — the controller needs each agent's scope and changes in a predictable format." |

---

### using-git-worktrees/SKILL.md
**Unmotivated rules found:** 3

| Rule (quoted) | Why Obvious? | Proposed Motivation |
|---------------|-------------|-------------------|
| `If NOT ignored: Add appropriate line to .gitignore — Commit the change` | The verify-then-commit sequence is not explained | "Committing the .gitignore update before creating the worktree ensures the worktree contents are excluded from the very first `git status` — doing it after creates a window where worktree contents appear as untracked files." |
| `Run project setup (npm install / cargo build / etc.)` after creating worktree | No — this step could be skipped as "optional setup" without understanding why it's in the process | "Worktrees share the repo but not node_modules or build artifacts. Skipping setup causes the baseline test run to fail for the wrong reason — missing dependencies rather than actual bugs." |
| `Report failures, ask whether to proceed or investigate` (when baseline tests fail) | Partially — stopping seems obvious, but asking rather than auto-stopping needs justification | "Some repos have pre-existing failures on main. The human needs to confirm whether the failures are known and safe to work around, or indicators the worktree setup is wrong." |

---

### handoff-acceptance/SKILL.md
**Unmotivated rules found:** 2

Note: This skill is already well-motivated — every BLOCKING check has a "Why" explanation. Two RECOMMENDED checks lack motivation:

| Rule (quoted) | Why Obvious? | Proposed Motivation |
|---------------|-------------|-------------------|
| `If no fixtures exist, the receiving agent must create them from the handoff's descriptions and verify they match the contract before proceeding.` | No — the receiving agent might skip this step as burdensome | "Fixtures created from descriptions are the minimum bar for verifying the handoff is internally consistent. Without them, type assumptions from the handoff propagate directly into implementation — the same failure mode the BLOCKING fixture check exists to prevent." |
| `A runnable test that loads a fixture and verifies it matches the declared contract... This is the ground-truth anchor. Without it, type assumptions are validated only by reading — reading misses errors that tests catch mechanically.` | Motivation IS present here ("ground-truth anchor"). No addition needed. | N/A |

Actually only 1 gap (the fixture-creation rule). The acceptance test rule already has motivation.

**Unmotivated rules found:** 1

---

### receiving-code-review/SKILL.md
**Unmotivated rules found:** 3

| Rule (quoted) | Why Obvious? | Proposed Motivation |
|---------------|-------------|-------------------|
| `Items may be related. Partial understanding = wrong implementation.` | Motivation IS present inline (`WHY:` tag). No addition needed. | N/A |
| `Push back with technical reasoning, not defensiveness` | No motivation for why the form of pushback matters | "Defensive pushback triggers the human to defend their feedback rather than evaluate the technical argument. Framing as a technical question opens the door to 'you're right, I missed that.' " |
| `Reply in the comment thread..., not as a top-level PR comment` (GitHub Thread Replies) | No — this rule has no explanation and could seem like arbitrary style | "Top-level PR comments appear as general comments, not threaded replies — reviewers lose the inline context of which line triggered the response." |

---

### requesting-code-review/SKILL.md
**Unmotivated rules found:** 2

| Rule (quoted) | Why Obvious? | Proposed Motivation |
|---------------|-------------|-------------------|
| `Never: Skip review because "it's simple"` | Partially — the pattern is named but not explained | " 'Simple' tasks are where assumptions go unexamined. The statement-reconciliation incident traced 3 production bugs to tasks that seemed simple — the simplicity was why no one looked carefully." (Incident reference from lessons-learned doc.) |
| `Fix Critical issues immediately / Fix Important issues before proceeding / Note Minor issues for later` | The triage priority is stated but not why the order matters | "Critical issues have cascading effects — an architecture error in Task 2 makes Task 3-6 wrong too. Addressing them immediately prevents compound rework." |

---

### using-superpowers/SKILL.md
**Unmotivated rules found:** 3

The `<EXTREMELY-IMPORTANT>` block intensity issues are covered in the area-1 de-escalation report. This audit focuses on motivation gaps in the lower-intensity parts of the skill.

| Rule (quoted) | Why Obvious? | Proposed Motivation |
|---------------|-------------|-------------------|
| `Never use the Read tool on skill files` (in How to Access Skills) | No — this constraint could seem paranoid or arbitrary | "The Read tool loads file content into the conversation context, consuming tokens and bypassing the skill loading mechanism. The Skill tool loads the skill cleanly and registers it as active — Read just dumps text." |
| `Process skills first (brainstorming, debugging) — these determine HOW to approach the task` | No motivation for why ordering matters | "Implementation skills applied before process skills produce a local-optimum solution to the wrong problem. Brainstorming and debugging change the frame — running them after you've started implementation means the frame change requires rework." |
| `Skills evolve. Read current version.` (Red Flags table, "I remember this skill") | No — this is asserted but not supported | "Skills in this fork are actively maintained and modified based on production incidents. The version in memory may predate a fix for the exact failure mode you're about to encounter." |

---

### verification-before-completion/SKILL.md
**Unmotivated rules found:** 3

Note: The shaming-language issues (dishonesty, lying, "you'll be replaced") are covered in the area-1 de-escalation report. This audit focuses on motivation gaps separate from tone problems.

| Rule (quoted) | Why Obvious? | Proposed Motivation |
|---------------|-------------|-------------------|
| `If you haven't run the verification command in this message, you cannot claim it passes.` | Partially — but the "this message" specificity has no explanation | "Test results from previous messages may be stale — code changes between messages invalidate prior run results. 'This message' is the freshness guarantee." |
| `Trusting agent success reports` (Red Flags list) | No motivation for why agent reports are not trustworthy | "Agent reports describe what the agent attempted, not what the code does. Agents can report DONE on partially-completed work, on work that passed wrong-assumption tests, or on work that doesn't wire into the consuming code. Verification bypasses the report and checks the artifact directly." |
| `Rule applies to: Exact phrases / Paraphrases and synonyms / Implications of success` | No explanation for why the rule extends to paraphrases | "Incomplete verification expressed in hedged language ('should pass', 'looks right') has caused the same downstream failures as explicit false claims. The rule covers substance, not phrasing." |

---

### writing-skills/SKILL.md
**Unmotivated rules found:** 4

| Rule (quoted) | Why Obvious? | Proposed Motivation |
|---------------|-------------|-------------------|
| `Why no @ links: @ syntax force-loads files immediately, consuming 200k+ context before you need them.` | Motivation IS present. No addition needed. | N/A |
| `Name uses only letters, numbers, hyphens (no parentheses/special chars)` (Skill Creation Checklist) | No — file system constraint is implied but not stated | "Special characters in skill names cause failures in shell scripts and the command stub generation loop — the `for dir in skills/*/` pattern breaks on names with parentheses or spaces." |
| `Description starts with 'Use when...'` | Motivation IS present (CSO section explains at length). No addition needed. | N/A |
| `Deploying untested skills = deploying untested code` | Motivation IS present as a direct analogy. No addition needed. | N/A |
| `Do NOT: Create multiple skills in batch without testing each` | No — the reason batch creation is risky is not stated | "Each skill iteration may reveal rationalizations that feed into the next skill's design. Writing 5 skills without testing means 4 of them were written blind to the failure modes that test 1 would have exposed." |
| `REQUIRED BACKGROUND: You MUST understand superpowers:test-driven-development before using this skill.` | No motivation for why background reading is required (not just useful) | "The RED-GREEN-REFACTOR cycle is referenced throughout this skill by name. Without understanding what those terms mean, the checklist steps are labels without content — you'll follow the steps mechanically and miss the point of each phase." |

Actual new motivation gaps: 3 (the TDD prerequisite, skill naming, and batch creation prohibition).

**Unmotivated rules found:** 3

---

### systematic-debugging/SKILL.md
**Unmotivated rules found:** 3

Note: "ALWAYS" and "Violating the spirit" intensity issues are covered in area-1. This audit focuses on motivation gaps in procedural rules.

| Rule (quoted) | Why Obvious? | Proposed Motivation |
|---------------|-------------|-------------------|
| `You MUST complete each phase before proceeding to the next.` | No — phase ordering could seem like structure-for-structure's sake | "Each phase depends on outputs from the prior. Phase 2 (pattern analysis) requires a reproducible symptom from Phase 1. Phase 3 (hypothesis) requires knowing what's different between working and broken cases from Phase 2. Jumping ahead means forming hypotheses about unknown unknowns." |
| `ONE change at a time / No 'while I'm here' improvements` | Partially obvious for isolation, but the specific consequence is not named | "Multiple simultaneous changes make it impossible to attribute a regression to the fix that caused it. If tests break after a bundle of changes, you must revert everything and re-apply one at a time — losing the work twice." |
| `Discuss with your human partner before attempting more fixes` (3+ fixes failed section) | No — stopping for discussion could seem like excessive caution | "Three failed fixes is the signal that the problem is architectural, not a local bug. Architectural problems require design decisions that exceed the debugging skill's scope — continuing without consultation means making design decisions without the human's input or buy-in." |

---

### test-driven-development/SKILL.md
**Unmotivated rules found:** 2

Note: This skill is already unusually well-motivated — the "Why Order Matters" section provides extensive rationale for the core rule. Tone issues are covered in area-1. Two gaps remain:

| Rule (quoted) | Why Obvious? | Proposed Motivation |
|---------------|-------------|-------------------|
| `Don't add features, refactor other code, or 'improve' beyond the test.` (GREEN phase) | No — this could seem overly restrictive | "GREEN phase code only needs to pass the current test. Adding more code beyond that adds untested behavior — you can't tell if the extra code is correct because no test exists for it. Refactor phase, with all tests green, is the safe place for improvements." |
| `No exceptions without your human partner's permission.` (Final Rule) | No — the human-in-loop requirement is stated but not explained | "Exceptions to TDD have a documented pattern of being 'just this once' in the moment and becoming team norms in practice. Human permission makes the exception visible and deliberate rather than a local optimization that silently spreads." |

---

### brainstorming/SKILL-v0.1.md
**Unmotivated rules found:** 3

| Rule (quoted) | Why Obvious? | Proposed Motivation |
|---------------|-------------|-------------------|
| `Do NOT invoke any implementation skill, write any code, scaffold any project, or take any implementation action until you have presented a design and the user has approved it.` | Motivation partially exists in the Anti-Pattern section below, but it applies to "simple projects" rationale, not to the general case | "Implementation without a written design produces code that encodes decisions the user hasn't reviewed. Reversing those decisions after code exists costs significantly more than iterating on a spec." |
| `The ONLY skill you invoke after brainstorming is writing-plans.` | No — this constraint excludes other skills but doesn't explain why | "Frontend-design, mcp-builder, and other implementation skills each assume the design is settled. Invoking them during brainstorming bypasses the design review step and prematurely closes options the user may want to revisit." |
| `Identify the feature archetype early` | No — why early matters is not stated | "Archetype identification determines what the spec needs to document. A replacement archetype requires obsolescence tracking; a refactor requires consumer verification. Identifying it late means retrofitting the spec after design is done — the spec may be missing critical sections." |

---

### writing-plans/SKILL-v0.1.md
**Unmotivated rules found:** 4

| Rule (quoted) | Why Obvious? | Proposed Motivation |
|---------------|-------------|-------------------|
| `If the plan will exceed 800 lines, it MUST be decomposed into independent modules.` | The "why" is actually present one sentence later ("exhausts subagent context windows, makes parallelism impossible, obscures dependencies"). No addition needed. | N/A |
| `Each file should have one clear responsibility with a well-defined interface.` | No — this is stated as a design principle without grounding it in the plan-execution context | "Subagents implement one task at a time. A file with multiple responsibilities will be partially owned by multiple tasks — both tasks will touch it, requiring serialization and increasing the chance of merge conflicts between task commits." |
| `Exact file paths always` | No — could seem like pedantry | "Subagents receiving a task prompt do not have your codebase knowledge. An ambiguous path like 'the router file' forces them to search the repo before implementing. Exact paths eliminate that ambiguity and reduce the chance of the subagent editing the wrong file." |
| `Complete code in plan (not 'add validation')` | No — the instruction is stated as a standard but without explaining why approximations are dangerous | "Vague instructions like 'add validation' leave the implementation decision to the subagent, who has no context about your validation patterns, error message formats, or existing validators. The plan should encode those decisions — the subagent should execute them, not make them." |

Actual new motivation gaps: 3 (file responsibility, exact paths, complete code). The 800-line limit already has motivation.

**Unmotivated rules found:** 3

---

### subagent-driven-development/SKILL-v0.1.md
**Unmotivated rules found:** 4

Note: This skill is heavily motivated in v0.1 — most major rules already have rationale. The "Review Enforcement" section, "file-based persistence" section, and "Task 0 exists" section all have good explanatory density. Four gaps remain in less prominent rules:

| Rule (quoted) | Why Obvious? | Proposed Motivation |
|---------------|-------------|-------------------|
| `Do not paraphrase it [Contract Constraints].` | No — paraphrasing seems like a reasonable summary technique | "Paraphrasing contract constraints introduces interpretation. A constraint like 'all amounts are strings' paraphrased as 'handle amounts carefully' loses the specific type information the subagent needs to implement correctly." |
| `Dispatch multiple implementation subagents in parallel (conflicts)` (Red Flags Never list) | No — parallel dispatch seems efficient and the conflict mechanism is not stated | "Parallel subagents write to files simultaneously. Without coordination, one subagent's commit will be overwritten by another's. The Write-Scope Partitioning table resolves this, but only if subagents are dispatched sequentially." |
| `Try to fix a failed task manually (context pollution) — dispatch a fix subagent` | No — fixing manually seems faster; context pollution is mentioned but not defined | "When the controller edits files directly to fix a failed task, it accumulates session context about implementation details that should belong to a fresh subagent. This context bleeds into subsequent task dispatches and spec reviews, making the controller a less reliable evaluator of its own work." |
| `The controller MUST declare the review tier before dispatching each task and state the rationale.` | No — pre-declaration seems bureaucratic | "Declaring tier before dispatch forces the controller to make an explicit risk assessment before it sees the implementer's report. Deciding tier after seeing the report introduces post-hoc rationalization — 'the report looks clean, minimum review is fine.' " |

---

### subagent-driven-development/implementer-prompt-v0.1.md
**Unmotivated rules found:** 1

Note: This prompt template is well-motivated. The CLAUDE.md section has incident context ("caused full rewrites"), the contract constraints section explains what to do when violated, and the self-review section explains what each category catches. One gap:

| Rule (quoted) | Why Obvious? | Proposed Motivation |
|---------------|-------------|-------------------|
| `Use DONE_WITH_CONCERNS if you have any entries in Deviations or Concerns. / Never silently produce work you're unsure about.` | Partially — the instruction is clear, but why the controller specifically needs this vs. reading the report itself is not stated | "The controller uses DONE_WITH_CONCERNS as a routing signal. DONE triggers a standard review path; DONE_WITH_CONCERNS triggers reading the deviations before review, not after. A DONE report with concerns buried in the body will be reviewed without the controller knowing to look for them." |

---

### subagent-driven-development/spec-reviewer-prompt-v0.1.md
**Unmotivated rules found:** 2

Note: The "Do Not Trust the Report" block in v0.1 is an improvement over the original — the de-escalation report addresses tone. This audit looks at motivation gaps separate from tone.

| Rule (quoted) | Why Obvious? | Proposed Motivation |
|---------------|-------------|-------------------|
| `A contract violation that 'works because the test fixture matches the wrong type' is still a violation. Verify against the constraint, not the test.` | Good motivation actually follows ("Verify against the constraint, not the test"). The distinction is made. However, WHY tests can't be trusted here is not stated. | "Test fixtures in subagent implementations are written by the same subagent that wrote the code. If the subagent used the wrong type, the fixture will match the wrong type — both will be wrong together. Test passage proves internal consistency, not external contract compliance." |
| `Did they look for and read any CLAUDE.md files in directories containing modifications?` | No — the reviewer is asked to check this but not told why it matters to the spec compliance review | "If the implementer skipped the CLAUDE.md step, they may have used wrong component patterns, typography variants, or anti-patterns specific to that part of the codebase. These are spec violations for codebases where the CLAUDE.md defines the implementation contract." |

---

### subagent-driven-development/code-quality-reviewer-prompt-v0.1.md
**Unmotivated rules found:** 1

Note: The dead code rule already has strong motivation ("Dead code findings are blocking — they must be resolved"). One gap:

| Rule (quoted) | Why Obvious? | Proposed Motivation |
|---------------|-------------|-------------------|
| `Only dispatch after spec compliance review passes.` | No — the ordering is stated but not why quality review before spec review wastes effort | "Code quality review evaluates how the code is built. Spec compliance review evaluates whether the right thing was built. Reviewing quality on code that will be rewritten due to spec failures wastes the reviewer's analysis. Spec pass is the gate that confirms the code is in its final form." |

---

## Summary

### Total Unmotivated Rules by File

| File | Rules Flagged |
|------|--------------|
| `executing-plans/SKILL.md` | 5 |
| `finishing-a-development-branch/SKILL.md` | 4 |
| `dispatching-parallel-agents/SKILL.md` | 2 |
| `using-git-worktrees/SKILL.md` | 3 |
| `handoff-acceptance/SKILL.md` | 1 |
| `receiving-code-review/SKILL.md` | 2 |
| `requesting-code-review/SKILL.md` | 2 |
| `using-superpowers/SKILL.md` | 3 |
| `verification-before-completion/SKILL.md` | 3 |
| `writing-skills/SKILL.md` | 3 |
| `systematic-debugging/SKILL.md` | 3 |
| `test-driven-development/SKILL.md` | 2 |
| `brainstorming/SKILL-v0.1.md` | 3 |
| `writing-plans/SKILL-v0.1.md` | 3 |
| `subagent-driven-development/SKILL-v0.1.md` | 4 |
| `implementer-prompt-v0.1.md` | 1 |
| `spec-reviewer-prompt-v0.1.md` | 2 |
| `code-quality-reviewer-prompt-v0.1.md` | 1 |
| **Total** | **47** |

### Top 10 Highest-Impact Additions

Priority based on: (1) the rule is high-stakes and compliance failures are expensive; (2) the motivation references real incidents; (3) the "why" is genuinely non-obvious without reading incident documents.

**1. `subagent-driven-development/SKILL-v0.1.md` — parallel dispatch prohibition**
> "Parallel subagents write to files simultaneously. Without coordination, one subagent's commit will be overwritten by another's."
The rule appears in the Red Flags Never list with no explanation. Engineers frequently assume parallelism is safe if they "just avoid touching the same file" — but they haven't seen the Write-Scope Partitioning table.

**2. `spec-reviewer-prompt-v0.1.md` — why tests can't verify contract compliance**
> "Test fixtures in subagent implementations are written by the same subagent that wrote the code. If the subagent used the wrong type, the fixture will match the wrong type — both will be wrong together."
This is the exact failure mode from the reconciliation incident (3 bugs shipped, all tests passing). The reviewer rule to "verify against the constraint, not the test" has more weight when it names this failure mode explicitly.

**3. `requesting-code-review/SKILL.md` — why "simple" tasks still require review**
> "The statement-reconciliation incident traced 3 production bugs to tasks that seemed simple — the simplicity was why no one looked carefully."
This rule is currently a flat prohibition with no context. Adding the incident reference transforms it from "don't skip review" to "here's what happened when we skipped it."

**4. `executing-plans/SKILL.md` — why blockers must not be forced through**
> "Forcing through a blocker in a plan means every subsequent task builds on a broken foundation — the cost of not stopping compounds with each additional task."
The rule exists but has no compounding-failure rationale. Plan execution across 10+ tasks amplifies this — the motivation explains why the rule is more important here than in ad-hoc debugging.

**5. `code-quality-reviewer-prompt-v0.1.md` — why spec review must precede quality review**
> "Reviewing quality on code that will be rewritten due to spec failures wastes the reviewer's analysis. Spec pass is the gate that confirms the code is in its final form."
The dispatch ordering is stated but not justified. Controllers under context pressure will be tempted to run reviews in parallel to save time — this motivation names the specific cost of doing that.

**6. `verification-before-completion/SKILL.md` — why agent reports cannot be trusted**
> "Agent reports describe what the agent attempted, not what the code does. Agents can report DONE on partially-completed work, on work that passed wrong-assumption tests, or on work that doesn't wire into the consuming code."
The Red Flags list currently just says "Trusting agent success reports" without explaining why the trust is misplaced. The three failure modes named here are all attested in the reconciliation lessons-learned.

**7. `subagent-driven-development/SKILL-v0.1.md` — why review tier must be declared before dispatch**
> "Deciding tier after seeing the report introduces post-hoc rationalization — 'the report looks clean, minimum review is fine.' "
The pre-declaration requirement reads as process overhead without this rationale. The motivation explains it as a bias-prevention mechanism.

**8. `writing-plans/SKILL-v0.1.md` — why complete code (not "add validation") is required**
> "Vague instructions leave the implementation decision to the subagent, who has no context about your validation patterns, error message formats, or existing validators. The plan should encode those decisions — the subagent should execute them, not make them."
This rule is often treated as style guidance. The motivation grounds it in the controller/subagent division of labor.

**9. `using-superpowers/SKILL.md` — why the Read tool must not be used on skill files**
> "The Read tool loads file content into the conversation context, consuming tokens and bypassing the skill loading mechanism. The Skill tool loads the skill cleanly and registers it as active — Read just dumps text."
Currently a bare prohibition. Without the mechanism explained, users may view Read as equivalent to Skill.

**10. `finishing-a-development-branch/SKILL.md` — why typed 'discard' confirmation is required**
> "Typed confirmation prevents accidental discard from ambiguous affirmations like 'yes' or 'ok' that could be leftover from a prior question."
This is a safety-critical rule that reads as arbitrary without the mechanism. The reason is a usability one (conversation context ambiguity), not just a general "destructive action" principle.

### Calibration Notes

**Skills that are well-motivated and need the fewest additions:**
- `handoff-acceptance/SKILL.md` — Every BLOCKING check has a "Why" subsection. Model for other skills.
- `subagent-driven-development/SKILL-v0.1.md` — Plan ingestion section, Task 0 section, and file persistence section all have strong motivation. Only minor gaps in peripheral rules.
- `test-driven-development/SKILL.md` — The "Why Order Matters" section is comprehensive. Only two gaps, both in later procedural rules.

**Skills with the most motivation gaps relative to their stakes:**
- `executing-plans/SKILL.md` — 5 gaps, all in rules that govern how a multi-task execution goes wrong. This skill is invoked for the highest-stakes workflows and has the tersest explanations.
- `finishing-a-development-branch/SKILL.md` — 4 gaps in rules that look arbitrary without context. The "present exactly 4 options" rule is the most likely to be deviated from without motivation.

**Implementation advice:**
Add motivation inline, adjacent to the rule it explains — not in a separate "Why This Matters" section at the bottom. The best practice example from the Anthropic guide shows motivation as part of the same instruction, not footnoted. The `handoff-acceptance/SKILL.md` pattern (bold rule + indented "Why:" line immediately below) is the right model.
