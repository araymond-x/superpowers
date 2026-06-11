---
schema_version: 1
feature_archetype: extension
enforcement_tier: standard
source_contracts: null
shared_constants: []
pattern_references:
  - name: "checkpoint-tests"
    source_files: ["tests/unit/test_pre_completion_gates.py"]
    reason: "Test patterns for pre-completion checks (ratio caps, git-reality)"
  - name: "validate-plan-tests"
    source_files: ["tests/unit/test_validate_plan.py"]
    reason: "Test patterns for validate-plan.py structural checks"
  - name: "transition-tests"
    source_files: ["tests/unit/test_transition_module.py"]
    reason: "Test patterns for transition-module.py"
  - name: "hook-subprocess-tests"
    source_files: ["tests/unit/test_sdd_classification.py"]
    reason: "Bash hook subprocess testing patterns"
  - name: "model-tests"
    source_files: ["tests/unit/test_models/test_implementer_report_model.py"]
    reason: "Pydantic model validation test patterns"
tasks:
  - id: 1
    title: "N16: ImplementerReport task_type exemption"
    pattern_references: ["model-tests"]
  - id: 2
    title: "N9: _task_ids_where + _load_all_plan_contents helpers"
    pattern_references: ["checkpoint-tests"]
  - id: 3
    title: "N5+N13: Fence-aware task-header parsing"
    depends_on: [2]
    pattern_references: ["validate-plan-tests", "checkpoint-tests"]
  - id: 4
    title: "N7: Source Contracts None equals valid-absent"
    depends_on: [3]
    pattern_references: ["checkpoint-tests"]
  - id: 5
    title: "N12: Split file-existence from provenance gating"
    pattern_references: ["transition-tests"]
  - id: 6
    title: "N17: Main-plan fallback for verification-id lookup"
    depends_on: [5]
    pattern_references: ["transition-tests"]
  - id: 7
    title: "N1: Multi-error accumulation regression test"
    review_tier: minimum
    pattern_references: ["hook-subprocess-tests"]
---

# Module 1: Cleanup — Implementation Plan

> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` via the Skill tool.

**Goal:** Close 7 enforcement-pipeline bugs (N16, N5+N13, N9, N7, N12, N17, N1) across controller-checkpoint.py, validate-plan.py, transition-module.py, and implementer_report.py.

**Source Contracts:** None

**Contract Constraints:** None

**Pattern References:**
- `tests/unit/test_models/test_implementer_report_model.py` — Pydantic model test patterns
- `tests/unit/test_pre_completion_gates.py` — pre-completion check test patterns
- `tests/unit/test_validate_plan.py` — validate-plan structural test patterns
- `tests/unit/test_transition_module.py` — transition-module test patterns
- `tests/unit/test_sdd_classification.py` — bash hook subprocess test patterns

**Acceptance Criteria:**
- N16: verification report w/ empty `files_changed` validates; implementation empty + DONE still FAILs; template + prompt emit `task_type`.
- N5: fenced task headers ignored at ALL 7 sites in validate-plan.py and controller-checkpoint.py.
- N9: single `_task_ids_where` + single `_load_all_plan_contents`; parent-only declarations visible.
- N7: `Source Contracts: None` yields pre-execution PASS.
- N12: micro+modules w/ self-review files + no dispatch log yields transition PASS.
- N17: transition reads verif ids from main plan when `module.file` empty.
- N1: regression test for multi-error accumulation; no hook edit; baseline untouched.

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `skills/scripts/models/implementer_report.py` | Modify | Add `task_type` field, exempt validator |
| `skills/subagent-driven-development/implementer-prompt.md` | Modify | Add `task_type` to report template |
| `skills/subagent-driven-development/SKILL.md` | Modify | Verification emit guidance |
| `skills/subagent-driven-development/scripts/validate-report.py` | Read-only | N16 verification tested against (not modified) |
| `skills/subagent-driven-development/scripts/controller-checkpoint.py` | Modify | N9 helpers, N5 fence-aware, N7 fix |
| `skills/subagent-driven-development/scripts/validate-plan.py` | Modify | N5 fence-aware parsing |
| `skills/subagent-driven-development/scripts/transition-module.py` | Modify | N12 + N17 |
| `docs/imp-plans/2026-06-01-sdd-enforcement-hardening/plan.md` | Modify | N13 mkdir backport |
| `tests/unit/test_n16_verification_report.py` | Create | N16 tests |
| `tests/unit/test_fence_aware_parsing.py` | Create | N5 tests |
| `tests/unit/test_n9_plan_loading_helpers.py` | Create | N9 tests |
| `tests/unit/test_n1_multi_error_accumulation.py` | Create | N1 regression test |

## Write-Scope Partitioning

| Task | Owned Files (write) | Read-Only Files | Depends On |
|------|---------------------|-----------------|------------|
| Task 1 | `implementer_report.py`, `implementer-prompt.md`, `SKILL.md` (SDD), `tests/unit/test_n16_verification_report.py` | `_base.py`, `validate-report.py` | — |
| Task 2 | `controller-checkpoint.py`, `tests/unit/test_n9_plan_loading_helpers.py` | `plan.py`, `sdd_session.py` | — |
| Task 3 | `validate-plan.py`, `controller-checkpoint.py`, `tests/unit/test_fence_aware_parsing.py`, `plan.md` (hardening) | — | Task 2 |
| Task 4 | `controller-checkpoint.py`, existing checkpoint tests | — | Task 3 |
| Task 5 | `transition-module.py`, existing transition tests | `sdd_session.py` | — |
| Task 6 | `transition-module.py`, existing transition tests | — | Task 5 |
| Task 7 | `tests/unit/test_n1_multi_error_accumulation.py` | `sdd-pre-dispatch-hook.sh` | — |

Note: Tasks 2, 3, 4 serialize on `controller-checkpoint.py`. Tasks 5, 6 serialize on `transition-module.py`. Task 1 and Task 7 have no file conflicts with any other task.

---

### Task 1: N16 — ImplementerReport task_type exemption

**Files:**
- Modify: `skills/scripts/models/implementer_report.py`
- Modify: `skills/subagent-driven-development/implementer-prompt.md:193-206`
- Modify: `skills/subagent-driven-development/SKILL.md:357-359`
- Create: `tests/unit/test_n16_verification_report.py`

**Pattern References:** `tests/unit/test_models/test_implementer_report_model.py` — follow existing model test patterns.

- [x] **Step 1: Write failing tests** in `tests/unit/test_n16_verification_report.py`

Read `tests/unit/test_models/test_implementer_report_model.py` for existing patterns. Write 6 tests:

```python
"""N16: ImplementerReport task_type field + verification exemption.
Run: .venv/bin/python3 -m pytest tests/unit/test_n16_verification_report.py -v
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills/scripts/models"))
from implementer_report import ImplementerReport


def _base_report(**overrides):
    defaults = {
        "schema_version": 1,
        "task_id": 5,
        "status": "DONE",
        "files_changed": [{"path": "foo.py", "description": "changed"}],
        "tests": {"written": 1, "passing": 1, "command": "pytest", "result": "PASS"},
    }
    defaults.update(overrides)
    return defaults


class TestTaskTypeField:
    def test_default_is_implementation(self):
        r = ImplementerReport(**_base_report())
        assert r.task_type == "implementation"

    def test_explicit_verification(self):
        r = ImplementerReport(**_base_report(task_type="verification"))
        assert r.task_type == "verification"

    def test_invalid_value_rejected(self):
        with pytest.raises(Exception):
            ImplementerReport(**_base_report(task_type="audit"))


class TestVerificationExemption:
    def test_verification_done_empty_files_passes(self):
        """N16 core fix: verification task with DONE + empty files_changed is valid."""
        r = ImplementerReport(**_base_report(
            task_type="verification",
            status="DONE",
            files_changed=[],
        ))
        assert r.status == "DONE"
        assert r.files_changed == []

    def test_implementation_done_empty_files_still_fails(self):
        """Implementation tasks must still have files_changed when DONE."""
        with pytest.raises(ValueError, match="files_changed is empty"):
            ImplementerReport(**_base_report(
                task_type="implementation",
                status="DONE",
                files_changed=[],
            ))

    def test_verification_blocked_empty_files_passes(self):
        """Non-DONE statuses with empty files always pass (existing behavior)."""
        r = ImplementerReport(**_base_report(
            task_type="verification",
            status="BLOCKED",
            files_changed=[],
        ))
        assert r.status == "BLOCKED"
```

- [x] **Step 2: Run tests — expect FAIL**

```bash
.venv/bin/python3 -m pytest tests/unit/test_n16_verification_report.py -v
```

Expected: `test_default_is_implementation` FAILS (no `task_type` field), `test_verification_done_empty_files_passes` FAILS (validator rejects it).

- [x] **Step 3: Add `task_type` field to ImplementerReport**

In `skills/scripts/models/implementer_report.py`, add the field and update the validator:

```python
# Add import at top (Literal already imported)
# Add field to ImplementerReport class, after contract_compliance:
    task_type: Literal["implementation", "verification"] = "implementation"

# Update the files_changed_non_empty_for_done validator:
    @model_validator(mode="after")
    def files_changed_non_empty_for_done(self) -> "ImplementerReport":
        if self.task_type == "verification":
            return self
        if self.status in ("DONE", "DONE_WITH_CONCERNS") and not self.files_changed:
            raise ValueError(
                f"status is {self.status} but files_changed is empty — "
                f"completed tasks must list at least one file"
            )
        return self
```

- [x] **Step 4: Run tests — expect PASS**

```bash
.venv/bin/python3 -m pytest tests/unit/test_n16_verification_report.py -v
```

Expected: All 6 tests PASS.

- [x] **Step 5: Update report template in implementer-prompt.md**

In `skills/subagent-driven-development/implementer-prompt.md`, find the YAML frontmatter template (~line 193-206). Add `task_type` after `task_id`:

```yaml
    schema_version: 1
    task_id: [your task number]
    task_type: implementation
    status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
```

- [x] **Step 6: Update SDD SKILL.md verification guidance**

In `skills/subagent-driven-development/SKILL.md`, find the "Modified implementer prompt for verification tasks" section (~line 357-359). Add after the auditor quote:

Add a line instructing the subagent: "Set `task_type: verification` in your report frontmatter."

Check word count stays under 5000: `wc -w skills/subagent-driven-development/SKILL.md`

> **Audit Order 5 (IMPORTANT):** Current SKILL.md is 4904 words — only 96 words of headroom. Keep the addition to a single sentence (e.g., "Set `task_type: verification` in your report frontmatter."). If the resulting count exceeds 4950, extract equivalent content to `references/` first.

- [x] **Step 7: Add validate-report CLI fixture test**

Add a test that writes a complete markdown report file (valid YAML frontmatter with `task_type: verification`, `status: DONE`, `files_changed: []`, plus all 5 prose sections), runs `validate-report.py --report-file <path>`, and asserts exit code 0. Also write a report with `task_type: implementation`, `status: DONE`, `files_changed: []` and assert exit code 1 (Pydantic rejects it). This verifies the N16 fix flows through the full CLI validation pipeline, not just the in-process Pydantic model.

- [x] **Step 8: Run full existing test suite to check no regressions**

```bash
.venv/bin/python3 -m pytest tests/unit/test_models/ -v
.venv/bin/python3 -m pytest tests/unit/test_n16_verification_report.py -v
```

Expected: All tests PASS.

- [x] **Step 9: Commit**

```bash
git add skills/scripts/models/implementer_report.py \
       skills/subagent-driven-development/implementer-prompt.md \
       skills/subagent-driven-development/SKILL.md \
       tests/unit/test_n16_verification_report.py
git commit -m "feat(N16): add task_type to ImplementerReport, exempt verification from files_changed"
```

---

### Task 2: N9 — _task_ids_where + _load_all_plan_contents helpers

**Files:**
- Modify: `skills/subagent-driven-development/scripts/controller-checkpoint.py`
- Create: `tests/unit/test_n9_plan_loading_helpers.py`

**Pattern References:** `tests/unit/test_pre_completion_gates.py` — follow existing checkpoint test patterns.

- [x] **Step 1: Write failing tests** in `tests/unit/test_n9_plan_loading_helpers.py`

Read `tests/unit/test_pre_completion_gates.py` for patterns. Write tests for the two new helpers:

```python
"""N9: _task_ids_where + _load_all_plan_contents helpers.
Run: .venv/bin/python3 -m pytest tests/unit/test_n9_plan_loading_helpers.py -v
"""
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPT_PATH = os.path.join(ROOT, "skills", "subagent-driven-development", "scripts", "controller-checkpoint.py")

def _load_checkpoint():
    spec = importlib.util.spec_from_file_location("controller_checkpoint", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_ckpt = _load_checkpoint()


PLAN_WITH_MIN = """---
schema_version: 1
feature_archetype: extension
tasks:
  - id: 1
    title: "Task one"
    review_tier: minimum
  - id: 2
    title: "Task two"
  - id: 3
    title: "Task three"
    task_type: verification
