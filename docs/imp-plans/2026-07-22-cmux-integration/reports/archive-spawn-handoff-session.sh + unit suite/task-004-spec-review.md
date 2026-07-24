# Task 4 — Spec Compliance Review

**Verdict: PASS** — spec compliant AND contract compliant, with advisories.
**Review tier:** full (dispatched, general-purpose)
**Audited commit:** `77537bc` (`git diff f869405..77537bc`)

Reviewer ran all experiments in an isolated `/tmp` mirror (symlinked `skills/` + `.venv/`); no repository file was ever patched. Repo state byte-identical to session start.

---

## Anti-circularity check (gated the verdict)

`git diff f869405..HEAD -- module-1-spawn-script.md` is **empty** — the plan was **not** retrofitted to match the code. Only uncommitted plan change is a Task-**3** checkbox tick. So the "verbatim" findings below are real, not self-referential.

Programmatic comparison of the plan's Task-4 Step-2 bash fence vs. the committed block (`spawn-handoff-session.sh:199-281`): **byte-identical**. Test bodies semantically verbatim vs. the Step-1 snippet modulo black reformatting; the only additions are `PICKER_ENV_VARS` + the autouse fixture.

## Deviation 1 — autouse `_hermetic_picker_env`: **JUSTIFIED** (anti-masking, not test-weakening)

- Ambient env confirmed set on this machine: `CLAUDE_CODE_PICKER_VERSION` (len 7), `_LABEL` (21), `_ARGS` (7), `_APPEND_PROMPT` (**len 0**), `CLAUDE_CODE_ENABLE_TELEMETRY` (1).
- `run_spawn` does `env = dict(os.environ)` (`spawn_handoff_helpers.py:105`) — the leak path is real.
- Fixture neutralized in the mirror → **1 failed, 33 passed**. Failure is `test_telemetry_on_and_off` off-case, observed stderr `telemetry=on`.

**Not masking.** The discriminator: without the fixture the suite goes **red**, not silently green. Test-weakening moves red→green by loosening an assertion; this moves an env-dependent test to deterministic. No prior test *body* changed — only their environment, strictly more hermetic.

**[ADVISORY] [MISUNDERSTANDING]** the implementer's justification is partly inaccurate on two counts:
1. `test_append_prompt_empty_keeps_original_path` would **not** have inverted — ambient `CLAUDE_CODE_PICKER_APPEND_PROMPT` is set-but-**empty**, so `ap_b64` is falsy and it passes either way *on this machine*. (The fixture is still correct — a session launched with a real append prompt would break it.)
2. "Assert the opposite of their stated intent" is imprecise: the test **fails**, it does not silently invert.

## Deviation 2 — bash floor: **JUSTIFIED** (and plan-mandated)

`deviations.md` shows the pre-execution audit explicitly ordered this determination. Reviewer's independent conclusion — **two numbers, do not collapse them**:

| | Value | Governing evidence |
|---|---|---|
| **Construct floor** | **bash ≥ 3.1** | `FORWARDED+=("$tok")` (`:256`) — array `+=` landed in 3.1. Everything else ≤3.0: `FORWARDED=()`, `${FORWARDED[*]}`, `[[ =~ ]]`, `read -r -d ''` (2.04), `${BASH_SOURCE[0]}`. |
| **Verified floor** | **bash 3.2.57** | Independent PATH shim (`bash` → logging wrapper → `exec /bin/bash`), full test file **34 passed**, probe log **33 script invocations, all `3.2.57(1)-release`**. `/bin/bash -n` clean. |

4.x-only construct scan (`mapfile|readarray|declare -A|${v^^}|${v,,}|;;&|&>>|[-1]|[@]: -n`): **zero bash hits** (the one `argv[-1]` match is inside the quoted Python heredoc).

➡ **Task 9 must document `bash ≥ 3.2`.** The plan's "≥ 4.x" caveat is confirmed wrong.

**[ADVISORY] [EXTRA]** the `set -u` ↔ `${FORWARDED[*]}`-on-empty-array coupling is real and load-bearing. Verified under 3.2.57: `set -u; A=(); echo "${A[*]}"` → `A[*]: unbound variable`; without `set -u` → `[]`. The header documents the no-`set -u` choice only *generically*, not at the `FORWARDED` site. A future `set -u` breaks bash 3.2 silently while passing on 4.4+. **Task 9 should make the coupling explicit.**

## Contract Constraints — verified against code (not tests)

