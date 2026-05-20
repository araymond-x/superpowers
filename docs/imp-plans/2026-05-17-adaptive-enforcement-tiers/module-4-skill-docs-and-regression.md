---
schema_version: 1
feature_archetype: refactor
# enforcement_tier: standard — added by this plan's own Task 3
source_contracts: null
pattern_references:
  - name: "validators-cli"
    source_files: ["skills/scripts/models/validators.py"]
    reason: "CLI subcommand pattern for adding session validation"
tasks:
  - id: 16
    title: "Validators CLI session subcommand"
    pattern_references: ["validators-cli"]
  - id: 17
    title: "validate-plan.py tier and module checks"
  - id: 18
    title: "SDD SKILL.md updates"
  - id: 19
    title: "Writing-plans SKILL.md updates"
  - id: 20
    title: "Regression test updates"
    depends_on: [16, 17, 18, 19]
---

# Module 4: Skill Docs, Plan Validation, and Regression

**Goal:** Add `session` subcommand to validators CLI, add tier/module validation to `validate-plan.py`, update SDD and writing-plans SKILL.md files, and update regression test counts.

**Source Contracts:** None

**Reference spec:** `spec-distilled.md` §Plan Validation, §SDD SKILL.md Changes, §Writing-Plans SKILL.md Changes (contract verification in Module 1 Task 0)

**Contract Constraints:**
- `validators.py session <path>` validates `.sdd-session.json`
- `validate-plan.py` adds: tier in `{micro, standard}`, micro with >3 tasks → warn, modules with micro → warn
- SDD SKILL.md: add manifest ingestion, module transitions, controller instructions
- Writing-plans SKILL.md: add `enforcement_tier` to template, tier selection guidance

**Pattern References:**
- `skills/scripts/models/validators.py` — CLI `argparse` + `choices` pattern for adding `session` subcommand

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `skills/scripts/models/validators.py` | Modify | Add `session` subcommand |
| `skills/subagent-driven-development/scripts/validate-plan.py` | Modify | Add tier + module validation checks |
| `skills/subagent-driven-development/SKILL.md` | Modify | Add manifest ingestion, module transitions |
| `skills/writing-plans/SKILL.md` | Modify | Add enforcement_tier to template |
| `tests/unit/test_validate_plan.py` | Extend | Add tier + module validation tests |
| `tests/ARaymond-skill-regression/validate-all-skills.py` | Modify | Update check counts |

## Write-Scope Partitioning

| Task | Owned Files (write) | Read-Only Files | Depends On |
|------|---------------------|-----------------|------------|
| Task 16 | `skills/scripts/models/validators.py` | `skills/scripts/models/sdd_session.py` | Module 1 |
| Task 17 | `skills/subagent-driven-development/scripts/validate-plan.py`, `tests/unit/test_validate_plan.py` | `skills/scripts/models/plan.py` | Module 1 |
| Task 18 | `skills/subagent-driven-development/SKILL.md` | — | Module 1, 2 |
| Task 19 | `skills/writing-plans/SKILL.md` | — | Module 1 |
| Task 20 | `tests/ARaymond-skill-regression/validate-all-skills.py` | all modified skill files | Tasks 16-19 |

## Acceptance Criteria

- [ ] `python3 validators.py session <manifest.json>` validates manifest files
- [ ] `validate-plan.py` warns on micro tier with >3 tasks
- [ ] `validate-plan.py` warns on modules with micro tier
- [ ] SDD SKILL.md documents manifest ingestion and module transitions
- [ ] Writing-plans SKILL.md includes `enforcement_tier` in plan template
- [ ] Regression suite passes with updated check counts

---

### Task 16: Validators CLI Session Subcommand

**Files:**
- Modify: `skills/scripts/models/validators.py`

**Pattern References:**
- `skills/scripts/models/validators.py` — existing `plan`, `handoff`, `report` subcommand pattern

- [x] **Step 1: Add session validation function**

After the `validate_report` function, add:

```python
def validate_session(path: str, schema_version: int | None = None) -> int:
    """Validate an SDD session manifest file. Returns exit code."""
    session_path = Path(path)
    if not session_path.is_file():
        print(f"File not found: {path}", file=sys.stderr)
        return 2

    if _check_bypass():
        return 0

    try:
        data = json.loads(session_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in {path}: {e}", file=sys.stderr)
        return 1

    try:
        from sdd_session import SddSession
        SddSession.model_validate(data)
    except ValidationError as e:
        print(format_validation_error(e, path), file=sys.stderr)
        return 1
    except Exception as e:
        print(
            f"VALIDATOR CRASHED: {type(e).__name__}: {e}",
            file=sys.stderr,
        )
        return 2

    return 0
```

- [x] **Step 2: Add import and subcommand**

Add `import json` at the top (if not already present).

Update the `choices` in `main()`:

```python
parser.add_argument("command", choices=["plan", "handoff", "report", "session"])
```

Add the session branch:

```python
elif args.command == "session":
    sys.exit(validate_session(args.path, args.schema_version))
```

- [x] **Step 3: Run existing validator tests**

```bash
.venv/bin/python3 -m pytest tests/unit/test_validators/ -v
```

