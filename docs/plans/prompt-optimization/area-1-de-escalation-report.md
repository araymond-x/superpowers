# De-escalation Audit Report — Superpowers Skills

**Audit date:** 2026-03-23
**Standard applied:** Anthropic prompting best practices for Claude 4.6 models
**Key reference:** `docs/prompting-best-practices.md` — "Tool Use" section: "Where you might have said 'CRITICAL: You MUST use this tool when...', you can use more normal prompting like 'Use this tool when...' — these models may now overtrigger."

**Scope:** 15 SKILL files (v0.1 where available) + 3 prompt templates

---

## Per-File Audit

### brainstorming/SKILL-v0.1.md
**Instances found:** 4

| Line | Original | Warranted? | Proposed |
|------|----------|-----------|----------|
| 12–14 | `## CRITICAL CONSTRAINT` / `**Do NOT invoke any implementation skill, write any code, scaffold any project, or take any implementation action until you have presented a design and the user has approved it. This applies to EVERY project regardless of perceived simplicity.**` | WARRANTED | Keep "Do NOT" + "regardless of perceived simplicity" — this is an enforcement gate that replaces the old `<HARD-GATE>` XML tag. The constraint itself is legitimate; the header could soften to `## Design Gate` but the body language is appropriate for a blocking constraint. |
| 18 | `you MUST present it and get approval` (in "Anti-Pattern" section) | OVERBLOWN | "you must present it and get approval" — lowercase MUST is sufficient here; the blocking context is already established by the section header. |
| 22 | `You MUST create a task for each of these items` | OVERBLOWN | "Create a task for each of these items" — the checklist context makes this instruction self-evident without the uppercase MUST. |
| 208 | `**This offer MUST be its own message.**` | OVERBLOWN | "**This offer should be its own message.**" — the reason follows immediately ("Do not combine it with clarifying questions..."), which is sufficient. |

---

### dispatching-parallel-agents/SKILL.md
**Instances found:** 0

No ALL CAPS emphasis, threatening language, absolutist claims, or shaming language found. This skill is well-calibrated.

---

### executing-plans/SKILL.md
**Instances found:** 2

| Line | Original | Warranted? | Proposed |
|------|----------|-----------|----------|
| 36 | `**REQUIRED SUB-SKILL:** Use superpowers:finishing-a-development-branch` | OVERBLOWN | "**Sub-skill required:** Use superpowers:finishing-a-development-branch" — "REQUIRED" in all caps adds no meaning that isn't already conveyed by the bold label. |
| 68 | `**superpowers:using-git-worktrees** - REQUIRED: Set up isolated workspace before starting` | OVERBLOWN | `**superpowers:using-git-worktrees** — Set up isolated workspace before starting` — "REQUIRED" in a bulleted integration list is redundant with the list's purpose. |

---

### finishing-a-development-branch/SKILL.md
**Instances found:** 1

| Line | Original | Warranted? | Proposed |
|------|----------|-----------|----------|
| 181–191 | Red Flags `**Never:**` / `**Always:**` list | WARRANTED | These are standard safety-check lists in a low-risk skill. The "Never" items are concrete safety rules (don't proceed with failing tests, don't delete work without confirmation). No overblown intensity here — these read as professional checklists, not threats. |

No items found that are genuinely aggressive or potentially overtriggering for 4.6. The "Never/Always" lists are appropriate for a safety-critical completion workflow.

---

### handoff-acceptance/SKILL.md
**Instances found:** 2

| Line | Original | Warranted? | Proposed |
|------|----------|-----------|----------|
| 21 | `the controller (or a dispatched reviewer subagent) MUST verify each item` | OVERBLOWN | "the controller (or a dispatched reviewer subagent) should verify each item" — the [BLOCKING] tag on items below carries the enforcement weight; MUST here is redundant. |
| 21 | `A handoff package that fails any BLOCKING check must be returned for revision before consumption.` | WARRANTED | "BLOCKING" is a status label, not an intensity marker. The sentence is clear enforcement without being threatening. Keep as-is. |

---

### receiving-code-review/SKILL.md
**Instances found:** 5

