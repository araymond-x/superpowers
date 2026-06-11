# Partner Review — Task 9 (C2 risk-surface WARNING + Step 0 fold-ins) Dispatch

Three rounds, all dispatched 2026-06-10 (haiku, provenance in .dispatch-log).

## Round 1: BLOCKED
- Verified: Step 0a feasible (implementer_report imported at _report_utils.py:20); frontmatter
  parsed at validate-plan.py ~L493-502 and shared with both existing heuristics (SSOT pass-point
  feasible); new risk heuristic orthogonal to verification-keyword heuristic (no duplication);
  plan body does NOT self-trigger the new WARNING; deviations clean.
- Findings: (1) CRITICAL — prescribed test code `from validate_plan import validate_plan`
  cannot work (hyphenated filename); dispatch must prescribe the exact working load pattern.
  (2) Verify frontmatter pass point. (3) Clarify Step 0c semantics.

## Round 2: BLOCKED (one residual)
- Remediations A (importlib `_load_script` pattern from test_fence_aware_parsing.py; direct
  function call; `result['warnings']` semantics), B (pass the same frontmatter dict, call site
  after verification-keyword check ~L665), C (drop sys.path block — conftest covers it; hoist
  imports; re-run the 5 model tests as 0c verification) — all verified accurate against code.
- Residual: "copy OR import-share" phrasing ambiguous — must prescribe ONE pattern.

## Round 3: APPROVED
- Final wording: COPY `_load_script` verbatim into the test file; module name
  `validate_plan_c2`; do NOT cross-import or use conftest — per-file local loader is the
  established convention (test_fence_aware_parsing.py + test_n9_plan_loading_helpers.py
  verified both define their own).
- Collision-safety verified: spec_from_file_location does not register in sys.modules;
  distinct module names; zero collision risk. Zero remaining path to the broken direct import.

**Final Status: APPROVED**
