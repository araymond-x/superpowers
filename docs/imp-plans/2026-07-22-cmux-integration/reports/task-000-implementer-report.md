---
schema_version: 1
task_id: 0
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "tests/unit/fixtures/spawn-handoff/valid-manifest.json"
    description: "Minimal valid work/SDD manifest fixture with __REPO_ID__ sentinel"
  - path: "tests/unit/fixtures/spawn-handoff/wrong-type-manifest.json"
    description: "Invalid fixture: bundle_type=review"
  - path: "tests/unit/fixtures/spawn-handoff/wrong-skill-manifest.json"
    description: "Invalid fixture: entry_skill=superpowers:brainstorming"
  - path: "tests/unit/fixtures/spawn-handoff/foreign-repo-manifest.json"
    description: "Invalid fixture: repo_id points at a different repo"
  - path: "tests/unit/spawn_handoff_helpers.py"
    description: "Shared subprocess/PATH-stub test harness (setup_worktree, install_bundle, install_version, run_spawn, PACE_* constants)"
  - path: "tests/unit/test_spawn_handoff.py"
    description: "Contract-fact test module: frozen CMUX_NEW_WORKSPACE_FLAGS/PICKER_EXPORTS constants + test_fixtures_shape_matches_contract"
tests:
  written: 1
  passing: 1
  command: ".venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -v"
  result: PASS
contract_compliance:
  - constraint: "claude-picker --handoff-contract must print '1' exactly"
    status: compliant
    detail: "Live check: `claude-picker --handoff-contract` -> '1', exit 0. Verified via string equality per spec."
  - constraint: "4 skill symlinks (cmux, cmux-workspace, cmux-markdown, cmux-diagnostics) resolve"
    status: compliant
    detail: "All 4 SKILL.md paths under $HOME/.claude/skills/<s>/ resolve, pointing into ~/projects/claude-custom/cmux-custom-skills/skills/<s>/."
  - constraint: "cmux ping -> PONG"
    status: compliant
    detail: "Live `cmux ping` returned PONG (session is inside a cmux workspace)."
  - constraint: "--command sends text+Enter into the new workspace's interactive shell (not direct exec)"
    status: compliant
    detail: "`cmux new-workspace --help` flag doc reads verbatim: '--command <text>  Send text+Enter to the new workspace after creation' — confirms shell-typed, not direct-exec semantics."
  - constraint: "4 picker exports (VERSION/LABEL/ARGS/APPEND_PROMPT) via _set_picker_env"
    status: compliant
    detail: "grep of telemetry-exp/launchers/claude-picker confirms _set_picker_env exports exactly CLAUDE_CODE_PICKER_VERSION, _LABEL, _ARGS, _APPEND_PROMPT on every launch path (lines 178-186, 320, 430, 438)."
  - constraint: "append-file exit-3 is --non-interactive-only"
    status: compliant
    detail: "Lines 261-267: the readable-file check and its `exit 3` are inside `if [[ \"$non_interactive\" == \"true\" ]]`."
  - constraint: "versions/<v> discovered via find -type f -perm -u+x"
    status: compliant
    detail: "Line 283: `find \"$VERSIONS_DIR\" -mindepth 1 -maxdepth 1 -type f -perm -u+x -exec basename {} \\;` — exact match."
  - constraint: "Repo identity match is realpath(git rev-parse --git-common-dir), worktree-invariant"
    status: compliant
    detail: "Harness's setup_worktree() computes repo_id exactly this way (matches the spec's stated pickup-guard formula); this is a Task-0 fixture/harness concern only — the script itself is Task 1+."
  - constraint: "CLAUDE_CODE_PICKER_ARGS decoded without eval (v1: prefix, base64, json.loads)"
    status: not_applicable
    detail: "Decode logic lives in spawn-handoff-session.sh, built in Task 4 — Task 0 only froze the ARGS-encoding helper (encode_args) and PICKER_EXPORTS constant that later tasks consume/assert against."
---

