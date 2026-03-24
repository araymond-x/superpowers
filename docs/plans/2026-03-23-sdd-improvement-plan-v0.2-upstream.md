# SDD Improvement Plan v0.2 — Upstream Quality Gates

> **Extends**: v0.1 plan (Iterations 1-5, focused on plan writing and SDD execution)
> **Scope**: Upstream pipeline stages that feed INTO the SDD execution loop
> **Test Case**: Statement Reconciliation handoff package, spec, and plan review

---

## Problem Statement

The v0.1 improvements address what happens DURING implementation (plan decomposition, controller discipline, subagent feedback, completion gates). But the Statement Reconciliation incident showed that flawed inputs entered the pipeline at three upstream stages:

1. **Handoff package** — External agent produced code that wasn't copy-paste ready, with type assumptions buried in prose
2. **Plan review** — Reviewer lacked mechanical verification checks and source file access
3. **Spec quality** — 1347-line spec mixed definitive decisions with historical alternatives, forcing the plan writer to summarize and introducing drift

If Superpowers guides the entire pipeline, each upstream stage needs the same rigor we applied to the downstream execution.

---

## Iteration 7: Handoff Package Acceptance Gate

**Problem**: An external agent produces a handoff package. The receiving agent (Superpowers brainstorming or writing-plans) accepts it as-is with no structured verification. The handoff's code snippets may not be executable, its type declarations may be buried, and it ships no acceptance test.

**Root Cause**: No "handoff acceptance" skill or protocol exists. The handoff is treated as a trusted input.

**Proposed Solution**: Create a new skill or skill section that defines a **Handoff Acceptance Protocol** — a structured gate that any handoff package must pass before being consumed by the brainstorming or writing-plans skills.

### Handoff Acceptance Checklist

The receiving agent (or a dispatched reviewer subagent) must verify:

| Check | What It Catches |
|-------|----------------|
| **Executable snippets** | Every code snippet in the handoff must be syntactically valid and runnable. Imports must be present. If a snippet is illustrative, it must be labeled `pseudocode`. | Wrong code that gets copy-pasted into plans |
| **Contract summary at top** | A "Contract Constraints" section must exist within the first 50 lines — field types, formats, invariants. Not buried in prose. | Type assumptions hidden in the middle of a 408-line document |
| **Acceptance fixtures** | At least one sample input/output pair must exist in a machine-readable format (JSON, not prose). The sample must include edge cases (empty fields, format variations). | Fixtures that don't match real output |
| **Acceptance test** | A runnable test that loads the fixture and verifies it matches the declared contract. If the handoff doesn't include one, the receiving agent creates one as the first action. | No ground truth anchor |
| **Document authority declaration** | The handoff must state which document is authoritative for each concern (types, behavior, naming). If the handoff conflicts with a spec, the declaration says which wins. | Cross-document drift |
| **Open decisions explicitly marked** | Any decisions the handoff leaves open must be listed in a "Decisions Still Open" table, not buried in text. | Plan writer inherits ambiguity silently |

### Where This Lives

Option A: New section in `brainstorming/SKILL.md` (since brainstorming is where external inputs enter the pipeline)
Option B: New standalone skill `handoff-acceptance/SKILL.md` that brainstorming invokes when a handoff package is referenced
Option C: New section in `writing-plans/SKILL.md` (since the plan writer is the first agent to consume the handoff)

**Recommended: Option B** — a standalone skill is reusable across contexts (brainstorming, planning, even SDD when a mid-implementation handoff arrives).

### Test Against Reconciliation

Evaluate: If the handoff acceptance protocol had been applied to the v3 handoff package, would it have caught:
- The buried type declarations (amounts as strings) → YES (Contract summary at top)
- The non-executable code snippets → YES (Executable snippets check)
- The missing acceptance test → YES (would have created one, anchoring types)
- The rate field mapping gap → PARTIAL (depends on "open decisions" check)

---

## Iteration 8: Plan Review Rigor

**Problem**: The plan-document-reviewer prompt checks 4 high-level categories with no mechanical verification. The reviewer doesn't receive source contract files. The v0.1 writing-plans skill added 9 new review categories to the skill text, but the actual reviewer prompt template was never updated to match.

**Root Cause**: The reviewer prompt and the skill text are out of sync. The skill describes what should be checked but the reviewer subagent only sees its prompt, not the skill text.

**Proposed Solution**: Create `plan-document-reviewer-prompt-v0.1.md` that:

### Enhanced Reviewer Capabilities

1. **Receives source files, not just plan + spec**
   - Controller MUST include paths to handoff packages, source contracts, and schema files
   - Reviewer reads source files independently — doesn't rely on the plan's description of them

2. **Mechanical verification checklist** (all 13 categories from v0.1 writing-plans skill)
   - The reviewer prompt must contain the full checklist, not reference it by name
   - Each category includes specific instructions, not just a label

3. **Cross-document consistency audit**
   - Reviewer compares plan assertions against handoff package and spec
   - If the plan says "amounts are numeric" but the handoff says "amounts are strings", that is a blocking issue
   - Minimum 3 representative fields traced end-to-end: handoff → spec → plan → task code snippet

4. **Snippet verification**
   - Reviewer reads at least 3 code snippets from the plan
   - For each: verifies imports, field names, and types against source files
   - Labels each as: VERIFIED / MISMATCH / ILLUSTRATIVE-ONLY

5. **Size and complexity assessment**
   - If plan exceeds 800 lines without modular decomposition: flag as blocking
   - If any single task exceeds 200 lines: flag as blocking
   - If task count exceeds 10 without Write-Scope Partitioning table: flag as blocking

### Test Against Reconciliation

