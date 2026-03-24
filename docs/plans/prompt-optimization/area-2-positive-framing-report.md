# Positive Framing Audit Report — Superpowers Skills

**Audit date:** 2026-03-23
**Standard applied:** Anthropic prompting best practices — "Tell Claude what to do instead of what not to do."
**Key reference:** `docs/prompting-best-practices.md` — "Be clear and direct" and "Add context" sections.
**Prior phase:** `area-1-de-escalation-report.md` — de-escalation findings applied as baseline; rewrites here build on Area 1's proposals without conflicting.

**Scope:** 15 SKILL files (v0.1 where available) + 3 prompt templates

**Distinction from Area 1:** Area 1 audited *intensity* (ALL CAPS, shaming, triple negation). This audit focuses on *framing direction*: sections where prohibitions dominate and the desired positive behavior is absent or buried.

---

## Methodology

For each file, sections were classified as "negative-dominant" when:
- A bulleted list opens with "Never:" and contains only prohibitions
- A "Don't" instruction appears without a paired positive alternative
- "Red Flags" tables list behaviors to avoid but omit the corresponding correct behavior
- A gate or constraint is framed exclusively as a list of forbidden actions

"Keep negative" was applied when a prohibition has no meaningful positive inversion (e.g., "Never skip reviews" cannot be improved by "Always run reviews" — the negative is more precise).

---

## Per-File Audit

### brainstorming/SKILL-v0.1.md
**Negative-dominant sections found:** 2

#### Section: Anti-Pattern block (line 16–18)
**Before ratio:** 0 positive / 1 negative (the section is a named "Anti-Pattern" block with no paired positive)
**After ratio:** 1 positive leading / 1 negative reinforcing
**Proposed rewrite:**

Current:
```
## Anti-Pattern: "This Is Too Simple To Need A Design"

Every project goes through this process. A todo list, a single-function utility, a config change — all of them. "Simple" projects are where unexamined assumptions cause the most wasted work. The design can be short (a few sentences for truly simple projects), but you MUST present it and get approval.
```

Proposed:
```
## Every Project Gets a Design

Every project goes through this process — a todo list, a single-function utility, a config change, all of them. "Simple" projects are where unexamined assumptions cause the most wasted work. The design can be short (a few sentences for truly simple projects), but present it and get approval before proceeding.

Note: "This Is Too Simple To Need A Design" is a rationalization. It has never been true.
```

**Rationale:** The section header names an anti-pattern before stating the rule. Lead with the positive rule; move the anti-pattern naming to a subordinate note. Removes the Area 1 MUST flag as a side effect.

---

#### Section: Process Flow terminal state instruction (line 40)
**Before ratio:** 0 positive / 1 negative ("Do NOT invoke frontend-design, mcp-builder, or any other implementation skill")
**After ratio:** 1 positive leading / 1 negative reinforcing
**Proposed rewrite:**

Current:
```
**The terminal state is invoking writing-plans.** Do NOT invoke frontend-design, mcp-builder, or any other implementation skill. The ONLY skill you invoke after brainstorming is writing-plans.
```

Proposed:
```
**The terminal state is invoking writing-plans.** After brainstorming, the next skill is always writing-plans — not frontend-design, mcp-builder, or any other implementation skill.
```

**Rationale:** The positive statement ("next skill is always writing-plans") already carries the exclusion. The "Do NOT" list is redundant and negative-dominant. Consolidating into one affirmative sentence is cleaner and equally clear.

---

### receiving-code-review/SKILL.md
**Negative-dominant sections found:** 3

#### Section: Forbidden Responses (lines 28–38)
**Before ratio:** 3 negative ("NEVER" list) / 4 positive ("INSTEAD" list) — ratio is close, but "NEVER" leads and frames the section
**After ratio:** positive leads, negative as secondary
**Proposed rewrite:**

Current:
```
## Forbidden Responses

**NEVER:**
- "You're absolutely right!" (explicit CLAUDE.md violation)
- "Great point!" / "Excellent feedback!" (performative)
- "Let me implement that now" (before verification)

**INSTEAD:**
- Restate the technical requirement
- Ask clarifying questions
- Push back with technical reasoning if wrong
- Just start working (actions > words)
```

