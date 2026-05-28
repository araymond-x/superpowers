# SDD Hook Improvements — Design Spec

> **Feature archetype:** Extension
> **Source:** `docs/2026-05-28-sdd-session-assessment-btd-consolidation.md` (items 1-4, plus item 5 added during design)
> **Scope:** `sdd-pre-dispatch-hook.sh`, `controller-checkpoint.py`, `validate-plan.py`, `plan.py`, `writing-plans/SKILL.md`
> **Spec review:** R1 NEEDS_REVISION (5 blockers), R2 pending

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

## Item 1: Restructure manifest-mode dispatch classification

**File:** `sdd-pre-dispatch-hook.sh`

**Root cause:** Line 169 lists `general-purpose` in the known non-implementer passthrough. Post-migration (2026-05-07), all reviewers AND implementers use `subagent_type: "general-purpose"`. Both exit at line 170 before reaching reviewer detection at line 174. Consequences:
- Reviewer dispatches are not logged to the dispatch log
- Dispatch log may never be created
- Subsequent implementer dispatches fail the dispatch provenance check (no reviewer entries found)

**Fix:** Restructure the manifest-mode dispatch classification into a three-stage pipeline. The current approach (passthrough → reviewer check → "everything else is implementer") is replaced with explicit classification at each stage:

```
Stage 1: Reviewer detection (by description pattern)
  → If match: log to dispatch log, allow

Stage 2: Implementer detection (by description + prompt pattern)
  → If match: enforce all gates

Stage 3: Passthrough (known non-implementer types + unclassified dispatches)
  → Allow without logging
```

**Concrete changes to lines 155-224:**

```bash
# ─── Manifest-mode dispatch classification ──────────────────────────────
SUBAGENT_TYPE=$(echo "$INPUT" | jq -r '.tool_input.subagent_type // ""' 2>/dev/null)

# Stage 1: Reviewer detection (BEFORE passthrough — reviewers must be logged)
IS_REVIEWER=false
if echo "$DESCRIPTION" | grep -qiE '(review|spec.compliance|code.quality|spec.review|quality.review|trace.audit|partner.review)'; then
  IS_REVIEWER=true
fi

if [ "$IS_REVIEWER" = true ]; then
  # ... existing reviewer logging + sentinel logic ...
  exit 0
fi

# Stage 2: Implementer detection (description or prompt mentions task dispatch)
IS_IMPLEMENTER=false
TASK_NUMBER=""
if echo "$DESCRIPTION" | grep -qiE '(implement|dispatch).*task\s*[0-9]'; then
  TASK_NUMBER=$(echo "$DESCRIPTION" | grep -oiE 'task\s*[0-9]+' | grep -oE '[0-9]+' | head -1)
  IS_IMPLEMENTER=true
elif echo "$PROMPT" | grep -qiE 'you are implementing task\s*[0-9]'; then
  TASK_NUMBER=$(echo "$PROMPT" | grep -oiE 'task\s*[0-9]+' | grep -oE '[0-9]+' | head -1)
  IS_IMPLEMENTER=true
fi

if [ "$IS_IMPLEMENTER" = false ]; then
  # Stage 3: Not a reviewer, not an implementer — allow
  # (covers Explore, Plan, debugger, and ad-hoc dispatches like "investigate schema")
  exit 0
fi

# ... proceed with enforcement gates for the implementer ...
```

**Why this structure:**
- Reviewers with `general-purpose` are caught at Stage 1 (fixes the original bug)
- Implementers with `general-purpose` are caught at Stage 2 (explicit pattern match)
- Exploration/research dispatches during SDD sessions fall through to Stage 3 and are allowed (no false-positive blocks)
- The `subagent_type` passthrough list for `Explore`, `Plan`, etc. is no longer needed — Stage 2's pattern match is the gate, not agent type

**What gets deleted:** The entire `subagent_type` passthrough block (lines 168-171) and the unconditional `IS_IMPLEMENTER=true` at line 211.

## Item 2: Surface validation errors inline

**File:** `sdd-pre-dispatch-hook.sh`

