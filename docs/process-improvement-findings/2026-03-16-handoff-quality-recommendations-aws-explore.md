# Handoff Package Quality Recommendations for Multi-Agent Development

**Date**: 2026-03-16 17:05 MDT
**Author**: AWS-Explore agent (experiment specialist perspective)
**Source materials reviewed**:
- `docs/superpowers-process-improvement/2026-03-16-plan-review-findings-aws-explore.md`
- `docs/superpowers-process-improvement/2026-03-16-statement-reconciliation-lessons-learned.md`
- `docs/superpowers-process-improvement/ResponseCapture-CodexSuggestions-raw.txt`
- `docs/superpowers-process-improvement/ResponseCapture-Raw-statementcycle-1st pass.txt`
- `docs/plans/2026-03-11-statement-parsing-handoff/` (full package)
- `statement-parsing-experiment/implementation-plan-review-checklist.md`

---

## Executive Summary

The statement parsing handoff package from AWS-Explore was well-structured for human readers but insufficiently defensive for multi-agent execution pipelines. The implementing agent built a 17-task plan with 2800+ lines of code that faithfully encoded wrong assumptions about data types — assumptions the handoff package could have prevented with stronger contract specification. Three P1/P2 bugs (all string-vs-numeric mismatches) reached localhost testing before discovery. Every bug traced back to the same root cause: the handoff described field types in schema definitions (`"type": "string"`) but never surfaced this as a critical constraint in the integration sections that implementation agents actually read.

This report identifies 5 categories of improvement with 18 specific recommendations, organized by phase of the handoff-to-implementation lifecycle.

---

## Category 1: Contract Clarity in Handoff Packages

### Problem

The handoff README's "Expected Input/Output" section showed a JSON example with string amounts (`"-1,788.69"`), and the schema files declared `"type": "string"`. But the "Reconciliation Context" and "Production Validation Pipeline" sections described behavior in abstract terms that could be interpreted as numeric. An implementation agent reading the integration sections — which is what planners focus on — never encountered a clear, unambiguous statement like "all fields are strings; parse before math."

### Recommendations

**1.1 — Add a "Contract Constraints" section as the first integration-facing section**

Place this immediately after "Expected Input/Output" and before any behavioral description. Format it as a numbered list of non-negotiable facts about the data contract:

```markdown
## Contract Constraints (Non-Negotiable)

1. ALL amount fields are `"type": "string"` with commas preserved (e.g., `"-11,350.00"`).
   Parse with comma-stripping before any arithmetic. Do NOT use `float()` or `isinstance(float)`.
2. ALL date fields are `"type": "string"` in MM/DD/YY format (2-digit year).
3. ALL rate fields (APR, APY) are `"type": "string"` (e.g., `"28.99"` not `28.99`).
4. The `toolChoice` constraint guarantees schema compliance — malformed JSON is not possible.
5. Sign convention: credit card charges are positive, payments negative. Asset accounts: deposits positive, withdrawals negative.
```

**Why this matters**: Implementation agents scan for "how to use this" sections, not schema definitions. A contract that's only visible in JSON Schema `"type"` fields is effectively invisible to planners.

**1.2 — Include a "Wrong Way / Right Way" code block for the most critical parsing operation**

```markdown
### Amount Parsing — WRONG vs RIGHT

```python
# WRONG — will crash on "-11,350.00"
total = sum(float(tx["amount"]) for tx in transactions)

# RIGHT — strip commas first
def parse_amount(s: str) -> float:
    return float(s.replace(",", ""))

total = sum(parse_amount(tx["amount"]) for tx in transactions)
```
```

**Why**: A concrete failure example is more memorable and grep-able than a prose description. Subagents that receive the handoff text in their prompt will pattern-match on this.

**1.3 — Add explicit type annotations to sample output JSON**

Annotate the JSON example with inline comments marking the types:

```json
{
  "previous_balance": "2,936.31",   // STRING — parse before arithmetic
  "new_balance": "2,940.45",        // STRING — parse before arithmetic
  "purchase_apr": "28.99",          // STRING — not a float
  "amount": "-1,788.69"             // STRING — signed, commas preserved
}
```

**Why**: The existing sample shows strings but a skimming agent could interpret the values as "just happens to be quoted." Explicit annotations remove ambiguity.

---

## Category 2: Handoff-to-Plan Boundary Management

### Problem

Four of nine review findings (Category 1 in the plan review doc) were cross-document drift: the handoff said one thing, the plan said another, and the implementation agent had no single source of truth. The rate field mapping (LOC-WF `apr` -> `cash_advance_apr`) was resolved in the plan but left as an open question in the handoff. Gate severities were reclassified in the plan without noting the change from the handoff's definitions.

