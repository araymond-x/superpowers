---
schema_version: 1
feature_archetype: migration
source_contracts: "docs/specs/2026-04-24-pydantic-phase-1-design-distilled.md"
pattern_references:
  - name: "skill-structure"
    source_files: ["skills/writing-plans/SKILL.md"]
    reason: "Existing skill structure for where to add YAML frontmatter section"
  - name: "handoff-spec-format"
    source_files: ["skills/handoff-acceptance/references/handoff-package-spec.md"]
    reason: "Existing handoff spec format"
  - name: "check-pattern"
    source_files: ["tests/ARaymond-installation/verify-symlink-install.sh"]
    reason: "Check pattern (pass/fail/warn functions)"
tasks:
  - id: 10
    title: "Prompt Template Updates"
  - id: 11
    title: "Documentation + Installation Verification"
    depends_on: [10]
  - id: 12
    title: "Pre-Ship Smoke Test"
  - id: 13
    title: "Obsolescence Verification"
    depends_on: [12]
---
# Pydantic Phase 1 — Module 3: Cutover + Verification

> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first.

**Goal:** Update prompt templates atomically with validators, add documentation, run pre-ship smoke test against real plans, and verify no stale legacy references remain.

**Source Contracts:** None

**Contract Constraints:** Prompt templates and validators must ship atomically (same commit for templates that reference the new format). See `docs/specs/2026-04-24-pydantic-phase-1-design-distilled.md` Section 5.3 for the update table.

**Pattern References:**
- `skills/writing-plans/SKILL.md` — existing skill structure for where to add YAML frontmatter section
- `skills/handoff-acceptance/references/handoff-package-spec.md` — existing handoff spec format
- `tests/ARaymond-installation/verify-symlink-install.sh` — check pattern (`pass`/`fail`/`warn` functions)

**Feature Archetype:** Migration

## File Map

```
skills/writing-plans/SKILL.md                     # Task 10 (modify)
skills/handoff-acceptance/references/
  handoff-package-spec.md                          # Task 10 (modify)
skills/subagent-driven-development/SKILL.md        # Task 10 (modify)
CLAUDE.md                                          # Task 11 (modify)
tests/ARaymond-installation/verify-symlink-install.sh  # Task 11 (modify)
tests/unit/test_smoke_real_plans.py                # Task 12 (create)
tests/fixtures/_smoke-test-plans/                  # Task 12 (create, deleted post-merge)
```

## Write-Scope Partitioning

| Task / Worker | Owned Files (write) | Read-Only Files | Depends On |
|---------------|---------------------|-----------------|------------|
| Task 10 | writing-plans/SKILL.md, handoff-package-spec.md, SDD SKILL.md | — | Module 2 |
| Task 11 | CLAUDE.md, verify-symlink-install.sh | — | Task 10 |
| Task 12 | test_smoke_real_plans.py, _smoke-test-plans/\* | validators.py | Module 2 |
| Task 13 | (grep audit only — no file creation) | All modified files | Task 12 |

Tasks 10+11 and Task 12 are parallel candidates (disjoint write sets).

---

### Task 10: Prompt Template Updates

**Files:**
- Modify: `skills/writing-plans/SKILL.md`
- Modify: `skills/handoff-acceptance/references/handoff-package-spec.md`
- Modify: `skills/subagent-driven-development/SKILL.md`

- [x] **Step 1: Add YAML frontmatter section to writing-plans/SKILL.md**

Add a new section after the "Plan Document Header" section in `skills/writing-plans/SKILL.md`. Insert before the "Write-Scope Partitioning" section:

```markdown
## YAML Frontmatter (Required)

Every plan file must begin with a YAML frontmatter block between `---` delimiters. The frontmatter contains typed fields that the Pydantic validator checks. The markdown body follows below.

```yaml
---
schema_version: 1
feature_archetype: greenfield  # greenfield | replacement | extension | refactor | migration
source_contracts: "path/to/spec.md"  # or null
shared_constants:
  - path: "app.config.X"
    value: "42"
    reason: "Used in task 3"
pattern_references:
  - name: "existing-pattern"
    source_files: ["src/example.py"]
    reason: "Follow this layout"
modules:  # only if modular plan
  - id: 1
    title: "Core"
    task_ids: [0, 1, 2]
tasks:
  - id: 0
    title: "Setup"
  - id: 1
    title: "Implement"
    depends_on: [0]
    module_id: 1
    shared_constants_used: ["app.config.X"]
    pattern_references: ["existing-pattern"]
---
```

The validator checks: sequential task IDs, valid dependency references (no forward refs), declared shared constants and pattern references, and module-task consistency. Run the validator to see explanatory error messages for any issues.
```

- [x] **Step 2: Update handoff-package-spec.md with YAML frontmatter template**

In `skills/handoff-acceptance/references/handoff-package-spec.md`, add a YAML frontmatter section near the top, after the existing structure template:

