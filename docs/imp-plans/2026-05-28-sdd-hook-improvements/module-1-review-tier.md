---
schema_version: 1
feature_archetype: extension
enforcement_tier: standard
source_contracts: null
shared_constants: []
pattern_references:
  - name: "review-tier-counter"
    source_files: ["skills/subagent-driven-development/scripts/controller-checkpoint.py"]
    reason: "_count_review_tiers + Check 7 ratio block is the code Task 3 refactors"
tasks:
  - id: 1
    title: "Add review_tier field to Task model"
  - id: 2
    title: "validate-plan.py review_tier heuristic warning"
    depends_on: [1]
  - id: 3
    title: "controller-checkpoint.py declared-minimum ratio exclusion"
    depends_on: [1]
  - id: 4
    title: "writing-plans SKILL.md review_tier decision table"
---

# Module 1 — Per-task `review_tier` declaration

> **For agentic workers:** Invoke `superpowers:subagent-driven-development` before implementing. This module is part of the SDD Hook Improvements feature; see `plan.md` for the parent.

**Goal:** Add an optional per-task `review_tier: minimum|full` field to the plan schema (Item 4a), warn on suspicious uses (Item 4c), exclude declared-minimum tasks from the pre-completion minimum-tier ratio denominator for both quality AND partner reviews (Item 4b), and document the decision criteria for plan authors (Item 4d).

**Source Contracts:** None

Internal models/scripts only.

**Contract Constraints:**
- `review_tier: Literal["minimum", "full"] = "full"`. Optional. `StrictModel` (`extra="forbid"`) — use the default value, not `Optional`/`None`.
- Do **NOT** bump `CURRENT_SCHEMA_VERSION` (adding an optional field with a default is non-breaking).
- `review_tier` is orthogonal to `enforcement_tier`.
- Ratio threshold stays at 50%; only the denominator changes (exclude declared-minimum from numerator AND denominator).
- Apply the exclusion symmetrically to BOTH the quality-review and partner-review ratio checks.
- Zero-denominator guard: filtered denominator 0 → PASS (mirror the existing `if total > 0`).
- Plan-parse failure → empty exclusion set + WARNING (preserve current behavior).
- validate-plan heuristic: warn on `review_tier: minimum` + title keywords `refactor|service|security|business logic|auth`; warn on `migration` ONLY when co-occurring with `backfill|UPDATE|DELETE|transform|data`; never warn on `migration` alone.

**Feature Archetype:** Extension.

## Code Footprint

| Category | File / Function | Action |
|----------|-----------------|--------|
| Modified | `skills/scripts/models/plan.py` — `Task` | Add `review_tier` field |
| Modified | `skills/subagent-driven-development/scripts/validate-plan.py` | Add `check_review_tier_heuristic` + wire into `validate_plan` |
| Modified | `skills/subagent-driven-development/scripts/controller-checkpoint.py` | Refactor `_count_review_tiers` → per-task; add declared-minimum exclusion in `run_pre_completion` |
| Modified | `skills/writing-plans/SKILL.md` | Add decision table after Task Structure (~line 360) |
| Modified | `tests/unit/test_models/test_plan_model.py` | review_tier model tests |
| Modified | `tests/unit/test_validate_plan.py` | heuristic tests |
| Modified | `tests/unit/test_pre_completion_gates.py` | filtered-ratio tests |

## Write-Scope Partitioning

| Task | Owned Files (write) | Read-Only | Depends On |
|------|---------------------|-----------|------------|
| 1 | `skills/scripts/models/plan.py`, `tests/unit/test_models/test_plan_model.py` | — | — |
| 2 | `skills/subagent-driven-development/scripts/validate-plan.py`, `tests/unit/test_validate_plan.py` | `plan.py` | 1 |
| 3 | `skills/subagent-driven-development/scripts/controller-checkpoint.py`, `tests/unit/test_pre_completion_gates.py` | `plan.py`, `sdd_session.py` | 1 |
| 4 | `skills/writing-plans/SKILL.md` | — | — |