### Recommendations

**2.1 — Handoff packages must include a "Decisions Still Open" section with resolution protocol**

```markdown
## Open Decisions (Must Be Resolved Before Implementation)

| # | Decision | Options | Recommended | Resolved? |
|---|----------|---------|-------------|-----------|
| 1 | LOC-WF `apr` maps to which DB column? | `interest_rate` or `cash_advance_apr` | Check frontend code | NO |
| 2 | Gate 4 parser: strict or lenient? | Strict (fail on format noise) or lenient (strip $, commas) | Strict | NO |
```

**Resolution protocol**: When the planning agent resolves a decision, it must update this table in the handoff (same commit as the plan). This prevents the handoff from contradicting the plan.

**2.2 — Handoff packages should declare which document is authoritative for each concern**

```markdown
## Document Authority

| Concern | Authoritative Document | Notes |
|---------|----------------------|-------|
| What the model outputs (field names, types, format) | This handoff package | Derived from experiment |
| What the system does with the output (storage, UI, matching) | Implementation plan | Design decisions |
| Gate severity (hard reject vs soft warning) | Implementation plan | May reclassify experiment gates |
| Bedrock API call pattern | This handoff package | Proven in experiment |
```

**Why**: The implementation agent currently has to guess which document wins when they conflict. This eliminates that ambiguity.

**2.3 — Handoff README should include a "Changes Since Handoff" changelog that downstream agents maintain**

When the planning or implementation agent changes something the handoff described (e.g., reclassifying a gate severity), they append to a changelog section in the handoff README:

```markdown
## Post-Handoff Changes

| Date | Changed By | What Changed | Why | Plan Reference |
|------|-----------|--------------|-----|----------------|
| 2026-03-15 | Plan author | Gate 2 reclassified from "hard reject" to "approval gate" | Balance checksums that fail on minor rounding should not block the entire flow | Plan line 557 |
```

**Why**: Without this, the handoff becomes a snapshot that silently diverges from the plan. Future agents (or humans) reading the handoff get stale information.

---

## Category 3: Ground-Truth Artifacts for Multi-Agent Execution

### Problem

Subagents wrote code from plan descriptions without reading the actual schema files or sample outputs. The plan had 2800 lines of code that assumed numeric types. TDD validated those wrong assumptions because test fixtures also used numeric types. The entire pipeline was internally consistent but wrong relative to the actual Bedrock output.

### Recommendations

**3.1 — Handoff packages must include machine-readable "acceptance fixtures"**

Beyond the existing `samples/` directory (which contains full experiment output), add a dedicated `fixtures/` directory with minimal, annotated test data specifically designed for implementation testing:

```
handoff/
  fixtures/
    acceptance_credit_card.json    # Minimal credit card output (3 transactions)
    acceptance_deposit_account.json # Minimal deposit account output (2 transactions)
    acceptance_shared_pdf.json     # CHECK-WF + SAVE-WF from same PDF
    FIXTURES_README.md             # What each fixture tests and expected parse results
```

Each fixture should include:
- Raw model output (strings with commas, as Bedrock returns)
- Expected parsed values (floats, after correct parsing)
- Expected validation gate results

**Why**: The existing `samples/` directory was overlooked because it was nested and labeled as "sample outputs" not "test data." Dedicated acceptance fixtures with a README make their purpose unambiguous.

**3.2 — Handoff README should include a "First Test" section**

```markdown
## First Test (Run Before Writing Any Code)

Load `fixtures/acceptance_credit_card.json` and verify:
1. `parse_amount(fixture["transactions"][0]["amount"])` returns `-1788.69` (float)
2. `validate_balance_checksum(fixture["model_output"])` returns `{"pass": true}`
3. Amount field is `str`, not `int` or `float`

If your code fails these checks, your type assumptions are wrong. Read "Contract Constraints" above.
```

**Why**: This is the "ground-truth fixtures before implementation" recommendation from the lessons learned, made concrete in the handoff package itself.

**3.3 — Plans that reference handoff packages must include a "Contract Verification Task" as Task 0**

Before any implementation tasks, the plan should include:

```markdown
### Task 0: Contract Verification (Blocking)

1. Read handoff `fixtures/` directory
2. Write unit tests that load each fixture and verify:
   - All amount fields are strings
   - Parsing produces expected float values
   - Validation gates produce expected results
3. These tests must pass before any other task begins

**Why this blocks**: If these tests don't pass, every downstream task will encode wrong assumptions.
```

