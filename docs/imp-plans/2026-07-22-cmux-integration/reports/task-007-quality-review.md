# Task 7 — Code Quality Review (Sweep A)

**Reviewer:** general-purpose code quality reviewer (template: `skills/requesting-code-review/code-reviewer.md`)
**Scope:** `git diff 518875c..8ea8509` — `tests/unit/spawn_handoff_helpers.py`, `tests/unit/test_spawn_handoff.py`

## Assessment: **PASS with fixes**

One Important comment-accuracy fix in Task 7's own file; two coverage residuals routed to Task 8.

## Strengths

- **The mutation discipline is real, not performative.** M4b/M5b (delete only the reassignment, keep the WARNING) isolate the behavioral half from the diagnostic half — exactly the discrimination Task 6's seven hollow assertions lacked. Running M1b and recording its GREEN rather than inferring it, then disclosing the substituted mutation as a Deviation, is the right handling of a plan defect.
- **Test-echo collision genuinely avoided, including second-order.** The telemetry test anchors on `_successor_cmd(r)`; `_warning_lines` (`:1051`) reads `r.stderr` only and prefix-anchors. The reviewer checked *preconditions* too, not just asserted strings: in the two env tests the quota gate fires at script `:190` **before** launch composition, so their lack of `install_version`/`_meta` cannot make the assertion vacuously true by another route.
- **Knobs are minimal, orthogonal, default-preserving.** Test-file diff is a pure append; zero existing tests edited; knobs landed and run at 58-green before any new test.
- **`else: assert picker_body is None`** (`spawn_handoff_helpers.py:138`) turns a meaningless argument combination into a loud harness error rather than a silently-ignored argument.

## Issues

### Important

**1. `tests/unit/test_spawn_handoff.py:1007-1010` — the rationale comment is factually wrong.**
The comment reads "Only the `-f` half was covered (via a version name with no file at all)". A **nonexistent path fails `[ -x ]` too**, so the pre-existing `test_picker_manual_when_metadata_degraded` param pins the *conjunction*, not the `-f` half. Neither half was individually covered before this task; after it, `-x` is pinned and `-f` still is not.

*Evidence:* MX-A — reducing `:298` to a bare `[ -x … ]` leaves all **63** tests green. **Controller independently re-ran this: 63 passed, script restored, diff verified empty.**

*Failure scenario the missing `-f` guards:* a version stored as a **directory** at `~/.local/share/claude/versions/2.1.218` (dirs are 0755, so `-x` passes, `-f` fails). Preflight would say `launch=auto`; the picker's own `find -type f -perm -u+x` would never discover it → auto-spawn against a version the picker refuses — precisely what script `:296-297` says the predicate exists to prevent.

*Fix (this task, coverage-only, no script edit):* correct the comment. Adding the `-f` test (install a *directory* named `2.1.218`) is a Task-8 item.

**2. Same class, weaker — the fractional half of the `QUOTA_MIN_PCT` regex is unpinned.**
`spawn-handoff-session.sh:27` is `^[0-9]+(\.[0-9]+)?$`, and the script comment blesses `12.5` as legitimate. Every MIN_PCT value in the suite is an integer (`"70"` `:216`, `"63"` `:231`, `"abc"` `:1076`), so tightening the regex to `^[0-9]+$` — which would make a legitimate fractional threshold silently revert to 15 — leaves all 63 green (MX-B).

*Fix:* Task-8 checkbox — one test with `SUPERPOWERS_CMUX_QUOTA_MIN_PCT="12.5"` asserting **no** WARNING and `quota=ok` at a 63.0% reading.

**Disposition note from the reviewer:** "this run's own lesson is *disposition ≠ done*. Both residuals should land as **checkboxes in Task 8**, not as prose notes in a report." — Controller agreed and did exactly that.

### Minor