Tasks 2 and 3 are parallel candidates after Task 1. Task 4 is independent.

---

### Task 1: Add `review_tier` field to the `Task` model

**Files:**
- Modify: `skills/scripts/models/plan.py:24-30` (the `Task` class)
- Test: `tests/unit/test_models/test_plan_model.py`

Run all pytest commands from the repo root with: `.venv/bin/python3 -m pytest <path> -v`

- [x] **Step 1: Write the failing tests**

Add to `tests/unit/test_models/test_plan_model.py` (the file already imports `Plan`, `Task`, `MINIMAL_PLAN`, `CURRENT_SCHEMA_VERSION`):

```python
class TestReviewTier:
    def test_review_tier_defaults_to_full(self):
        task = Task(id=1, title="x")
        assert task.review_tier == "full"

    def test_review_tier_accepts_minimum(self):
        task = Task(id=1, title="x", review_tier="minimum")
        assert task.review_tier == "minimum"

    def test_review_tier_rejects_other_values(self):
        with pytest.raises(ValidationError) as exc:
            Task(id=1, title="x", review_tier="medium")
        assert exc.value.errors()[0]["type"] == "literal_error"

    def test_plan_with_review_tier_parses(self):
        data = {
            "schema_version": CURRENT_SCHEMA_VERSION,
            "feature_archetype": "extension",
            "tasks": [
                {"id": 0, "title": "Setup"},
                {"id": 1, "title": "DDL", "review_tier": "minimum"},
            ],
        }
        plan = Plan.model_validate(data)
        assert plan.tasks[0].review_tier == "full"   # default
        assert plan.tasks[1].review_tier == "minimum"

    def test_schema_version_unchanged(self):
        """Adding review_tier is non-breaking — schema version must NOT change."""
        assert CURRENT_SCHEMA_VERSION == 1
```

- [x] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python3 -m pytest tests/unit/test_models/test_plan_model.py::TestReviewTier -v`
Expected: FAIL — `Task` has no `review_tier` (the first three fail on extra_forbidden / AttributeError, `test_plan_with_review_tier_parses` fails on `extra_forbidden`).

- [x] **Step 3: Add the field**

In `skills/scripts/models/plan.py`, add `review_tier` to the `Task` class. The module already imports `Literal` from `typing`:

```python
class Task(StrictModel):
    id: int
    title: str
    module_id: int | None = None
    depends_on: list[int] = Field(default_factory=list)
    pattern_references: list[str] = Field(default_factory=list)
    shared_constants_used: list[str] = Field(default_factory=list)
    review_tier: Literal["minimum", "full"] = "full"
```

Do NOT modify `_base.py` or `CURRENT_SCHEMA_VERSION`.

- [x] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python3 -m pytest tests/unit/test_models/test_plan_model.py -v`
Expected: PASS (new `TestReviewTier` class + all pre-existing tests still green).

- [x] **Step 5: Commit**

```bash
git add skills/scripts/models/plan.py tests/unit/test_models/test_plan_model.py
git commit -m "feat(plan-model): add optional per-task review_tier field"
```

---

### Task 2: `validate-plan.py` review_tier heuristic warning

**Files:**
- Modify: `skills/subagent-driven-development/scripts/validate-plan.py` (add a function near the other check helpers ~line 330; call it inside `validate_plan` near the enforcement-tier block ~line 553)
- Test: `tests/unit/test_validate_plan.py`

**Pattern References:** the enforcement-tier appropriateness block in `validate-plan.py:531-563` shows the exact "read `frontmatter` dict → append to `warnings` + `sections[...]`" idiom to follow.

- [x] **Step 1: Write the failing tests**

Add to `tests/unit/test_validate_plan.py`. Tests invoke `validate-plan.py` as a subprocess and parse JSON. Reuse the file's existing helper if present; otherwise use this self-contained pattern:

