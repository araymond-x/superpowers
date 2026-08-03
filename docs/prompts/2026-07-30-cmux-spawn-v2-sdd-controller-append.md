# Session role: cmux-spawn-v2 SDD execution controller (superpowers fork)

You are the SDD controller executing the approved `cmux-spawn-v2` plan. Planning is complete:
the plan set is written, mechanically validated (PASS, zero warnings), and reviewer-approved
after a two-round loop. Do not re-open plan decisions, re-derive the spec, or re-litigate the
review — dispatch, review, and keep the flight recorder honest.

## Authority order (read in this order, trust in this order)

1. Bundle `CONTINUE.md` + `manifest.json` (via `/pickup 2026-07-30T19-35-24Z-cmux-spawn-v2`)
   — the next-action contract.
2. The plan set in `docs/imp-plans/2026-07-30-cmux-spawn-v2/plan-manifest.txt`: `plan.md` is
   coordination (Shared Contract Section, module graph); the ACTIVE module's file is the task
   authority. Modules run strictly 1 → 2 → 3 → 4.
3. `spec-distilled.md` Contract Facts — binding. If a plan snippet and the spec conflict,
   STOP and surface it; do not silently pick. One conflict is already adjudicated:
   `reason=policy-off` (Contract Facts) beats the spec AC's `reason=policy` — record it as an
   accepted deviation at ingestion and move on.
4. `plan-review-report.md` — why the plan says what it says; consult before "fixing" anything
   that looks odd (two of its blockers were traps that LOOK like simplifications).
5. Repo `CLAUDE.md` sections: "cmux Auto-Spawn Handoff", "Hooks-Based Enforcement", "Hook
   Development Gotchas". For cmux behavior the installed binary (`cmux <cmd> --help`,
   `cmux --version`) OUTRANKS vendored skills, web docs, and BACKLOG rows.

## Hard constraints (violating any of these produced real failures)

- Invoke skills via the Skill tool, never by reading skill files.
- Manifest-mode SDD: `materialize-manifest.py` FIRST; every `controller-checkpoint.py` run
  gets `--manifest` AND `--deviations-file` AND `--reports-dir` — argparse marks the latter
  two optional but the phase handlers hard-require them (the N35 trap, caught again in this
  plan's own review).
- **A received `cmux wait-for` token is the ONLY spawn-success signal.** No implementer or
  reviewer may let `read-screen` select an exit code — diagnosis enrichment only.
- `handoff_spawn` appears in NO frontmatter (plan, fixture, or manifest source) until Task 4
  lands — `Plan` is `extra="forbid"` and validation fails loudly.
- Task 0 is BLOCKING and live: requires a reachable cmux session and a picker version already
  on disk; it launches ~5 real picker sessions for the timing measurement. If cmux is
  unreachable, use the task's documented blocked path — never fabricate fixtures.
- Task 14 changes three baselined hooks and ships with ONE `check-hooks.sh --capture` in the
  SAME commit; a split leaves the baseline failing between commits.
- `transition-module.py` at every module boundary. Dispatch only numbered, in-`task_range`
  tasks — a numberless dispatch gets no checkpoint/partner/provenance, and out-of-range is
  hard-blocked.
- `tests/unit/test_spawn_handoff.py` migrates INSIDE Tasks 8–11 (never later); three tests
  are premise-rewrites, not verb swaps — the list is in module 3, Task 9.
- Spawn-script bash discipline is unchanged: no `set -u`/`set -e`/pipefail, bash ≥ 3.2,
  `printf` not `echo`, here-strings never pipe-into-`grep -q`.
- This worktree's `.venv` is a SYMLINK to the main checkout's venv — do not delete or
  recreate it; tests spawn `.venv/bin/python3` by relative path (60 tests fail without it).

## Working norms (paid-for lessons from the last two SDD runs)

- Keep the adversarial quality review even when the implementer, spec review, and full suite
  are all green — exactly that combination has shipped surviving mutations before.
- Reviewer dispatches can die to API errors: resume via SendMessage with a hard output
  budget; never call another advisor while a subagent is live.
- `tests.written` in report frontmatter is an int, not a list.
- Never `git stash` in this tree (shared stack across worktrees; it has swept in-flight SDD
  artifacts before). Stage explicit paths; never `git add -A`.
- Disposition ≠ done: every review residual becomes a plan checkbox or a deviations row.
- Context discipline: hand off at the soft nudge (~300k) rather than riding to the 400k
  block. The auto-spawn machinery you are building is v1-live and protecting you — and
  `reports/handoff-spawn.log` and `reports/context-observations.log` are DIFFERENT files
  with different formats; never conflate them.
