# Task 3 — Code Quality Review

**Verdict: PASS** — no BLOCKING defects. Four ADVISORY items.
**Review tier:** full (dispatched, general-purpose)
**Audited commit:** `7131698`

The fail-open contract is the load-bearing property and it holds on every path the reviewer could construct.

---

## Verification performed

The reviewer drove the **real** script through the repo's harness across failure shapes no test covers. All → `quota=unchecked`, rc 0:

| Condition | Result |
|---|---|
| 2 MB tool output (>`ARG_MAX` 1048576) | `unchecked`, 0.8s, no stray stderr |
| Tool writes stderr only, empty stdout, rc 0 | `unchecked` |
| `remaining_pct: null` / `windows` a dict not list | `unchecked` (TypeError/AttributeError caught) |
| `SUPERPOWERS_ROOT` bogus → no venv `$PYTHON` | `ok` — L18 PATH fallback works |
| `TMPDIR` unwritable | BSD `mktemp` falls back to `/var/folders/...`; still works |
| Timeout (`QUOTA_TIMEOUT=1`, `exec sleep 20`) | `unchecked`, rc 0, **1.5s** |
| Paths with spaces (HOME, bundles, stubs, override tool) | all correct |

Also correct-and-untested: `remaining_pct` as the **string** `"8.0"` → `float()` accepts → correctly classifies `low`/exit 3. Boundary `pct == MIN` → `ok` (strict `<`). `shellcheck --severity=warning` clean apart from SC2034s; `bash -n` clean.

**Two implementer concerns do NOT reproduce.** No `Killed: 9` job notice appears in non-interactive bash (stdout was exactly `[unchecked(rc=137)]`). The orphaned `sleep` does **not** hold the caller's stdout pipe (the watcher's `>/dev/null 2>&1` covers it) — a capturing caller returns in 0s. **The stderr-corruption risk is not real.**

## Findings

### [ADVISORY] convention-fit — the two new numeric env vars skip the house validation guard (`spawn-handoff-session.sh:21,139`)

`sdd-pre-dispatch-hook.sh:41–50` — same scripts directory, same feature family — establishes the convention: regex-validate numeric env thresholds, warn on stderr, revert to defaults. `QUOTA_MIN_PCT` and `QUOTA_TIMEOUT` get no such guard. One gap, three observed behaviors:

- **awk code injection.** L168 interpolates `$QUOTA_MIN_PCT` into an awk program. Confirmed executable: `SUPERPOWERS_CMUX_QUOTA_MIN_PCT='999)} END{ print "INJECTED-CODE-RAN" > "/dev/stderr" } BEGIN{ x=(0'` runs the injected block **and** returns rc 0, flipping a healthy 63% to `low`. Self-injection via one's own env var ⇒ low severity, but it is the same expression producing the dispositioned "non-numeric compares against 0" case.
- **A typo'd `SUPERPOWERS_CMUX_QUOTA_TIMEOUT` silently disables the gate.** `sleep abc` fails instantly, the watcher `kill -9`s the tool immediately, rc≠0 → `unchecked`. 8/8 trials `unchecked` — deterministic, not a race, and it fails in the *safe* direction. But the quota check becomes permanently inert with no diagnostic.

Fix matching house style; note `QUOTA_MIN_PCT` may legitimately be a float, so the hook's integer regex needs widening to `^[0-9]+(\.[0-9]+)?$`.

### [ADVISORY] test coverage — a hardcoded `15` would pass all 7 quota tests (`test_spawn_handoff.py:167–202`)

In fairness to the plan's tests: they *do* catch a basic fail-open inversion (`unchecked`→exit 3 trips the rc-0 assertion; `low`→proceed trips the rc-3 assertion). The gap is narrower and maps onto CLAUDE.md's Shared Constants principle — **nothing pins that `$QUOTA_MIN_PCT` is actually consulted.** Both gaps closable cheaply (reviewer-measured):

