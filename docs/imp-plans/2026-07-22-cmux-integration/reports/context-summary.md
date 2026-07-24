# Context Summary — cmux-integration repo-3 SDD (Module 1 COMPLETE, Module 2 active)

> Regenerated at the Module 1→2 transition boundary. Rich resume guidance is in the handoff
> bundle's CONTINUE.md; this file is the flight-recorder digest.

## Status: **Module 1 COMPLETE and transitioned.** Module 2 active (tasks 7–9). Resume at **Task 7**.

| Task | State | Commit | Notes |
|------|-------|--------|-------|
| 0–5 | ✅ done (reviewed) | thru `eae39dc` | Contract fixtures, script foundation, bundle validation, quota, decode/label/telemetry, launch composition. |
| 6 | ✅ **done (reviewed, 3 commits)** | `5c6e4d9` + `3491171` + `ec0df92` | Spawn sequence, reservation ordering, exit codes, `--dry-run`. Spec review FAIL→fix→**re-review PASS**; quality review PASS-with-fixes→fix→**re-review PASS**. |
| 7–9 | ⬜ **NEXT** | — | Module 2: protocol rewrite, e2e Step 14, docs. See `module-2-protocol-e2e-docs.md`. |

Suites at the boundary: `test_spawn_handoff.py` **58 passed**; `tests/unit/` **611 passed**;
regression **PASS 159 / FAIL 0 / WARNING 2**; lint-shell clean for this script.
Module 1 checkboxes **38/38**. **0 pending deviations.** Working tree clean.
Manifest: `active_module_id: 2`, `active_module_file: module-2-protocol-e2e-docs.md`,
`context_summary_at` recomputed to **8**. 25 Module-1 reports archived to
`reports/archive-spawn-handoff-session.sh + unit suite/`.

## ⚠ READ FIRST — what Task 6 proved, and what it costs you if you forget

1. **MUTATION-TEST EVERY ASSERTION. This is the run's single highest-value practice.**
   Task 6 shipped **seven** assertions across three rounds that looked like coverage and caught
   nothing. Reviews found them only by *breaking the behavior and watching the suite stay green*:
   - the quality review found **5 surviving mutations on a fully green 56-test suite** (MX1–MX5);
   - the re-review found **2 more** (NM4, NM5) after those were closed.
   Require every implementer to prove each new test goes RED when its behavior is broken, and
   verify at least one mutation yourself.

2. **The test-echo collision is a RECURRING class in this script, not a one-off.**
   `spawn-handoff-session.sh` is chatty on stderr. MX2 showed
   `assert "/pickup b1" in (r.stdout + r.stderr)` is already satisfied by the Task-5
   `successor command:` echo at `:355`, so it never observed `print_manual_instructions` — on the
   one path where a hop is already consumed and manual recovery is mandatory. It was flagged as a
   CRITICAL carry-forward for Task 5 and **recurred anyway in Task 6.**
   ➡ **Treat ANY assertion against combined `stdout+stderr` as contaminated until proven
   otherwise.** Anchor on a distinctive line, then mutate to prove it discriminates.

3. **A declined cheap experiment is not evidence.** Task 6's implementer decided
   `cmux new-workspace` returns no workspace ref, reasoning from the absence of a `--json` flag,
   and explicitly declined to create-and-close a throwaway workspace because "it would not change
   the outcome." The spec reviewer ran exactly that probe: `OK workspace:6` on stdout. The
   supporting claim was also false in both directions (none of the three subcommands has `--json`).
   That was the round's one BLOCKING finding. ➡ When a one-command experiment would settle a
   factual premise, require it.

4. **`cmux new-workspace` / `close-workspace` are deprecated aliases** for
   `cmux workspace create` / `close` (legacy form supported indefinitely; `CMUX_QUIET=1` silences
   the notice). The script uses the legacy spelling, matching spec and plan text. BACKLOG candidate.

## Contract facts frozen (Task 0 + verified live through Task 6)
- `--command <text>` = cmux "send text+Enter after creation" → shell-typed (zsh); composed
  successor cmd must be POSIX/zsh-safe.
- Picker exports 4 vars every launch path: VERSION/LABEL/ARGS/APPEND_PROMPT. append-file exit-3 is
  `--non-interactive`-only. `versions/<v>` = executable regular file.
- Repo identity = `realpath(git rev-parse --git-common-dir)`, NOT `--show-toplevel`.
- **Bash floor: construct floor 3.1 (`FORWARDED+=`), verified floor 3.2.57.** Task 9 documents ≥ 3.2.
- Composed flag order (spec.md:157, verified exact):
  `claude-picker --non-interactive --pick-version <v> --telemetry <on|off> [--session-label <l>] <forwarded args> "/pickup <id>"`.
