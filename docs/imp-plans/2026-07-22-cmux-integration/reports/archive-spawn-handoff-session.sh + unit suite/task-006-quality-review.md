# Task 6 — Code Quality Review

**Reviewed:** cumulative `3f4f0ae..3491171` (feature `5c6e4d9` + fix round `3491171`)
**Date:** 2026-07-24
**Assessment: PASS with fixes** — no Critical. 3 Important, 4 Minor. **5 mutations SURVIVED a 56-green suite.**

## Strengths

- **The §5.4d spawn-id fix is real work the plan would have shipped broken.** `_fallback_spawn_id()`
  is anchored on the runtime-deferred `$(date …)` field rather than "some uuid somewhere," which is
  why M6 goes RED on correlation while staying green on shape.
- **Worked-example comment (`:341-347`) VERIFIED against a real run**, not trusted. Reproduced
  through the harness (LABEL=`Proj-Session-2`, telemetry=1, args
  `["--append-system-prompt-file","/tmp/a b.md"]`, version 2.1.218) — byte-identical to the comment
  modulo the uuid and log path, exactly as the comment claims.
- **`test_reservation_lands_before_cmux_new_workspace_runs` is sound, not over-clever.** Snapshotting
  from inside the stub proves *time*-ordering (hop consumed at `new-workspace` time), which file
  order cannot. The stub is the only observer positioned at that instant, and using `cp` with the
  existing `cmux_body`/`env_extra` knobs kept the read-only helper untouched.
- **bash 3.2.57 verified by execution:** `local -a nw` + `CMUX_QUIET=1 "${nw[@]}"` +
  `${t//\{workspace\}/W}` → `rc=0 sub=a W b`. `bash -n` clean. `scripts/lint-shell.sh --all` reports
  **zero findings for this script** (its exit-1 is the pre-existing N32 baseline in unrelated files).
- `rc` handling correct: `local rc` declared separately (`:382`), `rc=$?` taken standalone from the
  redirected command (`:389`) — no `local rc=$(…)` trap. No `set -u`, no producer-into-`grep -q`.
- Growth proportionate: +124 script lines for a genuinely new phase, comment density matching the
  Task-5 habit (every non-obvious construct carries its *why*).

## Issues

### Important

**1. Spawn-failure branch can lose `print_manual_instructions` with all 56 tests green.** `:443`

Spec §5.5: *"Every non-spawn path prints the manual instructions — the protocol never dead-ends."*
The guarding assertion in `test_spawn_failure_keeps_hop_exits_3` is
`"/pickup b1" in (r.stdout + r.stderr)` — but under `_reach_spawn` that string is **already** on
stderr from the `successor command:` echo at `:355`. The assertion never sees the instructions.

**Proof — MX2 (delete the `print_manual_instructions` call on the failure branch): `56 passed`.**

This is the **same test-echo collision class** that was a CRITICAL carry-forward for Task 5,
recurring in a new location. The path it fails to guard is the worst one: a hop is already consumed
and the user *must* recover manually.

Fix: assert distinctive instruction text (e.g. `"Manual resume required"`, `"cd \"…\" && claude"`).

**2. `--cwd` is asserted as a flag, never as a value.** `:385`, test `:592`

`for tok in ["--name", "--cwd", "--command", "--focus false"]` checks presence only.
**Proof — MX1 (`--cwd "$cwd"` → `--cwd /tmp`): `56 passed`.**

Not cosmetic: per repo `CLAUDE.md` ("Worktree Sessions"), hooks resolve CWD from session start, so a
successor spawned in the wrong directory produces a silently mis-rooted SDD session.
Fix: assert the `--cwd $WORKTREE_ROOT` *value*.

**3. Frozen contract constants are dead, and Task 6 duplicated them instead of consuming them.**
`tests/unit/test_spawn_handoff.py:15-16`

`CMUX_NEW_WORKSPACE_FLAGS` / `CMUX_NOTIFY_FLAGS` carry the comment *"the exact-argv assertions in
later tasks must be updated too."* **Task 6 IS that later task** — and `:592` hardcodes
`["--name", "--cwd", "--command", "--focus false"]`, a literal duplicate. Verified dead at BASE_SHA
(definitions only), so these commits did not orphan them — but they are the commits that were
supposed to close the loop and instead entrenched the duplication. Undocumented in either report's
Deviations. **SSOT violation.**

### Minor

