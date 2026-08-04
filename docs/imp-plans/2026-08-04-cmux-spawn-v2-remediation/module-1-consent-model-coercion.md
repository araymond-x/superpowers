# Module 1 — Consent model + YAML coercion (N83)

**Goal:** Accept unquoted `handoff_spawn: off` (and its manifest sibling `spawn_policy`) as the off policy at the Pydantic model boundary, rejecting bare `on`, so the plan gate stops FAILing on the feature's headline opt-out value. Quoted `"off"` stays unchanged; the default stays `auto`.

**Source Contracts:**
- `docs/imp-plans/2026-08-04-cmux-spawn-v2-remediation/spec-distilled.md` — Contract Facts (`handoff_spawn`/`spawn_policy` Literals, N83 coercion behavior, reason codes) + Component Spec C1.
- `skills/scripts/models/plan.py` — `Plan.handoff_spawn: Literal["auto","ask","off"] = "auto"` (line 62); `field_validator` already imported (line 5); existing `@field_validator` idiom on `IntegrationTest.path_must_be_relative_and_safe` (lines 28-37).
- `skills/scripts/models/sdd_session.py` — `SpawnPolicy = Literal["auto","ask","off"]` (line 13); `Handoff.spawn_policy: SpawnPolicy = "auto"` (line 21); imports only `Field, model_validator` (line 4) — **`field_validator` is NOT imported here**.
- `skills/subagent-driven-development/scripts/materialize-manifest.py` — handoff block (lines 117-122): `spawn_policy = frontmatter.get("handoff_spawn")` then `if spawn_policy is None: spawn_policy = "auto"`.
- `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` — Precondition 2b already emits `reason=policy-off` (line 211) when manifest `spawn_policy=off`.

**Contract Constraints:**
- PyYAML 6.0.3 (YAML 1.1): unquoted `off`→`False`, `on`→`True`, `no`→`False`, `yes`→`True`; quoted `"off"`→`'off'` (str). Verified empirically 2026-08-04.
- Fix: `mode="before"` validators map `False`→`"off"`; **reject** `True` with an actionable message. Do NOT change the Literal value set or the `auto` default.
- The real plan-gate rejection is **Gate 1b** (`validators.py plan <file>` under venv python). Test at the `validators.py` layer, not `validate-plan.py --plan-file`.
- `validate-plan.py` stays stdlib-only — do not import pydantic from anything it imports. (The fix touches only `plan.py`, `sdd_session.py`, `materialize-manifest.py` — none imported by `validate-plan.py`.)

**Pattern References:**
- `skills/scripts/models/plan.py` `IntegrationTest.path_must_be_relative_and_safe` — the `@field_validator("field")` + `@classmethod` idiom (Tasks 1, 2).

## File Map

| File | Responsibility |
|------|----------------|
| `tests/fixtures/n83_yaml_cases.py` (new) | Canonical YAML coercion cases + expected coerced values (Task 0) |
| `tests/unit/test_n83_yaml_contract.py` (new) | Contract test: PyYAML coerces off→False etc.; current model/reader shape (Task 0) |
| `skills/scripts/models/plan.py` | `Plan.handoff_spawn` `mode="before"` validator (Task 1) |
| `skills/scripts/models/sdd_session.py` | `Handoff.spawn_policy` `mode="before"` validator (Task 2) |
| `skills/subagent-driven-development/scripts/materialize-manifest.py` | Normalize `False`→`"off"` (Task 3) |
| `tests/unit/test_models/test_plan_model.py` (existing — extend `TestHandoffSpawn`) | plan.py coercion tests + validators.py CLI proof (Task 1) |
| `tests/unit/test_models/test_sdd_session_model.py` (existing — extend `TestHandoffBlock`) | sdd_session.py coercion tests (Task 2) |
| `tests/unit/test_materialize_manifest.py` (existing — extend `TestHandoffBlockMaterialization`, flip the pre-fix `test_off_survives_*` test) | materialize normalization + script proof (Task 3) |

## Write-Scope Partitioning