- **`cmux new-workspace` prints `OK <ref>` on stdout** (e.g. `OK workspace:6`), LF-terminated,
  rc 0 — verified live three times. Parsed with `awk '/^OK[ \t]/{print $2; exit}'`.
  Do NOT parse with `while read`: it drops a final line lacking a trailing newline, which would
  silently degrade every real spawn to `(spawned)` while echo-based test stubs stayed green.

## Plan-defect ledger (the plan is NOT fully trustworthy as written)
Four confirmed defects, all empirically proven, all still present in `module-1-spawn-script.md`:
- **Task 3 Step 2 timeout snippet** — command-substitution + background watcher stalls the FULL
  timeout on the SUCCESS path. Shipped code uses `mktemp` + `wait`.
- **Task 3 Step 2 tool resolution** — the plan's line makes its own Step 1 tests impossible to pass.
- **Task 4 "Bash version caveat"** — says ≥ 4.x; actual floor is 3.2.
- **Task 6 Step 2 ordering defect (NEW)** — generated `SPAWN_ID` *after* the compose block, so the
  composed fallback tail baked in the literal word `spawn` where §5.4d requires the uuid. Shipped
  code generates it once *before* composition and threads it through all four records.
  (Task 5's fence was correct as written — the ledger is defects, not a per-task tally.)

➡ **Treat plan code fences as drafts to verify, not gospel.** Have implementers prove the fence
works by EXECUTING it before adopting it.

## Process gotchas for the resuming controller (NOT re-derivable from deviations.md)
1. **Report field rule**: `tests.written`/`tests.passing` are **per-task/per-round** counts, and
   `passing` ≤ `written`. Bake into every implementer prompt. Also: one subagent returned
   `tests.written` as a **list of test names** — the strict Pydantic model requires an **int**, so
   normalize before saving or `validate-report.py` fails and blocks the next dispatch.
2. **Check any `-k` filter with `--collect-only -q`** before letting an implementer derive counts —
   the plan's filters have been substring-contaminated before.
3. **Environment `.py` file-watcher** cosmetically line-wraps test files post-write — benign.
4. **The ambient env is picker-populated.** The autouse `_hermetic_picker_env` fixture is
   **load-bearing** — do not remove or narrow it.
5. **Tick plan checkboxes before running the next checkpoint.** A missed tick FAILed Task 4's.
6. **Advisor tool ↔ background subagents:** never call advisor while any subagent is live — an
   earlier session died to an unrecoverable API 400 (orphaned `advisor_tool_result`).
7. **Do NOT add `set -u`** to `spawn-handoff-session.sh` (`${FORWARDED[*]}` on an empty array
   raises `unbound variable` on bash 3.2 while passing on 4.4+).
8. **Disposition deviations before dispatching.** The pre-dispatch hook hard-blocks on any
   `| Pending |` row.
9. **Reviewer dispatches died twice to transient API server errors** mid-response (~110–130k
   subagent tokens each, no usable output). Recovery that worked: `SendMessage` to resume the dead
   agent from its transcript **with a hard output budget** (~800–1200 words) — a blind retry is
   likely to fail the same way. Give every reviewer an explicit output budget up front.
10. **`tests/unit/spawn_handoff_helpers.py` is READ-ONLY for Tasks 1–6** per the Write-Scope table
    — which CONTRADICTS an older carry-forward note saying Task 6 "MAY modify" it. The plan won.
    New stub behavior goes through the existing `cmux_body=` / `picker_body=` / `env_extra=` knobs.

## ⚠ OUTSTANDING: the Module-1 test-debt sweep was NOT done
Module 1 closed with its plan tasks complete and every debt item **formally dispositioned**, but
the sweep itself is still owed. It lives in `deviations.md` → "Deferred Work" → "Task 6 test-debt
sweep". Highlights: two env-validation regression tests; the Task-4 cleanup trio (`max(0,…)` label
slice, surrogate `try`-wrap); six Task-5 mutation-proven gaps (three of which need a new harness
knob in the read-only helper); the unchecked reservation writes (`:422-423`); the untested
mktemp-failure branch; NM4 (failure-branch notify unasserted); NM5 (accepted, no test).
**Decide deliberately** whether to run it as a bounded round before Task 7 or fold it into Module 2
— do not let it evaporate.

## Enforcement scaffolding (all satisfied through Task 6)
Manifest `.sdd-session.json`: standard tier, **active_module_id 2**, `context_summary_at` **8**.
Per-task: `checkpoint-pre-dispatch-NNN.json` + `partner-review-NNN.md` (Task 0 exempt) + spec +
quality reviews, all dispatched (provenance in `reports/.dispatch-log`, archived at transition).
Task 6 additionally has `task-006-implementer-report-fix.md`, `-fix2.md`, and both re-reviews
appended to the bottom of its spec and quality review files. Pre-execution-audit present.
**0 pending deviations.**