**4. `# Pure mechanics (no SDD policy)` overclaims.** `:359, :400` — the notify *body* is
parameterized via `{workspace}`, but `--title "SDD handoff"` is hardcoded SDD branding inside the
"generic, extraction-ready" core; on extraction it is the one line a caller must edit. Either
parameterize the title or soften the comment to "no SDD *sequencing* policy."
Otherwise the global-publish + placeholder shape is the right call in bash: `local` cannot return a
second value; a nameref (`declare -n`) is bash 4.3+, off the 3.2.57 floor; and returning the ref on
stdout collides with the rc-must-survive constraint the fix round exists to protect. **No simpler
shape available.**

**5. Log-record field values unasserted beyond `workspace=`.** `:423, :434` — `_spawn_log_records()`
extracts only (type, id); `_outcome_workspace()` only `workspace`.
**Proof — MX4 (`intent hop=` → `hop=Z1`): `56 passed`.** §5.4d's log format also pins `launch`,
`bundle`, `quota` — all unchecked.

**6. Notify title/name values unasserted.** **MX5 (`--title` → `"BOGUS TITLE"`): `56 passed`;
MX3 (`--name "$ws_name"` → `--name BOGUS`): `56 passed`.** Both are spec-named strings (§5.4d
steps 2–3). Same root cause as #2.

**7. `$out_f` leaks on signal death only.** `:386-392` — every normal return path `rm -f`s; there is
no `trap`; `mktemp` lands in `$TMPDIR`. Acceptable; noted for completeness. The
`awk '/^OK[ \t]/{print $2; exit}'` parse is **locale-safe** (bracket expression of literal bytes,
not a character class) and correctly first-match-wins.

## Scope — clean

Diff touches exactly the two in-scope files; `spawn_handoff_helpers.py` untouched; nothing from the
deferred list (`max(0,…)`, lone-surrogate wrap, `shq` rc, contract-probe timeout, the
unchecked-reservation-write advisory) was modified. `APPEND_TARGET_DIR` (`:218`) is still consumed
at `:219` — **vestigial-but-used, documented in Concerns, NOT dead code.** `out_f` and `nw` both
used. No earlier-task code became unreachable.

## Mutation Results

| ID | Mutation | Outcome |
|---|---|---|
| MX1 | `--cwd "$cwd"` → `--cwd /tmp` | **SURVIVED** — 56 passed |
| MX2 | drop `print_manual_instructions` on spawn-failure branch | **SURVIVED** — 56 passed |
| MX3 | `--name "$ws_name"` → `--name BOGUS` | **SURVIVED** — 56 passed |
| MX4 | intent record `hop=` value corrupted (`hop=Z1`) | **SURVIVED** — 56 passed |
| MX5 | notify `--title "SDD handoff"` → `"BOGUS TITLE"` | **SURVIVED** — 56 passed |

Baseline before and after: `56 passed`; script restored byte-clean. Not re-run: M-A/B/D/E/F/G,
M1–M6 (already reproduced elsewhere). `--focus false` and the auto-path `--command` *content* were
evaluated as candidates and are **genuinely covered** (`:592` and
`test_append_prompt_file_written_on_real_spawn`) — not mutated.

## Assessment

