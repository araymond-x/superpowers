# Task 11 Quality Review — Post-spawn setup (/rename, /rc) + knobs

Tree clean (only the two pre-existing non-code log files, untouched by reviewer); both code files byte-identical to `fb353a7`; all mutations and the scratch file restored/removed.

## Central-question answer (lead)

**The vacuity vector is `_sent_text` (last logged `send`), it appears at exactly four call sites — `test_spawn_handoff_v2.py:920, 937, 966, 1007` — and all four are inside the fixed six.** No other reach-handshake-ok test reads the last send or counts sends. The implementer's fix is complete for the actual vector, and — contra the loose "~76" framing — this was verified by measurement, not by trusting the green suite.

**Reach-handshake-ok pool: 39** (of 82 tests). Breakdown: TestPolicyDial 3, TestStallAndCeiling 10, TestCeilingDerivationIsSingle 1, TestMaxStallHopsKnob 1, TestTasksDoneFallbackAndDenominator 1, TestSurfaceTopology 16, TestHandshake 1 (`test_token_success_exits_0_handshake_ok`), TestPostSpawn 7. Minus the **6 fixed** → **33 rely on the "don't care" disjunct**, of which 7 (TestPostSpawn) intentionally exercise post-spawn, leaving ~26 incidental. The implementer's "~76" lumped 43 genuinely-never-reach tests together with the 33 that actually run post-spawn default-on — loose framing, but the conclusion holds.

