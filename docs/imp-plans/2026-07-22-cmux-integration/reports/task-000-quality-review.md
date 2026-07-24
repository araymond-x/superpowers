# Code Quality Review — Task 0 (cmux-integration, module-1-spawn-script)

**Scope:** `tests/unit/fixtures/spawn-handoff/*.json`, `tests/unit/spawn_handoff_helpers.py`, `tests/unit/test_spawn_handoff.py`
**Base:** `2f8340c` **Head:** `56210f1`

## Strengths

- **Harness mirrors the established convention closely.** `spawn_handoff_helpers.py` follows the same shape as `tests/unit/sdd_test_helpers.py` and the stub-on-PATH subprocess pattern used by `test_context_gate_tier.py`'s `run_hook`: build per-test executable stubs under a tmp `stubs/` dir, prepend to `PATH`, isolate `HOME`, run the real script via `subprocess.run`. No novel pattern was invented where an existing one applied.
- **Fixtures are minimal and single-variable.** Each invalid fixture (`wrong-type`, `wrong-skill`, `foreign-repo`) changes exactly one field from `valid-manifest.json`, which keeps the eventual test matrix easy to reason about (isolates one precondition failure per fixture). All four parse as valid JSON and match the plan's verbatim spec.
- **`__REPO_ID__` sentinel handling is correct and consistent.** `install_bundle` only substitutes the sentinel when present; `foreign-repo-manifest.json` correctly uses a literal, never-matching path instead of the sentinel, so it stays a foreign repo regardless of the calling test's actual `repo_id`.
- **No unused imports, no unreachable branches, no commented-out code** in either `.py` file.
- **The "unused for now" symbols are legitimately not dead code.** `install_version`, `PACE_MISSING_WINDOW`, `PACE_NONZERO`, `encode_args`, `CMUX_NOTIFY_FLAGS`, `PICKER_CONTRACT_VERSION` are all unreferenced by Task 0's own test, but the plan explicitly front-loads the full harness/contract-constant surface in Task 0 so Tasks 1–6 never mutate the harness — consistent with the brief, not a violation.
- **Verified independently:** ran `.venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -v` (1/1 PASS) and the full `tests/unit/` suite (554/554 PASS, no regressions). All 4 fixture files independently re-parsed as valid JSON.
- **The reported deviation (background-formatter reformat) is accurately characterized.** Diffing the committed file against the plan's verbatim code block confirms the changes are pure line-wrapping/whitespace — identifiers, string literals (including the tricky escaped-quote `PACE_*` strings), and control flow are byte-identical in substance. Nothing is left mid-expression or syntactically broken; both files import and execute cleanly.

## Issues

### Critical (Must Fix)
None.

### Important (Should Fix)
None.

### Minor (Nice to Have)

1. **Reformatted files now use a different line-wrapping style than their siblings.**
   - Files: `tests/unit/spawn_handoff_helpers.py`, `tests/unit/test_spawn_handoff.py`
   - The uncontrolled background formatter wrapped calls/lists to a ~88-char (black-like) width. The repo has no `pyproject.toml`/`.flake8`/black or ruff config, and the sibling files these two are patterned on (`tests/unit/sdd_test_helpers.py`, `tests/unit/test_context_gate_tier.py`) use a denser, largely-unwrapped style (single lines up to 170–190 chars). The result is a visible style seam between the new files and the rest of `tests/unit/`.
   - Why it matters: purely cosmetic — it doesn't affect readability or correctness, and PEP 8-narrower lines are arguably *more* readable in isolation. Flagging only because (a) it wasn't an intentional style choice, and (b) if the same background formatter doesn't consistently re-run during Tasks 1–6, the file could end up with a visible internal seam (early wrapped sections vs. later dense-style appends copied verbatim from the plan).
   - Suggested fix: no action required now. If Tasks 1–6 notice new appends look stylistically inconsistent with the existing (wrapped) top of the file, either reformat the whole file once or accept the mix — either is fine for a test-only harness. Not worth blocking on.

2. **`spawn_handoff_helpers.py` module docstring is terser than its sibling's.**
   - File: `tests/unit/spawn_handoff_helpers.py:1`
   - `"""Harness for spawn-handoff-session.sh subprocess tests."""` vs. `sdd_test_helpers.py`'s multi-line docstring describing what it provides. Not a real gap — the file is short and self-explanatory — but a one-line addition naming the exposed helpers (`setup_worktree`, `install_bundle`, `install_version`, `run_spawn`, `PACE_*`) would match house style if anyone revisits this file.

## Recommendations

- None beyond the Minor items above — this is a clean, narrowly-scoped Task 0.

## Assessment

**Ready to merge?** Yes

**Reasoning:** The harness and fixtures are a faithful, well-verified transcription of the frozen contracts with no dead code, no unused-but-actually-dead symbols, and no functional issues. The only finding is a cosmetic line-wrapping divergence from sibling test files caused by an out-of-repo background formatter — already transparently disclosed by the implementer, verified non-breaking, and not worth blocking Task 1.