| Task | Owned Files (write) | Read-Only | Depends On |
|------|---------------------|-----------|------------|
| Task 0 | `tests/fixtures/n83_yaml_cases.py`, `tests/unit/test_n83_yaml_contract.py` | plan.py, sdd_session.py, materialize-manifest.py, spawn-handoff-session.sh | — |
| Task 1 | `skills/scripts/models/plan.py`, `tests/unit/test_models/test_plan_model.py` | fixtures, validators.py | Task 0 |
| Task 2 | `skills/scripts/models/sdd_session.py`, `tests/unit/test_models/test_sdd_session_model.py` | fixtures | Task 0 |
| Task 3 | `skills/subagent-driven-development/scripts/materialize-manifest.py`, `tests/unit/test_materialize_manifest.py` | sdd_session.py, spawn-handoff-session.sh | Tasks 1, 2 |

---

### Task 0: Contract verification: YAML coercion ground truth + current model/reader shape (BLOCKING)

**Files:**
- Create: `tests/fixtures/n83_yaml_cases.py`
- Create: `tests/unit/test_n83_yaml_contract.py`

This is a blocking Task 0. It anchors Tasks 1–3 to the actual PyYAML behavior in this environment and the current shapes of the three readers, so no implementer builds against an assumed `off`→`False`.

> **Known pre-fix test to flip (do NOT fix here — Task 3 owns it):** `tests/unit/test_materialize_manifest.py::TestHandoffBlockMaterialization::test_off_survives_and_bare_off_is_never_coerced_to_auto` currently asserts the *buggy* behavior as correct (unquoted `handoff_spawn: off` makes materialize FAIL). It is green today and will invert once the N83 fix lands — Task 3 renames it and flips the assertion. Existing `handoff_spawn`/`spawn_policy` coverage also already lives in `tests/unit/test_models/test_plan_model.py::TestHandoffSpawn` and `tests/unit/test_models/test_sdd_session_model.py::TestHandoffBlock` — Tasks 1 and 2 extend those classes, they do not create new flat-path files (a duplicate basename under `tests/unit/` would break pytest collection).

- [x] **Step 1: Write the fixtures module**

Create `tests/fixtures/n83_yaml_cases.py`:

```python
"""Canonical YAML-1.1 coercion cases for handoff_spawn / spawn_policy (N83).

Ground truth captured 2026-08-04 against PyYAML 6.0.3 (yaml.safe_load).
Each entry: (raw_yaml_scalar, expected_python_value_after_safe_load).
"""

# What `handoff_spawn: <raw>` yields from yaml.safe_load, BEFORE any coercion.
YAML_SCALAR_CASES = [
    ("off", False),      # unquoted -> YAML 1.1 bool False  (the footgun)
    ('"off"', "off"),    # quoted   -> string, unchanged
    ("on", True),        # unquoted -> YAML 1.1 bool True    (invalid mode)
    ("auto", "auto"),
    ("ask", "ask"),
]

# What the coercion validators must produce from the parsed python value.
# False -> "off"; True -> ValueError; strings pass through unchanged.
COERCION_EXPECTATIONS = [
    (False, "off"),
    ("off", "off"),
    ("auto", "auto"),
    ("ask", "ask"),
    # True is handled separately (must raise), not in this pass-through table.
]
```

- [x] **Step 2: Write the contract test**

Create `tests/unit/test_n83_yaml_contract.py`:

```python
"""N83 contract: PyYAML coercion ground truth + current reader shapes.

These assertions are STABLE facts the N83 fix rests on. They do not assert the
pre-fix model rejection (Task 1 replaces that with the post-fix coercion).
"""
import os
import sys

import yaml

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "fixtures")
sys.path.insert(0, os.path.abspath(FIXTURES))
from n83_yaml_cases import YAML_SCALAR_CASES  # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def test_pyyaml_coerces_unquoted_off_to_false():
    for raw, expected in YAML_SCALAR_CASES:
        got = yaml.safe_load(f"handoff_spawn: {raw}")["handoff_spawn"]
        assert got == expected and type(got) is type(expected), (
            f"handoff_spawn: {raw} -> {got!r} (expected {expected!r})"
        )


def test_plan_model_has_handoff_spawn_literal():
    p = os.path.join(REPO, "skills", "scripts", "models", "plan.py")
    src = open(p, encoding="utf-8").read()
    assert 'handoff_spawn: Literal["auto", "ask", "off"] = "auto"' in src


def test_sdd_session_has_spawn_policy_literal():
    p = os.path.join(REPO, "skills", "scripts", "models", "sdd_session.py")
    src = open(p, encoding="utf-8").read()
    assert 'SpawnPolicy = Literal["auto", "ask", "off"]' in src
    assert "spawn_policy: SpawnPolicy" in src


def test_materialize_reads_handoff_spawn_from_frontmatter():
    p = os.path.join(REPO, "skills", "subagent-driven-development", "scripts",
                     "materialize-manifest.py")
    src = open(p, encoding="utf-8").read()
    assert 'frontmatter.get("handoff_spawn")' in src


def test_script_emits_policy_off_reason():
    p = os.path.join(REPO, "skills", "subagent-driven-development", "scripts",
                     "spawn-handoff-session.sh")
    src = open(p, encoding="utf-8").read()
    assert "reason=policy-off" in src
```

- [x] **Step 3: Run the contract test — it must PASS now (pre-fix)**

Run: `.venv/bin/python3 -m pytest tests/unit/test_n83_yaml_contract.py -v`
Expected: all PASS (these are current-state facts).

- [x] **Step 4: Commit**

```bash
git add tests/fixtures/n83_yaml_cases.py tests/unit/test_n83_yaml_contract.py
git commit -m "test(n83): contract fixtures + YAML coercion ground truth (Task 0)"
```

---

### Task 1: plan.py — `handoff_spawn` mode=before coercion validator

**Files:**
- Modify: `skills/scripts/models/plan.py` (`Plan` class, near the field/validators)
- Test: `tests/unit/test_models/test_plan_model.py` (extend `TestHandoffSpawn`)

**Pattern References:** `plan.py` `IntegrationTest.path_must_be_relative_and_safe` — same `@field_validator` + `@classmethod` idiom (with `mode="before"` here).

- [x] **Step 1: Write the failing tests (extend the existing `TestHandoffSpawn` class)**

Add to the existing `class TestHandoffSpawn` in `tests/unit/test_models/test_plan_model.py` (which already covers default `auto`, accept `ask`/`off`, reject invalid, and pins the Literal). It uses `Plan.model_validate(MINIMAL_PLAN)` and `{**MINIMAL_PLAN, "handoff_spawn": v}`; `Plan`, `ValidationError`, `pytest`, and `MINIMAL_PLAN` are already imported/defined in the file. Add:

```python
    def test_unquoted_off_coerces_to_off(self):
        # yaml.safe_load("handoff_spawn: off") -> False (YAML 1.1); model coerces to "off"
        data = {**MINIMAL_PLAN, "handoff_spawn": False}
        assert Plan.model_validate(data).handoff_spawn == "off"

    def test_bare_on_rejected_with_actionable_message(self):
        data = {**MINIMAL_PLAN, "handoff_spawn": True}
        with pytest.raises(ValidationError) as exc:
            Plan.model_validate(data)
        assert "on" in str(exc.value).lower()
```

