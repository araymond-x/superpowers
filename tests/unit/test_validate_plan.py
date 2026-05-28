#!/usr/bin/env python3
"""
Unit tests for validate-plan.py — task numbering collision detection.

Tests cover:
  - Within-file duplicate task number detection (BLOCKER)
  - Cross-module task number collision detection (BLOCKER)
  - Clean plans with no duplicates (PASS)
  - Edge cases: single task, Task 0 only, non-contiguous numbering

Run: python3 -m pytest tests/unit/test_validate_plan.py -v
"""

import json
import os
import subprocess
import sys
import tempfile

# Path to the script under test
SCRIPT_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "skills",
    "subagent-driven-development",
    "scripts",
    "validate-plan.py",
)


def run_validate(
    plan_content: str, additional_plan_contents: list | None = None
) -> dict:
    """
    Write plan content to a temp file, run validate-plan.py, return parsed JSON output.
    If additional_plan_contents is provided, writes each to a temp file and passes
    via --additional-plan-files.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(plan_content)
        plan_path = f.name

    additional_paths = []
    if additional_plan_contents:
        for content in additional_plan_contents:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
                f.write(content)
                additional_paths.append(f.name)

    try:
        cmd = [sys.executable, SCRIPT_PATH, "--plan-file", plan_path]
        if additional_paths:
            cmd.extend(["--additional-plan-files"] + additional_paths)

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return {
            "exit_code": result.returncode,
            "output": json.loads(result.stdout) if result.stdout.strip() else {},
            "stderr": result.stderr,
        }
    finally:
        os.unlink(plan_path)
        for p in additional_paths:
            os.unlink(p)


# ---------------------------------------------------------------------------
# Fixtures: plan content templates
# ---------------------------------------------------------------------------

CLEAN_SINGLE_MODULE = """\
# Implementation Plan

**Source Contracts**: None
**Feature Archetype**: Replace-and-Rewire

## Code Footprint
- app/services/extractor.py (new)

### Task 0 — Contract verification
- [ ] Copy fixtures
- [ ] Run acceptance test

### Task 1 — Create module
- [ ] Implement extractor
- [ ] Add type hints

### Task 2 — Unit tests
- [ ] Test parse_amount
- [ ] Test parse_date

### Task 3 — Integration tests
- [ ] Contract compliance (8 types x 6 assertions)
"""

DUPLICATE_WITHIN_FILE = """\
# Implementation Plan

**Source Contracts**: None

### Task 0 — Setup
- [ ] Create scaffolding

### Task 1 — Implement feature A
- [ ] Write code

### Task 1 — Implement feature B
- [ ] Write different code

### Task 2 — Tests
- [ ] Write tests
"""

TRIPLE_DUPLICATE = """\
# Implementation Plan

**Source Contracts**: None

### Task 0 — Setup
- [ ] Scaffolding

### Task 1 — First version
- [ ] Code

### Task 1 — Second version
- [ ] More code

### Task 1 — Third version
- [ ] Even more code
"""

MODULE_1_CLEAN = """\
# Module 1: Pre-processor

**Source Contracts**: fixtures/account-types/

### Task 0 — Contract verification
- [ ] Copy fixtures

### Task 1 — Create pre-processor
- [ ] Implement module

### Task 2 — Unit tests
- [ ] Test functions

### Task 3 — Contract compliance
- [ ] 8 account types x 6 assertions
"""

MODULE_2_COLLISION = """\
# Module 2: Job Service

### Task 3 — Add extraction functions
- [ ] Implement alongside Bedrock

### Task 4 — Rewire process_job
- [ ] Remove Bedrock code

### Task 5 — Remove schemas
- [ ] Delete statement_schemas/
"""

MODULE_2_CLEAN = """\
# Module 2: Job Service

### Task 4 — Add extraction functions
- [ ] Implement alongside Bedrock

### Task 5 — Rewire process_job
- [ ] Remove Bedrock code

### Task 6 — Remove schemas
- [ ] Delete statement_schemas/
"""

SINGLE_TASK = """\
# Implementation Plan

**Source Contracts**: None

