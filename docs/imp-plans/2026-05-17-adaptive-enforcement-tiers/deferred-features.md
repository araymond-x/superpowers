# Adaptive Enforcement Tiers — Deferred Features (v1.1+)

> **Source**: Brainstorm session 2026-05-17, reviewer amendments
> **Purpose**: Track improvements identified during design that are out of scope for v1 but should be revisited

---

## v1.1: Computed Tier Recommendation

**What**: The writing-plans skill computes a recommended enforcement tier based on heuristics, not just task count.

**Why deferred**: Plan reviewer validates tier appropriateness manually in v1. Adding heuristic analysis to writing-plans adds complexity before tiers are proven in practice.

**Heuristics to evaluate**:
- Task count (baseline: 1-2 → micro, 3-8 → standard, 9+ → comprehensive)
- Whether tasks modify security-sensitive resources (auth, credentials, IAM) → bump up
- Whether tasks are pure config/documentation → eligible for downgrade
- Whether tasks span multiple infrastructure domains → bump up
- Whether the plan has a Write-Scope Partitioning table with mixed read/write access → bump up

**Evidence**: practerus M15 had 6 tasks (standard tier by count) but involved AWS SES, Cognito, Secrets Manager, and Bunny API — the controller correctly noted that subagent dispatch for `test -f` prerequisite checks was overhead, but the SES/Cognito/Secrets tasks needed full review. A computed recommendation would have flagged this as needing standard-tier despite being only 6 tasks.

**Acceptance criteria**: Plan author can override the recommendation with justification that the plan reviewer must approve.

---

## v1.1: Context Budget Estimation Integration

**What**: The manifest includes `estimated_context_per_task` from the plan. The hook warns when cumulative context exceeds thresholds via `additionalContext` injection.

**Why deferred**: Token estimation script (`estimate-task-tokens.py`) was skipped in every observed session. Fixing the script's usability is a prerequisite. The manifest infrastructure from v1 makes this straightforward to add later.

**Design sketch**:
- writing-plans computes per-task token estimates during planning
- Estimates stored in plan frontmatter or manifest
- Hook reads cumulative estimate and injects compression reminders
- Non-blocking — warning only, not a gate

---

## v1.1: Per-Module Context Summaries

**What**: `context-summary.py` supports per-module compression (archive completed module context, keep active module context fresh).

**Why deferred**: The `transition-module.py` script in v1 archives completed module reports. Per-module context summaries are a refinement of this — instead of just archiving files, produce a compressed summary of the completed module's outcomes that the new module's controller can reference.

**Design sketch**:
- On module transition, run `context-summary.py --module <module-name>` before archiving
- Summary captures: what was implemented, key deviations, unresolved concerns
- New module's controller gets a 1-page summary instead of reading all prior reports

---

## v1.1: Dispatch Pattern Customization

**What**: The manifest includes a `dispatch_pattern` field that the hook reads for dispatch detection, allowing projects to use custom description conventions.

**Why deferred**: v1's manifest-presence detection (`.sdd-session.json` exists → enforce) is sufficient. Custom dispatch patterns add complexity without clear demand.

**Potential need**: If teams adopt SDD with different dispatch description conventions, they'd need this. Monitor adoption first.

---

## Future: Cross-Artifact Validation (Pydantic Phase 3)

**What**: Validate consistency across manifest, plan, reports, and deviations (e.g., manifest says 8 tasks but plan has 10 headers; manifest says spec-review dispatched but report file is controller-written).

**Why deferred**: Requires the session manifest from v1 to exist first. Pydantic Phase 3 was already scoped for cross-artifact validation — the manifest becomes another artifact in that validation graph.

**Dependency**: v1 manifest schema (Pydantic model in `skills/scripts/models/sdd_session.py`)
