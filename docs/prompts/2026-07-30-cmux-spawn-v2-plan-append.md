# Session role: cmux-spawn-v2 implementation planning (superpowers fork)

You are the planning session for the `cmux-spawn-v2` feature. Your predecessor completed
brainstorming: the spec is written, spec-reviewed, distilled, externally reviewed by a Codex
round trip, and remediated. Do not re-open settled design questions or re-derive the live-run
analysis — consume the committed artifacts.

## Authority order (read in this order, trust in this order)

1. Bundle `CONTINUE.md` + `manifest.json` (via `/pickup`) — the next-action contract.
2. `docs/imp-plans/2026-07-30-cmux-spawn-v2/spec-distilled.md` — the PRIMARY planning input.
   Its Contract Facts and Decision Summary are binding; its two Open Decisions are yours to
   resolve in the plan (mechanics-card generator language; Task 0 handshake-timeout
   measurement — true cold start, shipped default = measured p95 × 2).
3. `docs/imp-plans/2026-07-30-cmux-spawn-v2/spec.md` — rationale/evidence backup only.
4. Repo `CLAUDE.md` sections: "cmux Auto-Spawn Handoff", "Hooks-Based Enforcement",
   "Hook Development Gotchas" — constraints on the code you will plan against.
5. For cmux behavior: the installed binary (`cmux <cmd> --help`, version-pin with
   `cmux --version`) OUTRANKS vendored skills, web docs, and BACKLOG rows. BACKLOG rows are
   hypotheses, not facts — several were corrected this week.

## Hard constraints (violating any of these produced real failures)

- Worktree first: invoke `superpowers:using-git-worktrees` before planning; plan and execute
  from the worktree, never on main.
- Invoke skills via the Skill tool, never by reading skill files.
- **A received `cmux wait-for` token is the ONLY spawn-success signal.** Screen reading is
  post-timeout diagnosis only. Do not weaken this while decomposing tasks — it was the
  external review's blocker and three live incidents motivate it.
- Sequencing: SP1/SP2 spikes early; `plan.py`/`sdd_session.py` model changes land BEFORE any
  plan/manifest frontmatter uses the new fields (`Plan` is `extra="forbid"`); the three
  changed baselined hooks (session-start, stop, pre-dispatch) ship with ONE
  `check-hooks.sh --capture` in the same change.
- SDD SKILL.md is near its word ceiling: new protocol content goes in `references/`, never
  the SKILL body. Check `wc -w` before and after any SKILL.md edit.
- The spawn script keeps its bash discipline: no `set -u`/`set -e`/pipefail, bash ≥ 3.2
  floor, `printf` not `echo`, never pipe a producer into `grep -q`.
- e2e Step 14 and `tests/unit/test_spawn_handoff*.py` assert the current workspace
  vocabulary — they change in the same tasks that change the topology, not later.

## Working norms

- Plan frontmatter declares `enforcement_tier`, modules with task ranges, and an
  `integration_test` pointing at the updated e2e step.
- Shared Constants Passthrough and Pattern References sections are required by the
  writing-plans skill — the spawn script, hooks, and checkpoint script are the pattern
  sources; do not let implementers rebuild what exists.
- Verify each spec claim you turn into a task against the current code (constructs, not line
  numbers — cite function names and quoted strings).
