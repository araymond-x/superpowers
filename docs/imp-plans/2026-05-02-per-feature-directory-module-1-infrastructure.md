---
schema_version: 1
feature_archetype: migration
source_contracts: "docs/specs/2026-05-02-per-feature-directory-design-distilled.md"
shared_constants: []
pattern_references:
  - name: "superpowers-root-resolution"
    source_files: ["skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh"]
    reason: "SUPERPOWERS_ROOT self-resolution preamble pattern (lines 27-34)"
modules: null
tasks:
  - id: 0
    title: "Contract Verification"
  - id: 1
    title: "Add .active-feature to .gitignore and create test helpers"
    depends_on: [0]
  - id: 2
    title: "Unit tests for .active-feature resolution and conflict detection"
    depends_on: [1]
  - id: 3
    title: "Unit tests for feature name validation"
    depends_on: [1]
---

# Per-Feature Directory — Module 1: Infrastructure & Testing Foundation

> **Parent plan:** `docs/imp-plans/2026-05-02-per-feature-directory-plan.md`
> **Module:** 1 of 3
> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first — direct implementation bypasses review enforcement, quality gates, and hooks.

**Module Goal:** Establish the `.active-feature` file convention, add it to `.gitignore`, and create the test infrastructure (helpers + unit tests) that Module 2's hook migrations will test against.

**Source Contracts:** `docs/specs/2026-05-02-per-feature-directory-design-distilled.md`

**Contract Constraints:**
- `.active-feature` is single-line plaintext at project root, contains relative path to feature dir
- Feature dir format: `docs/imp-plans/YYYY-MM-DD-<feature-name>/`
- Feature name is kebab-case
- `deviations.md` is lowercase (was `DEVIATIONS.md`)
- Gitignored — workspace state, not project state

**Feature Archetype:** Migration

## File Map

| File | Responsibility |
|------|----------------|
| `.gitignore` | Add `.active-feature` entry |
| `tests/unit/test_active_feature.py` | Unit tests for `.active-feature` resolution, conflict detection, feature name validation |
| `tests/unit/conftest.py` | Shared pytest fixtures for feature directory setup (if not already present) |

## Write-Scope Partitioning

| Task | Owned Files (write) | Read-Only Files | Depends On |
|------|---------------------|-----------------|------------|
| Task 0 | (verification only) | distilled spec, existing hooks | — |
| Task 1 | `.gitignore` | — | Task 0 |
| Task 2 | `tests/unit/test_active_feature.py` | — | Task 1 |
| Task 3 | `tests/unit/test_active_feature.py` (append) | — | Task 2 |

## Acceptance Criteria

- [ ] `.active-feature` is in `.gitignore`
- [ ] Unit tests verify: reading `.active-feature` returns correct path, empty/missing file returns empty string, conflict detection identifies stale pointers, completed features, and incomplete features
- [ ] Feature name validation rejects non-kebab-case names, names with special characters, empty names
- [ ] All tests pass with `pytest tests/unit/test_active_feature.py -v`

---

## Tasks

### Task 0: Contract Verification (BLOCKING)

**Files:**
- Read: `docs/specs/2026-05-02-per-feature-directory-design-distilled.md`
- Read: `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` (lines 27-34 for SUPERPOWERS_ROOT pattern)
- Read: `.gitignore`

- [ ] **Step 1: Read the distilled spec**

Read `docs/specs/2026-05-02-per-feature-directory-design-distilled.md` in full. Verify the Contract Facts section specifies:
- `.active-feature` format: single-line plaintext, relative path
- Feature dir format: `docs/imp-plans/YYYY-MM-DD-<feature-name>/`
- `deviations.md` lowercase
- Hooks fall back to root-level paths when `$FEAT` is empty

- [ ] **Step 2: Read the SUPERPOWERS_ROOT pattern**

Read `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` lines 27-34. Confirm the preamble pattern:

```bash
SUPERPOWERS_ROOT="${SUPERPOWERS_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
if [ -f "$SUPERPOWERS_ROOT/.venv/bin/python3" ]; then
  PYTHON="$SUPERPOWERS_ROOT/.venv/bin/python3"
else
  PYTHON="python3"
fi
```

