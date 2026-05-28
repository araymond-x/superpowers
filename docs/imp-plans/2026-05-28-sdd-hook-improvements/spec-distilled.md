# SDD Hook Improvements — Distilled Implementation Spec

> **Source**: `docs/imp-plans/2026-05-28-sdd-hook-improvements/spec.md` (R2 APPROVED)
> **Distilled**: 2026-05-28
> **For**: Plan writer and implementation agents ONLY. For full rationale, see source.

## Contract Facts

- `review_tier` field: `Literal["minimum", "full"]`, default `"full"`, optional on each task in plan YAML frontmatter
- `review_tier` is orthogonal to `enforcement_tier` — never derive one from the other
- Adding `review_tier` is non-breaking — do NOT bump `CURRENT_SCHEMA_VERSION`
- Minimum-tier ratio threshold stays at 50% — only the denominator changes
- `sdd-pre-dispatch-hook.sh` manifest-mode classification becomes: reviewer detection → implementer detection → passthrough (in that order)
- Legacy (non-manifest) dispatch path is removed entirely — manifest mode is required for SDD enforcement
- Dispatch log auto-creation uses `mkdir -p` + `touch` (idempotent)
- Validation error excerpt uses `head -n 5` (line-based, not character-based)

## Open Decisions

None — all decisions resolved during design.

## Decision Summary

| # | Decision | Chosen |
|---|----------|--------|
| 1 | How to fix `general-purpose` passthrough | 3-stage classification pipeline (reviewer → implementer → passthrough) |
| 2 | How to surface validation errors | Include first 5 lines of validation output inline |
| 3 | How to handle dispatch log cold-start | `mkdir -p` + `touch` before reviewer logging |
| 4 | How to fix minimum-tier ratio | Per-task `review_tier` declaration in plan frontmatter; exclude declared-minimum from ratio denominator |
| 5 | How to handle legacy path | Remove entirely; block if SDD artifacts exist without manifest; allow if no artifacts |

## Component Specifications

### Item 1: Restructure manifest-mode dispatch classification

**File:** `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`

Replace lines 155-224 with a 3-stage pipeline:

**Stage 1 — Reviewer detection** (by description pattern, BEFORE any passthrough):
- Pattern: `(review|spec.compliance|code.quality|spec.review|quality.review|trace.audit|partner.review)`
- If match: `mkdir -p` + `touch` dispatch log (Item 3), log reviewer dispatch, write sentinel if first dispatch, exit 0

**Stage 2 — Implementer detection** (by description + prompt pattern):
- Description pattern: `(implement|dispatch).*task\s*[0-9]`
- Prompt pattern: `you are implementing task\s*[0-9]`
- If match: extract task number, proceed to enforcement gates

**Stage 3 — Passthrough:**
- Not a reviewer, not an implementer → exit 0

**Delete:** `subagent_type` passthrough block (lines 168-171), unconditional `IS_IMPLEMENTER=true` (line 211).

### Item 2: Surface validation errors inline

**File:** `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`

Change lines 459-460. When `validate-report.py` exits non-zero, include first 5 lines of output:
```bash
VALIDATE_EXCERPT=$(echo "$VALIDATE_OUTPUT" | head -n 5)
ERRORS+=("BLOCKED: ... failed validation (exit $VALIDATE_EXIT):\n${VALIDATE_EXCERPT}\n\nRe-dispatch ...")
```

No change to the INCOMPLETE branch (lines 463-465) — it already surfaces missing sections.

### Item 3: Auto-create dispatch log

**File:** `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`

At the start of the reviewer handling block (Item 1 Stage 1), before logging:
```bash
mkdir -p "$(dirname "$DISPATCH_LOG")"
touch "$DISPATCH_LOG"
```

### Item 4: Per-task `review_tier` declaration

**4a. Schema — `skills/scripts/models/plan.py`:**
Add to Task model: `review_tier: Literal["minimum", "full"] = "full"`
Must work with `StrictModel` (`extra="forbid"`) — use default value, not Optional.

