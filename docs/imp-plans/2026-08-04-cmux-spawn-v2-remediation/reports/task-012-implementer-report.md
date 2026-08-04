---
schema_version: 1
task_id: 12
task_type: implementation
status: DONE
files_changed:
  - path: "skills/subagent-driven-development/scripts/write-mechanics-card.py"
    description: "Added `import re`; validated SUPERPOWERS_CMUX_MAX_HOPS against ^[0-9]+$ (else falls back to hop_ceiling(expected)), matching spawn-handoff-session.sh's validation; replaced literal '$PYTHON' in the standalone regen-line with {sys.executable}, matching the checkpoint invocation lines in the same card."
  - path: "tests/unit/test_mechanics_card.py"
    description: "Extended _run_card(wt, feat) with an env_extra=None parameter merged in after the ambient SUPERPOWERS_CMUX_* strip; added test_card_regen_line_uses_real_interpreter and test_card_ceiling_validates_max_hops."
tests:
  written: 2
  passing: 9
  command: ".venv/bin/python3 -m pytest tests/unit/ -k \"card\" -q"
  result: PASS
contract_compliance:
  - constraint: "write-mechanics-card.py is NOT baselined — no baseline recapture needed"
    status: compliant
    detail: "Confirmed via tests/ARaymond-hook-baseline/baseline.txt scope; not touched, no recapture performed."
  - constraint: "N85: card display must match the script — {sys.executable} (not literal $PYTHON) and the script's validated MAX_HOPS value (numeric-or-derived-default)"
    status: compliant
    detail: "Regen line now uses {sys.executable}; ceiling now validated via re.fullmatch(r\"[0-9]+\", ...) before use, else hop_ceiling(expected)."
  - constraint: "Do not modify tests/integration/sdd-e2e-test.sh (satisfied by Task 13)"
    status: compliant
    detail: "Not touched."
---

**Implementation Summary:**
Fixed two display-consistency bugs in `write-mechanics-card.py`: the standalone regen-line now interpolates `sys.executable` instead of the literal string `$PYTHON`, matching the checkpoint invocation lines already in the same generated card; and the `ceiling` value now validates `SUPERPOWERS_CMUX_MAX_HOPS` as `^[0-9]+$` before using it (falling back to the derived default otherwise), mirroring `spawn-handoff-session.sh`'s existing validation of that same env var.

**Source Files Read:**
- `skills/subagent-driven-development/scripts/write-mechanics-card.py` — confirmed the ceiling line (`os.environ.get("SUPERPOWERS_CMUX_MAX_HOPS") or hop_ceiling(expected)`) and the regen-line f-string using literal `$PYTHON`, while the checkpoint invocation lines a few lines below already use `{sys.executable}`.
- `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` — confirmed the validation pattern: `[[ "$SUPERPOWERS_CMUX_MAX_HOPS" =~ ^[0-9]+$ ]]`, else warn and revert to derived default.
- `tests/unit/test_mechanics_card.py` — read in full; confirmed `_run_card(wt, feat)` strips all `SUPERPOWERS_CMUX_*` env vars before every existing call, and that the fixture manifest sets `expected_hops: 2` (derived ceiling = 6, per `hop_ceiling`).

**CLAUDE.md Files Read:**
None found in `skills/subagent-driven-development/` or `tests/` directories.

**Deviations from Plan:**
- The plan's illustrative pseudocode asserted `sys.executable in card` directly. In practice `VENV_PY` (the worktree's `.venv/bin/python3`) is a symlink to the main checkout's venv, and Python's own `sys.executable` resolves one level of that symlink — so the value embedded in the card differs from the raw `VENV_PY` string used to invoke the subprocess. Fixed the test to compute the expected value by actually running `VENV_PY -c "import sys; print(sys.executable)"` and asserting that resolved string appears in the card, rather than hardcoding either the symlink path or a naive `os.path.realpath()` (which over-resolved through a second-level Homebrew symlink chain and did not match what the script's own `sys.executable` reports).

**Self-Review Findings:**
- Initial test assertion (`VENV_PY in card`) failed because of the symlink-resolution mismatch described above; corrected by deriving the expected interpreter path the same way the script itself does, rather than assuming the invoking path is preserved verbatim.
- Removed an unused `import sys` initially added to the test file after realizing the interpreter path needed to come from a subprocess call, not `sys.executable` of the test-runner process itself.

**Concerns:**
No concerns. Full unit suite (868 tests, includes the 9 card tests) passes; commit `65ae978` is clean with only the two intended files changed.
