# Task 3 — Spec Compliance Review

**Verdict: PASS** — spec compliant and contract compliant.
**Review tier:** full (dispatched, general-purpose)
**Audited commit:** `7131698` (`git diff 019b65f..7131698`)

Both implementer deviations verified **empirically** as JUSTIFIED (real plan defect, minimal fix). One ADVISORY carried: the plan doc still holds the broken snippet.

---

## Deviation 1 — timeout capture rewritten to `mktemp` + `wait`: **JUSTIFIED (real defect, minimal fix)**

Reviewer reconstructed the plan's original `check_quota()` verbatim in a scratch script and timed it against stub tools (scratch deleted afterward):

| Variant | Tool shape | `QUOTA_TIMEOUT` | Wall clock | Result |
|---|---|---|---|---|
| Plan original | fast (instant echo) | 4s | **4.067s** | `ok:63.0` |
| Minimal fix (`>/dev/null 2>&1` on watcher) | fast | 4s | 0.065s | `ok:63.0` |
| Minimal fix | forks a `sleep 30` child | 4s | **30.3s** | `ok:63.0` |
| Committed impl | fast / forking / `exec sleep 60` / forking-hang | 3s | 0.059s / 0.057s / **3.047s** / **3.049s** | ok / ok / unchecked / unchecked |

The plan's snippet stalls the **full timeout on the success path** — confirmed. The fd-inheritance reasoning is correct: the watcher's `sleep` grandchild holds the command-substitution pipe's write end.

The implementer's claim that the minimal watcher-redirect fix is insufficient is **also confirmed**: it fixes the fast path, but a *forking* tool still blows through the timeout entirely (30.3s under a 4s limit) — i.e. the minimal fix silently voids the spec's 60s bound. The committed temp-file version is the smallest change that actually honors the timeout across all four shapes. **Not excessive.**

## Deviation 2 — default-only PATH fallback: **JUSTIFIED (real defect, minimal fix)**

`spawn_handoff_helpers.py:run_spawn` does set `env["HOME"] = str(tmp_path / "home")` and installs the `claude-usage-pace` stub only on `PATH`. Both halves proved by patching the committed script and re-running the plan's own tests (repo restored afterward; `git status` clean on the script):

- **Variant A** — plan's verbatim resolution line (no fallback): `test_quota_low_exits_3` and `test_quota_ok_proceeds` **FAIL** (both get `quota=unchecked`). The plan's Step 2 snippet and its own Step 1 tests are mutually inconsistent; **the task as written could not pass.**
- **Variant B** — fallback made unconditional (drop the `[ -z "$SUPERPOWERS_CMUX_QUOTA_TOOL" ]` guard): `test_quota_tool_absent_proceeds` **FAILS** (finds the PATH stub, prints `quota=ok:63.0`). The override guard is load-bearing and the absent-test is **non-vacuous** under the shipped code.

The plan corroborates PATH resolution as the intended test mechanism (`module-1-spawn-script.md:175` `make_stub(stubs, "claude-usage-pace", pace_body)`; `:199` "on a per-test PATH"). Worst case is safe: if `command -v` finds nothing, `QUOTA_TOOL=""` → `[ ! -x "" ]` → `unchecked`, so the fallback can never produce a spurious refusal.

## Contract verification — quota fail-open

All seven classes reach `unchecked` by code reading; six covered by tests; timeout verified by the reviewer's own timing runs:

| Class | Mechanism | Verified by |
|---|---|---|
| tool absent | `[ ! -x "$QUOTA_TOOL" ]` (incl. empty string) | test + variant B |
| non-zero exit | `rc -ne 0` | `PACE_NONZERO` |
| timeout | `kill -9` → `wait` rc 137 → `rc -ne 0` | timing runs above |
| unparseable JSON | python `except` → exit 1 → `pct` empty | `PACE_MALFORMED` |
| `session` window missing | `w[0]` IndexError | `PACE_MISSING_WINDOW` |
| `remaining_pct` missing | KeyError | `PACE_MISSING_FIELD` |
| non-numeric | `float()` ValueError/TypeError | `except` branch |

Only a parsed numeric `< $QUOTA_MIN_PCT` exits 3 (`awk` strict `<`; equality classifies `ok`). `$QUOTA_MIN_PCT` used in both the comparison and the notify body; **no literal `15` anywhere** in either file. `$out` passed as `sys.argv[1]`, not interpolated — no injection surface. House style honored: no `set -u`, no `grep -q` pipeline, `$PYTHON` used.

## Scope

Commit `7131698` touches exactly the two in-scope files. No baselined hook, SDD `SKILL.md`, or `verify-symlink-install.sh` touched. Task 4/5/6 markers survive intact at lines 181–182. The plan's test code was preserved **verbatim** (only `black` reflow — statement split and import wrapping; zero semantic change).

> Note for anyone glancing at `git status`: `context-observations.log` and `.dispatch-log` show Modified in the working tree, but those are the pre-dispatch hook's own logging from the review dispatches — **outside the audited commit**, not implementer changes.

## Report completeness

`validate-report.py` → `COMPLETE`, all 5 prose sections present, none empty. `tests: 7 written / 7 passing` matches reality (`-k quota` → 7 passed; full file 21/21 in 8.58s — no residual stall). Source Files Read and CLAUDE.md Files Read populated; the "only CLAUDE.md in the tree" claim verified via `find` — correct.

---

## Findings

- **[ADVISORY] [PLAN-DEFECT]** `module-1-spawn-script.md` Task 3 Step 2 (the `check_quota()` snippet, ~L600+) still contains the broken command-substitution timeout **and** the fallback-less `QUOTA_TOOL=` line. A future re-run copying it verbatim gets a 60s stall on every spawn plus two tests that cannot pass. **Correction target is `module-1-spawn-script.md` only** — reviewer grepped `plan.md` and `spec.md`; neither mirrors the snippet.
- **[ADVISORY] [INHERITED-EDGE]** awk line: a JSON `Infinity` for `remaining_pct` parses via `float()` → prints `inf` → awk treats it as an uninitialized variable (0) → classifies **low → exit 3** rather than failing open. Confirmed empirically (`awk "BEGIN{exit !(inf < 15)}"` → true). Inherited from the plan's verbatim awk line; requires non-standard JSON the real tool won't emit. No action needed.
- **[ADVISORY] [INHERITED-EDGE]** A non-numeric `SUPERPOWERS_CMUX_QUOTA_MIN_PCT` makes awk compare against 0 → classifies `ok` (proceed). Plan-inherited; direction is fail-open, the safe side.
- **No BLOCKING findings.** `QUOTA_STATUS` set-but-unused (SC2034) is plan-mandated forward scaffolding for Task 6, tracked in `deviations.md` for disposition there.