**PASS with fixes.** The implementation is correct and well-reasoned, and the two hardest things
about it — reservation *timing* and `$?` survival under capture — are proven by tests that genuinely
discriminate. The task is functionally done. But five mutations survived a 56-green suite, and two
of them (#1 dead-ended failure path, #2 wrong `--cwd`) break behavior the spec explicitly pins. Add
those assertions before closing Module 1; #3 (dead contract constants) should be closed in the same
edit since it is the SSOT the other fixes want.

---

# QUALITY RE-REVIEW after `[task 6 fix] round 2` — **PASS**

**Re-reviewed:** commit `ec0df92` (cumulative `3f4f0ae..ec0df92`)
**Verdict: PASS.** All five previously-surviving mutations CLOSED. No Critical, no Important.
2 new Minor survivors (coverage gaps in already-correct code). **Task 6 is done; Module 1 can close.**

## C1 — Verification table: all four re-run by the reviewer, all CLOSED

| ID | Mutation | Result | Caught by |
|---|---|---|---|
| MX1 | `--cwd "$cwd"` → `--cwd /tmp` | **RED** 1/57 | `test_new_workspace_and_notify_argv_values_match_spec` |
| MX3 | `--name "$ws_name"` → `--name BOGUS` | **RED** 1/57 | same |
| MX5 | notify `--title` → `"BOGUS TITLE"` | **RED** 1/57 | same |
| MX4 | `intent hop=%s` → `hop=9%s` | **RED** 1/57 | `test_spawn_log_record_fields_match_spec_log_format` |

Each failed **exactly one** test — the assertions are targeted, not collateral.
(MX2 was independently re-run by the controller → RED.)

## C2 — The assertions are RIGHT, not merely red

- **`--cwd`:** the script derives `WORKTREE_ROOT="$(git rev-parse --show-toplevel)"` (`:53`); the
  test recomputes it via an independent `subprocess` run (`test:588`) rather than reading back the
  recorded argv — so it is **not** `x == x`. The `/var`→`/private/var` reasoning holds
  (`realpath()` would drift on macOS).
- **Unique strings:** `Manual resume required` → 1 hit (`:68`); `Then STOP the current session` →
  1 hit (`:72`); both only inside `print_manual_instructions`. The sole other stdout emitter
  (`:440`) is the success branch, mutually exclusive. **No collision** — asserting on `r.stdout`
  alone kills the Task-5 stderr-echo class.
- **Log fields:** `:715-720` pins real values (`hop=1`, `workspace=(spawned)`, `launch=auto`,
  `bundle=b1`, `quota` prefix), not key presence.

## C3 — The argv-recording stub

Reasoning correct: the default stub's `echo "$@"` cannot separate `--name` from a space-bearing
value (`SDD resume: feat`). Well-built (per-subcommand file, `printf '%s\n' "$@"`, still writes
`$CMUX_LOG` so the default assertions keep working). Only divergence is the absent
`CMUX_PING_FAIL` branch — irrelevant on this path. Expressed via the existing `cmux_body=` knob;
`spawn_handoff_helpers.py` **byte-unchanged**.

## C4 — Helper refactor safety ✅

All 5 unpack sites updated (`:661, :746, :820` tuple unpack; `:865` via `_spawn_log_fields`). The
diff's deletion list shows **no assertion dropped** except `assert "/pickup b1" in
(r.stdout+r.stderr)` — replaced by two stronger ones. `_outcome_workspace` is *strengthened*:
`_spawn_log_fields` asserts exactly-one-outcome vs the old first-match. `/pickup b1` content
coverage still exists at `:128` and `:773`.

## C5 — New mutation hunt

| # | Mutation | Outcome |
|---|---|---|
| NM1 | `:389` `--focus false` → `--focus true` | RED (1/57) |
| NM2 | `:352` picker-manual branch drops the pickup arg | RED (3/55) |
| NM3 | `:437` success `outcome hop=` → `done hop=` | RED (5/53) |
| NM4 | `:445` **delete the failure-branch `cmux notify`** | **SURVIVED — 58 passed** |
| NM5 | `:396` **delete `rm -f "$out_f"`** | **SURVIVED — 58 passed** |

## Issues

**Minor — NM4 coverage gap** (`:445`): no test asserts the failure-branch notify fires.
`test_notify_failure_still_exit_0` only proves a *failing* notify doesn't break exit 0. The code is
**correct**; this is a missing assertion, not a defect. One line would close it.

**Minor / accepted — NM5** (`:396`): deleting the temp-file cleanup is unobservable to the suite;
behaviourally equivalent in-harness (leak only). Not worth a test.

No Critical. No Important. No dead code introduced. No `[NEEDS_CONTEXT]`.

## C6 — Fix-2 side effects ✅

Script diff is **comment-only** (6 lines; the FIX-5 correction, now accurate — it names
`--title "SDD handoff"` as the one remaining caller-specific string). Test diff is additions plus
the tuple refactor. **No deferred-sweep item touched.** FIX 3 confirmed: the literal
`["--name","--cwd","--command","--focus false"]` is deleted and the Task-0 frozen constants (values
unchanged since `56210f1`) are consumed at `:656/:659/:694/:702`.
`_flag_value(nw,"--command") == _successor_cmd(r)` is judged **correct coupling, not brittle** —
the workspace must launch the exact composed command, and a looser check is precisely how
MX-class bugs survive.

## C7 — Suite health ✅

`test_spawn_handoff.py` **58 passed**; `tests/unit/` **611 passed, 1 warning**; regression
**PASS 159 / FAIL 0 / WARNING 2**. All three Pyright diagnostics are benign and **pre-date fix 2**
(none appear in its diff): the `pytest` import is an env/stub resolution artifact,
`_hermetic_picker_env` is an autouse fixture (unused-by-design), and `_meta(telem=None)` is a
type-checker nit that runs green.