This pattern will be replicated in `plan-validation-gate-hook.sh` and `sdd-stop-hook.sh` in Module 2.

- [ ] **Step 3: Verify .gitignore exists and check current contents**

Read `.gitignore`. Confirm `.active-feature` is NOT already listed. Note where to add it (near `.allow-main` if present, or at the end).

- [ ] **Step 4: Confirm contract facts**

Log confirmation that all contract facts verified against source files. No discrepancies.

---

### Task 1: Add .active-feature to .gitignore

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Add .active-feature to .gitignore**

Add `.active-feature` to `.gitignore`. Place it near other dot-files or at the end of the file:

```
# Superpowers workspace state
.active-feature
```

- [ ] **Step 2: Verify git will ignore the file**

Run: `touch .active-feature && git status`
Expected: `.active-feature` does NOT appear in untracked files.

Run: `rm .active-feature`

- [ ] **Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore: add .active-feature to .gitignore"
```

---

### Task 2: Unit tests for .active-feature resolution and conflict detection

**Files:**
- Create: `tests/unit/test_active_feature.py`

- [ ] **Step 1: Write tests for .active-feature reading**

Create `tests/unit/test_active_feature.py`:

```python
"""Tests for .active-feature file resolution and conflict detection.

These tests validate the shell logic that hooks will use to read .active-feature.
We test the behavior via subprocess calls to small bash snippets that mirror
the hook preamble.
"""
import os
import subprocess
import tempfile

import pytest


FEAT_PREAMBLE = '''
FEAT=""
if [ -f ".active-feature" ]; then
  FEAT=$(cat .active-feature)
fi
echo "$FEAT"
'''


class TestActiveFeatureResolution:
    """Test reading .active-feature and resolving the feature directory."""

    def test_reads_feature_dir_from_file(self, tmp_path):
        feat_file = tmp_path / ".active-feature"
        feat_file.write_text("docs/imp-plans/2026-05-02-my-feature")
        result = subprocess.run(
            ["bash", "-c", FEAT_PREAMBLE],
            cwd=str(tmp_path), capture_output=True, text=True
        )
        assert result.stdout.strip() == "docs/imp-plans/2026-05-02-my-feature"

    def test_returns_empty_when_file_missing(self, tmp_path):
        result = subprocess.run(
            ["bash", "-c", FEAT_PREAMBLE],
            cwd=str(tmp_path), capture_output=True, text=True
        )
        assert result.stdout.strip() == ""

    def test_returns_empty_when_file_is_empty(self, tmp_path):
        feat_file = tmp_path / ".active-feature"
        feat_file.write_text("")
        result = subprocess.run(
            ["bash", "-c", FEAT_PREAMBLE],
            cwd=str(tmp_path), capture_output=True, text=True
        )
        assert result.stdout.strip() == ""

    def test_strips_trailing_newline(self, tmp_path):
        feat_file = tmp_path / ".active-feature"
        feat_file.write_text("docs/imp-plans/2026-05-02-feature\n")
        result = subprocess.run(
            ["bash", "-c", FEAT_PREAMBLE],
            cwd=str(tmp_path), capture_output=True, text=True
        )
        assert result.stdout.strip() == "docs/imp-plans/2026-05-02-feature"

    def test_path_prefixing_works(self, tmp_path):
        feat_file = tmp_path / ".active-feature"
        feat_file.write_text("docs/imp-plans/2026-05-02-my-feature")
        feat_dir = tmp_path / "docs" / "imp-plans" / "2026-05-02-my-feature"
        feat_dir.mkdir(parents=True)
        reports_dir = feat_dir / "reports"
        reports_dir.mkdir()
        (reports_dir / "task-000-implementer-report.md").write_text("x" * 100)

        script = '''
FEAT=""
if [ -f ".active-feature" ]; then
  FEAT=$(cat .active-feature)
fi
if [ -d "$FEAT/reports" ]; then
  echo "FOUND"
else
  echo "MISSING"
fi
'''
        result = subprocess.run(
            ["bash", "-c", script],
            cwd=str(tmp_path), capture_output=True, text=True
        )
        assert result.stdout.strip() == "FOUND"


