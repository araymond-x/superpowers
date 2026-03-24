# Template Optimization Report — Agentic Best Practices Audit

**Audit date:** 2026-03-23
**Reference:** `docs/prompting-best-practices.md` — "Agentic Systems", "Tool Use", "Thinking and Reasoning" sections
**Scope:** 4 files — implementer-prompt-v0.1.md, spec-reviewer-prompt-v0.1.md, code-quality-reviewer-prompt-v0.1.md, agents/code-reviewer.md

**Prior phases already applied (or proposed):**
- Area 8: Role identity statements added to all four templates
- Area 1: De-escalated language (CRITICAL removed, "suspiciously quickly" removed, shaming language replaced)
- Area 2: Positive framing (DO NOT lists converted to affirmative, negative-dominant sections rewritten)
- Area 3: Motivation added to unmotivated rules (fixture test failure mode, why tests can't verify contracts, etc.)

This report evaluates the remaining gap: agentic systems best practices — investigate-before-answering, thinking guidance, parallel tool calling, file cleanup, avoid-overengineering patterns, and confidence-based assertions.

---

## Pattern Reference

The six patterns to evaluate, sourced from `docs/prompting-best-practices.md`:

1. **`<investigate_before_answering>`** — "Never speculate about code you have not opened... Make sure to investigate and read relevant files BEFORE answering questions about the codebase."

2. **Thinking guidance** — "After receiving tool results, carefully reflect on their quality and determine optimal next steps before proceeding."

3. **Parallel tool calling** — "Read several files at once to build context faster... If you intend to call multiple tools and there are no dependencies between the tool calls, make all of the independent tool calls in parallel."

4. **File cleanup** — "If you create any temporary new files, scripts, or helper files for iteration, clean up these files by removing them at the end of the task."

5. **`<avoid_overengineering>`** — "Avoid over-engineering. Only make changes that are directly requested or clearly necessary. Don't add features, refactor code, or make 'improvements' beyond what was asked."

6. **Confidence-based assertions** — From "Research and information gathering": "Track your confidence levels in your progress notes to improve calibration."

---

## Per-Template Analysis

### implementer-prompt-v0.1.md

**Current state summary:** The most comprehensive of the four templates. After prior phases, it has a role statement (Area 8), de-escalated CLAUDE.md section (Area 1), positive-framed report structure (Area 2), and motivation on status routing (Area 3). The Self-Review section already includes a YAGNI/overbuilding check. The Before You Begin section instructs asking questions before starting.

**Best practice patterns applicable:**

| Pattern | Applicable? | Already Present? | Recommendation |
|---------|------------|-----------------|----------------|
| `<investigate_before_answering>` | YES — implementer reads source files and CLAUDE.md before coding | PARTIAL — source file and CLAUDE.md reading is instructed, but the framing is task-specific, not the general "never speculate about code you haven't read" pattern | ADD — a single sentence generalizing the investigate-first principle beyond the specific source-file and CLAUDE.md steps |
| Thinking guidance | YES — especially after reading source files and after each implementation step | NO — the template does not mention reflecting on tool results before proceeding | ADD — a brief reflection instruction after the source file reading block |
| Parallel tool calling | YES — when reading multiple source files listed for a task | NO — no mention of parallel reads | ADD — one sentence encouraging parallel reads when multiple files are listed |
| File cleanup | YES — implementer may create temp scripts for testing | NO | ADD — one sentence after "Your Job" |
| `<avoid_overengineering>` | YES — this is the core YAGNI concern | PARTIAL — the Self-Review "Discipline" check covers it ("Did I avoid overbuilding?"), and the Code Organization section says "don't split files on your own." However, the formal pattern from the best practices doc is not present at the top where it could prime behavior before the task content loads | PARTIAL ADD — the Self-Review check is sufficient for in-progress behavior; a brief priming statement near the role statement or "Your Job" section would reinforce it earlier. Lower priority than the other gaps. |
| Confidence-based assertions | YES — the DONE_WITH_CONCERNS status serves this purpose | PRESENT — the report format already routes uncertain work to DONE_WITH_CONCERNS, which is a stronger mechanism than confidence labeling | NO CHANGE — the status routing is a better fit for the subagent context than inline confidence levels |

**Proposed additions with exact text:**

**Addition 1: Investigate-first principle (add to "Source Files" section, after the existing instruction)**

Location: After "If source files are listed above, read them BEFORE writing any code..." paragraph and before "## Subdirectory CLAUDE.md Files"

```
More broadly: never write code that assumes something about the codebase without
verifying it first. If you are unsure about a type, an existing function, or a
file's structure, read it before proceeding. Speculation about code you haven't
opened produces errors that tests may not catch.
```

**Addition 2: Thinking reflection after reading (add to end of "Source Files" section)**

Location: After Addition 1, still within the Source Files block

```
After reading source files, take a moment to verify your understanding is correct
before writing any code. If what you read contradicts the task description or your
assumptions, surface the conflict — do not silently work around it.
```

**Addition 3: Parallel file reads (add as first bullet under "Your Job")**

Location: "Your Job" section, before "1. Implement exactly what the task specifies"

```
When you need to read multiple files to build context (source files, CLAUDE.md
files, existing code), read them in parallel rather than sequentially — this
reduces your context usage and speeds up your work.
```

**Addition 4: File cleanup (add as new bullet under "Your Job", after "4. Commit your work")**

Location: After "4. Commit your work" in the "Your Job" numbered list

```
4a. Clean up any temporary files, test scripts, or scratch files you created
    during implementation — they should not appear in your final commit.
```

---

### spec-reviewer-prompt-v0.1.md

**Current state summary:** After prior phases, this template has a skeptical-auditor role statement (Area 8), a de-escalated verification section replacing "CRITICAL: Do Not Trust the Report" (Areas 1 + 2), and motivation on why test fixtures can't verify contract compliance (Area 3). The core behavior is code reading to verify claims.

**Best practice patterns applicable:**

| Pattern | Applicable? | Already Present? | Recommendation |
|---------|------------|-----------------|----------------|
| `<investigate_before_answering>` | HIGHLY APPLICABLE — the reviewer's entire job is to read code rather than trust reports | PRESENT — the "Verify by reading code, not the report" section (post-Area-1/2 revision) already encodes this as the reviewer's primary instruction. The formal XML pattern from the best practices doc adds little beyond what the section already says | NO CHANGE — the section text already instantiates this pattern. Adding the XML wrapper would be redundant. |
| Thinking guidance | YES — the reviewer reads many changed files and must form findings; reflection between reads would improve finding quality | NO — no reflection instruction exists | ADD — a targeted instruction to reflect after reading the diff before forming findings |
| Parallel tool calling | YES — when examining multiple changed files simultaneously | NO | ADD — encourage parallel reads of changed files |
| File cleanup | NO — reviewer reads but does not create files | N/A | SKIP |
| `<avoid_overengineering>` | NO — not applicable to a reviewer's output | N/A | SKIP |
| Confidence-based assertions | YES — reviewer findings currently carry no confidence signal; [BLOCKING] vs [ADVISORY] is severity, not confidence | PARTIAL — the severity taxonomy (BLOCKING/ADVISORY) exists but there is no mechanism for the reviewer to express "I think this is a violation, but I may be missing context" vs. "This is unambiguously wrong" | ADD — a confidence qualifier for findings where the reviewer cannot fully verify the context |

**Proposed additions with exact text:**

**Addition 1: Thinking/reflection guidance (add after the "Changed Files" section header)**

Location: After the "Changed Files" block, before "What Implementer Claims They Built"

```
Before forming any findings, read all changed files. Build a complete picture of
what was implemented before evaluating whether it matches the spec. Findings formed
after reading only part of the diff frequently miss context that changes the verdict.
```

**Addition 2: Parallel file reads (add to the "Changed Files" section)**

Location: In the "Changed Files" block, after the git diff instruction

```
When multiple files changed, read them in parallel where possible — run git diff
and read all changed files simultaneously rather than one at a time.
```

**Addition 3: Confidence qualifier for findings (add to the "Report" section, after the PASS/FAIL taxonomy)**

Location: After the existing PASS/FAIL/REPORT_INCOMPLETE taxonomy, before the final "Note" line

```
For findings where you cannot fully verify due to missing context (e.g., a type
mismatch you suspect but cannot confirm without seeing the consuming code), tag
the finding with [UNVERIFIED] and describe what additional context would resolve it:

- [BLOCKING] [CONTRACT] [UNVERIFIED]: [finding] — needs: [what context would confirm]

The controller will decide whether to provide the missing context or treat the
finding as blocking by default.
```

---

### code-quality-reviewer-prompt-v0.1.md

**Current state summary:** This is a dispatch stub, not a direct prompt template. It delegates to the `superpowers-code-reviewer` agent via the Task tool. The stub appends a checklist of additional items (dead code, contract compliance, file responsibility, file size). After prior phases, Area 1 confirmed the dead code rule language is warranted and no de-escalation was needed. Area 8 confirmed no role statement is needed in the stub (it belongs in the agent file). Area 2 confirmed the stub is not negative-dominant.

The stub's structure limits what can be added here — any behavioral guidance must be added either as additional checklist items or in the agent file (`agents/code-reviewer.md`).

**Best practice patterns applicable:**

| Pattern | Applicable? | Already Present? | Recommendation |
|---------|------------|-----------------|----------------|
| `<investigate_before_answering>` | YES — the code reviewer should read changed files before forming opinions | NOT IN STUB — the agent file has no explicit investigate-first instruction; it describes what to review but not the read-before-opine discipline | ADD to agent file (see agents/code-reviewer.md section below) |
| Thinking guidance | YES — the reviewer reads many files and forms structured findings | NOT IN STUB | ADD to agent file |
| Parallel tool calling | YES — reading multiple changed files simultaneously | NOT IN STUB | ADD to agent file or as a stub checklist item |
| File cleanup | NO — reviewer does not create files | N/A | SKIP |
| `<avoid_overengineering>` | NO — not applicable to reviewer output | N/A | SKIP |
| Confidence-based assertions | YES — same rationale as spec reviewer | NOT IN STUB | ADD — as a new item in the stub's supplemental checklist |

**Proposed additions with exact text:**

**Addition 1: Confidence qualifier (add to the stub's supplemental checklist, after the contract compliance item)**

Location: After "If Contract Constraints were provided: does the implementation honor them?..." bullet

```
- For any finding where you cannot confirm the severity without additional context
  (e.g., a potential architectural issue that might be intentional, or a pattern
  that looks wrong but might follow a convention you haven't seen), label it as
  [NEEDS_CONTEXT] and describe what context would confirm or dismiss it. Do not
  classify uncertain findings as Minor to avoid surfacing them — surface them with
  the [NEEDS_CONTEXT] label instead.
```

**Note on parallel tool calling and thinking guidance:** These belong in `agents/code-reviewer.md` rather than the stub, since the stub only configures the dispatch. See the agent analysis below.

---

### agents/code-reviewer.md

**Current state summary:** The strongest of the four files. Has a clear Senior Code Reviewer role statement (confirmed good by Area 8). The five numbered review sections (Plan Alignment, Code Quality, Architecture, Documentation, Issue Identification) are well-structured. The Communication Protocol section addresses escalation. No prior-phase changes were needed for this file in Areas 1, 2, or 8.

**Best practice patterns applicable:**

| Pattern | Applicable? | Already Present? | Recommendation |
|---------|------------|-----------------|----------------|
| `<investigate_before_answering>` | HIGHLY APPLICABLE — the agent reviews code and must read it before forming opinions | IMPLICIT — the numbered sections say "review code for..." and "check for..." but nowhere does the agent explicitly read files before forming opinions. The sections describe what to assess but not the read-first discipline | ADD — an explicit read-before-assess instruction early in the agent prompt |
| Thinking guidance | YES — the agent reads multiple changed files and must synthesize complex findings | NO | ADD — a brief reflection instruction after tool use |
| Parallel tool calling | YES — when reading multiple changed files for a review | NO | ADD — a one-line parallel-reads instruction |
| File cleanup | NO — reviewer does not create files | N/A | SKIP |
| `<avoid_overengineering>` | NO — reviewer is evaluating overengineering, not doing it | N/A | SKIP |
| Confidence-based assertions | YES — the current finding taxonomy (Critical/Important/Suggestion) is severity-only. Reviewers cannot express "I'm uncertain this is actually wrong" vs. "This is unambiguously wrong" | NO | ADD — a NEEDS_CONTEXT label in the issue taxonomy |

**Proposed additions with exact text:**

**Addition 1: Investigate-first + parallel reads (add before "When reviewing completed work, you will:")**

Location: After the opening role statement and before the numbered review sections

```
Before forming any findings, read all changed files. Use the git diff to identify
the scope of changes, then read each changed file in full context. When multiple
files changed, read them in parallel to build complete context before evaluating
any single file in isolation. Findings formed without reading the full change set
frequently misattribute causality or miss context that explains an unusual pattern.
```

**Addition 2: Thinking reflection (add to the Communication Protocol section, item 7)**

Location: As a new numbered item in the "Communication Protocol" section, before the closing summary sentence

```
7. After reading all changed files and before writing findings, take a moment to
   consider whether your initial impressions hold up across the full context. A
   pattern that looks wrong in one file sometimes reflects a constraint visible only
   in another file you've already read.
```

**Addition 3: NEEDS_CONTEXT finding label (add to Issue Identification section, item 5)**

Location: In the "Issue Identification and Recommendations" section, after the Critical/Important/Suggestions taxonomy

```
For findings where you cannot determine severity without additional context (e.g.,
a pattern that might be intentional per a convention you haven't seen, or a
potential architecture issue that might reflect a constraint outside the diff),
classify it as:

**Needs Context** — Cannot determine severity without additional information.
Describe what context would resolve the finding (e.g., "Is this pattern consistent
with the project's error handling convention? If yes, dismiss; if no, Critical.").

Do not classify uncertain findings as Suggestions to avoid surfacing them. Surface
them as Needs Context instead — the controller can provide the missing context or
escalate to the human.
```

---

## Cross-Template Findings

### Pattern: Investigate-first is implicit, not explicit

All three prompt templates (implementer, spec-reviewer, code-quality-reviewer stub) instruct the agent to "read" specific things, but none generalizes this into the formal `<investigate_before_answering>` principle: never form an opinion about code you haven't read. The agent file makes the same assumption. The implementations are correct but the principle is missing, meaning a fresh subagent can form opinions based on the task description alone if the task description seems sufficient.

The proposed additions make this explicit in each template's appropriate voice:
- Implementer: "never write code that assumes something without verifying it first"
- Spec reviewer: "read all changed files before forming any findings"
- Code reviewer agent: "read all changed files before forming any findings; read in parallel"

### Pattern: Thinking guidance is entirely absent

None of the four files contains any instruction to reflect on information gathered before proceeding to conclusions or actions. The best practices doc specifically identifies this as high-value for tool-use-heavy workflows: "After receiving tool results, carefully reflect on their quality and determine optimal next steps before proceeding."

For reviewers, this maps to: read the diff, then think before writing findings. For the implementer, this maps to: read source files, then verify understanding before writing code. The proposed additions add this in each case without conflicting with the "ask questions first" instruction in the implementer prompt — they are complementary. Asking questions is appropriate when the task description itself is unclear; reflection is appropriate after reading source material.

### Pattern: Parallel tool calling is a missed efficiency

All three primary templates describe reading multiple files but none encourages doing so in parallel. For reviewers examining large diffs, this matters: sequential reads of 5-10 changed files significantly increases response latency. The model already does parallel reads naturally on Claude 4.6 per the best practices doc, but explicit guidance boosts this to ~100%. Given the volume of file reads in a typical review cycle, this is a meaningful efficiency gain.

### Pattern: Confidence labeling fills a real gap for reviewers

Currently, spec-reviewer and code-reviewer findings have severity labels (BLOCKING/ADVISORY, Critical/Important/Minor) but no mechanism for expressing uncertainty about whether a finding is actually valid. In practice, reviewers sometimes flag things they cannot fully confirm — the current taxonomy forces them to either classify at their best-guess severity (which may be wrong) or stay silent (which loses the finding). The proposed [UNVERIFIED] / [NEEDS_CONTEXT] label gives reviewers a third option that is honest about epistemic state and actionable for the controller.

This aligns with the best practices doc's research guidance ("Track your confidence levels") and is architecturally consistent with how DONE_WITH_CONCERNS works for implementers — it is a routing signal, not a quality signal.

### Pattern: File cleanup is a gap only in the implementer

The best practices doc notes that Claude 4.6 may create temporary files during iteration. The implementer is the only template where this is possible (reviewers read but don't write). The addition is a single line in "Your Job" and has no interaction with any prior phase change.

---

## Priority Order for Implementation

1. **agents/code-reviewer.md — investigate-first + parallel reads** (Addition 1): This is the highest-impact change because the agent is invoked for every task's quality review, it reviews multiple files, and the investigate-first principle is currently entirely implicit. No prior phases proposed changes to this file, so there is no interaction complexity.

2. **spec-reviewer-prompt-v0.1.md — thinking guidance + parallel reads** (Additions 1 and 2): Reviewers form findings based on code they read; the read-then-reflect sequence significantly improves finding quality. The parallel reads addition is pure efficiency.

3. **agents/code-reviewer.md — NEEDS_CONTEXT finding label** (Addition 3): Fills a structural gap in the finding taxonomy. Low implementation cost, high value for ambiguous findings in large codebases.

4. **spec-reviewer-prompt-v0.1.md — confidence qualifier** (Addition 3): Same rationale as code-reviewer NEEDS_CONTEXT. The [UNVERIFIED] label is the spec-reviewer equivalent.

5. **implementer-prompt-v0.1.md — investigate-first generalization** (Additions 1 and 2): The template already has specific read instructions; this generalizes them to a principle. Medium priority — the specific instructions already cover most cases.

6. **implementer-prompt-v0.1.md — parallel reads** (Addition 3): Pure efficiency. Low priority because the implementer typically reads fewer files than reviewers.

7. **implementer-prompt-v0.1.md — file cleanup** (Addition 4): Low priority, narrow impact.

8. **code-quality-reviewer-prompt-v0.1.md — confidence qualifier** (Addition 1): Low priority since the stub delegates to the agent; the agent's NEEDS_CONTEXT label (item 3 above) already covers this for the code quality reviewer.

---

## What Was Deliberately Not Added

**`<avoid_overengineering>` formal pattern in implementer:** The self-review Discipline section ("Did I avoid overbuilding (YAGNI)?") and the Code Organization section already cover this adequately. Adding the formal XML pattern at the top would create redundancy with the self-review section and conflict with the Area 8 role statement ("build exactly what the spec asks"), which encodes the same constraint as identity. Three places saying the same thing is too many.

**Thinking guidance in implementer at high volume:** The best practices doc warns that Claude Opus 4.6 may overthink with large or complex system prompts. The implementer prompt is already long. Adding extensive thinking guidance risks increasing latency. The proposed additions are minimal (two sentences) and targeted to a specific inflection point (post-source-file-read), not general "think more" guidance.

**Parallel tool calling in implementer as a formal `<use_parallel_tool_calls>` block:** The formal XML block from the best practices doc is designed for system prompts in API-direct usage. The implementer prompt is a Task tool dispatch — a natural language instruction ("read them in parallel rather than sequentially") is the appropriate form here, not an XML directive.
