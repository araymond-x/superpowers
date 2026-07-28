# Task 5 Code Quality Review — Launch composition B (auto preflight + successor command)

**Reviewer:** general-purpose senior code reviewer
**Date:** 2026-07-24
**Range:** `9edb259..e7d5fe1` (2 files, +148/−0: +40 script / +108 tests)
**Scope:** code quality only. Spec compliance is settled by `task-005-spec-review.md` (PASS) and not re-litigated.

**Verdict: With fixes — nothing blocks Task 6 dispatch.** No Critical findings. No dead code. Injection safety verified by execution, not inspection.

---

## What was run (vs. judged by reading)

| Action | Result |
|---|---|
| `.venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -q` | 41 passed (29.8s) |
| `shellcheck --severity=warning` on the script | Only 2 pre-existing SC2034s (`FEATURE_NAME:60`, `QUOTA_STATUS:197`). **The new block adds zero findings.** |
| 6 mutation tests against the new block | 4 survived (test gaps), 2 caught — detail below |
| End-to-end hostile-argv trace (env → v1 decode → `shq` → join → `shlex.split`) | argv round-trips exactly; **no injection** |
| `shq` failure-mode probes under `/bin/bash 3.2.57` (missing `$PYTHON`, non-UTF8 byte, newline, empty, trailing-newline args) | See Important #1 |
| `echo` vs `printf` under `BASHOPTS=xpg_echo`, bash 3.2 and 5.3.9 | See Minor #1 |

Script restored byte-identical after every mutation (`git diff --stat` empty, verified between each batch).

---

## Strengths

- **Decomposition is genuinely clean.** Four units, each with one responsibility and a well-defined interface: `preflight_ok` (`:287-297`) is a pure predicate returning 0/1 with no side effects; `shq` (`:302`) is a single-value transform; `build_successor_cmd` (`:303-311`) composes and returns via stdout; `_successor_cmd(r)` (test:`406-419`) is a pure extractor. Each is independently testable and the tests do test them independently (preflight via 4 degradation cases, composition via 2 assertion styles).
- **Comments explain *why*, not *what*** — exactly the repo's documented convention. `:290-291` ("Match the picker's own version discovery predicate … not a lenient `-e`"), `:294` ("String equality, not `>=`: a future v2 picker must degrade, never pass"), and `:300-301` / `:312-313` (why `$SP_HOP` expands at compose time but `date` doesn't) each encode a decision a future editor would otherwise reverse. This is the highest-value part of the change.
- **Compose-side quoting is correct, proven by execution.** Driving the real script with `['--append-system-prompt-file', '/tmp/a b.md', '--foo', 'he said "hi"; rm -rf /tmp/PWNED', '--bar', 'back\\slash']` produced a composed string that `shlex.split`s back into the *exact* original argv — every hostile metacharacter a single literal element, no injection surface. This is the load-bearing security property of the change and it holds.
- **The self-added 6th test earns its place.** Mutation M6 (replace `shq` with an identity `echo "$1"`) → `test_auto_mode_composes_exact_command` **passes**, `test_composed_command_reparses_with_correct_arity` **fails**. Without the added test the compose-quoting Contract Constraint would have had zero real coverage. Independently reproduced.
- **`_successor_cmd`'s docstring succeeds** (test:`407-413`). It names the collision (Task 4's `forwarded=` line already emits `a b.md`), names the consequence (assertions would pass without the compose block running), and states the invariant ("Every compose assertion anchors on this line"). A future reader understands *why* the extraction exists without opening `deviations.md`. It also asserts non-emptiness before slicing, so a TDD-red failure is a legible message rather than an `IndexError`.
- **Deviations discipline is exemplary.** All 4 concerns mirrored into `deviations.md`, plus a CRITICAL carry-forward block for Task 6. Forward-scaffolding (`LAUNCH_MODE`/`SUCCESSOR_CMD`) is covered by the established set-but-unused row precedent.

---

## Issues

### Critical
**None.**

### Important

**1. `shq` failure is silent and does not degrade — the fail-safe invariant has a hole. `spawn-handoff-session.sh:302-311`**

**First, the reassuring part:** when `shq` fails it emits **empty**, never the raw unquoted value. Verified under `/bin/bash 3.2.57`:

```
$ shq "$(printf 'bad\xffbyte')"   # non-UTF8
UnicodeEncodeError: 'utf-8' codec can't encode character '\udcff' … surrogates not allowed
rc=1 out=[]
composed=[claude-picker --pick-version  --telemetry on]
```

