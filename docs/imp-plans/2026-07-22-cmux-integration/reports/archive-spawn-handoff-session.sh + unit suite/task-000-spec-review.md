# Task 0 Spec Compliance Review — cmux-integration repo-3, module-1

**Reviewed commit:** `56210f1` (`test(cmux-int): contract fixtures + prerequisite assertions + harness (Task 0)`)
**Spec:** `docs/imp-plans/2026-07-22-cmux-integration/module-1-spawn-script.md`, Task 0 (Steps 1–7)
**Report reviewed:** `docs/imp-plans/2026-07-22-cmux-integration/reports/task-000-implementer-report.md`

## Verdict: PASS

Every spec-mandated artifact was independently read from the committed tree and compared, field-by-field / AST-by-AST, against the spec's verbatim code blocks. All contract-verification claims in the implementer report were independently re-run against the live sources they cite. No discrepancies found.

## Method

- `git show --stat 56210f1` — confirmed exactly 6 files changed, all in-scope (4 fixtures, helper, test module).
- Read all 6 committed files in full; read the spec section (module-1-spawn-script.md lines 1–920, Task 0 = lines 52–250) in full.
- Diffed fixture JSON byte-for-byte against the spec's field values.
- Extracted the spec's verbatim `spawn_handoff_helpers.py` and `test_spawn_handoff.py` code blocks, stripped fences, and compared to the committed files two ways: (a) `diff -Bb` (whitespace-insensitive) to see every formatting delta, (b) Python `ast.dump()` equality on both parse trees, which is blind to whitespace/line-wrapping but catches any identifier, literal, operator, or docstring change.
- Independently re-ran every live-verification claim in the implementer report against the actual live tools/files on this machine (not trusting the report's transcription).
- Ran `pytest tests/unit/test_spawn_handoff.py -v` and the full `tests/unit/` suite myself.
- Ran `skills/subagent-driven-development/scripts/validate-report.py` against the implementer report.

## Findings

None. All checks below passed.

### 1. Fixtures (Step 2) — exact match

| File | Spec field values | Committed file | Match |
|---|---|---|---|
| `valid-manifest.json` | `bundle_type=work`, `entry_skill=superpowers:subagent-driven-development`, `repo_id=__REPO_ID__` | identical | yes |
| `wrong-type-manifest.json` | `bundle_type=review`, all else same as valid | identical | yes |
| `wrong-skill-manifest.json` | `entry_skill=superpowers:brainstorming`, all else same as valid | identical | yes |
| `foreign-repo-manifest.json` | `repo_id=/some/other/repo/.git`, all else same as valid | identical | yes |

Each invalid fixture changes exactly one field vs. the valid fixture, as required.

### 2. `tests/unit/spawn_handoff_helpers.py` (Step 3) — semantically verbatim

`ast.dump()` comparison of the spec's code block vs. the committed file: **AST EQUAL**. The only differences are Black-style line-wrapping (e.g. `SCRIPT = (...)` multi-line, `run_spawn(` args broken one-per-line, dict/list literals expanded). No identifier, string literal, default value, or control-flow changed.

Confirmed present and un-trimmed, per the "expose all knobs upfront" requirement:
- `run_spawn` knobs: `env_extra`, `in_cmux`, `pace_body`, `picker_body`, `cmux_body` — file:130/spawn_handoff_helpers.py:89-94, all five present.
- All 6 `PACE_*` constants: `PACE_OK`, `PACE_LOW`, `PACE_MALFORMED`, `PACE_MISSING_FIELD`, `PACE_MISSING_WINDOW`, `PACE_NONZERO` — spawn_handoff_helpers.py:19-26, all six present, values unchanged.
- `setup_worktree` repo-id formula: spawn_handoff_helpers.py:52-57 computes `os.path.realpath(str(wt / common) if not os.path.isabs(common) else common)` from `git rev-parse --git-common-dir` — worktree-invariant, NOT `--show-toplevel`. Matches spec exactly.
- `install_bundle`, `install_version`, `make_stub`, `encode_args` — all present, logic unchanged (AST-confirmed).

### 3. `tests/unit/test_spawn_handoff.py` (Step 4) — semantically verbatim

`ast.dump()` comparison: **AST EQUAL** to the spec block. Same Black-reformatting-only deltas (e.g. `PICKER_EXPORTS` list and the four `assert` statements in `test_fixtures_shape_matches_contract` were expanded to multi-line parenthesized form).

Confirmed:
- Module docstring present verbatim (mirrors `test_context_gate_tier.py` pattern reference note).
- `CMUX_NEW_WORKSPACE_FLAGS = ["--name", "--cwd", "--command", "--focus"]` — matches spec exactly.
- `CMUX_NOTIFY_FLAGS = ["--title", "--body"]` — matches spec exactly.
- `PICKER_CONTRACT_VERSION = "1"` — matches spec exactly.
- `PICKER_EXPORTS` = all 4 exports incl. `CLAUDE_CODE_PICKER_APPEND_PROMPT` — matches spec exactly, order preserved.
- `test_fixtures_shape_matches_contract` — present, asserts all 4 fixture fields + the `PICKER_EXPORTS` membership check with the "(Task 4)" comment intact.

### 4. Contract-fact verification (Step 5) — independently re-confirmed against live sources

Every claim in the implementer report's `contract_compliance` block and "Source Files Read" section was re-run independently on this machine, not merely trusted:

- `claude-picker --handoff-contract` → `1`, exit 0. Confirmed live. Also confirmed in `telemetry-exp/launchers/claude-picker:243`: `--handoff-contract) printf '1\n'; exit 0`.
- 4 skill symlinks resolve: `cmux`, `cmux-workspace`, `cmux-markdown`, `cmux-diagnostics` — all 4 `SKILL.md` files present under `~/.claude/skills/<s>/`. Confirmed live.
- `cmux ping` → `PONG`. Confirmed live.
- `cmux new-workspace --help` flag doc: `--command <text>     Send text+Enter to the new workspace after creation` — confirmed live, byte-for-byte match to the report's quoted text. This is the load-bearing sub-check added to Step 5 (shell-typed, not direct-exec) — correctly frozen.
- `cmux notify --help`: `--title`, `--body` flags present (plus `--subtitle`, `--workspace`, `--surface`, `--window` not part of the frozen subset) — `CMUX_NOTIFY_FLAGS` correctly captures the two flags the plan uses.
- 4 picker exports: `telemetry-exp/launchers/claude-picker:183-186` exports exactly `CLAUDE_CODE_PICKER_VERSION`, `_LABEL`, `_ARGS`, `_APPEND_PROMPT` inside `_set_picker_env()`, called on every launch path (lines 320, 430, 438). Confirmed live — matches report and `PICKER_EXPORTS`.
- Append-file `exit 3` is `--non-interactive`-only: `telemetry-exp/launchers/claude-picker:261-265`, the readable-file check and `exit 3` are inside `if [[ "$non_interactive" == "true" ]]; then`. Confirmed live, line numbers accurate.
- `versions/<v>` discovery: `telemetry-exp/launchers/claude-picker:283`, `find "$VERSIONS_DIR" -mindepth 1 -maxdepth 1 -type f -perm -u+x -exec basename {} \;`. Confirmed live, matches report verbatim.

No contract constraint was mis-frozen. This is the category the review brief flags as CRITICAL if wrong — it is not wrong.

### 5. Reformatting concern — genuinely cosmetic, confirmed independently

The implementer's report flags a background formatter (Black-style) reformatting `spawn_handoff_helpers.py` and `test_spawn_handoff.py` after they were written. I independently verified this claim rather than accepting it:
- `ast.dump()` parity (see §2, §3 above) proves no identifier, literal, operator, or docstring changed — only line-wrapping/whitespace.
- `diff -Bb` (whitespace-insensitive) against the spec blocks shows only multi-line-vs-single-line formatting deltas, consistent with Black's default 88-char line-length wrapping.
- The JSON fixtures are untouched (`git diff HEAD -- tests/unit/fixtures/spawn-handoff/` empty, confirmed).
- The test still passes and the full suite is unaffected.

Verdict on this concern: genuinely cosmetic. Correctly classified as `DONE_WITH_CONCERNS` rather than silently suppressed or wrongly escalated to a blocker.

### 6. Scope discipline

- `git diff 2f8340c..56210f1 --name-only` shows exactly the 6 files the plan authorizes for Task 0 — no `sdd-pre-dispatch-hook.sh`, no hook baseline, no `SKILL.md` body edits, no `verify-symlink-install.sh`.
- `spawn-handoff-session.sh` does not exist anywhere in the tree (`find . -iname "*spawn-handoff-session*"` empty) — correctly deferred to Task 1.
- Working-tree-only uncommitted changes exist to `module-1-spawn-script.md` / `module-2-protocol-e2e-docs.md` (a Step-5 addendum paragraph and later-task renumbering) plus untracked `deviations.md` / `reports/*` — none of these are part of commit `56210f1`; they are plan-tracking/SDD-process artifacts outside the scope of "what Task 0 committed." Not a finding against this task.

### 7. Test execution — reproduced independently

- `.venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -v` → `1 passed` (`test_fixtures_shape_matches_contract`). Matches report.
- `.venv/bin/python3 -m pytest tests/unit/ -q` → `554 passed, 1 warning`. Matches report's claimed regression-free full-suite run exactly (same count: 554).
- `validate-report.py --report-file .../task-000-implementer-report.md` → `"status": "COMPLETE"`, all 5 required sections found, none missing.

## Report Completeness Assessment

The implementer report has all schema-required sections, all substantive (none are boilerplate-empty):
- **Implementation Summary** — accurate, specific (names the commit hash, test counts).
- **Source Files Read** — lists the spec section, pattern-reference files, and every live verification performed with its result. Substantive.
- **CLAUDE.md Files Read** — explicitly states none found under `tests/`, with the `find` command used to check. Not a stub — shows the check was actually done.
- **Deviations from Plan** — the reformatting deviation, explained with root-cause reasoning (checked for a pre-commit hook, found none, correctly attributes it to an external file-watcher) and verification steps taken (re-ran pytest, diffed fixtures).
- **Self-Review Findings** — states what was checked (fixture fields, harness knobs, full suite) and the conclusion, not just "no issues found" with nothing behind it.
- **Concerns** — correctly scoped to the one real issue (reformatting), correctly states prerequisites are NOT a concern (both live).
- YAML frontmatter (`contract_compliance` list) is unusually thorough for a Task-0 report — 8 constraints each with `status` + `detail` citing line numbers. This is exactly what let me spot-check the claims and confirms the implementer actually consulted the live sources rather than asserting compliance.

No sections are suspiciously terse or generic. This report gives a verifier enough to check without re-deriving everything from scratch — which is what this review did.

## Summary

Task 0 is spec-compliant and contract-compliant. All 4 fixtures match the spec exactly. The harness and test module are semantically verbatim (AST-equal) to the spec's code blocks; the only deltas are cosmetic auto-formatting, independently confirmed non-breaking. All 8 live contract-verification claims in the report were independently re-checked against the actual live tools/files and are accurate, including the newly-added `--command` shell-typed-semantics sub-check. No out-of-scope files were touched. Tests pass (1/1 targeted, 554/554 full suite). The report is complete with no suspiciously empty sections.
