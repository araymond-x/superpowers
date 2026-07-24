# Context Summary — cmux-integration repo-3 SDD (Module 2 active, Task 7 done)

> Flight-recorder digest. Rich resume guidance is in the handoff bundle's CONTINUE.md.

## Status: **Module 1 complete + transitioned. Task 7 (Sweep A) complete. Resume at Task 8 (Sweep B).**

| Task | State | Commit | Notes |
|------|-------|--------|-------|
| 0–6 | ✅ done (reviewed) | thru `cfe8c27` | Module 1: script + 58-test unit suite. Archived to `reports/archive-…/`. |
| — | ✅ plan surgery | `518875c` | Sweep promoted from unnumbered round → gated Tasks 7-8; old 7/8/9 renumbered → 9/10/11. |
| 7 | ✅ **done (reviewed, 2 commits)** | `8ea8509` + `4f1328f` | Sweep A: 2 harness knobs + 5 mutation-proven tests. Partner APPROVED; spec PASS; quality PASS-with-fixes → fix → **re-review PASS**. |
| 8 | ⬜ **NEXT** | — | Sweep B: script hardening + residual coverage + plan-doc corrections. **Now the largest remaining task — 8 step-checkboxes.** |
| 9–11 | ⬜ | — | Protocol rewrite, e2e Step 14, docs. |

Suites: `test_spawn_handoff.py` **63 passed**; `tests/unit/` **616 passed**. Working tree clean at `35c382b`.
Module-2 checkboxes: **7 ticked / 30 unchecked**. **0 pending deviations.**
Manifest: `task_range [7,11]`, `total_tasks 12`, `midpoint`/`context_summary_at` **9**.

## ⚠ READ FIRST

1. **MUTATION-TEST EVERY ASSERTION — and it is still not enough on its own.** Task 7's implementer
   ran 7 mutations and did it well (it even ran a *predicted-GREEN* mutation rather than inferring
   it, which is how a plan defect surfaced). The spec reviewer independently re-ran 5 more and
   audited the test-echo collision class clean. **The quality review still found TWO surviving
   mutations on a green 63-test suite** (MX-A: the `-f` half of the version predicate; MX-B: the
   fractional half of the `QUOTA_MIN_PCT` regex). Both are now Task 8 Step 4b. ➡ The lesson is not
   "mutate more"; it is **keep the adversarial quality review even when everything upstream passed.**

2. **The `-f`/`-x` class: ask which HALF of a conjunction a test pins.** A test that fails both
   operands pins only the conjunction. Task 7's original comment claimed prior coverage of `-f`
   that never existed. Generalize this when reviewing Task 8's new tests.

3. **Reviewers are fallible in a specific, checkable way — verify their premises, not just their
   conclusions.** The Task-7 quality re-review filed a confident finding backed by an "empirical"
   throwaway test. It was **wrong**: the probe lived in a scratchpad file, so the module-scoped
   autouse `_hermetic_picker_env` fixture never applied and ambient picker env leaked in. A
   controller probe **with a positive control** (inject `exit 42` if the var is set; confirm the
   `9.9.9` param FAILS so the guard is proven live, then confirm the `{}` param PASSES) settled it,
   and the reviewer withdrew the finding. ➡ **Always include a positive control** — without the
   `9.9.9` leg, the `{}` pass is indistinguishable from a probe that never fired.

4. **Disposition ≠ done.** The Module-1 sweep was fully dispositioned yet undone for a whole module.
   Every residual found in Task 7 was given a **plan checkbox** (Steps 4b/4c/4d), not a report
   paragraph, because only checkboxes reach the pre-completion gate.

5. **Do not "clean up" the plan.** Steps 4b/4c/4d and the sweep checkboxes are load-bearing.

## Task 8 is pre-loaded with findings — read its steps before dispatching
- **Step 1** reservation-write rc checks. **Route failure to the EXISTING exit 3** — the 0/3/1 ladder is frozen by the module Contract Constraints and documented by Task 11. A new exit code silently invalidates Task 10's e2e and Task 11's docs. Implementer must report BLOCKED rather than mint one.
- **Step 4b** the two surviving mutations (MX-A `-f` half → test with a *directory* named `2.1.218`; MX-B fractional `MIN_PCT` → `"12.5"` at a 63.0% reading, expect no WARNING + `quota=ok`).
- **Step 4c** decide the `:299` `command -v claude-picker` redundancy **explicitly** (it is provably redundant with `:301` and unobservable black-box). Keeping it is defensible — but state the reason; do not leave it decided-by-default.
- **Step 4d** move `_hermetic_picker_env` to `tests/unit/conftest.py` (import `PICKER_ENV_VARS`, do not restate it). Module scope is what let a reviewer's own probe inherit ambient env and file a wrong finding.
- **Step 5** the three owed plan-doc corrections in `module-1-spawn-script.md`.

## Contract facts frozen (unchanged)
- Composed flag order: `claude-picker --non-interactive --pick-version <v> --telemetry <on|off> [--session-label <l>] <args> "/pickup <id>"`.
- `cmux new-workspace` prints `OK <ref>` on stdout, LF-terminated, rc 0 — parse with `awk`, never `while read`.
- Repo identity = `realpath(git rev-parse --git-common-dir)`. Bash floor **3.2** (not 4.x).
- `cmux new-workspace`/`close-workspace` are deprecated aliases; script keeps the legacy spelling. BACKLOG candidate.

## Process gotchas (still current)
1. `tests.written`/`tests.passing` are **per-round integers**, `passing ≤ written` — never the file total (63 pass now). A list of names fails the Pydantic model and blocks the next dispatch.
2. Verify any `-k` filter with `--collect-only -q`.
3. Env `.py` file-watcher cosmetically line-wraps test files post-write — benign.
4. Do **not** add `set -u` to the script (bash 3.2 `${FORWARDED[*]}` on empty array).
5. Tick plan checkboxes **before** running the next checkpoint.
6. **Never call the advisor tool while a subagent is live** (unrecoverable API 400).
7. Disposition deviations before dispatching — the hook hard-blocks on any `| Pending |`.
8. Give every reviewer an explicit **output budget** up front (800–1400 words). Two Module-1 reviewer dispatches died mid-response; `SendMessage` resume from transcript is the recovery that works — and it worked again here for the re-review round.
9. Mutating the read-only script for a proof is fine — restore with `git checkout --`/copy-restore, **never `git stash`** (it sweeps the controller's in-flight report artifacts), and verify `git diff --name-only` is empty.

## Enforcement scaffolding
Per-task `checkpoint-pre-dispatch-NNN.json` + `partner-review-NNN.md` + spec + quality reviews, all dispatched (provenance in `reports/.dispatch-log`). Task 7 additionally has `task-007-implementer-report-fix.md` and the round-2 re-review appended to the bottom of `task-007-quality-review.md`.
