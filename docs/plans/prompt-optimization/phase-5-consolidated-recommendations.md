# Prompt Optimization — Consolidated Recommendations

**Date:** 2026-03-23
**Consolidates:** Areas 1–8 (8 audit reports)
**Status:** Research only — no skill files modified

---

## Executive Summary

Eight audit reports covering 15 skill files and 4 prompt templates identified 171 distinct recommendations across description quality, XML tag naming, role identity, language de-escalation, positive framing, motivation additions, template agentic patterns, and thinking guidance. The most impactful changes are Tier 1 (description fixes and XML renames — low risk, direct behavioral improvement) and the highest-risk item in the entire audit is the `<EXTREMELY-IMPORTANT>` block in `using-superpowers/SKILL.md`, which Area 1 identifies as the most direct overtrigger risk for Claude 4.6. Tier 2 (de-escalation + positive framing) and Tier 3 (motivation + thinking guidance + template additions) are content improvements that require judgment but have no conflicts between areas.

---

## Overlap Resolution

The following passages are touched by two or more areas. Resolutions are noted.

### 1. `using-superpowers/SKILL.md` — `<EXTREMELY-IMPORTANT>` block (lines 10–16)

**Areas:** Area 1 (de-escalation), Area 2 (positive framing), Area 5 (XML tags)

**Area 1 proposal:** Remove the entire block; replace with: "If a skill applies to your task, invoke it. When in doubt about whether a skill applies, invoke it to check — if it turns out to be the wrong skill, you don't need to use it."

**Area 2 proposal:** Replace `<EXTREMELY-IMPORTANT>` with `<important>`, rewrite content to be positive-led: "When a skill applies to your task, invoke it before responding. When in doubt — even a small chance a skill applies — invoke it to check. If the invoked skill turns out not to fit, you do not need to follow it."

**Area 5 proposal:** Rename `<EXTREMELY-IMPORTANT>` → `<mandatory>` (lowercase-with-hyphens).

**Resolution:** Take Area 2's proposed replacement verbatim (it fully incorporates Area 1's de-escalation AND produces a positive-framed rewrite). The XML tag name: Area 5 proposed `<mandatory>`; Area 2 used `<important>`. **Use `<important>`** — it is shorter, more descriptive of the block's actual function (not a gate, but a priority instruction), and is proposed by the report that actually rewrites the content. This is the single highest-priority change in the entire audit.

---

### 2. `subagent-driven-development/SKILL-v0.1.md` — Review Enforcement section (line 284)

**Areas:** Area 1 (de-escalation), Area 2 (positive framing)

**Area 1 proposal:** Convert `**YOU MUST NOT SKIP REVIEWS FOR ANY REASON.**` to `**Do not skip reviews for any reason.**`; remove the triple negation ("This is not a guideline. This is not optional...").

**Area 2 proposal:** Reframe to positive-led: `**Run spec compliance and code quality review after every task, without exception.**`

**Resolution:** Combine. Area 2's positive reframe is the better opener. Area 1's triple-negation removal is subsumed. **Use:** `**Run spec compliance and code quality review after every task, without exception.**` followed by the rationalization list (renamed per Area 1 to "Rationalizations that don't override the requirement:").

---

### 3. `subagent-driven-development/SKILL-v0.1.md` — Red Flags "Never" list (lines 443–454)

**Areas:** Area 1 (de-escalation), Area 2 (positive framing)

**Area 1 proposal:** Reformulate `**Start code quality review before spec compliance is PASS**` to remove bold-capitalization combination.

**Area 2 proposal:** Convert the entire 11-item "Never" list to a "Required practices" positive-framed list.

**Resolution:** Take Area 2's full positive rewrite (it naturally resolves Area 1's specific item flag as a side effect). The positive "Required practices" list is provided in full in the Area 2 report and should be used verbatim.

---

### 4. `receiving-code-review/SKILL.md` — "Forbidden Responses" section (lines 28–38)

**Areas:** Area 1 (de-escalation — "NEVER" header, shaming parenthetical), Area 2 (positive framing — convert to "Response Pattern")

**Area 1 proposal:** Change `**NEVER:**` to `**Avoid:**` or `**Don't:**`; remove "(explicit CLAUDE.md violation)" parenthetical.

**Area 2 proposal:** Rename section to "Response Pattern," lead with "Do:" list, demote prohibited phrases to a secondary "Avoid performative openers:" block.

**Resolution:** Take Area 2's full structural rewrite (it achieves Area 1's header and parenthetical removals as side effects while improving framing direction). Section header: `## Response Pattern`.

---

### 5. `receiving-code-review/SKILL.md` — "Acknowledging Correct Feedback" / "DELETE IT" (line 139–148)

**Areas:** Area 1 (de-escalation — "DELETE IT"), Area 2 (positive framing — consolidate ❌ list)

**Area 1 proposal:** `**If you start to write "Thanks":** Skip it. State the fix instead.`

**Area 2 proposal:** Consolidate five ❌ bullets into one explanatory sentence; use Area 1's "Skip it" language verbatim.

**Resolution:** Take Area 2's full rewrite (it incorporates Area 1's proposed text). No conflict.

---

### 6. `subagent-driven-development/spec-reviewer-prompt-v0.1.md` — "CRITICAL: Do Not Trust the Report" section

**Areas:** Area 1 (remove "CRITICAL" header, remove "suspiciously quickly"), Area 2 (positive-led rewrite), Area 4 (thinking guidance addition), Area 8 (role statement before opening task line)

**Resolution:** Apply changes in this sequence:
1. Area 8: Insert role statement before the opening task line
2. Areas 1+2 combined: Section becomes `## Verify Independently — Do Not Trust the Report` with "Verify by:" positive list and single-sentence closing prohibition (full text in Area 2 report)
3. Area 4: Add reflection guidance after the "Changed Files" section (not inside the CRITICAL block)

No conflicts. All four areas touch different parts or layers of the same template.

---

### 7. `spec-reviewer-prompt-v0.1.md` — Opening line and role

**Areas:** Area 8 (role identity), Area 1 (indirect — de-escalates the section header), Area 2 (positive framing of the DO NOT list), Area 4 (thinking guidance additions)

**Resolution:** Area 8 inserts the role statement as the new opening paragraph, pushing "You are reviewing whether an implementation matches its specification." down to the second paragraph. Areas 1+2 combined rewrite applies to the CRITICAL section body (separate location). Area 4 adds thinking guidance after the Changed Files block. Sequence is: role statement → task line → Area 4 thinking guidance → Area 1+2 rewritten verification section.

---

### 8. `implementer-prompt-v0.1.md` — CLAUDE.md section ("CRITICAL" + positive framing)

**Areas:** Area 1 (remove "CRITICAL" caps), Area 2 (positive-led rewrite), Area 4 (Area 4 proposes adding investigate-first principle nearby), Area 8 (role statement at top)

**Resolution:** Area 8 role statement goes at the very top. Area 1+2 combined rewrite for the CLAUDE.md section (Area 2 provides the full rewrite text). Area 4 additions go in their specified locations (Source Files section, Your Job section). No conflicts — they touch different sections of the same file.

---

### 9. `writing-skills/SKILL.md` — "REQUIRED BACKGROUND" line

**Areas:** Area 1 (remove REQUIRED + MUST), Area 2 (positive framing — adds "why" clause), Area 3 (adds TDD prerequisite motivation)

**Area 1 proposal:** `**Background:** Read superpowers:test-driven-development before using this skill.`

**Area 2 proposal:** `**Background:** Understand superpowers:test-driven-development before using this skill — this skill adapts TDD's Red-Green-Refactor cycle to documentation.`

