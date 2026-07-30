# Plan Review Report — cmux-spawn-v2

Reviewer: plan-document-reviewer (general-purpose dispatch, template
`skills/writing-plans/plan-document-reviewer-prompt.md`), 2026-07-30.
Scope: plan.md + module-1-contracts-spikes.md + module-2-models-budget.md +
module-3-spawn-script.md + module-4-card-hooks-docs.md, reviewed as a unit
against spec-distilled.md and 12 source-contract files read independently.

Round 1: **Issues Found** (5 blocking, 7 advisory) → all fixed same session.
Round 2 (same reviewer agent, fix-site re-verification): **Approved** (3 residual
advisories, all applied to the plan after approval — Module 3 Contract
Constraints fail-closed wording; `test_mktemp_failure_still_spawns_uncaptured`
added to the premise-rewrite bucket; Module 2 helpers header attribution).

---

## Round 2 (final): Plan Review

**Status:** Approved

All 5 blocking issues are correctly resolved, all 7 advisories are addressed, and the hoisted sections are complete with no dangling references or duplicated definitions. Cross-document consistency holds. Three residual advisories below (one is a small leftover from the wording advisory, one is a premise-rewrite candidate the B4 fix pattern should also cover) — none blocks implementation.

**Fix-site verification:**

- **B1 (validate-report CLI):** FIXED — Module 4 Task 12 `test_report_skeleton_passes_validate_report` now invokes `[VENV_PY, ..., "--report-file", str(skel)]`, matching the real argparse (`--report-file`, required). The skeleton itself remains model-valid and section-complete.
- **B2 (card checkpoint invocations):** FIXED — both composed commands now carry `--deviations-file {deviations_abs} --reports-dir {reports}/`; `deviations_abs` is defined before use with a manifest-derived default; the golden test asserts both flags (with the N35 comment); the trailing note now targets `run_pre_dispatch`/`run_pre_completion`'s hard requirements and demands running the composed commands verbatim against the fixture — the correct proof, since argparse alone cannot surface the requirement. Confirmed against the fixture shape: manifest mode resolves `plan_file` via `_load_manifest_config`, and a missing deviations *file* is tolerated once the *flag* is present, so the verbatim run will produce a checkpoint result.
- **B3 (fallback surface awk):** FIXED — `awk 'NR==1{first=$1} /\[selected\]/{print $1; f=1; exit} END{if(!f) print first}'` emits exactly one line in every case. Verified the awk semantics trap is handled: `exit` still runs the `END` block, and the `f` flag correctly suppresses the double print. Comment documents the two-line trap and the newline-passes-glob hazard.
- **B4 (migration list):** FIXED — count corrected to 3 `test_workspace_ref_*` tests; the four missing full-spawn tests are named with the correct reason (no `OK surface:` stdout vs. the new ref-shape checks); the `(spawned)`-degrade premise rewrite is explicit for `test_workspace_ref_falls_back_when_cmux_emits_nothing` and `test_spawn_log_record_fields_match_spec_log_format`. I re-swept the entire test file this round: every remaining unlisted test is either `--dry-run` (exits before the spawn sequence) or an exits-3-before-spawn path — the list is now complete, with one premise nuance noted in the advisories.
- **B5 (byte-proxy invariant):** FIXED — `test_byte_proxy_interference_invariant` added to Task 12's test file; the docstring correctly instructs mirroring the ACTUAL hook patterns (grep `ctx_byte_estimate` + stale-scan prefixes) rather than trusting the illustrative fnmatch list, and the illustrative patterns match `detect_stale_artifacts`' real globs (`task-*`, `pre-execution-audit*`).

**Hoisted sections (structural check):**

- Module 2 "Shared test helpers": single definition site; `VENV_PY`/`SUPPORT` reference `Path`/`SCRIPTS` from Task 6 Step 1's file header (same file) — no dangles; Task 7 Step 1 references it explicitly. `_write_report`/`_log` appear nowhere else.
- Module 4 "Test harness": complete (imports, `ROOT`/`SCRIPTS`/`CARD`/`VENV_PY`, `_fixture_feature`, env-stripping `_run_card`, `_materialize_minimal_plan`); Task 12 Step 1 references it; no duplicates. The local `import os` in `_run_card` covers the one symbol the hoisted import block lacks.
- Module 4 "Generator helpers": `_read`/`_last_line`/`_skeleton` hoisted once; the generator body carries an explicit placement marker comment; `_skeleton`'s dependencies (`ImplementerReport`, `REQUIRED_SECTIONS`, `yaml`) are all in the generator's import block, `_read`'s `Path` likewise. Nothing from the round-1 inline versions was lost (byte-identical logic).
- Task sizes post-hoist all land under the 200-line limit (Tasks 8, 9, 12 are the largest at roughly 191–195 lines).