class TestConflictDetection:
    """Test detection of stale/conflicting .active-feature files."""

    def test_stale_pointer_detected(self, tmp_path):
        """Feature dir doesn't exist — stale pointer."""
        feat_file = tmp_path / ".active-feature"
        feat_file.write_text("docs/imp-plans/2026-01-01-deleted-feature")

        script = '''
FEAT=$(cat .active-feature 2>/dev/null)
if [ -n "$FEAT" ] && [ ! -d "$FEAT" ]; then
  echo "STALE"
else
  echo "OK"
fi
'''
        result = subprocess.run(
            ["bash", "-c", script],
            cwd=str(tmp_path), capture_output=True, text=True
        )
        assert result.stdout.strip() == "STALE"

    def test_completed_feature_detected(self, tmp_path):
        """Feature dir exists with plan where all tasks have matching reports."""
        feat_dir = tmp_path / "docs" / "imp-plans" / "2026-05-02-done-feature"
        reports_dir = feat_dir / "reports"
        reports_dir.mkdir(parents=True)

        plan = feat_dir / "plan.md"
        plan.write_text("### Task 0: Setup\n### Task 1: Build\n")

        (reports_dir / "task-000-implementer-report.md").write_text("x" * 100)
        (reports_dir / "task-001-implementer-report.md").write_text("x" * 100)

        feat_file = tmp_path / ".active-feature"
        feat_file.write_text("docs/imp-plans/2026-05-02-done-feature")

        script = '''
FEAT=$(cat .active-feature)
if [ -d "$FEAT" ] && [ -f "$FEAT/plan.md" ]; then
  TASK_COUNT=$(grep -c "^### Task " "$FEAT/plan.md" 2>/dev/null || echo 0)
  REPORT_COUNT=$(ls "$FEAT/reports/"task-*-implementer-report*.md 2>/dev/null | wc -l | tr -d " ")
  if [ "$TASK_COUNT" -gt 0 ] && [ "$REPORT_COUNT" -ge "$TASK_COUNT" ]; then
    echo "COMPLETED"
  else
    echo "INCOMPLETE"
  fi
else
  echo "NO_PLAN"
fi
'''
        result = subprocess.run(
            ["bash", "-c", script],
            cwd=str(tmp_path), capture_output=True, text=True
        )
        assert result.stdout.strip() == "COMPLETED"

    def test_incomplete_feature_detected(self, tmp_path):
        """Feature dir exists with plan but missing reports."""
        feat_dir = tmp_path / "docs" / "imp-plans" / "2026-05-02-wip-feature"
        reports_dir = feat_dir / "reports"
        reports_dir.mkdir(parents=True)

        plan = feat_dir / "plan.md"
        plan.write_text("### Task 0: Setup\n### Task 1: Build\n### Task 2: Test\n")

        (reports_dir / "task-000-implementer-report.md").write_text("x" * 100)

        feat_file = tmp_path / ".active-feature"
        feat_file.write_text("docs/imp-plans/2026-05-02-wip-feature")

        script = '''
FEAT=$(cat .active-feature)
if [ -d "$FEAT" ] && [ -f "$FEAT/plan.md" ]; then
  TASK_COUNT=$(grep -c "^### Task " "$FEAT/plan.md" 2>/dev/null || echo 0)
  REPORT_COUNT=$(ls "$FEAT/reports/"task-*-implementer-report*.md 2>/dev/null | wc -l | tr -d " ")
  if [ "$TASK_COUNT" -gt 0 ] && [ "$REPORT_COUNT" -ge "$TASK_COUNT" ]; then
    echo "COMPLETED"
  else
    echo "INCOMPLETE"
  fi
else
  echo "NO_PLAN"
fi
'''
        result = subprocess.run(
            ["bash", "-c", script],
            cwd=str(tmp_path), capture_output=True, text=True
        )
        assert result.stdout.strip() == "INCOMPLETE"

    def test_no_plan_detected(self, tmp_path):
        """Feature dir exists but has no plan (abandoned brainstorming)."""
        feat_dir = tmp_path / "docs" / "imp-plans" / "2026-05-02-abandoned"
        feat_dir.mkdir(parents=True)
        (feat_dir / "spec.md").write_text("# Some spec")

        feat_file = tmp_path / ".active-feature"
        feat_file.write_text("docs/imp-plans/2026-05-02-abandoned")

        script = '''
FEAT=$(cat .active-feature)
if [ -d "$FEAT" ] && [ -f "$FEAT/plan.md" ]; then
  echo "HAS_PLAN"
else
  echo "NO_PLAN"
fi
'''
        result = subprocess.run(
            ["bash", "-c", script],
            cwd=str(tmp_path), capture_output=True, text=True
        )
        assert result.stdout.strip() == "NO_PLAN"

    def test_fallback_to_root_when_no_active_feature(self, tmp_path):
        """Without .active-feature, paths resolve to root level (backwards compat)."""
        (tmp_path / "reports").mkdir()
        (tmp_path / "DEVIATIONS.md").write_text("# Deviations")

        script = '''
FEAT=""
if [ -f ".active-feature" ]; then
  FEAT=$(cat .active-feature)
fi
if [ -n "$FEAT" ]; then
  REPORTS="$FEAT/reports"
  DEVS="$FEAT/deviations.md"
else
  REPORTS="reports"
  DEVS="DEVIATIONS.md"
fi
if [ -d "$REPORTS" ] && [ -f "$DEVS" ]; then
  echo "RESOLVED"
else
  echo "MISSING"
fi
'''
        result = subprocess.run(
            ["bash", "-c", script],
            cwd=str(tmp_path), capture_output=True, text=True
        )
        assert result.stdout.strip() == "RESOLVED"
