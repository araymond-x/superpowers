---
schema_version: 1
task_id: 3
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh"
    description: "Added Stage 0 (fix/re-review marker classification), guarded Stage 1 + Stage-2 log write with MARKED_FIX, added Stage-3 unattributed fallback, extended Check 3b allowlist, appended FIX/RE-REVIEW MARKERS additionalContext line"
  - path: "skills/subagent-driven-development/references/dispatch-markers.md"
    description: "New controller-side doc documenting the [task N fix] / [task N re-review:KIND] marker convention and the type=implementer-window invariant"
  - path: "tests/ARaymond-hook-baseline/baseline.txt"
    description: "Re-captured sha256 baseline for the edited hook (only the sdd-pre-dispatch-hook.sh hash line changed)"
  - path: "tests/unit/test_sdd_classification.py"
    description: "Added 4 tests + _read_log helper at end of file: marked-fix type=fix-not-implementer, marked re-review reviewer passthrough, markerless fix-unattributed, Check 3b gate-artifact allowlist"
tests:
  written: 4
  passing: 4
  command: ".venv/bin/python3 -m pytest tests/unit/test_sdd_classification.py -v -k 'marked_fix or marked_rereview or markerless_fix or check3b'"
  result: PASS
contract_compliance:
  - constraint: "Marked fix emits ONLY `type=fix`, NEVER `type=implementer` (would move Check 9's verification window)"
    status: compliant
    detail: "Stage 0 logs `DISPATCH fix task=N type=fix` and sets MARKED_FIX=true; the Stage-2 write is guarded with `[ \"$MARKED_FIX\" = false ] &&`. Test test_marked_fix_logs_type_fix_not_implementer asserts BOTH presence of `task=3 type=fix` AND absence of `task=3 type=implementer`."
  - constraint: "Stage 0 runs BEFORE Stage 1 (a fix-REVIEW description contains 'review')"
    status: compliant
    detail: "Stage 0 inserted between TASK_NUMBER=\"\" and the `# Stage 1` comment; Stage 1 condition prefixed with `[ \"$MARKED_FIX\" = false ] &&`. RED step confirmed the unmodified hook mis-classified `[task 4 re-review:quality]` as `task=4 type=unknown`, which is the exact justification for Stage 0 precedence."
  - constraint: "Dispatch-log line grammar unchanged for the reader (controller-checkpoint.py Check 9 `_merged_dispatch_times`)"
    status: compliant
    detail: "Confirmed read-only against controller-checkpoint.py regex `(\\S+)\\s+DISPATCH\\s+implementer\\s+task=(\\d+)\\s+type=implementer` — only `type=implementer` lines open a window. New lines emit `type=fix` / `type=fix-unattributed`, which the reader never matches."
  - constraint: "Baseline re-captured in the SAME commit as the hook edit"
    status: compliant
    detail: "git diff baseline.txt showed exactly one changed hash line (sdd-pre-dispatch-hook.sh: a7b5b1→b61d5a); settings.json block unchanged; live hook hash matches baseline; check-hooks.sh verify PASSes. All 4 files committed together."
  - constraint: "Commit uses explicit paths only (no git add -A); untracked plan/reports/.dispatch-log stay untracked"
    status: compliant
    detail: "Staged exactly the 4 named files; git status confirms plan/reports/deviations remain untracked post-commit."
  - constraint: "No regression across other hook-driven unit files"
    status: compliant
    detail: "Full tests/unit/ suite run after hook edit: 477 passed, 0 failed (covers test_sdd_hook_hardening.py, test_n1_multi_error_accumulation.py, test_checkpoint_archive_aware.py, etc.)."
---

**Implementation Summary:**