**Area 3 motivation:** Adds "The RED-GREEN-REFACTOR cycle is referenced throughout this skill by name. Without understanding what those terms mean, the checklist steps are labels without content."

**Resolution:** Take Area 2's phrasing (it already adds the motivating "why" clause). Area 3's motivation can be incorporated inline: `**Background:** Understand superpowers:test-driven-development before using this skill. The Red-Green-Refactor cycle is referenced throughout by name — without understanding what those phases mean, the checklist steps are labels without content.`

---

### 10. `brainstorming/SKILL-v0.1.md` — Anti-Pattern block and process flow

**Areas:** Area 1 (MUST → must, lowercase), Area 2 (positive framing — "Every Project Gets a Design"), Area 3 (adds motivation for "no implementation until design approved"), Area 6 (thinking guidance for clarifying questions + commit-to-design)

**Resolution:** Apply in layers. Area 2's section header rename ("Every Project Gets a Design") and body rewrite are the structural change. Area 1's MUST de-escalations within the same section are subsumed by Area 2. Area 3's motivation ("implementation without a written design produces code that encodes decisions the user hasn't reviewed") should be added as an inline explanatory sentence adjacent to the rule, not as a separate section. Area 6's thinking guidance goes in the Asking Clarifying Questions section and Presenting the Design section — separate locations. No conflicts.

---

### 11. `test-driven-development/SKILL.md` — Iron Law "No exceptions" block

**Areas:** Area 1 (soften "Delete it" / "Delete means delete"), Area 2 (positive reframe — collapse Don't list)

**Area 1 proposal:** `If you wrote code before the test, delete it and start over.` (one sentence, softer than current)

**Area 2 proposal:** `Write code before the test? Delete it and start over with a failing test.` + single "Do not" sentence collapsing the four Don't bullets + motivation "Starting from a clean slate is what makes the Red step meaningful."

**Resolution:** Take Area 2's full rewrite (it incorporates Area 1's proposed language verbatim and adds the motivating context). No conflict.

---

### 12. `verification-before-completion/SKILL.md` — Shaming language + positive framing

**Areas:** Area 1 (remove "dishonesty", "lying", "you'll be replaced"), Area 2 (positive anchors for Red Flags and Bottom Line)

**Resolution:** These touch different lines. Area 1's shaming-language removals (lines 10, 37, 115, 139) are independent of Area 2's Red Flags section header and Bottom Line rewrites. Apply both. No conflicts.

---

### 13. `systematic-debugging/SKILL.md` — Red Flags section

**Areas:** Area 1 ("ALL of these mean: STOP"), Area 2 (positive anchor before list), Area 6 (thinking guidance at Phase 1 and Phase 3)

**Resolution:** Area 1 de-escalates "ALL/STOP" to lowercase. Area 2 adds a positive framing sentence before the list and renames the section header to "Red Flags — Return to Phase 1." Area 6 adds thinking guidance at different locations (Phase 1 evidence-gathering, Phase 3 hypothesis). These are additive and non-conflicting. Apply all.

---

### 14. `writing-plans/SKILL-v0.1.md` — MUST instances

**Areas:** Area 1 (four MUST → imperative or "should"), Area 2 (confirms Area 1 proposals apply, adds write-scope partitioning positive reframe)

**Resolution:** Areas 1 and 2 converge on the same proposals for the MUST instances. Area 2 adds one additional positive reframe (Write-Scope Partitioning rules) not in Area 1. Apply both without modification.

---

### 15. `plan-document-reviewer-prompt-v0.1.md` — Opening and role

**Areas:** Area 4 (template optimization — agentic patterns), Area 8 (role identity)

**Resolution:** Area 8 replaces "You are a plan document reviewer" with the full implementation-readiness-auditor role statement. Area 4's agentic additions are within the template body. Area 8 goes first (before the task line); Area 4 additions go at their specified locations. No conflict.

---

## Per-File Changes

### Tier 1 — High Impact, Low Risk

*Description fixes (Area 7), XML tag renames (Area 5), role statement additions (Area 8)*

---

#### `skills/brainstorming/SKILL.md` (frontmatter description only)
**Areas touching this file:** Area 7
**Changes:**
1. [Area 7] `description:` field: Replace with `Use when starting any creative or implementation work — building features, adding functionality, modifying behavior, or designing components — before writing a spec or touching code.`

**Command stub update required:** See Command Stub Updates section.

---

#### `skills/finishing-a-development-branch/SKILL.md` (frontmatter description only)
**Areas touching this file:** Area 7
**Changes:**
1. [Area 7] `description:` field: Replace with `Use when implementation is complete, all tests pass, and you need to decide how to integrate the work (merge, PR, or cleanup)`

**Command stub update required:** Yes.

---

#### `skills/handoff-acceptance/SKILL.md` (frontmatter description only)
**Areas touching this file:** Area 7
**Changes:**
1. [Area 7] `description:` field: Replace with `Use when receiving code, schemas, or documentation from another agent, team, or system that will feed into brainstorming, planning, or implementation`

**Command stub update required:** Yes.

---

#### `skills/receiving-code-review/SKILL.md` (frontmatter description only)
**Areas touching this file:** Area 7
**Changes:**
1. [Area 7] `description:` field: Replace with `Use when receiving code review feedback and about to implement suggestions, especially when feedback is unclear, seems technically questionable, or conflicts with your understanding`

**Command stub update required:** Yes.

---

#### `skills/subagent-driven-development/SKILL.md` (frontmatter description only — non-v0.1)
**Areas touching this file:** Area 7
**Changes:**
1. [Area 7] `description:` field: Replace with `Use when executing an implementation plan that has independent tasks and you want each task handled by a dedicated subagent with post-task review in the current session`

**Note:** If there is no non-v0.1 SKILL.md for this skill (only SKILL-v0.1.md), apply this to the v0.1 file's frontmatter.
**Command stub update required:** Yes.

---

#### `skills/using-git-worktrees/SKILL.md` (frontmatter description only)
**Areas touching this file:** Area 7
**Changes:**
1. [Area 7] `description:` field: Replace with `Use when starting feature work that needs isolation from the current workspace, or before executing implementation plans in a dedicated directory`

**Command stub update required:** Yes.

---

#### `skills/using-superpowers/SKILL.md` (frontmatter description only)
**Areas touching this file:** Area 7
**Changes:**
1. [Area 7] `description:` field: Replace with `Use when starting any conversation, before responding to any request including clarifying questions`

**Command stub update required:** Yes.

---

#### `skills/verification-before-completion/SKILL.md` (frontmatter description only)
**Areas touching this file:** Area 7
**Changes:**
1. [Area 7] `description:` field: Replace with `Use when about to claim work is complete, fixed, or passing, before committing or creating PRs`

**Command stub update required:** Yes.

---

#### `skills/writing-plans/SKILL.md` (frontmatter description only — non-v0.1)
**Areas touching this file:** Area 7
**Changes:**
1. [Area 7] `description:` field: Replace with `Use when you have a spec or requirements for a multi-step task, before touching code`

**Command stub update required:** Yes.

---

#### `skills/executing-plans/SKILL.md` (frontmatter description — optional)
**Areas touching this file:** Area 7
**Changes:**
1. [Area 7] `description:` field: Optional trim to `Use when you have a written implementation plan ready to execute in a new session` — current version passes but has a borderline trailing clause.

**Command stub update required:** Only if description changes.

---

