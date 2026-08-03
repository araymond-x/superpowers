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

**Contract Constraints:** `Plan` and `SddSession` are `extra="forbid"` — new fields must be optional with defaults so every existing plan/manifest still validates; `CURRENT_SCHEMA_VERSION` stays 1. `expected_hops = ceil(total_tasks / 2.5)` standard, `1` micro. Derivation precedence: validated manifest total → union of module task IDs → inclusive `task_range`; invalid/zero → `None` (absent-with-warning). `tasks_done`: unique task IDs whose implementer-report frontmatter parses AND has status `DONE`/`DONE_WITH_CONCERNS` (verification reports count under the same statuses — their `files_changed` may be empty); filenames alone never count; scans `reports/` AND `archive-*/`. **Python 3.9 scan asymmetry (deferred order B7):** `check_python39_compat` flat-globs `skills/subagent-driven-development/scripts/*.py` ONLY — so `_handoff_support.py` (Tasks 6-7) must use no PEP-604 unions and no builtin generics in annotations (`Optional[X]` / `Dict[str, int]`, not `X | None` / `dict[str, int]`), while `skills/scripts/models/` is NOT scanned and Task 5's `Handoff | None` is correct there. Do not "harmonize" the two directories. **Never normalize `handoff_spawn` with `or` (Task 6):** PyYAML is YAML 1.1, so bare `handoff_spawn: off` parses to boolean `False`, and `False or "auto"` silently turns a *refusal* into spawn-without-asking. Use `if spawn_policy is None:` so a falsy value reaches the `Handoff` model and fails materialization loudly.

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


