---
schema_version: 1
task_id: 4
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/subagent-driven-development/scripts/spawn-handoff-session.sh"
    description: "Replaced the `# (Tasks 4-5 insert launch composition here.)` marker with launch composition A: VERSIONS_DIR + ARGS_OK forward-scaffolding, no-eval v1 argv decode with /pickup strip guard and APPEND_PROMPT rematerialize+substitute, spec §5.4b label rule, telemetry resolution, and the stderr `forwarded=/label=/telemetry=` echo. Task 6 marker untouched."
  - path: "tests/unit/test_spawn_handoff.py"
    description: "Appended the Task-4 decode/strip-guard/telemetry/label/append-prompt matrix (10 collected cases) plus an autouse `_hermetic_picker_env` fixture that scrubs the five ambient CLAUDE_CODE_PICKER_*/ENABLE_TELEMETRY vars so 'absent' cases test absence."
tests:
  written: 10
  passing: 10
  command: ".venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -k \"decoded or telemetry or label or append\" -v"
  result: PASS
contract_compliance:
  - constraint: "CLAUDE_CODE_PICKER_ARGS is decoded without eval: strip v1:, base64-decode, json.loads into a list of strings via python3 stdlib. Absent => empty argv. v1-prefixed-but-corrupt => decode failure => metadata unusable, never a silent arg-drop."
    status: compliant
    detail: "Quoted heredoc python; the payload is read from the environment, never interpolated into program text. Non-v1 prefix sets ARGS_OK=0 in bash; corrupt body / non-list / non-str elements exit 3 => ARGS_OK=0. Manually smoke-checked all four unusable classes (corrupt-v1, non-v1, json-not-list, list-of-int): each degrades to empty FORWARDED with rc=0, no crash."
  - constraint: "CLAUDE_CODE_PICKER_APPEND_PROMPT must be consumed: decode to a stable absolute file outside any repo and substitute that path into the forwarded --append-system-prompt-file value. Empty-but-flag-present => keep the original path."
    status: compliant
    detail: "Rematerialized to $HOME/.claude-codex-handoff/append-prompts/<bundle>-hop<N>.md (outside any repo); substitution covers BOTH `--flag value` and `--flag=value` forms (parametrized test). Empty/absent APPEND_PROMPT leaves the original path intact (dedicated test). Write failure exits 4 => ARGS_OK=0."
  - constraint: "Hop-recursion strip guard: strip any trailing positional beginning /pickup after decoding."
    status: compliant
    detail: "Done in python (argv[-1].startswith('/pickup')) rather than bash, avoiding 4.3-only negative array indexing. Test asserts a stale `/pickup old-bundle` never reaches the forwarded output."
  - constraint: "Label ceiling is 255: reserve len(suffix) before truncating the base, then concatenate (round-trip must be picker-sanitizer-stable)."
    status: compliant
    detail: "base[:255 - len(suffix)] + suffix. 300-char input yields exactly 255 chars ending in -Session-2. Sanitize charset [^A-Za-z0-9_.-] applied to the base before truncation, so the result is sanitizer-stable. Empty / empty-after-sanitize => empty label (omit --session-label, consumed by Task 5)."
  - constraint: "CLAUDE_CODE_ENABLE_TELEMETRY==1 => --telemetry on; absent => --telemetry off (never blocks auto)."
    status: compliant
    detail: "Strict `= \"1\"` string compare with `${VAR:-}`; anything else (including absent) resolves off. Both directions tested with the ambient var genuinely removed."
  - constraint: "Compose-side quoting: every interpolated element is shlex-style re-quoted when building the --command string."
    status: not_applicable
    detail: "Task 5's scope. Task 4 only echoes ${FORWARDED[*]} to stderr for assertion; no --command string is built here."
  - constraint: "Picker version discovery: versions/<v> is an executable regular file; the auto preflight asserts -f AND -x."
    status: not_applicable
    detail: "Task 5's preflight. Task 4 only defines VERSIONS_DIR (forward-scaffolding), matching install_version's on-disk layout at $HOME/.local/share/claude/versions."
---

**Commit:** `77537bc`

**Implementation Summary:** Inserted launch composition part A into `spawn-handoff-session.sh`: eval-free v1 argv decode (via a NUL-terminated temp file, so args with spaces/newlines survive), the `/pickup` hop-recursion strip guard, `CLAUDE_CODE_PICKER_APPEND_PROMPT` rematerialization + path substitution for both flag forms, the §5.4b label rule with suffix-space reservation at 255, and telemetry resolution — followed by the stderr `forwarded=/label=/telemetry=` echo Task 4 asserts against. `VERSIONS_DIR` and `ARGS_OK` are deliberately left unconsumed for Task 5's preflight.

**Bash Minimum Version Determination:** **bash ≥ 3.2**, and the plan's "confirm `env bash --version` is ≥ 4.x" caveat is **wrong** — Task 9 should document 3.2.

