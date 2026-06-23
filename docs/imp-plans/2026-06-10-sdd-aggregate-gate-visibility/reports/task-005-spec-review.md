# Task 5 (N20) — Spec Compliance Review

**Verdict: PASS** — spec- and contract-compliant. Verified by reading the diff (ae05d8a..a8a76cf), the source, and running tests/suites.

## Spec match (step-by-step)
- **Step 1:** `TestFenceHelperEdges` added with the exact 5 tests (test_fence_aware_parsing.py:104-140).
- **Step 2 (RED):** genuine — base `_report_utils.py` (ae05d8a) has zero `ends_in_open_fence` and no tilde/`fence_char` handling.
- **Step 3:** `_FENCE_RE = re.compile(r"^([\`~]{3,})")`; `_fence_marker` returns the marker char; `_unfenced_content` tracks `fence_char` and closes ONLY on the same marker type (`if marker == fence_char`); unclosed blanks to EOF; `ends_in_open_fence` shares the `_fence_marker` primitive (not duplicated regex).
- **Step 4:** import extended (line 31); `check_unclosed_fence` (:446) returns the advisory WARNING when `ends_in_open_fence(content)`, wired at :730-734 (`sections["unclosed_fence"]=WARNING`). `_C2_RISK_PATTERNS` + `check_integration_test_risk` body UNTOUCHED (Task 6 scope) — no ± lines there.
- **Step 5 (D15):** `sdd_test_helpers.py` gained `import importlib.util`+`ROOT`+`_load_script` (verbatim docstring); `test_fence_aware_parsing.py` imports it, dropped local def, `_vp`/`_ckpt` still load. `test_c2_integration_gate.py` NOT in diff.
- **Steps 6-7:** tests pass; exactly the 4 named files committed.

## Contract constraints — all confirmed
1. **3.9-safe type comment:** `_fence_marker(line):` + `# type: (str) -> Optional[str]` (:64-65). PEP-604 union scan over both helper files: NONE.
2. **stdlib-only (both files):** `_report_utils.py` imports = re/sys/pathlib only; `validate-plan.py` adds no new non-stdlib import. Both runnable under bare python3.
3. **Line-count preserved:** verified empirically across 5 cases (incl. no-trailing-newline) — input lines == output lines.
4. **own-marker closing:** `test_backtick_not_closed_by_tilde` PASSES; `~~~` inside ``` stays blanked, only ``` closes.

## Tests / suites
- TestFenceHelperEdges: 5/5 PASS. test_fence_aware_parsing.py: 12/12 PASS. Full unit suite: 483 passed. Regression: 145 PASS / 0 FAIL / 3 advisory WARNING (unchanged — no Category-8/PEP-604 leak). Report validates clean (exit 0).

## Dead-import deviation — safe
`import re` genuinely dead before this task (post-commit `\bre\.` grep → zero usages). Removal (one beyond plan-named importlib.util/os) is a safe cleanup, disclosed in Deviations. `argparse` correctly retained.

## Scope
Exactly 4 files committed; no stray edits; untracked plan/reports preserved.

## Concern (non-blocking, accurately self-reported)
`check_unclosed_fence` is a raw-content scan → a plan with an intentionally-unclosed final fence would warn, but it's advisory-only (WARNING, never FAIL), consistent with the C2 risk-surface posture and the plan's design ("close the fence"). No enforcement impact.

No BLOCKING/CONTRACT/MISSING findings.
