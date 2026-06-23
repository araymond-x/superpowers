---
schema_version: 1
task_id: 5
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/subagent-driven-development/scripts/_report_utils.py"
    description: "Rewrote _unfenced_content to recognize ~~~ fences with own-marker-type closing and unclosed-to-EOF semantics; added _FENCE_RE, _fence_marker (3.9-safe type comment), and ends_in_open_fence."
  - path: "skills/subagent-driven-development/scripts/validate-plan.py"
    description: "Extended the _report_utils import to also pull ends_in_open_fence; added check_unclosed_fence (advisory WARNING); wired it into the main validation flow next to check_integration_test_risk."
  - path: "tests/unit/sdd_test_helpers.py"
    description: "D15 hoist: added importlib.util import, ROOT constant, and the shared _load_script importlib loader (single source of truth)."
  - path: "tests/unit/test_fence_aware_parsing.py"
    description: "Added TestFenceHelperEdges (5 N20 characterization tests); replaced the local ROOT/_load_script with an import from sdd_test_helpers; removed now-dead imports (importlib.util, os) and the pre-existing-dead re import."
tests:
  written: 5
  passing: 5
  command: ".venv/bin/python3 -m pytest tests/unit/test_fence_aware_parsing.py tests/unit/test_validate_plan.py -v"
  result: PASS
contract_compliance:
  - constraint: "_fence_marker uses 3.9-safe `# type: (str) -> Optional[str]` comment, NOT PEP-604 `-> str | None`"
    status: compliant
    detail: "Used the plan's verbatim form. Regression suite (Category-8 scanner) ran 145 PASS / 0 FAIL / 3 WARNING unchanged — no PEP-604 leak. Did NOT add `from typing import Optional` (the comment is never evaluated)."
  - constraint: "_report_utils.py and validate-plan.py remain stdlib-only / runnable under system python3 (gate runs validate-plan.py with bare python3)"
    status: compliant
    detail: "Check (a): `python3 -c 'from _report_utils import _unfenced_content, ends_in_open_fence'` → 'report_utils stdlib OK'. Check (b): `python3 validate-plan.py --plan-file .../plan.md` → JSON status PASS. New code uses only re (already imported)."
  - constraint: "Preserve _unfenced_content line-count invariant (blank-line substitution, keepends)"
    status: compliant
    detail: "Every input line yields exactly one output line (either the original or '\\n'); splitlines(keepends=True) preserved."
  - constraint: "Unclosed-fence-to-EOF is a deliberate characterization — pin it, do not 'fix' it"
    status: compliant
    detail: "test_unclosed_fence_blanks_to_eof pins the behavior; ends_in_open_fence reports the open state. Both pass."
  - constraint: "Write-scope: only the 4 owned files; do NOT touch _C2_RISK_PATTERNS / check_integration_test_risk body (Task 6), controller-checkpoint.py, or test_c2_integration_gate.py (Task 6 owns its loader)"
    status: compliant
    detail: "validate-plan.py edits limited to the import line + new check_unclosed_fence + its wiring. _C2_RISK_PATTERNS and check_integration_test_risk's body untouched. test_c2_integration_gate.py and controller-checkpoint.py not modified."
  - constraint: "Hoist _load_script docstring kept verbatim (documents full D15 scope)"
    status: compliant
    detail: "Kept the verbatim 'previously duplicated in test_fence_aware_parsing.py and test_c2_integration_gate.py' line unchanged."
  - constraint: "Remove now-unused imports from test_fence_aware_parsing.py"
    status: compliant
    detail: "Removed importlib.util and os (made dead by the hoist) plus the pre-existing-dead re. argparse (line 95) and pytest left in place — see Deviations."
---