| Line | Original | Warranted? | Proposed |
|------|----------|-----------|----------|
| 28–29 | `**NEVER:**` (Forbidden Responses header) | OVERBLOWN | `**Avoid:**` or `**Don't:**` — this is a style guide for response tone, not a safety-critical constraint. "NEVER" in all caps is excessive for "don't say 'Great point!'". |
| 29 | `- "You're absolutely right!" (explicit CLAUDE.md violation)` | OVERBLOWN | Remove the parenthetical "(explicit CLAUDE.md violation)" — it reads as a threat/shame label. The example speaks for itself. |
| 141–143 | `❌ ANY gratitude expression` | BORDERLINE | Keep — this is a behavioral pattern marker using emoji, not all-caps. Acceptable as a code-review style guide. |
| 148 | `**If you catch yourself about to write "Thanks":** DELETE IT. State the fix instead.` | OVERBLOWN | `**If you start to write "Thanks":** Skip it. State the fix instead.` — "DELETE IT" in all caps is more intense than needed for a style preference. |
| 115 | `**If you catch yourself thinking: ... ALL of these mean: STOP. Return to Phase 1.**` (in systematic-debugging — this entry filed there) | N/A | See systematic-debugging below |

---

### requesting-code-review/SKILL.md
**Instances found:** 1

| Line | Original | Warranted? | Proposed |
|------|----------|-----------|----------|
| 93–97 | `**Never:**` list ("Skip review because 'it's simple'", "Ignore Critical issues", etc.) | WARRANTED | These are legitimate workflow enforcement rules. "Never skip review because 'it's simple'" is appropriate — this skill exists because simplicity is a rationalization for skipping reviews. The intensity matches the use case. |

---

### subagent-driven-development/SKILL-v0.1.md
**Instances found:** 15

This file contains the highest concentration of aggressive language. The Review Enforcement section was deliberately added after a real incident (controller skipped 34 reviews in a single session). Entries are annotated accordingly.

| Line | Original | Warranted? | Proposed |
|------|----------|-----------|----------|
| 152 | `Before dispatching any subagent, the controller MUST complete a full plan ingestion pass. This is not optional.` | INCIDENT-BACKED | Reduce tone while preserving constraint: "Before dispatching any subagent, complete a full plan ingestion pass — all sections are load-bearing." |
| 155 | `Do not skim. Read every section. The plan header, Contract Constraints, task list, Write-Scope Partitioning table, and any notes are all load-bearing. Missing context at this stage causes silent failures 10 tasks later.` | WARRANTED | The "Do not skim" framing is direct rather than aggressive. The consequence statement ("silent failures 10 tasks later") is factual. Keep. |
| 189 | `If the plan has a Task 0 (Contract Verification), it MUST be the first item.` | INCIDENT-BACKED | "If the plan has a Task 0 (Contract Verification), it should be the first item." — The enforcement context is established by the surrounding rules; MUST is redundant. |
| 206 | `When dispatching each implementer subagent, the controller MUST include the plan's Contract Constraints section verbatim` | INCIDENT-BACKED | "When dispatching each implementer subagent, include the plan's Contract Constraints section verbatim" — direct imperative is sufficient. |
| 210 | `This passthrough is not optional.` | INCIDENT-BACKED | Remove — the preceding "include...verbatim" is already imperative. "Not optional" is redundant intensity. |
| 284 | `**YOU MUST NOT SKIP REVIEWS FOR ANY REASON.**` | INCIDENT-BACKED | `**Do not skip reviews for any reason.**` — Uppercase renders this as a shout. The constraint is legitimate (incident-backed); the shouting is the problem. Bold is sufficient. |
| 286 | `This is not a guideline. This is not optional. This is not something you can optimize away.` | INCIDENT-BACKED | Remove entirely — the "Rationalizations that are never valid" list immediately below makes this point concretely. The triple negation reads as hectoring. |
| 288–295 | `**Rationalizations that are never valid:**` list (7 items) | INCIDENT-BACKED | Rename to `**Rationalizations that don't override the requirement:**` and keep the list — the specific examples are valuable and incident-backed. |
| 295 | `"Just this once" — There is no "just this once." Every skip is a policy decision.` | INCIDENT-BACKED | Keep — this is a clear statement of principle, not a threat. The logic is sound and non-shaming. |
| 223 | `This is a deterministic check. Do not override it based on judgment — if the script says TOO_LARGE, the task is too large. Split it.` | WARRANTED | Keep — this is a process instruction, not aggressive language. "Deterministic" and "Split it" are appropriate. |
| 345 | `Never ignore an escalation or force the same model to retry without changes.` | WARRANTED | Keep — process rule, appropriate tone. |
| 403–413 | Pre-Completion Gate list: `These checks are not bureaucratic overhead.` | WARRANTED | Keep — this is a legitimate defense of the process, not aggressive. |
| 441–454 | `**Never:**` list at end of Red Flags section | INCIDENT-BACKED | Most items are legitimate. Flag one item: `**Start code quality review before spec compliance is PASS** (wrong order)` — reformulate as: `Start code quality review only after spec compliance returns PASS.` Removes the bold-capitalization combination. |
| 451 | `Accept "close enough" on spec compliance (spec reviewer found issues = not done)` | WARRANTED | Keep — the parenthetical clarification is helpful, not shaming. |
| 152 (Plan Ingestion header) | Section heading "**This is not optional.**" embedded in prose | INCIDENT-BACKED | Already handled in line 152 entry above. |

