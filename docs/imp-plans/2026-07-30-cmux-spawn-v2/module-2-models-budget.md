---
schema_version: 1
feature_archetype: extension
enforcement_tier: standard
entry_mode: brainstorming
source_contracts: "docs/imp-plans/2026-07-30-cmux-spawn-v2/spec-distilled.md"
tasks:
  - id: 4
    title: "plan.py: handoff_spawn field"
  - id: 5
    title: "sdd_session.py: optional handoff block"
    depends_on: [4]
  - id: 6
    title: "_handoff_support.py: expected_hops formula + derivation precedence; materialize-manifest.py writes the handoff block"
    depends_on: [5]
  - id: 7
    title: "_handoff_support.py: tasks_done counting + stall streak + CLI"
    depends_on: [6]
---

# cmux-spawn-v2 — Module 2: Models + hop-budget support layer

> **Parent plan:** `docs/imp-plans/2026-07-30-cmux-spawn-v2/plan.md`
> **Module:** 2 of 4
> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first — direct implementation bypasses review enforcement, quality gates, and hooks.

**Module Goal:** Land every data-layer change BEFORE anything consumes it: the `handoff_spawn` plan field, the manifest `handoff` block, and `_handoff_support.py` — the single source of truth for the Decision 9 formula, the derivation precedence, `tasks_done` counting, and stall streaks. `materialize-manifest.py` starts writing the block. No schema-version bump anywhere.

**Source Contracts:** None

_External contracts were frozen into fixtures by Module 1's Task 0 (repo convention: the mechanical Task-0 gate resolves against the module that owns Task 0). The binding facts this module consumes — spec-distilled Contract Facts (Plan model, Manifest, `expected_hops` formula, `tasks_done` counting), `skills/scripts/models/implementer_report.py` statuses, and the parent plan's Shared Contract Section items 2 and 4 — are restated under Contract Constraints below._

**Contract Constraints:** `Plan` and `SddSession` are `extra="forbid"` — new fields must be optional with defaults so every existing plan/manifest still validates; `CURRENT_SCHEMA_VERSION` stays 1. `expected_hops = ceil(total_tasks / 2.5)` standard, `1` micro. Derivation precedence: validated manifest total → union of module task IDs → inclusive `task_range`; invalid/zero → `None` (absent-with-warning). `tasks_done`: unique task IDs whose implementer-report frontmatter parses AND has status `DONE`/`DONE_WITH_CONCERNS` (verification reports count under the same statuses — their `files_changed` may be empty); filenames alone never count; scans `reports/` AND `archive-*/`. **Python 3.9 scan asymmetry (deferred order B7):** `check_python39_compat` flat-globs `skills/subagent-driven-development/scripts/*.py` ONLY — so `_handoff_support.py` (Tasks 6-7) must use no PEP-604 unions and no builtin generics in annotations (`Optional[X]` / `Dict[str, int]`, not `X | None` / `dict[str, int]`), while `skills/scripts/models/` is NOT scanned and Task 5's `Handoff | None` is correct there. Do not "harmonize" the two directories.

## File Map

| File | Responsibility |
|------|----------------|
| `skills/scripts/models/plan.py` | + `handoff_spawn` field |
| `skills/scripts/models/sdd_session.py` | + `Handoff` model, `SddSession.handoff` |
| `skills/subagent-driven-development/scripts/_handoff_support.py` | NEW — formula/precedence/tasks_done/stall SSOT + CLI |
| `skills/subagent-driven-development/scripts/materialize-manifest.py` | writes the `handoff` block |
| `tests/unit/test_models/test_plan_model.py`, `test_sdd_session_model.py` | model tests |
| `tests/unit/test_handoff_support.py` | NEW — support-module + CLI tests |
| `tests/unit/test_materialize_manifest.py` | handoff-block materialization tests |

## Write-Scope Partitioning