3. **`_only_failing_predicate_is` (`:981`) is named broader than it can guarantee** — picker absence necessarily fails two predicates. Concurs with the spec review's ADVISORY; a naming nit, not a defect.
4. **`_path_without` (`spawn_handoff_helpers.py:91`) edge cases.** The disclosed one (a PATH dir holding both `claude-picker` and `git`) is the real one and fails loudly. Two undisclosed ones are behavior-neutral: dropping empty PATH entries (POSIX "current dir") and resolving relative entries against pytest's cwd rather than `ctx["wt"]`. Both apply only on the `picker_stub=False` path and both err toward *more* filtering, i.e. toward the test's intent. `os.path.exists` also over-filters vs `command -v` — again conservative. No change wanted.
5. **`test_invalid_quota_timeout_warns_and_quota_gate_stays_live` (`:1085`) has a timing dependency, but not a flaky one.** 1s tool vs. the reverted 60s watchdog is a 60× margin, and the mutation's failure mode is an *instant* kill, so discrimination is robust. Adds ~1s to the suite. Acceptable.
6. **Pyright noise — correctly ignored, both.** `_hermetic_picker_env` "not accessed" is a false positive (autouse fixture). `_meta(telem=None)` at `:323`/`:1034` is inferred-`str`-from-default noise; the file carries **zero** annotations, so adding one here would be the inconsistency, not the fix.

## Dead code, SSOT, size

- **No dead code.** The diff adds no imports. Live callers verified: `_only_failing_predicate_is` (2), `_warning_lines` (2), `_path_without` (1), `picker_stub=False` (1), `executable=False` (1), and the `else:` assert branch.
- **SSOT clean.** No frozen contract constant restated — the Task-6 failure mode did not recur. `QUOTA_WARN_PREFIX` (`:1048`) pins the script's user-facing contract string, which is the test's job. `_warning_lines` duplicates no existing helper.
- **Size contribution** (+50 helpers / +127 tests) proportionate to 5 tests + 3 helpers.

## Data path traced end-to-end

`env_extra={"SUPERPOWERS_CMUX_QUOTA_TIMEOUT": "abc"}` → `run_spawn` `env.update` (`helpers:153`) → subprocess env → script `:154` `QUOTA_TIMEOUT="${…:-60}"` → `:155` regex fails → stderr WARNING + revert to 60 → `check_quota` watchdog `sleep 60` → `sleep 1; PACE_LOW` stub completes well inside → awk `8.0 < 15` → `low:8.0` → `:193` stderr `quota=low:8.0` + `exit 3`. Asserted via `_warning_lines(r,"TIMEOUT")` (stderr-only) + `rc == 3` + `"quota=low" in r.stderr`. Consistent; **all three assertions stderr-anchored**, no stdout contamination path. Exit-code ladder (0/3/1) untouched.

## Surviving-mutation hunt (required section)

Candidates considered per test, weakest-edit-first. M1/M1b/M2/M3/M4b/M5b were NOT re-run (already covered by spec review + controller).

| Test | Weakest edits considered | Result |
|---|---|---|
| `picker_absent` | delete `:299` alone | already known GREEN (M1b, disclosed) |
| `picker_absent` | delete `:301` (probe) alone | ruled out — reddens pre-existing `test_picker_manual_when_contract_wrong` |
| `non_executable_version` | **drop the `-f` half, keep `[ -x ]`** | **RAN — SURVIVES. 63 passed.** → Important 1 |
| `telemetry_off` | hardcode `"--telemetry" "off"` | ruled out — `test_auto_mode_composes_exact_command:438` asserts `--telemetry on` |
| `telemetry_off` | invert `= "1"` to `= "0"` in resolution | ruled out — reddens `test_telemetry_on_and_off` r_on |
| `min_pct` | revert to a *different* number > 8.0 | survives, but **disclosed** (Concerns 2) as the deliberate shared-constants trade — not counted as new |
| `min_pct` | **tighten regex to `^[0-9]+$`** | **RAN — SURVIVES. 63 passed.** → Important 2 |
| `timeout` | revert to any value > 1s | survives; same disclosed class, not counted as new |
| `timeout` | loosen regex to accept fractional | survives; strictly weaker than MX-B (no reachable behavioral consequence), not worth a checkbox |

**Two new surviving mutations found**, both in the `-f`/regex-half class the plan's Step 3/Step 5 wording under-specified. Neither is a defect in the delivered script (unmodified and correct); both are coverage residuals whose *documentation* inside Task 7's own file is wrong (Important 1).

## Mutation restore confirmation