**Note on the Review Enforcement section (lines 282–312):** This entire section was added to address a documented incident where a controller skipped 34 of 34 per-task reviews. The aggressive language was intentional. The recommendation is to **preserve the constraint strength while removing the shouting and triple negation**. The specific rationalization examples and "no just this once" principle should be kept — they are the behavioral value. What can go: uppercase MUST NOT, "This is not a guideline. This is not optional. This is not something you can optimize away."

---

### systematic-debugging/SKILL.md
**Instances found:** 6

| Line | Original | Warranted? | Proposed |
|------|----------|-----------|----------|
| 12 | `**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.` | OVERBLOWN | `**Core principle:** Find root cause before attempting fixes. Symptom fixes mask the real problem.` — "ALWAYS" in caps + "are failure" is double intensity. |
| 14 | `**Violating the letter of this process is violating the spirit of debugging.**` | OVERBLOWN | Remove — this sentence is a preemptive accusation. The process itself makes the point. |
| 19 | `NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST` (Iron Law box) | BORDERLINE | Keep as a visually distinct block, but it could be rendered as: `Root cause investigation before any fixes.` The all-caps block format is used intentionally for the "Iron Law" pattern across multiple skills; it's a visual convention more than an aggression signal. Judge by whether it's causing overtriggering — if so, soften. |
| 48 | `You MUST complete each phase before proceeding to the next.` | OVERBLOWN | `Complete each phase before proceeding to the next.` — imperative is sufficient. |
| 230 | `**ALL of these mean: STOP. Return to Phase 1.**` | OVERBLOWN | `**Any of these means: stop and return to Phase 1.**` — "ALL" in caps + "STOP" in caps is double intensity. |
| 15–16 area | (See also Red Flags section "If you catch yourself thinking") | WARRANTED | The Red Flags list structure itself is appropriate — it's a checklist format. The specific items are reasonable behavioral warnings. |

---

### test-driven-development/SKILL.md
**Instances found:** 7

| Line | Original | Warranted? | Proposed |
|------|----------|-----------|----------|
| 14 | `**Violating the letter of the rules is violating the spirit of the rules.**` | OVERBLOWN | Remove — same pattern as systematic-debugging. This preemptive challenge is an anti-pattern for 4.6 models. |
| 29 | `Thinking "skip TDD just this once"? Stop. That's rationalization.` | OVERBLOWN | `If you're thinking about skipping TDD "just this once," that's a rationalization.` — "Stop." as a one-word sentence reads as a command-shout in a text prompt. |
| 37 | `Write code before the test? Delete it. Start over.` | BORDERLINE | Keep — this is the Iron Law box convention. The bluntness is functional here, not aggressive. But "Delete it." with a period does read more emphatically than needed. Could soften to: `If you wrote code before the test, delete it and start over.` |
| 43–44 | `- Don't keep it as "reference"` / `- Delete means delete` | OVERBLOWN | `Delete means delete` is a phrase that reads as mocking future rationalizations. Replace with: `Delete it completely — do not keep it as reference or adapt it while writing tests.` Consolidates into one clear instruction. |
| 115 | `**MANDATORY. Never skip.**` (Verify RED step) | OVERBLOWN | `**Required. Do not skip.**` or just keep as `**Do this every time.**` — "MANDATORY" in all caps for a step description is unnecessary given the surrounding Iron Law framing. |
| 170 | `**MANDATORY.**` (Verify GREEN step) | OVERBLOWN | Same as above: `**Required.**` |
| 340 | `Can't check all boxes? You skipped TDD. Start over.` | OVERBLOWN | `If any box is unchecked, TDD was not followed. Start over.` — "You skipped TDD" is a shame statement. The factual statement ("TDD was not followed") conveys the same enforcement without accusation. |