| Constraint | Status | Evidence |
|---|---|---|
| ARGS decoded **without eval** | ✅ | Heredoc `<<'PY'` quoted (`:223`); payload read via `os.environ.get(...)` inside Python (`:226`) — never interpolated into program text |
| Absent ARGS ⇒ empty argv | ✅ | `:220` guard; `FORWARDED=()` at `:217`. Probed live: `forwarded=` empty, rc 0 |
| Corrupt `v1:` ⇒ `ARGS_OK=0`, no silent arg-drop | ✅ | `bash -x` trace confirms for corrupt-b64, non-`v1:` prefix, and non-list JSON. Observable `launch=picker-manual` assertions are Task 5's — deferral plan-sanctioned |
| APPEND_PROMPT → stable absolute file **outside any repo** | ✅ | `$HOME/.claude-codex-handoff/append-prompts/<bundle>-hop<N>.md`. Non-dry-run probe: correct bytes written |
| Substituted for **both** flag forms | ✅ | `:244-249`; trailing-flag-with-no-value handled safely (`i+1 < len(argv)`) |
| Empty-but-flag-present ⇒ original path kept | ✅ | `if ap_b64:` falsy on empty. Probed |
| Telemetry `==1` ⇒ on; absent ⇒ off | ✅ | `:279` strict compare. Both directions verified with var genuinely absent |
| Label ceiling 255, suffix reserved before truncation | ✅ | `base[:255 - len(suffix)] + suffix` (`:274`). 300-char input → exactly 255 ending `-Session-2` |
| Round-trip picker-sanitizer-stable | ✅ | Ran **repo-1's actual `_sanitize_attr`** (`telemetry-exp/launchers/claude-picker:55-58`) over outputs incl. the boundary case → all stable |
| Compose-side quoting | ✅ `not_applicable` | Genuinely Task 5, not skipped |
| Version `-f` AND `-x` preflight | ✅ `not_applicable` | Genuinely Task 5's preflight |

### [ADVISORY] [MISUNDERSTANDING] label overflow edge (plan-inherited, non-blocking)

`:274` — when `255 - len(suffix)` goes **negative**, the Python slice silently yields `""` and the result is `suffix` alone, **unbounded**. Live probe with `CLAUDE_CODE_PICKER_LABEL="Base-Session-<300 nines>"` emitted a **310-character** label.

**Non-blocking because** the picker caps its export: `_sanitize_attr` runs `cut -c1-255` before `export CLAUDE_CODE_PICKER_LABEL` (`claude-picker:57,184`). Reviewer proved algebraically that any input ≤255 yields output ≤255. **If repo-1 ever drops that cap, this goes live.** Worth a `max(0, …)` in Task 5/9 hardening.

### [ADVISORY] [MISUNDERSTANDING] sanitizer charset divergence (plan-level, not implementer)

Spec §5.4b says sanitize with "the picker's attr charset rule." The picker *keeps* `/` and *replaces* unsafe chars with `-`; the script's `[^A-Za-z0-9_.-]` **strips** and drops `/`. Verified: `feat/x` → picker leaves `feat/x`, spawn script emits `featx-Session-2`. The binding constraint (round-trip stability) still holds ⇒ cosmetic. Code is verbatim from the plan ⇒ **plan defect, not implementer error.**

## Also verified

- **Forward scaffolding preserved:** `VERSIONS_DIR` (`:200`) and `ARGS_OK` (`:203`) present and unconsumed — not YAGNI'd.
- **Scope:** exactly the 2 in-scope files. No hook / `SKILL.md` / `verify-symlink-install.sh` / `context-observations.log`. **Task 6 marker intact** at `:282`.
- **Temp-file hygiene:** no `trap` (by design). `rm -f "$DECODE_TMP"` (`:258`) after the if/else, reached on success and `ARGS_OK=0`. On `mktemp` failure `DECODE_TMP=""` → Python `open("")` raises **outside** the `try` → non-zero → `ARGS_OK=0`; `rm -f ""` verified rc=0 under 3.2.57. **No leak on any path.**
- **Lint:** shellcheck only SC2034 on forward-scaffolding vars; `bash -n` clean on 5.3.9 and 3.2.57.
- **Tests:** full unit suite independently re-run → **587 passed**. `test_spawn_handoff.py` → 34. `passing (10) ≤ written (10)` ✓.
- **Report completeness:** all sections present and substantive, including the mandated Bash Minimum Version Determination. Line references spot-checked and correct (marker L199, `SP_HOP` L132, `PYTHON` L17, `_spawnable` L163).

## The three open Concerns — reviewer assessment

1. **Autouse fixture affects prior 24 tests** — acceptable, and *strictly* an improvement. Not a spec violation.
2. **`mkdir -p` creates empty `append-prompts/` when APPEND_PROMPT empty** — reproduced; cosmetic, **verbatim from the plan**, no spec text forbids it. Gating on `ap_b64` is a reasonable Task 5/6 cleanup.
3. **Rematerialized files accumulate, no reaper** — spec §5.4d defines no reaper. Correctly out-of-scope; Task 9 doc note is the right disposition.

## Pyright diagnostics — confirmed cosmetic

`_hermetic_picker_env is not accessed` (inherent to autouse); `telem=None` not assignable to `str` (default-inference artifact; runtime guard is `if telem is not None`; identical signature is in the plan's own snippet). Neither signals a defect.

## [UNVERIFIED]

- Nothing below bash 3.2 tested (no 3.0/3.1 binary). The ≥3.1 construct floor is analytic only. Immaterial — 3.2 is the shipping recommendation.
- The picker's 255-char cap is verified in the **current** `telemetry-exp/launchers/claude-picker` (external repo, own trail). Would be settled by pinning that cap as a fixture assertion if label overflow ever matters.