- `env_extra={"SUPERPOWERS_CMUX_QUOTA_MIN_PCT": "70"}` + `PACE_OK` → exit 3, **0.6s**. Pins the shared constant.
- `env_extra={"SUPERPOWERS_CMUX_QUOTA_TIMEOUT": "1"}` + `pace_body="exec sleep 20"` → rc 0, `unchecked`, **1.5s**. Closes the class verified only out-of-band. The plan forbade a *`sleep`-based CI test* — that rules out a 60s test, not a 1s bounded one.
- Boundary `pct == MIN` → `ok` is likewise verified only out-of-band.

The plan's tests are thin here, not badly written.

### [ADVISORY] the implementer report's orphan concern understates scope — code fine, prose needs correcting

The report says "*A timeout* leaves one orphaned `sleep`". It happens on **every** invocation including the success path and `--dry-run`: with a fast tool, `kill $watcher` reaps the subshell but `sleep` reparents to PPID 1 and lives the full `QUOTA_TIMEOUT` (observed `98498 1 00:01 sleep 45`). In production: a stray `sleep 60` for 60s after every spawn. It is invisible in output and cannot stall or corrupt the caller (measured 0s, `/dev/null`'d streams) — visible only via `ps`. Close to inherent in the no-`timeout`-on-macOS watcher pattern (killing the process group would kill the caller, as the script isn't a session leader), so **accepting it is reasonable**; only the record needs correcting so Tasks 4-6 aren't misled. The *code comment* (L145–148) is accurate and never claims orphan-freedom.

### [ADVISORY] `nan` classification is a sibling of the dispositioned `Infinity` case (L168)

`float("nan")` → `nan < MIN` = false → `ok`. Same root cause; folded into the existing disposition.

## Resource hygiene — clean

Temp file created `0600`, `mktemp` failure handled (`|| { echo "unchecked"; return 0; }`), `rm -f` covers every post-`mktemp` path **including the `exit 3` low-quota route** — `check_quota` removes the file *before* returning the class, so the caller's `exit 3` cannot skip it. Survived a SIGINT probe. Concurrency safe (`mktemp` unique per run, no shared paths). **No EXIT trap**, consistent with house style (`sdd-pre-dispatch-hook.sh:274`, `check-hooks.sh:83` both use bare `mktemp` + explicit `rm`; traps appear only in `tests/claude-code/` harnesses). `wait $pid` correct — bash retains a background job's exit status, so a tool exiting before the `wait` still yields the true rc.

## Patterns to copy at the Task 4-6 markers

- **`$out` passed as `sys.argv[1]`, never interpolated into the Python program text** (L156-157); heredoc quoted `<<'PY'`. Reuse verbatim for Task 4's manifest/append-prompt decoding.
- **Temp file over pipe for bounded subprocesses**, with the *why* in the comment (L145-148).
- **Fail-open discipline: every branch is `echo <class>; return 0`**; the one bare-status line (L168 `awk`) is consumed by an `if`.
- **`cmux notify ... 2>/dev/null || true`** (L174) matches the hop-limit path (L125) — notification never fails the flow.
- No EXIT trap exists: **Tasks 4-6 must self-clean any temp resources**, in the same immediate-`rm -f` style.
- `QUOTA_STATUS` (SC2034) is deliberate forward-scaffolding consistent with five pre-existing peers (`PICKER_CONTRACT`, `DRY_RUN`, `FEATURE_NAME`, `SPAWN_LOG`, `SP_HOP`) — uniform known pattern, not new debt.

---

## Controller disposition

Reviewer's recommendation: propagate the numeric-env guard, add the two sub-2s tests, correct the orphan wording. Explicitly "none of these should block marking Task 3 complete."

Controller elected to **action the two code items now** (in Task 3's own scope, its own env vars and test file, with reviewer-measured recipes) via a `[task 3 fix]` dispatch rather than deferring — see `task-003-quality-review-fix.md` for the fix round and its verification.
