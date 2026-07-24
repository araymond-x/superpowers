# Task 1 Quality Review — spawn-handoff-session.sh foundation

**Reviewer scope:** Code quality only (spec compliance already PASSED in `task-001-spec-review.md`).
**Files reviewed:** `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` (new, 76 lines), `tests/unit/test_spawn_handoff.py` (appended 5 tests + imports).
**Verification performed:** `bash -n` syntax check, `shellcheck --severity=warning --external-sources`, `xxd`/`tail -c` trailing-byte inspection, `.venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -v` (6 passed), full `tests/unit/` suite (559 passed, no regressions).

## Strengths

- **Layer 0 self-resolution is solid and slightly more robust than its model.** The `BASH_SOURCE`/symlink-walk (lines 10–16) correctly chains through multiple levels of symlinks before resolving `SCRIPT_DIR`, matching `sdd-pre-dispatch-hook.sh`'s self-resolving pattern but handling the general case (`sdd-pre-dispatch-hook.sh` only does a single-level `dirname`). `PYTHON` falls back to system `python3` with an inline comment explaining why that's safe here (stdlib-only json/base64) — good, non-obvious-decision documentation per house convention.
- **House style honored:** no `set -u` (with the required CLAUDE.md-referencing comment at lines 6–7), no producer piped into `grep -q`, config values pull from env vars with sane defaults (`${SUPERPOWERS_CMUX_MAX_HOPS:-3}` etc.) rather than hardcoded literals — this is exactly the "shared constants passthrough" pattern the fork's subagent-context improvements require.
- **Arg-parse loop is correctly ordered and exits cleanly.** Unknown flags, extra positional args, and missing `BUNDLE_ID` all exit 1 with a clear stderr message before any git/filesystem work happens — cheap failures fail fast.
- **Precondition ordering matches the plan's acceptance criteria exactly**: `.active-feature` check precedes the clean-tree check, both exit 1, both with greppable substrings (`"active-feature"`, `"clean"`) that the tests assert against.
- **Marker comments are byte-exact and correctly ordered** (Task 2 → Task 3 → Tasks 4-5 → Task 6), which is what actually matters for Tasks 2–6: each later task's plan text does a literal string-replace against these markers, so any drift here would silently break every subsequent task's Step 2.
- **Tests are idiomatic for this harness.** Naming (`test_<scenario>_exits_<code>`), use of `setup_worktree`/`install_bundle`/`run_spawn` from the Task-0 helper, and assertion style (`returncode == N and "<needle>" in (stdout+stderr)`) are all consistent with `test_context_gate_tier.py` and the rest of the SDD test suite.
- **shellcheck is clean apart from the expected SC2034 set** (the 11 front-loaded config/derived variables the plan explicitly defers to Tasks 2–6) — no quoting bugs, no other warnings.

## Issues

### Critical (Must Fix)
None.

### Important (Should Fix)
None.

### Minor (Nice to Have)

1. **Trailing newline — spec reviewer's concern does not apply; worth closing out explicitly.**
   File: `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` (EOF)
   The spec review flagged a possible missing trailing newline. Byte inspection (`tail -c 20 | xxd`) confirms the file ends `... exit 0\n` — it *is* newline-terminated. No action needed; noting this so the concern is formally closed rather than silently dropped. (Even if it had been missing, Task 2's `Modify` + insert-at-marker approach doesn't literally `cat >>` onto the file, so it would not have caused a corruption issue for Task 2 regardless — but it's moot since the newline is present.)

2. **Imports appended mid-file rather than consolidated at the top.**
   File: `tests/unit/test_spawn_handoff.py:60-62`
   `import os`, `import subprocess`, and the `spawn_handoff_helpers` import land after `test_fixtures_shape_matches_contract` rather than joining the `json`/`Path` imports at the top of the file (the convention in `test_context_gate_tier.py` and other SDD test modules). This is plan-directed, not an implementer choice — the plan's Task 1 Step 1 code block literally shows "Append to `test_spawn_handoff.py`" with the imports leading the appended block, and the same append-in-place pattern recurs in Tasks 2–5 (each inserts more imports at its own append point, including one inline `import base64` inside a test function in Task 5). Flagging only so whichever task does final polish (Task 9, if it exists, or a dedicated cleanup pass) considers hoisting all imports to the top once the file stops growing. Not worth interrupting the TDD append rhythm to fix now — cosmetic only, doesn't affect correctness or test discovery.

## Recommendations

- When Task 9 (or whatever task does final docs/cleanup) touches `test_spawn_handoff.py` for the last time, consider one pass to consolidate the top-of-file imports (item 2 above). Purely cosmetic, low priority.

## Assessment

**Ready to merge?** Yes.

**Reasoning:** The foundation is clean, matches the house bash style, and both flagged items are non-issues in practice (the newline concern doesn't materialize; the import placement is plan-mandated and harmless). Nothing here would make Tasks 2–6 harder — the marker comments are exact and the config variables are ready to be consumed at their designated insertion points.