**Cross-file check (the vector is not file-scoped — advisor's catch).** The default harness stub returns `exit 0` for `wait-for`, so `handshake=ok` and default-on post-spawn are reachable in the sibling suites too. Grep of `test_spawn_handoff.py` and `test_spawn_handoff_hardening.py` for last-send/count-send signatures: **zero send-log assertions in either file** (the only `send` hit in `test_spawn_handoff.py` is a comment at :1080). Several of their `cmux_v2_stub` tests do reach `handshake=ok` and run post-spawn (e.g. `test_spawn_handoff.py:755-783`), but they assert on the intent/outcome/notify/stdout channels post-spawn never writes — so they tolerate the extra `post_spawn=partial:rename` field and are not vacuous. **The vector is confined to `test_spawn_handoff_v2.py`'s four fixed sites, grep-confirmed across all three spawn suites.** e2e Step 14's assertions are all `grep -q` presence checks + intent/outcome ordering + hop count — none index or count sends, so post-spawn cannot make it vacuous (full e2e not run; see Needs Context).

### Mutations run (all scoped; restored by file-copy + `diff -q`, verified IDENTICAL each time)

| # | Candidate (pool, not in fixed-6) | Channel | Mutation | Command | Result |
|---|---|---|---|---|---|
| M1 | `TestSurfaceTopology::test_rename_tab_success_is_never_ref_parsed` | send log (first `--surface`) | launch send → `--surface "surfaceBOGUS"` (`spawn-handoff-session.sh:692`) | `pytest …::test_rename_tab_success_is_never_ref_parsed` | **RED** (`assert 'surfaceBOGUS' == 'surface:7'`) |
| M2 | `TestStallAndCeiling::test_over_expected_notifies_never_refuses` | outcome printf (the printf post-spawn extended with `$POST_SPAWN_FIELD`) | `"$BUDGET_FLAG"` → `""` (`:914`) | `pytest …::test_over_expected_notifies_never_refuses` | **RED** (`' budget=over-expected' in …`); captured record showed `handshake=ok post_spawn=partial:rename`, proving post-spawn ran and the assertion still bit |
| M3 | `TestPostSpawn::test_verify_failure_warns_partial_never_fails_spawn` | exit code | rc partial branch `return 0` → `exit 3` (`:907`) | `pytest …::test_verify_failure… …::test_knob_disables_all` | **RED** (`assert 3 == 0`); positive control `test_knob_disables_all` **PASSED** under same mutation (disabled path never reaches the branch) |

M1 is the decisive one for the central question: the launch-send assertion stayed sensitive **even though post-spawn appended a correct `surface:7` send after it** — precisely because it reads the *first* `--surface`, not the last. M3 traces the exit-code path the task asked about: a post-spawn verify failure records `partial:rc` and returns 0; the explicit `exit 0` at `:918` is untouched.

**Positive control on the fix path:** the six fixes inject `SUPERPOWERS_CMUX_POST_SPAWN=""` via `_reach_gate(..., **knobs)` → `env.update`. `test_knob_disables_all` uses the identical path (`_success_ctx` → `_reach_gate(**extra)` → `env.update`), passed to the subprocess as a real (empty) env var. Same mechanism → it is a valid positive control for the fix, confirmed by M3.

## Strengths

- **Exit-code invariant is airtight.** `run_post_spawn` always `return 0`; the wiring `[ -n "$POST_SPAWN" ] && run_post_spawn` cannot abort (no `set -e`); the success path ends in an explicit `exit 0`. Verified by reading and by M3.
- **No dead code.** `post_spawn_send_verified` takes exactly `$1/$2/$3`; no `$4`, no regex-vs-fixed branch, no unreachable `case` arm. Matches the AMENDED fence's "3 args, no branch" mandate.
- **Contract-compliant shell:** here-string `grep -qiF … <<< "$screen"` (no producer-into-`grep -q` SIGPIPE), `printf` for the composed record, `local IFS=','`, `[[ =~ ]]`, `${//}` — all bash-3.2 safe.
- **Anchors are echo-proof and MEASURED**, matching `cmux-verb-shapes.json` rationale (bare `/remote-control` occurs twice, `/remote-control is active` once). The new tests pull anchors from the fixture at runtime (`_rc_anchor()`/`_rename_anchor()` read `rc_confirmation_screen`), not hardcoded duplicates — and `_post_spawn_screen` renders the echoed line *alongside* the confirmation, so a regression to a bare anchor fails on its own fixture. `test_echo_only_screen…` genuinely exercises the echo-defeat hazard (asserts the pre-amendment anchors WOULD have matched, then that verification correctly fails → `partial:rename`).
- **Post-spawn is correctly gated to `handshake=ok`** (after the `exit 3` timeout block), so it never runs on a failed hop.

## Issues

### Important (Should Fix)

1. **Ordering canonicalization is incomplete — the "rc last" acceptance criterion is not met for regex-valid multi-token knobs.**
   - `spawn-handoff-session.sh:67` accepts `^(rename|rc)(,(rename|rc))*$`, but `:898` only rewrites the exact literal `rc,rename`.
   - **Measured** (`SUPERPOWERS_CMUX_POST_SPAWN="rename,rc,rename"`, screen verifying both anchors): sends were `/rename`, `/rc`, `/rename` — a `/rename` lands **after** `/rc`, and **no reorder warning fired**. `rc,rename,rc` behaves the same. This violates Module 3 Acceptance Criterion (module-3-spawn-script.md:846): *"ordering always resolves to `/rc` LAST."*
   - Why it matters: the criterion says "always"; the implementation guarantees it for one input. The *consequence* is small (post-spawn is cosmetic; Task 0 measured the post-`/rc` send actually working; malformed multi-token input is unusual), but the criterion is unmet as written. This faithfully implements the authoritative fence, which itself under-specifies — so it is arguably a plan gap the implementer inherited, and the controller should decide whether to accept a documented deviation rather than have it filed as trivia.
   - Fix (~1 line): after validation, if the token list contains `rc`, move it last and dedupe (e.g. drop non-final `rc`s / collapse to canonical `rename,rc` | `rc`), instead of matching one literal. Secondary: `rename,rename` / `rc,rc` send a step twice.

### Minor / Needs Context

2. **rename anchor appends `$TAB_TITLE`, reintroducing a line-wrap fragility the measured anchor was chosen to avoid — but fail-safe.** (`:906`, `:825`)
   - The fixture `rename_anchor` is `"Session renamed to:"`, chosen because it "matches exactly 1 line." The code greps `"Session renamed to: $TAB_TITLE"`. A long title that wraps in the terminal splits the rendered `Session renamed to: <title>` across lines, so the single-line `grep -F` misses → a spurious `post_spawn=partial:rename` on a *successful* rename.
   - **Fail-safe:** this can only produce a false *partial WARNING* (exit stays 0), never a false verify-*success*. The default title (`hop1 SDD feat`) is short and does not wrap. It matches the authoritative AMENDED fence byte-for-byte, so this is a plan observation, not an implementation defect. Not merge-blocking. (If tightened, revert to the bare measured anchor and accept the negligible "title == the anchor phrase" edge.)

3. **Out of scope — surface for module finish, not a Task 11 defect:** e2e Step 14 (`sdd-e2e-test.sh:646-695`) uses the pre-rework stub (`echo … ; exit 0`, no `OK surface:` line) and greps for `new-workspace`, which the Module 3 rework replaced with `workspace create` and which `test_spawn_handoff_v2.py:1350` asserts is gone. Step 14 may be stale against the reworked script. It is the plan's declared `integration_test`, so it should be run at module/feature finish. Full e2e NOT run (out of Task 11's two-file scope, and unaffected by post-spawn as shown above). [CONTROLLER NOTE: the e2e is RED by design until Task 17, which owns its rewrite — a known, already-accounted-for item, not a Task 11 regression.]

## Recommendations

- Close finding #1 with a canonicalization that enforces "rc last" for *any* accepted token list (not one literal), or record an explicit deviation that the guarantee is scoped to `rc,rename`.
- When #1 is fixed, add one test driving `rename,rc,rename` (or `rc,rename,rc`) asserting `/rc` is the last `send` — the scratch run above shows the current gap and would pin the fix.
- Consider running the full e2e at module finish to resolve #3.

## Assessment

**Ready to merge?** **With fixes.**

**Reasoning:** The central risk — silent vacuity from default-on post-spawn — is genuinely resolved: the last-send vector is grep-confined to the four fixed `_sent_text` sites across all three spawn suites, and mutation tests confirm the non-fixed reach-ok tests still bite on the send-log and outcome-printf channels post-spawn touches. The exit-code and echo-proof-anchor contracts are sound and test-verified. The one substantive gap is the ordering canonicalization (finding #1), which leaves the "rc last" acceptance criterion unmet for regex-valid multi-token knobs (empirically demonstrated); it is a cheap fix with cosmetic real-world impact, so it warrants a fix or a recorded deviation rather than blocking. `git status` is clean — only the two pre-existing non-code log files remain modified; both code files are byte-identical to `fb353a7`.