- *Empirically demonstrated:* 3.2.57 (the macOS system bash). Temporarily added an uncommitted `echo "[bv] $BASH_VERSION" >> "${SPAWN_BV_LOG:-/dev/null}"` probe at the top of the block, put a `bash` → `exec /bin/bash "$@"` shim first on PATH (the harness calls `["bash", SCRIPT]`, so this is what it resolves), and ran the **full** test file: **34 passed**, with the log containing 19 entries (every invocation that reached the block; the rest exit earlier at preconditions) and `sort -u` showing exactly one distinct value — `3.2.57(1)-release`. Without that log the "3.2 passed" claim would have been unverifiable. `/bin/bash -n` also parses the script clean. The probe was then removed and its absence verified (`grep -c BASH_VERSION` → 0) before committing.
- *Analytically, the construct that sets the floor:* array append `FORWARDED+=("$tok")` (line ~257), introduced in bash **3.1**. Everything else is ≤ 3.0: `FORWARDED=()`, `${FORWARDED[*]}` on an empty array (safe because the script deliberately does not `set -u` — that combination is what breaks on < 4.4), `read -r -d ''` (2.04), `while ... done < file`, env-prefixed heredoc command, `$?` capture after the heredoc. A targeted grep over the block for `mapfile|readarray|declare -A|${v^^}|${v,,}|;;&|&>>|[-1]|[@]:offset:-len` returned no bash hits (the one match, `argv[-1]`, is inside the quoted Python heredoc — not shell). No `local` in this block; `mapfile`/`readarray` deliberately not used.
- So the block would run on 3.1+, but no 3.1 binary was available and nothing below 3.2 was tested. **State the floor as 3.2** (verified, and the oldest bash anyone will realistically hit on macOS); note the underlying construct is 3.1-era, so 3.2 clears it with margin. Nothing here requires 4.x, and no rewrite for compatibility was needed.

**Source Files Read:** `spawn-handoff-session.sh` (confirmed marker at L199, `BUNDLE_ID`/`DRY_RUN` L38, `SP_HOP` L132, `PYTHON` L17; DRY_RUN is `0|1` so the `= "1"` compare is right); `tests/unit/spawn_handoff_helpers.py` (`encode_args` = `v1:`+b64(json); `install_version` writes an executable regular file under `$HOME/.local/share/claude/versions` — matches `VERSIONS_DIR`; `run_spawn` snapshots `os.environ` — the source of the leak below); `tests/unit/test_spawn_handoff.py` (24 tests, `_spawnable` at L163); `spec.md` §5.3–§5.5 (label rule, forwarding metadata, preflight, degradation ladder).

**CLAUDE.md Files Read:** repo root `CLAUDE.md` — only one in the repo. Hook Development Gotchas (no `set -u`, never pipe into `grep -q` under pipefail — neither introduced here; the block uses a temp file, not a pipe); Testing (`.venv/bin/python3 -m pytest tests/unit/`); shell-lint harness expectations.

**Deviations from Plan:**

1. **Added an autouse `_hermetic_picker_env` fixture** (not in the plan's Step-1 snippet). This machine's own Claude session is claude-picker-launched, so all five vars (`CLAUDE_CODE_PICKER_VERSION/LABEL/ARGS/APPEND_PROMPT`, `CLAUDE_CODE_ENABLE_TELEMETRY`) are **live in the ambient environment**, and `run_spawn` copies `os.environ`. The plan's `_meta` signals "absent" by *omitting* a key, which would have inherited the real value instead — `test_telemetry_on_and_off`'s off-case and `test_append_prompt_empty_keeps_original_path` would both have asserted the opposite of their stated intent (vars confirmed set before writing). The fixture `monkeypatch.delenv`s them, giving genuine absence. It is autouse so the pre-existing 24 tests (which now flow through the new block on their `--dry-run` paths) don't decode this session's real payload either, and so Task 5's VERSION-preflight tests inherit the same hygiene. Every test body from the plan is otherwise **verbatim**.
2. **The plan's "Bash version caveat" is factually wrong** — see above. Task 9 must document ≥ 3.2, not ≥ 4.x.

**Self-Review Findings:**
- `DECODE_TMP` cleanup audited: `rm -f` sits after the if/else, so both the success and the `ARGS_OK=0` branch reach it; there is no `exit`/`return` between `mktemp` and `rm` (matching the no-EXIT-trap house style). If `mktemp` itself fails, `DECODE_TMP=""` makes the Python `open("")` fail → non-zero → `ARGS_OK=0` → correct degrade, no leak.
- Verified `"$PYTHON" - "$LABEL"` is safe for a label beginning with `-`: CPython stops option processing at `-`, so the value lands in `sys.argv[1]` rather than being parsed as a flag.
- Verified the untested-by-design corrupt path doesn't regress or emit tracebacks (four unusable classes smoke-checked manually) — no test added, per the task's note that the corrupt-v1 test belongs to Task 5.
- ShellCheck `--severity=warning`: only SC2034 "appears unused" on forward-scaffolding vars — `VERSIONS_DIR` joins the pre-existing `PICKER_CONTRACT`/`FEATURE_NAME`/`SPAWN_LOG`/`QUOTA_STATUS`, i.e. the established Task 1–3 pattern. No new severe (fail-open) class. `bash -n` clean on both 5.3.9 and 3.2.57.
- `VERSIONS_DIR` and `ARGS_OK` preserved (not YAGNI'd); Task 6 marker untouched; the plan's `${FORWARDED[*]}` stderr echo left as-is (no Task-5 shlex re-quoting pulled forward).

**Concerns:**
- The autouse fixture changes the ambient environment for the 24 pre-existing tests. Benign — they assert on return codes and `quota=`, not the new echo — and all 34 pass, but it is a behavior change to tests the implementer was told not to restructure, so flagged explicitly.
- `mkdir -p "$APPEND_TARGET_DIR"` runs on any non-dry-run invocation with ARGS present, even when `APPEND_PROMPT` is empty, so it can create an empty `~/.claude-codex-handoff/append-prompts/` directory. That is exactly what the plan specifies and it's harmless; noted in case Task 5/6 review prefers it gated on `ap_b64`.
- Rematerialized append-prompt files accumulate at `~/.claude-codex-handoff/append-prompts/<bundle>-hop<N>.md` with no reaper. Out of scope here; worth a look when Task 9 documents the artifact set.
- Full-file total is **34 passing** (24 prior + 10 new collected cases; the `written/passing: 10` field uses the collected-case convention, counting the 4 label and 2 append-form parametrizations individually). Full `tests/unit/` suite: **587 passed**, no regressions.
