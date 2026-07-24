# Task 3 — Quality Review Fix Round

**Dispatch marker:** `[task 3 fix]`
**Status:** DONE
**Commit:** `926ab60`
**Trigger:** two ADVISORY items from `task-003-quality-review.md` (verdict was already PASS — these are improvements, not defect fixes).

---

## Fix 1 — numeric env validation

Mirrored the `sdd-pre-dispatch-hook.sh:39-50` house pattern (regex-validate → stderr WARNING → revert to default, never exit) at two sites:

| Var | Regex | Rationale |
|---|---|---|
| `QUOTA_MIN_PCT` (L26-29) | `^[0-9]+(\.[0-9]+)?$` | Widened from the hook's integer-only pattern — a percent threshold may legitimately be fractional (`12.5`) |
| `QUOTA_TIMEOUT` (L153-156) | `^[0-9]+$` | Integer-only, deliberately: POSIX `sleep` guarantees only an integer operand, and this is a coarse watchdog bound where sub-second precision has no use |

Messages: `WARNING: invalid SUPERPOWERS_CMUX_QUOTA_MIN_PCT (<value>) — reverting to default 15.` / same shape for the timeout.

**Deliberate one-line divergence from the hook:** both sites use a named `QUOTA_*_DEFAULT` constant for the `:-` expansion, the revert, and the message. The hook double-hardcodes its literal (`300000` on both the `:-` and revert lines); copying that would put `15`/`60` in the file twice, violating the single-documented-default constraint. Structure and stderr style still mirror the hook.

Fail-open contract untouched — validation only warns, adds no exit path.

**Verification (subagent, throwaway harness outside the repo):**
- Injection string → warns + reverts, then `quota=ok:63.0`, rc 0. `INJECTED-CODE-RAN` never executes. Pre-fix, the raw awk line demonstrably *did* run the injected block and return rc 0 (would classify `low`).
- `SUPERPOWERS_CMUX_QUOTA_TIMEOUT=abc` → warns + reverts; the gate stays **live** rather than silently inerting to `unchecked`.
- `12.5` accepted silently; `12.5.6` warns + reverts.

## Fix 2 — three tests

| Test | Setup | Result | Wall clock |
|---|---|---|---|
| `test_quota_threshold_reads_env_not_hardcoded_default` | `MIN_PCT=70` + `PACE_OK` (63.0%) | exit 3, `quota=low` | 0.70s |
| `test_quota_tool_timeout_proceeds` | `QUOTA_TIMEOUT=1` + `pace_body="exec sleep 20"` | rc 0, `quota=unchecked` | 1.53s |
| `test_quota_threshold_boundary_is_strict_less_than` (sanctioned optional) | `MIN_PCT=63` + 63.0% | rc 0, `quota=ok` | 0.71s |

**Mutation-proven:** replacing `$QUOTA_MIN_PCT` with a literal `15` in the awk comparison fails the shared-constant test **and only that test** (1 failed / 23 passed); script restored, confirmed via `git diff --stat`. This is the guard against the hardcoded-constant failure mode.

The timeout test covers the watchdog-kill → fail-open path none of the existing 7 reach (they cover absent / non-zero / unparseable, never a kill). Honest caveat from the subagent: it does not *assert* env consumption — if the timeout were ignored it would still pass, just ~20s instead of 1.5s. The 1s bound is the speed guard; nothing can hang.

## Controller-independent verification

Not taken on report alone. Controller re-ran:

- `.venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -q` → **24 passed in 11.76s** (no stall regression)
- `bash -n` → syntax OK
- `shellcheck --severity=warning` → **7 SC2034 only** (the known placeholder set), no new findings
- `grep` on the script confirms `15` and `60` each appear in exactly one default assignment, referenced by constant everywhere else
- `git show --stat 926ab60` → exactly the two in-scope files; `git status` shows no stray scratch files in the repo

Subagent-reported full unit suite: **577 passed in 93.78s**.

## Open gap accepted (subagent-raised, controller-dispositioned)

Fix 1's env validation has **no committed regression test** — deleting either regex block leaves all 24 tests green, because the shared-constant test pins env *consumption*, not *validation*.

**Controller disposition: DEFERRED to Task 6, with reason.** The awk-injection vector is self-injection through one's own environment variable — anyone who can set `SUPERPOWERS_CMUX_QUOTA_MIN_PCT` can already execute arbitrary commands, so this is a robustness guard, not a privilege boundary. Both invalid-input directions fail safe (revert to default). The genuine value — preventing a silently-inert gate — is already covered by the timeout test. Task 3 has consumed three dispatches and Tasks 4-5 are the densest in the module; Task 6 is the natural sweep point for script-level test debt. Tracked in `deviations.md`.
