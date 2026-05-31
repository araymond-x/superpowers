---
schema_version: 1
feature_archetype: extension
enforcement_tier: standard
source_contracts: "docs/imp-plans/2026-05-31-pipeline-flexibility/spec-distilled.md"
pattern_references:
  - name: "review-tier-model-precedent"
    source_files: ["skills/scripts/models/plan.py"]
    reason: "review_tier field shows how to add optional Literal fields to Task model"
  - name: "review-tier-test-precedent"
    source_files: ["tests/unit/test_models/test_plan_model.py"]
    reason: "TestReviewTier class shows test pattern for new optional Task fields"
  - name: "review-tier-heuristic-precedent"
    source_files: ["skills/subagent-driven-development/scripts/validate-plan.py"]
    reason: "check_review_tier_heuristic shows WARNING pattern for keyword-based checks"
tasks:
  - id: 0
    title: "Plan model: add entry_mode and task_type fields"
    depends_on: []
    pattern_references: ["review-tier-model-precedent", "review-tier-test-precedent"]
  - id: 1
    title: "validate-plan: add verification keyword WARNING"
    depends_on: [0]
    pattern_references: ["review-tier-heuristic-precedent"]
---

# Module 1: Model and Validation

**Goal:** Add `entry_mode` field to Plan model and `task_type` field to Task model, then add a keyword-based WARNING to `validate-plan.py` for verification tasks with write-suggesting titles.

**Source Contracts:** None

**Contract Constraints:**
- `Task` extends `StrictModel` (`extra="forbid"`) — new fields must be explicitly declared
- No schema version bump (optional fields with defaults, precedent: `review_tier`)
- `entry_mode` on Plan: `Literal["brainstorming", "direct"]`, default `"brainstorming"`
- `task_type` on Task: `Literal["implementation", "verification"]`, default `"implementation"`
- WARNING keywords (case-insensitive, word-boundary): `create`, `add`, `implement`, `fix`, `modify`, `write`, `update`, `refactor`, `migrate`, `delete`, `remove`

## Write-Scope Partitioning

| Task / Worker | Owned Files (write) | Read-Only Files | Depends On |
|---------------|---------------------|-----------------|------------|
| Task 0 | `skills/scripts/models/plan.py`, `tests/unit/test_models/test_plan_model.py` | `skills/scripts/models/_base.py`, `skills/scripts/models/sdd_session.py` | — |
| Task 1 | `skills/subagent-driven-development/scripts/validate-plan.py`, `tests/unit/test_validate_plan.py` | `skills/scripts/models/plan.py` | Task 0 |

---

### Task 0: Plan model — add `entry_mode` and `task_type` fields

**Files:**
- Modify: `skills/scripts/models/plan.py`
- Test: `tests/unit/test_models/test_plan_model.py`

**Pattern References:**
- `skills/scripts/models/plan.py:31` — `review_tier: Literal["minimum", "full"] = "full"` on Task
- `tests/unit/test_models/test_plan_model.py:235-264` — `TestReviewTier` class (5 tests for optional Literal field)

- [x] **Step 1: Write failing tests for `entry_mode` on Plan**

Add a `TestEntryMode` class to `tests/unit/test_models/test_plan_model.py`:

```python
class TestEntryMode:
    def test_entry_mode_defaults_to_brainstorming(self):
        plan = Plan.model_validate(MINIMAL_PLAN)
        assert plan.entry_mode == "brainstorming"

    def test_entry_mode_accepts_direct(self):
        data = {**MINIMAL_PLAN, "entry_mode": "direct"}
        plan = Plan.model_validate(data)
        assert plan.entry_mode == "direct"

    def test_entry_mode_rejects_invalid(self):
        data = {**MINIMAL_PLAN, "entry_mode": "handoff"}
        with pytest.raises(ValidationError) as exc:
            Plan.model_validate(data)
        assert exc.value.errors()[0]["type"] == "literal_error"
```

- [x] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python3 -m pytest tests/unit/test_models/test_plan_model.py::TestEntryMode -v`
Expected: FAIL — `entry_mode` field not defined on Plan

- [x] **Step 3: Write failing tests for `task_type` on Task**

Add a `TestTaskType` class to `tests/unit/test_models/test_plan_model.py`:

```python
class TestTaskType:
    def test_task_type_defaults_to_implementation(self):
        task = Task(id=1, title="x")
        assert task.task_type == "implementation"

    def test_task_type_accepts_verification(self):
        task = Task(id=1, title="x", task_type="verification")
        assert task.task_type == "verification"

    def test_task_type_rejects_invalid(self):
        with pytest.raises(ValidationError) as exc:
            Task(id=1, title="x", task_type="audit")
        assert exc.value.errors()[0]["type"] == "literal_error"

    def test_plan_with_task_type_parses(self):
        data = {
            "schema_version": CURRENT_SCHEMA_VERSION,
            "feature_archetype": "extension",
            "tasks": [
                {"id": 0, "title": "Setup"},
                {"id": 1, "title": "Audit orphans", "task_type": "verification"},
            ],
        }
        plan = Plan.model_validate(data)
        assert plan.tasks[0].task_type == "implementation"  # default
        assert plan.tasks[1].task_type == "verification"

    def test_task_type_orthogonal_to_review_tier(self):
        task = Task(id=1, title="x", task_type="verification", review_tier="minimum")
        assert task.task_type == "verification"
        assert task.review_tier == "minimum"

    def test_schema_version_unchanged(self):
        """Adding task_type is non-breaking — schema version must NOT change."""
        assert CURRENT_SCHEMA_VERSION == 1