### Task 0 — The only task
- [ ] Do the thing
"""

# 802 lines with "Module" mid-heading (real writing-plans output format)
LONG_PLAN_MODULE_MID_HEADING = (
    "# Slack Agent Bridge v1 Inbound — Module 5: Hooks\n\n"
    "**Source Contracts**: None\n\n"
    "### Task 0 — Setup\n- [ ] Scaffolding\n\n"
    + "\n".join(f"Line {i}" for i in range(796))
    + "\n"
)

# 802 lines with "Module" as first word in heading (simple format)
LONG_PLAN_MODULE_FIRST_WORD = (
    "# Module 5: Hooks\n\n"
    "**Source Contracts**: None\n\n"
    "### Task 0 — Setup\n- [ ] Scaffolding\n\n"
    + "\n".join(f"Line {i}" for i in range(796))
    + "\n"
)

# 802 lines with NO module header at all
LONG_PLAN_NO_MODULE = (
    "# Implementation Plan\n\n"
    "**Source Contracts**: None\n\n"
    "### Task 0 — Setup\n- [ ] Scaffolding\n\n"
    + "\n".join(f"Line {i}" for i in range(796))
    + "\n"
)


# ---------------------------------------------------------------------------
# Tests: Within-file duplicate detection
# ---------------------------------------------------------------------------


class TestWithinFileDuplicates:
    """Task numbers must be unique within a single plan file."""

    def test_clean_plan_no_duplicates(self):
        result = run_validate(CLEAN_SINGLE_MODULE)
        assert result["exit_code"] in (0, 2), (
            f"Expected PASS or WARNING, got exit {result['exit_code']}"
        )
        assert "duplicate_task_numbers" not in result["output"].get("blockers", [])

    def test_duplicate_task_1_is_blocker(self):
        result = run_validate(DUPLICATE_WITHIN_FILE)
        assert result["exit_code"] == 1, (
            f"Expected FAIL (exit 1), got exit {result['exit_code']}"
        )
        assert "duplicate_task_numbers" in result["output"]["blockers"]

    def test_duplicate_reported_in_blocker_message(self):
        result = run_validate(DUPLICATE_WITHIN_FILE)
        dup_check = result["output"]["sections"].get("duplicate_task_numbers", {})
        assert "1" in dup_check.get("detail", ""), (
            "Blocker should identify Task 1 as duplicate"
        )

    def test_triple_duplicate_detected(self):
        result = run_validate(TRIPLE_DUPLICATE)
        assert result["exit_code"] == 1
        assert "duplicate_task_numbers" in result["output"]["blockers"]
        dup_check = result["output"]["sections"]["duplicate_task_numbers"]
        assert "3" in dup_check["detail"] or "1" in dup_check["detail"], (
            "Should report Task 1 appears 3 times"
        )

    def test_single_task_no_duplicate(self):
        result = run_validate(SINGLE_TASK)
        assert "duplicate_task_numbers" not in result["output"].get("blockers", [])


# ---------------------------------------------------------------------------
# Tests: Cross-module collision detection
# ---------------------------------------------------------------------------


class TestCrossModuleCollisions:
    """Task numbers must be unique across all module files."""

    def test_cross_module_collision_is_blocker(self):
        """M1 has Task 3, M2 also has Task 3 -> FAIL."""
        result = run_validate(MODULE_1_CLEAN, [MODULE_2_COLLISION])
        assert result["exit_code"] == 1, (
            f"Expected FAIL, got exit {result['exit_code']}"
        )
        assert "cross_module_task_collision" in result["output"]["blockers"]

    def test_cross_module_collision_identifies_task(self):
        """Blocker detail should identify Task 3 as the collision."""
        result = run_validate(MODULE_1_CLEAN, [MODULE_2_COLLISION])
        collision_check = result["output"]["sections"].get(
            "cross_module_task_collision", {}
        )
        assert "3" in collision_check.get("detail", ""), (
            "Should identify Task 3 as colliding"
        )

    def test_cross_module_no_collision(self):
        """M1 has Tasks 0-3, M2 has Tasks 4-6 -> PASS."""
        result = run_validate(MODULE_1_CLEAN, [MODULE_2_CLEAN])
        assert "cross_module_task_collision" not in result["output"].get("blockers", [])

    def test_no_additional_files_skips_cross_module_check(self):
        """Without --additional-plan-files, no cross-module check is run."""
        result = run_validate(MODULE_1_CLEAN)
        assert "cross_module_task_collision" not in result["output"].get("checks", {})

    def test_cross_module_collision_with_multiple_overlaps(self):
        """Multiple task numbers collide across files."""
        module_a = """\
# Module A

### Task 0 — Setup
- [ ] Do setup

### Task 1 — Build
- [ ] Build it
"""
        module_b = """\
# Module B

### Task 0 — Different setup
- [ ] Other setup