#### `skills/using-superpowers/SKILL.md` (body — XML tag renames)
**Areas touching this file:** Area 5, Area 1, Area 2, Area 7
**Tier 1 changes (XML renames, highest priority in entire audit):**
1. [Area 5] `<SUBAGENT-STOP>` → `<subagent-stop>` and `</SUBAGENT-STOP>` → `</subagent-stop>`
2. [Area 5 + Area 1 + Area 2 combined] Replace entire `<EXTREMELY-IMPORTANT>...</EXTREMELY-IMPORTANT>` block with:
```
<important>
When a skill applies to your task, invoke it before responding. When in doubt — even a small chance a skill applies — invoke it to check. If the invoked skill turns out not to fit, you do not need to follow it.
</important>
```

**Overlap resolution:** Area 5 proposed `<mandatory>`; Area 2 used `<important>`. Use `<important>` (the tag that accompanies the content rewrite).

---

#### `skills/test-driven-development/SKILL.md` (XML tag renames)
**Areas touching this file:** Area 5, Area 1, Area 2
**Tier 1 changes:**
1. [Area 5] `<Good>` → `<good>`, `</Good>` → `</good>` (4 occurrences)
2. [Area 5] `<Bad>` → `<bad>`, `</Bad>` → `</bad>` (4 occurrences)

---

#### `skills/writing-skills/SKILL.md` (XML tag renames)
**Areas touching this file:** Area 5, Area 1, Area 2
**Tier 1 changes:**
1. [Area 5] `<Good>` → `<good>`, `</Good>` → `</good>` (1 pair)
2. [Area 5] `<Bad>` → `<bad>`, `</Bad>` → `</bad>` (1 pair)

---

#### `skills/writing-skills/testing-skills-with-subagents.md` (XML tag renames)
**Areas touching this file:** Area 5
**Tier 1 changes:**
1. [Area 5] `<Before>` → `<good>`, `</Before>` → `</good>`
2. [Area 5] `<After>` → `<bad>`, `</After>` → `</bad>`

---

#### `skills/subagent-driven-development/implementer-prompt-v0.1.md` (role statement)
**Areas touching this file:** Area 8, Area 1, Area 2, Area 3, Area 4
**Tier 1 changes:**
1. [Area 8] Insert role statement as the new first paragraph, before "You are implementing Task N: [task name]":
```
You are a focused implementation engineer. Your job is to build exactly what the
spec asks — nothing more, nothing less. When requirements are clear, execute them
precisely. When they are ambiguous, ask before assuming.
```

---

#### `skills/subagent-driven-development/spec-reviewer-prompt-v0.1.md` (role statement)
**Areas touching this file:** Area 8, Area 1, Area 2, Area 3, Area 4
**Tier 1 changes:**
1. [Area 8] Insert role statement as the new first paragraph, before "You are reviewing whether an implementation matches its specification.":
```
You are a skeptical spec compliance auditor. Your value comes from verifying by
reading code, not by accepting reports. Assume the implementer's report is
incomplete until the code proves otherwise.
```

---

#### `skills/brainstorming/distillation-reviewer-prompt.md` (role statement)
**Areas touching this file:** Area 8
**Tier 1 changes:**
1. [Area 8] Insert role statement as the new first paragraph, before "You are verifying that a distilled spec accurately represents the decisions from a full design document.":
```
You are a precision editor verifying distillation fidelity. Your job is to check
whether decisions were preserved accurately — not to re-evaluate them. A decision
you disagree with is not a finding; a decision that was lost or inverted is.
```

---

#### `skills/brainstorming/spec-document-reviewer-prompt.md` (role statement)
**Areas touching this file:** Area 8
**Tier 1 changes:**
1. [Area 8] Replace "You are a spec document reviewer. Verify this spec is complete and ready for planning." with:
```
You are a design quality auditor evaluating whether a spec is ready for implementation
planning. Your standard is planning-readiness, not perfection — flag gaps that would
cause a planner to build the wrong thing, not gaps that are merely incomplete or
stylistically imperfect.

Verify this spec is complete and ready for planning.
```

---

#### `skills/writing-plans/plan-document-reviewer-prompt-v0.1.md` (role statement)
**Areas touching this file:** Area 8, Area 4
**Tier 1 changes:**
1. [Area 8] Replace "You are a plan document reviewer. Verify this plan is complete and ready for implementation." with:
```
You are an implementation readiness auditor. Your job is to catch plan defects before
they reach subagents — type mismatches, wrong field names, unverified code snippets,
and gaps that would cause an implementer to build the wrong thing. A single type
mismatch that looks minor can propagate to production bugs; treat contract accuracy
as the highest-stakes check in this review.

Verify this plan is complete and ready for implementation.
```

---

### Tier 2 — Medium Impact, Requires Judgment

*De-escalation (Area 1) and positive framing (Area 2), applied together per overlap resolutions*

---

#### `skills/using-superpowers/SKILL.md` (body — language changes)
**Areas:** Area 1, Area 2
**Tier 2 changes** (beyond Tier 1 XML changes above):
1. [Area 1] Line ~44: Normalize `**Invoke relevant or requested skills BEFORE any response or action.** Even a 1% chance a skill might apply means that you should invoke the skill.` to: `Invoke relevant or requested skills before any response or action. When in doubt — even a small chance a skill applies — invoke it to check.`
2. [Area 2] Red Flags section header: Change `## Red Flags` + "These thoughts mean STOP—you're rationalizing:" to `## When to Invoke Skills` + "These situations all call for checking skills first:" and rename the "Reality" column to "Why skills apply"

---