**Root cause:** Lines 457-460 capture `$VALIDATE_OUTPUT` from `validate-report.py` but only report the exit code:
```bash
ERRORS+=("BLOCKED: ... failed validation (exit $VALIDATE_EXIT). Re-dispatch ...")
```

The controller must run `validate-report.py` manually to see which field failed.

**Fix:** Include a truncated excerpt of the validation output in the error message, using line-based truncation for clean output:
```bash
if [ "$VALIDATE_EXIT" -ne 0 ]; then
  VALIDATE_EXCERPT=$(echo "$VALIDATE_OUTPUT" | head -n 5)
  ERRORS+=("BLOCKED: Implementer report for Task $PREV ($IMPL_LATEST) failed validation (exit $VALIDATE_EXIT):\n${VALIDATE_EXCERPT}\n\nRe-dispatch the implementer to fix Pydantic frontmatter or complete all 5 required prose sections before proceeding.")
fi
```

`head -n 5` captures the first 5 lines of output, which for Pydantic validation errors includes the field name(s) and error description(s). Line-based truncation avoids cutting mid-field-name (unlike character-based `head -c`).

The INCOMPLETE branch (lines 463-465) already surfaces missing section names — no change needed there.

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

**Note:** With legacy path removal (Item 5), the `DISPATCH_LOG` path is always resolved from the manifest, so the directory path is reliable.

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

**Schema versioning:** Adding an optional field with a default value is non-breaking. `CURRENT_SCHEMA_VERSION` in `_base.py` does NOT need to be bumped.

**Relationship to `enforcement_tier`:** `enforcement_tier` (plan-level, `micro|standard`) controls hook-level enforcement relaxation. `review_tier` (task-level, `minimum|full`) declares expected review depth for the pre-completion ratio check. These are orthogonal axes — one should never be derived from the other. A `standard` enforcement plan can have tasks with `review_tier: minimum`; a `micro` enforcement plan skips the ratio check entirely.

### Checkpoint logic change

**File:** `controller-checkpoint.py`

**Applies to both quality review AND partner review ratio checks** (lines 1054-1098). The same declared-minimum exclusion logic applies symmetrically to both.

Current logic (lines 1058, 1079):
```
if quality_min / quality_total > 0.5 -> FAIL
if partner_min / partner_total > 0.5 -> FAIL
```

New logic:
1. Parse the plan's YAML frontmatter using the existing Pydantic `Plan` model (imported from `skills/scripts/models/plan.py`). The checkpoint script already imports from `skills/scripts/models/` (line 45-48) and receives `--plan-file` as an argument — no new dependency needed.
2. Build a set of task IDs where `review_tier == "minimum"` from the parsed `tasks` array.
3. **For modular plans:** The manifest's `modules` array lists per-module plan files. During pre-completion, read ALL module plan files (not just the active one) to build the complete exclusion set. Resolve module file paths via `<git_root>/<feature_dir>/<module_file>` (same convention as `transition-module.py`).
4. Refactor `_count_review_tiers()` to return per-file results (task ID extracted from filename pattern `task-NNN-*`) instead of aggregate counts, so each review can be checked against the declared-minimum set.
5. When counting reviews, classify each:
   - **Declared minimum:** task ID is in the exclusion set -> excluded from numerator AND denominator
   - **Undeclared minimum:** task ID NOT in the set, but review file is `-minimum-tier.md` -> counts as minimum in the ratio
   - **Full review:** normal review file -> counts as full in the ratio
6. Ratio: `undeclared_minimum / (undeclared_minimum + full)` — if >50%, FAIL

**Fallback when plan parsing fails:** If the plan file has no YAML frontmatter, no `tasks` array, or parsing fails, fall back to the current behavior (empty exclusion set = all reviews count). Log a WARNING but do not block.

The 50% threshold stays but now measures the right thing: "of the tasks where full review was expected, how many did the controller skip?"

### Heuristic validation

**File:** `validate-plan.py`