### Task 1 — Different build
- [ ] Other build
"""
        result = run_validate(module_a, [module_b])
        assert result["exit_code"] == 1
        assert "cross_module_task_collision" in result["output"]["blockers"]
        collision_check = result["output"]["sections"]["cross_module_task_collision"]
        assert "0" in collision_check["detail"]
        assert "1" in collision_check["detail"]


# ---------------------------------------------------------------------------
# Tests: Blocker message quality
# ---------------------------------------------------------------------------


class TestModuleHeaderDetection:
    """Plans over 800 lines must have a Module header to pass."""

    def _has_size_blocker(self, result: dict) -> bool:
        return any("800-line limit" in b for b in result["output"].get("blockers", []))

    def test_long_plan_with_module_mid_heading_passes(self):
        """'# Feature Name — Module 5: Hooks' should be recognized as modular."""
        result = run_validate(LONG_PLAN_MODULE_MID_HEADING)
        assert not self._has_size_blocker(result), (
            "Module in mid-heading should satisfy the modular decomposition check"
        )

    def test_long_plan_with_module_first_word_passes(self):
        """'# Module 5: Hooks' should be recognized as modular."""
        result = run_validate(LONG_PLAN_MODULE_FIRST_WORD)
        assert not self._has_size_blocker(result)

    def test_long_plan_without_module_header_blocked(self):
        """802-line plan with no Module header anywhere should be blocked."""
        result = run_validate(LONG_PLAN_NO_MODULE)
        assert self._has_size_blocker(result)


class TestBlockerMessages:
    """Blocker messages should explain WHY the collision matters."""

    def test_within_file_message_explains_hook_impact(self):
        result = run_validate(DUPLICATE_WITHIN_FILE)
        dup_check = result["output"]["sections"].get("duplicate_task_numbers", {})
        detail = dup_check.get("detail", "").lower()
        assert any(
            word in detail for word in ["report", "hook", "overwrite", "sequential"]
        ), (
            f"Blocker should explain WHY duplicates break the pipeline: {dup_check.get('detail', '')}"
        )

    def test_cross_module_message_explains_hook_impact(self):
        result = run_validate(MODULE_1_CLEAN, [MODULE_2_COLLISION])
        collision_check = result["output"]["sections"].get(
            "cross_module_task_collision", {}
        )
        detail = collision_check.get("detail", "").lower()
        assert any(
            word in detail for word in ["report", "hook", "overwrite", "sequential"]
        ), (
            f"Blocker should explain WHY cross-module collisions break the pipeline: {collision_check.get('detail', '')}"
        )


# ---------------------------------------------------------------------------
# Tests: Enforcement tier validation
# ---------------------------------------------------------------------------


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
- [ ] Fix the bug

**Task 1** — Test
- [ ] Test the fix
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

### Task 0
- [ ] Do thing 0
### Task 1
- [ ] Do thing 1
### Task 2
- [ ] Do thing 2
### Task 3
- [ ] Do thing 3
### Task 4
- [ ] Do thing 4
"""


# ---------------------------------------------------------------------------
# Tests: Frontmatter offset — header area should start after YAML frontmatter
# ---------------------------------------------------------------------------

# 35 lines of YAML frontmatter pushes section labels past line 50
PLAN_WITH_LONG_FRONTMATTER = """\
---
schema_version: 1
feature_archetype: greenfield
enforcement_tier: standard
source_contracts: null
contract_constraints: null
shared_constants: null
pattern_references: null
tasks:
  - id: 0
    title: "Contract verification"
  - id: 1
    title: "Write failing self-test for the CTA guard"
  - id: 2
    title: "Implement the CTA guard module"
  - id: 3
    title: "Wire CTA guard into the pipeline"
  - id: 4
    title: "Add integration test for CTA rendering"
  - id: 5
    title: "Test negative paths and edge cases"
  - id: 6
    title: "Update existing tests for new contract"
  - id: 7
    title: "Final acceptance and cleanup"
  - id: 8
    title: "Smoke test full pipeline"
  - id: 9
    title: "Documentation and handoff"
  - id: 10
    title: "Deploy behind feature flag"
  - id: 11
    title: "Monitor and validate in staging"
  - id: 12
    title: "Enable for beta users"
  - id: 13
    title: "Full rollout and cleanup"
modules: null
notes: |
  This plan has intentionally verbose frontmatter to exercise
  the header area offset logic. The YAML block consumes more
  than 45 lines, pushing markdown section labels past the
  original 50-line header window.
---
# Implementation Plan: CTA Guard

## Source Contracts: None
## Feature Archetype: Greenfield
**Contract Constraints**: Single-pass rendering only

## Code Footprint
- app/guards/cta.py (new)
- tests/unit/test_cta_guard.py (new)

### Task 0 — Contract verification
- [ ] Copy fixtures

### Task 1 — Write failing self-test
- [ ] Write test for guard logic
"""


class TestFrontmatterOffset:
    """Header area for section detection should start after YAML frontmatter."""

    def test_sections_detected_despite_long_frontmatter(self):
        result = run_validate(PLAN_WITH_LONG_FRONTMATTER)
        sections = result["output"].get("sections", {})
        assert sections["source_contracts"]["present"], (
            "Source Contracts should be detected after long frontmatter"
        )
        assert sections["feature_archetype"]["present"], (
            "Feature Archetype should be detected after long frontmatter"
        )
        assert sections["code_footprint"]["present"], (
            "Code Footprint should be detected after long frontmatter"
        )
        assert sections["contract_constraints"]["present"], (
            "Contract Constraints should be detected after long frontmatter"
        )

    def test_no_frontmatter_unchanged(self):
        """Plans without frontmatter should behave identically."""
        result = run_validate(CLEAN_SINGLE_MODULE)
        sections = result["output"].get("sections", {})
        assert sections["code_footprint"]["present"]
        assert sections["file_map"]["present"]


class TestEnforcementTierValidation:
    def test_valid_micro_tier_passes(self):
        result = run_validate(PLAN_WITH_MICRO_TIER)
        assert result["exit_code"] in (0, 2)  # PASS or WARNING

    def test_micro_with_many_tasks_warns(self):
        result = run_validate(PLAN_WITH_MICRO_TOO_MANY_TASKS)
        assert result["exit_code"] == 2  # WARNING
        sections = result["output"].get("sections", {})
        tier_check = sections.get("enforcement_tier_appropriateness", {})
        assert tier_check.get("status") == "WARNING"