#### `skills/subagent-driven-development/SKILL-v0.1.md`
**Areas:** Area 1, Area 2
**Tier 2 changes:**
1. [Area 1+2 combined — Overlap #2] Line 152: Replace "Before dispatching any subagent, the controller MUST complete a full plan ingestion pass. This is not optional." with: "Before dispatching any subagent, complete a full plan ingestion pass — all sections are load-bearing."
2. [Area 1] Line 189: `it MUST be the first item` → `it should be the first item`
3. [Area 1] Line 206: `the controller MUST include` → `include` (remove MUST, direct imperative)
4. [Area 1] Line 210: Remove "This passthrough is not optional." entirely
5. [Area 1+2 combined — Overlap #2] Line 284: Replace `**YOU MUST NOT SKIP REVIEWS FOR ANY REASON.**` + triple negation paragraph with: `**Run spec compliance and code quality review after every task, without exception.**`; rename following list to `**Rationalizations that don't override the requirement:**`
6. [Area 2 — Overlap #3] Lines 443–454: Replace entire 11-item "Never:" list with the positive "Required practices:" list (full text in Area 2 report, section "Red Flags — Never list")

---

#### `skills/subagent-driven-development/spec-reviewer-prompt-v0.1.md`
**Areas:** Area 1, Area 2
**Tier 2 changes:**
1. [Area 1+2 combined — Overlap #6] Replace `## CRITICAL: Do Not Trust the Report` section entirely with the Area 2 rewrite:
   - Section header: `## Verify Independently — Do Not Trust the Report`
   - Remove "The implementer finished suspiciously quickly." sentence
   - Convert to "Verify by:" positive list
   - Single closing "Do not rely on the implementer's word..." sentence
   - (Full text in Area 2 report, spec-reviewer-prompt section)

---

#### `skills/verification-before-completion/SKILL.md`
**Areas:** Area 1, Area 2
**Tier 2 changes:**
1. [Area 1] Line 10: `Claiming work is complete without verification is dishonesty, not efficiency.` → `Claiming work is complete without verification is inaccurate, not efficient.`
2. [Area 1] Line 14: Remove "**Violating the letter of this rule is violating the spirit of this rule.**" entirely
3. [Area 1] Line 37: `Skip any step = lying, not verifying` → `All five steps are required — skipping any step produces an unverified claim, not a completion.` (incorporates Area 2's positive anchor)
4. [Area 1] Line 115: Remove or replace "Violates: 'Honesty is a core value. If you lie, you'll be replaced.'" with: "Unverified completion claims have historically led to re-work and broken trust."
5. [Area 1] Line 139: Remove "This is non-negotiable."
6. [Area 2] Red Flags section: Rename `## Red Flags - STOP` to `## Red Flags — Run Verification First`; add framing sentence: "When any of these patterns appear, run the verification step before continuing:"
7. [Area 2] Bottom Line: Consolidate to: `Run the command. Read the output. Then claim the result — in that order, every time.`

---

#### `skills/systematic-debugging/SKILL.md`
**Areas:** Area 1, Area 2
**Tier 2 changes:**
1. [Area 1] Line 12: `**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.` → `**Core principle:** Find root cause before attempting fixes. Symptom fixes mask the real problem.`
2. [Area 1] Line 14: Remove "**Violating the letter of this process is violating the spirit of debugging.**" entirely
3. [Area 1] Line 48: `You MUST complete each phase before proceeding to the next.` → `Complete each phase before proceeding to the next.`
4. [Area 1+2 combined] Line 230: Change `**ALL of these mean: STOP. Return to Phase 1.**` to `**Any of these means: stop and return to Phase 1.**`; rename section header to `## Red Flags — Return to Phase 1`; add framing sentence before list: "When any of these thoughts appear, stop and return to Phase 1 (Root Cause Investigation) before proceeding:"
5. [Area 2] Merge "Don't skip when:" block (3 items) into existing "Use this ESPECIALLY when:" block as additional entries; remove "Don't skip when:" block

---

#### `skills/test-driven-development/SKILL.md`
**Areas:** Area 1, Area 2
**Tier 2 changes:**
1. [Area 1] Line 14: Remove "**Violating the letter of the rules is violating the spirit of the rules.**" entirely
2. [Area 1] Line 29: `Thinking "skip TDD just this once"? Stop. That's rationalization.` → `If you're thinking about skipping TDD "just this once," that's a rationalization.`
3. [Area 1+2 combined — Overlap #11] Lines 39–45 "No exceptions" block: Replace with: `Write code before the test? Delete it and start over with a failing test.` + `Delete completely — do not keep it as reference, adapt it while writing tests, or consult it for guidance. Starting from a clean slate is what makes the Red step meaningful.`
4. [Area 1] Line 115: `**MANDATORY. Never skip.**` → `**Required. Do not skip.**`
5. [Area 1] Line 170: `**MANDATORY.**` → `**Required.**`
6. [Area 1+2 combined — Overlap #11 continuation] Line 340: Replace `Can't check all boxes? You skipped TDD. Start over.` with: `All boxes checked? TDD was followed — mark the work complete.` + `If any box is unchecked, TDD was not followed. Start over.`
7. [Area 2] Red Flags section: Rename `## Red Flags - STOP and Start Over` to `## Red Flags — Start Over with TDD`; add framing sentence: "When any of these patterns appear, delete the code and restart with a failing test:"

---

#### `skills/receiving-code-review/SKILL.md`
**Areas:** Area 1, Area 2
**Tier 2 changes:**
1. [Area 1+2 combined — Overlap #4] Convert "Forbidden Responses" section to "Response Pattern" with "Do:" positive list leading, "Avoid performative openers:" list secondary (full text in Area 2 report)
2. [Area 1+2 combined — Overlap #5] Consolidate "Acknowledging Correct Feedback" ❌ list; use Area 2's rewrite: explanatory sentence replacing five bullet points (full text in Area 2 report)

---

#### `skills/brainstorming/SKILL-v0.1.md`
**Areas:** Area 1, Area 2
**Tier 2 changes:**
1. [Area 1+2 combined — Overlap #10] Rename "Anti-Pattern" section to "Every Project Gets a Design"; rewrite body per Area 2 (full text in Area 2 report)
2. [Area 1] Line 18: `you MUST present it and get approval` → `present it and get approval`
3. [Area 1] Line 22: `You MUST create a task for each of these items` → `Create a task for each of these items`
4. [Area 1] Line 208: `**This offer MUST be its own message.**` → `**This offer should be its own message.**`
5. [Area 2] Process Flow terminal state: Replace `**The terminal state is invoking writing-plans.** Do NOT invoke frontend-design, mcp-builder, or any other implementation skill. The ONLY skill you invoke after brainstorming is writing-plans.` with: `**The terminal state is invoking writing-plans.** After brainstorming, the next skill is always writing-plans — not frontend-design, mcp-builder, or any other implementation skill.`

---

#### `skills/writing-plans/SKILL-v0.1.md`
**Areas:** Area 1, Area 2
**Tier 2 changes:**
1. [Area 1] Line 27: `it MUST be decomposed into independent modules` → `decompose it into independent modules`
2. [Area 1] Line 142: `MUST include this section before the task list` → `Include this section before the task list`
3. [Area 1] Line 164: `Every plan MUST classify its feature archetype` → `Every plan should classify its feature archetype`
4. [Area 1] Line 198: `Task 0 is mandatory` → `include a Task 0 (Contract Verification)`
5. [Area 2] Write-Scope Partitioning Rules: Reorder to lead with the positive invariant (`Each file appears in exactly one task's "Owned Files" column`) and convert the two prohibitions to positive form (full rewrite in Area 2 report)

---

#### `skills/writing-skills/SKILL.md`
**Areas:** Area 1, Area 2
**Tier 2 changes:**
1. [Area 1+2+3 combined — Overlap #9] Line 17: Replace "REQUIRED BACKGROUND: You MUST understand superpowers:test-driven-development before using this skill." with: `**Background:** Understand superpowers:test-driven-development before using this skill. The Red-Green-Refactor cycle is referenced throughout by name — without understanding what those phases mean, the checklist steps are labels without content.`
2. [Area 2] Lines 385–392 "No exceptions" block: Replace with: `**No exceptions.** Delete untested skill content and start over — for simple additions, new sections, and documentation updates alike. Do not keep untested changes as reference or adapt them while testing.`
3. [Area 2] "STOP: Before Moving to Next Skill" block: Replace with: `**After writing any skill, complete the deployment checklist before moving on.**` + positive one-at-a-time instruction + analogical motivation (full text in Area 2 report)

---

#### `skills/executing-plans/SKILL.md`
**Areas:** Area 1
**Tier 2 changes:**
1. [Area 1] Line 36: `**REQUIRED SUB-SKILL:** Use superpowers:finishing-a-development-branch` → `**Sub-skill required:** Use superpowers:finishing-a-development-branch`
2. [Area 1] Line 68: `**superpowers:using-git-worktrees** - REQUIRED: Set up isolated workspace before starting` → `**superpowers:using-git-worktrees** — Set up isolated workspace before starting`

---

#### `skills/handoff-acceptance/SKILL.md`
**Areas:** Area 1
**Tier 2 changes:**
1. [Area 1] Line 21: `the controller (or a dispatched reviewer subagent) MUST verify each item` → `the controller (or a dispatched reviewer subagent) should verify each item`

---

#### `skills/using-git-worktrees/SKILL.md`
**Areas:** Area 1
**Tier 2 changes:**
1. [Area 1] Lines 55–56: `**MUST verify directory is ignored before creating worktree:**` → `**Verify directory is ignored before creating worktree:**`

---

### Tier 3 — Content Additions

*Motivation (Area 3), template agentic patterns (Area 4), thinking guidance (Area 6)*

---

#### `skills/subagent-driven-development/implementer-prompt-v0.1.md`
**Areas:** Area 3, Area 4
**Tier 3 changes:**
1. [Area 3] After `DONE_WITH_CONCERNS` status instruction, add: "The controller uses DONE_WITH_CONCERNS as a routing signal. DONE triggers a standard review path; DONE_WITH_CONCERNS triggers reading the deviations before review, not after. A DONE report with concerns buried in the body will be reviewed without the controller knowing to look for them."
2. [Area 4] In "Source Files" section, after existing source-file reading instruction, add investigate-first generalization: "More broadly: never write code that assumes something about the codebase without verifying it first. If you are unsure about a type, an existing function, or a file's structure, read it before proceeding."
3. [Area 4] After above, add reflection instruction: "After reading source files, take a moment to verify your understanding is correct before writing any code. If what you read contradicts the task description or your assumptions, surface the conflict — do not silently work around it."
4. [Area 4] In "Your Job" section, add parallel-reads instruction before item 1: "When you need to read multiple files to build context, read them in parallel rather than sequentially — this reduces context usage and speeds up your work."
5. [Area 4] In "Your Job" section, after item 4 (Commit), add: "Clean up any temporary files, test scripts, or scratch files you created during implementation — they should not appear in your final commit."

---

#### `skills/subagent-driven-development/spec-reviewer-prompt-v0.1.md`
**Areas:** Area 3, Area 4
**Tier 3 changes:**
1. [Area 3] Adjacent to the "verify against the constraint, not the test" rule, add: "Test fixtures in subagent implementations are written by the same subagent that wrote the code. If the subagent used the wrong type, the fixture will match the wrong type — both will be wrong together. Test passage proves internal consistency, not external contract compliance."
2. [Area 3] Adjacent to the "Did they read CLAUDE.md files?" check, add: "If the implementer skipped the CLAUDE.md step, they may have used wrong component patterns, typography variants, or anti-patterns specific to that part of the codebase. These are spec violations for codebases where the CLAUDE.md defines the implementation contract."
3. [Area 4] After the "Changed Files" section, before "What Implementer Claims They Built," add reflection guidance: "Before forming any findings, read all changed files. Build a complete picture of what was implemented before evaluating whether it matches the spec. Findings formed after reading only part of the diff frequently miss context that changes the verdict."
4. [Area 4] In the "Changed Files" section, after the git diff instruction, add parallel-reads note: "When multiple files changed, read them in parallel where possible — run git diff and read all changed files simultaneously rather than one at a time."
5. [Area 4] In the "Report" section, after PASS/FAIL taxonomy, add confidence qualifier for uncertain findings (full text: the [UNVERIFIED] label block in Area 4 report, spec-reviewer Addition 3)

---

#### `skills/subagent-driven-development/code-quality-reviewer-prompt-v0.1.md`
**Areas:** Area 4
**Tier 3 changes:**
1. [Area 4] After the contract compliance bullet, add confidence qualifier: "For any finding where you cannot confirm the severity without additional context, label it as [NEEDS_CONTEXT] and describe what context would confirm or dismiss it. Do not classify uncertain findings as Minor to avoid surfacing them — surface them with the [NEEDS_CONTEXT] label instead."

---

#### `agents/code-reviewer.md`
**Areas:** Area 4
**Tier 3 changes:**
1. [Area 4] Before "When reviewing completed work, you will:", add investigate-first + parallel reads instruction (full text in Area 4 report, agents/code-reviewer.md Addition 1)
2. [Area 4] In Communication Protocol section, add as item 7: reflection before writing findings (full text in Area 4 report, Addition 2)
3. [Area 4] In Issue Identification section, after Critical/Important/Suggestions taxonomy, add NEEDS_CONTEXT finding label (full text in Area 4 report, Addition 3)

---

#### `skills/executing-plans/SKILL.md`
**Areas:** Area 3
**Tier 3 changes** (motivation additions):
1. [Area 3] Adjacent to "Never start on main/master without consent" rule, add: "A failed plan execution mid-stream on main leaves the repo in a partial state with no clean rollback path."
2. [Area 3] Adjacent to "Don't skip verifications" rule, add: "Verifications in the plan are the only objective confirmation that a step produced the expected artifact — skipping them means proceeding with unverified state."
3. [Area 3] Adjacent to "Reference skills when plan says to" rule, add: "Skills encode additional guardrails the plan author relied on — invoking them is how those guardrails apply."
4. [Area 3] Adjacent to "Don't force through blockers — stop and ask" rule, add: "Forcing through a blocker means every subsequent task builds on a broken foundation — the cost of not stopping compounds with each additional task."
5. [Area 3] Adjacent to "Follow plan steps exactly," add: "Plan steps were written with full codebase context. Deviating mid-execution without consultation introduces assumptions the plan author couldn't anticipate."

---

#### `skills/finishing-a-development-branch/SKILL.md`
**Areas:** Area 3
**Tier 3 changes** (motivation additions):
1. [Area 3] Adjacent to "Present exactly 4 options" rule, add: "Fewer than 4 options omits real workflows; more than 4 triggers decision paralysis. The 4 options cover every real completion path."
2. [Area 3] Adjacent to "Don't add explanation — keep options concise" rule, add: "At completion the human already knows what was built. Explanation restates what they know; the decision is the only new information needed."
3. [Area 3] Adjacent to "Require typed 'discard' confirmation" rule, add: "Typed confirmation prevents accidental discard from ambiguous affirmations like 'yes' or 'ok' that could be leftover from a prior question."
4. [Area 3] Adjacent to the worktree cleanup logic (Options 1 and 4 only), add: "Options 2 and 3 both leave the branch alive — the worktree may still be needed for additional commits or investigation after the PR is created."

---

#### `skills/dispatching-parallel-agents/SKILL.md`
**Areas:** Area 3
**Tier 3 changes** (motivation additions):
1. [Area 3] Adjacent to "Don't change other code" constraint in agent prompt structure section, add: "Subagents have no session context. Without an explicit constraint, a subagent that needs to refactor shared code will do so, creating conflicts with other parallel agents writing to the same files."
2. [Area 3] Adjacent to required output format ("Summary of what you found and fixed"), add: "The controller must synthesize multiple agent results and verify no conflicts. Summaries without a consistent structure cannot be compared reliably — the controller needs each agent's scope and changes in a predictable format."

---

#### `skills/using-git-worktrees/SKILL.md`
**Areas:** Area 3
**Tier 3 changes** (motivation additions):
1. [Area 3] Adjacent to the verify-then-commit-gitignore sequence, add: "Committing the .gitignore update before creating the worktree ensures the worktree contents are excluded from the very first `git status` — doing it after creates a window where worktree contents appear as untracked files."
2. [Area 3] Adjacent to "Run project setup (npm install / cargo build / etc.)" step, add: "Worktrees share the repo but not node_modules or build artifacts. Skipping setup causes the baseline test run to fail for the wrong reason — missing dependencies rather than actual bugs."
3. [Area 3] Adjacent to "Report failures, ask whether to proceed" instruction, add: "Some repos have pre-existing failures on main. The human needs to confirm whether the failures are known and safe to work around, or indicators the worktree setup is wrong."

---

#### `skills/handoff-acceptance/SKILL.md`
**Areas:** Area 3
**Tier 3 changes** (motivation additions):
1. [Area 3] Adjacent to the "If no fixtures exist, the receiving agent must create them" instruction, add: "Fixtures created from descriptions are the minimum bar for verifying the handoff is internally consistent. Without them, type assumptions from the handoff propagate directly into implementation — the same failure mode the BLOCKING fixture check exists to prevent."

---

#### `skills/receiving-code-review/SKILL.md`
**Areas:** Area 3
**Tier 3 changes** (motivation additions):
1. [Area 3] Adjacent to "Push back with technical reasoning, not defensiveness" rule, add: "Defensive pushback triggers the human to defend their feedback rather than evaluate the technical argument. Framing as a technical question opens the door to 'you're right, I missed that.'"
2. [Area 3] Adjacent to the "Reply in the comment thread" (GitHub Thread Replies) rule, add: "Top-level PR comments appear as general comments, not threaded replies — reviewers lose the inline context of which line triggered the response."

---

#### `skills/requesting-code-review/SKILL.md`
**Areas:** Area 3, Area 2
**Tier 2 changes:**
1. [Area 2] Replace "Never:" list with "Required:" positive list: Fix Critical immediately, Fix Important before next task, accept valid feedback or push back with reasoning (full text in Area 2 report)

**Tier 3 changes:**
1. [Area 3] Adjacent to "Skip review because 'it's simple'" rule (now in positive form per Tier 2 change), add: "The statement-reconciliation incident traced 3 production bugs to tasks that seemed simple — the simplicity was why no one looked carefully."
2. [Area 3] Adjacent to the triage priority (Critical/Important/Minor order), add: "Critical issues have cascading effects — an architecture error in Task 2 makes Tasks 3–6 wrong too. Addressing them immediately prevents compound rework."

---

#### `skills/using-superpowers/SKILL.md`
**Areas:** Area 3
**Tier 3 changes** (motivation additions):
1. [Area 3] Adjacent to "Never use the Read tool on skill files" rule, add: "The Read tool loads file content into the conversation context, consuming tokens and bypassing the skill loading mechanism. The Skill tool loads the skill cleanly and registers it as active — Read just dumps text."
2. [Area 3] Adjacent to "Process skills first" ordering instruction, add: "Implementation skills applied before process skills produce a local-optimum solution to the wrong problem. Brainstorming and debugging change the frame — running them after you've started implementation means the frame change requires rework."
3. [Area 3] Adjacent to "Skills evolve. Read current version." rule, add: "Skills in this fork are actively maintained and modified based on production incidents. The version in memory may predate a fix for the exact failure mode you're about to encounter."

---

#### `skills/verification-before-completion/SKILL.md`
**Areas:** Area 3
**Tier 3 changes** (motivation additions):
1. [Area 3] Adjacent to "If you haven't run the verification command in this message, you cannot claim it passes," add: "Test results from previous messages may be stale — code changes between messages invalidate prior run results. 'This message' is the freshness guarantee."
2. [Area 3] Adjacent to "Trusting agent success reports" in Red Flags list, add: "Agent reports describe what the agent attempted, not what the code does. Agents can report DONE on partially-completed work, on work that passed wrong-assumption tests, or on work that doesn't wire into the consuming code."
3. [Area 3] Adjacent to "Rule applies to: Exact phrases / Paraphrases and synonyms / Implications of success," add: "Incomplete verification expressed in hedged language ('should pass', 'looks right') has caused the same downstream failures as explicit false claims. The rule covers substance, not phrasing."

---

#### `skills/writing-skills/SKILL.md`
**Areas:** Area 3
**Tier 3 changes** (motivation additions — beyond Tier 2 prerequisite line already handles writing-skills motivation #1):
1. [Area 3] Adjacent to "Name uses only letters, numbers, hyphens" rule, add: "Special characters in skill names cause failures in shell scripts and the command stub generation loop — the `for dir in skills/*/` pattern breaks on names with parentheses or spaces."
2. [Area 3] Adjacent to "Do NOT: Create multiple skills in batch without testing each," add: "Each skill iteration may reveal rationalizations that feed into the next skill's design. Writing 5 skills without testing means 4 of them were written blind to the failure modes that test 1 would have exposed."

---

#### `skills/systematic-debugging/SKILL.md`
**Areas:** Area 3, Area 6
**Tier 3 changes:**
1. [Area 3] Adjacent to "Complete each phase before proceeding," add: "Each phase depends on outputs from the prior. Phase 2 (pattern analysis) requires a reproducible symptom from Phase 1. Phase 3 (hypothesis) requires knowing what's different between working and broken cases from Phase 2. Jumping ahead means forming hypotheses about unknown unknowns."
2. [Area 3] Adjacent to "ONE change at a time / No 'while I'm here' improvements," add: "Multiple simultaneous changes make it impossible to attribute a regression to the fix that caused it. If tests break after a bundle of changes, you must revert everything and re-apply one at a time — losing the work twice."
3. [Area 3] Adjacent to "Discuss with your human partner before attempting more fixes," add: "Three failed fixes is the signal that the problem is architectural, not a local bug. Architectural problems require design decisions that exceed the debugging skill's scope — continuing without consultation means making design decisions without the human's input or buy-in."
4. [Area 6] After Phase 1 evidence-gathering subsection, add: "After running diagnostic instrumentation and gathering evidence, pause before moving to Phase 2. Ask: Do I know which component boundary is failing? If yes, proceed. If not, identify what additional evidence is needed — then gather only that before moving on."
5. [Area 6] Before or within "Form Single Hypothesis" step in Phase 3, add: "State your hypothesis before testing it. Once stated, commit to testing it fully before reconsidering. If the hypothesis is wrong, revise based on new evidence — not before."

---

#### `skills/brainstorming/SKILL-v0.1.md`
**Areas:** Area 3, Area 6
**Tier 3 changes:**
1. [Area 3] Adjacent to "Do NOT invoke any implementation skill" gate, add: "Implementation without a written design produces code that encodes decisions the user hasn't reviewed. Reversing those decisions after code exists costs significantly more than iterating on a spec."
2. [Area 3] Adjacent to "The ONLY skill you invoke after brainstorming is writing-plans," add: "Frontend-design, mcp-builder, and other implementation skills each assume the design is settled. Invoking them during brainstorming bypasses the design review step and prematurely closes options the user may want to revisit."
3. [Area 3] Adjacent to "Identify the feature archetype early," add: "Archetype identification determines what the spec needs to document. A replacement archetype requires obsolescence tracking; a refactor requires consumer verification. Identifying it late means retrofitting the spec after design is done."
4. [Area 6] In the "Asking clarifying questions" section, add: "After 3–4 clarifying questions, assess whether you have enough to propose approaches. You do not need complete information to propose — you need enough to identify the main trade-off. Choose your leading approach based on what you know and propose it. Gaps can be filled during design review."
5. [Area 6] In the "Presenting the design" section, before "Write design doc," add: "Once the user has approved the design direction, commit to it. Write the spec from the approved design — do not re-open architectural questions during the writing phase. If a new concern emerges while writing, note it as a decision to surface after the spec is written, not a reason to restart the design."

---

#### `skills/writing-plans/SKILL-v0.1.md`
**Areas:** Area 3, Area 6
**Tier 3 changes:**
1. [Area 3] Adjacent to "Each file should have one clear responsibility with a well-defined interface," add: "Subagents implement one task at a time. A file with multiple responsibilities will be partially owned by multiple tasks — both tasks will touch it, requiring serialization and increasing the chance of merge conflicts between task commits."
2. [Area 3] Adjacent to "Exact file paths always" rule, add: "Subagents receiving a task prompt do not have your codebase knowledge. An ambiguous path like 'the router file' forces them to search the repo before implementing. Exact paths eliminate that ambiguity and reduce the chance of the subagent editing the wrong file."
3. [Area 3] Adjacent to "Complete code in plan (not 'add validation')" rule, add: "Vague instructions leave the implementation decision to the subagent, who has no context about your validation patterns, error message formats, or existing validators. The plan should encode those decisions — the subagent should execute them, not make them."
4. [Area 6] Before the "Write the tasks" section, add reflect-then-commit guidance: "Before writing tasks, read the core files your plan will modify. After each read, assess whether you now understand the relevant interfaces, naming conventions, and file ownership. When you can answer 'where does this logic live and what does it touch?' for each task in the plan, you have enough context. Do not read more files beyond that — write from what you know."
5. [Area 6] After the Write-Scope Partitioning section, add: "Once you have written the Write-Scope Partitioning table, treat task ownership as settled. Do not revise file assignments mid-plan — if a conflict is discovered later, add a serialization dependency rather than re-partitioning."

---

#### `skills/subagent-driven-development/SKILL-v0.1.md`
**Areas:** Area 3, Area 6
**Tier 3 changes:**
1. [Area 3] Adjacent to "Do not paraphrase it [Contract Constraints]" rule, add: "Paraphrasing contract constraints introduces interpretation. A constraint like 'all amounts are strings' paraphrased as 'handle amounts carefully' loses the specific type information the subagent needs to implement correctly."
2. [Area 3] Adjacent to "Dispatch multiple implementation subagents in parallel (conflicts)" in Red Flags, add: "Parallel subagents write to files simultaneously. Without coordination, one subagent's commit will be overwritten by another's. The Write-Scope Partitioning table resolves this, but only if subagents are dispatched sequentially."
3. [Area 3] Adjacent to "Try to fix a failed task manually (context pollution)" rule, add: "When the controller edits files directly to fix a failed task, it accumulates session context about implementation details that should belong to a fresh subagent. This context bleeds into subsequent task dispatches and spec reviews, making the controller a less reliable evaluator of its own work."
4. [Area 3] Adjacent to "Declare review tier before dispatching" rule, add: "Declaring tier before dispatch forces the controller to make an explicit risk assessment before it sees the implementer's report. Deciding tier after seeing the report introduces post-hoc rationalization — 'the report looks clean, minimum review is fine.'"
5. [Area 6] In the Plan Ingestion section, after the read-all-sections instruction, add: "Plan ingestion is a one-pass activity. Read the plan, read the source contracts if present, extract what you need — then start the task loop. Do not read additional codebase files beyond what the plan's Contract Constraints reference. Your job in this phase is to understand the plan, not to verify it against the codebase."
6. [Area 6] In the task loop section, after the two-stage review description, add: "After spec compliance and code quality reviews both pass, mark the task complete and move to the next one. Do not re-examine completed task output or re-read implementation files between tasks — the review is the completion gate."

---

#### `skills/test-driven-development/SKILL.md`
**Areas:** Area 3, Area 6
**Tier 3 changes:**
1. [Area 3] Adjacent to "Don't add features, refactor other code, or 'improve' beyond the test" (GREEN phase), add: "GREEN phase code only needs to pass the current test. Adding more code beyond that adds untested behavior — you can't tell if the extra code is correct because no test exists for it. Refactor phase, with all tests green, is the safe place for improvements."
2. [Area 3] Adjacent to "No exceptions without your human partner's permission" (Final Rule), add: "Exceptions to TDD have a documented pattern of being 'just this once' in the moment and becoming team norms in practice. Human permission makes the exception visible and deliberate rather than a local optimization that silently spreads."
3. [Area 6] In the RED phase instructions, add: "Write the simplest test that captures the intended behavior — not the most comprehensive test. One assertion is often correct for the RED step. If you find yourself planning multiple test cases before running the first one, stop: write the first test, run it, confirm it fails for the right reason, then proceed to GREEN."

---

#### `skills/handoff-acceptance/SKILL.md`
**Areas:** Area 6
**Tier 3 changes:**
1. [Area 6] After the Acceptance Checklist intro, before the numbered checks, add: "For each blocking check, read the relevant section of the handoff, then pause before recording your verdict. Ask: If I were an implementer consuming this handoff tomorrow, would this gap cause me to write wrong code? If yes, it is blocking. If the gap is present but would not change the implementation, note it as recommended — not blocking."

---

#### `skills/receiving-code-review/SKILL.md`
**Areas:** Area 6
**Tier 3 changes:**
1. [Area 6] In The Response Pattern section, near steps 3–4 (VERIFY/EVALUATE), add: "Before writing your response, pause to evaluate the feedback technically. Is the reviewer correct given the actual codebase patterns? Is there a case where the reviewer is right in principle but wrong for this specific context? Commit to a position — agree, push back with reasoning, or ask a clarifying question — before typing your response."

---

## Command Stub Updates Required

The following command stub files at `~/.claude/commands/superpowers/<name>.md` must have their `description:` frontmatter updated to match the Area 7 proposed descriptions. These files are outside the repo; they must be updated manually or regenerated.

| Stub file | New description |
|-----------|----------------|
| `~/.claude/commands/superpowers/brainstorming.md` | `Use when starting any creative or implementation work — building features, adding functionality, modifying behavior, or designing components — before writing a spec or touching code.` |
| `~/.claude/commands/superpowers/finishing-a-development-branch.md` | `Use when implementation is complete, all tests pass, and you need to decide how to integrate the work (merge, PR, or cleanup)` |
| `~/.claude/commands/superpowers/handoff-acceptance.md` | `Use when receiving code, schemas, or documentation from another agent, team, or system that will feed into brainstorming, planning, or implementation` |
| `~/.claude/commands/superpowers/receiving-code-review.md` | `Use when receiving code review feedback and about to implement suggestions, especially when feedback is unclear, seems technically questionable, or conflicts with your understanding` |
| `~/.claude/commands/superpowers/subagent-driven-development.md` | `Use when executing an implementation plan that has independent tasks and you want each task handled by a dedicated subagent with post-task review in the current session` |
| `~/.claude/commands/superpowers/using-git-worktrees.md` | `Use when starting feature work that needs isolation from the current workspace, or before executing implementation plans in a dedicated directory` |
| `~/.claude/commands/superpowers/using-superpowers.md` | `Use when starting any conversation, before responding to any request including clarifying questions` |
| `~/.claude/commands/superpowers/verification-before-completion.md` | `Use when about to claim work is complete, fixed, or passing, before committing or creating PRs` |
| `~/.claude/commands/superpowers/writing-plans.md` | `Use when you have a spec or requirements for a multi-step task, before touching code` |
| `~/.claude/commands/superpowers/executing-plans.md` | `Use when you have a written implementation plan ready to execute in a new session` (optional — current passes audit) |

**Note:** Changing `description:` in a SKILL.md frontmatter does NOT automatically update the picker. Both the SKILL.md frontmatter and the command stub frontmatter must be updated. The `!cat` preprocessing in command stubs only pulls body content, not frontmatter.

---

## Statistics

### Total Recommendations by Area

| Area | Focus | Recommendations |
|------|-------|----------------|
| Area 7 (CSO descriptions) | 9 NEEDS_FIX descriptions + 6 PASS | 9 fixes, 6 command stub updates |
| Area 5 (XML tags) | Tag renames | 11 tag pairs across 4 files |
| Area 8 (Role identity) | Role statements | 5 new role statements, 1 already good |
| Area 1 (De-escalation) | Language intensity | 65 instances audited: 36 overblown, 14 incident-backed (tone only), 15 warranted |
| Area 2 (Positive framing) | Framing direction | 23 sections rewritten across 13 files |
| Area 3 (Motivation) | Why-context additions | 47 unmotivated rules across 18 files |
| Area 4 (Template optimization) | Agentic patterns | 12 additions across 4 template files |
| Area 6 (Thinking guidance) | Exploration behavior | 14 guidance additions across 8 skills |

**Grand total: approximately 171 distinct change points**

### Recommendations Per File (descending)

| File | Areas Touching It | Approximate Changes |
|------|-------------------|-------------------|
| `subagent-driven-development/SKILL-v0.1.md` | 1, 2, 3, 6 | ~15 |
| `skills/using-superpowers/SKILL.md` | 1, 2, 3, 5, 7 | ~10 |
| `skills/verification-before-completion/SKILL.md` | 1, 2, 3, 7 | ~9 |
| `skills/test-driven-development/SKILL.md` | 1, 2, 3, 5, 6 | ~10 |
| `subagent-driven-development/spec-reviewer-prompt-v0.1.md` | 1, 2, 3, 4, 8 | ~8 |
| `subagent-driven-development/implementer-prompt-v0.1.md` | 1, 2, 3, 4, 8 | ~8 |
| `skills/brainstorming/SKILL-v0.1.md` | 1, 2, 3, 6 | ~9 |
| `skills/systematic-debugging/SKILL.md` | 1, 2, 3, 6 | ~8 |
| `skills/writing-plans/SKILL-v0.1.md` | 1, 2, 3, 6 | ~7 |
| `skills/writing-skills/SKILL.md` | 1, 2, 3, 5 | ~7 |
| `skills/receiving-code-review/SKILL.md` | 1, 2, 3, 6 | ~7 |
| `agents/code-reviewer.md` | 4 | ~3 |
| `skills/executing-plans/SKILL.md` | 1, 3 | ~7 |
| `skills/finishing-a-development-branch/SKILL.md` | 3, 7 | ~5 |
| `skills/requesting-code-review/SKILL.md` | 2, 3, 7 | ~4 |
| `skills/using-git-worktrees/SKILL.md` | 1, 3, 7 | ~5 |
| `skills/handoff-acceptance/SKILL.md` | 1, 3, 6, 7 | ~5 |
| `skills/brainstorming/spec-document-reviewer-prompt.md` | 8 | 1 |
| `skills/brainstorming/distillation-reviewer-prompt.md` | 8 | 1 |
| `skills/writing-plans/plan-document-reviewer-prompt-v0.1.md` | 8, 4 | 2 |
| `skills/dispatching-parallel-agents/SKILL.md` | 3 | 2 |
| `skills/writing-skills/testing-skills-with-subagents.md` | 5 | 2 tag pairs |
| `subagent-driven-development/code-quality-reviewer-prompt-v0.1.md` | 4 | 1 |

### Overlaps Resolved

15 overlap cases identified and resolved (documented in Overlap Resolution section above). In all 15 cases, the overlap was **compatible rather than conflicting** — areas operated on the same passage from different dimensions (intensity vs. direction, or role vs. agentic pattern). No genuine conflicts requiring human decision were found.

### Files With No Changes

Based on audit findings across all 8 areas:

| File | Reason |
|------|--------|
| `skills/dispatching-parallel-agents/SKILL.md` | Description passes (Area 7), no XML tags, no role template (SKILL not a prompt template), language well-calibrated (Area 1), no negative-dominant sections (Area 2). Only Area 3 motivation additions (2 rules). Area 6 assessed as NOT APPLICABLE. |
| `skills/requesting-code-review/SKILL.md` | Description passes (Area 7). Most language warranted (Area 1). One positive-framing rewrite (Area 2) and two motivation additions (Area 3). Light touchload. |
| `agents/code-reviewer.md` | Role already strong (Area 8 — no change). No language issues (Areas 1, 2 — no change). Only Area 4 additions (3 items). |
| `subagent-driven-development/code-quality-reviewer-prompt-v0.1.md` | Dispatch stub — no role statement needed, no language issues, no positive-framing gaps. Only Area 4 confidence qualifier addition (1 item). |

---

## Implementation Sequence

Apply in this order to minimize rework and maximize early behavioral improvement:

### Pass 1: Tier 1 — All files (estimated 1–2 hours)
Apply in this order within Tier 1:
1. `using-superpowers/SKILL.md` — `<EXTREMELY-IMPORTANT>` block replacement (highest overtrigger risk in entire audit)
2. All 9 SKILL.md frontmatter description fixes (mechanical find-replace)
3. `using-superpowers/SKILL.md` — `<SUBAGENT-STOP>` rename
4. `test-driven-development/SKILL.md` — `<Good>/<Bad>` renames (4 pairs)
5. `writing-skills/SKILL.md` — `<Good>/<Bad>` renames (1 pair)
6. `writing-skills/testing-skills-with-subagents.md` — `<Before>/<After>` renames (1 pair)
7. All 5 role statement insertions (implementer, spec-reviewer, distillation-reviewer, spec-document-reviewer, plan-document-reviewer)
8. All 9 command stub description updates (outside repo)

### Pass 2: Tier 2 — High-density files first (estimated 3–4 hours)
Apply in this order within Tier 2, prioritized by overtrigger risk and session-critical files:
1. `using-superpowers/SKILL.md` — body language changes (Red Flags section rename)
2. `verification-before-completion/SKILL.md` — shaming language removal + positive anchors
3. `subagent-driven-development/SKILL-v0.1.md` — Review Enforcement section + Red Flags Never list
4. `subagent-driven-development/spec-reviewer-prompt-v0.1.md` — CRITICAL section rewrite
5. `systematic-debugging/SKILL.md` — core principle + spirit sentence removal + MUST + Red Flags
6. `test-driven-development/SKILL.md` — spirit sentence removal + Iron Law + MANDATORY + completion checklist + Red Flags
7. `receiving-code-review/SKILL.md` — Forbidden Responses → Response Pattern + Acknowledging Correct Feedback
8. `brainstorming/SKILL-v0.1.md` — Anti-Pattern rename + MUST instances + process flow
9. `writing-plans/SKILL-v0.1.md` — MUST instances + Write-Scope Partitioning
10. `writing-skills/SKILL.md` — Background line + Iron Law + STOP block
11. `executing-plans/SKILL.md` — REQUIRED label removals
12. `handoff-acceptance/SKILL.md` — MUST → should
13. `using-git-worktrees/SKILL.md` — MUST verify removal
14. `requesting-code-review/SKILL.md` — Never → Required list
15. `implementer-prompt-v0.1.md` — CRITICAL section rewrite

### Pass 3: Tier 3 — Motivation additions (estimated 4–6 hours, can be done file-by-file)
Apply file-by-file. No ordering dependency within Tier 3.

Recommended order based on stakes and usage frequency:
1. `subagent-driven-development/SKILL-v0.1.md` — motivation + thinking guidance (4 motivation + 2 thinking)
2. `spec-reviewer-prompt-v0.1.md` — motivation + thinking + template additions (5 items)
3. `implementer-prompt-v0.1.md` — motivation + template additions (5 items)
4. `agents/code-reviewer.md` — template additions (3 items)
5. `systematic-debugging/SKILL.md` — motivation + thinking (5 items)
6. `brainstorming/SKILL-v0.1.md` — motivation + thinking (5 items)
7. `writing-plans/SKILL-v0.1.md` — motivation + thinking (5 items)
8. `test-driven-development/SKILL.md` — motivation + thinking (3 items)
9. `executing-plans/SKILL.md` — motivation (5 items)
10. `finishing-a-development-branch/SKILL.md` — motivation (4 items)
11. `requesting-code-review/SKILL.md` — motivation (2 items)
12. `using-superpowers/SKILL.md` — motivation (3 items)
13. `verification-before-completion/SKILL.md` — motivation (3 items)
14. `writing-skills/SKILL.md` — motivation (2 items)
15. `receiving-code-review/SKILL.md` — motivation + thinking (3 items)
16. `dispatching-parallel-agents/SKILL.md` — motivation (2 items)
17. `using-git-worktrees/SKILL.md` — motivation (3 items)
18. `handoff-acceptance/SKILL.md` — motivation + thinking (2 items)
19. `code-quality-reviewer-prompt-v0.1.md` — confidence qualifier (1 item)