```markdown
## YAML Frontmatter (Required)

Handoff package README.md files must begin with YAML frontmatter:

```yaml
---
schema_version: 1
package_name: "your-package-name"
feeds_into: "brainstorming"  # which skill consumes this
one_sentence_purpose: "Describe the package in one sentence."
contract_constraints:
  - name: "field_name"
    kind: "string"  # string | integer | float | boolean | date | enum
    format_hint: "YYYY-MM-DD"  # optional
    nullable: false  # optional, default false
format_rules:
  - applies_to: ["field_name"]
    rule: "Must be positive"
samples:
  - path: "samples/example.csv"
    description: "Example data file"
---
```

The validator checks that format_rules reference declared fields and that sample files exist on disk.
```

- [x] **Step 3: Add one-line note to SDD SKILL.md** (extracted Context Health Protocol to references/, 4809 words)

**WARNING:** SDD SKILL.md is at 5029 words (over the 5000 soft limit). Before adding, check word count with `wc -w skills/subagent-driven-development/SKILL.md`. If over limit, extract content to `references/` to offset before adding.

Add a single sentence to the plan ingestion section of `skills/subagent-driven-development/SKILL.md`:

```
Plans consumed by SDD now use YAML frontmatter — the typed fields are validated by Pydantic before execution begins.
```

- [x] **Step 4: Run skill regression tests** (122 PASS, 0 FAIL, 1 WARNING)

- [x] **Step 5: Commit** (627c3e4)

---

### Task 11: Documentation + Installation Verification

**Files:**
- Modify: `CLAUDE.md`
- Modify: `tests/ARaymond-installation/verify-symlink-install.sh`

- [x] **Step 1: Add Pydantic section to CLAUDE.md**

Add a new section after "Hooks-Based Enforcement" in `CLAUDE.md`:

```markdown
## Pydantic Validation (Phase 1)
- Models at `skills/scripts/models/` — `_base.py`, `plan.py`, `handoff.py`, `errors.py`, `validators.py`
- Two base classes: `StrictModel` (nested types, `extra="forbid"`) and `SchemaVersionedModel` (top-level artifacts, `schema_version` pinned)
- CLI: `python3 validators.py plan <path>` / `python3 validators.py handoff <dir>`
- Exit codes: 0 pass / 1 validation fail / 2 infrastructure
- Bypass: `export SUPERPOWERS_VALIDATOR_BYPASS=1` (emergency unblock, stderr warning)
- Schema version: `CURRENT_SCHEMA_VERSION = 1` in `_base.py`. Bump per `docs/plans/2026-04-24-pydantic-meta-design.md` Section 4.2.
- Plans without YAML frontmatter are hard FAILs — add frontmatter to validate.
```

- [x] **Step 2: Add 2 Pydantic checks to verify-symlink-install.sh**

Add after the existing checks section in `tests/ARaymond-installation/verify-symlink-install.sh`:

```bash
section "Pydantic Validation"

if .venv/bin/python3 -c 'import pydantic; v=pydantic.VERSION.split("."); assert v[0]=="2" and int(v[1])>=7' 2>/dev/null; then
  pass "Pydantic v2.7+ importable"
else
  fail "Pydantic v2.7+ not importable — run: .venv/bin/pip install -r requirements.txt"
fi

if .venv/bin/python3 -c 'import sys; sys.path.insert(0,"skills/scripts/models"); from plan import Plan; from handoff import HandoffPackage; from errors import format_validation_error; from _base import CURRENT_SCHEMA_VERSION' 2>/dev/null; then
  pass "Pydantic model modules import cleanly"
else
  fail "Pydantic model modules failed to import — check skills/scripts/models/"
fi
```

- [x] **Step 3: Run installation verification** (105 PASS, 0 FAIL)

- [x] **Step 4: Commit** (55b397e)

---

### Task 12: Pre-Ship Smoke Test

**Files:**
- Create: `tests/unit/test_smoke_real_plans.py`
- Create: `tests/fixtures/_smoke-test-plans/` (populated with real plan copies)

- [ ] **Step 1: Identify recent plans (post 2026-04-08)**

```bash
# macOS: use -newermt for date comparison (GNU find) or reference file
find ~/projects -name "*.md" -path "*/imp-plans/*" -type f 2>/dev/null | xargs ls -lt 2>/dev/null | head -20
# Or filter by name pattern (plans are dated):
ls ~/projects/*/docs/imp-plans/2026-04-{08,09,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24}*.md 2>/dev/null
```

Also check this repo:
```bash
ls docs/imp-plans/2026-04-08-*.md docs/imp-plans/2026-04-24-*.md 2>/dev/null
```

- [ ] **Step 2: Copy plans into smoke test directory**

```bash
mkdir -p tests/fixtures/_smoke-test-plans
```

For each plan found, copy it (do NOT modify originals):
```bash
cp <source-plan.md> tests/fixtures/_smoke-test-plans/<name>.md
```

- [ ] **Step 3: Add YAML frontmatter to each copy**

For each copied plan, add YAML frontmatter reflecting what the author would have written in the new format. Read each plan's header to extract: feature_archetype, source_contracts, tasks (IDs and titles), modules (if present), shared_constants, pattern_references.

Example frontmatter to add at the top of each copy:
```yaml
---
schema_version: 1
feature_archetype: extension
tasks:
  - id: 0
    title: "Setup"
  - id: 1
    title: "Core implementation"
    depends_on: [0]
---
```