---
# Plan
"""

PLAN_NO_FM = "# Plan with no frontmatter\n"


class TestTaskIdsWhere:
    def test_review_tier_minimum(self):
        _task_ids_where = _ckpt._task_ids_where
        ids, parsed = _task_ids_where([PLAN_WITH_MIN], "review_tier", "minimum")
        assert ids == {1}
        assert parsed is True

    def test_task_type_verification(self):
        _task_ids_where = _ckpt._task_ids_where
        ids, parsed = _task_ids_where([PLAN_WITH_MIN], "task_type", "verification")
        assert ids == {3}
        assert parsed is True

    def test_no_frontmatter(self):
        _task_ids_where = _ckpt._task_ids_where
        ids, parsed = _task_ids_where([PLAN_NO_FM], "review_tier", "minimum")
        assert ids == set()
        assert parsed is False

    def test_multi_file_aggregation(self):
        _task_ids_where = _ckpt._task_ids_where
        plan2 = """---
schema_version: 1
feature_archetype: extension
tasks:
  - id: 4
    title: "Task four"
    review_tier: minimum
---
"""
        ids, parsed = _task_ids_where([PLAN_WITH_MIN, plan2], "review_tier", "minimum")
        assert ids == {1, 4}


class TestLoadAllPlanContents:
    def test_parent_plus_modules(self, tmp_path):
        _load_all_plan_contents = _ckpt._load_all_plan_contents
        feat = tmp_path / "feat"
        feat.mkdir()
        parent = feat / "plan.md"
        parent.write_text("# Parent plan\n")
        mod1 = feat / "module-1.md"
        mod1.write_text("# Module 1\n")
        manifest = {
            "plan_file": "feat/plan.md",
            "paths": {"feature_dir": "feat"},
            "modules": [{"id": 1, "title": "M1", "task_ids": [1], "file": "module-1.md"}],
        }
        result = _load_all_plan_contents(manifest, str(tmp_path))
        assert len(result) == 2
        assert "# Parent plan" in result[0]
        assert "# Module 1" in result[1]

    def test_deduplicates(self, tmp_path):
        _load_all_plan_contents = _ckpt._load_all_plan_contents
        feat = tmp_path / "feat"
        feat.mkdir()
        plan = feat / "plan.md"
        plan.write_text("# Plan\n")
        manifest = {
            "plan_file": "feat/plan.md",
            "paths": {"feature_dir": "feat"},
            "modules": [{"id": 1, "title": "M1", "task_ids": [1], "file": "plan.md"}],
        }
        result = _load_all_plan_contents(manifest, str(tmp_path))
        assert len(result) == 1

    def test_missing_module_file_skipped(self, tmp_path):
        _load_all_plan_contents = _ckpt._load_all_plan_contents
        feat = tmp_path / "feat"
        feat.mkdir()
        plan = feat / "plan.md"
        plan.write_text("# Plan\n")
        manifest = {
            "plan_file": "feat/plan.md",
            "paths": {"feature_dir": "feat"},
            "modules": [{"id": 1, "title": "M1", "task_ids": [1], "file": "gone.md"}],
        }
        result = _load_all_plan_contents(manifest, str(tmp_path))
        assert len(result) == 1
```

- [x] **Step 2: Run tests — expect FAIL**

```bash
.venv/bin/python3 -m pytest tests/unit/test_n9_plan_loading_helpers.py -v
```

Expected: ImportError — `_task_ids_where` and `_load_all_plan_contents` don't exist yet.

- [x] **Step 3: Implement _task_ids_where**

In `controller-checkpoint.py`, replace `_declared_minimum_task_ids` (~L232-264) and `_verification_task_ids` (~L267-293) with a single generic `_task_ids_where(plan_contents, field, value) -> (set, bool)`. Same YAML-parse logic, parameterized by field name and target value. Update all callers: `_declared_minimum_task_ids(x)` → `_task_ids_where(x, "review_tier", "minimum")`, `_verification_task_ids(x)` → `_task_ids_where(x, "task_type", "verification")`. Remove the two old functions.

- [x] **Step 4: Implement _load_all_plan_contents**

Add `_load_all_plan_contents(manifest_data, git_root) -> list[str]` to `controller-checkpoint.py`. It reads the parent plan (`manifest_data["plan_file"]`), then each module's file (`<git_root>/<feature_dir>/<module.file>`). De-duplicates by `os.path.realpath`. Skips missing files. Returns list of file content strings. Use the existing `read_file()` helper.

- [x] **Step 5: Retrofit pre-completion to use _load_all_plan_contents**

In `run_pre_completion`, replace the ad-hoc module-file loading block (~lines 1057-1068) with a call to `_load_all_plan_contents`. Replace `_declared_minimum_task_ids` call with `_task_ids_where`: `declared_min, _parsed = _task_ids_where(all_plan_contents, "review_tier", "minimum")`. Replace `_verification_task_ids` call with unpacked `_task_ids_where`: `verification_ids, _ = _task_ids_where(all_plan_contents, "task_type", "verification")` — note the tuple unpack, since `_task_ids_where` returns `(set, bool)` while the old function returned a bare `set`.

> **Audit Order 2 (BLOCKING) — Double-count prevention:** When manifest is present, set `all_plan_contents = _load_all_plan_contents(manifest_data, git_root)` as a **full replacement** — do NOT extend the existing `[plan_content]` seed. Remove the L1046 seed initialization and the L1057-1068 ad-hoc block entirely in the manifest case. When manifest is absent, keep `all_plan_contents = [plan_content]` unchanged (single-file fallback). The helper already de-duplicates by `os.path.realpath`, so the active module appears exactly once. CRITICAL: `_load_manifest_config` mutates `args.plan_file` to the active module (L595-598), so `plan_content` at L1040 is the active module — appending `_load_all_plan_contents` output would double-count it.

- [x] **Step 6: Run tests — expect PASS**

```bash
.venv/bin/python3 -m pytest tests/unit/test_n9_plan_loading_helpers.py -v
.venv/bin/python3 -m pytest tests/unit/test_pre_completion_gates.py -v
```

Expected: All tests PASS, including existing pre-completion tests (behavior unchanged).

- [x] **Step 7: Commit**

```bash
git add skills/subagent-driven-development/scripts/controller-checkpoint.py \
       tests/unit/test_n9_plan_loading_helpers.py
git commit -m "refactor(N9): collapse declared-min/verif helpers into _task_ids_where + _load_all_plan_contents"
```

---

### Task 3: N5+N13 — Fence-aware task-header parsing

**Files:**
- Modify: `skills/subagent-driven-development/scripts/validate-plan.py:48,160,264`
- Modify: `skills/subagent-driven-development/scripts/controller-checkpoint.py:58,429,474,486`
- Modify: `docs/imp-plans/2026-06-01-sdd-enforcement-hardening/plan.md` (N13)
- Create: `tests/unit/test_fence_aware_parsing.py`

**Pattern References:** `tests/unit/test_validate_plan.py`, `tests/unit/test_pre_completion_gates.py`

- [x] **Step 1: Write failing tests** in `tests/unit/test_fence_aware_parsing.py`

```python
"""N5: Fence-aware task-header parsing at all 7 sites.
Run: .venv/bin/python3 -m pytest tests/unit/test_fence_aware_parsing.py -v
"""
import importlib.util
import os
import re

import pytest

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))

def _load_script(name, filename):
    path = os.path.join(ROOT, "skills", "subagent-driven-development", "scripts", filename)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_vp = _load_script("validate_plan", "validate-plan.py")
_ckpt = _load_script("controller_checkpoint", "controller-checkpoint.py")


# SELF-HOSTING GUARD: use _H variable to avoid plan-validator false match.
# The f-string interpolates at runtime; the plan file never has literal
# "### Task <digit>" at column 0 in fixture strings.
_H = "##" + "# Task"  # => "### Task" at runtime

FENCED_PLAN = f"""---
schema_version: 1
feature_archetype: extension
tasks:
  - id: 1
    title: "Real task"
  - id: 2
    title: "Another real task"
