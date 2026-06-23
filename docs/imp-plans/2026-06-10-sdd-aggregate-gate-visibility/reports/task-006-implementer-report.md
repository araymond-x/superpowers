---
schema_version: 1
task_id: 6
task_type: implementation
status: DONE
files_changed:
  - path: "skills/subagent-driven-development/scripts/validate-plan.py"
    description: "Replaced _C2_RISK_PATTERNS (singular literals) with the N22 stem regex (auth\\w*|migrat\\w*|rout(?:e|er)\\w*|cach\\w*|middleware\\w*|cors\\b|securit\\w*); changed the lone .search() in check_integration_test_risk to scan _unfenced_content(content) (already-imported helper from Task 5). No new module-level imports — stays stdlib-only / bare-python3 runnable."
  - path: "tests/unit/test_c2_integration_gate.py"
    description: "D15 swap: removed the local _load_script + ROOT + dead `import importlib.util`, replaced with `from sdd_test_helpers import ROOT, _load_script` (ROOT also imported because line ~155 CHECKPOINT_SCRIPT consumes it). Added the _warns_risk helper + TestRiskSurfaceStemming (3 tests: inflected-forms-match, fenced-only-no-warn, declared-integration-test-suppresses)."
tests:
  written: 3
  passing: 3
  command: ".venv/bin/python3 -m pytest tests/unit/test_c2_integration_gate.py -v"
  result: PASS
contract_compliance:
  - constraint: "validate-plan.py stays runnable under SYSTEM python3 (bare-python3 gate) — add NO new module-level imports"
    status: compliant
    detail: "Change is regex + a call to the already-imported _unfenced_content (validate-plan.py:31, from Task 5). `python3 skills/subagent-driven-development/scripts/validate-plan.py --plan-file .../plan.md` (SYSTEM python3) emitted JSON status=PASS, not a traceback."
  - constraint: "Regression suite unchanged: 145 PASS / 3 advisory WARNING / 0 FAIL"
    status: compliant
    detail: "`python3 tests/ARaymond-skill-regression/validate-all-skills.py` → PASS: 145  FAIL: 0  WARNING: 3 (Result: PASS with warnings) — unchanged."
  - constraint: "Stem alignment: test words match the chosen stems; do NOT over-broaden to secur\\w*"
    status: compliant
    detail: "Regex uses securit\\w* (matches 'security', not 'securing') exactly as the plan NOTE prescribes; test words (migrations/caches/routers/authentication/security) are all aligned to their stems. No secur\\w* over-broadening introduced."
  - constraint: "The risk WARNING stays ADVISORY (appends to warnings; never blockers/FAIL)"
    status: compliant
    detail: "check_integration_test_risk still only appends to its local warnings list and returns it; the .search() target changed but the advisory contract is untouched. No FAIL/blocker path added."
  - constraint: "Fenced keywords must not warn — relies on Task 5's _unfenced_content blanking fenced lines"
    status: compliant
    detail: "Wired via `_C2_RISK_PATTERNS.search(_unfenced_content(content))`. test_fenced_only_keyword_does_not_warn (```\\nauth migration router\\n```) now passes; unfenced RISK_PLAN prose ('Add auth middleware') still warns (TestC2RiskSurfaceWarning green)."
  - constraint: "Write-scope: ONLY _C2_RISK_PATTERNS + the ONE .search() line in check_integration_test_risk; do NOT touch check_unclosed_fence (Task 5) or other functions; do NOT modify _report_utils.py / controller-checkpoint.py / sdd_test_helpers.py"
    status: compliant
    detail: "git show --stat of the commit lists exactly validate-plan.py (4 lines: 2 regex, 1 .search() target, plus the closing paren of the regex tuple) + test_c2_integration_gate.py. check_unclosed_fence untouched; no other files changed."
  - constraint: "D15: remove the now-dead `import importlib.util` after swapping to the hoisted loader"
    status: compliant
    detail: "Removed line 5 `import importlib.util`; post-edit `grep importlib tests/unit/test_c2_integration_gate.py` returns no matches. Live imports (json/os/subprocess/sys/pytest, `from plan import IntegrationTest, Plan`) retained."
---