Warn (not block) when `review_tier: minimum` appears on a task whose title matches high-risk patterns. The "migration" keyword is only flagged when it co-occurs with data manipulation terms, to avoid false warnings on pure DDL migration tasks:

- **Always warn:** title contains "refactor", "service", "security", "business logic", "auth"
- **Conditional warn:** title contains "migration" AND also contains "backfill", "UPDATE", "DELETE", "transform", or "data"
- **Never warn:** "migration" alone (pure DDL migrations are legitimately minimum-tier)

### Writing-plans guidance

**File:** `writing-plans/SKILL.md`

Add a decision table in the task-writing step, adjacent to the Task Structure section (~line 323). This adds ~200 words, bringing the file to ~4100 words (well under the 5000-word limit).

The plan author consults this when filling out each task's frontmatter entry.

**Full review expected (default — omit `review_tier` or set to `full`):**

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

**Dead legacy branches in shared enforcement section:** Lines in the shared enforcement checks (post line 274) that have `else` branches referencing `FEAT` or checking "Legacy mode" become unreachable after this change. These dead branches must be removed in the same change per the project's architectural principle: "Dead code must be removed, not left around."

**Test updates required:** Unit tests for legacy-mode behavior need to be updated to expect BLOCK or removed if they test pure legacy scenarios.

## Files Changed Summary

| File | Items | Change Type |
|------|-------|-------------|
| `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` | 1, 2, 3, 5 | Restructure classification + legacy removal |
| `skills/subagent-driven-development/scripts/controller-checkpoint.py` | 4 | Logic change (ratio denominator, both quality + partner) |
| `skills/scripts/models/plan.py` | 4 | Schema addition (`review_tier` field) |
| `skills/subagent-driven-development/scripts/validate-plan.py` | 4 | Heuristic warning for suspicious `review_tier` |
| `skills/writing-plans/SKILL.md` | 4 | Guidance addition (decision table, ~200 words) |
| `tests/unit/test_sdd_hard_gates.py` | 1, 5 | Update for restructured classification + legacy removal |
| `tests/unit/test_sdd_dispatch_log.py` | 1, 3 | Update for reviewer logging changes |
| `tests/unit/test_sdd_partner_gate.py` | 5 | Update for legacy removal |
| `tests/unit/test_pre_completion_gates.py` | 4 | New tests for filtered ratio (quality + partner) |
| `tests/unit/test_validate_plan.py` | 4 | New tests for `review_tier` heuristic |

## Acceptance Criteria

- [ ] Reviewer dispatches with `subagent_type: "general-purpose"` are logged to dispatch log (not passthrough'd)
- [ ] Implementer dispatches with `subagent_type: "general-purpose"` are enforced (not passthrough'd)
- [ ] Non-reviewer, non-implementer dispatches during SDD sessions (e.g., "investigate schema") are allowed without enforcement
- [ ] Validation errors include the first 5 lines of validation output, not just exit code
- [ ] First reviewer dispatch creates `reports/` directory and dispatch log if missing
- [ ] Plans with declared `review_tier: minimum` tasks pass the ratio check when only declared-minimum tasks use minimum-tier reviews
- [ ] Plans where the controller uses minimum-tier reviews on non-declared tasks still trigger the >50% blocker
- [ ] Partner review ratio check uses the same declared-minimum exclusion as quality reviews
- [ ] Modular plans: declared-minimum tasks from all module plan files are included in the exclusion set
- [ ] Fallback: if plan parsing fails, ratio check uses current behavior (empty exclusion set) with a WARNING
- [ ] `validate-plan.py` warns on `review_tier: minimum` + high-risk title keywords (but not "migration" alone)
- [ ] Dispatches without a manifest + with SDD artifacts are BLOCKED with a clear message
- [ ] Dispatches without a manifest + without SDD artifacts are ALLOWED (non-SDD sessions)
- [ ] Dead legacy branches in shared enforcement section are removed
- [ ] All existing tests pass (with updates for legacy removal and classification restructure)
- [ ] New tests cover: classification pipeline, dispatch log auto-creation, filtered ratio, review_tier heuristic