---

# Plan

{_H} 1: Real task

Do something.

```markdown
{_H} 99: This is inside a fence and must be ignored
```

{_H} 2: Another real task

Do something else.
"""


class TestValidatePlanFenceAware:
    def test_extract_task_numbers_ignores_fenced(self):
        extract_task_numbers = _vp.extract_task_numbers
        nums = extract_task_numbers(FENCED_PLAN)
        assert 99 not in nums
        assert sorted(nums) == [1, 2]

    def test_analyse_tasks_ignores_fenced(self):
        analyse_tasks = _vp.analyse_tasks
        tasks, warnings, blockers = analyse_tasks(FENCED_PLAN.splitlines())
        task_nums = [t["number"] for t in tasks]
        assert 99 not in task_nums
        assert sorted(task_nums) == [1, 2]

    def test_task_zero_check_ignores_fenced(self):
        fenced_zero = f"\n```\n{_H} 0: Fake task zero inside fence\n```\n\n{_H} 1: Real first task\n"
        check_sections = _vp.check_sections
        lines = fenced_zero.splitlines()
        sections = check_sections(lines, fenced_zero)
        assert sections["task_0"]["present"] is False


class TestCheckpointFenceAware:
    def test_count_tasks_ignores_fenced(self):
        count_tasks = _ckpt.count_tasks
        assert count_tasks(FENCED_PLAN) == 2

    def test_has_task_zero_ignores_fenced(self):
        fenced_zero = f"\n```\n{_H} 0: Fake zero\n```\n{_H} 1: Real\n"
        has_task_zero = _ckpt.has_task_zero
        assert has_task_zero(fenced_zero) is False

    def test_checkbox_range_ignores_fenced_headers(self):
        plan = f"{_H} 1: Real\n\n- [ ] Step A\n\n```\n{_H} 2: Fake boundary\n- [ ] Fake checkbox\n```\n\n- [ ] Step B\n\n{_H} 2: Real next\n- [ ] Step C\n"
        get_task_checkbox_range = _ckpt.get_task_checkbox_range
        cbs = get_task_checkbox_range(plan, 1)
        assert cbs["unchecked"] == 2  # Step A + Step B, not the fenced one
```

- [x] **Step 2: Run tests — expect FAIL**

```bash
.venv/bin/python3 -m pytest tests/unit/test_fence_aware_parsing.py -v
```

Expected: Tests FAIL because current parsing is fence-blind.

- [x] **Step 3: Add fence-aware helpers**

Add a helper function to each script that filters out lines inside fence blocks. The approach: track fence state while iterating lines, mark fenced lines.

In `validate-plan.py`, add a helper before `extract_task_numbers`:

```python
def _unfenced_content(text: str) -> str:
    """Return text with lines inside ``` fence blocks replaced by blank lines.

    Preserves line numbering so span calculations remain correct.
    """
    lines = text.splitlines(keepends=True)
    result = []
    in_fence = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            result.append("\n")
        elif in_fence:
            result.append("\n")
        else:
            result.append(line)
    return "".join(result)
```