**Why**: This prevents the "subagents didn't read source files" failure mode. Task 0 forces the first code written to be contract-anchored.

---

## Category 4: Review Process Improvements

### Problem

The plan review process caught 9 issues — but only after implementation had already produced 3 bugs. The review checklist (`implementation-plan-review-checklist.md`) was created by the experiment agent and was focused on architectural correctness, not data contract verification. The subagent-driven-development skill's two-stage review was skipped entirely for speed. No mechanism existed to accumulate subagent deviations.

### Recommendations

**4.1 — Add "Data Contract Audit" to the plan review checklist**

The existing checklist covers correctness and architecture but not type-level contract verification. Add:

```markdown
## Data Contract Audit

- [ ] Every field consumed from the handoff has its type explicitly stated in the plan
- [ ] Plan code snippets use the correct type (string, not number, for amounts)
- [ ] Test fixtures in the plan match handoff sample output shapes exactly
- [ ] Any type conversion (string -> float) is explicitly shown with the parsing function
- [ ] No `isinstance(x, (int, float))` or `float(x)` without comma-stripping on handoff data
```

**Why**: The existing checklist would not have caught the string-vs-numeric bug because it didn't check at the type level.

**4.2 — Handoff author should produce a "Reviewer's Cheat Sheet"**

A compact, single-page document that tells the plan reviewer what to look for:

```markdown
## Reviewer's Cheat Sheet (Statement Parsing Handoff)

### Critical assumptions that MUST be preserved in any plan:
1. All amounts are strings with commas — never treat as numeric without parsing
2. CHECK-WF and SAVE-WF share one PDF — always two API calls
3. AMEX opening_date may be empty — must compute from statement chain
4. Gate 2 (balance checksum) is mathematical proof — if it passes, extraction is complete

### Fields most likely to be mishandled:
- `amount`: String "-1,788.69" not float -1788.69
- `apy`: String "3.65" not float 0.0365 (do NOT divide by 100)
- `interest_earned`: Extracted but NOT stored — no DB column needed

### If the plan contains any of these patterns, it's WRONG:
- `isinstance(amount, (int, float))`
- `float(tx["amount"])` without `.replace(",", "")`
- `apy / 100`
- Treating Gate 2 as a soft warning
```

**Why**: The experiment agent has deep domain knowledge about what goes wrong. This cheat sheet transfers that knowledge to the reviewer in the most scannable format possible.

**4.3 — Spec review must include a "contract trace" step**

Before approving any plan that consumes a handoff package:

1. Pick 3 representative fields from the handoff (one amount, one date, one rate)
2. Trace each field through the plan: extraction -> parsing -> validation -> storage -> API response -> UI display
3. At each step, verify the type is correct and any transformation is explicit

This is a 15-minute investment that would have caught all 3 bugs in this cycle.

**4.4 — Don't skip subagent reviews — but tier them**

The lessons learned identified that skipping all 34 reviews was a mistake. But 34 reviews is genuinely expensive. Tiered approach:

| Task Type | Review Level | Rationale |
|-----------|-------------|-----------|
| Tasks consuming external contracts (schemas, APIs, handoff data) | Full spec compliance + code quality | Highest risk of assumption drift |
| Tasks with complex logic (matching, validation, sign inversion) | Spec compliance only | Logic errors are hard to spot in summaries |
| Straightforward CRUD / UI wiring | Skip review, audit at end | Low risk, high volume |

This reduces 34 reviews to ~8-12 while covering the highest-risk tasks.

**4.5 — Implement a DEVIATIONS.md accumulator**

When the controller dispatches subagents, maintain a `DEVIATIONS.md` file that the controller appends to whenever:
- A subagent returns `DONE_WITH_CONCERNS`
- A subagent skips part of a task
- A subagent makes an independent decision not in the plan
- The controller observes a scope change

Format:

```markdown
## Deviations Register

| Task | Deviation | Subagent Decision | Impact | Follow-up |
|------|-----------|-------------------|--------|-----------|
| T10 | Dead code removal skipped | Functions still used by StatementsPage.tsx | Deferred removal | Track as tech debt |
| T15 | TestModeControls not wired into pages | Built components but no page imports | Feature unreachable | Wire in follow-up |
```

Review this file before merge. Any row without a "Follow-up" resolution is a blocking issue.

---

## Category 5: Structural Improvements to Handoff Package Design

### Problem

The handoff README was a single 400-line document that served multiple audiences: the human project owner, the planning agent, the implementation agent, and the review agent. Each audience needs different information at different detail levels. A planning agent needs the contract constraints and field mappings. An implementation subagent needs the API call pattern and parsing rules. A reviewer needs the cheat sheet and known pitfalls.