---

### using-git-worktrees/SKILL.md
**Instances found:** 2

| Line | Original | Warranted? | Proposed |
|------|----------|-----------|----------|
| 55–56 | `**MUST verify directory is ignored before creating worktree:**` | OVERBLOWN | `**Verify directory is ignored before creating worktree:**` — the bold is sufficient; MUST adds no enforcement above "verify". |
| 69 | `**Why critical:**` (label for the "prevents accidentally committing worktree contents" explanation) | BORDERLINE | Keep — "Why critical" is a section label explaining severity. Not an intensity marker per se. |

---

### using-superpowers/SKILL.md
**Instances found:** 5

| Line | Original | Warranted? | Proposed |
|------|----------|-----------|----------|
| 10–16 | `<EXTREMELY-IMPORTANT>` block: `If you think there is even a 1% chance a skill might apply to what you are doing, you ABSOLUTELY MUST invoke the skill. / IF A SKILL APPLIES TO YOUR TASK, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT. / This is not negotiable. This is not optional. You cannot rationalize your way out of this.` | OVERBLOWN — AND HIGH OVERTRIGGER RISK | This block is the single highest-priority item in the audit. Per the best practices doc: "these models may now overtrigger" from exactly this kind of language. Proposed: Remove the `<EXTREMELY-IMPORTANT>` block entirely (or replace with `<mandatory>` per the XML audit recommendations). Replace content with: `If a skill applies to your task, invoke it. When in doubt about whether a skill applies, invoke it to check — if it turns out to be the wrong skill, you don't need to use it.` |
| 11 | `you ABSOLUTELY MUST invoke the skill` | OVERBLOWN | Covered by block replacement above. |
| 12 | `IF A SKILL APPLIES TO YOUR TASK, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT.` | OVERBLOWN | Covered by block replacement above. |
| 15 | `This is not negotiable. This is not optional. You cannot rationalize your way out of this.` | OVERBLOWN | Covered by block replacement above. |
| 44 | `**Invoke relevant or requested skills BEFORE any response or action.** Even a 1% chance a skill might apply means that you should invoke the skill to check.` | BORDERLINE | The body text is fine. The 1% threshold is a concrete decision rule, not aggression. Keep but normalize: `Invoke relevant or requested skills before any response or action. When in doubt — even a small chance a skill applies — invoke it to check.` |

---

### verification-before-completion/SKILL.md
**Instances found:** 7

| Line | Original | Warranted? | Proposed |
|------|----------|-----------|----------|
| 10 | `Claiming work is complete without verification is dishonesty, not efficiency.` | OVERBLOWN | `Claiming work is complete without verification is inaccurate, not efficient.` — "dishonesty" frames unverified claims as a moral failing. This is shaming language. The corrected framing ("inaccurate") conveys the same behavioral constraint without the accusation. |
| 14 | `**Violating the letter of this rule is violating the spirit of this rule.**` | OVERBLOWN | Remove — same pattern as systematic-debugging and TDD. Preemptive challenge, not a useful instruction. |
| 19 | `NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE` (Iron Law box) | BORDERLINE | Same as TDD/debugging Iron Law boxes. Keep as visual convention or soften to: `Verification evidence required before any completion claim.` |
| 37 | `Skip any step = lying, not verifying` | OVERBLOWN | `Skip any step = unverified claim, not completion` — "lying" is a moral accusation. The factual framing ("unverified claim") is more accurate and less shaming. |
| 115 | `Violates: "Honesty is a core value. If you lie, you'll be replaced."` | OVERBLOWN | Remove or replace with: `Unverified completion claims have historically led to re-work and broken trust.` — the quoted threat ("you'll be replaced") is inappropriate for a process document and irrelevant to 4.6. It references a prior conversation context that doesn't generalize. |
| 139 | `This is non-negotiable.` | OVERBLOWN | Remove — the "No shortcuts for verification. Run the command. Read the output. THEN claim the result." before it is already the closing statement. "This is non-negotiable" adds nothing except intensity. |
| 36 | (Gate function header) `BEFORE claiming any status or expressing satisfaction:` | WARRANTED | Keep — "BEFORE" here is a sequencing cue, not an intensity marker. |

