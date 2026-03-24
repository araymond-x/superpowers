---
name: handoff-acceptance
description: "Use when receiving code, schemas, or documentation from another agent, team, or system that will feed into brainstorming, planning, or implementation"
---

# Handoff Acceptance

Verify that external handoff packages are accurate, complete, and implementation-ready before consuming them in brainstorming, planning, or implementation.

**Why this exists**: A handoff package that looks authoritative but contains wrong assumptions will poison every downstream step. Code snippets with wrong types get copy-pasted into plans. Type declarations buried in prose get missed. Missing acceptance tests mean no ground truth anchor. This skill catches those problems at the gate.

## When to Use

- Receiving a handoff package from another agent or team
- Starting brainstorming that references external schemas, APIs, or code
- Writing a plan that consumes external documentation
- Any time the phrase "handoff package", "reference implementation", or "sample code" appears in requirements

## Acceptance Checklist

The controller (or a dispatched reviewer subagent) should verify each item. A handoff package that fails any BLOCKING check must be returned for revision before consumption.

For each blocking check, pause before recording your verdict. Ask: If I were an implementer consuming this handoff tomorrow, would this gap cause me to write wrong code?

### 1. Contract Summary at Top [BLOCKING]

The handoff README/main doc must have a "Contract Constraints" or equivalent section within the first 50 lines containing:
- Field names (exact spelling and case)
- Field types (string, int, decimal, etc.)
- Format constraints (date formats, currency formats, etc.)
- Required vs. optional fields
- Any invariants or non-negotiable rules

If contract-critical information is buried beyond line 50 in prose, the handoff fails this check. The fix is to extract and promote it.

**Why**: In the incident that created this skill, amounts were defined as `"type": "string"` in a section 200 lines into the document. The plan writer never saw it. Every downstream agent assumed numeric types.

### 2. Executable Code Snippets [BLOCKING]

Every code snippet in the handoff must be one of:
- **Executable**: Syntactically valid, includes required imports, uses correct function signatures. Can be copied into a file and run.
- **Labeled pseudocode**: Explicitly marked as `# pseudocode` or `# illustrative — do not copy directly`. Not presented as if it can be pasted.

A code snippet that looks executable but is missing imports, uses wrong types, or references non-existent functions fails this check.

**Verification method**: For each snippet, check:
- Are imports present?
- Do function signatures match the actual API?
- Do field names match the Contract Summary?
- Are type assertions consistent with declared types?

### 3. Acceptance Fixtures [BLOCKING]

The handoff must include at least one machine-readable sample input/output pair:
- In a `samples/`, `fixtures/`, or `tests/` directory
- In JSON, YAML, or another parseable format (not prose descriptions)
- Including edge cases (empty fields, null values, format variations)
- Matching the types declared in the Contract Summary

If no fixtures exist, the receiving agent must create them from the handoff's descriptions and verify they match the contract before proceeding. Fixtures created from descriptions are the minimum bar for verifying internal consistency. Without them, type assumptions propagate directly into implementation.

### 4. Acceptance Test [RECOMMENDED]

A runnable test that loads a fixture and verifies it matches the declared contract. If the handoff doesn't include one, the receiving agent creates one as the FIRST action after acceptance.

This is the ground-truth anchor. Without it, type assumptions are validated only by reading — reading misses errors that tests catch mechanically.

### 5. Document Authority Declaration [RECOMMENDED]

If both a handoff and a spec exist for the same feature:
- The handoff must state which document is authoritative for each concern
- Where they conflict, the declaration says which wins
- Open decisions must be listed explicitly, not left as implicit conflicts

### 6. Open Decisions [RECOMMENDED]

Any decisions the handoff leaves open must be listed in a visible table:

```markdown
## Open Decisions

| # | Decision | Options | Must Be Resolved By |
|---|----------|---------|-------------------|
| 1 | Rate field mapping | See LOC-WF discussion | Plan writer |
```

Decisions buried in prose that could be interpreted multiple ways fail this check.

## Acceptance Process

See `references/acceptance-flow.dot` for the complete acceptance process flow diagram (Graphviz dot format). The process is linear: read README → check contract summary → verify snippets → check fixtures → verify fixtures match → check authority + open decisions → ACCEPTED.

## Acceptance Report

After running the checklist, produce an acceptance report:

```markdown
## Handoff Acceptance Report

**Package**: [path/name]
**Date**: [ISO date]
**Reviewer**: [controller or subagent]

### Checklist Results

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | Contract Summary at top | PASS/FAIL | [details] |
| 2 | Executable code snippets | PASS/FAIL | [N verified, M issues] |
| 3 | Acceptance fixtures | PASS/FAIL/CREATED | [details] |
| 4 | Acceptance test | PASS/CREATED/MISSING | [details] |
| 5 | Document authority | PASS/MISSING | [details] |
| 6 | Open decisions | PASS/MISSING | [N open decisions listed] |

### Contract Facts Extracted

[Copy the Contract Summary here for downstream consumption by brainstorming/writing-plans]

### Issues Found

- [issue with file:line reference]

### Verdict: ACCEPTED / REJECTED — [reason]
```

Save this report to the project docs directory. It becomes an input to the brainstorming skill's context exploration phase.

## Integration

- **brainstorming/SKILL.md**: When the user references external handoff packages, invoke handoff-acceptance before proceeding with design questions
- **writing-plans/SKILL.md**: When the plan's Source Contracts reference a handoff package, verify it was accepted. If not, run acceptance first
- **subagent-driven-development/SKILL.md**: During Plan Ingestion, if source files come from a handoff package, verify an acceptance report exists