```

- [x] **Step 4: Run tests to verify they fail**

Run: `.venv/bin/python3 -m pytest tests/unit/test_models/test_plan_model.py::TestTaskType -v`
Expected: FAIL — `task_type` field not defined on Task

- [x] **Step 5: Implement both fields in plan.py**

In `skills/scripts/models/plan.py`, add to the `Plan` class (after `enforcement_tier` field, around line 43):

```python
entry_mode: Literal["brainstorming", "direct"] = "brainstorming"
```

Add to the `Task` class (after `review_tier` field, around line 32):

```python
task_type: Literal["implementation", "verification"] = "implementation"
```

- [x] **Step 6: Run all plan model tests to verify they pass**

Run: `.venv/bin/python3 -m pytest tests/unit/test_models/test_plan_model.py -v`
Expected: ALL PASS (existing + new tests)

- [x] **Step 7: Commit**

```bash
git add skills/scripts/models/plan.py tests/unit/test_models/test_plan_model.py
git commit -m "feat(plan-model): add entry_mode and task_type fields

- entry_mode: Literal['brainstorming', 'direct'] on Plan (default: brainstorming)
- task_type: Literal['implementation', 'verification'] on Task (default: implementation)
- Both optional with defaults, no schema version bump

Prompted by Aaron; Co-Authored by Claude"
```

---

### Task 1: validate-plan — add verification keyword WARNING

**Files:**
- Modify: `skills/subagent-driven-development/scripts/validate-plan.py`
- Test: `tests/unit/test_validate_plan.py`

**Pattern References:**
- `skills/subagent-driven-development/scripts/validate-plan.py:332-361` — `check_review_tier_heuristic()` function and its call site at line 603

- [x] **Step 1: Write failing tests**

Add a `FRONTMATTER_PLAN` fixture near the top of `tests/unit/test_validate_plan.py` (after existing fixtures, around line 68):

```python
FRONTMATTER_PLAN = """\
---
schema_version: 1
feature_archetype: extension
{tasks}
---
# Implementation Plan

**Source Contracts**: None
**Contract Constraints**: None
**Feature Archetype**: Extension

## Code Footprint
- app/services/foo.py (modified)

## Write-Scope Partitioning

| Task | Owned Files | Read-Only | Depends On |
|------|-------------|-----------|------------|
| Task 91 | foo.py | — | — |

### Task 91: Test task

- [x] Step 1: Do something
"""
```

Then add a test class:

```python
class TestVerificationKeywordWarning:
    """Verification tasks with write-suggesting titles get a WARNING."""

    def test_verification_task_with_create_warns(self):
        plan = FRONTMATTER_PLAN.format(
            tasks='tasks:\n  - id: 1\n    title: "Create orphan cleanup script"\n    task_type: verification'
        )
        result = run_validate(plan)
        assert result["exit_code"] == 2  # WARNING
        warnings = result["output"].get("warnings", [])
        assert any("verification_keyword" in w for w in warnings)

    def test_verification_task_with_verify_no_warning(self):
        plan = FRONTMATTER_PLAN.format(
            tasks='tasks:\n  - id: 1\n    title: "Verify orphaned code is removed"\n    task_type: verification'
        )
        result = run_validate(plan)
        warnings = result["output"].get("warnings", [])
        assert not any("verification_keyword" in w for w in warnings)

    def test_implementation_task_with_create_no_warning(self):
        plan = FRONTMATTER_PLAN.format(
            tasks='tasks:\n  - id: 1\n    title: "Create new service"'
        )
        result = run_validate(plan)
        warnings = result["output"].get("warnings", [])
        assert not any("verification_keyword" in w for w in warnings)

    def test_verification_task_default_type_no_warning(self):
        """Default task_type is implementation — no keyword check triggered."""
        plan = FRONTMATTER_PLAN.format(
            tasks='tasks:\n  - id: 1\n    title: "Create new service"'
        )
        result = run_validate(plan)
        warnings = result["output"].get("warnings", [])
        assert not any("verification_keyword" in w for w in warnings)

    def test_multiple_keywords_all_reported(self):
        plan = FRONTMATTER_PLAN.format(
            tasks='tasks:\n  - id: 1\n    title: "Create and update config"\n    task_type: verification'
        )
        result = run_validate(plan)
        warnings = result["output"].get("warnings", [])
        kw_warnings = [w for w in warnings if "verification_keyword" in w]
        assert len(kw_warnings) == 1
        assert "create" in kw_warnings[0].lower()
        assert "update" in kw_warnings[0].lower()