**Implementation Summary:**
Implemented Task 6 (N22) per the module-2 plan's 6 steps. (1) D15 completion for the second duplicating file: removed `test_c2_integration_gate.py`'s local `_load_script`, `ROOT`, and the dead `import importlib.util`, replacing them with `from sdd_test_helpers import ROOT, _load_script`. Kept the `_vp = _load_script("validate_plan_c2", "validate-plan.py")` call site and the `CHECKPOINT_SCRIPT` line unchanged. Added the `_warns_risk` helper + `TestRiskSurfaceStemming` (3 tests) verbatim from the plan. (2) Confirmed RED — `test_inflected_forms_match` failed (singular patterns miss `migrations`/`authentication`/etc.) and `test_fenced_only_keyword_does_not_warn` failed (raw-content scan warned on fenced keywords); `test_declared_integration_test_suppresses` already passed (suppression logic pre-existed). (3) Replaced `_C2_RISK_PATTERNS` (lines 420-423) with the stem regex. (4) Changed the lone `.search()` in `check_integration_test_risk` (line 435) from `content` to `_unfenced_content(content)` — `_unfenced_content` was already imported at validate-plan.py:31 by Task 5, so no re-import. (5) Full `test_c2_integration_gate.py` green (25 passed — 3 new + all pre-existing C2/Check-10 tests, including RISK_PLAN's unfenced "Add auth middleware" still warning). (6) Committed with explicit paths (efc9204).

**Source Files Read:**
- `docs/imp-plans/2026-06-10-sdd-aggregate-gate-visibility/module-2-calibration.md` — Task 6's 6 steps + exact code blocks; verified dependency ordering after Task 5.
- `skills/subagent-driven-development/scripts/validate-plan.py` — confirmed the Task 5 import at line 31 (`_unfenced_content, ends_in_open_fence`), the `_C2_RISK_PATTERNS` definition (420-423), and the `.search()` call (435); confirmed `check_unclosed_fence` is Task 5's and out of scope.
- `tests/unit/test_c2_integration_gate.py` — confirmed `ROOT` is consumed at line ~155 (`CHECKPOINT_SCRIPT`), not only inside the local `_load_script`, so `ROOT` had to be imported too.
- `tests/unit/sdd_test_helpers.py` (READ-ONLY) — confirmed it exports both `ROOT` and `_load_script` (the D15 hoist landed in Task 5).
- `tests/unit/test_fence_aware_parsing.py` — reference for how Task 5 performed the equivalent D15 import swap (it imported only `_load_script` because that file has no other `ROOT` consumer; the difference drove the `ROOT, _load_script` import here).
- `skills/subagent-driven-development/scripts/_report_utils.py` (consumer reference, via grep) — confirmed `_unfenced_content` is the SSOT fence-blanking helper consumed.

**CLAUDE.md Files Read:**
- Repo-root `CLAUDE.md` — documents the C2 risk-surface WARNING (advisory; raw-content → now unfenced scan), validate-plan.py stdlib-only / bare-python3 gate requirement, and `_unfenced_content` SSOT in `_report_utils.py` (with its lazy `implementer_report` import keeping validate-plan.py stdlib-only).
- User global `~/.claude/CLAUDE.md` + rules (architectural-principles, coding-style) — TDD red-green, audit-all-callers, single-source-of-truth, automated-gate-FAILs-are-never-expected.

**Deviations from Plan:**
- Plan Step 1 says replace the local `_load_script` and `ROOT` with `from sdd_test_helpers import _load_script`. I imported **both** `ROOT` and `_load_script` (`from sdd_test_helpers import ROOT, _load_script`) because `ROOT` is also consumed at line ~155 (`CHECKPOINT_SCRIPT = os.path.join(ROOT, ...)`, used by the pre-existing `TestC2Check10`). Importing only `_load_script` would NameError there. The hoisted `sdd_test_helpers.ROOT` is the identical expression (`os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))`) resolving to the same path (both files live in `tests/unit/`), so this is the D15/SSOT-faithful fix for the plan's overlooked line-155 dependency. Confirmed with the advisor before editing. No other deviations.

**Self-Review Findings:**
- Verified the commit captured exactly the two owned files (`git show --stat efc9204`): validate-plan.py (4 lines) + test_c2_integration_gate.py (41 lines) — zero leakage into `_report_utils.py`, `controller-checkpoint.py`, or `sdd_test_helpers.py`.
- Verified `check_unclosed_fence` (Task 5's function) is untouched — only `_C2_RISK_PATTERNS` and the single `.search()` line in `check_integration_test_risk` changed.
- Verified the stem regex matches all 5 inflected test words and that `cors\b` (anchored) + `securit\w*` (not `secur\w*`) match the plan's exact intent — no over-broadening.
- Bare-SYSTEM-python3 check passed (JSON status=PASS, no traceback) — proves no non-stdlib import slipped in.
- Dead-import audit: post-edit `grep importlib` on the test file returns nothing; all other imports are live (`json`/`os`/`subprocess`/`sys` are used by the Check-10 harness; `pytest`, `plan` imports used).
- Regression suite 145/0/3 unchanged.

**Concerns:**
None. All three new tests pass (RED→GREEN demonstrated), all 25 tests in the file pass, both CRITICAL CONSTRAINTS (bare-python3 JSON output, regression suite 145/0/3) are satisfied, and the write-scope boundary held. Status DONE.