def _write_report(d, task_id, status, task_type="implementation", name=None,
                  files_changed="[{path: x, description: y}]"):
    # files_changed defaults NON-EMPTY: ImplementerReport rejects DONE /
    # DONE_WITH_CONCERNS with an empty list. Pass files_changed="[]" to
    # exercise the task_type=="verification" exemption.
    d.mkdir(parents=True, exist_ok=True)
    body = (f"---\nschema_version: 1\ntask_id: {task_id}\nstatus: {status}\n"
            f"task_type: {task_type}\nfiles_changed: {files_changed}\n"
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

- [x] **Step 1: Write the failing tests.** `_minimal_session()` **DOES NOT EXIST** — verified, see the note below. Use the file's real idiom: the module-level `MINIMAL_SESSION` dict spread into `SddSession.model_validate({**MINIMAL_SESSION, ...})`, exactly as `TestSddSessionGoldenInput` does. Add `Handoff` to the existing `from sdd_session import (...)` block.

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

    def test_extra_key_rejected(self):    # pins StrictModel base — see note below
        with pytest.raises(ValidationError):
            SddSession.model_validate({**MINIMAL_SESSION,
                                       "handoff": {"expected_hops": 5, "typo": 1}})
```

**`test_extra_key_rejected` pins the BASE CLASS, and none of the other seven can.** Controller
amendment at Task 5 dispatch. Every one of the first seven tests exercises only fields `Handoff`
declares, so they pin its *positive* surface; `class Handoff(BaseModel)` — non-strict — passes all
seven green. `test_partial_block_rejected` is not a substitute: "missing required field" and
"unknown field rejected" are different Pydantic mechanisms, and only `extra="forbid"` (inherited
from `StrictModel`, `_base.py`) produces the latter. This is the over-permissive shape a
one-directional mutation battery misses — the same class of defect as Task 4's un-pinned `Literal`.
Discriminating control: swapping the base to `BaseModel` must fail exactly this test and no other.

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

- [x] **Step 2: Run to verify failure** — expect FAIL (extra field forbidden).

- [x] **Step 3: Implement** — in `sdd_session.py`, after `RequirementLevel`:

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

- [x] **Step 4: Run** — the class, then the whole model dir, then the session CLI on a real manifest to prove backward compat:

```bash
.venv/bin/python3 -m pytest tests/unit/test_models/ -v
.venv/bin/python3 skills/scripts/models/validators.py session docs/imp-plans/2026-07-22-cmux-integration/.sdd-session.json 2>/dev/null || true
```

(The old manifest may not exist in this worktree; if absent, construct one via `materialize-manifest.py` against the prior feature's plan in a temp dir, or rely on `test_absent_handoff_still_validates` — do not skip the backward-compat assertion in tests.)

- [x] **Step 5: Commit** — landed as `f91b94f`; a `[task 5 fix]` round added three mutation-killing tests in `d1741e0` (`test_expected_hops_accepts_one`, `test_rejects_invalid_spawn_policy`, `test_expected_hops_must_be_an_integer` — see deviations). Suite 671 → 674.

```bash
git add skills/scripts/models/sdd_session.py tests/unit/test_models/test_sdd_session_model.py
git commit -m "feat(cmux-spawn-v2): sdd_session.py optional handoff block (expected_hops + spawn_policy)"
```

### Task 6: _handoff_support.py (formula + precedence) + materialize-manifest.py wiring

**Files:**
- Create: `skills/subagent-driven-development/scripts/_handoff_support.py`
- Modify: `skills/subagent-driven-development/scripts/materialize-manifest.py`
- Test: `tests/unit/test_handoff_support.py` (new), `tests/unit/test_materialize_manifest.py`

- [x] **Step 1: Write the failing tests** (new file `tests/unit/test_handoff_support.py`):

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

- [x] **Step 2: Run to verify failure** — `ModuleNotFoundError: _handoff_support`.

- [x] **Step 3: Implement `_handoff_support.py`** (import-only in this task; CLI arrives in Task 7):

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

- [x] **Step 4: Run** — the new test file passes.

- [x] **Step 5: Write the failing materialize tests** (append to `tests/unit/test_materialize_manifest.py`). **`_materialize()` DOES NOT EXIST** — verified; third instance of this plan-wide phantom-helper defect after `_minimal_plan()` and `_minimal_session()`, pre-resolved here rather than handed to an implementer. Real idiom: module-level `make_plan(tier=, tasks=, modules=, omit_tier=)` returns plan TEXT, then `run_materialize(plan, tmp_dir=)` returns a dict whose `["manifest"]` is the parsed JSON; wrap in `tempfile.mkdtemp()` + `try/finally shutil.rmtree` (both already imported). Two signature traps: `tasks` is a **list of dicts** (`[{"id": i}]`), NOT a count; and there is **no `extra_frontmatter` param** — add one to `make_plan` (you own the file) so frontmatter can carry `handoff_spawn`. There is no `tmp_path` fixture in this file.

```python
class TestHandoffBlockMaterialization:
    def _mf(self, ok=True, **kw):            # make_plan + run_materialize + cleanup
        tmp = tempfile.mkdtemp()
        try:
            r = run_materialize(make_plan(**kw), tmp_dir=tmp)
            assert (r["exit_code"] == 0) is ok, r["stderr"]
            return r["manifest"] if ok else r
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    def test_manifest_gains_handoff_block(self):      # default 5 tasks, standard
        assert self._mf()["handoff"] == {"expected_hops": 2, "spawn_policy": "auto"}
    def test_spawn_policy_copied_from_plan(self):
        assert self._mf(extra_frontmatter="handoff_spawn: ask")["handoff"]["spawn_policy"] == "ask"
    def test_micro_tier_expected_hops_is_one(self):
        assert self._mf(tier="micro", tasks=[{"id": 0}, {"id": 1}])["handoff"]["expected_hops"] == 1
    def test_off_survives_and_bare_off_is_never_coerced_to_auto(self):   # YAML 1.1: bare off is False
        assert self._mf(extra_frontmatter='handoff_spawn: "off"')["handoff"]["spawn_policy"] == "off"
        assert self._mf(extra_frontmatter="handoff_spawn: off", ok=False)["exit_code"] != 0
```

- [x] **Step 6: Implement the materialize wiring** — import beside the existing `_midpoint` import (mid-file, ~line 59 — NOT the file top), then in `materialize()` between `total_tasks` and the `SddSession(...)` call:

```python
from _handoff_support import expected_hops   # beside the _midpoint import
    # --- Handoff block (cmux-spawn-v2) ---
    spawn_policy = frontmatter.get("handoff_spawn")
    if spawn_policy is None:                 # NOT `or` — bare `off` is YAML 1.1 False
        spawn_policy = "auto"
    handoff = {"expected_hops": expected_hops(total_tasks, tier),
               "spawn_policy": spawn_policy}
```

Pass `handoff=handoff` into `SddSession(...)`. The model then validates the literal, so a non-`None` bad value (incl. `False` from bare `off`) fails materialization **loudly** — correct: the plan gate should have caught it.

- [x] **Step 7: Run everything this touches**

```bash
.venv/bin/python3 -m pytest tests/unit/test_handoff_support.py tests/unit/test_materialize_manifest.py tests/unit/test_models/ -v
bash tests/integration/sdd-e2e-test.sh   # Steps 1-13 exercise materialize + checkpoint on manifests that now carry handoff
```

All PASS. The e2e run here is load-bearing: it proves old consumers (hook, checkpoint, transition) tolerate the new manifest key.

- [x] **Step 8: Commit**

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

- [x] **Step 1: Write the failing tests** (append; the module-level helpers from the "Shared test helpers" section above must already be in the file):

```python
class TestTasksDone:
    def test_done_and_concerns_count_blocked_and_malformed_do_not(self, tmp_path):
        from _handoff_support import count_tasks_done
        r = tmp_path / "reports"
        _write_report(r, 1, "DONE", task_type="verification", files_changed="[]")
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
        assert self._run("spawn-policy", "--manifest", str(tmp_path / "no.json")).stdout.strip() == "ask"   # fails CLOSED
```

- [x] **Step 2: Run to verify failure** — ImportError on `count_tasks_done` / `stall_streak`; CLI exits 2.

- [x] **Step 3: Implement** (append to `_handoff_support.py`):

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
    """Unique task IDs across reports/ + archive-*/ with parsing frontmatter AND
    completed status. Filenames/BLOCKED/malformed/dupes never inflate progress."""
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
    """Trailing consecutive outcome records whose tasks_done == current count. 0 = progress or
    first hop. 'indeterminate' = newest outcome missing/malformed on tasks_done; caller SKIPs."""
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
    """CLI for spawn-handoff-session.sh: ONE value on stdout; exit 0 with a value
    ('unknown'/'indeterminate' count), exit 2 = usage. Spec pins only READABLE-but-
    absent-block -> 'auto'; unreadable fails CLOSED to 'ask' (sole consent gate)."""
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
        manifest = None                    # unreadable: consent must not default OPEN
    if not isinstance(manifest, dict): manifest = None   # valid JSON that isn't an object
    if a.cmd == "expected-hops":
        eh = derive_expected_hops(manifest or {})
        print("unknown" if eh is None else eh); return 0
    h = (manifest or {}).get("handoff")
    pol = h.get("spawn_policy") if isinstance(h, dict) else None   # unreadable -> "ask"
    print(pol if pol in ("auto", "ask", "off") else ("auto" if manifest is not None else "ask")); return 0


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
```

- [x] **Step 4: Run** — `.venv/bin/python3 -m pytest tests/unit/test_handoff_support.py -v` — all PASS. Then the module-wide check: `.venv/bin/python3 -m pytest tests/unit/ -q` — no regressions.

- [x] **Step 5: Commit**

```bash
git add skills/subagent-driven-development/scripts/_handoff_support.py tests/unit/test_handoff_support.py
git commit -m "feat(cmux-spawn-v2): tasks_done counting + stall streak + _handoff_support CLI"
```

## Module 2 Acceptance Criteria

- [x] `Plan` accepts `handoff_spawn` (default `auto`); every pre-existing plan still validates; schema version still 1.
- [x] `SddSession` accepts an optional `handoff` block; pre-v2 manifests (no block) still validate.
- [x] `materialize-manifest.py` writes `handoff` with the Decision 9 `expected_hops` and the plan's `spawn_policy`.
- [x] `_handoff_support.py` is the ONLY place the formula constants (2.5 / 6 / 2), precedence, tasks_done rules, and stall streak live.
- [x] CLI prints `unknown` / `indeterminate` as values (exit 0) — degradation is observable. **GREEN 2026-08-02, after Task 8 landed all three blocking rows. Flipped on MEASUREMENT, not on the reports' say-so** — each path was re-run against the shipped CLI by the controller: P7-3 with PyYAML genuinely blocked via a `PYTHONPATH` stub (`raise ImportError`) prints `unknown`, not a fake count, for both a populated and an empty `reports/` — **and the first attempt at this probe was invalid because system `python3` turns out to HAVE PyYAML 6.0.3, so the "no PyYAML" arm did not exist until the blocker was added and positive-controlled**; P7-6 with a non-UTF-8 byte inside the frontmatter exits 0 with a value instead of raising; P7-8 with an unreadable spawn log prints `indeterminate`, not `0`. Positive controls run alongside each. **One residual, deliberately NOT held against this box** (new and narrower than any of the three scheduled rows): a report skipped for a decode error is skipped SILENTLY — two DONE reports, one corrupted, prints `1` with empty stderr and rc 0, so that particular degradation is real but *not* observable. The skip itself is the right call and is reasoned in-code (`_handoff_support.py`, the `except (OSError, UnicodeDecodeError)` comment): under-counting biases the stall guard toward FIRING, whereas `errors="replace"` would produce a decoded-garbage count biased toward disabling it. Only the missing diagnostic is open — a candidate BACKLOG row at merge, since `_handoff_support.py` is read-only for Tasks 9–11. **Prior text, retained for provenance:** _"PARTIAL, deliberately not green."_ Every path the plan's Step 3 text specifies is met, but three measured paths violate it and are scheduled to Module 3: P7-3 (empty `reports/` + no PyYAML prints a fake `0`), P7-6 (a non-UTF-8 report byte raises `UnicodeDecodeError`, escaping the `except OSError` → exit 1, empty stdout), P7-8 (`stall_streak` returns `0` = proceed on any `OSError`). All three need a production edit to a plan-verbatim body, which Task 7 was not permitted to make. Quality review round 2 required this annotation before the module transition, because the reports carrying these findings get archived at the boundary while this register survives it.
- [x] Full unit suite + e2e Steps 1-13 green.