```

> **Prerequisite (pre-execution audit, Order 2):** Task 1 has `depends_on: [0]` and
> MUST run only after Task 0 is committed. The `FRONTMATTER_PLAN` fixture carries
> `task_type: verification`; that field exists on the `Task` model only after Task 0.
> If you run these tests before Task 0 lands, `validate-plan.py` FAILs with a Pydantic
> `task_type: Extra inputs are not permitted` blocker (exit 1) — a misleading RED that
> is NOT the heuristic. With Task 0 present, the correct RED is: the heuristic does not
> yet exist, so no `verification_keyword` warning is produced and `assert exit_code == 2`
> / `any("verification_keyword" in w ...)` fail as intended.

- [x] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python3 -m pytest tests/unit/test_validate_plan.py::TestVerificationKeywordWarning -v`
Expected (with Task 0 committed): FAIL — heuristic not implemented, so no `verification_keyword` warning is emitted and the assertions fail. (If you see a Pydantic `extra inputs` error instead, Task 0 has not been applied — stop and apply Task 0 first.)

- [x] **Step 3: Implement `check_verification_keyword_heuristic()`**

Add to `skills/subagent-driven-development/scripts/validate-plan.py` after `check_review_tier_heuristic()` (around line 361):

```python
_VERIFICATION_WRITE_KEYWORDS = (
    "create", "add", "implement", "fix", "modify",
    "write", "update", "refactor", "migrate", "delete", "remove",
)

_VERIFICATION_KEYWORD_RE = re.compile(
    r"\b(?:{})\b".format("|".join(_VERIFICATION_WRITE_KEYWORDS)),
    re.IGNORECASE,
)


def check_verification_keyword_heuristic(frontmatter: Optional[Dict]) -> List[str]:
    """Return warning strings for verification tasks whose titles contain write-suggesting keywords."""
    warnings: List[str] = []
    if not isinstance(frontmatter, dict):
        return warnings
    tasks = frontmatter.get("tasks")
    if not isinstance(tasks, list):
        return warnings
    for task in tasks:
        if not isinstance(task, dict):
            continue
        if task.get("task_type") != "verification":
            continue
        title = str(task.get("title", ""))
        tid = task.get("id")
        matched = _VERIFICATION_KEYWORD_RE.findall(title)
        if matched:
            warnings.append(
                "verification_keyword_warning: Task {} ('{}') is task_type: verification "
                "but its title contains write-suggesting keyword(s): {}. "
                "Verification tasks must not modify files. "
                "If this task modifies files, change it to task_type: implementation.".format(
                    tid, task.get("title", ""), ", ".join(matched)
                )
            )
    return warnings
```

Then call it in `validate_plan()` after the `review_tier` heuristic block (around line 610):

```python
    # --- verification keyword heuristic ---
    vk_warnings = check_verification_keyword_heuristic(frontmatter)
    for w in vk_warnings:
        warnings.append(w)
    if vk_warnings:
        sections["verification_keyword_heuristic"] = {
            "status": "WARNING",
            "detail": " | ".join(vk_warnings),
        }
```

- [x] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python3 -m pytest tests/unit/test_validate_plan.py::TestVerificationKeywordWarning -v`
Expected: ALL PASS

- [x] **Step 5: Run full validate-plan test suite**

Run: `.venv/bin/python3 -m pytest tests/unit/test_validate_plan.py -v`
Expected: ALL PASS (existing + new)

- [x] **Step 6: Commit**

```bash
git add skills/subagent-driven-development/scripts/validate-plan.py tests/unit/test_validate_plan.py
git commit -m "feat(validate-plan): add verification keyword WARNING

Warn when verification task titles contain write-suggesting keywords
(create, add, implement, fix, modify, write, update, refactor, etc.).
WARNING not FAIL — edge cases exist.

Prompted by Aaron; Co-Authored by Claude"
```

## Module 1 Acceptance Criteria

- [x] `entry_mode` field accepts `"brainstorming"` and `"direct"`, defaults to `"brainstorming"`
- [x] `task_type` field accepts `"implementation"` and `"verification"`, defaults to `"implementation"`
- [x] Both fields are optional with defaults — backwards-compatible, no schema version bump
- [x] `validate-plan.py` emits WARNING for verification task titles with write-suggesting keywords
- [x] Implementation tasks with write keywords do NOT trigger warning
- [x] All existing model and validate-plan tests pass