(Quoted `"off"` and the `auto` default are already covered by the class's existing `test_accepts_ask_and_off` / `test_defaults_to_auto`.)

- [x] **Step 2: Run to verify failure**

Run: `.venv/bin/python3 -m pytest tests/unit/test_models/test_plan_model.py -k "unquoted_off or bare_on" -v`
Expected: `test_unquoted_off_coerces_to_off` FAILs (currently `False` is rejected by the Literal); `test_bare_on_rejected_with_actionable_message` currently raises but with a generic `literal_error` (no "on" text) — both go green after Step 3.

- [x] **Step 3: Add the validator**

In `skills/scripts/models/plan.py`, add to the `Plan` class (place with the other validators, after the field declarations):

```python
    @field_validator("handoff_spawn", mode="before")
    @classmethod
    def _coerce_yaml_bool_handoff_spawn(cls, v: object) -> object:
        # PyYAML (YAML 1.1) coerces unquoted `off`->False, `on`->True. The consent
        # opt-out is `off`, so accept the coerced False as "off". Reject True: bare
        # `on` is not a valid mode (and there is no "on" policy).
        if v is False:
            return "off"
        if v is True:
            raise ValueError(
                "handoff_spawn: bare `on` is YAML 1.1 True, not a valid mode. "
                "Use one of auto/ask/off (write `off` unquoted or quoted — both accepted)."
            )
        return v
```

(`field_validator` is already imported at `plan.py:5`.)

- [x] **Step 4: Run to verify pass**

Run: `.venv/bin/python3 -m pytest tests/unit/test_models/test_plan_model.py -k "unquoted_off or bare_on" -v`
Expected: all PASS.

- [x] **Step 5: Prove the gate layer (validators.py CLI)**

Add a subprocess test asserting the ACTUAL gate layer (Gate 1b runs `validators.py plan <file>` under this same venv python). Add it to `tests/unit/test_models/test_plan_model.py` (module-level functions are fine alongside the class). NOTE the path depth: this file lives at `tests/unit/test_models/`, so the repo root is **three** `..` up:

```python
import os, subprocess, sys, tempfile, textwrap

VALIDATORS = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "skills", "scripts", "models", "validators.py"
)

def _write_plan(tmp_path, handoff_line):
    body = textwrap.dedent(f"""\
        ---
        schema_version: 1
        feature_archetype: extension
        {handoff_line}
        tasks:
          - id: 0
            title: t
        ---
        # Plan
        ### Task 0: t
        - [ ] do it
        """)
    p = os.path.join(tmp_path, "plan.md")
    open(p, "w").write(body)
    return p

def test_validators_cli_accepts_unquoted_off(tmp_path):
    p = _write_plan(tmp_path, "handoff_spawn: off")  # unquoted -> False in YAML
    r = subprocess.run([sys.executable, VALIDATORS, "plan", p],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr

def test_validators_cli_rejects_bare_on(tmp_path):
    p = _write_plan(tmp_path, "handoff_spawn: on")
    r = subprocess.run([sys.executable, VALIDATORS, "plan", p],
                       capture_output=True, text=True)
    assert r.returncode == 1, r.stdout + r.stderr
```

Run: `.venv/bin/python3 -m pytest tests/unit/test_models/test_plan_model.py -k "unquoted_off or bare_on or validators_cli" -v` → all PASS.

- [x] **Step 6: Commit**

```bash
git add skills/scripts/models/plan.py tests/unit/test_models/test_plan_model.py
git commit -m "fix(n83): coerce unquoted handoff_spawn off->off, reject bare on (plan.py)"
```

---

### Task 2: sdd_session.py — `Handoff.spawn_policy` mode=before coercion validator

**Files:**
- Modify: `skills/scripts/models/sdd_session.py` (import line + `Handoff` class)
- Test: `tests/unit/test_models/test_sdd_session_model.py` (extend `TestHandoffBlock`)

**Pattern References:** same `@field_validator` idiom as Task 1.

- [x] **Step 1: Write the failing tests (extend the existing `TestHandoffBlock` class)**

Add to the existing `class TestHandoffBlock` in `tests/unit/test_models/test_sdd_session_model.py` (which already has `test_handoff_block_validates`, `test_spawn_policy_defaults_auto`, `test_spawn_policy_literal_is_closed_set`, `test_rejects_invalid_spawn_policy`). `Handoff`, `ValidationError`, and `pytest` are already imported. `Handoff` requires `expected_hops` (`ge=1`). Add:

```python
    def test_spawn_policy_unquoted_off_coerces_to_off(self):
        # YAML 1.1 unquoted `off` -> False; the Handoff validator coerces to "off"
        assert Handoff(expected_hops=1, spawn_policy=False).spawn_policy == "off"

    def test_spawn_policy_bare_on_rejected(self):
        with pytest.raises(ValidationError) as exc:
            Handoff(expected_hops=1, spawn_policy=True)
        assert "on" in str(exc.value).lower()
```

(Quoted `"off"` is already covered by `test_off_survives_*` / `test_handoff_block_validates`; the closed Literal and invalid-value rejection are already pinned.)

- [x] **Step 2: Run to verify failure**

Run: `.venv/bin/python3 -m pytest tests/unit/test_models/test_sdd_session_model.py -k "unquoted_off or bare_on" -v`
Expected: `test_spawn_policy_unquoted_off_coerces_to_off` FAILs.

- [x] **Step 3: Add the import and validator**

In `skills/scripts/models/sdd_session.py`, change the pydantic import (line 4) to include `field_validator`:

```python
from pydantic import Field, field_validator, model_validator
```

Add to the `Handoff` class (after the field declarations):

```python
    @field_validator("spawn_policy", mode="before")
    @classmethod
    def _coerce_yaml_bool_spawn_policy(cls, v: object) -> object:
        # Backstop for a manifest whose spawn_policy arrived as a YAML-1.1 bool
        # (unquoted off->False, on->True). materialize-manifest.py normalizes
        # False->"off" too; this guards direct construction and any bypass.
        if v is False:
            return "off"
        if v is True:
            raise ValueError(
                "spawn_policy: bare `on` is YAML 1.1 True, not a valid policy. "
                "Use one of auto/ask/off."
            )
        return v
```

- [x] **Step 4: Run to verify pass**

Run: `.venv/bin/python3 -m pytest tests/unit/test_models/test_sdd_session_model.py -k "unquoted_off or bare_on" -v`
Expected: all PASS.

- [x] **Step 5: Commit**

```bash
git add skills/scripts/models/sdd_session.py tests/unit/test_models/test_sdd_session_model.py
git commit -m "fix(n83): coerce unquoted spawn_policy off->off on Handoff (sdd_session.py)"
```

---

### Task 3: materialize-manifest.py — normalize False→off + cross-reader proof

**Files:**
- Modify: `skills/subagent-driven-development/scripts/materialize-manifest.py` (handoff block, lines ~117-122)
- Test: `tests/unit/test_materialize_manifest.py`

**Why materialize also normalizes:** materialize re-reads the raw plan frontmatter with PyYAML, independently of the Plan model, so it sees `False` for unquoted `off`. Without normalization it would write `false` into the manifest; the `Handoff` validator (Task 2) would then coerce it, but normalizing here keeps the stored value clean and is the load-bearing site now that Gate 1b passes and materialize actually runs.

- [ ] **Step 1: Flip the existing pre-fix test + add the coercion assertion (use the real `_mf` helper)**

`tests/unit/test_materialize_manifest.py` already has `class TestHandoffBlockMaterialization` with a helper `self._mf(ok=True, **kw)` (make_plan + run_materialize + cleanup) returning a dict with `["handoff"]["spawn_policy"]`, `["exit_code"]`, and `["stderr"]`. It already uses `extra_frontmatter="handoff_spawn: ask"`.

There is a **pre-fix test that asserts the buggy behavior as correct** and MUST be flipped:

```python
    def test_off_survives_and_bare_off_is_never_coerced_to_auto(self):   # YAML 1.1: bare off is False
        assert self._mf(extra_frontmatter='handoff_spawn: "off"')["handoff"]["spawn_policy"] == "off"
        r = self._mf(extra_frontmatter="handoff_spawn: off", ok=False)
        assert r["exit_code"] != 0 and "spawn_policy" in r["stderr"]
```

Rename it and flip the second assertion so unquoted `off` now **succeeds** and materializes to `"off"` (the N83 fix):

```python
    def test_bare_off_coerces_to_off_policy(self):   # N83: YAML 1.1 unquoted off (False) -> "off"
        # quoted "off" already worked
        assert self._mf(extra_frontmatter='handoff_spawn: "off"')["handoff"]["spawn_policy"] == "off"
        # unquoted off (parsed False) now normalizes to "off" instead of failing
        assert self._mf(extra_frontmatter="handoff_spawn: off")["handoff"]["spawn_policy"] == "off"
```

(The absent-default `auto` case is already covered by `test_manifest_gains_handoff_block`.)

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python3 -m pytest tests/unit/test_materialize_manifest.py -k "coerces_to_off or bare_off" -v`
Expected: `test_bare_off_coerces_to_off_policy` FAILs on the second assertion — materialize currently makes unquoted `off` (False) fail SddSession construction (`spawn_policy: False` rejected).

**Pre-execution audit note (Order 1):** because Pydantic runs nested-model field validators during parent construction, once Task 2's `Handoff` `mode="before"` validator has landed, `SddSession(handoff={"spawn_policy": False, ...})` already coerces to `"off"` on its own — this assertion may therefore **already PASS** before this task's own code change lands. That is expected and fine, not a TDD violation: Task 3's normalization in the handoff-block-building code is defense-in-depth (it protects the case where `handoff_spawn` reaches `SddSession` construction through a path other than this dict, e.g. a manually authored manifest), not the sole load-bearing site once Task 2 exists. If the assertion already passes, skip straight to Step 3, apply the normalization change anyway per this defense-in-depth rationale, and note in the task report that the test was already green pre-change rather than treating it as a broken red→green cycle.

- [ ] **Step 3: Normalize in the handoff block**

In `materialize-manifest.py`, change the handoff block (lines ~117-120) from:

```python
    spawn_policy = frontmatter.get("handoff_spawn")
    if spawn_policy is None:                 # NOT `or` — bare `off` is YAML 1.1 False
        spawn_policy = "auto"
```

to:

```python
    spawn_policy = frontmatter.get("handoff_spawn")
    if spawn_policy is None:                 # absent -> default
        spawn_policy = "auto"
    elif spawn_policy is False:              # unquoted `off` -> YAML 1.1 False
        spawn_policy = "off"
    # bare `on` (True) is rejected upstream by the Plan gate and the Handoff validator.
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python3 -m pytest tests/unit/test_materialize_manifest.py -k "coerces_to_off or bare_off" -v`
Expected: all PASS.

- [ ] **Step 5: Verify the script's reason=policy-off end-to-end (read-only check)**

Confirm `spawn-handoff-session.sh` already refuses with `reason=policy-off` when the manifest carries `spawn_policy=off` (Precondition 2b, line ~210-212). Grep for an existing test:

Run: `/usr/bin/grep -rn "reason=policy-off\|spawn_policy=off\|policy-off" tests/unit/`
Expected: an existing assertion in `test_spawn_handoff_v2.py` (or sibling). If NONE exists, add a bash-driven test using the `pytest-bash-stub-harness` (a manifest with `spawn_policy: off` → the script exits 3 and prints `reason=policy-off`). Do not duplicate an existing one.

- [ ] **Step 6: Run the full Module 1 test surface + commit**

Run: `.venv/bin/python3 -m pytest tests/unit/test_models/test_plan_model.py tests/unit/test_models/test_sdd_session_model.py tests/unit/test_materialize_manifest.py tests/unit/test_n83_yaml_contract.py -q`
Expected: all PASS.

```bash
git add skills/subagent-driven-development/scripts/materialize-manifest.py tests/unit/test_materialize_manifest.py
git commit -m "fix(n83): materialize normalizes unquoted off->off; per-reader proof (Task 3)"
```

## Acceptance Criteria (Module 1)

- [ ] `Plan(handoff_spawn=False)` → `"off"`; `Plan(handoff_spawn=True)` → `ValidationError` mentioning `on`; `"auto"/"ask"/"off"` unchanged; default `auto`.
- [ ] `Handoff(spawn_policy=False)` → `"off"`; `Handoff(spawn_policy=True)` → `ValidationError`.
- [ ] `validators.py plan <file>` exits 0 on unquoted `handoff_spawn: off`, exit 1 on `handoff_spawn: on`.
- [ ] `materialize-manifest.py` on an unquoted-`off` plan yields manifest `handoff.spawn_policy == "off"`; quoted `"off"` and absent (→`auto`) also correct.
- [ ] `spawn-handoff-session.sh` refuses with `reason=policy-off` for a `spawn_policy=off` manifest (verified; test present).
- [ ] `validate-plan.py` remains stdlib-only (no new pydantic import in its import chain).
