# SDD Hook Improvements — Design Spec

> **Feature archetype:** Extension
> **Source:** `docs/2026-05-28-sdd-session-assessment-btd-consolidation.md` (items 1-4, plus item 5 added during design)
> **Scope:** `sdd-pre-dispatch-hook.sh`, `controller-checkpoint.py`, `validate-plan.py`, `plan.py`, `writing-plans/SKILL.md`

## Problem Statement

A 10-task SDD session (BTD Consolidation, personal-finance-api) took ~3 hours for 28 minutes of actual code work. The remaining 2.5 hours was process friction caused by enforcement hook bugs, opaque error messages, and a minimum-tier review threshold that penalizes plans with legitimately mechanical tasks.

Five targeted improvements address the root causes without weakening enforcement rigor.

## Items Addressed

| # | Item | Category |
|---|------|----------|
| 1 | `general-purpose` subagent_type bypasses reviewer detection in manifest mode | Bug |
| 2 | Validation errors not surfaced inline — controller must run scripts manually to diagnose | UX |
| 3 | Dispatch log not auto-created on first reviewer dispatch — cascading failures | Bug |
| 4 | Minimum-tier threshold (>50%) penalizes plans with legitimately mechanical tasks | Design |
| 5 | Legacy (non-manifest) dispatch path creates weaker enforcement loophole | Debt |

## Item 1: Fix `general-purpose` passthrough bug

**File:** `sdd-pre-dispatch-hook.sh`

**Root cause:** Line 169 lists `general-purpose` in the known non-implementer passthrough:
```bash
if echo "$SUBAGENT_TYPE" | grep -qiE '^(Explore|general-purpose|Plan|debugger|feature-dev|code-reviewer|code-simplifier)$'; then
    exit 0
fi
```

Post-migration (2026-05-07), all reviewers AND implementers use `subagent_type: "general-purpose"`. Both exit at line 170 before reaching reviewer detection at line 174. Consequences:
- Reviewer dispatches are not logged to the dispatch log
- Dispatch log may never be created
- Subsequent implementer dispatches fail the dispatch provenance check (no reviewer entries found)

**Fix:** Remove `general-purpose` from the passthrough list:
```bash
if echo "$SUBAGENT_TYPE" | grep -qiE '^(Explore|Plan|debugger|feature-dev|code-reviewer|code-simplifier)$'; then
    exit 0
fi
```

All `general-purpose` dispatches flow through reviewer detection (line 174) and get classified correctly by description pattern matching.

**Scope:** Manifest-mode path only. The legacy path (to be removed per Item 5) does not have this passthrough.

## Item 2: Surface validation errors inline

**File:** `sdd-pre-dispatch-hook.sh`

**Root cause:** Lines 457-460 capture `$VALIDATE_OUTPUT` from `validate-report.py` but only report the exit code:
```bash
ERRORS+=("BLOCKED: ... failed validation (exit $VALIDATE_EXIT). Re-dispatch ...")
```

The controller must run `validate-report.py` manually to see which field failed.

**Fix:** Include a truncated excerpt of the validation output in the error message:
```bash
if [ "$VALIDATE_EXIT" -ne 0 ]; then
  VALIDATE_EXCERPT=$(echo "$VALIDATE_OUTPUT" | head -c 300)
  ERRORS+=("BLOCKED: Implementer report for Task $PREV ($IMPL_LATEST) failed validation (exit $VALIDATE_EXIT):\n${VALIDATE_EXCERPT}\n\nRe-dispatch the implementer to fix Pydantic frontmatter or complete all 5 required prose sections before proceeding.")
fi
```

300 characters captures the specific field name and error without flooding the hook output. The INCOMPLETE branch (lines 463-465) already surfaces missing section names — no change needed there.

## Item 3: Auto-create dispatch log on first reviewer dispatch

**File:** `sdd-pre-dispatch-hook.sh`

**Root cause:** Reviewer logging at line 189 uses `>> "$DISPATCH_LOG"` (which creates the file), but it's gated by `if [ -d "$(dirname "$DISPATCH_LOG")" ]` at line 180. If `reports/` doesn't exist yet, the append silently skips.

**Fix:** Before the reviewer logging block, ensure the directory and file exist:
```bash
if [ "$IS_REVIEWER" = true ]; then
  mkdir -p "$(dirname "$DISPATCH_LOG")"
  touch "$DISPATCH_LOG"
  # ... existing reviewer logging ...
```

Both operations are idempotent. The sentinel logic (lines 192-206) already handles "first dispatch" correctly — it just needs the file to exist.

## Item 4: Per-task `review_tier` declaration

### Schema change

**File:** `skills/scripts/models/plan.py`

Add optional `review_tier` field to the task model in the plan's YAML frontmatter:

```yaml
tasks:
  - id: 0
    title: "Contract verification"
  - id: 1
    title: "Create SQL migration (DDL only)"
    review_tier: minimum
  - id: 2
    title: "Refactor balance calculation service"
    # omitted -> defaults to "full"
```

Type: `Literal["minimum", "full"]`, default `"full"`. Binary signal — no other tiers.

### Checkpoint logic change

**File:** `controller-checkpoint.py`, lines 1054-1098

Current logic:
```
if quality_min / quality_total > 0.5 -> FAIL
```

New logic:
1. Read the plan's YAML frontmatter to get the `tasks` array
2. Build a set of task IDs where `review_tier == "minimum"`
3. When counting reviews, classify:
   - **Declared minimum:** task ID in the set -> excluded from numerator AND denominator
   - **Undeclared minimum:** task ID NOT in the set, but review file is `-minimum-tier.md` -> counts as minimum in the ratio
   - **Full review:** normal review file -> counts as full in the ratio