**Advisory-fix verification:** `post_spawn_send_verified` gained the `fixed|regex` fourth parameter with matching call sites (`-F` for the title, `-E` for the rc phrase, both here-strings) — contradiction resolved. `_frontmatter` now imports `yaml` with ImportError propagating (and the `except OSError` in the counting loop cannot swallow it; zero-reports still legitimately returns 0 without touching yaml), and the `tasks-done` CLI prints `unknown` on ImportError — the fake-0 stall-manufacture path is closed. `_run_card` strips ambient `SUPERPOWERS_CMUX_*`; Module 3 Task 8 carries the ambient-knob note. Parent item 3 wording corrected; the `reason=policy` spec discrepancy is recorded as an accepted deviation; Task 0's version-not-on-disk branch now `exit 1`s and the measurement block carries the "measurement shell only" annotation; `_commit`/`_spawn_log_text_or_empty` are defined in Task 8's helper block (and `subprocess` is already imported by `spawn_handoff_helpers.py`).

**Snippet Verification (re-run):**

- Snippet 1 [Module 3 Task 8, precondition bash]: VERIFIED — unchanged from round 1's verified state; helper additions consistent with `spawn_handoff_helpers.py`.
- Snippet 2 [Module 3 Task 9, spawn-core functions]: VERIFIED — awk fix correct (including the exit-runs-END guard); per-verb parsing, temp-file rc preservation, one-shot fallback guard, and literal `\n` send all match the contracts.
- Snippet 3 [Module 2 Task 7, `count_tasks_done`/`stall_streak`/CLI]: VERIFIED — statuses match `implementer_report.Status`; ImportError degradation observable; CLI arg names round-trip.
- Snippet 4 [Module 4 Task 12, generator + tests]: VERIFIED — invocations now satisfy the phase handlers' hard requirements; `--report-file` correct; `deviations_abs` defined; hoisted helpers wired with no dangles.
- Snippet 5 [Module 4 Task 14, hooks trio]: VERIFIED — unchanged; stop-hook vars, `set -euo pipefail` survival, Check 3b regex quote all match current sources.
- Snippet 6 [Module 4 Task 15, Check 9]: VERIFIED — unchanged; signature and insertion point match current code.

**Cross-Document Audit (re-run):**

- Field 1 (outcome-record field set): spec -> parent Shared Contract item 2 -> Task 9/10 printfs — MATCH.
- Field 2 (`expected_hops` formula + precedence + ceiling): spec -> parent -> `_handoff_support.py` -> materialize wiring -> script derivation — MATCH (2.5/6/2; manifest-total → module-union → inclusive `task_range`; env wins absolutely).
- Field 3 (`handoff_spawn`/`spawn_policy` literals): `plan.py` -> `sdd_session.py` `SpawnPolicy` -> manifest block -> CLI whitelist -> script `case` — MATCH (`"auto"|"ask"|"off"`, default `auto`).

**Recommendations (advisory, do not block approval; ALL THREE applied post-approval):**

- Module 3 Contract Constraints (the `**Contract Constraints:**` line) still says "`.handoff-hops` + `SUPERPOWERS_CMUX_MAX_HOPS`'s **fail-closed** numeric guards, which are **untouched**" — this is the one site the A4 wording fix missed, and it is now doubly inconsistent: the parent correctly says fail-closed belongs ONLY to `.handoff-hops`, and Task 8(b)/(e) explicitly deletes and rewrites the MAX_HOPS validation (so "untouched" is wrong too). Reword to match the parent (`.handoff-hops` fail-closed guard untouched; MAX_HOPS stays validate-warn-revert but moves to the ceiling derivation). *(Applied.)*
- `test_mktemp_failure_still_spawns_uncaptured` sits in Task 9's generic migration group, but its original invariant (mktemp unavailable → spawn proceeds uncaptured) is impossible under the v2 design: `create_surface_target`/`create_workspace_target` both `return 1` on mktemp failure because the ref is now load-bearing (rename/send need it). Add it to the premise-rewrite bucket alongside the `(spawned)` tests — new contract: mktemp failure → fallback attempt → spawn-failed exit 3, hop consumed (its rc-3 sibling `test_mktemp_failure_preserves_spawn_failure_rc` survives naturally). *(Applied.)*
- Module 2's "Shared test helpers" header says "used by Tasks 6-7", but only Task 7's tests consume them; add three words ("added when Task 6 creates the file") so the Task 6 implementer knows the block is theirs to include rather than Task 7's. *(Applied.)*

**Spec-lock spot checks (round 1, all held; unchanged by fixes):** the received `wait-for` token is the only exit-0 path in every snippet (Task 9's success stanza gates on `cmux wait-for` rc; Task 10's `diagnose_target` is called only after two timeouts and its result reaches only the record/messages, never the exit code; `test_token_is_only_success` pins it); reservation precedes spawn; policy checks sit before reservation (Precondition 2b, nothing written); fallback fires only pre-accepted-send with the `SPAWN_TOPOLOGY` one-shot guard; `spawn_claude_workspace()` deletion is explicit in Task 9.