So the failure mode is **arity shift, not shell injection** — a re-parsing shell would hand `--pick-version` the value `--telemetry`, shifting every subsequent flag. Bad, but not a security hole.

**Second, it is essentially unreachable.** Every `shq` input was traced for *"is any input both un-guarded upstream and possibly non-UTF8?"*:

| Call site | Input | Upstream guard |
|---|---|---|
| `:305` | `CLAUDE_CODE_PICKER_VERSION` | preflight `:292` requires it name an existing `-f`+`-x` file |
| `:307` | `LABEL` | Task 4 `:270` strips to `[A-Za-z0-9_.-]` |
| `:308` | each `FORWARDED` element | Task 4 `:228`/`:251` strict `.decode()`/`.encode()`; failure ⇒ `ARGS_OK=0` ⇒ preflight fails |
| `:309`,`:316`,`:318` | `/pickup $BUNDLE_ID` | `:84` charset `^[A-Za-z0-9_.-]+$` |
| `:316` | `SPAWN_LOG` | from `.active-feature` — **un-guarded**, but it is the log **redirect target**, not a picker arg, so it cannot shift the picker's arity |

**Answer: no.** There is no reachable path to a corrupted picker invocation. A total `$PYTHON` failure is also unreachable — line `:98` already uses `$PYTHON` and would `REFUSED:` out long before line `:302`.

**Why it still matters:** the module's whole design posture, stated in this block's own comment at `:284-285`, is *"any failure degrades to the attended interactive picker rather than a mismatched session."* `shq` is the one place that posture is not enforced — `build_successor_cmd`'s exit status is `echo`'s, so a `shq` failure cannot propagate, and `:315` discards the status anyway. This is a **fail-safe-invariant** finding, not a live bug. Cheap fix:

```bash
shq() { "$PYTHON" -c 'import shlex,sys;print(shlex.quote(sys.argv[1]))' "$1"; }
build_successor_cmd() {
  local parts=("claude-picker" "--non-interactive" "--pick-version") q
  q="$(shq "${CLAUDE_CODE_PICKER_VERSION:-}")" || return 1
  parts+=("$q" "--telemetry" "$TELEMETRY")
  ...
}
if [ "$LAUNCH_MODE" = "auto" ] && PICKER_CMD="$(build_successor_cmd)"; then ... else LAUNCH_MODE="picker-manual"; fi
```

**Does not block Task 6.**

---

**2. The `picker-manual` branch's composed command has ZERO assertion coverage. `spawn-handoff-session.sh:318`, `tests/unit/test_spawn_handoff.py:452-509`**

This is a **novel finding** — the spec review did not surface it.

Mutation M2: replace `:318` entirely with `SUCCESSOR_CMD="TOTALLY-BROKEN"` → **41/41 tests still pass.**

Four of the seven collected Task-5 cases exercise the picker-manual path (`test_picker_manual_when_metadata_degraded[2]`, `..._contract_wrong`, `test_bad_codec_...`, `test_corrupt_v1_body_...`) and every one of them asserts only `"launch=picker-manual" in (r.stdout + r.stderr)`. None asserts what command is produced. The asymmetry matters: the auto branch is asserted token-by-token *and* by re-parse arity, while the branch a **human actually runs** when auto degrades — the user-facing safety net — is unverified.

**Fix is nearly free:** `_successor_cmd(r)` already works on both branches. One added assertion in any existing picker-manual test closes it:

```python
    assert _successor_cmd(r) == "claude-picker '/pickup b1'"
```

Recommend adding **now**, not deferring to the Task-6 sweep — it costs one line and it is the branch with the worst coverage-to-importance ratio in the change.

---

**3. Remaining mutation-survivable gaps (consolidated).**

**Novel:**
- **M5 — the empty-`LABEL` omission rule is untested.** `:307`'s `[ -n "$LABEL" ] &&` guard implements spec §5.4b's "empty result ⇒ omit `--session-label`" (the rule is even restated in the comment at `:261`). Removing the guard leaves **41/41 green** — every auto-path test passes `_meta(label="Proj-Session-2")`, so no case ever has an empty `LABEL` at compose time. Cheap to add now (`_meta(label="")` + `assert "--session-label" not in cmd`).

