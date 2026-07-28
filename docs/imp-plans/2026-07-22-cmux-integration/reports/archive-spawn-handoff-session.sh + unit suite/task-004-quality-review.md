# Task 4 — Code Quality Review

**Verdict: PASS** — no BLOCKING defects.
**Review tier:** full (dispatched, general-purpose)
**Audited commit:** `77537bc`

All experiments ran against copies in `/tmp/spawnrev/`. **No repository file modified** — verified.

---

## Verification performed

Drove the real script through 12 decode shapes, 9 label shapes, 6 strip-guard shapes, and the **non-dry-run write path** (which no committed test reaches). Bash 3.2.57; `bash -n` clean; shellcheck shows exactly 5 SC2034s, all on dispositioned forward-scaffolding vars — **`ARGS_OK` is not among them; it is genuinely read at `:220`.**

| Property | Evidence |
|---|---|
| NUL round-trip faithful | `["a","","b\nc",""]` → exactly 4 elements under 3.2.57; empties **and the trailing empty** preserved, embedded newline preserved. Works *because* the encoding is NUL-**terminated**, not separated — the comment at `:216` is accurate and load-bearing |
| Empty file → no spurious element | 0-arg payload → `FORWARDED` count 0. No phantom `""` |
| NUL byte inside an arg | Not reachable — OS argv cannot contain NUL |
| `ARGS_OK` reaches Task 5 intact | Probed at the exact append point (`:282`) across all 12 shapes. Only writes are `:203/:205/:254`; the `LABEL` command substitution is a subshell and cannot clobber it |
| `$?` after env-prefixed heredoc | Correct — captures Python's exit status. Matches house idiom at `sdd-stop-hook.sh:148` |
| Huge `CLAUDE_CODE_PICKER_ARGS` | 500 KB single arg round-trips fine; env-read avoids a second argv copy |
| `APPEND_TARGET` path traversal | Closed **upstream**: `BUNDLE_ID` charset admits `..`, but `validate_bundle`'s `pwd -P` + containment `case` refuses it before `APPEND_TARGET` is built |
| Quoting | No unquoted expansions in the new block; paths with spaces verified |
| Telemetry | Strict `= "1"`; `"0"`, `"true"`, `"1 "`, `""` all → `off` |
| Convention fit | `$PYTHON` for both heredocs; no `set -u`; no producer-piped-into-`grep -q`; `ARGS_OK` `0|1` matches `DRY_RUN` at `:38`; no EXIT trap |

**Comment-block accuracy:** every clause at `:208–216` describes behavior actually present. Nothing aspirational except the forward reference to `picker-manual`, correct as intent.

**Critical test-quality question — answered: the test is adequate, no fix needed.** `test_decoded_args_and_strip_guard` **does** distinguish "stripped" from "everything dropped." Assertion 2 fails outright if decode collapsed, because at Task 4 those substrings have exactly one emitter — the `forwarded=` echo at `:281`. Confirmed empirically. A spurious pass is impossible.

## Findings

### [ADVISORY] test-coverage — the non-dry-run write path has **zero** committed coverage

All 10 Task-4 tests pass `--dry-run`, skipping **both** side-effecting statements: the shell `mkdir -p` (`:221`) and the Python `open(target,"wb")` write (gated by `SPAWN_DRY_RUN` at `:237`). Only argv substitution (which runs regardless) is exercised in-repo.

Reviewer confirmed both work out-of-band: non-dry-run with `APPEND_PROMPT=b64("SECRET prompt body")` wrote exactly those bytes and substituted the absolute path; with the target dir pre-created **as a regular file**, the write failed → `exit(4)` → `ARGS_OK=0` → `forwarded=` empty (the designed degrade). The plan mandates its listed test bodies verbatim but does not forbid *adding* one — a single non-dry-run test asserting the written bytes closes the class cheaply.

### [ADVISORY] robustness — `mkdir -p` gated on ARGS-present, not on there being anything to write (`:221`) *(plan-verbatim)*

- Creates an empty `append-prompts/` dir whenever `CLAUDE_CODE_PICKER_ARGS` is set, even with no `APPEND_PROMPT`.
- If that path exists as a **file**, the run emits a raw unprefixed `mkdir: …/append-prompts: File exists` to stderr then proceeds normally (`ARGS_OK=1`, Task 5 would compose `launch=auto`). An operator sees an error line on a healthy run with no `[spawn-handoff]` prefix to attribute it.

Cheap fix at Task 5/6: drop the shell `mkdir` and use `os.makedirs(os.path.dirname(target), exist_ok=True)` inside the `if ap_b64:` branch, where failure already routes to `exit(4)`.

