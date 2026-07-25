# Context Summary — cmux-integration repo-3 SDD (Module 2 active, Task 8 done)

> Flight-recorder digest. Rich resume guidance is in the handoff bundle's CONTINUE.md.

## Status: **Module 1 complete + transitioned. Tasks 7 and 8 complete. Resume at Task 9.**

| Task | State | Commit | Notes |
|------|-------|--------|-------|
| 0–6 | ✅ done (reviewed) | thru `cfe8c27` | Module 1: script + 58-test unit suite. Archived to `reports/archive-…/`. |
| — | ✅ plan surgery | `518875c` | Sweep promoted from unnumbered round → gated Tasks 7-8; old 7/8/9 renumbered → 9/10/11. |
| 7 | ✅ done (reviewed) | `8ea8509` + `4f1328f` | Sweep A: 2 harness knobs + 5 mutation-proven tests. Quality found 2 surviving mutations → routed to Task 8. |
| 8 | ✅ **done (reviewed, 2 commits)** | `7a46dae` + `53318b5` | Sweep B: reservation hardening + 9 tests + fixture move + plan-doc fixes. Quality found MX1 → fix round → **re-review PASS**. |
| 9 | ⬜ **NEXT** | — | Rewrite `context-handoff-protocol.md` steps 3–5 (steps 1–2 byte-identical). |
| 10–11 | ⬜ | — | e2e Step 14 + banner 14→15; docs (CLAUDE.md, manifest, BACKLOG N43(D)). |

Suites: `test_spawn_handoff.py` **72 passed**; `tests/unit/` **625 passed**. Working tree clean of code at `53318b5`.
Module-2 checkboxes: **17 ticked / 22 unchecked** (Task 9: 5, Task 10: 5, Task 11: 6, Acceptance: 6). **0 pending deviations.**
Manifest: `task_range [7,11]`, `total_tasks 12`, `midpoint`/`context_summary_at` **9**.

**⚠ `spawn-handoff-session.sh` IS NOW FROZEN.** Task 8 was the last task that writes it. Tasks 9–11
consume it read-only. Any change to its observable behavior invalidates Task 10's e2e assertions and
Task 11's docs.

## ⚠ READ FIRST

1. **THE QUALITY REVIEW HAS NOW PAID ON THREE CONSECUTIVE TASKS (6, 7, 8) — never thin it.** On Task
   8 the implementer ran 9 mutations well, *self-caught* a hollow assertion mid-task, and the spec
   reviewer independently re-ran 4 more and verified every contract constraint. **The quality review
   still found a surviving mutation on the green 625-test suite** (MX1). Upstream rigor does not
   predict downstream cleanliness.

2. **The conjunction trap recurs at every layer — isolate the FIXTURE, don't just sharpen the
   assertion.** MX1: leg A's fixture (`chmod 0555` on the reports dir) failed **both** reservation
   writes, so deleting the hops guard's `exit 3` left 72/72 green — the *intent* guard downstream
   supplied the `rc==3` and absent spawn, while the un-mutated `echo` satisfied the warning
   assertion. The implementer had already found this class in the same test and fixed message
   *attribution*; that was not enough, because **detection and stopping are different properties**
   and only one was mutated. Fix: `.handoff-hops` pre-created as a **directory** (EISDIR on that
   write alone). Ask of every assertion: *which half does this pin, and does the fixture let the
   other half stand in for it?*

3. **Always run a POSITIVE CONTROL.** Every empirical claim this session carried one: the partner's
   line-number finding (verified by `grep -n` before accepting), MX1 (printed the mutated block
   before trusting the test result), MX-A (a real executable file must reach `launch=auto`, since
   `preflight_ok()` is a five-way AND), MX-P (moving an echo one line up proves placement is
   load-bearing). A passing test without a positive control is indistinguishable from a probe that
   never ran.