### Recommendations

**5.1 — Structure handoff packages with audience-specific sections**

```
handoff/
  README.md                    # Overview + changelog (human audience)
  CONTRACT.md                  # Data types, field conventions, constraints (planner/reviewer)
  INTEGRATION_GUIDE.md         # API patterns, code samples, error handling (implementer)
  REVIEWERS_CHEAT_SHEET.md     # Critical assumptions, anti-patterns (reviewer)
  fixtures/                    # Acceptance test data (implementer)
  schemas/                     # JSON schemas + prompts (reference)
  samples/                     # Full experiment output (reference)
```

**Why**: A monolithic README means every reader must scan 400 lines to find their relevant 50 lines. Multi-agent environments amplify this because each agent gets the full text in its prompt — noise reduces signal.

**5.2 — Every handoff should include a "Quick Start for Agents" block at the top of README**

```markdown
## Quick Start for Agents

**If you are a planning agent**: Read `CONTRACT.md` first. All field types are strings.
**If you are an implementation agent**: Read `INTEGRATION_GUIDE.md` and load `fixtures/` before coding.
**If you are a review agent**: Read `REVIEWERS_CHEAT_SHEET.md` for known anti-patterns.
**Critical constraint**: All amounts are strings with commas. Parse before arithmetic. See CONTRACT.md.
```

**Why**: Agents receive the README as context. The first 5 lines determine whether they absorb the critical constraints or skim past them.

**5.3 — Handoff packages should version-lock against the plan**

When the plan is approved, the handoff README should record the plan version and commit hash:

```markdown
## Plan Lock

- Plan: `docs/plans/2026-03-15-statement-reconciliation-ui-design.md` v1.1
- Plan commit: `abc1234`
- Any changes to the handoff after this lock require re-review of the plan
```

**Why**: Prevents silent drift where the handoff is updated but the plan still references the old version.

---

## Implementation Priority

| Priority | Recommendation | Effort | Impact |
|----------|---------------|--------|--------|
| P0 | 1.1 Contract Constraints section | 15 min per handoff | Prevents the #1 failure mode (type assumptions) |
| P0 | 3.2 "First Test" section | 10 min per handoff | Forces ground-truth anchoring before code |
| P0 | 3.3 Task 0: Contract Verification | 5 min per plan | Blocks implementation on wrong assumptions |
| P1 | 1.2 Wrong Way / Right Way examples | 10 min per handoff | Makes failures concrete and grep-able |
| P1 | 4.2 Reviewer's Cheat Sheet | 20 min per handoff | Transfers experiment domain knowledge |
| P1 | 4.4 Tiered subagent reviews | Process change | Reduces review cost while covering high-risk tasks |
| P1 | 4.5 DEVIATIONS.md accumulator | Process change | Makes subagent decisions visible |
| P2 | 2.1 Open Decisions section | 10 min per handoff | Prevents cross-document drift |
| P2 | 2.2 Document Authority table | 5 min per handoff | Eliminates "which doc wins" ambiguity |
| P2 | 5.1 Audience-specific structure | Restructure effort | Scales with project complexity |
| P2 | 5.2 Quick Start for Agents | 5 min per handoff | Improves agent context absorption |
| P3 | 1.3 Annotated sample JSON | 5 min per handoff | Belt-and-suspenders for type clarity |
| P3 | 2.3 Post-Handoff Changes changelog | Ongoing maintenance | Prevents stale handoff information |
| P3 | 4.1 Data Contract Audit checklist | 10 min one-time | Adds type-level review to existing checklist |
| P3 | 4.3 Contract trace step | 15 min per review | Catches field-level transformation errors |
| P3 | 5.3 Plan version lock | 2 min per approval | Prevents version drift |

---

## The Core Insight

The statement parsing handoff was good documentation — it accurately described the system. But it was written for comprehension, not for defense against misinterpretation. In a multi-agent pipeline, every ambiguity is a potential bug. The handoff described amounts as `"type": "string"` in JSON Schema definitions that implementation agents never read directly. It showed string examples in sample output that agents interpreted as "just happens to be quoted." It documented field conventions in prose that agents skimmed.

**The fix is not better documentation — it's documentation designed for the failure modes of its readers.** When the reader is an AI agent that will execute assumptions at scale, the handoff must be aggressively explicit about constraints, include concrete failure examples, and provide machine-testable acceptance criteria that anchor implementation before any code is written.

The three P0 recommendations (Contract Constraints section, First Test section, Task 0 verification) would have prevented all three bugs discovered in this cycle. Combined effort: ~30 minutes per handoff package.