- [ ] **Step 4: Write smoke test file**

```python
# tests/unit/test_smoke_real_plans.py
"""Pre-ship smoke test: validate real plans against Pydantic schema.

Auto-discovers fixtures in tests/fixtures/_smoke-test-plans/.
Skipped if the directory is empty or missing (post-merge state).
"""
import subprocess
import pytest
from pathlib import Path

VALIDATORS_PATH = str(
    Path(__file__).resolve().parent.parent
    / "skills" / "scripts" / "models" / "validators.py"
)

SMOKE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "_smoke-test-plans"


def _get_smoke_plans() -> list[Path]:
    if not SMOKE_DIR.is_dir():
        return []
    return sorted(SMOKE_DIR.glob("*.md"))


smoke_plans = _get_smoke_plans()


@pytest.mark.skipif(not smoke_plans, reason="No smoke test fixtures (expected post-merge)")
@pytest.mark.parametrize("plan_path", smoke_plans, ids=[p.name for p in smoke_plans])
def test_real_plan_validates(plan_path: Path):
    """Each smoke test plan should pass Pydantic validation."""
    result = subprocess.run(
        [".venv/bin/python3", VALIDATORS_PATH, "plan", str(plan_path)],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, (
        f"Plan {plan_path.name} failed validation:\n{result.stderr}"
    )
```

- [ ] **Step 5: Run smoke tests**

Run: `.venv/bin/python3 -m pytest tests/unit/test_smoke_real_plans.py -v`
Expected: All fixtures PASS. If any FAIL:
- Schema bug → fix the schema, re-run
- Real plan-authoring mistake → document in test output, do NOT relax schema

- [ ] **Step 6: Commit (smoke test will be deleted in merge commit)**

```bash
git add tests/unit/test_smoke_real_plans.py tests/fixtures/_smoke-test-plans/
git commit -m "test: add pre-ship smoke test with real plan fixtures"
```

---

### Task 13: Obsolescence Verification

**Files:** None created — grep audit only.

This task is required by the Migration feature archetype. It verifies no stale references to legacy patterns remain after cutover.

- [ ] **Step 1: Grep for legacy patterns that should be routed around**

```bash
# Check that no NEW code calls the old regex path directly
grep -rn "check_sections" skills/subagent-driven-development/scripts/validate-plan.py
grep -rn "TASK_HEADER_RE\|MODULE_HEADER_RE" skills/subagent-driven-development/scripts/validate-plan.py
```

Expected: These patterns STILL EXIST in validate-plan.py (kept for Phase 7 cleanup). Verify they are only in the legacy branch (after the frontmatter detection guard).

- [ ] **Step 2: Verify prompt templates reference new format**

```bash
grep -rn "YAML frontmatter" skills/writing-plans/SKILL.md
grep -rn "YAML frontmatter\|schema_version" skills/handoff-acceptance/references/handoff-package-spec.md
grep -rn "YAML frontmatter" skills/subagent-driven-development/SKILL.md
```

Expected: Each file contains at least one reference to the new format.

- [ ] **Step 3: Verify no prompt template still instructs old format exclusively**

```bash
grep -rn "Contract Constraints.*first 50 lines" skills/
```

Expected: The old "first 50 lines" instruction should NOT appear in updated templates. If found in templates NOT modified by this plan, that's acceptable (Phase 7 cleanup).

- [ ] **Step 4: Run full test suite**

```bash
.venv/bin/python3 -m pytest tests/unit/ -v
python3 tests/ARaymond-skill-regression/validate-all-skills.py
bash tests/ARaymond-installation/verify-symlink-install.sh
```

Expected: All tests pass. Document any deviations in DEVIATIONS.md.

- [ ] **Step 5: Log findings**

If any stale references are found that are outside the scope of this plan (Phase 7 cleanup candidates), log them to DEVIATIONS.md:

```markdown
## Obsolescence Verification Findings

| Finding | Location | Disposition |
|---------|----------|-------------|
| Legacy regex patterns in validate-plan.py | `validate-plan.py:check_sections()` | Kept — Phase 7 cleanup |
| First-50-lines grep in check-handoff.sh | `check-handoff.sh:10-25` | Kept — Phase 7 cleanup |
```

- [ ] **Step 6: Commit if any deviations logged**

```bash
git add DEVIATIONS.md
git commit -m "docs: log obsolescence verification findings for Phase 7"
```

## Module 3 Acceptance Criteria

- [ ] `writing-plans/SKILL.md` has YAML frontmatter section with template
- [ ] `handoff-package-spec.md` has YAML frontmatter template
- [ ] `SDD SKILL.md` has one-line note about YAML frontmatter
- [ ] `CLAUDE.md` has Pydantic section (schema location, version bumps, bypass)
- [ ] `verify-symlink-install.sh` has 2 new Pydantic checks (total 105)
- [ ] Pre-ship smoke test present with ≥5 real plan fixtures, all PASS
- [ ] Obsolescence grep audit complete, findings logged
- [ ] All 3 test suites pass (pytest, regression, installation)