**Confirming the spec reviewer's advisories by mutation (not re-derived):**
- **`-x` half of the version predicate:** reducing `:292` to a bare `[ -f … ]` leaves **41/41 green**. This is a constraint Task 5 explicitly *owns* and whose comment explains why `-e` is wrong — but nothing enforces it. `install_version()` always `chmod 0o755`, so the harness cannot express the case without a new knob.
- **`command -v claude-picker`:** deleting `:293` entirely leaves **41/41 green**. The harness always installs a `claude-picker` stub and exposes no removal knob.
- **`--telemetry off` on the *composed* line:** unasserted (all auto-path tests use `telem="1"`). Dropping the flag pair from `:306` *is* caught (M3), so the flag's presence is pinned; only the `off` value is not.

**Recommendation:** add M2 + M5 now (two lines, no harness change). Route the `-x`, picker-missing, and `telemetry off` gaps to the existing **"Task 6 test-debt sweep"** in `deviations.md` — each needs a new harness knob, which is genuinely sweep-shaped work.

---

### Minor

**1. `echo "${parts[*]}"` → `printf '%s\n' "${parts[*]}"`. `spawn-handoff-session.sh:310`** — asked to judge: **yes, materially better.** Reproduced:

```
--- bash 5.3.9, BASHOPTS=xpg_echo ---
== echo:   claude-picker 'a<TAB>b' 'x<NEWLINE>y'      # mangled
== printf: claude-picker 'a\tb' 'x\ny'                # intact
```

With `BASHOPTS=xpg_echo` in the environment, bash 5's `echo` builtin interprets backslash escapes and corrupts any forwarded arg containing `\t`, `\n`, or `\\`; `\c` would **truncate** the string mid-command, yielding an unterminated quote. `printf '%s\n'` is immune in both bash 3.2.57 and 5.3.9. Consequence is mangling/truncation → a `--command` that fails to parse — **degradation, not injection**. Trigger requires an unusual env var *and* a backslash-bearing arg, hence Minor; the fix is one word. (The separate `-n`/`-e` option-swallowing hazard is *not* reachable here: `"${parts[*]}"` is one word beginning `claude-picker`.)

**2. `$(shq "/pickup $BUNDLE_ID")` computed in three places. `:309`, `:316`, `:318`** — three Python spawns for one value, and three edit sites if the prompt format ever changes. Weighed against the SSOT principle: worth hoisting to `PICKUP_ARG="$(shq "/pickup $BUNDLE_ID")"` before the branch. Small, real, one-line.

**3. `_successor_cmd` returns `lines[0]`, truncating on an embedded newline. `tests/unit/test_spawn_handoff.py:417-419`** — `shq` preserves interior newlines (verified: `shq $'a\nb'` → `'a<NL>b'`), so a newline-bearing forwarded arg makes `SUCCESSOR_CMD` multi-line and the helper silently returns a prefix. Test-helper robustness only; no production impact. `"\n".join(...)` from the marker line onward would close it, or simply document the assumption.

**4. `[ -n "$LABEL" ] && parts+=(...)` mid-function. `:307`** — correct today (no `set -e`, and it is not the last statement). The readability cost is small, but the *fragility* is real: if a future edit makes it the final statement, `build_successor_cmd` silently returns 1. A plain `if [ -n "$LABEL" ]; then parts+=(...); fi` costs one line and removes the trap entirely. Judgment: worth changing, low urgency.

**5. Contract probe `claude-picker --handoff-contract` has no timeout. `:295`** — a hung picker hangs the spawn script indefinitely. Noted only because this file establishes the opposite precedent 130 lines earlier: `check_quota` (`:159-187`) bounds its external tool with a watchdog and a 24-line comment about why macOS forces that pattern. The picker is a same-author local script answering with a bare `echo`, so the risk is low — flagged for consistency, not correctness.

---

## Explicitly checked, no finding

- **Dead code: none.** `preflight_ok`, `shq`, `build_successor_cmd` all have callers; `PICKER_CMD` (`:315`) is consumed one line later. `LAUNCH_MODE`/`SUCCESSOR_CMD` are Task-6 forward-scaffolding — brief-authorized, consistent with the five pre-existing peers, and documented in `deviations.md` as an established pattern. shellcheck does not flag them. **Correct call; no Critical.**
- **Mid-file `import shlex` (test:`452`) is consistent with the file's convention,** not a violation — the file already has mid-file imports at lines 60, 62, 98, 153, 254, 362, and 377. No finding.
- **File growth is proportionate.** +40 script lines for one cohesive concern-block (script now 324 lines); +108 test lines for 7 collected cases. Section is delimited by a banner comment matching Tasks 1–4. Follows the plan's file structure exactly — a single `@@ -279,6 +279,46 @@` insertion after the Task-4 echo, with the Task-6 placeholder comment intact.
- **The composed `SUCCESSOR_CMD` at `:316` is dense but survivable.** It is the highest-risk line to edit in the file (nested double/single quotes, an escaped `\$(date …)` that must stay deferred, a `{ …; }` group whose trailing `;` is load-bearing, a `>>` whose target is a command substitution). The `:312-313` comment explains the one non-obvious rule (compose-time vs runtime expansion), which is the right thing to explain. What is missing is a **worked example of the emitted string** — the single artifact that would let a future editor verify a change without executing the script. Recommend adding the real output as a 2-line comment above `:314`. Not a defect.
- **Bash-floor compliance:** multiline `local parts=(…)`, `parts+=(…)`, and `"${FORWARDED[@]}"` on an empty array with no `set -u` all verified under `/bin/bash 3.2.57`. No `set -u` introduced. No producer piped into `grep -q`. `$PYTHON` used for the Python call. All CLAUDE.md gotchas honored.