**Implementation Summary:** Implemented Task 0 of the cmux-integration repo-3 plan (module-1-spawn-script.md): verified repos 1+2 prerequisites are live, froze the bundle-manifest and cmux/picker contracts into 4 JSON fixtures plus a shared pytest harness (`spawn_handoff_helpers.py`), and wrote the initial contract-fact test (`test_spawn_handoff.py`). All code blocks were transcribed from the plan's verbatim spec. `.venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -v` passes (1/1), and the full `tests/unit/` suite (554 tests) passes with no regressions. Committed as `56210f1`.

**Source Files Read:**
- `docs/imp-plans/2026-07-22-cmux-integration/module-1-spawn-script.md` (Task 0 section, full spec)
- `tests/unit/sdd_test_helpers.py` and `tests/unit/test_context_gate_tier.py` (pattern references — subprocess+PATH-stub harness convention)
- Live verification results (Step 5):
  - `claude-picker --handoff-contract` → `1` (exit 0)
  - 4 skill symlinks resolve: `cmux`, `cmux-workspace`, `cmux-markdown`, `cmux-diagnostics` → `~/projects/claude-custom/cmux-custom-skills/skills/<s>/SKILL.md`
  - `cmux ping` → `PONG`
  - `cmux new-workspace --help`: `--command <text>` = **"Send text+Enter to the new workspace after creation"** — confirms the string is typed into the new workspace's interactive shell and executed, NOT exec'd directly without a shell. The interpreting shell is the user's login shell (zsh); the composed successor command in later tasks must be POSIX/zsh-safe.
  - `~/projects/claude-custom/telemetry-exp/launchers/claude-picker`: `_set_picker_env()` exports exactly `CLAUDE_CODE_PICKER_VERSION`, `_LABEL`, `_ARGS`, `_APPEND_PROMPT` (4 vars, matches `PICKER_EXPORTS`)
  - The `--append-system-prompt-file` readability check's `exit 3` is guarded by `if [[ "$non_interactive" == "true" ]]` (lines 261-267)
  - `versions/<v>` discovery: `find "$VERSIONS_DIR" -mindepth 1 -maxdepth 1 -type f -perm -u+x` (line 283) — confirms executable-regular-file semantics

**CLAUDE.md Files Read:** None found in `tests/` or `tests/unit/` (checked via `find tests -maxdepth 2 -iname "CLAUDE.md"` — no results). Repo root `CLAUDE.md` conventions honored (pytest via `.venv/bin/python3`, not unittest).

**Deviations from Plan:** After writing `tests/unit/spawn_handoff_helpers.py` and `tests/unit/test_spawn_handoff.py` verbatim per the spec and committing, the harness detected both files had been reformatted on disk (long lines broken into multi-line calls/lists, e.g. `PICKER_EXPORTS` list and `run_spawn()` signature) by what appears to be a background formatter (no `.pre-commit-config.yaml` or git `pre-commit` hook exists in this repo — only the standard `.sample` hooks — so the reformat happened via some other file-watching tool outside my control, not a repo-level pre-commit gate). The reformatting is purely cosmetic (line-wrapping/whitespace); no identifiers, logic, string literals, or behavior changed. Re-ran `pytest tests/unit/test_spawn_handoff.py -v` against the actual committed content — still 1/1 PASS. The 4 JSON fixture files are confirmed byte-identical to what I wrote (`git diff HEAD -- tests/unit/fixtures/spawn-handoff/` is empty).

**Self-Review Findings:** No issues found. Confirmed fixture JSON exactly matches spec fields/values; confirmed `test_fixtures_shape_matches_contract` assertions align 1:1 with fixture content; confirmed `run_spawn`/`install_bundle`/`install_version`/`setup_worktree` all present with every parameter (`env_extra`, `in_cmux`, `pace_body`, `picker_body`, `cmux_body`) intact per the "do not trim any knobs" instruction; ran the full `tests/unit/` suite (554 passed) to confirm no cross-file regressions from the new files.

**Concerns:** None regarding prerequisites — both repo-1 (picker contract) and repo-2 (vendored cmux skills) are confirmed live, so this task is not blocked. Flagged as `DONE_WITH_CONCERNS` solely because of the file-reformatting deviation noted above (cosmetic only, verified non-breaking) — surfacing per the report-format instruction that any deviation should use `DONE_WITH_CONCERNS` rather than `DONE`.