Route all 3 sites through it:
1. `extract_task_numbers`: `return [int(m) for m in TASK_HEADER_RE.findall(_unfenced_content(content))]`
2. `analyse_tasks`: operate on `_unfenced_content("\n".join(lines)).splitlines()` for header detection, keep original lines for span measurement
3. `check_sections` Task 0 check (~L264): use `_unfenced_content(full_content)` for the Task 0 search

In `controller-checkpoint.py`, add the same helper and route 4 sites:
1. `count_tasks`: apply to content before regex
2. `has_task_zero` (~L429): apply to content before regex
3. `get_task_checkbox_range` (~L474): apply `_unfenced_content` **inside** the function body (not at the call site). The Step 1 test passes raw fenced content and expects the function to ignore fenced checkboxes internally. (Audit Order 4 clarification: unfence internally, not caller-side.)
4. `all_tasks_have_reports` (~L506): apply to content for task number extraction. (Auditor cross-ref: this is an 8th fence-affected site not counted in the "7 sites" — apply `_unfenced_content` here too for completeness.)

- [x] **Step 4: Run tests — expect PASS**

```bash
.venv/bin/python3 -m pytest tests/unit/test_fence_aware_parsing.py -v
.venv/bin/python3 -m pytest tests/unit/test_validate_plan.py -v
.venv/bin/python3 -m pytest tests/unit/test_pre_completion_gates.py -v
```