---

## Assessment

**Ready to merge? With fixes** — none of which block Task 6.

**Reasoning:** The decomposition is clean, the comments encode the decisions that matter, and the security-critical property (compose-side quoting survives a shell re-parse with hostile input intact) is verified by execution rather than assertion. The two real signals are (a) `shq`'s failure posture contradicts the module's own "degrade, never mismatch" invariant — though every input was traced and no reachable trigger found, and the failure emits *empty*, so there is no injection surface even when it fires; and (b) the `picker-manual` branch's composed command is entirely unasserted, proven by a mutation that replaces it with garbage and still passes 41/41. Both fixes are a handful of lines.

**Suggested sequencing:** apply the two cheap test additions (M2 picker-manual assertion, M5 empty-label case) and the `printf` swap in this task; route the `shq` rc-propagation restructure and the harness-knob gaps (`-x`, picker-missing, `telemetry off`) to the existing Task-6 test-debt sweep, where they land *with* coverage. The already-logged CRITICAL carry-forward — Task 6 must actively fix the literal `spawn` spawn-id placeholder, since its plan text as written will not — remains the highest-priority open item and is correctly owned outside this task.

---
---

# RE-REVIEW after the bounded fix round (`e7d5fe1..eae39dc`)

**Reviewer:** general-purpose senior code reviewer (independent re-review)
**Date:** 2026-07-24
**Range judged:** `e7d5fe1..eae39dc` — 2 files, +44/−5
**Fix-round report:** `task-005-quality-review-fix.md`

## GATE RESULT: **PASS** — Task 5 may be marked complete.

All five fixes CLOSED, each verified by running the discriminating mutation independently (not accepting the implementer's or controller's proofs). Composed output byte-identical across 5 cases. Two new observations, both Minor, neither blocking.

### What the re-reviewer ran

| # | Action | Result |
|---|---|---|
| 1 | FIX 1 mutation: `:333` → `SUCCESSOR_CMD="TOTALLY-BROKEN"` | **2 FAILED** (`test_picker_manual_when_metadata_degraded[env_extra0]`, `[env_extra1]`) |
| 2 | FIX 1 *subtle* mutation: `:333` → `"claude-picker /pickup $BUNDLE_ID"` (quoting dropped) | **2 FAILED** — exact-equality assertion catches quote loss, not just garbage |
| 3 | FIX 2 mutation: `:310` guard removed, `--session-label` unconditional | **1 FAILED** (`test_empty_label_omits_session_label`), `launch=auto` still held |
| 4 | Byte-identity: old vs new script, fixed `$SPAWN_LOG`, 5 cases | `diff` → **empty. Byte-identical.** |
| 5 | Worked-example comment vs real run, programmatic compare after `<log>` elision | **True** — character-for-character |
| 6 | FIX 3 value-integrity under `BASHOPTS=xpg_echo` (diagnostic emitter neutralized in *both* versions) | old **mangled + truncated**; new **intact** |
| 7 | `shellcheck --severity=warning --external-sources` | Exactly the 2 pre-existing SC2034s. Zero new. |
| 8-11 | `bash -n` under 3.2.57; file suite; full `tests/unit/`; file suite under a 3.2.57 shim | clean; **42**; **595**; **42** |
| 12-13 | Commit scope; tree cleanliness after each mutation | exactly 2 files; restored each time |

### Fix-by-fix gate result