4. **Verify reviewer PREMISES, not just conclusions — in both directions.** The partner review was
   right about the notify line number (`:445`, not the controller's claimed `:447`) and **wrong**
   about "1 pending deviation" (actually 0). Both were checked; one accepted, one rejected, both
   recorded. A reviewer being right about one thing is not evidence it is right about the next.

5. **Disposition ≠ done.** Every residual gets a plan **checkbox**, never a report paragraph. Task 8's
   ratified `cmux notify` asymmetry became **Task 11 Step 1b**. Do not delete or un-tick boxes to
   "tidy" the plan — the pre-completion all-checkboxes gate is their only enforcement.

## Task 8 outcome (for Tasks 9–11 to build on)

- **Reservation writes are now rc-checked.** Both `.handoff-hops` and the `intent` append route a
  failure to the **existing exit 3** after `print_manual_instructions`. **The 0/3/1 ladder is
  unchanged** — verified: shell exits are only 0, 1, 3; the lone `exit 4` token is inside a comment,
  and the decoder's `sys.exit(5)` is heredoc-internal (consumed as `if [ $? -ne 0 ]; then ARGS_OK=0`).
- **Decode failures now emit a diagnostic** (`[spawn-handoff] warn: forwarded-args decode failed —
  degrading to picker-manual`). The echo must stay **inside** the `if [ $? -ne 0 ]` branch — moving it
  above makes `[` consume the decoder's status and a decode failure silently proceeds with dropped
  args (proven by mutation MX-P).
- **`_hermetic_picker_env` now lives in `tests/unit/conftest.py`**, autouse for all 625 tests, with
  `PICKER_ENV_VARS` defined exactly once and no test-module import. Do not weaken or narrow it.
- **Task 11 owes a doc item** beyond its original scope: Step 1b, documenting that reservation-write
  failures exit 3 **without** a `cmux notify` (unlike hop-limit / quota-low / spawn-failed) as a
  deliberate rule.

## Contract facts frozen (unchanged)
- Composed flag order: `claude-picker --non-interactive --pick-version <v> --telemetry <on|off> [--session-label <l>] <args> "/pickup <id>"`.
- `cmux new-workspace` prints `OK <ref>` on stdout, LF-terminated, rc 0 — parse with `awk`, never `while read`.
- Repo identity = `realpath(git rev-parse --git-common-dir)`. Bash floor **3.2** (`/bin/bash` here IS 3.2.57).
- `cmux new-workspace`/`close-workspace` are deprecated aliases; script keeps the legacy spelling. BACKLOG candidate.

## Process gotchas (still current)
1. `tests.written`/`tests.passing` are **per-round integers**, `passing ≤ written` — never the file total, never a list of names (fails the Pydantic model and blocks the next dispatch).
2. **`bash scripts/lint-shell.sh` with no args is VACUOUS post-commit** — it selects changed-vs-base and prints "No shell files found." Run `shellcheck --severity=warning --external-sources <file>` directly, or `lint-shell.sh --all`. Task 8's Step-6 lint line was evidence of nothing (caught by spec review).
3. Verify any `-k` filter with `--collect-only -q`.
4. Env `.py` file-watcher cosmetically line-wraps test files post-write — benign.
5. Do **not** add `set -u`/`set -e`/`pipefail` to the script (bash 3.2 `${FORWARDED[*]}` on empty array).
6. Tick plan checkboxes **before** running the next checkpoint.
7. **Never call the advisor tool while a subagent is live** (unrecoverable API 400).
8. Disposition deviations before dispatching — the hook hard-blocks on any `| Pending |`.
9. Give every reviewer an explicit **output budget** up front (800–1400 words; 600–1000 for a re-review). `SendMessage` resume from transcript is the recovery when a reviewer dies mid-response — used successfully twice this session (partner round 2, quality round 2).
10. Mutating the read-only script for a proof is fine — restore with `git checkout --`/copy-restore, **never `git stash`** (it sweeps the controller's in-flight report artifacts), and verify `git diff --name-only` is empty.
11. **Locate plan targets by CONTENT, not line number.** The controller injected a "verified fact" block to prevent line drift and put a drift error in it (claimed the notify was at `:447`; it is `:445`). The partner caught it pre-dispatch.

## Enforcement scaffolding
Per-task `checkpoint-pre-dispatch-NNN.json` + `partner-review-NNN.md` + spec + quality reviews, all
dispatched (provenance in `reports/.dispatch-log`). Task 8 additionally has
`task-008-implementer-report-fix.md`, and the round-2 re-review is appended to the bottom of
`task-008-quality-review.md`. Task 8 provenance rows: partner-review, implementer, spec-review,
quality-review, fix.