```python
import json, os, subprocess, sys, tempfile

VALIDATE_PLAN = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..",
    "skills", "subagent-driven-development", "scripts", "validate-plan.py",
))

def _run_validate(plan_text: str) -> dict:
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as fh:
        fh.write(plan_text)
        path = fh.name
    try:
        r = subprocess.run([sys.executable, VALIDATE_PLAN, "--plan-file", path],
                           capture_output=True, text=True, timeout=15)
        return {"exit": r.returncode, "json": json.loads(r.stdout) if r.stdout.strip() else {}}
    finally:
        os.unlink(path)

def _plan(tasks_yaml: str, body_tasks: str) -> str:
    return (
        "---\n"
        "schema_version: 1\n"
        "feature_archetype: extension\n"
        f"{tasks_yaml}"
        "---\n\n"
        "# Plan\n\n"
        "**Source Contracts:** None\n"
        "**Contract Constraints:** None\n"
        "**Feature Archetype:** Extension\n"
        "## Code Footprint\n\n"
        "## Write-Scope Partitioning\n\n"
        f"{body_tasks}"
    )

class TestReviewTierHeuristic:
    def test_warns_minimum_on_refactor_title(self):
        tasks_yaml = (
            "tasks:\n"
            "  - id: 0\n    title: 'Refactor balance service'\n    review_tier: minimum\n"
        )
        body = "### Task 0 -- Refactor balance service\n- [ ] do\n"
        out = _run_validate(_plan(tasks_yaml, body))
        warns = " ".join(out["json"].get("warnings", []))
        assert "review_tier" in warns.lower()

    def test_no_warn_minimum_on_ddl_title(self):
        tasks_yaml = (
            "tasks:\n"
            "  - id: 0\n    title: 'Create table accounts (DDL)'\n    review_tier: minimum\n"
        )
        body = "### Task 0 -- Create table accounts\n- [ ] do\n"
        out = _run_validate(_plan(tasks_yaml, body))
        warns = " ".join(out["json"].get("warnings", []))
        assert "review_tier" not in warns.lower()

    def test_no_warn_migration_alone(self):
        tasks_yaml = (
            "tasks:\n"
            "  - id: 0\n    title: 'Add migration for new column'\n    review_tier: minimum\n"
        )
        body = "### Task 0 -- Add migration\n- [ ] do\n"
        out = _run_validate(_plan(tasks_yaml, body))
        warns = " ".join(out["json"].get("warnings", []))
        assert "review_tier" not in warns.lower()

    def test_warns_migration_with_backfill(self):
        tasks_yaml = (
            "tasks:\n"
            "  - id: 0\n    title: 'Migration with backfill of balances'\n    review_tier: minimum\n"
        )
        body = "### Task 0 -- Migration with backfill\n- [ ] do\n"
        out = _run_validate(_plan(tasks_yaml, body))
        warns = " ".join(out["json"].get("warnings", []))
        assert "review_tier" in warns.lower()

    def test_full_tier_never_warns(self):
        tasks_yaml = (
            "tasks:\n"
            "  - id: 0\n    title: 'Refactor security auth service'\n    review_tier: full\n"
        )
        body = "### Task 0 -- Refactor security auth service\n- [ ] do\n"
        out = _run_validate(_plan(tasks_yaml, body))
        warns = " ".join(out["json"].get("warnings", []))
        assert "review_tier" not in warns.lower()
```

- [x] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python3 -m pytest tests/unit/test_validate_plan.py::TestReviewTierHeuristic -v`
Expected: FAIL — no heuristic yet, so the "warns" assertions fail.

- [x] **Step 3: Implement the heuristic**

Add this function to `validate-plan.py` (place near the other module-level helpers, e.g. after `source_contracts_non_none` ~line 325):

```python
# Titles matching these always warrant a full review.
_ALWAYS_FULL_KEYWORDS = ("refactor", "service", "security", "business logic", "auth")
# "migration" only warrants full review when paired with data-manipulation terms.
_MIGRATION_DATA_KEYWORDS = ("backfill", "update", "delete", "transform", "data")