| Fix | Original finding | Result | Evidence |
|---|---|---|---|
| **FIX 1** | Important #2 — picker-manual composed command has zero assertion coverage | **CLOSED** | 2 mutations run; both fail the new assertion. Exact-equality shape catches quote loss, not just garbage. |
| **FIX 2** | Important #3 / M5 — empty-label omission rule untested | **CLOSED** | Guard-removal mutation run; test fails while `launch=auto` still holds. |
| **FIX 3** | Minor #1 — `echo` → `printf` | **CLOSED** | Byte-identical in default env; proved the value survives `xpg_echo` intact where the old form truncated it and **dropped the `/pickup` arg entirely**. |
| **FIX 4** | Minor #2 — `$(shq …)` computed three times | **CLOSED** | Single `PICKUP_ARG` at `:320`, consumed at `:312`/`:331`/`:333`. Byte-identical; placement sound; failure mode neutral-to-better. |
| **FIX 5** | Minor #4 — `[ -n … ] && …` fragility | **CLOSED** | Explicit `if/fi` at `:310`; byte-identical; comment encodes the trap it removes. |

### FIX 3 is materially stronger than the fix report claimed

The report asserted immunity; the re-reviewer proved the consequence. Composing `["--x","a\tb","--y","z\cTRUNCATED"]` under `BASHOPTS=xpg_echo`, measuring `$SUCCESSOR_CMD` itself rather than the diagnostic line:
- **old (`echo`):** `… --x 'a<TAB>b' --y 'z` — `\t` expanded, `\c` **truncated the value mid-string**, leaving an unterminated quote and **losing `/pickup b1` entirely**. A successor command that cannot parse and would not resume the bundle.
- **new (`printf`):** `… --x 'a\tb' --y 'z\cTRUNCATED' '/pickup b1'` — fully intact.

The form is also the safe one: fixed format string `printf '%s\n'` with data as the `%s` *argument*, not `printf "${parts[*]}\n"`.

### New observations (Minor, non-blocking)

1. **`PICKUP_ARG` reads as undefined when `build_successor_cmd` is read top-down** — `:312` (use) vs `:320` (assignment). Genuinely new: pre-fix each site computed inline, so ordering was irrelevant. **Correct today and verified**: bash resolves a function body's variable references at *call* time (`:330`), not definition time (`:303`), and `:320 < :330`; no `exit`/`return`/`set -e` intervenes between `:298` and `:334`; confirmed empirically on the auto, picker-manual, and `--dry-run` paths. Residual cost is readability — the SSOT rationale comment sits at the assignment, not the use. A four-word note at `:312` would remove the trap.
2. **The worked example's `LABEL=` annotation collides with the script's own `$LABEL`** (`:323`). The annotation names the *input* `CLAUDE_CODE_PICKER_LABEL=Proj-Session-2`; the example output correctly shows `--session-label Proj-Session-3` after the increment rule at `:265-274`. But `LABEL` is a live shell variable 13 lines above holding `Proj-Session-3`, so a reader may see an apparent off-by-one and "correct" the example. Naming it `CLAUDE_CODE_PICKER_LABEL=` removes the ambiguity. **The example itself is verified correct.**

### Informational (outside the diff)

The *diagnostic* `echo` at `:336` is itself subject to the same `xpg_echo` mangling. **Pre-existing in `e7d5fe1`, untouched by the fix round.** It does not undermine FIX 3 — it confirms FIX 3 targeted the right line: `:316` produces the *value* Task 6 will execute; `:336` only renders a human-facing stderr line. `BASHOPTS=xpg_echo` is set neither in the hermetic test env nor on any real path.

### Deferred-item routing — confirmed honest

The re-reviewer read `deviations.md` directly rather than trusting the reports' description. The "Task 6 test-debt sweep" section lists all six deferred items with rationale (the `-x` predicate, `command -v claude-picker`, `--telemetry off` on the composed line, `shq` rc-propagation with its "no reachable trigger / emits empty / arity shift not injection" reasoning, `_successor_cmd`'s newline truncation, and the contract probe's missing timeout). The literal `spawn` spawn-id placeholder is separately recorded as a **⚠ CRITICAL carry-forward**, including the caveat that Task 6's plan text *as written will not fix it*. The ledger does not list the two closed items as still open — correct.

### Assessment

**Ready to merge: yes. Gate result: PASS.** All five fixes close their findings, each confirmed by an independently-run discriminating mutation. The three refactors are byte-identical across five independently-captured cases; the one intentional divergence (FIX 3 under `xpg_echo`) is a genuine correctness improvement. The two new observations are Minor readability items with no behavioral consequence on any reachable path. Scope clean: 2 files, no protected path touched. Suites green — 42 on the file, 595 across `tests/unit/`, 42 again under the verified bash floor of 3.2.57. The two Minor items may be folded into the Task 6 sweep or dropped — neither warrants another fix round.
