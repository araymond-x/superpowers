# Pydantic Phase 1 — Session Continuation Handoff

**Date created:** 2026-04-24
**Handoff type:** Intra-feature session continuity (not cross-team, not cross-agent-pipeline)
**Reason:** Context preservation — prior session accumulated exploratory brainstorming content; a fresh session will run distillation → worktree setup → writing-plans transition with cleaner context
**Git state at handoff:** HEAD = `92c78c7` on `main`

---

## Required Reading Order (For Resuming Session)

Read in this order before taking any action:

1. **This document** — session state + next steps
2. **`docs/specs/2026-04-24-pydantic-phase-1-design.md`** — the full Phase 1 spec (~750 lines, approved after 2-pass spec review)
3. **`docs/plans/2026-04-24-pydantic-meta-design.md`** — cross-phase architecture decisions the spec references
4. **`docs/external-references/2026-04-23-pydantic-adoption-plan.md`** — 17-candidate inventory across all 6 phases (context for why this particular scope)
5. **`CLAUDE.md`** (fork root) — fork conventions, especially "Testing" + "Output Path Convention" + "Skill Invocation Rule"

You do **NOT** need to re-read:
- `docs/external-references/2026-04-21-*.md` (the LinkedIn source material) — already distilled into the adoption plan
- The full brainstorming dialogue — every decision is captured in the 11-row locked decisions table below

---

## State At Handoff

### What's Complete

| Brainstorm step | Status | Artifact |
|-----------------|--------|----------|
| 1. Explore project context | ✅ | N/A (session work) |
| 2. Clarifying questions | ✅ | 11 locked decisions (see below) |
| 3. Propose approaches | ✅ | Approach 3 chosen (full + forward-compat) |
| 4. Present design (7 sections) | ✅ | User-approved section-by-section |
| 5. Write design doc + commit | ✅ | `docs/specs/2026-04-24-pydantic-phase-1-design.md` (commit `5b0324b`) |
| 6. Spec review loop | ✅ | 2-pass approved (commit `92c78c7`) |

### What's Pending

| Step | Next action |
|------|-------------|
| **7. Distill spec for implementation** | **START HERE** — produce `docs/specs/2026-04-24-pydantic-phase-1-design-distilled.md`, dispatch distillation reviewer, run `check-distillation.sh` |
| 7.5 Distillation review | Dispatch distillation-reviewer subagent; fix until approved (max 3 iterations) |
| 8. User reviews written spec | After distillation, ask user to review both docs before proceeding |
| 9. Set up worktree | Invoke `superpowers:using-git-worktrees` for implementation isolation |
| 10. Transition to writing-plans | Invoke `superpowers:writing-plans` with distilled spec as primary reference |

---

## Locked Decisions (DO NOT RE-LITIGATE)

These 11 decisions are closed. The prior session walked through extensive dialogue on each. Do not reopen them without explicit user permission:

| # | Decision | Choice |
|---|----------|--------|
| 1 | Phase 1 scope | A3 Plan + B4 HandoffPackage + cross-phase meta-design doc |
| 2 | Format | YAML frontmatter + markdown body (both artifacts) |
| 3 | Dependency | Pydantic v2.7+ only (NO Instructor — fork doesn't call API directly) |
| 4 | Migration | Hard cutover, no migration script, archived plans stay archival |
| 5 | Pre-ship test | Yes, against plans post 2026-04-08 (recency cutoff is deliberate) |
| 6 | Model location | `skills/scripts/models/` (neutral location, not per-skill) |
| 7 | Schema versioning | Validator-pinned (producers can't game version); `--schema-version N` forensic flag |
| 8 | YAML/Pydantic errors | Split into separate blocks (distinct failure layers) |
| 9 | Exit codes | 0 pass / 1 producer-fix / 2 infrastructure |
| 10 | Bypass env var | `SUPERPOWERS_VALIDATOR_BYPASS=1` — included (emergency unblock, stderr warning) |
| 11 | Approach tier | Approach 3 (full Phase 1 + forward-compat via schema versioning) |

---

## Subtle Context To Preserve

### Two-Base-Class Pattern (Important Correction From Review)

The spec uses **two** base classes, not one. This was corrected during spec review:

- `StrictModel(BaseModel)` — for nested types (Task, Module, SharedConstant, FieldType, Sample, etc.) — enforces `extra="forbid"` but does NOT require `schema_version`
- `SchemaVersionedModel(StrictModel)` — for top-level artifacts (Plan, HandoffPackage) — adds required `schema_version: int` + pinning check

**Rationale:** if every nested type inherited `SchemaVersionedModel`, every list entry in YAML would need its own `schema_version: 1` line (absurd verbosity). Only artifacts that exist as files on disk need versioning.

### Pure Model / External I/O Split

Pydantic models validate **data shape only**. Filesystem / network / subprocess I/O lives in the CLI wrapper. Specifically:

- `HandoffPackage` model validates `samples: list[Sample]` shape
- CLI wrapper (`validators.py` handoff subcommand) checks each `sample.path` exists on disk AFTER model validation succeeds
- This avoids Pydantic-v2 `ValidationInfo` context-injection complexity AND makes models unit-testable without filesystem mocking

This split is codified in meta-design Section 5.3 as a cross-phase locked pattern.

### Distinct Error Block Headers

Three distinct error-block headers exist, each for a distinct failure layer:
- `YAML PARSE FAILED` (YAML syntax before Pydantic runs)
- `VALIDATION FAILED` (Pydantic schema/validator failure)
- `SAMPLE FILE MISSING` (filesystem check after Pydantic passes — CLI wrapper only)

Each serves a distinct producer-facing purpose. Don't collapse them into a single generic block.

### Forensic Escape Hatch

`--schema-version N` on the CLI is intended **only for humans doing archival review**. Hooks NEVER use it. Do not propagate this flag to hook invocations in the plan — that would defeat the validator-pinning property.

---

## Known Advisories From Spec Review (Preserved For Planner, Not For Brainstorm)

These were flagged as non-blocking but worth preserving so the planner picks them up:

1. **`jq` availability** — hook JSON wrapping uses `jq -Rs .`. Install-verify should assert `jq` is on PATH. If unavailable, hook should emit an infrastructure-failure message rather than a confusing `jq: not found`.
2. **`FormatRule.applies_to` uniqueness** — currently `list[str]`; duplicates would pass silently. Phase 2 consideration if it surfaces.
3. **Pydantic `ctx.expected` shape test** — `err["ctx"]["expected"]` for `literal_error` is technically not part of Pydantic's public API contract. Unit test should pin the exact shape against installed Pydantic version.

These are already in the spec's Acceptance Criteria — no action needed in the resumed session unless the planner raises them.

---

## Pitfalls / Traps To Avoid In The Resumed Session

1. **Don't read the full LinkedIn source material unless strictly needed.** The 3 docs in `docs/external-references/` are context-heavy and already distilled. The adoption plan is the summary you need.

2. **Don't re-design.** The distillation step is about *reduction*, not refinement. If something feels wrong during distillation, pause and ask the user rather than silently editing the design.

3. **Don't invoke implementation skills prematurely.** The brainstorming workflow's terminal state is `superpowers:writing-plans`, NOT `frontend-design`, `mcp-builder`, `subagent-driven-development`, etc. Only invoke writing-plans.

4. **Don't commit the distillation without running `check-distillation.sh`.** The script greps for exploration artifact patterns ("Options Considered", "Rationale", "we considered"). A distilled spec that contains these has failed distillation.

5. **Worktree convention (step 9):** worktrees go at `<project-root>/.worktrees/<feature-name>/`. Branch name matches feature name. Start the worktree session FROM the worktree directory (hooks receive CWD from session start, not from `! cd`).

6. **SDD SKILL.md word count:** currently 5029 words (over the 5000 soft limit). The spec calls for updating it; any addition must first extract content to `references/` to offset. See CLAUDE.md for the authoritative count. Re-check with `wc -w skills/subagent-driven-development/SKILL.md` before editing.

---

## Resumption Verification Checklist

Before doing any work, the new session should:

1. `git log --oneline -3` → confirm HEAD is `92c78c7`
2. `ls docs/specs/2026-04-24-pydantic-phase-1-design.md` → file exists, ~750 lines
3. `ls docs/plans/2026-04-24-pydantic-meta-design.md` → file exists
4. `find skills/scripts/models/ 2>/dev/null` → should return **nothing** (implementation hasn't started — this is expected)

If any check fails, stop and surface to user before proceeding.

---

## Artifacts Produced This Session (Persisted)

| Path | Purpose | Commit |
|------|---------|--------|
| `docs/external-references/2026-04-21-claude-code-production-guardrails.md` | LinkedIn source (DO/DON'T infographic + companion post) | `5b0324b` |
| `docs/external-references/2026-04-21-production-guardrails-gap-analysis.md` | Initial fork-vs-DO/DON'T gap analysis | `5b0324b` |
| `docs/external-references/2026-04-23-pydantic-adoption-plan.md` | Full 17-candidate inventory across 6 phases | `5b0324b` |
| `docs/specs/2026-04-24-pydantic-phase-1-design.md` | **Phase 1 spec** (approved) | `5b0324b` → `92c78c7` |
| `docs/plans/2026-04-24-pydantic-meta-design.md` | **Cross-phase meta-design** (companion) | `5b0324b` → `92c78c7` |
| `tests/fixtures/honesty-checks/2026-04-11-minimum-payment-extraction.md` | Real honesty-check response for future Phase 3 schema design | `5b0324b` |
| `docs/handoffs/2026-04-24-pydantic-phase-1-session-continuation.md` | **This document** | (upcoming commit) |

---

## First Action For Resumed Session

1. Invoke `superpowers:using-superpowers` skill (session-start hygiene)
2. Read this document fully
3. Invoke `superpowers:brainstorming` skill
4. Create TodoWrite tasks 7–10 (distillation, user review, worktree, writing-plans)
5. Begin step 7 (spec distillation) per the brainstorming skill's "Spec Distillation" section

The distillation target is `docs/specs/2026-04-24-pydantic-phase-1-design-distilled.md`. Target size: <500 lines (current full spec is ~750; distilled should strip rationale/exploration and promote contract facts to the top).

---

## If Anything Feels Wrong

- Conflict between this document and the spec → **spec wins** (it's the approved artifact, this doc is navigation)
- Conflict between this document and CLAUDE.md → **CLAUDE.md wins** for project conventions
- Conflict between the spec and the meta-design doc → surface to user (those should be consistent)
- Ambiguity in a locked decision → re-read the adoption plan's relevant section; if still ambiguous, surface to user