Expected: All existing tests PASS

- [x] **Step 4: Commit**

```bash
git add skills/scripts/models/validators.py
git commit -m "feat: add session subcommand to Pydantic validators CLI"
```

---

### Task 17: validate-plan.py Tier and Module Checks

**Files:**
- Modify: `skills/subagent-driven-development/scripts/validate-plan.py`
- Extend: `tests/unit/test_validate_plan.py`

- [x] **Step 1: Write failing tests**

Add to `tests/unit/test_validate_plan.py`:

```python
PLAN_WITH_MICRO_TIER = """\
---
schema_version: 1
feature_archetype: greenfield
enforcement_tier: micro
tasks:
  - id: 0
    title: "Fix bug"
  - id: 1
    title: "Test fix"
---
# Plan

**Source Contracts**: None
**Feature Archetype**: Greenfield

## Code Footprint
- app/fix.py (modified)

**Task 0** — Fix
- [x] Fix the bug

**Task 1** — Test
- [x] Test the fix
"""

PLAN_WITH_MICRO_TOO_MANY_TASKS = """\
---
schema_version: 1
feature_archetype: greenfield
enforcement_tier: micro
tasks:
  - id: 0
    title: "T0"
  - id: 1
    title: "T1"
  - id: 2
    title: "T2"
  - id: 3
    title: "T3"
  - id: 4
    title: "T4"
---
# Plan

**Source Contracts**: None
**Feature Archetype**: Greenfield

## Code Footprint
- app/thing.py

**Task 0**
- [x] Do thing 0
**Task 1**
- [x] Do thing 1
**Task 2**
- [x] Do thing 2
**Task 3**
- [x] Do thing 3
**Task 4**
- [x] Do thing 4
"""


class TestEnforcementTierValidation:
    def test_valid_micro_tier_passes(self):
        result = run_validate(PLAN_WITH_MICRO_TIER)
        assert result["exit_code"] in (0, 2)  # PASS or WARNING

    def test_micro_with_many_tasks_warns(self):
        result = run_validate(PLAN_WITH_MICRO_TOO_MANY_TASKS)
        # Should produce a WARNING about micro tier with >3 tasks
        assert result["exit_code"] == 2  # WARNING
        sections = result["output"].get("sections", {})
        tier_check = sections.get("enforcement_tier_appropriateness", {})
        assert tier_check.get("status") == "WARNING"
```

- [x] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/python3 -m pytest tests/unit/test_validate_plan.py::TestEnforcementTierValidation -v
```

Expected: FAIL (no `enforcement_tier_appropriateness` check exists yet)

- [x] **Step 3: Discover integration points in validate-plan.py**

The variables referenced below are defined inside `validate_plan_content()` (the main validation function). Run this discovery step first:

```bash
grep -n "blockers\|warnings_list\|checks\[" skills/subagent-driven-development/scripts/validate-plan.py | head -20
grep -n "frontmatter\|yaml_data\|pydantic" skills/subagent-driven-development/scripts/validate-plan.py | head -10
grep -n "task_count\|TASK_HEADER_RE" skills/subagent-driven-development/scripts/validate-plan.py | head -10
```

The output dict uses `sections` (not `checks`) and `warnings` (not `warnings_list`). The `blockers` list is a list of strings. `task_count` is computed from `TASK_HEADER_RE.findall()`.

**Important**: `validate_plan_content()` does NOT currently parse YAML frontmatter into a dict — it delegates that to the Pydantic subprocess. The new tier check needs in-process access to the frontmatter. You must add parsing.

- [x] **Step 4: Add YAML frontmatter parsing to validate_plan_content()**

At the top of `validate_plan_content()`, after the `has_frontmatter` boolean check, add in-process YAML parsing:

```python
# Parse YAML frontmatter into dict for in-process checks
frontmatter = None
if has_frontmatter:
    end_idx = content.find("---", 3)
    if end_idx != -1:
        try:
            import yaml
            frontmatter = yaml.safe_load(content[3:end_idx])
        except Exception:
            frontmatter = None
```

This gives you a `frontmatter` dict (or None) for the tier check below.

- [x] **Step 5: Add tier validation using the parsed frontmatter**

After the existing checks and BEFORE the final status computation (`if blockers: status = "FAIL"`), add:

```python
# ─── Enforcement tier appropriateness ────────────────────────────────
if frontmatter and isinstance(frontmatter, dict):
    tier = frontmatter.get("enforcement_tier")
    if tier is not None:
        if tier not in ("micro", "standard"):
            blockers.append("enforcement_tier_invalid")
            sections["enforcement_tier_invalid"] = {
                "status": "FAIL",
                "detail": f"enforcement_tier '{tier}' is not valid. Must be 'micro' or 'standard'.",
            }
        elif tier == "micro" and task_count > 3:
            warnings.append("enforcement_tier_appropriateness")
            sections["enforcement_tier_appropriateness"] = {
                "status": "WARNING",
                "detail": f"enforcement_tier is 'micro' but plan has {task_count} tasks. "
                          "Micro tier is designed for 1-2 tasks. Consider 'standard' for better enforcement.",
            }

        modules = frontmatter.get("modules")
        if modules and tier == "micro":
            warnings.append("micro_with_modules")
            sections["micro_with_modules"] = {
                "status": "WARNING",
                "detail": "enforcement_tier is 'micro' but plan has modules. "
                          "Multi-module plans typically need standard enforcement.",
            }