```

- [ ] **Step 2: Run tests to verify they all pass**

Run: `.venv/bin/python3 -m pytest tests/unit/test_active_feature.py -v`
Expected: All tests pass (they test bash snippets against temp directories, no production code yet).

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_active_feature.py
git commit -m "test: add unit tests for .active-feature resolution and conflict detection"
```

---

### Task 3: Unit tests for feature name validation

**Files:**
- Modify: `tests/unit/test_active_feature.py` (append)

- [ ] **Step 1: Add feature name validation tests**

Append to `tests/unit/test_active_feature.py`:

```python
class TestFeatureNameValidation:
    """Test that feature names follow kebab-case convention."""

    @pytest.mark.parametrize("name,expected", [
        ("pydantic-phase-2", True),
        ("statement-reconciliation-v3", True),
        ("fix-login-bug", True),
        ("a", True),
        ("2026-feature", True),
        ("PascalCase", False),
        ("camelCase", False),
        ("has spaces", False),
        ("has_underscores", False),
        ("ALLCAPS", False),
        ("has.dots", False),
        ("has/slashes", False),
        ("", False),
        ("has--double-dashes", False),
        ("-starts-with-dash", False),
        ("ends-with-dash-", False),
    ])
    def test_feature_name_validation(self, name, expected):
        """Validate kebab-case: lowercase letters, digits, single hyphens, no leading/trailing hyphens."""
        import re
        pattern = r'^[a-z0-9]+(-[a-z0-9]+)*$'
        result = bool(re.match(pattern, name)) if name else False
        assert result == expected, f"Expected {name!r} to be {'valid' if expected else 'invalid'}"

    def test_feature_dir_path_construction(self):
        """Verify the complete path format."""
        import re
        name = "pydantic-phase-2"
        date = "2026-05-02"
        path = f"docs/imp-plans/{date}-{name}"
        assert re.match(r'^docs/imp-plans/\d{4}-\d{2}-\d{2}-[a-z0-9]+(-[a-z0-9]+)*$', path)
```

- [ ] **Step 2: Run all tests**

Run: `.venv/bin/python3 -m pytest tests/unit/test_active_feature.py -v`
Expected: All tests pass.

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_active_feature.py
git commit -m "test: add feature name validation tests"
```