def check_review_tier_heuristic(frontmatter: Optional[Dict]) -> List[str]:
    """Return warning strings for tasks declaring review_tier=minimum on high-risk titles."""
    warnings: List[str] = []
    if not isinstance(frontmatter, dict):
        return warnings
    tasks = frontmatter.get("tasks")
    if not isinstance(tasks, list):
        return warnings
    for task in tasks:
        if not isinstance(task, dict):
            continue
        if task.get("review_tier") != "minimum":
            continue
        title = str(task.get("title", "")).lower()
        tid = task.get("id")
        suspicious = any(kw in title for kw in _ALWAYS_FULL_KEYWORDS)
        if not suspicious and "migration" in title:
            suspicious = any(kw in title for kw in _MIGRATION_DATA_KEYWORDS)
        if suspicious:
            warnings.append(
                "review_tier_minimum_on_high_risk_task: Task {} ('{}') declares "
                "review_tier: minimum but its title suggests full review is warranted. "
                "Confirm this is genuinely mechanical.".format(tid, task.get("title", ""))
            )
    return warnings
```

Wire it into `validate_plan` right after the enforcement-tier appropriateness block (after line 563, still inside `if frontmatter and isinstance(frontmatter, dict):` scope is fine, or just after that block at module-dict level):

```python
    # --- review_tier heuristic (Item 4c) ---
    rt_warnings = check_review_tier_heuristic(frontmatter)
    for w in rt_warnings:
        warnings.append(w)
    if rt_warnings:
        sections["review_tier_heuristic"] = {
            "status": "WARNING",
            "detail": " | ".join(rt_warnings),
        }
```

This appends human-readable strings to `warnings` (so the test's substring check on `warnings` passes) and surfaces a `sections` entry. Status becomes WARNING (exit 2) when only these warnings exist — acceptable; the plan author resolves or accepts them.

- [x] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python3 -m pytest tests/unit/test_validate_plan.py -v`
Expected: PASS (new class + all existing tests).

- [x] **Step 5: Commit**

```bash
git add skills/subagent-driven-development/scripts/validate-plan.py tests/unit/test_validate_plan.py
git commit -m "feat(validate-plan): warn on review_tier:minimum for high-risk task titles"
```

---

### Task 3: `controller-checkpoint.py` declared-minimum ratio exclusion

**Files:**
- Modify: `skills/subagent-driven-development/scripts/controller-checkpoint.py` — refactor `_count_review_tiers` (lines 188-212), update the ratio block in `run_pre_completion` (lines 1054-1098)
- Test: `tests/unit/test_pre_completion_gates.py`

**Pattern References:** `test_pre_completion_gates.py` helpers `run_pre_completion`, `_make_reports_with_minimum_tier` (lines 98-191) — extend these.

> **Task size note (accepted deviation):** this task runs ~220 plan-lines, over the advisory 200-line guideline (`validate-plan.py` WARNING, which does **not** block the plan-validation gate — only FAILs do). It is a single atomic refactor: renaming `_count_review_tiers` → `_review_tiers_per_task` breaks its two callers immediately, so the function change, the new declared-minimum helpers, the ratio rewrite, and their tests must land together — splitting would create a broken intermediate. The multi-file test was added per plan review and is reviewer-required coverage. Logged here per the "satisfy structurally where sensible + record the rationale" rule for advisory gate warnings.

**Context for the implementer:** `run_pre_completion` already reads `all_plan_contents = [plan_content] + additional_plan_files` (lines 888-896) and accepts `--manifest`. The current ratio block counts *every* minimum-tier review file against the total. The new logic must exclude tasks the plan *declared* as `review_tier: minimum` from both numerator and denominator. For modular plans, declared-minimum task IDs must be gathered from ALL module plan files.