---

### writing-plans/SKILL-v0.1.md
**Instances found:** 4

| Line | Original | Warranted? | Proposed |
|------|----------|-----------|----------|
| 27 | `**If the plan will exceed 800 lines, it MUST be decomposed into independent modules.**` | OVERBLOWN | `**If the plan will exceed 800 lines, decompose it into independent modules.**` — imperative form is sufficient. |
| 142 | `**Every plan intended for subagent execution MUST include this section before the task list.**` | OVERBLOWN | `**Every plan intended for subagent execution should include this section before the task list.**` — or rephrase as `**Include this section before the task list for any plan intended for subagent execution.**` |
| 164 | `**Every plan MUST classify its feature archetype and map its code footprint.**` | OVERBLOWN | `**Every plan should classify its feature archetype and map its code footprint.**` — same pattern. |
| 198 | `**If the plan has any Source Contracts (external APIs, schemas, handoff packages), Task 0 is mandatory.**` | OVERBLOWN | `**If the plan has any Source Contracts, include a Task 0 (Contract Verification).**` — "mandatory" adds no meaning to what is already a conditional imperative. |

---

### writing-skills/SKILL.md
**Instances found:** 2

| Line | Original | Warranted? | Proposed |
|------|----------|-----------|----------|
| 17 | `**REQUIRED BACKGROUND:** You MUST understand superpowers:test-driven-development before using this skill.` | OVERBLOWN | `**Background:** Read superpowers:test-driven-development before using this skill.` — REQUIRED and MUST together are double intensity for a prerequisite note. |
| (elsewhere in file — need verification) | Any `<Good>/<Bad>` XML tags | Not intensity language — see area-5-xml-tags-report.md for those findings. | N/A |

---

### Prompt Templates

### subagent-driven-development/implementer-prompt-v0.1.md
**Instances found:** 2

| Line | Original | Warranted? | Proposed |
|------|----------|-----------|----------|
| 43–46 | `**CRITICAL**: Before writing any code, check if the directories you will modify contain their own CLAUDE.md files. Read them first. ... Skipping this step has caused full rewrites in the past...` | INCIDENT-BACKED | Reduce to: `Before writing any code, check if the directories you will modify contain their own CLAUDE.md files and read them. These contain design systems, UI primitives, naming conventions, and anti-patterns. Skipping this step has caused full rewrites.` — Remove "CRITICAL" in caps; the consequence statement carries the weight. |
| 141 | `you MUST report using this exact structure. Do not omit sections.` | OVERBLOWN | `Report using this exact structure. Do not omit sections.` — imperative form is sufficient without MUST. |

---

### subagent-driven-development/spec-reviewer-prompt-v0.1.md
**Instances found:** 2

| Line | Original | Warranted? | Proposed |
|------|----------|-----------|----------|
| 28 | `## CRITICAL: Do Not Trust the Report` | OVERBLOWN | `## Verify Independently — Do Not Trust the Report` — "CRITICAL" as a section header combined with "Do Not Trust" is double aggression. The skepticism instruction is valid; the framing can be direct without being dramatic. |
| 29 | `The implementer finished suspiciously quickly.` | OVERBLOWN | Remove this sentence entirely. It presupposes bad faith and is factually inaccurate — fast completion can mean good planning. Replace with: `Verify all claims independently by reading the code, not the report.` |

---

### subagent-driven-development/code-quality-reviewer-prompt-v0.1.md
**Instances found:** 1

| Line | Original | Warranted? | Proposed |
|------|----------|-----------|----------|
| 26 | `**Dead code findings are blocking** — they must be resolved (removed or explicitly justified in DEVIATIONS.md with controller approval) before the task is marked complete. Do not classify dead code as Minor.` | WARRANTED | Keep — "blocking" is a status classification, not an aggression marker. The rule is precise and incident-backed (the global CLAUDE.md explicitly names dead code removal as a non-negotiable principle). |

---

## Summary

### Total Instances

