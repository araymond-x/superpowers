# Partner Review — Task 8 dispatch (round 2)

**Status:** BLOCKED

**F1 (B1 / hardening file):** **OPEN** — landed at four of five sites, but the executable half was not updated, and the closure claim it rests on is false.

Landed and verified first-hand: module-3 Write-Scope Task 8 and Task 9 rows (`module-3-spawn-script.md:51-52`); `plan.md`'s Module-3 row; Task 8's Files block (`:62`) plus the B1 paragraph (`:64`); the dispatch's write scope (`:29`); the dispatch's Acceptance section (`:99-105`, full suite). `test_spawn_handoff_hardening.py` is **10/10 green** today (ran it). The pin is actionable — "seed above the new derived ceiling" works; the alternative "set `SUPERPOWERS_CMUX_MAX_HOPS` explicitly" is incoherent for *that specific test* (an invalid knob value is the test's whole subject), but the hedge "whichever preserves each test's stated intent" covers it.

Two things are open:

**(a) Plan Steps 5 and 6 still describe the pre-amendment scope.** Step 5 (`:271`) runs `pytest tests/unit/test_spawn_handoff.py tests/unit/test_spawn_handoff_v2.py -v` — omitting `test_handoff_support.py` (which seven P7 rows edit) and `test_spawn_handoff_hardening.py` (B1's whole point). Step 6 (`:273`) says "`git add` the four files + fixtures" against an **eight-path** write scope. Under the standing never-`git add -A` rule, an implementer following Step 6 literally leaves `_handoff_support.py`, `test_handoff_support.py`, and `test_spawn_handoff_hardening.py` unstaged. The B1 paragraph declares "the acceptance run for this task is the FULL suite, not a file list" 200 lines above two checkboxes that still say otherwise — and the checkboxes are what the implementer ticks and what the spec reviewer mechanically diffs. The dispatch's Acceptance section rescues the *reported number* but not Step 6's staging list.

**(b) RETRACTION — my round-1 claim was wrong, and the plan now carries it verbatim.** I asserted the consumer sweep closes at exactly two test files. The plan adopted it at `:64` and the dispatch at `:55`. It is false in two directions:

- `tests/integration/sdd-e2e-test.sh:722` is a third `.handoff-hops` consumer. **Benign for Task 8** — `SPAWN_WT` ships no `.sdd-session.json`, so the derived ceiling is 6 and hops 0 passes; Module 4 already owns e2e Step 14. Worth naming, not fixing here.
- **Two more tests in `tests/unit` break, and neither is named anywhere.** Both were missed because every sweep — mine, and the controller's re-verification — grepped the *identifiers* (`MAX_HOPS`, `.handoff-hops`) and never the *rendered form*:
  - `test_spawn_handoff.py:664 test_new_workspace_and_notify_argv_values_match_spec`, assertion at `:692`: `assert _flag_value(notify, "--body").startswith("Hop 1/3 ")`. The script renders that at `spawn-handoff-session.sh:530` as `Hop $SP_HOP/$MAX_HOPS`. That fixture has no manifest → new ceiling 6 → `"Hop 1/6 "` → **FAILS**. A `MAX_HOPS` consumer containing neither token.
  - `test_spawn_handoff.py:695 test_spawn_log_record_fields_match_spec_log_format`, assertion at `:702`: `assert _spawn_log_fields(ctx, "intent") == {"hop": "1"}` — exact equality on the whole field set. Step (f) adds `tasks_done=` → **FAILS**. Step (f) has no migration note at all, though Step 2 writes one for `test_hop_limit_exits_3`.

Both are in `test_spawn_handoff.py` (in scope, in Step 5's run) and fail loudly, so far less dangerous than B1. But the dispatch tells the implementer "verify that closure yourself with `/usr/bin/grep`" — and grepping `MAX_HOPS` *confirms the false claim*. The self-verification instruction names the exact instrument that misses. This sprint's signature failure recurring inside the fix for it.

**F2 (P7-2):** **CLOSED** — dispatch `:57` carries P7-2, states `test_handoff_support.py` is Task 8's only window, and requires "make it cover the new degraded return you introduce for P7-8". Gap confirmed real: `_handoff_support.py:145-147` registers `stall-streak`; `TestCli` never invokes it.

**F3 (P7-8 vacuousness):** **CLOSED** — dispatch `:64-68` forbids the blanket handler, requires the split (`FileNotFoundError` → `0`, other `OSError` → `indeterminate`), and requires the paired missing-log-returns-`0` positive control. Verified against live code: `_handoff_support.py:117-120` is `except OSError: return 0` with docstring "no log yet: first hop". The instruction **does** discriminate — a blanket `return "indeterminate"` makes the missing-log case return `indeterminate`, which the required positive control then fails. The severity note at `:68` is correct: both values proceed, so the cost is a disabled guard, not consent.

**F4 (third consent path + conjunction test):** **OPEN** — contract stated, split real, but the third stub prescribes a seam that does not exist.

Stated: the fenced comment at `:192-195` and dispatch `:62` both say the absent-FILE case deliberately stays `auto` and the layers disagree on purpose. Verified empirically: `spawn-policy --manifest /nope/nope.json` → `ask` (fails closed); `spawn-policy` on `{"handoff":{"spawn_policy":"OFF"}}` → **`auto`** (P7-1(ii)'s live fail-open, confirmed).

The split is real — the three stubs name three genuinely distinct paths (shell `[ -f ]` short-circuit / CLI `auto` return / `*)` arm); no two collapse.

But `test_cli_failure_is_non_consent` says "**SUPPORT_CLI pointed at a nonexistent path**". No such seam exists: `SUPPORT_CLI="$SCRIPT_DIR/_handoff_support.py"` and `SCRIPT_DIR` derives from the real script location (`spawn-handoff-session.sh:15`), not overridable. This matters more than a wrong comment: **this is the only test pinning the `*) → ask` arm.** Its two siblings both pass if the gate always allows, so if the implementer weakens or drops it, P7-1(i)'s fail-closed fix ships with zero discriminating coverage.

A workable seam exists but is not the obvious one: `SUPERPOWERS_ROOT` is honored at `:16` and `env_extra` is applied last in `run_spawn` (`spawn_handoff_helpers.py:152-153`), so overriding it makes `$PYTHON` fall back to bare `python3`, which resolves to the stubs dir first on `PATH`. **A blanket `python3` stub will not work** — `validate_bundle` makes four `$PYTHON` calls (`:140-147`) and runs at `:160`, before the policy gate, so the test would die at bundle validation and never reach the arm under test. The stub must dispatch on argv: fail only for the `spawn-policy` invocation, `exec` the real interpreter otherwise.

**F5 (Shared Constants / Pattern References / SSOT):** **CLOSED** — both sections present (dispatch `:33-39`, `:41-47`). Values verified against `_handoff_support.py:15-17`: `HOP_DIVISOR = 2.5`, `CEILING_FLOOR = 6`, `CEILING_FACTOR = 2`. The SSOT comment at the shell site (`:229-231`) is truthful: `_handoff_support.py:69` computes `max(CEILING_FLOOR, CEILING_FACTOR * exp)`, mirroring the shell's `max(6, 2 × expected)`. The sanctioned-exception framing is right.

**Over-200 exception:** **SOUND** — measured, not accepted. `validate-plan.py:200-206` sets `status = "TOO_LARGE"` then `warnings.append(...)`; never touches `blockers`. Running it on the amended module-3 returns `"status": "WARNING"`, `blockers: []`, the single warning being the 217-line notice. `plan-validation-gate-hook.sh:172` gates on `if [ "$STATUS" = "FAIL" ]`. The constraint is advisory in the enforcing code, exactly as the deviations row claims. The split-rejection rationale is sound on its own terms. Keep the 217 lines.

**New defects introduced by the amendments:**

1. **Dispatch `:141` is stale and contradicts `:60`.** It says "(P7-1(i) is a deliberate authorized deviation from the plan's fenced `*)` arm — record it here.)" But `:60` says P7-1(i) is **already applied to the plan** and "no longer a deviation to make". Following `:141` writes a false row into `deviations.md` — the one artifact that survives `transition-module.py`'s archival, and the artifact this sprint just learned to treat as the durable record. Delete the parenthetical.
2. **The `test_cli_failure_is_non_consent` seam** (F4) — a fenced stub prescribing a mechanism that does not exist, guarding the only passing-direction proof of the consent fix.
3. **Nit, non-blocking:** the fenced comment at `:193` says "The CLI fails closed to `ask` on a missing `--manifest`". Omitting the *flag* is argparse exit 2 (confirmed); it is a nonexistent *manifest path* that returns `ask`. No code depends on the distinction, but the fence is read as contract.

**Vacuousness sweep:** **PASS**, with one noted weakness. `test_ask_with_flag_proceeds` and `test_absent_manifest_file_is_auto` both assert only that nothing refused — each would pass if the gate were deleted entirely. Neither is vacuous *as a pair member*: `test_ask_without_flag_refuses_retryable` and `test_cli_failure_is_non_consent` pin the refusal direction, and the plan's inline comment ("gate passed — later gates may still act") shows the weakness was seen deliberately. This is only a problem if the F4 seam defect causes `test_cli_failure_is_non_consent` to be dropped, at which point the whole `TestPolicyDial` class becomes non-discriminating in the consent direction.

**Still missing:** Plan Step 5's command and Step 6's staging list (F1a); a migration note for step (f)'s intent-record grammar change; a migration note for the `"Hop 1/3 "` pin; correction of the "closed at exactly two test files" claim at `module-3-spawn-script.md:64` and dispatch `:55`.

---

## Findings

1. **Plan Steps 5 and 6 describe the pre-amendment scope** — Step 5 runs two of four relevant test files; Step 6 stages "the four files" against an eight-path scope. Fix: Step 5 becomes the full-suite run (matching the dispatch); Step 6's list becomes the explicit eight paths.
2. **The B1 closure claim is false; two unnamed tests break** — `test_new_workspace_and_notify_argv_values_match_spec` (`"Hop 1/3 "` → `"Hop 1/6 "`) and `test_spawn_log_record_fields_match_spec_log_format` (exact-equality intent fields). Fix: name both in Step 2's migration note; replace the "closed at exactly two test files" sentence with the measured list, and state that the sweep must cover the **rendered** strings (`Hop N/M`, intent field sets), not just the `MAX_HOPS`/`.handoff-hops` identifiers — otherwise the dispatch's "verify the closure yourself with `/usr/bin/grep`" confirms the error. Note `tests/integration/sdd-e2e-test.sh:722` as a benign third consumer owned by Module 4.
3. **Dispatch `:141` induces a false deviation row** — delete the parenthetical; it contradicts `:60`.
4. **`test_cli_failure_is_non_consent` has no seam as written** — replace "SUPPORT_CLI pointed at a nonexistent path" with: override `SUPERPOWERS_ROOT` so `$PYTHON` falls back to bare `python3`, and stub a `python3` on `PATH` that **dispatches on argv** — failing only the `spawn-policy` call and `exec`-ing the real interpreter otherwise, because `validate_bundle` makes four `$PYTHON` calls before the gate is reached. Flag in the dispatch that this is the sole discriminating test for the `*) → ask` arm.

---

## Premises verified first-hand vs. accepted

First-hand: both commit diffs in full; Task 8 in full (`:58-273`); `plan.md`'s Module-3 row; both new `deviations.md` rows; the dispatch in full. Ran `validate-plan.py` on module-3 (`WARNING`, `blockers: []`, 217 lines) and read `validate-plan.py:200-206` and `plan-validation-gate-hook.sh:172`. Ran the hardening suite (10 passed). Executed `_handoff_support.py` for `spawn-policy` on a nonexistent path (`ask`), flag-omitted (argparse exit 2), `"OFF"` (`auto`), and `stall-streak --tasks-done unknown` (argparse reject, confirming P7-4's premise and that step (e)'s `unknown` branch covers it). Read `stall_streak` (`:114-133`), the CLI registrations (`:141-148`), the constants (`:15-17`), `run_spawn`, `_reach_hop_gate`, `_spawn_log_fields`, and the script's `SCRIPT_DIR`/`PYTHON`/`validate_bundle`/`Hop $SP_HOP/$MAX_HOPS` sites. All recursive sweeps used `/usr/bin/grep` or `find -print0 | xargs -0`, each with a positive control.

Accepted without independent check: that the eleven-row count is the right enumeration — confirmed B1 + P7-1…P7-9 + OP-1 = 11 exist and are gated on Task 8/Module 3.

**Corrections to round 1, stated plainly:** my claim that the consumer sweep "closes at exactly two test files" was **wrong**, and the controller propagated it verbatim into `module-3-spawn-script.md:64` and the dispatch. There are at least four other consumers — two breaking tests in `tests/unit/test_spawn_handoff.py` and one benign reference in `tests/integration/sdd-e2e-test.sh`. My sweep grepped identifiers and never the rendered output strings, which is the same undercount the B1 row itself was filed to correct. That correction belongs in the plan text, not only in this report. Separately, on **F4 I was right that the conjunction test needed splitting, but the split the controller wrote inherits a seam that does not exist** — a defect neither of us would have caught without reading `SCRIPT_DIR`'s derivation.

---

## Controller disposition (round 2)

All four findings ACCEPTED. Finding 2 independently re-verified by the controller, and the verification produced a **stronger** result than the reviewer's:

`/usr/bin/grep -rlc 'MAX_HOPS' tests/unit/*.py` matches **only `test_spawn_handoff_hardening.py`** — `test_spawn_handoff.py` scores **0**, despite pinning `"Hop 1/3 "` at `:692` (rendered from `$MAX_HOPS` at `spawn-handoff-session.sh:530`) and exact-equality intent fields at `:702`. Both cited line numbers confirmed present, as is the benign `sdd-e2e-test.sh:722`.

**So the identifier sweep does not merely miss consumers — it returns a clean, plausible, FALSE closure.** This is the eleventh instrument failure of the sprint, and the first where the flawed sweep was written into the fix for a missed-consumer row. Recorded as a standing rule: **a dependency on a value is not the same as a textual reference to its name; sweep the RENDERED form as well as the identifier.**