**4b. Checkpoint — `skills/subagent-driven-development/scripts/controller-checkpoint.py`:**
- Parse plan YAML using existing Pydantic `Plan` model (already imported from `skills/scripts/models/`)
- Build exclusion set: task IDs where `review_tier == "minimum"`
- For modular plans: read ALL module plan files from manifest's `modules` array (resolve via `<git_root>/<feature_dir>/<module_file>`)
- Refactor `_count_review_tiers()` to return per-task results (extract task ID from filename `task-NNN-*`)
- Filter: exclude declared-minimum tasks from numerator AND denominator
- Apply symmetrically to BOTH quality review (line 1058) AND partner review (line 1079) ratio checks
- Zero-denominator guard: if filtered denominator is 0, PASS (same pattern as existing `if total > 0`)
- Fallback: if plan parsing fails, empty exclusion set + WARNING (current behavior preserved)

**4c. Heuristic — `skills/subagent-driven-development/scripts/validate-plan.py`:**
- Warn on `review_tier: minimum` + title keywords: "refactor", "service", "security", "business logic", "auth"
- Warn on `review_tier: minimum` + "migration" ONLY when co-occurring with: "backfill", "UPDATE", "DELETE", "transform", "data"
- Do NOT warn on "migration" alone

**4d. Guidance — `skills/writing-plans/SKILL.md`:**
- Insert decision table adjacent to Task Structure section (~line 323)
- ~200 words addition (file stays well under 5000-word limit)
- Full review signals: business logic, data integrity, architectural boundary crossing, shared code, API contracts, security, Pattern References/Shared Constants
- Minimum-tier signals: pure DDL, configuration, documentation, test-only, verification/audit, cosmetic
- Gray zone: SQL views with logic → full; contract-compliance tests → full; DDL + config registration → minimum

### Item 5: Remove legacy dispatch detection path

**File:** `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`

Replace lines 123-153 and 226-273 with guard clause:
```bash
if [ "$MANIFEST_MODE" = false ]; then
  if [ -f ".active-feature" ]; then
    FEAT_CHECK=$(cat .active-feature | tr -d '\n' | sed 's|/$||')
    if [ -d "$FEAT_CHECK/reports" ] || [ -f "$FEAT_CHECK/deviations.md" ]; then
      echo "BLOCKED: SDD artifacts found but no .sdd-session.json manifest..." >&2
      exit 2
    fi
  fi
  exit 0
fi
```

**Also delete:** dead legacy branches in shared enforcement section (post line 274) — any `else` branches referencing `FEAT` variable or "Legacy mode" that become unreachable.

## Test Files

| Test File | Items | Changes |
|-----------|-------|---------|
| `tests/unit/test_sdd_hard_gates.py` | 1, 5 | Classification restructure, legacy removal |
| `tests/unit/test_sdd_dispatch_log.py` | 1, 3 | Reviewer logging, auto-creation |
| `tests/unit/test_sdd_partner_gate.py` | 5 | Legacy removal |
| `tests/unit/test_pre_completion_gates.py` | 4 | Filtered ratio (quality + partner) |
| `tests/unit/test_validate_plan.py` | 4 | `review_tier` heuristic |

## Acceptance Criteria

- [ ] Reviewer dispatches with `subagent_type: "general-purpose"` are logged to dispatch log
- [ ] Implementer dispatches with `subagent_type: "general-purpose"` are enforced
- [ ] Non-reviewer, non-implementer dispatches during SDD sessions are allowed
- [ ] Validation errors include first 5 lines of validation output
- [ ] First reviewer dispatch creates `reports/` directory and dispatch log if missing
- [ ] Declared `review_tier: minimum` tasks excluded from ratio denominator (quality + partner)
- [ ] Undeclared minimum-tier reviews on non-declared tasks still trigger >50% blocker
- [ ] Modular plans: all module plan files read for exclusion set
- [ ] Plan parsing failure: fallback to current behavior with WARNING
- [ ] `validate-plan.py` warns on suspicious `review_tier` + high-risk keywords
- [ ] No manifest + SDD artifacts → BLOCKED
- [ ] No manifest + no artifacts → ALLOWED
- [ ] Dead legacy branches removed
- [ ] All existing tests pass with updates
- [ ] New tests cover all changed behavior