Evaluate: If the enhanced reviewer had reviewed the v1.0 implementation plan against the handoff package and spec, would it have caught:
- The string-vs-numeric type mismatch in code snippets → YES (snippet verification + cross-document audit)
- The 2816-line plan size → YES (size assessment, blocking)
- The exception name drift → YES (cross-document consistency)
- The missing rate field mapping → YES (end-to-end field trace)
- The missing write-scope partitioning → YES (blocking for subagent plans)

---

## Iteration 9: Spec Conciseness & Implementability

**Problem**: The spec was 1347 lines with a 75-decision log that mixed definitive decisions with historical alternatives. The "Options Considered" column and "Rationale" column are valuable during brainstorming but are noise for implementation. A plan writer working from a 1347-line spec must summarize, introducing drift.

**Root Cause**: The brainstorming skill produces a spec optimized for the brainstorming process (exploration, alternatives, rationale) but doesn't transform it into an implementation-ready format. The same document serves two audiences with different needs.

**Proposed Solution**: Add a **Spec Distillation Step** between brainstorming and writing-plans.

### Spec Distillation

After the spec is approved by the spec reviewer and the user, but before invoking writing-plans, the brainstorming skill produces a **distilled spec** — a companion document that contains ONLY definitive decisions.

#### Distillation Rules

1. **Decision log → Decision summary**: Strip "Options Considered" and "Rationale" columns. Keep only "Decision" and "Chosen" columns. The implementation agent needs to know WHAT was decided, not WHY.

2. **Historical references removed**: Prior art, earlier designs, and "we considered but rejected" text is stripped. Only the current design remains.

3. **Size target**: Distilled spec should be <500 lines. If the original spec is 1347 lines, the distilled version should be ~400-500 lines.

4. **Contract facts promoted**: Any field types, format constraints, or invariants are moved to a "Contract Facts" section at the top of the distilled spec — not buried in decision rationale.

5. **Ambiguity flag**: Anything in the original spec that was ambiguous or had multiple valid interpretations is either resolved in the distilled version or flagged as "Open Decision — plan writer must resolve."

#### Two-Document Model

| Document | Audience | Purpose | Size |
|----------|----------|---------|------|
| `*-design.md` | Humans, brainstorming, future reference | Full decision log with rationale, alternatives, history | 500-1500 lines |
| `*-design-distilled.md` | Plan writer, implementation agents | Definitive decisions only, contract facts first | <500 lines |

The plan writer consumes the distilled spec, NOT the full design. The full design is retained for human reference and future context.

#### Spec Distillation Review

After distillation, dispatch a reviewer subagent to verify:
- Every definitive decision from the original spec appears in the distilled version
- No decision was lost, inverted, or reinterpreted during distillation
- No historical/alternative text remains
- Contract facts are promoted to the top
- Total size is under 500 lines

### Where This Lives

Add as a new step in `brainstorming/SKILL.md`, between step 7 (spec review loop) and step 8 (user reviews written spec):

```
7.5. **Distill spec for implementation** — produce `*-design-distilled.md` with definitive decisions only
```

Or as a standalone skill `spec-distillation/SKILL.md` that brainstorming invokes after spec approval.

### Test Against Reconciliation

Evaluate: What would a distilled version of the 1347-line reconciliation spec look like?
- 75 decisions × ~2 lines (Decision + Chosen) = ~150 lines for decision summary
- Purpose + architecture + file references = ~50 lines
- Contract facts (field types, formats) = ~50 lines
- Component descriptions (what each UI piece does) = ~150 lines
- **Estimated distilled size: ~400 lines** (vs 1347 original)
- **Signal-to-noise improvement**: All "Options Considered" and "Rationale" removed (~600 lines of alternatives text eliminated)

---

## Metrics for New Iterations

### M8: Handoff Acceptance Pass Rate
- **Baseline**: 0% (handoff accepted with no structured verification)
- **Target**: 100% of handoff packages pass acceptance checklist before consumption
- **Measurement**: Count checklist items passed vs total

### M9: Plan Review Catch Rate
- **Baseline**: 0 of 9 plan-review-level issues caught by reviewer (all found post-hoc by aws-explore agent)
- **Target**: >80% of mechanical issues caught during plan review
- **Measurement**: Run enhanced reviewer against v1.0 plan, count issues found vs known issues

### M10: Spec Distillation Compression Ratio
- **Baseline**: N/A (no distillation step exists)
- **Target**: Distilled spec is <40% of original spec line count
- **Measurement**: `wc -l` on both documents

### M11: Spec Completeness Preservation
- **Baseline**: N/A
- **Target**: 100% of definitive decisions from original spec appear in distilled version
- **Measurement**: Distillation reviewer checks every decision

---

## Execution Priority

| Iteration | Effort | Impact | Dependencies |
|-----------|--------|--------|-------------|
| 8: Plan Review Rigor | Low (update one prompt template) | High (catches most plan-level issues) | None — can start immediately |
| 9: Spec Distillation | Medium (new step in brainstorming) | High (reduces drift from spec to plan) | None |
| 7: Handoff Acceptance | Medium (new skill) | High (catches upstream contract errors) | None |

**Recommended order: 8 → 9 → 7** — Plan review is the lowest-effort highest-impact change (one prompt template update). Spec distillation reduces the input size for all downstream consumers. Handoff acceptance is the most structurally novel (new skill) and should be last.

---

## Combined Improvement Roadmap

| Phase | Iterations | Focus |
|-------|-----------|-------|
| **Phase 1 (Complete)** | 1-5 | Plan writing + SDD execution pipeline |
| **Phase 2 (This Plan)** | 7-9 | Upstream quality gates (handoff, review, spec) |
| **Phase 3 (Future)** | 6 + 10+ | Plan quality rules integration + real-project validation |