| Task | Owned Files (write) | Read-Only Files | Depends On |
|------|---------------------|-----------------|------------|
| Task 4 | `plan.py`, `test_plan_model.py` | — | Task 0 |
| Task 5 | `sdd_session.py`, `test_sdd_session_model.py` | plan.py | Task 4 |
| Task 6 | `_handoff_support.py`, `materialize-manifest.py`, `test_handoff_support.py`, `test_materialize_manifest.py` | sdd_session.py | Task 5 |
| Task 7 | `_handoff_support.py`, `test_handoff_support.py` | implementer_report.py | Task 6 |

Tasks 6 and 7 both write `_handoff_support.py` — strictly serialized.

## Shared test helpers (module-level in `tests/unit/test_handoff_support.py`; added when Task 6 creates the file, consumed by Task 7's tests)

```python
import subprocess

VENV_PY = str(Path(__file__).resolve().parent.parent.parent / ".venv" / "bin" / "python3")
SUPPORT = str(SCRIPTS / "_handoff_support.py")


def _write_report(d, task_id, status, task_type="implementation", name=None):
    d.mkdir(parents=True, exist_ok=True)
    body = (f"---\nschema_version: 1\ntask_id: {task_id}\nstatus: {status}\n"
            f"task_type: {task_type}\nfiles_changed: []\n"
            "tests: {written: 0, passing: 0, command: x, result: PASS}\n---\nbody\n")
    (d / (name or f"task-{task_id:03d}-implementer-report.md")).write_text(body)


def _log(lines):
    return "".join(l + "\n" for l in lines)
```

### Task 4: plan.py — handoff_spawn field

**Files:**
- Modify: `skills/scripts/models/plan.py`
- Test: `tests/unit/test_models/test_plan_model.py`

