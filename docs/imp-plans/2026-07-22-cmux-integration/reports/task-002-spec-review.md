# Task 2 Spec Review — Bundle validation + cmux/hop preconditions

**Verdict: PASS**

## Scope of review

Diff `2557250..c176b4e` (commit `c176b4e`), plan section `docs/imp-plans/2026-07-22-cmux-integration/module-1-spawn-script.md` "### Task 2", implementer report `docs/imp-plans/2026-07-22-cmux-integration/reports/task-002-implementer-report.md`.

Files changed (confirmed via `git show --stat c176b4e`): only
- `skills/subagent-driven-development/scripts/spawn-handoff-session.sh`
- `tests/unit/test_spawn_handoff.py`

No out-of-scope files touched — `sdd-pre-dispatch-hook.sh`, `tests/ARaymond-hook-baseline/baseline.txt`, any `SKILL.md`, and `verify-symlink-install.sh` are absent from the commit.

## Step-by-step verification

**Step 1 (tests).** The appended test block in `tests/unit/test_spawn_handoff.py` (diff, lines +93 to +150) matches the plan's Step-1 code block essentially verbatim, with one intentional, disclosed deviation in `test_hop_limit_exits_3` (see below). 8 test cases total: 4 parametrized `test_bundle_validation_failures_exit_1` cases + `test_bundle_dir_missing_exits_1` + `test_not_in_cmux_exits_3_with_instructions` + `test_ping_failure_exits_3` + `test_hop_limit_exits_3`.

**Step 2 (implementation).** Diffed the inserted block in `spawn-handoff-session.sh` (lines 71-129 of the current file) character-for-character against the plan's Step 2 code block. It is a verbatim match:
- `validate_bundle()`: charset check `^[A-Za-z0-9_.-]+$` (line 75); `$BUNDLES_DIR`/`$bid` resolution via `cd … && pwd -P` for both `real_bundles` (line 78) and `real_bdir` (line 80); containment via `case "$real_bdir" in "$real_bundles"/*)` (lines 82-85); manifest.json presence check (line 87); `btype`/`bskill`/`brepo` read via three separate `$PYTHON -c` one-liners (lines 89-91); type/skill exact-match checks (lines 92-93); non-empty `brepo` check (line 94); and the **`active_id`** computation via a `$PYTHON -` heredoc that runs `git rev-parse --git-common-dir` (not `--show-toplevel`) + `os.path.realpath` (lines 96-104) — confirmed this is the Contract Constraint identity check, matches the plan verbatim, and is distinct from the pre-existing (Task 1) `--show-toplevel` call at line 44 used only for `cd`-ing to the worktree root.
- Precondition 3 (lines 112-117): `[ -z "$CMUX_WORKSPACE_ID" ] || [ "$(cmux ping 2>/dev/null)" != "PONG" ]` → `print_manual_instructions` + `exit 3`, verbatim.
- Precondition 4 (lines 119-129): reads `$HOPS_FILE`, defaults `HOPS=0`, defines `SP_HOP=$((HOPS + 1))` (line 123, present for later-task consumption), gate `[ "$HOPS" -ge "$MAX_HOPS" ]` using the existing `$MAX_HOPS` config var (not a hardcoded `3`) → `cmux notify` (best-effort, `|| true`) + `print_manual_instructions` + `exit 3`, verbatim.

**The other three later-task markers are intact and byte-identical** — confirmed via `grep -n "Task 3\|Tasks 4-5\|Task 6"` against both the pre-Task-2 and post-Task-2 file: line content unchanged (only line numbers shifted from 72-74 to 130-132 as expected from the insertion above).

**No `set -u`, no pipe-into-`grep -q`** introduced by this diff — confirmed by reading the full inserted block; all new conditionals use `[ ]`/`[[ ]]`/`case` directly on command substitutions, no piping into `grep`.

**Step 3 (tests pass).** Ran `.venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -v` independently: **14/14 PASSED** (6 pre-existing Task 0/1 tests + 8 new Task 2 tests), matching the implementer's claim exactly.

**Step 4 (commit).** Commit `c176b4e` message and file set match the plan's Step 4 instruction.

## Deviation scrutiny — `test_hop_limit_exits_3`

The implementer added a `git add -A` + `git commit -qm "seed hops"` after writing `.handoff-hops`, which the verbatim spec test omits. I verified this is **not a rubber-stamp** — I reproduced the spec's literal (uncommitted) version in an isolated scratch script using the same `setup_worktree`/`install_bundle`/`run_spawn` harness:

```
WITHOUT COMMIT: returncode= 1
stdout+stderr: REFUSED: worktree not clean — commit pending state first (protocol step 2)
```

This confirms the spec's verbatim test, as written, would fail — the uncommitted `.handoff-hops` write trips Precondition 1 (clean-tree, shipped in Task 1) before Precondition 4 (hop limit) is ever reached, exactly as the implementer's deviation note describes. With the added commit step, the actual test run returns **exit 3 with "hop" in the output**, which (given Preconditions 1-3 all pass cleanly — clean tree after the seed commit, valid bundle, `in_cmux=True` default with a passing `cmux ping` stub) is only reachable via the Precondition 4 hop-limit branch. Exit 3 is therefore correctly attributable to the hop-limit gate, not a fallback/misattributed path.

The fix mirrors the existing `test_missing_active_feature_exits_1` pattern in the same file (`.unlink()` a tracked file → `git commit -aqm "rm af"` → assert), which uses the identical "restore clean tree via commit before invoking the script" idiom. The assertion itself (`r.returncode == 3 and "hop" in (r.stdout + r.stderr).lower()`) is unchanged from the plan's verbatim text.

This deviation is logged in `deviations.md` as Accepted; I independently confirm it is **genuinely correct** — a necessary fixture correction, not a change that weakens or misdirects the test's assertion.

## Report completeness

`task-002-implementer-report.md` contains all required sections: YAML frontmatter (schema_version, task_id, status, files_changed, tests, contract_compliance) + prose sections (Implementation Summary, Source Files Read, CLAUDE.md Files Read, Deviations from Plan, Self-Review Findings, Concerns). `tests.passing` (8) == `tests.written` (8), consistent with the independently-verified 14/14 full-file run (6 pre-existing + 8 new).

## Findings

None. No BLOCKING or CONTRACT findings.
