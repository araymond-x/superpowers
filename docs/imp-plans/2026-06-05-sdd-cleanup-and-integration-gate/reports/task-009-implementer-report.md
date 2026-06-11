---
schema_version: 1
task_id: 9
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/subagent-driven-development/scripts/_report_utils.py"
    description: "0a: eager implementer_report import replaced with PEP 562 module __getattr__ (lazy VALID_STATUSES resolution, cached) — importing _unfenced_content no longer pulls pydantic"
  - path: "skills/scripts/models/plan.py"
    description: "0b: IntegrationTest path validator rejects empty/whitespace-only paths first"
  - path: "tests/unit/test_c2_integration_gate.py"
    description: "0b pin tests (empty, bare '..'); 0c sys.path removal + module-level imports; Task 9 TestC2RiskSurfaceWarning (3 tests) with copied _load_script loader"
  - path: "skills/subagent-driven-development/scripts/validate-plan.py"
    description: "_C2_RISK_PATTERNS + check_integration_test_risk wired into validate_plan() after the verification keyword heuristic, reusing the parsed frontmatter dict"
tests:
  written: 5
  passing: 5
  command: ".venv/bin/python3 -m pytest tests/unit/ -q -> 446 passed; python3 tests/ARaymond-skill-regression/validate-all-skills.py -> 145 PASS / 0 FAIL / 3 advisory WARNING"
  result: PASS
contract_compliance:
  - constraint: "None"
    status: not_applicable
    detail: "No external contract dependencies"
---

> Controller note: frontmatter normalized on save (files_changed path+description structure,
> tests.result) per the logged mechanical-correction precedent.

## Implementation Summary

Two commits as prescribed:

**Commit 1 (`2db2171`) — Step 0 fold-ins:**
- **0a**: Replaced `_report_utils.py`'s eager `from implementer_report import Status` with a PEP 562 module `__getattr__` that lazily resolves `VALID_STATUSES` on first access (cached via `globals()`). Verified with the plan's one-liner: bare `python3` loads validate-plan.py with `'pydantic' not in sys.modules` → **0a OK**. All three consumer patterns verified: `_mod.VALID_STATUSES` attribute access (extract-execution-trace.py), `from _report_utils import VALID_STATUSES`, and AttributeError for unknown attrs. controller-checkpoint.py and validate-report.py import only `_unfenced_content`/`validate_report_sections` — full suite confirms.
- **0b**: `IntegrationTest.path_must_be_relative_and_safe` rejects empty/whitespace-only paths first ("integration_test path must not be empty"). Pin tests: empty string rejected, bare ".." rejected.
- **0c**: Removed redundant module-level sys.path.insert (conftest covers it), hoisted `from plan import IntegrationTest, Plan` to module level. All 7 model tests green.

**Commit 2 (`14e5906`) — C2 feature (TDD):** `_C2_RISK_PATTERNS` + `check_integration_test_risk(content, frontmatter)` per the plan's prescribed code (annotation style adapted), wired into `validate_plan()` after the verification keyword heuristic, reusing the same parsed `frontmatter` dict (no re-parse). Tests: `_load_script` copied verbatim from test_fence_aware_parsing.py L14-22, loaded as `validate_plan_c2`; `_H` self-hosting guard as prescribed. RED confirmed, GREEN after.

**Self-hosting verification:** bare-python3 `validate-plan.py --plan-file module-2-integration-gate.md` → **exit 2, status WARNING, blockers [], exactly one warning: `integration_test_risk_surface`**. The warning fires on our own plan (raw-content scan includes fenced code; the prescribed regex block contains "auth"/"middleware"). Per instructions: did NOT silence via frontmatter, did NOT make the scan fence-aware. Gate keys on FAIL → live gate unaffected.

## Source Files Read
validate-plan.py (fully, 793 lines), _report_utils.py (fully), plan.py (model region), test_c2_integration_gate.py, test_fence_aware_parsing.py (loader), test_validate_plan.py conventions, conftest.py, extract-execution-trace.py (VALID_STATUSES consumer), validate-all-skills.py, module-2-integration-gate.md Task 9.

## CLAUDE.md Files Read
Repo-root CLAUDE.md (Pipeline Flexibility + Pydantic Validation). No CLAUDE.md in modified dirs.

## Deviations from Plan
1. **Test loading via `_load_script`** (pre-approved partner correction): the plan's `from validate_plan import validate_plan` cannot work (hyphenated filename); per-file loader convention used; the plan snippet's superseded SCRIPTS/sys.path lines dropped.
2. **Type annotations adapted**: prescribed `dict | None`/`list[str]` → `Optional[Dict]`/`List[str]` matching validate-plan.py's Python 3.9 compat style.
3. **0a as the "accessor" option** (module `__getattr__`) rather than function-local import — `VALID_STATUSES` is consumed via `_mod.VALID_STATUSES` attribute access in extract-execution-trace.py; a named-function move would have broken that caller.

## Self-Review Findings
- The new heuristic appends to `warnings` only — no `sections` entry, matching the plan's prescription exactly, though the two neighboring heuristics set sections entries. Deliberate fidelity choice; flag if reviewers want parity.
- `re` already imported; `routes/` alternative's `\b` behavior confirmed via passing tests.
- Full suite 446 passed (441 baseline + 2 pin + 3 C2). Regression 145/0/3-advisory.

## Concerns
- **Our own module-2 plan now emits `integration_test_risk_surface`** (exit 2 WARNING) via the live gate. Acceptable (advisory; gate keys on FAIL); controller must log in deviations.md. module-1 likely warns too ("migration"/"auth" wording) — same advisory class.
- The raw-content scan (fenced code included) means any plan merely QUOTING these keywords in code blocks warns — inherent to the prescribed design; noted, not changed.