- [x] **Step 1: Write the failing tests** (append a class, following the file's `test_entry_mode_*` style): _Note: shipped with a FIFTH test, `test_literal_is_closed_set`, added by the fix round — the four below never pinned the Literal as a closed set. Construction uses the file's real `MINIMAL_PLAN` idiom; `_minimal_plan()` below is hypothetical and does not exist._

```python
class TestHandoffSpawn:
    def test_defaults_to_auto(self):
        plan = _minimal_plan()          # use the file's existing minimal-plan helper/idiom
        assert plan.handoff_spawn == "auto"

    def test_accepts_ask_and_off(self):
        for v in ("ask", "off"):
            plan = _minimal_plan(handoff_spawn=v)
            assert plan.handoff_spawn == v

    def test_rejects_invalid_value(self):
        with pytest.raises(ValidationError):
            _minimal_plan(handoff_spawn="prompt")

    def test_schema_version_not_bumped(self):
        from _base import CURRENT_SCHEMA_VERSION
        assert CURRENT_SCHEMA_VERSION == 1
```

If the file has no reusable minimal-plan helper, construct inline exactly as its existing tests do (`Plan(schema_version=1, feature_archetype="greenfield", tasks=[...])`).

- [x] **Step 2: Run to verify failure** — `.venv/bin/python3 -m pytest tests/unit/test_models/test_plan_model.py -k HandoffSpawn -v` — expect FAIL: unexpected keyword / extra field forbidden.

- [x] **Step 3: Implement** — in `class Plan`, directly under `entry_mode`:

```python
    handoff_spawn: Literal["auto", "ask", "off"] = "auto"
```

- [x] **Step 4: Run tests** — the class passes; then the whole file: `.venv/bin/python3 -m pytest tests/unit/test_models/ -v` — all PASS.

- [x] **Step 5: Commit** — landed as `ab1ffd2`; a `[task 4 fix]` round added `test_literal_is_closed_set` in `fe2437e` (see deviations)

```bash
git add skills/scripts/models/plan.py tests/unit/test_models/test_plan_model.py
git commit -m "feat(cmux-spawn-v2): plan.py handoff_spawn consent field (no schema bump)"
```

### Task 5: sdd_session.py — optional handoff block

**Files:**
- Modify: `skills/scripts/models/sdd_session.py`
- Test: `tests/unit/test_models/test_sdd_session_model.py`

- [ ] **Step 1: Write the failing tests.** `_minimal_session()` **DOES NOT EXIST** — verified, see the note below. Use the file's real idiom: the module-level `MINIMAL_SESSION` dict spread into `SddSession.model_validate({**MINIMAL_SESSION, ...})`, exactly as `TestSddSessionGoldenInput` does. Add `Handoff` to the existing `from sdd_session import (...)` block.

```python
class TestHandoffBlock:
    def test_absent_handoff_still_validates(self):
        s = SddSession.model_validate(MINIMAL_SESSION)
        assert s.handoff is None

    def test_handoff_block_validates(self):
        s = SddSession.model_validate({**MINIMAL_SESSION,
                                       "handoff": {"expected_hops": 5, "spawn_policy": "ask"}})
        assert s.handoff.expected_hops == 5
        assert s.handoff.spawn_policy == "ask"

    def test_spawn_policy_defaults_auto(self):
        s = SddSession.model_validate({**MINIMAL_SESSION, "handoff": {"expected_hops": 3}})
        assert s.handoff.spawn_policy == "auto"

    def test_expected_hops_must_be_positive(self):
        for bad in (0, -1):
            with pytest.raises(ValidationError):
                SddSession.model_validate({**MINIMAL_SESSION, "handoff": {"expected_hops": bad}})

    def test_round_trips_through_json(self):
        s = SddSession.model_validate({**MINIMAL_SESSION,
                                       "handoff": {"expected_hops": 4, "spawn_policy": "off"}})
        import json
        s2 = SddSession.model_validate(json.loads(s.model_dump_json()))
        assert s2.handoff == s.handoff

    def test_partial_block_rejected(self):        # deferred order B4 — see note below
        for partial in ({}, {"spawn_policy": "ask"}):
            with pytest.raises(ValidationError):
                SddSession.model_validate({**MINIMAL_SESSION, "handoff": partial})

    def test_spawn_policy_literal_is_closed_set(self):   # carry-forward from Task 4 quality r2
        from typing import get_args
        assert get_args(Handoff.model_fields["spawn_policy"].annotation) == ("auto", "ask", "off")
```

**The `_minimal_session()` helper is hypothetical — the same defect Task 4 hit, pre-resolved here
rather than passed to an implementer.** Verified with `/usr/bin/grep -rn "_minimal_session" tests/
skills/`: the only match is a *test method* named `test_minimal_session_parses`, not a helper.
`tests/unit/test_models/test_sdd_session_model.py` builds sessions from a module-level
`MINIMAL_SESSION` dict (line 19, itself referencing `MINIMAL_PATHS` at line 12) — the exact sibling
of `test_plan_model.py`'s `MINIMAL_PLAN`. Two further facts the Task 5 implementer needs: the file
already imports `CURRENT_SCHEMA_VERSION` and `ValidationError` at top level (do not re-import
inside a method), and it imports selectively from `sdd_session` — so **`Handoff` must be added to
that import list or `test_spawn_policy_literal_is_closed_set` raises `NameError`.**

**Deferred order B4 — the pinned reading, applied here and in Module 3.** `Handoff.expected_hops`
stays **required** (`int = Field(ge=1)`), i.e. the block is **all-or-nothing**: absent entirely is
legal (pre-v2 manifests, `handoff: None`), present-but-partial is not. Rationale: at
materialization `total_tasks` has already passed the plan gate, so `expected_hops` is always
derivable and Task 6 always emits both keys — the "invalid/zero → absent-with-warning"
degradation in Contract Constraints belongs to the *spawn-time* reader
(`derive_expected_hops`, which parses raw JSON and never goes through this model), not to
materialization. The model therefore enforces well-formedness for everything **we** write while
the CLI stays tolerant of anything we didn't. `test_partial_block_rejected` is the test B4
requires. **Consumer half:** Module 3 Task 8's `write_manifest` helper defaulted to
`expected_hops=None, spawn_policy=None`, which emits `"handoff": {}` — invalid under this
reading; it is amended there to emit a complete block by default (`omit_handoff=True` remains
the way to build a pre-v2 manifest).

**Carry-forward from Task 4's round-2 quality review.** `test_spawn_policy_literal_is_closed_set`
is the symmetric guard to Task 4's `test_literal_is_closed_set`. `SpawnPolicy` here and
`Plan.handoff_spawn` in `plan.py` are two **independent** declarations of the same three values
(deliberately not shared — the `implementer_report.TaskType` precedent), which is exactly the
shape where one-sided drift goes unnoticed. Task 4's guard watches only `plan.py`'s copy.

- [ ] **Step 2: Run to verify failure** — expect FAIL (extra field forbidden).

- [ ] **Step 3: Implement** — in `sdd_session.py`, after `RequirementLevel`:

```python
SpawnPolicy = Literal["auto", "ask", "off"]


class Handoff(StrictModel):
    """Auto-spawn consent + advisory hop budget (cmux-spawn-v2). Optional —
    absent on pre-v2 manifests; spawn-time consumers re-derive (see
    _handoff_support.derive_expected_hops)."""
    expected_hops: int = Field(ge=1)
    spawn_policy: SpawnPolicy = "auto"
```

and in `SddSession` (after `dispatch_log_sentinel`):

```python
    handoff: Handoff | None = None
```

- [ ] **Step 4: Run** — the class, then the whole model dir, then the session CLI on a real manifest to prove backward compat:

```bash
.venv/bin/python3 -m pytest tests/unit/test_models/ -v
.venv/bin/python3 skills/scripts/models/validators.py session docs/imp-plans/2026-07-22-cmux-integration/.sdd-session.json 2>/dev/null || true
```

(The old manifest may not exist in this worktree; if absent, construct one via `materialize-manifest.py` against the prior feature's plan in a temp dir, or rely on `test_absent_handoff_still_validates` — do not skip the backward-compat assertion in tests.)

- [ ] **Step 5: Commit**

```bash
git add skills/scripts/models/sdd_session.py tests/unit/test_models/test_sdd_session_model.py
git commit -m "feat(cmux-spawn-v2): sdd_session.py optional handoff block (expected_hops + spawn_policy)"
```

### Task 6: _handoff_support.py (formula + precedence) + materialize-manifest.py wiring

**Files:**
- Create: `skills/subagent-driven-development/scripts/_handoff_support.py`
- Modify: `skills/subagent-driven-development/scripts/materialize-manifest.py`
- Test: `tests/unit/test_handoff_support.py` (new), `tests/unit/test_materialize_manifest.py`

- [ ] **Step 1: Write the failing tests** (new file `tests/unit/test_handoff_support.py`):

```python
"""_handoff_support.py — formula, precedence, degradation."""
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent.parent / "skills" / "subagent-driven-development" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from _handoff_support import (  # noqa: E402
    HOP_DIVISOR, CEILING_FLOOR, CEILING_FACTOR,
    expected_hops, derive_total_tasks, derive_expected_hops, hop_ceiling,
)


class TestExpectedHops:
    def test_formula_standard(self):
        assert expected_hops(1, "standard") == 1
        assert expected_hops(5, "standard") == 2      # ceil(5/2.5)
        assert expected_hops(19, "standard") == 8     # ceil(19/2.5)

    def test_micro_is_one(self):
        assert expected_hops(19, "micro") == 1

    def test_invalid_total_raises(self):
        import pytest
        for bad in (0, -3, "7", None):
            with pytest.raises(ValueError):
                expected_hops(bad, "standard")


class TestDeriveTotalTasks:
    def test_precedence_1_manifest_total(self):
        assert derive_total_tasks({"total_tasks": 12, "modules": [{"task_ids": [1]}]}) == 12

    def test_precedence_2_module_union_dedupes(self):
        m = {"total_tasks": 0,
             "modules": [{"task_ids": [0, 1, 2]}, {"task_ids": [2, 3]}]}
        assert derive_total_tasks(m) == 4

    def test_precedence_3_task_range_inclusive(self):
        assert derive_total_tasks({"total_tasks": None, "modules": [], "task_range": [3, 7]}) == 5

    def test_all_invalid_returns_none(self):
        assert derive_total_tasks({"total_tasks": 0, "modules": [], "task_range": [7, 3]}) is None


class TestDeriveExpectedHops:
    def test_block_wins_else_derive_else_none(self):
        assert derive_expected_hops({"handoff": {"expected_hops": 9}, "total_tasks": 5}) == 9
        assert derive_expected_hops({"total_tasks": 5, "tier": "standard"}) == 2
        assert derive_expected_hops({"total_tasks": 0}) is None


class TestHopCeiling:
    def test_floor_factor_and_none(self):
        assert hop_ceiling(2) == 6                    # max(6, 4)
        assert hop_ceiling(8) == 16
        assert hop_ceiling(None) == CEILING_FLOOR
```

- [ ] **Step 2: Run to verify failure** — `ModuleNotFoundError: _handoff_support`.

- [ ] **Step 3: Implement `_handoff_support.py`** (import-only in this task; CLI arrives in Task 7):

```python
"""Hop-budget support for the SDD auto-spawn handoff (cmux-spawn-v2).

SSOT for the Decision 9 formula, derivation precedence, tasks_done counting
and stall streaks. Consumers: materialize-manifest.py (import) and
spawn-handoff-session.sh (CLI via $PYTHON — see Task 7). Follows the
_midpoint.py precedent: one home for a formula two callers would otherwise
duplicate. Stdlib-only at import time; PyYAML is imported lazily where needed."""
import math

HOP_DIVISOR = 2.5
CEILING_FLOOR = 6
CEILING_FACTOR = 2


def expected_hops(total_tasks, tier):
    """Decision 9: ceil(total/2.5) standard; 1 micro. Raises on garbage —
    callers that must degrade catch ValueError (never divide by garbage)."""
    if tier == "micro":
        return 1
    if not isinstance(total_tasks, int) or isinstance(total_tasks, bool) or total_tasks <= 0:
        raise ValueError(f"total_tasks must be a positive int, got {total_tasks!r}")
    return math.ceil(total_tasks / HOP_DIVISOR)


def derive_total_tasks(manifest):
    """Pinned input precedence (spec Contract Facts): (1) validated manifest
    total_tasks; (2) union of unique module task IDs; (3) inclusive active
    task_range. Returns None when nothing is derivable (absent-with-warning)."""
    t = manifest.get("total_tasks")
    if isinstance(t, int) and not isinstance(t, bool) and t > 0:
        return t
    ids = set()
    for m in manifest.get("modules") or []:
        if isinstance(m, dict):
            for tid in m.get("task_ids") or []:
                if isinstance(tid, int) and not isinstance(tid, bool):
                    ids.add(tid)
    if ids:
        return len(ids)
    tr = manifest.get("task_range")
    if (isinstance(tr, (list, tuple)) and len(tr) == 2
            and all(isinstance(x, int) and not isinstance(x, bool) for x in tr)
            and tr[0] <= tr[1]):
        return tr[1] - tr[0] + 1
    return None


def derive_expected_hops(manifest):
    """Manifest handoff.expected_hops when valid; else re-derive; else None."""
    h = manifest.get("handoff") or {}
    eh = h.get("expected_hops") if isinstance(h, dict) else None
    if isinstance(eh, int) and not isinstance(eh, bool) and eh >= 1:
        return eh
    total = derive_total_tasks(manifest)
    if total is None:
        return None
    return expected_hops(total, manifest.get("tier") or "standard")


def hop_ceiling(exp):
    """Derived ceiling default: max(6, 2 x expected). None -> floor."""
    if exp is None:
        return CEILING_FLOOR
    return max(CEILING_FLOOR, CEILING_FACTOR * exp)
```

- [ ] **Step 4: Run** — the new test file passes.

- [ ] **Step 5: Write the failing materialize tests** (append to `tests/unit/test_materialize_manifest.py`, following its existing run-and-load idiom):

```python
class TestHandoffBlockMaterialization:
    def test_manifest_gains_handoff_block(self, tmp_path):
        # plan frontmatter WITHOUT handoff_spawn, 5 tasks, standard tier
        manifest = _materialize(tmp_path, tasks=5)          # existing helper idiom
        assert manifest["handoff"] == {"expected_hops": 2, "spawn_policy": "auto"}

    def test_spawn_policy_copied_from_plan(self, tmp_path):
        manifest = _materialize(tmp_path, tasks=5, extra_frontmatter="handoff_spawn: ask")
        assert manifest["handoff"]["spawn_policy"] == "ask"

    def test_micro_tier_expected_hops_is_one(self, tmp_path):
        manifest = _materialize(tmp_path, tasks=2, tier="micro")
        assert manifest["handoff"]["expected_hops"] == 1
```

Adapt `_materialize(...)` to however the file actually builds plan files and invokes the script — read it first; do not invent a parallel harness.

- [ ] **Step 6: Implement the materialize wiring** — in `materialize-manifest.py`:

```python
from _handoff_support import expected_hops  # top, beside the _midpoint import
```

and in `materialize()`, after the tier/tasks are known and before `SddSession(...)`:

```python
    # --- Handoff block (cmux-spawn-v2) ---
    spawn_policy = frontmatter.get("handoff_spawn") or "auto"
    handoff = {
        "expected_hops": expected_hops(total_tasks, tier),
        "spawn_policy": spawn_policy,
    }
```

pass `handoff=handoff` into the `SddSession(...)` constructor (the model validates the policy literal — an invalid frontmatter value fails materialization loudly, which is correct: the plan gate should have caught it).

- [ ] **Step 7: Run everything this touches**

```bash
.venv/bin/python3 -m pytest tests/unit/test_handoff_support.py tests/unit/test_materialize_manifest.py tests/unit/test_models/ -v
bash tests/integration/sdd-e2e-test.sh   # Steps 1-13 exercise materialize + checkpoint on manifests that now carry handoff
```

All PASS. The e2e run here is load-bearing: it proves old consumers (hook, checkpoint, transition) tolerate the new manifest key.

- [ ] **Step 8: Commit**

```bash
git add skills/subagent-driven-development/scripts/_handoff_support.py \
        skills/subagent-driven-development/scripts/materialize-manifest.py \
        tests/unit/test_handoff_support.py tests/unit/test_materialize_manifest.py
git commit -m "feat(cmux-spawn-v2): _handoff_support formula/precedence SSOT + manifest handoff block"
```

### Task 7: _handoff_support.py — tasks_done counting + stall streak + CLI

**Files:**
- Modify: `skills/subagent-driven-development/scripts/_handoff_support.py`
- Test: `tests/unit/test_handoff_support.py`

- [ ] **Step 1: Write the failing tests** (append; the module-level helpers from the "Shared test helpers" section above must already be in the file):

```python
class TestTasksDone:
    def test_done_and_concerns_count_blocked_and_malformed_do_not(self, tmp_path):
        from _handoff_support import count_tasks_done
        r = tmp_path / "reports"
        _write_report(r, 1, "DONE", task_type="verification")   # empty files_changed OK
        _write_report(r, 2, "DONE_WITH_CONCERNS")
        _write_report(r, 3, "BLOCKED")
        (r / "task-005-implementer-report.md").write_text("no frontmatter at all")
        assert count_tasks_done(str(r)) == 2                    # filename alone never counts

    def test_archives_counted_and_duplicates_deduped(self, tmp_path):
        from _handoff_support import count_tasks_done
        r = tmp_path / "reports"
        _write_report(r, 4, "DONE")
        _write_report(r / "archive-module-1", 1, "DONE")
        _write_report(r / "archive-module-1", 4, "DONE")        # dupe of live task 4
        assert count_tasks_done(str(r)) == 2                    # {1, 4}


class TestStallStreak:
    OUT = "2026-07-30T00:00:0{i}Z u{i} outcome hop={i} workspace=w surface=s launch=auto bundle=b quota=ok tasks_done={td} handshake=ok"

    def _streak(self, tmp_path, rows, current):
        f = tmp_path / "handoff-spawn.log"
        f.write_text(_log(rows))
        from _handoff_support import stall_streak
        return stall_streak(str(f), current)

    def test_first_hop_and_progress_are_zero(self, tmp_path):
        assert self._streak(tmp_path, [], 0) == 0
        rows = [self.OUT.format(i=1, td=2), self.OUT.format(i=2, td=4)]
        assert self._streak(tmp_path, rows, 5) == 0

    def test_one_stall_then_two_consecutive(self, tmp_path):
        rows = [self.OUT.format(i=1, td=2), self.OUT.format(i=2, td=4)]
        assert self._streak(tmp_path, rows, 4) == 1
        rows = [self.OUT.format(i=1, td=4), self.OUT.format(i=2, td=4)]
        assert self._streak(tmp_path, rows, 4) == 2

    def test_malformed_last_outcome_is_indeterminate(self, tmp_path):
        rows = ["2026-07-30T00:00:01Z u1 outcome hop=1 workspace=w launch=auto"]  # no tasks_done=
        assert self._streak(tmp_path, rows, 3) == "indeterminate"


class TestCli:
    def _run(self, *args):
        return subprocess.run([VENV_PY, SUPPORT, *args], capture_output=True, text=True)

    def test_tasks_done_cli(self, tmp_path):
        r = tmp_path / "reports"
        _write_report(r, 1, "DONE")
        out = self._run("tasks-done", "--reports-dir", str(r))
        assert out.returncode == 0 and out.stdout.strip() == "1"

    def test_expected_hops_and_policy_cli_on_legacy_and_garbage(self, tmp_path):
        m = tmp_path / "m.json"
        m.write_text('{"total_tasks": 5, "tier": "standard"}')   # pre-v2: no handoff block
        assert self._run("expected-hops", "--manifest", str(m)).stdout.strip() == "2"
        assert self._run("spawn-policy", "--manifest", str(m)).stdout.strip() == "auto"
        m.write_text('{"total_tasks": 0}')
        assert self._run("expected-hops", "--manifest", str(m)).stdout.strip() == "unknown"
```

- [ ] **Step 2: Run to verify failure** — ImportError on `count_tasks_done` / `stall_streak`; CLI exits 2.

- [ ] **Step 3: Implement** (append to `_handoff_support.py`):

```python
import glob, json, os, re, sys   # noqa: E401 — split one-per-line in the real file (house style)

_REPORT_GLOB = "task-*-implementer-report*.md"
_DONE_STATUSES = ("DONE", "DONE_WITH_CONCERNS")


def _frontmatter(text):
    import yaml   # ImportError PROPAGATES: a venv-less python3 must not fake "0 done"
    if not text.startswith("---"):
        return None
    end = text.find("---", 3)
    if end == -1:
        return None
    try:
        fm = yaml.safe_load(text[3:end])
    except Exception:
        return None
    return fm if isinstance(fm, dict) else None


def count_tasks_done(reports_dir):
    """Unique task IDs across reports/ + archive-*/ with parsing frontmatter
    AND completed status. Filenames alone never count; BLOCKED/malformed/
    duplicates never inflate progress."""
    done = set()
    patterns = [os.path.join(reports_dir, _REPORT_GLOB),
                os.path.join(reports_dir, "archive-*", _REPORT_GLOB)]
    for pat in patterns:
        for path in glob.glob(pat):
            try:
                fm = _frontmatter(open(path, encoding="utf-8").read())
            except OSError:
                continue
            if not fm:
                continue
            tid = fm.get("task_id")
            if (isinstance(tid, int) and not isinstance(tid, bool)
                    and fm.get("status") in _DONE_STATUSES):
                done.add(tid)
    return len(done)


_OUTCOME_RE = re.compile(r"^\S+ \S+ outcome ")


def stall_streak(spawn_log_path, current_tasks_done):
    """Trailing consecutive outcome records whose tasks_done == current count.
    0 = progress or first hop. 'indeterminate' = newest outcome record missing/
    malformed on tasks_done — caller SKIPs (fail-closed stays with .handoff-hops)."""
    try:
        lines = open(spawn_log_path, encoding="utf-8").read().splitlines()
    except OSError:
        return 0                                  # no log yet: first hop
    outcomes = [l for l in lines if _OUTCOME_RE.match(l)]
    if not outcomes:
        return 0
    streak = 0
    for line in reversed(outcomes):
        m = re.search(r"\btasks_done=(\d+)\b", line)
        if m is None:
            return "indeterminate" if streak == 0 else streak
        if int(m.group(1)) == current_tasks_done:
            streak += 1
        else:
            break
    return streak


def _cli(argv):
    """CLI for spawn-handoff-session.sh: prints ONE value on stdout. Exit 0
    with a value ('unknown'/'indeterminate' are values); exit 2 = usage error."""
    import argparse
    p = argparse.ArgumentParser(prog="_handoff_support.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("tasks-done").add_argument("--reports-dir", required=True)
    sub.add_parser("expected-hops").add_argument("--manifest", required=True)
    s3 = sub.add_parser("stall-streak")
    s3.add_argument("--spawn-log", required=True)
    s3.add_argument("--tasks-done", required=True, type=int)
    sub.add_parser("spawn-policy").add_argument("--manifest", required=True)
    a = p.parse_args(argv)
    if a.cmd == "tasks-done":
        try:
            print(count_tasks_done(a.reports_dir))
        except ImportError:
            print("unknown")   # missing PyYAML degrades observably — a fake 0 manufactures stalls
        return 0
    if a.cmd == "stall-streak":
        print(stall_streak(a.spawn_log, a.tasks_done)); return 0
    try:
        manifest = json.load(open(a.manifest, encoding="utf-8"))
    except Exception:
        manifest = {}
    if a.cmd == "expected-hops":
        eh = derive_expected_hops(manifest)
        print("unknown" if eh is None else eh); return 0
    h = manifest.get("handoff")
    pol = h.get("spawn_policy") if isinstance(h, dict) else None
    print(pol if pol in ("auto", "ask", "off") else "auto"); return 0


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
```

- [ ] **Step 4: Run** — `.venv/bin/python3 -m pytest tests/unit/test_handoff_support.py -v` — all PASS. Then the module-wide check: `.venv/bin/python3 -m pytest tests/unit/ -q` — no regressions.

- [ ] **Step 5: Commit**

```bash
git add skills/subagent-driven-development/scripts/_handoff_support.py tests/unit/test_handoff_support.py
git commit -m "feat(cmux-spawn-v2): tasks_done counting + stall streak + _handoff_support CLI"
```

## Module 2 Acceptance Criteria

- [ ] `Plan` accepts `handoff_spawn` (default `auto`); every pre-existing plan still validates; schema version still 1.
- [ ] `SddSession` accepts an optional `handoff` block; pre-v2 manifests (no block) still validate.
- [ ] `materialize-manifest.py` writes `handoff` with the Decision 9 `expected_hops` and the plan's `spawn_policy`.
- [ ] `_handoff_support.py` is the ONLY place the formula constants (2.5 / 6 / 2), precedence, tasks_done rules, and stall streak live.
- [ ] CLI prints `unknown` / `indeterminate` as values (exit 0) — degradation is observable, never an exception.
- [ ] Full unit suite + e2e Steps 1-13 green.