Expected: All tests PASS.

- [x] **Step 5: N13 — Backport mkdir lines to hardening plan**

In `docs/imp-plans/2026-06-01-sdd-enforcement-hardening/plan.md`, find the Task 4 code snippet (~line 801-802) where `setup_manifest_workspace` is called. Add the two missing `mkdir()` calls that were discovered during execution:

Find the first `_impl(reports / ...)` call in the Task 4 snippet and add before it:
```python
    reports.mkdir(exist_ok=True)
    (reports / ".dispatch-log").parent.mkdir(parents=True, exist_ok=True)
```

This is a documentation fix — the test code itself already works (it was fixed during implementation).

- [x] **Step 6: Commit**

```bash
git add skills/subagent-driven-development/scripts/validate-plan.py \
       skills/subagent-driven-development/scripts/controller-checkpoint.py \
       tests/unit/test_fence_aware_parsing.py \
       docs/imp-plans/2026-06-01-sdd-enforcement-hardening/plan.md
git commit -m "fix(N5): fence-aware task-header parsing at all 7 sites; fix(N13): backport mkdir to hardening plan"
```

---

### Task 4: N7 — Source Contracts None equals valid-absent

**Files:**
- Modify: `skills/subagent-driven-development/scripts/controller-checkpoint.py:444-465,690-694`

**Pattern References:** `tests/unit/test_pre_completion_gates.py`

- [x] **Step 1: Write failing test**

Add to `tests/unit/test_fence_aware_parsing.py` (or inline in the existing checkpoint test file — follow the test organization convention):

```python
class TestSourceContractsNonePass:
    def test_source_contracts_none_is_valid_absent(self, tmp_path):
        """N7: Source Contracts: None should yield PASS, not FAIL."""
        plan = tmp_path / "plan.md"
        plan.write_text(
            "---\nschema_version: 1\nfeature_archetype: extension\n"
            "source_contracts: null\ntasks:\n  - id: 1\n    title: T\n---\n"
            "# Plan\n\n**Source Contracts:** None\n\n**Contract Constraints:** None\n\n"
            "**Feature Archetype:** Extension\n\n**Code Footprint:**\n\n"
            "| Cat | Files | Action | Deps |\n|--|--|--|--|\n| New | f.py | Create | - |\n\n"
            f"{_H} 1: Do thing\n- [ ] Step 1\n"
        )
        run_pre_execution = _ckpt.run_pre_execution
        import argparse
        args = argparse.Namespace(
            plan_file=str(plan),
            deviations_file=None,
            reports_dir=None,
            manifest=None,
        )
        result = run_pre_execution(args)
        sc = result["checks"].get("source_contracts", {})
        assert sc["status"] != "FAIL", f"Source Contracts: None should PASS, got {sc}"
```

- [x] **Step 2: Run test — expect FAIL**

```bash
.venv/bin/python3 -m pytest tests/unit/test_fence_aware_parsing.py::TestSourceContractsNonePass -v
```

Expected: FAIL — current code treats "None" as non-empty content after the header.

- [x] **Step 3: Fix source_contracts_non_empty**

In `controller-checkpoint.py`, modify the `source_contracts_non_empty` function (~L444-465). The fix: treat "None", "N/A", empty, and "—" as valid-absent (return False), so the pre-execution check at ~L690-694 gets `PASS` instead of `FAIL`.

Current code already has this logic:
```python
    first_line = body_lines[0].lower()
    return first_line not in {"none", "n/a", "na", "-", "—"}
```

The bug is in the pre-execution check at ~L683-694: it calls `source_contracts_non_empty` and when it returns `False` (meaning "None"), the check says FAIL. Fix: change the logic so `False` means the section is present but legitimately empty/None, which should be OK (not FAIL).

Replace the source_contracts check block (~L683-694):

```python
    if source_contracts_present(plan_content):
        if source_contracts_non_empty(plan_content):
            checks["source_contracts"] = {
                "status": "PASS",
                "detail": "Source Contracts section present and non-empty",
            }
        else:
            checks["source_contracts"] = {
                "status": "OK",
                "detail": "Source Contracts section present — declared as None/empty (valid-absent)",
            }
    else:
        checks["source_contracts"] = {
            "status": "OK",
            "detail": "No Source Contracts section — Task 0 not required",
        }
```