---

## Round 1 (historical): Plan Review

**Status:** Issues Found

All five plan documents, the distilled spec, and every listed source contract were read (`spawn-handoff-session.sh`, `plan.py`, `sdd_session.py`, `implementer_report.py`, `_report_utils.py`, `materialize-manifest.py`, `sdd-pre-dispatch-hook.sh`, `controller-checkpoint.py`, `sdd-stop-hook.sh`, `hooks/session-start`, `spawn_handoff_helpers.py`, `test_spawn_handoff.py`, e2e Step 14, plus `validate-report.py` because Task 12's test depends on its CLI). The plan is strong overall — the spec-lock items hold — but four contract/snippet defects and one spec-coverage gap must be fixed before dispatch.

**Blocking Issues (all fixed before round 2):**

- [CONTRACT ACCURACY]: Module 4, Task 12, Step 1 (`test_report_skeleton_passes_validate_report`): the test invokes `validate-report.py` with a **positional** path. The real CLI takes **`--report-file PATH` (required)** and has no positional argument; the call as written exits 2 with an argparse error, so the test can never pass and an implementer will either stall or "fix" it by weakening the assertion. Change to `[..., "--report-file", str(skel)]`.
- [CONTRACT ACCURACY]: Module 4, Task 12, Step 3 (card template "Checkpoint invocations (copy verbatim)"): both composed commands **exit 3 against the real script**. `run_pre_dispatch` and `run_pre_completion` hard-require `--deviations-file` and `--reports-dir` even in manifest mode. The hook's own N35-corrected Check-5c remediation string is the correct shape. This blocks doubly: (a) the plan's safety caveat says "read controller-checkpoint.py's argparse block first" — but argparse declares both flags `required=False`, so following the caveat as written still ships a broken card; (b) the golden test only asserts substrings, so it cannot catch the omission. Fix the template to include both flags (manifest-derived paths) and add them to the golden-test assertions.
- [SNIPPET SAFETY]: Module 3, Task 9, Step 3(c) `create_workspace_target`: `awk '/\[selected\]/{print $1; exit} NR==1{print $1}'` prints **two lines** whenever the `[selected]` surface is not the first listed line. The resulting multi-line `SPAWN_SURFACE_REF` still passes the `case … surface:*)` glob (glob `*` matches the embedded newline), then feeds garbage into `rename-tab`/`send`/`read-screen`. The single-line `list-pane-surfaces` stub can never expose this. Fix with a single-line-guaranteed awk.
- [LEGACY REMOVAL]: Module 3, Task 9, Step 2 migration list incomplete against the actual `tests/unit/test_spawn_handoff.py`: (a) `test_workspace_ref_*` is 3 tests, not 4; (b) four full-spawn tests missing entirely (`test_picker_manual_spawn_uses_interactive_command`, `test_append_prompt_file_written_on_real_spawn`, `test_fallback_tail_spawn_id_correlates_with_intent_record`, `test_notify_failure_still_exit_0`) — their stubs emit no `OK surface:N` stdout and the new ref-shape checks turn that into spawn-failed; (c) the `"(spawned)"` empty-capture degrade tests need their **premise** rewritten, not just their verb.
- [SPEC ALIGNMENT]: Spec Testing Requirements enumerate a "**byte-proxy interference invariant**" unit test; no module's test list contained it. Add it.

**Round-1 snippet verification:** Snippet 1 (Task 8 bash) VERIFIED; Snippet 2 (Task 9 spawn core) MISMATCH (awk bug); Snippet 3 (Task 7 counting) VERIFIED; Snippet 4 (Task 12 generator) MISMATCH ×2 (flags, CLI shape); Snippet 5 (Task 14 hooks) VERIFIED (Check 3b regex quoted exactly; session-start `set -euo pipefail` claim true; stop-hook systemMessage claim true); Snippet 6 (Task 15 Check 9) VERIFIED (signature + insertion point match).

**Round-1 cross-document audit:** outcome-record field set MATCH; expected_hops formula/precedence/ceiling MATCH; handoff_spawn/spawn_policy literals MATCH.

**Round-1 advisories (all addressed):** post_spawn grep -F/-E contradiction; count_tasks_done ImportError vs fake-0; ambient `SUPERPOWERS_CMUX_*` env in tests; parent "fail-closed" wording for MAX_HOPS; `reason=policy` vs `reason=policy-off` spec-internal discrepancy (plan follows Contract Facts — record as accepted deviation); Task 0 ABORT branch didn't abort + pipe-rule annotation; Task 8 test-helper names (`_spawn_log_text_or_empty`, `_commit`) undefined.