- [ ] **Step 1: Write the failing tests**

Add to `tests/unit/test_pre_completion_gates.py`. `_make_reports_with_minimum_tier(task_count, quality_minimum_tasks, partner_minimum_tasks)` and `run_pre_completion(plan_content, report_files=...)` already exist. Add a frontmatter-builder and the tests:

```python
def _plan_with_review_tiers(task_count: int, minimum_task_ids: list[int]) -> str:
    """Plan markdown with YAML frontmatter declaring review_tier per task."""
    lines = ["---", "schema_version: 1", "feature_archetype: extension", "tasks:"]
    for n in range(task_count):
        lines.append(f"  - id: {n}")
        lines.append(f"    title: 'Task {n}'")
        if n in minimum_task_ids:
            lines.append("    review_tier: minimum")
    lines.append("---")
    lines.append("")
    for n in range(task_count):
        lines.append(f"### Task {n} -- Task {n}")
        lines.append("- [x] done")
    return "\n".join(lines) + "\n"


class TestDeclaredMinimumExclusion:
    # (declared_min, quality_min, partner_min, expect_quality_block, expect_partner_block)
    # Other blockers (honesty/trace) don't affect these specific ratio assertions.
    @pytest.mark.parametrize("declared,q_min,p_min,q_block,p_block", [
        ([0, 1, 2],    [0, 1, 2],    [],           False, False),  # declared-min quality excluded -> PASS
        ([],           [0, 1, 2],    [],           True,  False),  # undeclared 3/4 min -> block
        ([0, 1, 2],    [],           [0, 1, 2],    False, False),  # declared-min partner excluded -> PASS
        ([0],          [0, 1, 2],    [],           True,  False),  # 1 excluded; 2/3 remaining min -> block
        ([0, 1, 2, 3], [0, 1, 2, 3], [],           False, False),  # all declared -> zero denom -> PASS
    ])
    def test_declared_minimum_exclusion(self, declared, q_min, p_min, q_block, p_block):
        plan = _plan_with_review_tiers(4, minimum_task_ids=declared)
        reports = _make_reports_with_minimum_tier(
            4, quality_minimum_tasks=q_min, partner_minimum_tasks=p_min)
        blockers = run_pre_completion(plan, report_files=reports)["output"].get("blockers", [])
        assert ("excessive_minimum_tier_quality" in blockers) == q_block
        assert ("excessive_minimum_tier_partner" in blockers) == p_block

    def test_unparseable_plan_falls_back(self):
        """No YAML frontmatter -> empty exclusion set -> current behavior (3/4 min -> block)."""
        plan = "# Plan no frontmatter\n### Task 0\n### Task 1\n### Task 2\n### Task 3\n"
        reports = _make_reports_with_minimum_tier(4, quality_minimum_tasks=[0, 1, 2])
        blockers = run_pre_completion(plan, report_files=reports)["output"].get("blockers", [])
        assert "excessive_minimum_tier_quality" in blockers

    def test_declared_minimum_across_module_files(self, tmp_path):
        """Multi-file (acceptance 'all module plan files read'): declared-minimum
        tasks in a SECOND plan file are excluded. Without the cross-file scan,
        3/4 quality reviews are minimum -> block; with it -> PASS. Uses
        --additional-plan-files (same all_plan_contents path Step 3b feeds)."""
        (tmp_path / "plan.md").write_text(_plan_with_review_tiers(4, minimum_task_ids=[]))
        (tmp_path / "mod-b.md").write_text(_plan_with_review_tiers(4, minimum_task_ids=[1, 2, 3]))
        (tmp_path / "DEVIATIONS.md").write_text("")
        rdir = tmp_path / "reports"; rdir.mkdir()
        for name, c in _make_reports_with_minimum_tier(4, quality_minimum_tasks=[1, 2, 3]).items():
            (rdir / name).write_text(c)
        r = subprocess.run([sys.executable, SCRIPT_PATH, "--phase", "pre-completion",
                            "--plan-file", str(tmp_path / "plan.md"),
                            "--additional-plan-files", str(tmp_path / "mod-b.md"),
                            "--deviations-file", str(tmp_path / "DEVIATIONS.md"),
                            "--reports-dir", str(rdir)],
                           capture_output=True, text=True, timeout=10)
        assert r.stdout.strip(), f"checkpoint produced no output: {r.stderr}"  # proves the script ran
        out = json.loads(r.stdout)
        assert "excessive_minimum_tier_quality" not in out.get("blockers", [])
```