The key change: `None`/empty source contracts → `OK` (was `FAIL` + blocker).

- [x] **Step 3b: Consolidate `_unfenced_content` into `_report_utils.py` (scope addition 2026-06-10 — Task 3 quality review Important Issue 2 + partner-review finding; see deviations.md Scope Changes)**

Move the byte-identical `_unfenced_content` helper out of `validate-plan.py` and `controller-checkpoint.py` into `skills/subagent-driven-development/scripts/_report_utils.py` (the declared shared library / single source of truth). Update BOTH scripts to import it — follow the existing sibling-import pattern (`_midpoint.py` is imported by materialize-manifest.py and transition-module.py; check how those scripts and their importlib-loading tests handle the sibling import, and mirror it). Delete both local copies. All existing fence-aware tests must pass unchanged — they exercise behavior through the scripts' public functions, not the helper directly. Commit the consolidation as a SEPARATE commit: `refactor(SSOT): consolidate _unfenced_content into _report_utils.py`.

- [x] **Step 4: Run tests — expect PASS**

```bash
.venv/bin/python3 -m pytest tests/unit/test_fence_aware_parsing.py::TestSourceContractsNonePass -v
.venv/bin/python3 -m pytest tests/unit/test_pre_completion_gates.py -v
```

Expected: All tests PASS.

- [x] **Step 5: Commit**

```bash
git add skills/subagent-driven-development/scripts/controller-checkpoint.py \
       tests/unit/test_fence_aware_parsing.py
git commit -m "fix(N7): Source Contracts None/empty treated as valid-absent, not FAIL"
```

---

### Task 5: N12 — Split file-existence from provenance gating

**Files:**
- Modify: `skills/subagent-driven-development/scripts/transition-module.py:122-130`

**Pattern References:** `tests/unit/test_transition_module.py`

- [x] **Step 1: Write failing test**

Add to `tests/unit/test_transition_module.py` (extend existing file):

```python
class TestN12SplitFileProvenance:
    def test_micro_modules_self_review_no_dispatch_log_passes(self, tmp_path):
        """N12: With dispatch_provenance=False, missing dispatch log should not
        cause transition failure if review files exist."""
        # Setup a micro-tier manifest with dispatch_provenance=False
        # but spec/quality review files present (self-written)
        # Expect: transition PASS (file-existence gates pass, provenance skipped)
        pass  # fill with actual setup using manifest workspace helpers

    def test_missing_self_review_files_still_fails(self, tmp_path):
        """N12: Even without provenance gating, review FILES must exist."""
        pass  # fill: micro manifest, no quality-review file -> FAIL
```

Read `tests/unit/test_transition_module.py` for the exact workspace setup pattern, then fill in the test bodies with real setup code following the existing patterns.

- [x] **Step 2: Run tests — expect FAIL**

```bash
.venv/bin/python3 -m pytest tests/unit/test_transition_module.py::TestN12SplitFileProvenance -v
```

- [x] **Step 3: Fix validate_module_completion**

In `transition-module.py:validate_module_completion` (~L122-130), the current code gates both file-existence AND provenance on `process_requirements.{spec,quality}_review_mode != "skip"`. The fix: keep file-existence under `review_mode != "skip"`, but gate ONLY `_has_dispatch_provenance()` on `manifest.enforcement.dispatch_provenance`.

```python
        if pr.spec_review_mode != "skip":
            spec_report = os.path.join(reports_dir, f"task-{padded}-spec-review.md")
            if not os.path.isfile(spec_report) or os.path.getsize(spec_report) < 50:
                errors.append(f"Task {task_id}: missing or empty spec review")
            elif manifest.enforcement.dispatch_provenance and not _has_dispatch_provenance(dispatch_log, task_id, "spec-review"):
                errors.append(f"Task {task_id}: spec review not provenance-logged")

        if pr.quality_review_mode != "skip":
            # ... same pattern for quality: file-existence always, provenance only when enforced
```

- [x] **Step 4: Run tests — expect PASS**

```bash
.venv/bin/python3 -m pytest tests/unit/test_transition_module.py -v
```

- [x] **Step 5: Commit**

```bash
git add skills/subagent-driven-development/scripts/transition-module.py \
       tests/unit/test_transition_module.py
git commit -m "fix(N12): gate only provenance on dispatch_provenance, not file-existence"
```

---

### Task 6: N17 — Main-plan fallback for verification-id lookup

**Files:**
- Modify: `skills/subagent-driven-development/scripts/transition-module.py:109-112`

**Pattern References:** `tests/unit/test_transition_module.py`

- [x] **Step 1: Write failing test**

Add to `tests/unit/test_transition_module.py`:

```python
class TestN17MainPlanFallback:
    def test_reads_verif_ids_from_main_plan_when_module_file_empty(self, tmp_path):
        """N17: When module.file is empty, read verification IDs from the main plan."""
        # Setup: manifest with a module whose file="" but main plan declares
        # task_type: verification on a task in that module's range.
        # validate_module_completion should still exempt that task from reviews.
        pass  # fill with actual setup
```

- [x] **Step 2: Run test — expect FAIL**

```bash
.venv/bin/python3 -m pytest tests/unit/test_transition_module.py::TestN17MainPlanFallback -v
```

- [x] **Step 3: Add main-plan fallback**

In `transition-module.py`, at ~line 109-112, where `verif_ids` is populated:

```python
    verif_ids: set = set()
    if module.file:
        module_plan = os.path.join(git_root, manifest.paths.feature_dir, module.file)
        verif_ids = _verification_task_ids_from_file(module_plan)
    else:
        main_plan = os.path.join(git_root, manifest.plan_file)
        verif_ids = _verification_task_ids_from_file(main_plan)
```

This mirrors `sdd-pre-dispatch-hook.sh:297-298` which already has this fallback.

- [x] **Step 4: Run tests — expect PASS**

```bash
.venv/bin/python3 -m pytest tests/unit/test_transition_module.py -v
```

- [x] **Step 5: Commit**

```bash
git add skills/subagent-driven-development/scripts/transition-module.py \
       tests/unit/test_transition_module.py
git commit -m "fix(N17): fall back to main plan for verification-id lookup when module.file empty"
```

---

### Task 7: N1 — Multi-error accumulation regression test

**Files:**
- Create: `tests/unit/test_n1_multi_error_accumulation.py`

**Pattern References:** `tests/unit/test_sdd_classification.py` — bash hook subprocess test patterns (make_hook_input, setup_manifest_workspace).

This is test-only. No hook edits. No baseline recapture.

- [x] **Step 1: Write the regression test**

Read `tests/unit/test_sdd_classification.py` for the `make_hook_input` and `setup_manifest_workspace` patterns. The test must prove that the hook accumulates multiple errors (via `ERRORS+=()`) and emits ALL of them before exiting, rather than short-circuiting on the first failure.

```python
"""N1: Regression test proving multi-error accumulation in sdd-pre-dispatch-hook.sh.

The hook uses ERRORS=() array and appends via ERRORS+=("...") at each gate check.
At the end (~L702-709), ALL errors are emitted before exit 2. This test drives the
hook with multiple simultaneous violations and asserts all are reported.

Run: .venv/bin/python3 -m pytest tests/unit/test_n1_multi_error_accumulation.py -v
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(ROOT, "skills", "subagent-driven-development", "scripts", "sdd-pre-dispatch-hook.sh")
sys.path.insert(0, os.path.join(ROOT, "tests", "unit"))
from sdd_test_helpers import make_hook_input, setup_manifest_workspace


class TestMultiErrorAccumulation:
    def test_multiple_violations_all_reported(self, tmp_path):
        """Drive the hook with: missing implementer report + missing spec review
        + missing quality review for the previous task. Assert the output contains
        all three BLOCKED messages, not just the first one."""
        ws = setup_manifest_workspace(tmp_path, tier="standard", task_range=(1, 3), total_tasks=3)
        reports = ws["reports_dir"]
        log = reports / ".dispatch-log"
        log.write_text("# sdd-hook-sentinel\n")

        # Task 1 artifacts: NONE present (missing impl report, spec, quality)
        # Pre-execution audit must exist to avoid that separate early gate
        (reports / "pre-execution-audit.md").write_text("x" * 80)
        (reports / "checkpoint-pre-dispatch-002.json").write_text(
            json.dumps({"status": "PASS", "detail": "x" * 60})
        )
        (reports / "partner-review-002.md").write_text("x" * 80)

        hook_input = make_hook_input(
            description="Implement task 2",
            prompt="implement task 2",
            cwd=str(tmp_path),
        )
        result = subprocess.run(
            ["bash", HOOK],
            input=hook_input,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
        )
        output = result.stderr + result.stdout
        # All three missing-artifact messages should appear, not just the first
        assert "implementer report" in output.lower() or "task-001-implementer" in output
        assert "spec review" in output.lower() or "spec-review" in output
        assert "quality review" in output.lower() or "quality-review" in output
        assert result.returncode == 2
```

- [x] **Step 2: Run test — expect PASS**

This test should already PASS on the current hook (it already accumulates errors). This is a regression guard, not a bug fix.

```bash
.venv/bin/python3 -m pytest tests/unit/test_n1_multi_error_accumulation.py -v
```

Expected: PASS (hook already accumulates).

- [x] **Step 3: Verify no hook files touched**

```bash
git diff --name-only | grep -c "\.sh$"  # should be 0
```

- [x] **Step 4: Commit**

```bash
git add tests/unit/test_n1_multi_error_accumulation.py
git commit -m "test(N1): regression test for multi-error accumulation in sdd-pre-dispatch-hook"
```
