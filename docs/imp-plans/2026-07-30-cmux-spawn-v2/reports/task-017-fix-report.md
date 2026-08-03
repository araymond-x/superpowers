---
schema_version: 1
task_id: 17
task_type: implementation
status: DONE
files_changed:
  - path: "tests/integration/sdd-e2e-test.sh"
    description: "Step 14 cmux stub: corrected list-pane-surfaces/workspace-create comment to clarify these are the workspace-fallback topology never reached by this e2e's three sub-runs (all take the new-surface success path), retained for test-double fidelity and covered by the unit suite instead. Anchored the new-surface flag assertion to a single grep pinned to the new-surface line and the script's actual emission order (--workspace, --type terminal, --working-directory, --focus false), replacing two separate un-anchored greps."
tests:
  written: 0
  passing: 0
  command: "bash tests/integration/sdd-e2e-test.sh"
  result: PASS
contract_compliance:
  - constraint: "quality review Important #1 (comment accuracy) + Minor #2 (anchored assertion) addressed; stub fidelity preserved"
    status: compliant
    detail: "Comment rewritten to state the fallback verbs are unreached by Step 14, kept for fidelity, and unit-tested elsewhere; no change to stub output (printf lines identical). Assertion combined into one anchored grep matching the verified script emission order; no --working-directory assertion added. Bash 3.2 style preserved, no set -u/-e/pipefail added."
---

**Implementation Summary** — `[task 17 fix]` commit `800000e`. Two comment/assertion-only edits in `tests/integration/sdd-e2e-test.sh`, Step 14's cmux stub block:

1. Rewrote the comment above the `list-pane-surfaces)` arm to state explicitly that `list-pane-surfaces` and `workspace create` are the workspace-fallback topology this e2e's three sub-runs never reach (all take the `new-surface` success path), that the `* ` marker is kept in its frozen shape purely for test-double fidelity (not because Step 14 asserts against it), and that the fallback marker-parser is exercised by the unit suite (`tests/unit/spawn_handoff_helpers.py`), not here. Stub output (`printf` lines) byte-identical to before.
2. Replaced the two separate un-anchored asserts with a single grep anchored to the start of the `new-surface` line: `grep -q "^new-surface .*--workspace TEST-WS .*--type terminal .*--focus false" "$SPAWN_WORK/cmux.log"`, matching the script's real flag order. No `--working-directory` assertion added.

**Source Files Read** — `spawn-handoff-session.sh` `create_surface_target()`: `capture_cmux_ref surface cmux new-surface --workspace "$CMUX_WORKSPACE_ID" --type terminal --working-directory "$WORKTREE_ROOT" --focus false` — confirmed emission order `--workspace`, `--type terminal`, `--working-directory <path>`, `--focus false`. Chose the `.*`-separated pattern (skipping over `--working-directory`) so it matches the required-flag subset in the real relative order.

**CLAUDE.md Files Read** — repo-root `CLAUDE.md` (bash-3.2 floor, e2e conventions, `/usr/bin/grep` guidance).

**Deviations from Plan** — None. Both changes scoped exactly as specified; no other Step or file touched.

**Self-Review Findings** — Verified stub `printf` output lines untouched (diff shows only comment + assertion lines). `git commit -- tests/integration/sdd-e2e-test.sh` excluded unrelated SDD bookkeeping artifacts from the commit.

**Concerns** — None. Full suite: `E2E PIPELINE PASS - 15 steps composed correctly`, Step 14a/14b/14c all PASS.

_(Controller note: the quality reviewer's alternative suggestion to trim the two fallback stub verbs to bare `echo OK` was DECLINED — the verbs are legitimate test-double fidelity mirrors of `_CMUX_V2_STUB`; keeping their frozen shapes means the double stays faithful if a future script change routes through the fallback. The misleading COMMENT was the actual defect and was fixed; the fidelity was preserved. See deviations.md.)_