**Implementation Summary:**
Implemented Task 5 (N20) per the module-2 plan's 7 steps with the verbatim code blocks. (1) Added `TestFenceHelperEdges` — 5 failing characterization tests for tilde fences, own-marker-type closing, unclosed-to-EOF blanking, and the new `ends_in_open_fence` detector. (2) Confirmed RED (3 failed: `~~~` unrecognized + `ends_in_open_fence` absent; 2 backtick-path tests passed under the old impl, as expected). (3) Rewrote `_unfenced_content` in `_report_utils.py` to track a `fence_char` (None / '`' / '~') so a fence closes only on its own marker type, recognize `~~~`, and blank an unclosed fence to EOF; added `_FENCE_RE`, `_fence_marker` (with the 3.9-safe `# type:` comment), and `ends_in_open_fence` sharing the same primitive. (4) Extended the `validate-plan.py` import to pull `ends_in_open_fence`, added `check_unclosed_fence` (advisory WARNING), and wired it into the main flow next to `check_integration_test_risk`. (5) D15 hoist: added the shared `_load_script` (+ `ROOT`, `import importlib.util`) to `sdd_test_helpers.py` and switched `test_fence_aware_parsing.py` to import it. (6) Full touched suites green (41 passed). (7) Committed with explicit paths.

All critical verifications passed: both system-`python3` stdlib checks (report_utils import OK; validate-plan JSON status PASS), the regression suite (145 PASS / 0 FAIL / 3 advisory WARNING — unchanged, confirming no PEP-604/Category-8 leak), `py_compile` of all 4 files, and the full unit suite (483 passed).

**Source Files Read:**
- docs/imp-plans/2026-06-10-sdd-aggregate-gate-visibility/module-2-calibration.md (Task 5, lines 135-326)
- skills/subagent-driven-development/scripts/_report_utils.py (the `_unfenced_content` body + the lazy `implementer_report` `__getattr__`)
- skills/subagent-driven-development/scripts/validate-plan.py (import line 31; `_C2_RISK_PATTERNS` / `check_integration_test_risk` ~416-443; main-flow wiring ~685-712)
- tests/unit/sdd_test_helpers.py (import block + manifest/workspace helpers)
- tests/unit/test_fence_aware_parsing.py (existing characterization classes + local loader)

**CLAUDE.md Files Read:**
- Repo-root CLAUDE.md — confirmed `_report_utils.py`'s lazy `implementer_report` import / stdlib-only requirement, that validate-plan.py is stdlib-only (the plan-validation gate invokes it with bare python3), and that `_unfenced_content` is the SSOT fence helper imported by validate-plan.py + controller-checkpoint.py (N5).
- (No subdirectory CLAUDE.md exists under skills/subagent-driven-development/scripts/ or tests/unit/.)

**Deviations from Plan:**
1. Removed the pre-existing-dead `import re` from `test_fence_aware_parsing.py` (in addition to the `importlib.util` and `os` imports the plan named). `re` had only one occurrence (its own import line, confirmed by grep) and was already unused before this task; the hoist did not create that deadness, but leaving it would be flagged by the quality reviewer for the same reason the plan removes the others. One-beyond-the-two-named cleanup, flagged here for transparency. (`argparse` and `pytest` were left untouched — `argparse` is live at line 95; `pytest` is a pre-existing conventional import not made dead by this task and out of scope.)

**Self-Review Findings:**
- Line-count invariant verified by inspection: every branch appends exactly one element per input line. The `test_unclosed_fence_blanks_to_eof` and existing fence-aware checkpoint/validate tests (which depend on header line positions) all pass, confirming spans stay valid.
- The new in-method `from _report_utils import ...` calls in the tests resolve because `_vp = _load_script(...)` runs at module import and side-effect-inserts the scripts dir onto sys.path (validate-plan.py:30) — header ordering (`from sdd_test_helpers import _load_script` above the `_vp`/`_ckpt` lines) preserved, and `_vp`/`_ckpt` left unchanged.
- `_fence_marker` uses `line.strip()` so indented fences and trailing whitespace are handled; `_FENCE_RE` requires >=3 of `` ` `` or `~` at start (after strip), matching CommonMark fence-length rules at the minimum.

**Concerns:**
- `check_unclosed_fence` does a raw-content scan via `ends_in_open_fence`, so a plan whose LAST fenced block is intentionally an unclosed example (rare) would warn — but it is advisory-only (WARNING, never FAIL), consistent with the existing C2 risk-surface heuristic's raw-scan posture. Observed in passing: `module-2-calibration.md` itself, if validated, would emit this WARNING because it quotes many ` ``` ` code blocks (the final one in Task 14's region is the relevant edge); this is the gate target plan.md, which is clean (status PASS), so no enforcement impact. Status DONE_WITH_CONCERNS solely to surface the one-beyond `re` cleanup deviation and this advisory-scan note; no blockers.