4. Ratio: `undeclared_minimum / (undeclared_minimum + full)` — if >50%, FAIL

The 50% threshold stays but now measures the right thing: "of the tasks where full review was expected, how many did the controller skip?"

### Heuristic validation

**File:** `validate-plan.py`

Warn (not block) when `review_tier: minimum` appears on a task whose title contains high-risk keywords: "refactor", "service", "security", "business logic", "auth", "migration" (with data manipulation context).

### Writing-plans guidance

**File:** `writing-plans/SKILL.md`

Add a decision table in the task-writing step. The plan author consults this when filling out each task's frontmatter entry.

**Full review expected (default):**

| Signal | Examples |
|--------|----------|
| Changes business logic | Service layer refactors, calculation changes, state machines |
| Affects data integrity | Migrations with data manipulation, backfills, constraint changes |
| Crosses architectural boundaries | Multi-file changes spanning router -> service -> model |
| Modifies shared code | Utilities, base classes, shared types used by multiple consumers |
| Changes API contracts | Endpoint signatures, request/response shapes, error codes |
| Security-sensitive | Auth, input validation, encryption, credential handling |
| Has Pattern References or Shared Constants | Must follow existing patterns correctly |

**Minimum-tier appropriate (`review_tier: minimum`):**

| Signal | Examples |
|--------|----------|
| Pure schema DDL | CREATE TABLE, ADD COLUMN, CREATE VIEW (no data manipulation) |
| Configuration | Env vars, settings files, feature flags, migration registration |
| Documentation | CLAUDE.md updates, README, inline doc fixes |
| Test-only | Adding test coverage for already-implemented and reviewed code |
| Verification/audit | Grep for orphaned code, run full test suite, check consistency |
| Cosmetic | Type annotations, linting fixes, import reorg, renames |

**Gray zone guidance:**
- SQL views with business logic -> full (SQL encodes business rules)
- Tests that establish contract compliance (TDD-style) -> full (tests ARE the spec)
- Migration + config registration as single task (pure DDL + one-liner) -> minimum is fine

## Item 5: Remove legacy dispatch detection path

**File:** `sdd-pre-dispatch-hook.sh`, lines 123-153 and 226-273

**Root cause:** The legacy path provides weaker enforcement (no task range validation, no enforcement flags, no process requirements injection) when no manifest exists. This masks upstream failures rather than catching them.

**Fix:** Replace both legacy blocks with a single guard clause:

```bash
if [ "$MANIFEST_MODE" = false ]; then
  if [ -f ".active-feature" ]; then
    FEAT_CHECK=$(cat .active-feature | tr -d '\n' | sed 's|/$||')
    if [ -d "$FEAT_CHECK/reports" ] || [ -f "$FEAT_CHECK/deviations.md" ]; then
      echo "BLOCKED: SDD artifacts found in $FEAT_CHECK/ but no .sdd-session.json manifest. Run Plan Ingestion (materialize-manifest.py) to create the session manifest before dispatching tasks." >&2
      exit 2
    fi
  fi
  exit 0
fi
```

Logic:
- No manifest + no SDD artifacts -> not an SDD session, allow (don't block non-SDD Agent calls)
- No manifest + SDD artifacts present -> upstream failure, BLOCK with clear message
- Manifest exists -> proceed to manifest-mode enforcement

**Deleted code (~100 lines):**
- `feat_path()` helper function
- `DEVIATIONS.md` uppercase fallback
- Bare `reports/` fallback
- Entire legacy dispatch detection block (lines 226-273)
- Duplicated reviewer logging code

**Test updates required:** Unit tests for legacy-mode behavior need to be updated to expect BLOCK or removed if they test pure legacy scenarios.

## Files Changed Summary

| File | Items | Change Type |
|------|-------|-------------|
| `sdd-pre-dispatch-hook.sh` | 1, 2, 3, 5 | Bug fixes + legacy removal |
| `controller-checkpoint.py` | 4 | Logic change (ratio denominator) |
| `skills/scripts/models/plan.py` | 4 | Schema addition (`review_tier` field) |
| `validate-plan.py` | 4 | Heuristic warning |
| `writing-plans/SKILL.md` | 4 | Guidance addition (decision table) |
| `tests/unit/test_sdd_pre_dispatch_hook.py` | 1, 5 | Test updates |
| `tests/unit/test_validate_plan.py` | 4 | New tests for `review_tier` validation |
| `tests/unit/test_controller_checkpoint.py` | 4 | New tests for filtered ratio |

## Acceptance Criteria

- [ ] `general-purpose` reviewer dispatches are logged to dispatch log (not passthrough'd)
- [ ] Validation errors include the specific field/error, not just exit code
- [ ] First reviewer dispatch creates `reports/` and dispatch log if missing
- [ ] Plans with declared `review_tier: minimum` tasks pass the ratio check when only declared-minimum tasks use minimum-tier reviews
- [ ] Plans where the controller uses minimum-tier reviews on non-declared tasks still trigger the >50% blocker
- [ ] Dispatches without a manifest + with SDD artifacts are BLOCKED with a clear message
- [ ] Dispatches without a manifest + without SDD artifacts are ALLOWED (non-SDD sessions)
- [ ] All existing tests pass (with updates for legacy removal)
- [ ] New tests cover each changed behavior
