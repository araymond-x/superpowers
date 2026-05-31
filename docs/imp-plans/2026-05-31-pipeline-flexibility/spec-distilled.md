# Pipeline Flexibility — Distilled Implementation Spec

> **Source**: `docs/imp-plans/2026-05-31-pipeline-flexibility/spec.md` (v1.0, 5 decisions)
> **Distilled**: 2026-05-31
> **For**: Plan writer and implementation agents ONLY. For full rationale, see source.

## Contract Facts

- Plan model (`skills/scripts/models/plan.py`): `Plan` extends `SchemaVersionedModel`, `Task` extends `StrictModel`. Both use `extra="forbid"`. No schema version bump for new optional fields (precedent: `review_tier`).
- SDD SKILL.md is at 4753 words with 5000-word soft limit. New sections may require extracting existing content to `references/`.
- Dispatch log format: `task=N type={spec-review|quality-review|partner-review} ts=<ISO-8601>` — one entry per line, written by `sdd-pre-dispatch-hook.sh`. Implementer dispatches are NOT currently logged.
- `check-distillation.sh` takes a single path argument, returns JSON with `status: PASS|FAIL`. Already portable — no modifications needed.
- `controller-checkpoint.py` pre-completion phase currently has: honesty check, trace audit, minimum-tier ratio (≤50%). New checks append to the same phase.
- `validate-plan.py` already emits WARNING-level heuristic checks. New keyword check follows the same pattern.
- Hook uses `$PYTHON` (`$SUPERPOWERS_ROOT/.venv/bin/python3`) for PyYAML/Pydantic-dependent scripts.
- 4 active hooks in `~/.claude/settings.json`: `sdd-pre-dispatch-hook.sh`, `sdd-report-guard.sh`, `plan-validation-gate-hook.sh`, `session-start`.

## Open Decisions

| # | Decision | Options | Resolution Required By |
|---|----------|---------|----------------------|

(All decisions resolved)

## Decision Summary

| # | Decision | Chosen |
|---|----------|--------|
| D1 | Entry architecture | Parallel entry points (writing-plans gains direct-entry guardrails) |
| D2 | Verification task ceremony | Dispatch subagent, skip reviews (audit trail preserved) |
| D3 | Verification abuse prevention | 4-layer defense: plan-time warning, ratio cap, git reality check, restricted prompt |
| D4 | N2 scope | Investigation-only, findings doc + backlog rows, no code fixes |
| D5 | Plan structure | Single plan file, standard enforcement tier, ~10 tasks |

## Component Specifications

### C1: Plan Model Extension (`skills/scripts/models/plan.py`)

**Plan model** — add field:
```python
entry_mode: Literal["brainstorming", "direct"] = "brainstorming"
```
Informational audit trail. No downstream gates read it.

**Task model** — add field:
```python
task_type: Literal["implementation", "verification"] = "implementation"
```
Controls whether the task goes through the review cycle. Orthogonal to `review_tier`.

Both fields are optional with defaults — backwards-compatible, no schema version bump.

### C2: Writing-Plans SKILL.md — Direct Entry Path

Enhance Step 0.5 with:

1. **Conflict detection** (port from brainstorming Step 3.5, 4 branches):
   - `.active-feature` exists, dir doesn't → auto-clean, proceed
   - `.active-feature` exists, dir complete → auto-clean, proceed
   - `.active-feature` exists, dir has incomplete work → prompt: resume or archive
   - `.active-feature` exists, dir exists but no plan → prompt: resume or start fresh

2. **Worktree/branch guard**: If on `main`, offer worktree creation via `using-git-worktrees`. Allow proceeding on `main` with acknowledgment.

3. **Optional spec input**: If distilled spec provided, run `check-distillation.sh`. Record spec path in plan header's Source Contracts. Neither spec nor handoff required.

4. **Entry mode recording**: Set `entry_mode: direct` in plan YAML frontmatter when no brainstorming artifacts exist in the feature directory.

5. **Update Context block**: Describe direct entry as first-class path, not fallback.

### C3: SDD Pre-Dispatch Hook Changes (`sdd-pre-dispatch-hook.sh`)

**New: Implementer dispatch logging.** In Stage 2 (implementer detection), add dispatch log entry: `task=N type=implementer ts=<ISO-8601>`. Non-breaking — Check 4c only greps for reviewer entries.

**New: Task-type-aware check skipping.** Read `task_type` from plan YAML frontmatter via `$PYTHON` (PyYAML). Helper function takes plan path + task ID, returns task_type (default `"implementation"`).

- Current task is `verification` → skip Check 5d (partner review)
- Previous task was `verification` → skip Check 4b (review reports) and Check 4c (dispatch provenance)

### C4: Controller Checkpoint Changes (`controller-checkpoint.py`)

