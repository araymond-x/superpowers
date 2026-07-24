---
schema_version: 1
task_id: 2
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/subagent-driven-development/scripts/spawn-handoff-session.sh"
    description: "Replaced Task-2 marker with validate_bundle() (charset/containment/manifest/type/skill/repo-identity checks via git-common-dir), cmux-reachable precondition, and hop-limit precondition (defines SP_HOP)."
  - path: "tests/unit/test_spawn_handoff.py"
    description: "Appended Task-2 test block (bundle validation failures, missing bundle dir, not-in-cmux, ping failure, hop limit); added a commit step in test_hop_limit_exits_3 to keep the fixture faithful to the tracked-.handoff-hops invariant."
tests:
  written: 8
  passing: 8
  command: ".venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -v"
  result: PASS
contract_compliance:
  - constraint: "Repo identity = realpath(git rev-parse --git-common-dir), not --show-toplevel"
    status: compliant
    detail: "validate_bundle()'s active_id computation uses a python heredoc that runs `git rev-parse --git-common-dir` and os.path.realpath, exactly mirroring the pickup guard's repo_identity(). The pre-existing --show-toplevel at line 44 is unrelated Task-1 code (cd/feature-dir resolution only)."
---

**Implementation Summary:** Appended 5 test functions (8 test cases incl. parametrization) to `test_spawn_handoff.py` covering bundle validation failures, missing bundle dir, cmux unreachability, ping failure, and hop-limit exit. Replaced the Task-2 marker in `spawn-handoff-session.sh` with the verbatim `validate_bundle()` function (charset, containment, manifest field checks, worktree-invariant repo-identity via `git rev-parse --git-common-dir` + `os.path.realpath`), the cmux-reachability precondition, and the hop-limit precondition (with `SP_HOP` defined for later tasks). Full file total after this task: 14/14 tests passing.

**Source Files Read:** `spawn-handoff-session.sh` (Task 1 skeleton, config vars, markers), `spawn_handoff_helpers.py` (harness knobs), `test_spawn_handoff.py` (existing tests/imports), `module-1-spawn-script.md` Task 2 section (verbatim spec text), `sdd-pre-dispatch-hook.sh` (bash house style — no `set -u`, `$PYTHON` usage, here-strings).

**CLAUDE.md Files Read:** None found in `skills/subagent-driven-development/scripts/` or `tests/unit/` (checked via find; none present). Honored root `CLAUDE.md` bash gotchas (no `set -u`, no pipe-into-`grep -q`) per the pattern reference.

**Deviations from Plan:** One fixture correction in `test_hop_limit_exits_3`. The verbatim spec test wrote `.handoff-hops` to disk without committing it, which spuriously tripped the pre-existing Precondition 1 (clean-tree check, shipped in Task 1) before ever reaching the hop-limit precondition — an artifact of the plan's own documented invariant (spec.md L164: `.handoff-hops` is *tracked*, and by the time the hop gate runs in the real flow it's always committed via the successor's step-2 commit). Added a `git add -A` + `git commit` after the write, mirroring the existing `test_missing_active_feature_exits_1` pattern in the same file, to make the fixture faithful to that invariant. Assertion (exit 3, "hop" in output) is unchanged. Confirmed via the advisor tool before applying — verdict: correct, in-scope, not a BLOCKED-worthy contract conflict.

**Self-Review Findings:** Confirmed the `.sh` diff contains only the intended Task-2 insertion (checked via `git diff`); the Task 3, Tasks 4-5, and Task 6 markers remain exactly in place. `SP_HOP` is defined inside the new block. `MAX_HOPS` is read from the existing Task-1 config var — no hardcoded `3` in the new precondition logic. No `set -u` or pipe-into-`grep -q` introduced. Repo identity uses `git rev-parse --git-common-dir` + `os.path.realpath`, not `--show-toplevel`. Verified the file-watcher's cosmetic `.py` reformat did not alter committed content and did not touch the `.sh` file.

**Concerns:** None beyond the documented deviation above (the `.handoff-hops` commit in the hop-limit test fixture).
