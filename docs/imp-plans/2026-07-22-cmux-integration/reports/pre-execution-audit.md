# Pre-Execution Audit Report

**Feature:** cmux Integration — Repo-3 (superpowers)
**Date:** 2026-07-24
**Auditor:** general-purpose (sonnet), dispatched with self-assessment + all 3 plan files + distilled spec + Contract Constraints
**Verdict:** ORDERS_ISSUED (2 orders) → **both RESOLVED below**

The auditor independently traced and verified clean: precondition ordering (clean→bundle→cmux→hop→quota), `SP_HOP` define-before-use across Tasks 2/4/5/6, reservation-before-spawn, `ARGS_OK` decode-failure handling (round-1 blocker fix holds), label-rule arithmetic incl. 255 boundary, dry-run short-circuit placement, e2e Step 14 wiring, Write-Scope Partitioning. The self-assessment's flagged uncertainties (Task 3 quota timeout wrapper, Task 4 append rematerialize, Task 5 compose quoting) were each verified correct. No plan defect in the core logic.

---

## Order 1 (MEDIUM) — RESOLVED

**Finding:** Task 0 never verified that `cmux new-workspace --command` executes its value *through a shell*. The entire `launch=auto` design embeds a single-line compound command (`<picker cmd> || { printf …; claude-picker …; }`) into the `--command` string. Prior review confirmed only the argv *flag names* via `cmux --help`, not the execution semantics. If cmux exec'd the string directly (whitespace-split, no shell), the auto happy-path would silently break — and no unit test could catch it because the test harness stubs `cmux` as a trivial arg-logger. It would only surface at the Post-Merge Live Smoke, after all 9 tasks were built on the assumption.

**Resolution:** Verified the contract fact directly against live sources (controller is currently in a live cmux workspace):
- `cmux new-workspace --help` documents `--command <text>` as **"Send text+Enter to the new workspace after creation."** The string is typed into the new workspace's **interactive shell** and executed via Enter — so it IS shell-interpreted (compound `||`, `{ ;}`, quotes, `$(…)` all work).
- The interpreting shell is the workspace's login shell — **zsh** here, not bash. The composed successor command is zsh-safe (`||`, `{ ;}`, `printf`, `$(…)`, and `shlex.quote`d args are all POSIX/zsh-portable). Design holds.
- Corroborated by the vendored `cmux-workspace` skill doc (`references/commands.md:26`: `cmux new-workspace --command "npm run dev"`) and the `--help` examples (`--command "npm test"`), both of which use `--command` with shell command strings.

**Plan edit:** Added a sub-step to **Module 1, Task 0, Step 5** (module-1-spawn-script.md) instructing the implementer to freeze the `--command` = "text+Enter into the workspace shell (zsh)" semantics from `cmux new-workspace --help` and record it in the Task 0 report; `DONE_WITH_CONCERNS` if `--help` instead indicates direct exec without a shell.

**Definition of Done met:** Task 0 Step 5 now explicitly lists this check alongside the argv/exports/exit-3/executable-file checks; the Task 0 implementer will record the confirmed result before Task 1 begins.

---

## Order 2 (LOW) — RESOLVED

**Finding:** Module 2's three commit-message templates carried stale task numbers (off by 2 from their headers): Task 7's commit said `(Task 5)`, Task 8's `(Task 6)`, Task 9's `(Task 7)`. Left over from a pre-Task-0-insertion draft. Would corrupt future `git-reality` / trace-audit cross-referencing, and Task 9's `review_tier: minimum` means no full review would re-scrutinize it.

**Resolution:** Fixed all three parenthetical task numbers in module-2-protocol-e2e-docs.md to `(Task 7)`, `(Task 8)`, `(Task 9)` respectively.

**Definition of Done met:** `grep -n "(Task " module-2-protocol-e2e-docs.md` now shows Task 7/8/9 commit messages matching their surrounding `### Task N:` headers.

---

## Cross-repo prerequisite pre-check (controller, live)

Before dispatching Task 0, the controller confirmed live (cheap insurance against regression since the 2026-07-24 handoff):
- `claude-picker --handoff-contract` → `1` (exit 0) ✓
- All 4 cmux skill symlinks resolve (cmux, cmux-workspace, cmux-markdown, cmux-diagnostics) ✓
- `cmux ping` → `PONG` (controller is in a live cmux workspace) ✓

Task 0 re-verifies these by construction — this pre-check does not replace it.

**Both orders RESOLVED. Proceeding to Task 0 dispatch.**