### [ADVISORY] test-coverage — strip-guard **specificity** untested

| trailing/other element | result |
|---|---|
| `["a", "/pickup old"]` | stripped ✓ |
| `["/pickup old", "--flag"]` (non-trailing) | **kept** ✓ correct |
| `["a", "/pickupfoo"]` | **stripped** — `startswith` is a prefix match, so a `/pickup`-prefixed non-command arg is over-stripped |
| `["/pickup one", "/pickup two"]` | only the last stripped (by design) |
| `["a", " /pickup x"]` (leading space) | kept |

Defensible — in the auto flow Task 5 always appends `/pickup <id>` last — but **the non-trailing case is the one that matters**: a stale `/pickup` in a non-final position survives and would send the successor to the *wrong* bundle. Two parametrize rows pin it.

### [ADVISORY] robustness — lone-surrogate argv element produces an uncaught traceback + orphan file (`:250-251`) *(plan-verbatim)*

The final `x.encode()` sits **outside** the `try`, so `["\udcff"]` raises `UnicodeEncodeError` and prints a full traceback. Exit is non-zero → `ARGS_OK=0`, so the outcome is *safe*; but the operator gets a traceback instead of a diagnostic, and if `APPEND_PROMPT` was present the target file was already written before the crash (orphan). Wrapping the final write in the same `try` → `sys.exit(3)` makes the degrade uniform.

### [ADVISORY] hygiene (optional) — rematerialized prompt file mode is 0644 (`:239`)

**Consistent with the existing handoff tree, not a regression:** `~/.claude-codex-handoff/bundles/*/CONTINUE.md` (full continuation prompt) is likewise 0644 under 0755 dirs. Listed only so Task 5/9 can make a deliberate call; tightening to 0600 would be a repo-wide convention change.

### [ADVISORY] minor cluster
- `:226` comment `# read from env (no ARG_MAX limit)` is loose — env strings still count at exec time; the design avoids a *second* copy on argv. Directionally fine.
- `test_label_rule`'s `("", "")` row doesn't distinguish set-empty from unset.
- Dry-run substitutes a path to a file deliberately not written, so `--dry-run` is not a fully faithful preview. Intentional; noted so Task 6's dry-run acceptance criterion isn't read too literally.

**Label edge cases measured** (data only; 255-overflow and charset divergence already dispositioned): `-Session-` → `-Session--Session-2`; `-Session-2` / `-Session-0007` → `""` (base empties ⇒ label omitted, graceful); `12345` → `12345-Session-2`; Unicode-only → `""`; `x-Session-99999999999999999999` → `x-Session-100000000000000000000` (Python arbitrary-precision int, no overflow); `a/b` → `ab-Session-2`.

---

## What Task 5's implementer must know

1. **⚠ TEST-ECHO COLLISION — highest-value item.** Task 4's diagnostic at `:281` already emits `--append-system-prompt-file` and `a b.md` into stderr. Task 5's planned `test_auto_mode_composes_exact_command` asserts `"a b.md" in out` against combined stdout+stderr — **that assertion can pass without the compose line ever being exercised.** Anchor Task 5's greps on the specific `[spawn-handoff] successor command:` / `launch=` line, not bare `out`. (Tokens with no Task-4 emitter — `--non-interactive`, `--pick-version 2.1.218`, `--telemetry on`, `--session-label`, `/pickup b1` — are genuinely discriminating.)
2. **All consumed outputs reach `:282` intact** — verified: `ARGS_OK` (12 shapes), `FORWARDED` (element-faithful incl. spaces/empties/newlines, so `shq` quoting will be correct), `LABEL`, `TELEMETRY`, `VERSIONS_DIR`, `SP_HOP`.
3. **Do not add `set -u`.** `"${FORWARDED[@]}"`/`${FORWARDED[*]}` on an empty array are fine today but raise `unbound variable` under `set -u` on bash 3.2 (the verified floor).
4. **The autouse `_hermetic_picker_env` fixture is load-bearing for Task 5's own tests** — `test_picker_manual_when_metadata_degraded` with `env_extra={}` only means "metadata absent" because the fixture scrubs ambient picker vars. Do not remove or narrow it.
5. **No EXIT trap** — self-clean temp resources with immediate `rm -f`, matching `:258`.
6. Task 5's `preflight_ok` correctly requires both `CLAUDE_CODE_PICKER_VERSION` and `ARGS_OK=1`; an *empty* `CLAUDE_CODE_PICKER_ARGS` is treated as absent (`ARGS_OK=1`), which is right — the real picker always exports `v1:W10=` (7 bytes) for a zero-arg launch, never an empty string.