Closed the N26 dispatch-log fix-cycle blind spots in `sdd-pre-dispatch-hook.sh`. Added a deterministic **Stage 0** (before reviewer detection) that recognizes two explicit markers in the Agent dispatch description: `[task N re-review:{spec|quality|partner}]` logs a reviewer line and passes through (`exit 0`), and `[task N fix]` logs `DISPATCH fix task=N type=fix`, sets `IS_IMPLEMENTER=true` + `MARKED_FIX=true`, then falls through to the implementer enforcement path. Guarded Stage 1 (reviewer detection) and the Stage-2 implementer-log write with `[ "$MARKED_FIX" = false ] &&` so a marked fix is neither re-classified as a reviewer nor double-logged as `type=implementer` (the load-bearing invariant: a marked fix must not move task N's Check 9 verification window). Added a **Stage-3 unattributed fallback** that records `DISPATCH adhoc type=fix-unattributed` for a markerless dispatch matching `\bfix\b|remediat` (tamper-evidence, no enforcement change, no task attribution). Extended the Check 3b report-naming allowlist with `honesty-check-|execution-trace-audit\.md|final-code-review\.md` so the three gate-required artifacts no longer trip the non-standard-naming block. Appended a FIX/RE-REVIEW MARKERS line to the allowed-dispatch `additionalContext`, and created `references/dispatch-markers.md` documenting the convention (zero SKILL.md word cost). Re-captured the hook integrity baseline in the same commit.

TDD: wrote 4 failing tests first, confirmed each failed for its intended reason (especially the re-review test producing `task=4 type=unknown` against the unmodified hook), then implemented and confirmed all pass.

**Source Files Read:**
- `docs/imp-plans/2026-06-10-sdd-aggregate-gate-visibility/module-1-aggregate-visibility.md` (Task 3 — the 12 steps applied verbatim)
- `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` (the edited file; all anchors confirmed at lines 151/153-154/197/206-209/404/772)
- `skills/subagent-driven-development/scripts/controller-checkpoint.py` `_merged_dispatch_times` (READ-ONLY — confirmed the `type=implementer`-only window contract)
- `tests/unit/test_sdd_classification.py` (existing tests + helper-import pattern, extended at END)
- `tests/unit/sdd_test_helpers.py` (confirmed `make_hook_input`, `setup_sdd_workspace(tmpdir, task_count)`, `setup_full_sdd_workspace(tmpdir, total_tasks, completed_tasks)` signatures)
- `tests/ARaymond-hook-baseline/check-hooks.sh` + `baseline.txt` (re-capture mechanics; noted it reads settings.json from the main checkout but hashes REPO_ROOT = worktree)

**CLAUDE.md Files Read:**
- Repo-root `CLAUDE.md` (hook architecture, dispatch-log grammar, the "edit a baselined hook → re-capture baseline in same change" rule, Bash hook gotchas: never pipe a producer into `grep -q` under pipefail — though this task added no such pipe)
- `~/.claude/CLAUDE.md` + `~/.claude/rules/*` (global preferences: TDD, architectural principles, coding style)

**Deviations from Plan:**
1. **TEST SIGNATURE CORRECTION (Resolved PlanDefect, pre-flagged in the task brief and logged in deviations.md):** The plan's literal stubs call `setup_full_sdd_workspace(tmpdir, task_count=5)`. The real signature is `setup_full_sdd_workspace(tmpdir, total_tasks, completed_tasks)` (`task_count` is not a parameter; `completed_tasks` is required). Applied the prescribed correction `setup_full_sdd_workspace(tmpdir, total_tasks=5, completed_tasks=2)` in both stubs that use it (`test_marked_fix_logs_type_fix_not_implementer`, `test_check3b_allows_gate_artifact_names`), mirroring existing tests at test_sdd_classification.py:177/:241. The two stubs using `setup_sdd_workspace(tmpdir, task_count=5)` were correct as-is and left unchanged. No other deviations — all 12 steps' code blocks were applied exactly as written.

**Self-Review Findings:**
- All 5 hook edits were unique exact-string replacements; verified each anchor matched the plan before editing.
- RED step verified meaningful: each of the 4 tests failed for its intended cause (no `task=3 type=fix`; `task=4 type=unknown` mis-classification; empty log / no `type=fix-unattributed`; `non-standard naming` present in stderr).
- `set -uo pipefail` safety: `MARKED_FIX=false` is always assigned in Stage 0 before any later reference, so no unbound-variable risk. The new Stage-3 `grep -qiE` is a single command on a piped `echo`, matching the existing hook style (it is not a producer-into-`grep -q` pipeline that could fail-open under pipefail, so no here-string conversion was needed).
- Marked-fix GREEN behavior is by design: with `completed_tasks=2`, `[task 3 fix]` logs `task=3 type=fix` in Stage 0 then falls through to enforcement and BLOCKS (task 2's reports aren't seeded). The test asserts log CONTENT only (written before the gate), so exit 2 is expected and correct — no returncode assertion was added.
- Baseline trap actively checked: `git diff baseline.txt` showed exactly one changed hash line (the hook), and the live hook's hash equals the new baseline value — the baseline hashed the correct worktree copy, not a stale main copy.
- Full unit suite (477 passed) run to catch shared-hook regressions per the "audit all callers" principle; no `after == before` style assertion elsewhere regressed from the new Stage-3 fix-logging behavior.

**Concerns:**
- The Stage-3 `\bfix\b|remediat` heuristic logs `type=fix-unattributed` for ANY markerless dispatch whose description contains the word "fix" (e.g., an Explore dispatch described as "investigate the fix for X"). This is intentional tamper-evidence (it changes no enforcement and adds no task attribution), and matches the plan's design, but it does make the live `.dispatch-log` noisier. The line is harmless to Check 9 (never matches `type=implementer`). Flagging for awareness only — no action needed.
- `check-hooks.sh` hard-codes `SUPERPOWERS_PATH="/Users/araymond/projects/claude-custom/superpowers"` (the main checkout) for the settings.json registration scan, while hashing `REPO_ROOT` (the worktree). The two happened to agree here because the registration block is identical and unchanged. This is pre-existing behavior, out of scope for Task 3, but worth noting: a divergent settings.json on a different machine would surface in the registration block, not the hash block.
- Plan-level cosmetic gap (applied Stage 0 faithfully as the plan prescribed, no sentinel logic): the Stage 0 re-review (`exit 0`) and markerless-fix paths do not write the dispatch-log sentinel. If a re-review or markerless-fix dispatch is the FIRST write to a fresh log, the log is sentinel-less and a later implementer dispatch emits the WARN-only "no hook-written sentinel" line (Check at hook ~line 323). That check never blocks, so there is no enforcement impact — flagging as a plan-level follow-up candidate, not an implementation defect.