| Category | Count |
|----------|-------|
| Total language instances audited | 65 |
| Warranted (keep as-is) | 15 |
| Incident-backed (preserve constraint, reduce tone) | 14 |
| Overblown (can be de-escalated) | 36 |

### Breakdown by Type

| Pattern | Count | Severity |
|---------|-------|----------|
| ALL CAPS MUST / MUST NOT | 18 | Medium — causes overtriggering per best practices doc |
| ALL CAPS other (NEVER, CRITICAL, ABSOLUTELY, MANDATORY) | 10 | Medium |
| Triple negation / "This is not X. This is not Y." | 4 | High — signals over-prompting |
| Shaming/moral accusation language (dishonesty, lying, suspiciously) | 5 | High — inappropriate for process docs |
| EXTREMELY-IMPORTANT / ABSOLUTELY MUST block | 1 block (~5 sentences) | Critical — direct overtrigger risk |
| Redundant emphasis pairs (MUST + bold, REQUIRED + CRITICAL) | 8 | Low-Medium |

### Priority Files

**Priority 1 — Highest overtrigger risk / most aggressive:**

1. `skills/using-superpowers/SKILL.md` — The `<EXTREMELY-IMPORTANT>` block with "YOU DO NOT HAVE A CHOICE" and "This is not negotiable" is exactly the pattern the best practices doc warns against. This is likely the most direct contributor to skill overtriggering on 4.6.

2. `skills/subagent-driven-development/SKILL-v0.1.md` — Review Enforcement section has incident-backed justification but the delivery (uppercase YOU MUST NOT, triple negation) can be toned down while keeping the constraint intact.

3. `skills/verification-before-completion/SKILL.md` — Shaming language ("dishonesty", "lying") + Iron Law box + triple negation. The behavioral constraint is correct; the moral framing is counter-productive.

**Priority 2 — Moderate, straightforward fixes:**

4. `skills/systematic-debugging/SKILL.md` — "ALWAYS find root cause" + "violating the spirit" preemptive challenge.

5. `skills/test-driven-development/SKILL.md` — "Delete means delete" + "You skipped TDD. Start over." shaming + two MANDATORY labels.

6. `skills/subagent-driven-development/spec-reviewer-prompt-v0.1.md` — "CRITICAL: Do Not Trust the Report" + "finished suspiciously quickly."

**Priority 3 — Minor, mechanical fixes:**

7. `skills/writing-plans/SKILL-v0.1.md` — Four MUST instances that can become imperative or "should".

8. `skills/brainstorming/SKILL-v0.1.md` — Three MUST instances outside the CRITICAL CONSTRAINT block.

9. `skills/executing-plans/SKILL.md`, `skills/handoff-acceptance/SKILL.md`, `skills/writing-skills/SKILL.md` — One to two instances each.

### Warranted Intensity: What to Keep

The following uses of strong language are appropriate and should be preserved:

- `## CRITICAL CONSTRAINT` header in `brainstorming/SKILL-v0.1.md` (replaces `<HARD-GATE>`, is a genuine blocking gate)
- `[BLOCKING]` status labels in `handoff-acceptance/SKILL.md` (these are status classifiers, not intensity)
- The rationalization lists in both `subagent-driven-development/SKILL-v0.1.md` and `using-superpowers/SKILL.md` (specific examples with named rationalizations are valuable and can stay)
- Dead code rule in `code-quality-reviewer-prompt-v0.1.md` ("blocking" is a classification)
- "There is no 'just this once'" in the SDD Review Enforcement section (clear principle statement, not a shout)
- "Do NOT change production code" in dispatching-parallel-agents agent prompt examples (this is in a code block showing agent instructions, not skill prose)

### Calibration Note

The `brainstorming/SKILL-v0.1.md` `## CRITICAL CONSTRAINT` section (lines 12–14) represents a well-calibrated gate. The header is strong but the body uses "Do NOT" (not DO NOT in caps) and explains the scope clearly. This is the target pattern for other blocking constraints — not softened away, but not shouted either.

The spectrum for de-escalation should be:
- Iron Law boxes: Convert UPPERCASE box to bold block with clear rule statement
- MUST: Convert to imperative verb or "should" depending on whether it's a hard constraint or guidance
- "This is not optional / This is not negotiable": Remove when the constraint is already stated; keep only when the constraint might genuinely be misread as optional
- Shaming language: Replace with factual consequence statements in all cases