Both reviewer mutations restored; `git diff --name-only` and `git status --porcelain` on `spawn-handoff-session.sh` verified **empty** after each restore, lines 27 / 298 visually match HEAD. Controller re-verified after the review returned, and again after its own MX-A re-run.

---

---

# Re-review (round 2) — after fix commit `4f1328f`

**Dispatch marker:** `[task 7 re-review:quality]`

## Round-2 initial finding — RAISED, THEN WITHDRAWN

The re-review initially returned PASS-with-fixes, claiming the fix introduced a *new* false sub-claim: that the parenthetical "the **one** pre-existing param that reaches it" was wrong because **both** params reach `:298`. Its reasoning: `run_spawn` does `env = dict(os.environ)` and `if env_extra:` skips the update for a falsy `{}`, so `{}` would inherit the ambient `CLAUDE_CODE_PICKER_VERSION` from this picker-launched machine. It reported an empirical "throwaway test" confirming `launch=auto`.

**The controller did not accept this.** It contradicted a documented invariant of this suite — the autouse `_hermetic_picker_env` fixture exists precisely to stop that leak.

### Controller probe (with a positive control)

Injected into `preflight_ok()`, above the `-n` guard:

```
[ -z "${CLAUDE_CODE_PICKER_VERSION:-}" ] || exit 42
```

Then ran each param separately **against the real test file**, so the module-scoped autouse fixture applies:

| Param | Result | Meaning |
|---|---|---|
| `test_picker_manual_when_metadata_degraded[env_extra1]` (`9.9.9`) | **FAILED** | **Positive control** — proves the injected guard is live and does fire when the var is set |
| `test_picker_manual_when_metadata_degraded[env_extra0]` (`{}`) | **1 passed** | Guard did not fire ⇒ `CLAUDE_CODE_PICKER_VERSION` genuinely **unset** ⇒ stops at `:294`, never reaches `:298` |

Script restored; `git diff --name-only` verified empty.

Corroborating mechanism: `monkeypatch.delenv` mutates `os.environ`; `run_spawn` copies it **after** the fixture runs; `if env_extra:` skips the falsy `{}` — so `{}` receives the *hermetic* environment, not the ambient one. Two independent lines of evidence agree.

### Reviewer's response — finding withdrawn

The re-reviewer verified the mechanism directly (`_hermetic_picker_env` at `:271-274`, `autouse=True`, module-scoped; `PICKER_ENV_VARS` at `:262-268` includes `CLAUDE_CODE_PICKER_VERSION`; `tests/unit/conftest.py` has no `PICKER` reference) and concluded:

> "My throwaway probe lived in a scratchpad file, so that fixture never applied to it — the ambient leak I 'proved' was an artifact of my own harness, not of the real test. … Both lines of evidence are sound; mine was not."

**Corrected verdict: PASS.** The parenthetical is correct as written.

**The reviewer also WITHDREW its own suggested alternative wording** ("the pre-existing degraded-metadata params install no version file at all, so both fail BOTH halves"), and the controller did **not** adopt it:

> "'Both fail BOTH halves' is worse than the current text, not more durable. The `{}` param never evaluates `:298`, so saying it 'fails both halves' asserts an outcome for a predicate that is never reached — vacuously defensible, but it is the same class of imprecise coverage claim the original Important finding was about."

Logged as **premise disproven, wording NOT adopted — current text is more precise.**

## Round-2 verified claims (all stand)

Conjunction-only prior coverage; `-x` isolated via `executable=False` at mode 0644; `-f` unpinned; the directory-at-0755 failure scenario accurate against `:294-302`; the Task 8 Step 4b cross-reference resolves and matches. Scope comment-only; `git diff cfe8c27..HEAD -- skills/` empty; script clean; **63 passed**.

## New residual surfaced by round 2 (routed to Task 8)

**`_hermetic_picker_env` is module-scoped, not project-scoped.** It is defined in `test_spawn_handoff.py`, not `tests/unit/conftest.py`, so any future spawn-handoff test placed in a *different* file silently inherits the developer's ambient picker env — and "metadata absent" cases stop meaning absent. The reviewer's own bad probe is the existence proof. Moving the fixture to `tests/unit/conftest.py` would close it. Added as **Task 8 Step 4d**.

## Final round-2 assessment: **PASS**