Two additions to the pre-completion phase:

1. **Verification ratio check**: verification tasks / total tasks ≤ 30%. FAIL if exceeded, naming the verification tasks.

2. **Git reality check**: For each verification task N:
   - Read dispatch log for `type=implementer task=N ts=...` and `type=implementer task=<N+1> ts=...`
   - Run `git log --oneline --after=<ts_N> --before=<ts_N+1>` for file-modifying commits
   - If found → FAIL: "Verification task N produced file modifications"
   - Last task: use current time as upper bound
   - Best-effort heuristic backstop (primary defenses are plan-time warning + ratio cap)

### C5: Validate-Plan Script Changes (`validate-plan.py`)

**New WARNING**: Verification task titles containing write-suggesting keywords.

Keywords (case-insensitive, word-boundary-aware): `create`, `add`, `implement`, `fix`, `modify`, `write`, `update`, `refactor`, `migrate`, `delete`, `remove`.

WARNING not FAIL — edge cases exist (e.g., "Verify update script output").

### C6: SDD SKILL.md — Verification Tasks Section

New section documenting:
- When to use `task_type: verification`
- Simplified controller flow: dispatch → report → done (no reviews)
- Modified implementer prompt: "You are a read-only auditor. Do not create, modify, or delete any repository files."
- Defense-in-depth layers

Word budget: 247 words remaining. May need to extract existing content to `references/` first.

### C7: Writing-Plans SKILL.md — Verification Task Guidance

New subsection near `review_tier` guidance with classification table:

| Appropriate for `verification` | Stay as `implementation` |
|---|---|
| Grep for orphaned code/stale references | Code deletion based on grep results |
| Run test suite, report results | Fix failing tests |
| Consistency audit (naming, imports) | Refactor to fix inconsistencies |
| Count/inventory tasks | Anything that modifies files |
| Smoke test / manual verification | Test-writing (creates test files) |

Bright line: **if the task modifies any file, it's `implementation`**.

### C8: SSOT Audit Investigation

Read all 15 SKILL.md files. Compare manual prescriptions against 4 active hooks. Exclude `sdd-skill-enforcement-hook.sh` and `sdd-stop-hook.sh` (exist on disk but not registered in `settings.json` — findings about inactive hooks would be misleading). For each match document: SKILL.md location, hook check, drift, classification (retire/strengthen/keep).

Output: `docs/process-improvement-findings/2026-05-31-ssot-audit.md` + new `BACKLOG.md` rows.

No code changes.

## Non-Goals

- Changing brainstorming's behavior or entry flow
- Modifying the handoff acceptance skill or `/handoff` CLI tool
- Fixing the SSOT audit findings (sprint 3)
- Adding `entry_mode` to the SDD manifest (informational field stays in plan only)
- Changing the plan-validation-gate hook (already entry-mode-agnostic)

## Files Modified

| File | Action | Component |
|------|--------|-----------|
| `skills/scripts/models/plan.py` | Modify | C1 |
| `skills/writing-plans/SKILL.md` | Modify | C2, C7 |
| `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` | Modify | C3 |
| `skills/subagent-driven-development/scripts/controller-checkpoint.py` | Modify | C4 |
| `skills/subagent-driven-development/scripts/validate-plan.py` | Modify | C5 |
| `skills/subagent-driven-development/SKILL.md` | Modify | C6 |
| `docs/process-improvement-findings/2026-05-31-ssot-audit.md` | Create | C8 |
| `docs/process-improvement-findings/BACKLOG.md` | Modify | C8 |
| `tests/unit/` | Modify | C1-C5 |
| `tests/integration/sdd-e2e-test.sh` | Modify | C3, C4 |

## Acceptance Criteria

- [ ] `writing-plans` invoked directly creates `.active-feature`, feature dir, and plan with `entry_mode: direct`
- [ ] Stale `.active-feature` detected and resolved (4-branch conflict detection)
- [ ] Worktree/branch guard offers worktree creation on `main`
- [ ] `check-distillation.sh` runs on user-supplied distilled specs
- [ ] Plan with `task_type: verification` passes `validate-plan.py` (keyword WARNING where appropriate)
- [ ] SDD hook skips review checks (4b, 4c, 5d) for verification tasks
- [ ] SDD hook logs implementer dispatches to dispatch log
- [ ] SDD hook enforces review checks for implementation tasks unchanged
- [ ] Verification tasks dispatched with read-only auditor prompt
- [ ] Pre-completion caps verification tasks at ≤30%
- [ ] Pre-completion detects file modifications by verification tasks via git log
- [ ] SSOT audit findings document produced with backlog rows
- [ ] Existing tests pass (regression 145/3/0, unit 351, e2e 8 steps)
- [ ] New tests cover all changed components