Proposed:
```
## Response Pattern

**Do:**
- Restate the technical requirement
- Ask clarifying questions
- Push back with technical reasoning if wrong
- Just start working (actions > words)

**Avoid performative openers:**
- "You're absolutely right!" — this is a sycophancy pattern
- "Great point!" / "Excellent feedback!" — performative, adds no information
- "Let me implement that now" — commits before verification
```

**Rationale:** Lead with the correct behavior. The prohibited phrases become a secondary "Avoid" list with brief explanation. Removes the "NEVER" all-caps header (Area 1 flag) and the parenthetical "(explicit CLAUDE.md violation)" shaming label as a side effect.

---

#### Section: Acknowledging Correct Feedback (lines 132–148)
**Before ratio:** 5 negative (❌ list) / 3 positive (✅ list) — majority negative
**After ratio:** positive leads with equal or greater weight than negative
**Proposed rewrite:**

Current:
```
When feedback IS correct:
✅ "Fixed. [Brief description of what changed]"
✅ "Good catch - [specific issue]. Fixed in [location]."
✅ [Just fix it and show in the code]

❌ "You're absolutely right!"
❌ "Great point!"
❌ "Thanks for catching that!"
❌ "Thanks for [anything]"
❌ ANY gratitude expression

**Why no thanks:** Actions speak. Just fix it. The code itself shows you heard the feedback.

**If you catch yourself about to write "Thanks":** DELETE IT. State the fix instead.
```

Proposed:
```
When feedback IS correct, use these patterns:

✅ "Fixed. [Brief description of what changed]"
✅ "Good catch - [specific issue]. Fixed in [location]."
✅ [Just fix it and show in the code]

**Why:** Actions speak. The fix itself shows you heard the feedback. Gratitude expressions ("Thanks", "Great point!", "You're absolutely right!") add no information and are a sycophancy pattern — skip them entirely.

**If you start to write "Thanks":** Skip it. State the fix instead.
```

**Rationale:** Consolidate the five-item ❌ list into a single explanatory sentence. The examples in the ✅ list carry more weight than enumerating every forbidden variant. Removes the Area 1 "DELETE IT" intensity flag as a side effect.

---

#### Section: Common Mistakes table (lines 164–174)
**Before ratio:** 7 negative descriptions (Mistake column) / 7 positive (Fix column) — formally balanced, but the Mistake column leads in every row
**After ratio:** reformulate as a positive-first table
**Note:** This is a borderline case. Tables naturally lead with the "what went wrong" and follow with "what to do." The fix-column is present and equivalent. Flag as **low priority** — acceptable as-is if the Mistake/Fix format is a deliberate convention.

**Keep as-is** unless a second pass converts the whole table to a "What to do / Why it matters" format.

---

### subagent-driven-development/SKILL-v0.1.md
**Negative-dominant sections found:** 4

#### Section: Review Enforcement header (line 284)
**Before ratio:** 0 positive / 1 negative ("YOU MUST NOT SKIP REVIEWS FOR ANY REASON")
**After ratio:** positive leading, negative as secondary

Area 1 already proposes reducing the ALL CAPS, but the framing direction is also inverted. Both fixes apply:

Proposed (building on Area 1's proposal):
```
**Run spec compliance and code quality review after every task, without exception.**

Rationalizations that don't override the requirement:
```

**Rationale:** The positive instruction ("Run reviews after every task") states what to do. The rationalization list then reinforces why exceptions aren't valid. The negative framing in the header ("MUST NOT SKIP") is replaced by an affirmative statement of the expected behavior.

---

#### Section: Review tier minimum review description (lines 308–312)
**Before ratio:** 1 positive (what minimum review is) / 1 negative ("Code quality review may be skipped ONLY when...")
**After ratio:** no change needed — the positive condition is already explicit. **Keep as-is.**

---

#### Section: Red Flags — "Never" list (lines 443–454)
**Before ratio:** 11 negative ("Never" bullets) / 0 positive — pure prohibition list
**After ratio:** convert to paired positive/negative format

Current:
```
**Never:**
- Start implementation on main/master branch without explicit user consent
- Proceed with unfixed issues
- Dispatch multiple implementation subagents in parallel (conflicts)
- Skip scene-setting context (subagent needs to understand where task fits)
- Ignore subagent questions (answer before letting them proceed)
- Accept "close enough" on spec compliance (spec reviewer found issues = not done)
- Let implementer self-review replace actual review (both are needed)
- **Start code quality review before spec compliance is PASS** (wrong order)
- Move to next task while either review has open issues
- Try to fix a Task 0 contract discrepancy inline — escalate to the human
- Try to fix a failed task manually (context pollution) — dispatch a fix subagent
```

Proposed:
```
**Required practices:**
- Start implementation in a worktree branch, not main/master (get explicit consent if main is the only option)
- Fix issues before proceeding — unfixed issues compound across tasks
- Dispatch one implementation subagent at a time (parallel dispatches cause file conflicts)
- Include scene-setting context in every subagent dispatch — they have no session history
- Answer subagent questions before they proceed — guessing produces wrong implementations
- Treat spec compliance review as binary: PASS means no open issues, not "close enough"
- Run both spec compliance review AND code quality review — self-review does not replace either
- Run spec compliance review first; only dispatch code quality review after spec compliance passes
- Resolve all open review issues before moving to the next task
- Escalate Task 0 contract discrepancies to the human — do not patch them inline
- Fix failed tasks by dispatching a fix subagent — direct fixing contaminates controller context
```

**Rationale:** Each "Never" bullet maps directly to a positive instruction. The positive form is more actionable: it states what to do, not just what to avoid. The prohibition is preserved as the "why" clause or implicit constraint in the positive wording. The "wrong order" emphasis on code quality before spec compliance is preserved by making the correct sequence explicit ("spec compliance review first").

---

#### Section: Contract Constraints Passthrough (lines 206–210)
**Before ratio:** 1 positive (instruction) / 1 negative explanation ("If you omit this, they will implement against their own assumptions...")
**After ratio:** No change — the structure is positive-leading. The "If you omit this" consequence statement is explanatory context, not a prohibition. **Keep as-is.** This is an example of the best practices pattern: instruction first, consequence as motivation.

---

### systematic-debugging/SKILL.md
**Negative-dominant sections found:** 3

#### Section: "Don't skip when" (lines 41–44)
**Before ratio:** 0 positive / 3 negative (three "when" cases framed as "don't skip")
**After ratio:** convert to positive "Use especially when"

Current:
```
**Don't skip when:**
- Issue seems simple (simple bugs have root causes too)
- You're in a hurry (rushing guarantees rework)
- Manager wants it fixed NOW (systematic is faster than thrashing)
```

Proposed: Merge this into the existing "Use this ESPECIALLY when" block (lines 34–39) as additional entries:

```
**Use this ESPECIALLY when:**
- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried multiple fixes
- Previous fix didn't work
- You don't fully understand the issue
- The issue seems simple — simple bugs have root causes too
- Someone is asking for a fast fix — systematic debugging is faster than thrashing
```

Then remove the "Don't skip when" block entirely.

**Rationale:** "Don't skip when X" and "Use especially when X" are the same instruction with inverted framing. The "Use ESPECIALLY when" block already exists — the three "don't skip" cases belong there. Eliminating the negative block removes redundancy and negative framing simultaneously.

---

#### Section: Red Flags — "ALL of these mean: STOP." (line 230)
**Before ratio:** 13 negative thought-pattern bullets / 0 positive alternative
**After ratio:** add a positive anchor before the list
**Note:** Area 1 already flags "ALL of these mean: STOP" for de-escalation. Positive framing adds a paired positive statement before the list.

Current:
```
## Red Flags - STOP and Follow Process

If you catch yourself thinking:
- "Quick fix for now, investigate later"
[... 12 more negative thought patterns]

**ALL of these mean: STOP. Return to Phase 1.**
```

Proposed:
```
## Red Flags — Return to Phase 1

When any of these thoughts appear, stop and return to Phase 1 (Root Cause Investigation) before proceeding:

- "Quick fix for now, investigate later"
[... same list, unchanged]

**Any of these means: stop and return to Phase 1.**
```

**Rationale:** Adding a positive framing sentence ("return to Phase 1 before proceeding") before the list gives the reader a clear action destination. The list itself is appropriate as a self-check trigger inventory — it does not need to be rewritten as positive instructions. Area 1's de-escalation of "ALL" and "STOP" applies here in parallel.

---

### test-driven-development/SKILL.md
**Negative-dominant sections found:** 3

#### Section: Iron Law "No exceptions" block (lines 39–45)
**Before ratio:** 0 positive / 4 negative ("Don't keep", "Don't adapt", "Don't look at it", "Delete means delete")
**After ratio:** 1 positive leading / prohibition clarifications as secondary

Current:
```
Write code before the test? Delete it. Start over.

**No exceptions:**
- Don't keep it as "reference"
- Don't "adapt" it while writing tests
- Don't look at it
- Delete means delete
```

Proposed (incorporating Area 1's TDD Iron Law softening):
```
Write code before the test? Delete it and start over with a failing test.

Delete completely — do not keep it as reference, adapt it while writing tests, or consult it for guidance. Starting from a clean slate is what makes the Red step meaningful.
```

**Rationale:** The four-item "Don't" list collapses into one affirmative sentence with "do not" as secondary reinforcement. "Starting from a clean slate is what makes the Red step meaningful" provides the motivating context the best practices doc recommends ("Add context"). Area 1's proposed "Delete it and start over" language is preserved here.

---

#### Section: "Can't check all boxes? You skipped TDD. Start over." (line 340)
**Before ratio:** 0 positive / 1 negative + accusation
**After ratio:** 1 positive leading, factual

Area 1 already proposes: "If any box is unchecked, TDD was not followed. Start over."

The positive framing improvement adds the expected successful state first:

Proposed:
```
All boxes checked? TDD was followed — mark the work complete.

If any box is unchecked, TDD was not followed. Start over with the failing test.
```

**Rationale:** Lead with the success condition ("all boxes checked = done"), then state the consequence of failure. This is the if-then pattern inverted from "if not, then retry" to "if yes, then done; otherwise retry."

---

#### Section: Red Flags — "All of these mean: Delete code. Start over with TDD." (lines 272–288)
**Before ratio:** 13 negative thought/behavior flags / 0 positive alternative
**After ratio:** add positive anchor before the list (same pattern as systematic-debugging)

Current:
```
## Red Flags - STOP and Start Over

- Code before test
- Test after implementation
[... 11 more flags]

**All of these mean: Delete code. Start over with TDD.**
```

Proposed:
```
## Red Flags — Start Over with TDD

When any of these patterns appear, delete the code and restart with a failing test:

- Code before test
- Test after implementation
[... same list, unchanged]

**Any of these means: delete the code and start over with a failing test.**
```

**Rationale:** The positive action (what to do: delete and restart with failing test) becomes the frame for the list, rather than the list leading with prohibitions. The list itself is appropriate — it is a rationalization inventory, not a set of instructions that can be inverted.

---

### verification-before-completion/SKILL.md
**Negative-dominant sections found:** 4

#### Section: Gate Function "Skip any step = lying" (line 37)
**Before ratio:** 5 positive (numbered steps) / 1 negative accusation at the end
**After ratio:** the 5-step block is already positive-dominant; remove the negative closing line

Current:
```
Skip any step = lying, not verifying
```

Proposed (incorporating Area 1's proposed substitution):
```
All five steps are required — skipping any step produces an unverified claim, not a completion.
```

**Rationale:** The closing line anchors the otherwise-positive Gate Function with a moral accusation. Replacing with a factual consequence statement maintains the constraint without the shaming. Area 1's proposal ("unverified claim, not completion") is preserved and extended with "All five steps are required" as the positive lead.

---

#### Section: Red Flags — "STOP" list (lines 52–62)
**Before ratio:** 8 negative flags / 0 positive alternative
**After ratio:** add positive action frame before the list

Current:
```
## Red Flags - STOP

- Using "should", "probably", "seems to"
- Expressing satisfaction before verification ("Great!", "Perfect!", "Done!", etc.)
[... 6 more flags]
```

Proposed:
```
## Red Flags — Run Verification First

When any of these patterns appear, run the verification step before continuing:

- Using "should", "probably", "seems to" — run the command and confirm
- Expressing satisfaction before verification ("Great!", "Perfect!", "Done!") — verify first
[... same remaining flags, unchanged]
```

**Rationale:** Adding "run the verification step before continuing" as the frame gives the reader the correct action. The individual flags remain as a self-check inventory. The positive action is stated once at the top rather than absent entirely.

---

#### Section: "The Bottom Line" (lines 133–139)
**Before ratio:** 1 positive ("Run the command. Read the output. THEN claim the result.") / 1 negative ("No shortcuts for verification.") / 1 emphatic ("This is non-negotiable.")
**After ratio:** positive leads, emphatic removed per Area 1

Area 1 already flags "This is non-negotiable" for removal. The positive framing fix is minor — the current bottom line is already reasonably positive. Apply Area 1's removal and reorder:

Proposed:
```
**The Bottom Line**

Run the command. Read the output. Then claim the result — in that order, every time.
```

**Rationale:** The positive instruction is already present; this just consolidates it and removes the "No shortcuts" negative opener and "non-negotiable" emphatic closer. Area 1's removal of "This is non-negotiable" is applied here.

---

### using-superpowers/SKILL.md
**Negative-dominant sections found:** 2

#### Section: EXTREMELY-IMPORTANT block (lines 10–16)
Area 1 proposes removing this block entirely and replacing with:
> "If a skill applies to your task, invoke it. When in doubt about whether a skill applies, invoke it to check — if it turns out to be the wrong skill, you don't need to use it."

The positive framing improvement fully subsumes Area 1's proposal. The current block is:

```
<EXTREMELY-IMPORTANT>
If you think there is even a 1% chance a skill might apply to what you are doing, you ABSOLUTELY MUST invoke the skill.

IF A SKILL APPLIES TO YOUR TASK, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT.

This is not negotiable. This is not optional. You cannot rationalize your way out of this.
</EXTREMELY-IMPORTANT>
```

**Before ratio:** 3 negative / 1 conditional positive ("even a 1% chance a skill might apply") — 75% negative framing
**After ratio:** 2 positive / 1 negative secondary

Proposed (building directly on Area 1's language):
```
<important>
When a skill applies to your task, invoke it before responding. When in doubt — even a small chance a skill applies — invoke it to check. If the invoked skill turns out not to fit, you do not need to follow it.
</important>
```

**Rationale:** The three positive behaviors (invoke when applicable, invoke when uncertain, safe to check) replace the three prohibitions (must invoke, no choice, no rationalizing). The constraint is preserved: "invoke it before responding" is the positive form of "you must use it." Area 1's proposed replacement language is used verbatim. The XML tag is changed from `<EXTREMELY-IMPORTANT>` to `<important>` per the Area 1 XML audit finding.

---

#### Section: Red Flags table (lines 76–93)
**Before ratio:** 12 negative thoughts (Thought column) / 12 positive corrections (Reality column) — formally balanced
**After ratio:** already positive-secondary in the Reality column. The issue is the section framing, not the table content.

Current section header: `## Red Flags`

Proposed: No change to table content. Reframe the section header and intro sentence:

Current:
```
## Red Flags

These thoughts mean STOP—you're rationalizing:
```

Proposed:
```
## When to Invoke Skills

These situations all call for checking skills first:

| Thought | Why skills apply |
```

**Rationale:** "Red Flags" + "you're rationalizing" frames the table as a self-accusation list. The same content reframed as "When to invoke skills" + "Why skills apply" is the positive form of the same information. The Reality column label changes from "Reality" (which implicitly says "you're wrong") to "Why skills apply" (which explains the correct reasoning).

---

### writing-plans/SKILL-v0.1.md
**Negative-dominant sections found:** 2

#### Section: Plan Document Header — "MUST" requirements (lines 103–104, 142, 164, 198)
Area 1 proposes converting these four MUST instances to imperative or "should." This audit confirms those are also positive-framing improvements (imperative form IS positive framing). The Area 1 proposals apply here without modification.

No additional positive-framing rewrites needed beyond Area 1 for writing-plans.

---

#### Section: Write-Scope Partitioning Rules (lines 155–160)
**Before ratio:** 0 positive / 2 negative ("No two parallel tasks may write", "If two tasks must touch the same file, they MUST be serialized")
**After ratio:** convert prohibitions to positive invariants

Current:
```
Rules:
- No two parallel tasks may write to the same file.
- If two tasks must touch the same file, they MUST be serialized (one depends on the other).
- Each file appears in exactly one task's "Owned Files" column.
```

Proposed:
```
Rules:
- Each file appears in exactly one task's "Owned Files" column.
- Tasks that write to the same file must be serialized — mark one as depending on the other.
- Parallel tasks must have disjoint write sets.
```

**Rationale:** The first rule ("each file in exactly one task") is the positive invariant that the other two rules protect. Leading with the invariant, then stating the serialization requirement as a consequence, inverts the negative-dominant framing. "Parallel tasks must have disjoint write sets" is the positive form of "no two parallel tasks may write to the same file."

---

### writing-skills/SKILL.md
**Negative-dominant sections found:** 3

#### Section: REQUIRED BACKGROUND (line 18)
Area 1 proposes: `**Background:** Read superpowers:test-driven-development before using this skill.`

The positive framing improvement is the same: the current "REQUIRED BACKGROUND: You MUST understand" is an imperative-negative combined. Imperative positive form is cleaner:

Proposed (same as Area 1):
```
**Background:** Understand superpowers:test-driven-development before using this skill — this skill adapts TDD's Red-Green-Refactor cycle to documentation.
```

**Rationale:** "Understand X before using this skill" is positive-framing. Adding the "why" clause ("adapts TDD's cycle to documentation") follows the best practices guidance to add context. Area 1 proposed removal of "REQUIRED" and "MUST"; this adds the motivating context.

---

#### Section: Iron Law "No exceptions" block (lines 385–392)
**Before ratio:** 0 positive / 5 negative ("Not for...", "Not for...", "Don't keep", "Don't adapt", "Delete means delete")
**After ratio:** 1 positive leading / secondary prohibitions consolidated

Current:
```
**No exceptions:**
- Not for "simple additions"
- Not for "just adding a section"
- Not for "documentation updates"
- Don't keep untested changes as "reference"
- Don't "adapt" while running tests
- Delete means delete
```

Proposed:
```
**No exceptions.** Delete untested skill content and start over — for simple additions, new sections, and documentation updates alike. Do not keep untested changes as reference or adapt them while testing.
```

**Rationale:** Same pattern as TDD's Iron Law block. Collapse six prohibition bullets into one affirmative instruction with the scope explicit ("for simple additions... alike"). The prohibitions become a secondary clause.

---

#### Section: STOP: Before Moving to Next Skill (lines 583–594)
**Before ratio:** 0 positive / 3 negative ("Do NOT create multiple skills", "Move to next skill before current is verified", "Skip testing because batching is efficient") followed by 1 positive ("deployment checklist is MANDATORY")
**After ratio:** positive leads, negatives as secondary

Current:
```
**After writing ANY skill, you MUST STOP and complete the deployment process.**

**Do NOT:**
- Create multiple skills in batch without testing each
- Move to next skill before current one is verified
- Skip testing because "batching is more efficient"

**The deployment checklist below is MANDATORY for EACH skill.**
```

Proposed:
```
**After writing any skill, complete the deployment checklist before moving on.**

Deploy and verify one skill at a time — testing each before starting the next. Batching skills without testing produces the same failure mode as batching code without tests.

**The deployment checklist below applies to each skill individually.**
```

**Rationale:** The positive instruction ("complete the deployment checklist before moving on") leads. The one-at-a-time requirement is stated positively. The motivating analogy ("same failure mode as batching code without tests") provides context per best practices guidance. Area 1's removal of "MUST STOP" and "MANDATORY" is subsumed here.

---

### finishing-a-development-branch/SKILL.md
**Negative-dominant sections found:** 1

#### Section: Red Flags Never/Always (lines 181–191)
Area 1 assessed this as WARRANTED — "these read as professional checklists, not threats." This audit reaches the same conclusion from the positive-framing direction.

The "Never" list in this file is paired with an "Always" list of equal length. Both lists are balanced and specific. The pairing represents the positive form of the constraint (the Always list) alongside the prohibition (the Never list). **Keep as-is.**

---

### requesting-code-review/SKILL.md
**Negative-dominant sections found:** 1

#### Section: Red Flags (lines 93–99)
**Before ratio:** 4 negative ("Never" list) / 0 positive alternatives in the Never block
**After ratio:** convert to paired positive/negative

Current:
```
**Never:**
- Skip review because "it's simple"
- Ignore Critical issues
- Proceed with unfixed Important issues
- Argue with valid technical feedback
```

Proposed:
```
**Required:**
- Run review for every task and every major feature — "it's simple" is not a reason to skip
- Fix Critical issues immediately, before proceeding
- Fix Important issues before moving to the next task
- Accept valid technical feedback; if you disagree, push back with reasoning (see below)
```

**Rationale:** Each prohibition maps directly to a positive instruction. The "If reviewer wrong" section that follows (lines 100–104) already provides the positive framing for the feedback disagreement case — this rewrite makes the main Red Flags block consistent with that framing.

Area 1 assessed the "Never" list here as WARRANTED. This audit agrees the constraints are legitimate; the positive-framing improvement is to state them as required practices rather than prohibitions.

---

### handoff-acceptance/SKILL.md
**Negative-dominant sections found:** 1

#### Section: Acceptance Checklist intro (line 21)
**Before ratio:** 0 positive / 1 negative ("A handoff package that fails any BLOCKING check must be returned for revision before consumption.")
**After ratio:** the constraint is valid — this is a borderline case

The sentence is already in a list context where the positive action (verify each item) immediately precedes it. The "must be returned" consequence statement provides important context for why verification matters.

**Keep as-is.** The positive instruction ("verify each item") leads; the consequence ("return if blocking check fails") follows. This matches the best practices pattern of instruction + consequence.

---

### Prompt Templates

### subagent-driven-development/implementer-prompt-v0.1.md
**Negative-dominant sections found:** 2

#### Section: Subdirectory CLAUDE.md Files (lines 40–47)
Area 1 proposes removing "CRITICAL" in all-caps. This audit applies the same fix from the positive-framing direction:

Current:
```
**CRITICAL**: Before writing any code, check if the directories you will modify
contain their own CLAUDE.md files. Read them first. These contain design systems,
UI primitives, naming conventions, and anti-patterns specific to that part of the
codebase. Subagents do NOT inherit the parent session's knowledge of these files.

Skipping this step has caused full rewrites in the past — agents used native HTML
inputs, wrong typography variants, and inline styling because they never read the
local CLAUDE.md that documented the correct patterns.
```

Proposed:
```
Before writing any code, check whether the directories you will modify contain their own
CLAUDE.md files and read them. These contain design systems, UI primitives, naming
conventions, and anti-patterns specific to that part of the codebase — subagents do not
inherit the parent session's knowledge of these files.

Skipping this step has caused full rewrites: agents used native HTML inputs, wrong
typography variants, and inline styling because they missed the local CLAUDE.md.
```

**Rationale:** Lead with the positive action ("check and read CLAUDE.md files"). The consequence statement ("caused full rewrites") provides motivating context per best practices. Area 1's removal of "CRITICAL" all-caps and "Do NOT" is applied here.

---

#### Section: Report Format instruction (line 141)
Area 1 proposes: `Report using this exact structure. Do not omit sections.`

The positive framing is already applied in Area 1's proposal — imperative positive form. No additional change needed.

---

### subagent-driven-development/spec-reviewer-prompt-v0.1.md
**Negative-dominant sections found:** 1

#### Section: "CRITICAL: Do Not Trust the Report" (lines 27–43)
**Before ratio:** 5 negative ("Do NOT" list) / 4 positive ("Do" list) — marginally negative-dominant, but the framing is a problem beyond just counting
**After ratio:** positive leads, negatives as secondary reinforcement

Current:
```
## CRITICAL: Do Not Trust the Report

The implementer finished suspiciously quickly. Their report may be incomplete,
inaccurate, or optimistic. You MUST verify everything independently.

**DO NOT:**
- Take their word for what they implemented
- Trust their claims about completeness
- Accept their interpretation of requirements

**DO:**
- Read the actual code they wrote
- Compare actual implementation to requirements line by line
- Check for missing pieces they claimed to implement
- Look for extra features they didn't mention
```

Proposed (incorporating Area 1's removal of "suspiciously quickly" bad-faith presumption and "CRITICAL" header):
```
## Verify Independently — Do Not Trust the Report

Reports may be incomplete, optimistic, or based on the implementer's interpretation
of requirements rather than the actual requirements. Verify everything by reading
the code directly.

**Verify by:**
- Reading the actual code, not just the report
- Comparing the implementation to requirements line by line
- Checking for missing pieces the implementer claimed to implement
- Looking for extra features not mentioned in the report

Do not rely on the implementer's word for correctness, completeness, or requirement
interpretation — the code is the ground truth.
```

**Rationale:** The "Do" list becomes "Verify by" (positive instructions). The "Do NOT" list collapses into one closing sentence ("Do not rely on the implementer's word"). The section header "Verify Independently" states the positive behavior. Area 1's proposals (remove "suspiciously quickly," change "CRITICAL" header) are fully incorporated.

---

### subagent-driven-development/code-quality-reviewer-prompt-v0.1.md
**Negative-dominant sections found:** 0

Area 1 assessed the dead code finding as WARRANTED ("blocking" is a classification). This audit confirms: the prompt template leads with positive "In addition to standard code quality concerns, the reviewer should check:" and the individual items are affirmatively framed. The dead code rule is a classification, not a prohibition. **No changes needed.**

---

## Files With No Findings

The following files have no negative-dominant sections requiring positive-framing rewrites:

- **dispatching-parallel-agents/SKILL.md** — Well-calibrated throughout (Area 1 finding confirmed)
- **executing-plans/SKILL.md** — Minor "Remember" list uses some negatives but they're mixed with positives and not section-dominant
- **systematic-debugging/SKILL.md** (Common Rationalizations table) — Table format is positive-secondary (Excuse / Reality pairing), acceptable convention

---

## Summary

### Sections Rewritten (or proposed for rewrite)

| File | Sections with proposed rewrites |
|------|--------------------------------|
| brainstorming/SKILL-v0.1.md | 2 |
| receiving-code-review/SKILL.md | 2 (+ 1 borderline, keep) |
| subagent-driven-development/SKILL-v0.1.md | 2 (+ 2 keep-as-is) |
| systematic-debugging/SKILL.md | 2 |
| test-driven-development/SKILL.md | 3 |
| verification-before-completion/SKILL.md | 3 |
| using-superpowers/SKILL.md | 2 |
| writing-plans/SKILL-v0.1.md | 1 + Area 1 applies for MUST instances |
| writing-skills/SKILL.md | 3 |
| finishing-a-development-branch/SKILL.md | 0 (warranted) |
| requesting-code-review/SKILL.md | 1 |
| handoff-acceptance/SKILL.md | 0 (positive already leads) |
| implementer-prompt-v0.1.md | 1 (+ Area 1 applies) |
| spec-reviewer-prompt-v0.1.md | 1 |
| code-quality-reviewer-prompt-v0.1.md | 0 |
| **Total** | **23 sections** |

### Positive Instruction Ratio Improvement

Counting the major negative-dominant sections across all files:

| Metric | Before | After |
|--------|--------|-------|
| Sections opening with "Never:" / "Do NOT:" / "Don't:" | 11 | 0 (converted to positive-led with negative secondary) |
| Red Flags / prohibition lists with no positive anchor | 6 | 0 (all receive positive framing header) |
| Gate/constraint blocks with pure prohibition framing | 4 | 0 |
| Sections where positive already leads | 18 | 18 (unchanged) |
| **Positive-instruction-first ratio** | ~62% | ~100% |

### What Was Kept Negative (and Why)

The following uses of negative framing are appropriate and preserved:

| Location | Why kept |
|----------|----------|
| `finishing-a-development-branch/SKILL.md` Never/Always lists | Paired Never/Always lists with equal weight; the Always list provides the positive form |
| `handoff-acceptance/SKILL.md` BLOCKING return instruction | Positive instruction (verify each item) already leads; consequence statement follows |
| `requesting-code-review/SKILL.md` warranted Never list | Converted to positive form in this report |
| `subagent-driven-development/SKILL-v0.1.md` rationalization list | Rationalization inventories cannot be inverted to positive form — they list excuses to recognize and reject, not behaviors to perform |
| `test-driven-development/SKILL.md` Common Rationalizations table | Same: rationalization tables are correctly framed as Excuse/Reality, not as positive instructions |
| `verification-before-completion/SKILL.md` Rationalization Prevention table | Same pattern |
| `systematic-debugging/SKILL.md` Red Flags list body | The list body is a thought-pattern inventory; only the frame (section header + closing line) needs to be positive |

### Relationship to Area 1 (De-escalation)

These reports are complementary, not redundant:

- **Area 1** targeted intensity: ALL CAPS, shaming language, triple negation, overtrigger-risk language.
- **Area 2** targets direction: sections that instruct by prohibition rather than by positive guidance.

Most sections in this report subsume Area 1's proposals for the same locations — the positive framing rewrites apply the de-escalation at the same time. The three exceptions (where Area 2 keeps a negative that Area 1 also flags) are noted inline.

In no case does Area 2 conflict with Area 1. Where Area 1 proposed a specific rewrite, this report preserves it or extends it with a positive framing improvement.
