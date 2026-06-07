---
schema_version: 1
feature_archetype: extension
enforcement_tier: standard
source_contracts: null
shared_constants: []
pattern_references:
  - name: "checkpoint-tests"
    source_files: ["tests/unit/test_pre_completion_gates.py"]
    reason: "Test patterns for pre-completion checks (Check 8/9)"
  - name: "validate-plan-tests"
    source_files: ["tests/unit/test_validate_plan.py"]
    reason: "Test patterns for validate-plan.py structural checks"
  - name: "model-tests"
    source_files: ["tests/unit/test_models/"]
    reason: "Pydantic model validation test patterns"
tasks:
  - id: 8
    title: "C2: IntegrationTest model + Plan field + path validator"
    pattern_references: ["model-tests"]
  - id: 9
    title: "C2: validate-plan.py risk-surface WARNING"
    depends_on: [8]
    pattern_references: ["validate-plan-tests"]
  - id: 10
    title: "C2: Pre-completion Check 10 integration-test gate"
    depends_on: [9]
    pattern_references: ["checkpoint-tests"]
  - id: 11
    title: "C2: Docs + e2e extension"
    depends_on: [10]
    review_tier: minimum
---

# Module 2: C2 Integration-Test Gate — Implementation Plan

> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` via the Skill tool.

**Goal:** Add a pre-completion gate (Check 10) that verifies declared integration tests exist in the feature's changeset. Plans declare `integration_test: {path: "..."}` and the checkpoint confirms the file exists and was added/modified.

**Source Contracts:** None

**Contract Constraints:** None

**Pattern References:**
- `tests/unit/test_pre_completion_gates.py` — pre-completion check test patterns
- `tests/unit/test_validate_plan.py` — validate-plan structural test patterns
- `tests/unit/test_models/` — Pydantic model test patterns

**Acceptance Criteria:**
- C2 model: `IntegrationTest(path)` with path validator (non-absolute, no `..`, repo-relative). `Plan.integration_test` optional field.
- C2 validate-plan: risk-surface WARNING when `integration_test` absent AND plan content matches risk patterns.
- C2 Check 10: FAILs on missing/unchanged test, PASSes on untracked-new + modified-tracked, sees parent-only declarations in modular plans.
- At least 6 test fixtures across tasks 8-10.
- C2 docs in `writing-plans/SKILL.md`.
- E2e test step added to `sdd-e2e-test.sh`.

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `skills/scripts/models/plan.py` | Modify | Add IntegrationTest model + Plan.integration_test |
| `skills/subagent-driven-development/scripts/validate-plan.py` | Modify | Risk-surface WARNING |
| `skills/subagent-driven-development/scripts/controller-checkpoint.py` | Modify | Check 10 |
| `skills/writing-plans/SKILL.md` | Modify | C2 documentation |
| `tests/integration/sdd-e2e-test.sh` | Modify | C2 e2e step |
| `tests/unit/test_c2_integration_gate.py` | Create | C2 unit tests |

## Write-Scope Partitioning

| Task | Owned Files (write) | Read-Only Files | Depends On |
|------|---------------------|-----------------|------------|
| Task 8 | `plan.py`, `tests/unit/test_c2_integration_gate.py` (model section) | `_base.py` | — |
| Task 9 | `validate-plan.py`, `tests/unit/test_c2_integration_gate.py` (WARNING section) | `plan.py` | Task 8 |
| Task 10 | `controller-checkpoint.py`, `tests/unit/test_c2_integration_gate.py` (Check 10 section) | `plan.py`, `sdd_session.py` | Task 9 |
| Task 11 | `writing-plans/SKILL.md`, `sdd-e2e-test.sh` | — | Task 10 |

Note: Tasks 8, 9, 10 each write to `tests/unit/test_c2_integration_gate.py` but in different test classes (model / WARNING / Check 10). They also write to different source files. Since SDD runs sequentially, the same test file is appended by each task without conflict.

---

### Task 8: C2 — IntegrationTest model + Plan field + path validator

**Files:**
- Modify: `skills/scripts/models/plan.py`
- Create: `tests/unit/test_c2_integration_gate.py` (initial)

**Pattern References:** `tests/unit/test_models/` — Pydantic model test patterns.

- [ ] **Step 1: Write failing tests** in `tests/unit/test_c2_integration_gate.py`

```python
"""C2: Integration-test gate — model, validate-plan WARNING, Check 10.
Run: .venv/bin/python3 -m pytest tests/unit/test_c2_integration_gate.py -v
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills/scripts/models"))


class TestIntegrationTestModel:
    def test_valid_relative_path(self):
        from plan import IntegrationTest
        it = IntegrationTest(path="tests/integration/sdd-e2e-test.sh")
        assert it.path == "tests/integration/sdd-e2e-test.sh"

    def test_absolute_path_rejected(self):
        from plan import IntegrationTest
        with pytest.raises(ValueError, match="absolute"):
            IntegrationTest(path="/absolute/path/test.sh")

    def test_dotdot_path_rejected(self):
        from plan import IntegrationTest
        with pytest.raises(ValueError, match="\\.\\."):
            IntegrationTest(path="tests/../../../etc/passwd")

    def test_plan_integration_test_optional(self):
        from plan import Plan
        p = Plan(
            schema_version=1,
            feature_archetype="extension",
            tasks=[{"id": 1, "title": "T"}],
        )
        assert p.integration_test is None

    def test_plan_integration_test_present(self):
        from plan import Plan
        p = Plan(
            schema_version=1,
            feature_archetype="extension",
            tasks=[{"id": 1, "title": "T"}],
            integration_test={"path": "tests/e2e.sh"},
        )
        assert p.integration_test.path == "tests/e2e.sh"
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
.venv/bin/python3 -m pytest tests/unit/test_c2_integration_gate.py::TestIntegrationTestModel -v
```

Expected: ImportError — `IntegrationTest` doesn't exist yet.

- [ ] **Step 3: Add IntegrationTest model to plan.py**

In `skills/scripts/models/plan.py`, add the model and field:

```python
from pydantic import field_validator

class IntegrationTest(StrictModel):
    path: str

    @field_validator("path")
    @classmethod
    def path_must_be_relative_and_safe(cls, v: str) -> str:
        if os.path.isabs(v):
            raise ValueError(f"integration_test path must not be absolute: {v}")
        if ".." in v.split("/"):
            raise ValueError(f"integration_test path must not contain '..': {v}")
        return v
```

Add `import os` at the top if not already present. Add the field to `Plan`:

```python
class Plan(SchemaVersionedModel):
    # ... existing fields ...
    integration_test: IntegrationTest | None = None
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
.venv/bin/python3 -m pytest tests/unit/test_c2_integration_gate.py::TestIntegrationTestModel -v
.venv/bin/python3 -m pytest tests/unit/test_models/ -v
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/scripts/models/plan.py \
       tests/unit/test_c2_integration_gate.py
git commit -m "feat(C2): add IntegrationTest model + Plan.integration_test field with path validator"
```

---

### Task 9: C2 — validate-plan.py risk-surface WARNING

**Files:**
- Modify: `skills/subagent-driven-development/scripts/validate-plan.py`
- Modify: `tests/unit/test_c2_integration_gate.py` (add WARNING tests)

**Pattern References:** `tests/unit/test_validate_plan.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/unit/test_c2_integration_gate.py`:

```python
SCRIPTS = str(Path(__file__).resolve().parent.parent / "skills/subagent-driven-development/scripts")
sys.path.insert(0, SCRIPTS)

# SELF-HOSTING GUARD: _H avoids plan-validator false match on task headers in fixtures.
_H = "##" + "# Task"

RISK_PLAN = (
    "---\nschema_version: 1\nfeature_archetype: extension\n"
    "tasks:\n  - id: 1\n    title: Add auth middleware\n---\n"
    f"# Plan\n\n**Source Contracts:** None\n\n**Feature Archetype:** Extension\n\n"
    f"{_H} 1: Add auth middleware\n- [ ] Do it\n"
)

SAFE_PLAN_WITH_INTEGRATION = (
    "---\nschema_version: 1\nfeature_archetype: extension\n"
    "integration_test:\n  path: tests/e2e.sh\n"
    "tasks:\n  - id: 1\n    title: Add auth middleware\n---\n"
    f"# Plan\n\n**Source Contracts:** None\n\n**Feature Archetype:** Extension\n\n"
    f"{_H} 1: Add auth middleware\n- [ ] Do it\n"
)


class TestC2RiskSurfaceWarning:
    def test_risk_pattern_no_integration_test_warns(self):
        from validate_plan import validate_plan
        result = validate_plan(RISK_PLAN)
        assert any("integration" in w.lower() or "risk" in w.lower()
                    for w in result["warnings"])

    def test_risk_pattern_with_integration_test_no_warn(self):
        from validate_plan import validate_plan
        result = validate_plan(SAFE_PLAN_WITH_INTEGRATION)
        risk_warns = [w for w in result["warnings"]
                      if "integration" in w.lower() and "risk" in w.lower()]
        assert len(risk_warns) == 0

    def test_no_risk_pattern_no_warn(self):
        no_risk = (
            "---\nschema_version: 1\nfeature_archetype: extension\n"
            "tasks:\n  - id: 1\n    title: Add utility\n---\n"
            f"# Plan\n\n**Source Contracts:** None\n\n**Feature Archetype:** Extension\n\n"
            f"{_H} 1: Add utility\n- [ ] Do it\n"
        )
        from validate_plan import validate_plan
        result = validate_plan(no_risk)
        risk_warns = [w for w in result["warnings"]
                      if "integration" in w.lower() and "risk" in w.lower()]
        assert len(risk_warns) == 0
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
.venv/bin/python3 -m pytest tests/unit/test_c2_integration_gate.py::TestC2RiskSurfaceWarning -v
```

- [ ] **Step 3: Add risk-surface WARNING to validate-plan.py**

In `validate-plan.py`, add after the verification keyword heuristic section:

```python
_C2_RISK_PATTERNS = re.compile(
    r"\b(?:router|routes/|middleware|auth|migration|cache|cors|security)\b",
    re.IGNORECASE,
)


def check_integration_test_risk(content: str, frontmatter: dict | None) -> list[str]:
    """Warn when plan content matches risk-surface patterns but has no integration_test."""
    warnings = []
    has_integration_test = (
        isinstance(frontmatter, dict)
        and frontmatter.get("integration_test") is not None
    )
    if has_integration_test:
        return warnings
    if _C2_RISK_PATTERNS.search(content):
        warnings.append(
            "integration_test_risk_surface: Plan content matches risk-surface patterns "
            "(router/middleware/auth/migration/cache/cors/security) but no "
            "integration_test is declared in frontmatter. Consider adding "
            "integration_test: {path: 'tests/integration/...'} to declare the "
            "integration test that validates this feature."
        )
    return warnings
```

Call it from `validate_plan()` after the verification keyword check, passing `content` and `frontmatter`.

- [ ] **Step 4: Run tests — expect PASS**

```bash
.venv/bin/python3 -m pytest tests/unit/test_c2_integration_gate.py::TestC2RiskSurfaceWarning -v
.venv/bin/python3 -m pytest tests/unit/test_validate_plan.py -v
```

- [ ] **Step 5: Commit**

```bash
git add skills/subagent-driven-development/scripts/validate-plan.py \
       tests/unit/test_c2_integration_gate.py
git commit -m "feat(C2): validate-plan.py risk-surface WARNING when integration_test absent"
```

---

### Task 10: C2 — Pre-completion Check 10 integration-test gate

**Files:**
- Modify: `skills/subagent-driven-development/scripts/controller-checkpoint.py`
- Modify: `tests/unit/test_c2_integration_gate.py` (add Check 10 tests)

**Pattern References:** `tests/unit/test_pre_completion_gates.py` — pre-completion check patterns (Check 8/9).

- [ ] **Step 1: Write failing tests**

Append to `tests/unit/test_c2_integration_gate.py`. Build a `_run_checkpoint` helper (subprocess wrapper for `controller-checkpoint.py --phase pre-completion --manifest ...`) and write 6 tests using a `_H` variable for task headers to avoid plan-validator false match:

```python
import json, os, subprocess

_H10 = "##" + "# Task"
_MICRO = {"tier": "micro", "enforcement": {"context_summary_at": None, "pre_execution_audit": False, "partner_review": False, "dispatch_provenance": False, "checkpoint_files": False}, "process_requirements": {"spec_review_mode": "skip", "quality_review_mode": "skip"}, "task_range": [1,1], "midpoint": 1}

def _plan_str(integration_path=None):
    it = f"\nintegration_test:\n  path: {integration_path}" if integration_path else ""
    return f"---\nschema_version: 1\nfeature_archetype: extension{it}\ntasks:\n  - id: 1\n    title: T\n---\n{_H10} 1: T\n- [x] done\n"

class TestC2Check10:
    def _run(self, tmp_path, plan, manifest, extra_files=None, pre_commit_files=None):
        """Init git, commit plan+manifest, optionally add extra files after commit."""
        # ... setup feat/, reports/, deviations, plan, manifest, git init+add+commit
        # then create extra_files (untracked), run checkpoint, return parsed JSON
        pass  # implementer fills from test_pre_completion_gates.py patterns

    def test_no_declaration_passes(self, tmp_path): ...
    def test_path_missing_fails(self, tmp_path): ...
    def test_untracked_new_passes(self, tmp_path): ...
    def test_exists_but_unchanged_fails(self, tmp_path): ...
    def test_modified_tracked_passes(self, tmp_path): ...
    def test_parent_only_declaration_seen(self, tmp_path): ...
```

6 fixtures: (1) no declaration → PASS/SKIP; (2) declared but missing on disk → FAIL; (3) untracked-new after commit → PASS; (4) pre-committed unchanged → FAIL; (5) tracked then modified → PASS; (6) parent-only declaration in modular plan → the declared path is checked (FAIL if missing). Read `tests/unit/test_pre_completion_gates.py` for the git-init + subprocess pattern. Use `_plan_str()` helper and `_MICRO` manifest base.

- [ ] **Step 2: Run tests — expect FAIL**

```bash
.venv/bin/python3 -m pytest tests/unit/test_c2_integration_gate.py::TestC2Check10 -v
```

Expected: FAIL — `integration_test_present` check key absent.

- [ ] **Step 3: Add helpers `_resolve_base_ref` and `_in_changeset`**

In `controller-checkpoint.py`, add before `run_pre_completion`:

`_resolve_base_ref(git_root) -> str|None`: try `origin/HEAD`, `main`, `master` via `git rev-parse --verify`; return first that resolves, or None. If None, emit an infra-error FAIL (don't crash).

`_in_changeset(path, base_ref, git_root) -> bool`: first compute `merge_base = git merge-base <base_ref> HEAD` to isolate feature changes from base-branch drift. Then union: `git ls-files --others --exclude-standard -- <path>` (untracked) and `git diff --name-only <merge_base> -- <path>` (tracked diff against merge-base, not raw base ref). Returns True if any produces output. If merge-base computation fails (e.g., on default branch where merge-base == HEAD), fall back to untracked + `git diff --name-only HEAD -- <path>` (working-tree only).

- [ ] **Step 4: Implement Check 10 in `run_pre_completion`**

After Check 9 (git reality), add Check 10. Aggregate `integration_test.path` from all `all_plan_contents` frontmatter (YAML parse, same pattern as _task_ids_where). Per path: `is_file()` + `_in_changeset()`. No declaration → PASS (skipped). Any missing/unchanged → FAIL + `integration_test_missing` blocker. Use `_resolve_git_root` (existing) for the git root.

- [ ] **Step 5: Run tests — expect PASS**

```bash
.venv/bin/python3 -m pytest tests/unit/test_c2_integration_gate.py::TestC2Check10 -v
.venv/bin/python3 -m pytest tests/unit/test_pre_completion_gates.py -v
```

- [ ] **Step 6: Commit**

```bash
git add skills/subagent-driven-development/scripts/controller-checkpoint.py \
       tests/unit/test_c2_integration_gate.py
git commit -m "feat(C2): Check 10 pre-completion integration-test gate with changeset verification"
```

---

### Task 11: C2 — Docs + e2e extension

**Files:**
- Modify: `skills/writing-plans/SKILL.md`
- Modify: `tests/integration/sdd-e2e-test.sh`

- [ ] **Step 1: Add C2 documentation to writing-plans/SKILL.md**

In `skills/writing-plans/SKILL.md`, add a section after "Declaring `task_type` per Task" (or before the "No Placeholders" section):

```markdown
## Declaring `integration_test` per Plan

Plans that modify risk-surface code (routers, middleware, auth, migrations, caching, CORS, security) should declare an integration test in the YAML frontmatter:

    integration_test:
      path: tests/integration/my-feature-e2e-test.sh

The path must be repo-root-relative, non-absolute, and contain no `..` segments.

**Pre-completion Check 10** verifies that the declared file: (a) exists on disk, and (b) is part of this feature's changeset (added or modified — both tracked diffs and untracked new files count). Modifying an existing integration test to cover the new feature is acceptable.

When no `integration_test` is declared, `validate-plan.py` emits an advisory WARNING if the plan content matches risk-surface patterns. The WARNING is informational — not all plans need integration tests.
```

Check word count: `wc -w skills/writing-plans/SKILL.md` — must stay under 5000.

- [ ] **Step 2: Add C2 e2e step to sdd-e2e-test.sh**

In `tests/integration/sdd-e2e-test.sh`, add a step that exercises Check 10 with an untracked test file and a parent-only declaration. Read the existing step patterns (steps 9-10 for verification keyword) and follow the same structure.

The step should:
1. Create a plan with `integration_test: {path: ...}`
2. Create an untracked file at that path
3. Run controller-checkpoint.py pre-completion
4. Assert `integration_test_present` check is PASS

- [ ] **Step 3: Run the full test suites**

```bash
.venv/bin/python3 -m pytest tests/unit/ -v
python3 tests/ARaymond-skill-regression/validate-all-skills.py
bash tests/integration/sdd-e2e-test.sh
```

Expected: All suites green.

- [ ] **Step 4: Commit**

```bash
git add skills/writing-plans/SKILL.md \
       tests/integration/sdd-e2e-test.sh
git commit -m "docs(C2): integration_test declaration docs + e2e test step"
```