(`subprocess`, `sys`, `json`, `SCRIPT_PATH` are already module-level. Step 3b's manifest auto-resolution feeds the same `all_plan_contents` path and is additionally covered by the e2e test in Task 9.)

(Ensure `import pytest` is present at the top of `test_pre_completion_gates.py` for `@pytest.mark.parametrize`.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python3 -m pytest tests/unit/test_pre_completion_gates.py::TestDeclaredMinimumExclusion -v`
Expected: FAIL — declared-minimum is not yet excluded, so `test_declared_minimum_excluded_*` see a blocker that shouldn't be there.

- [ ] **Step 3a: Refactor `_count_review_tiers` to per-task**

Replace the function at lines 188-212 with a per-task version (keep the name's intent; rename to make the per-task contract explicit). Add `import re` is already present (line 39).

```python
def _review_tiers_per_task(reports_dir, review_type):
    # type: (str, str) -> list
    """Return [(task_id:int, is_minimum:bool), ...] for the given review type.

    Recognizes:
      quality-review: task-NNN-quality-review.md / task-NNN-quality-review-minimum-tier.md
      partner-review: partner-review-NNN.md       / partner-review-NNN-minimum-tier.md
    """
    if review_type == "quality-review":
        full_pat = os.path.join(reports_dir, "task-*-quality-review.md")
        min_pat = os.path.join(reports_dir, "task-*-quality-review-minimum-tier.md")
        id_re = re.compile(r"task-(\d+)-quality-review(?:-minimum-tier)?\.md$")
    elif review_type == "partner-review":
        full_pat = os.path.join(reports_dir, "partner-review-*.md")
        min_pat = os.path.join(reports_dir, "partner-review-*-minimum-tier.md")
        id_re = re.compile(r"partner-review-(\d+)(?:-minimum-tier)?\.md$")
    else:
        return []

    min_paths = set(glob.glob(min_pat))
    results = []
    for path in min_paths:
        m = id_re.search(os.path.basename(path))
        if m:
            results.append((int(m.group(1)), True))
    for path in glob.glob(full_pat):  # full glob excludes -minimum-tier.md (.md anchor)
        if path in min_paths:
            continue
        m = id_re.search(os.path.basename(path))
        if m:
            results.append((int(m.group(1)), False))
    return results
```

Add a helper to gather declared-minimum task IDs from plan frontmatter (place near the other helpers). **Parse choice (divergence from spec line 171, intentional):** use raw `yaml.safe_load` on the frontmatter rather than the Pydantic `Plan` model. The `Plan` model is strict (requires `feature_archetype`, sequential IDs, etc.) and would raise on any unrelated validation issue, taking down the ratio check; raw extraction reads only `tasks[].review_tier`/`id` and degrades gracefully to the parse-failure→WARNING fallback. This is the safer, spec-intent-preserving choice.

```python
def _declared_minimum_task_ids(plan_contents):
    # type: (list) -> tuple
    """Collect task IDs declaring review_tier=='minimum' from plan frontmatter.
    Returns (set_of_ids, parsed_any:bool)."""
    import yaml
    declared, parsed_any = set(), False
    for content in plan_contents:
        if not content or not content.startswith("---"):
            continue
        end = content.find("---", 3)
        if end == -1:
            continue
        try:
            fm = yaml.safe_load(content[3:end])
        except Exception:
            continue
        tasks = fm.get("tasks") if isinstance(fm, dict) else None
        if not isinstance(tasks, list):
            continue
        parsed_any = True
        for t in tasks:
            if isinstance(t, dict) and t.get("review_tier") == "minimum" and isinstance(t.get("id"), int):
                declared.add(t["id"])
    return declared, parsed_any
```

- [ ] **Step 3b: Gather module plan contents (modular plans)**

In `run_pre_completion`, after `all_plan_contents` is assembled (line ~896), add module-plan reading when a manifest with `modules` is supplied. The manifest path is `args.manifest` (may be None). Reuse `_resolve_git_root` (line 372):

```python
    # Item 4b: add module plan files (modular plans) to the scan, then collect
    # declared-minimum task IDs from ALL plan contents.
    if getattr(args, "manifest", None):
        try:
            from pathlib import Path as _P
            _mp = _P(args.manifest); _md = json.loads(_mp.read_text(encoding="utf-8"))
            _gr = _resolve_git_root(_mp); _feat = _md.get("paths", {}).get("feature_dir", "")
            for _mod in (_md.get("modules") or []):
                _full = os.path.join(_gr, _feat, _mod.get("file", ""))
                if _mod.get("file") and os.path.isfile(_full):
                    all_plan_contents.append(read_file(_full))
        except Exception:
            pass
    declared_min, _parsed = _declared_minimum_task_ids(all_plan_contents)
    if not _parsed:
        warnings.append("review_tier_plan_parse_skipped")
```

- [ ] **Step 3c: Rewrite the ratio block (lines 1054-1098)**

Replace the ratio block with the filtered version, applied symmetrically to quality and partner:

```python
    # Check 7: Minimum-tier review ratio cap (>50% triggers blocker), with
    # declared-minimum tasks excluded from numerator AND denominator (Item 4b).
    def _ratio_check(review_type, blocker_name, label):
        considered = [(t, m) for (t, m) in _review_tiers_per_task(args.reports_dir, review_type)
                      if t not in declared_min]
        total = len(considered)
        minimum = sum(1 for (_t, m) in considered if m)
        if total > 0 and minimum / total > 0.5:
            checks[blocker_name] = {"status": "FAIL", "detail": (
                f"{minimum}/{total} non-declared {label} reviews are minimum-tier "
                f"({round(100 * minimum / total)}%). Use full reviews for tasks touching "
                "shared files, multi-file changes, or Pattern References. "
                "(Declared review_tier:minimum tasks are excluded.)")}
            blockers.append(blocker_name)
        else:
            checks[blocker_name] = {"status": "PASS", "detail": (
                f"{minimum}/{total} non-declared {label} reviews are minimum-tier"
                if total > 0 else f"No non-declared {label} reviews to ratio")}

    _ratio_check("quality-review", "excessive_minimum_tier_quality", "quality")
    _ratio_check("partner-review", "excessive_minimum_tier_partner", "partner")
```

Remove the old `quality_total, quality_min = _count_review_tiers(...)` / `partner_total, partner_min = ...` lines and the two `if ... > 0.5` blocks they fed. Grep for any remaining `_count_review_tiers(` references and replace/remove them (the function is being renamed).

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python3 -m pytest tests/unit/test_pre_completion_gates.py -v`
Expected: PASS — new `TestDeclaredMinimumExclusion` class plus all pre-existing pre-completion tests (the undeclared-minimum cases still block exactly as before, since with no declarations `declared_min` is empty and behavior is identical).

- [ ] **Step 5: Commit**

```bash
git add skills/subagent-driven-development/scripts/controller-checkpoint.py tests/unit/test_pre_completion_gates.py
git commit -m "feat(checkpoint): exclude declared review_tier:minimum tasks from ratio denominator"
```

---

### Task 4: `writing-plans/SKILL.md` review_tier decision table

**Files:**
- Modify: `skills/writing-plans/SKILL.md` — insert after the Task Structure code block (the `### Task N` template ends ~line 360; insert before `## No Placeholders`)

**Context:** Item 4d. Current file is ~4100 words; this adds ~200, staying well under the 5000-word soft limit. No test (docs only) — verification is a word-count check + the regression suite in Task 8.

- [ ] **Step 1: Verify current word count and insertion point**

Run: `wc -w skills/writing-plans/SKILL.md`
Note the count (must remain < 5000 after the edit). Confirm the `## No Placeholders` header location with: `grep -n "^## No Placeholders" skills/writing-plans/SKILL.md`. Insert the new section immediately before it.

- [ ] **Step 2: Insert the decision table**

Add this section immediately before `## No Placeholders`:

```markdown
## Declaring `review_tier` per Task

Each task may declare `review_tier: minimum` in the plan's YAML frontmatter to signal that a full dispatched review is not warranted. Omit it (or set `full`) by default. This is **orthogonal** to `enforcement_tier` — a `standard` plan can still have individual `review_tier: minimum` tasks. The pre-completion gate excludes declared-minimum tasks from the minimum-tier ratio, so legitimately mechanical work no longer trips the >50% blocker.

**Full review expected (default — omit or set `full`):**

| Signal | Examples |
|--------|----------|
| Changes business logic | Service refactors, calculation changes, state machines |
| Affects data integrity | Migrations with data manipulation, backfills, constraint changes |
| Crosses architectural boundaries | Multi-file changes spanning router → service → model |
| Modifies shared code | Utilities, base classes, shared types |
| Changes API contracts | Endpoint signatures, request/response shapes, error codes |
| Security-sensitive | Auth, input validation, encryption, credentials |
| Has Pattern References or Shared Constants | Must follow existing patterns correctly |

**Minimum-tier appropriate (`review_tier: minimum`):**

| Signal | Examples |
|--------|----------|
| Pure schema DDL | CREATE TABLE, ADD COLUMN, CREATE VIEW (no data manipulation) |
| Configuration | Env vars, settings, feature flags, migration registration |
| Documentation | CLAUDE.md, README, inline doc fixes |
| Test-only | Adding coverage for already-implemented and reviewed code |
| Verification/audit | Grep for orphaned code, run the suite, consistency checks |
| Cosmetic | Type annotations, lint fixes, import reorg, renames |

**Gray zone:** SQL views with business logic → full (SQL encodes rules). Contract-compliance tests (TDD-style) → full (tests are the spec). DDL + a one-line config registration as a single task → minimum is fine.
```

- [ ] **Step 3: Verify word count and regression**

Run: `wc -w skills/writing-plans/SKILL.md` (confirm < 5000)
Run: `.venv/bin/python3 tests/ARaymond-skill-regression/validate-all-skills.py` (confirm writing-plans SKILL.md still passes size/cross-ref checks)
Expected: word count < 5000; regression PASS.

- [ ] **Step 4: Commit**

```bash
git add skills/writing-plans/SKILL.md
git commit -m "docs(writing-plans): add review_tier decision table"
```

## Acceptance Criteria (Module 1)

- [x] `Task.review_tier` defaults to `"full"`, accepts `"minimum"`, rejects others; schema version unchanged
- [x] `validate-plan.py` warns on review_tier:minimum + high-risk titles; not on `migration` alone
- [ ] Pre-completion ratio excludes declared-minimum from numerator AND denominator (quality + partner)
- [ ] Undeclared minimum-tier reviews still block at >50%; modular plans aggregate all module files; parse failure → WARNING fallback
- [ ] `writing-plans/SKILL.md` has the decision table and stays < 5000 words
- [ ] All Module 1 unit tests pass
