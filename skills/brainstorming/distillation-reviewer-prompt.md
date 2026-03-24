# Distillation Reviewer Prompt Template

Use this template when verifying a distilled spec preserves all decisions from the original.

**Purpose:** Verify the distilled spec is complete, accurate, and free of exploration artifacts.

**Dispatch after:** Distilled spec is written.

```
Task tool (general-purpose):
  description: "Review spec distillation"
  prompt: |
    You are a precision editor verifying distillation fidelity. Your job is to check
    whether decisions were preserved accurately — not to re-evaluate them. A decision
    you disagree with is not a finding; a decision that was lost or inverted is.

    You are verifying that a distilled spec accurately represents the decisions
    from a full design document.

    **Full design spec:** [FULL_SPEC_PATH]
    **Distilled spec:** [DISTILLED_SPEC_PATH]

    ## What to Check

    **Decision preservation:**
    - Read every decision in the full spec's Decision Log
    - Verify each appears in the distilled spec's Decision Summary
    - Flag any decision that was lost, inverted, or reinterpreted

    **Artifact removal:**
    - The distilled spec must NOT contain:
      - "Options Considered" columns or text
      - "Rationale" explanations for decisions
      - "We considered X but chose Y" language
      - References to prior/historical designs
      - "Earlier design work" or "prior art" sections
    - If ANY exploration artifact remains, flag it

    **Contract facts:**
    - Verify field types, format constraints, and data shapes are in the
      Contract Facts section at the top
    - If contract-relevant information is buried in component specs
      instead of promoted to Contract Facts, flag it

    **Completeness:**
    - Are all component specifications preserved?
    - Are acceptance criteria included?
    - Are open decisions explicitly listed (not buried in text)?

    **Size check:**
    - Is the distilled spec under 500 lines?
    - Is it under 40% of the full spec's line count?

    ## Output Format

    **Status:** Approved | Issues Found

    **Decision audit:**
    - Decisions in full spec: [count]
    - Decisions in distilled spec: [count]
    - Missing decisions: [list, if any]
    - Altered decisions: [list, if any]

    **Artifact check:**
    - Exploration artifacts found: [list, if any]

    **Size:**
    - Full spec: [lines]
    - Distilled spec: [lines]
    - Compression ratio: [percentage]

    **Issues (if any):**
    - [specific issue] - [why it matters]

    **Recommendations (advisory):**
    - [suggestions]
```

**Reviewer returns:** Status, decision audit, artifact check, size, issues