```

- [x] **Step 4: Run tests**

```bash
.venv/bin/python3 -m pytest tests/unit/test_validate_plan.py -v
```

Expected: All tests PASS

- [x] **Step 5: Commit**

```bash
git add skills/subagent-driven-development/scripts/validate-plan.py tests/unit/test_validate_plan.py
git commit -m "feat: add enforcement_tier validation to validate-plan.py"
```

---

### Task 18: SDD SKILL.md Updates

**Files:**
- Modify: `skills/subagent-driven-development/SKILL.md`

- [x] **Step 1: Add manifest ingestion to Plan Ingestion section**

In the "Plan Ingestion" flow diagram and steps, after "Read full plan document", add:

```markdown
### Manifest Materialization

After reading the plan and before creating TodoWrite:

1. Read `enforcement_tier` from plan frontmatter (default: `standard` if absent)
2. Run `materialize-manifest.py --plan-file <plan.md> --feature-dir <feature-dir>` to write `.sdd-session.json`
3. Display session contract to controller:

> **Session manifest**: Tier `{tier}`. Process requirements: subagent_dispatch={X}, spec_review={Y}, quality_review={Z}, partner_review={W}. These are immutable.

If `.sdd-session.json` already exists (resume scenario), validate it matches the plan frontmatter.
```

- [x] **Step 2: Add module transition section**

After the task loop section, add:

```markdown
### Module Transition (multi-module plans only)

When all tasks in the current module are complete:

```bash
python3 ~/.claude/skills/superpowers/subagent-driven-development/scripts/transition-module.py \
  --manifest <feature-dir>/.sdd-session.json \
  --completed-module <module-name> \
  --next-module <module-name>
```

Do not manually archive reports or update the manifest — the script handles all five steps (validate, archive, update manifest, archive dispatch log, log to deviations).
```

- [x] **Step 3: Verify SKILL.md word count**

```bash
wc -w skills/subagent-driven-development/SKILL.md
```

If over 5000 words, extract content to `references/` to stay under the limit.

- [x] **Step 4: Commit**

```bash
git add skills/subagent-driven-development/SKILL.md
git commit -m "docs: add manifest ingestion and module transition to SDD SKILL.md"
```

---

### Task 19: Writing-Plans SKILL.md Updates

**Files:**
- Modify: `skills/writing-plans/SKILL.md`

- [x] **Step 1: Add `enforcement_tier` to plan template**

In the "YAML Frontmatter (Required)" section, add after `feature_archetype`:

```yaml
enforcement_tier: standard  # micro | standard (default: standard)
```

- [x] **Step 2: Add tier selection guidance**

In the plan writing process, after task decomposition, add:

```markdown
### Enforcement Tier Selection

After decomposing tasks, select the enforcement tier:

- **micro** (1-2 tasks): Bug fixes, config changes, simple additions. Self-review OK, no partner review, no real-time hook enforcement.
- **standard** (3+ tasks): Typical features and multi-module plans. Full two-stage review, partner review, checkpoint files. Multi-module support activates when `modules` is declared.

Task count is a guideline. The plan reviewer validates tier appropriateness.
```

- [x] **Step 3: Add `file` field to module template**

In the module template section, add `file` to the module YAML:

```yaml
modules:
  - id: 1
    title: "Core"
    task_ids: [0, 1, 2]
    file: module-1-core.md  # path to module plan file (relative to feature dir)
```

- [x] **Step 4: Commit**

```bash
git add skills/writing-plans/SKILL.md
git commit -m "docs: add enforcement_tier and module file to writing-plans template"
```

---

### Task 20: Regression Test Updates

**Files:**
- Modify: `tests/ARaymond-skill-regression/validate-all-skills.py`

- [ ] **Step 1: Run existing regression suite**

```bash
python3 tests/ARaymond-skill-regression/validate-all-skills.py
```

Note which checks fail due to the new content.

- [ ] **Step 2: Update check counts and patterns**

Update any hardcoded check counts that changed due to:
- New `enforcement_tier` in plan template (writing-plans SKILL.md)
- New manifest ingestion section (SDD SKILL.md)
- New module transition section (SDD SKILL.md)
- New `sdd_session.py` model file
- New `materialize-manifest.py` script
- New `transition-module.py` script

- [ ] **Step 3: Run regression suite**

```bash
python3 tests/ARaymond-skill-regression/validate-all-skills.py
```

Expected: All checks PASS

- [ ] **Step 4: Run installation verification**

```bash
bash tests/ARaymond-installation/verify-symlink-install.sh
```

Expected: All checks PASS (script counts may need updating if new scripts were added)

- [ ] **Step 5: Commit**

```bash
git add tests/ARaymond-skill-regression/validate-all-skills.py
git commit -m "test: update regression check counts for adaptive enforcement tiers"
```
