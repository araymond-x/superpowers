# cmux Integration — Distilled Implementation Spec
> **Source**: `docs/imp-plans/2026-07-22-cmux-integration/spec.md` (10 decisions) · **Distilled**: 2026-07-22 · **For**: plan writer and implementation agents ONLY. Full rationale in source.

## Out of scope — do not build

- SDD sidebar telemetry (`set-progress`/`set-status` from controller or hooks) → future feature
- Live artifact panels (`cmux markdown open`, `cmux diff` at finish) → future feature
- Worktree-workspace customization (one-click worktree agent buttons) → future feature
- Fleet orchestration (parallel Claude sessions as cmux workspaces) → own design later
- The other 3 cmux skills (`cmux-browser`, `cmux-settings`, `cmux-customization`) → install later if needed
- Codex-side symlinks (`~/.agents/skills`) → later
- N43 component (C) full pace-aware pause/resume via cupace (`claude-usage-pace`) → its own spec; ONLY the minimal spawn-time quota precondition here
- B10 pressure-conditional context-summary gate → separate fast-follow
- Any change to context-gate thresholds, tiers, probe, or observation-log format
- Auto-spawn from `writing-plans`/`brainstorming` sessions → later; SDD controller seam only

## Contract Facts

- Script: `skills/subagent-driven-development/scripts/spawn-handoff-session.sh [BUNDLE_PATH] [--dry-run]`. `--dry-run` evaluates all preconditions, prints composed cmux commands, spawns nothing.
- Exit codes: `0` spawned · `3` manual fallback (not-in-cmux / hop limit / quota) · `1` refused (dirty tree / missing bundle / missing `.active-feature`). Every non-spawn path prints the manual resume instructions; exit-3 paths with cmux reachable also `cmux notify` the reason.
- Preconditions, in order (worktree root = `git rev-parse --show-toplevel`; feature dir = `.active-feature` at that root): (1) `git status --porcelain` empty else exit 1; (2) bundle exists else exit 1; (3) `CMUX_WORKSPACE_ID` set AND `cmux ping`=PONG else exit 3; (4) hops < `SUPERPOWERS_CMUX_MAX_HOPS` (default 3) else exit 3; (5) quota fail-open — below threshold exit 3; cupace absent/error/timeout → proceed, log `quota=unchecked`.
- Spawn argv: `cmux new-workspace --name "SDD resume: <feature>" --cwd <worktree-root> --command 'claude "/pickup"' --focus false`; then `cmux notify --title "SDD handoff" --body "Hop N/<max> — successor spawned in <workspace-ref>"`. Bundle default: latest under `~/.claude-codex-handoff`; default is NEVER interpolated (`/pickup` resolves latest). Explicit path must resolve under `~/.claude-codex-handoff`, no whitespace/quotes, else exit 1; then prompt is `claude "/pickup <path>"`.
- State files (both **tracked** in git, committed by successor's normal step-2 commit): `<feature-dir>/reports/.handoff-hops` (counter, incremented on spawn); `<feature-dir>/reports/handoff-spawn.log` (one line/spawn: ISO-8601, hop, workspace ref, bundle path, quota status). Separate from `context-observations.log` — do not touch its format.
- Vendored skills: `external-skills/{cmux,cmux-workspace,cmux-markdown,cmux-diagnostics}/` — pristine upstream copies (NEVER locally edited) from `manaflow-ai/cmux` at a pinned SHA recorded in `external-skills/VENDOR.md`. Symlinks: `~/.claude/skills/<name> → <repo>/external-skills/<name>` (no command stubs).
- `sdd-pre-dispatch-hook.sh`: **NO change**, no baseline re-capture (block message already points to the protocol doc, line 840 — verified). SDD SKILL.md body: **NO change** (word ceiling).
- Protocol doc `references/context-handoff-protocol.md`: steps 1–3 unchanged; steps 4–5 rewritten to: run the spawn script; exit 0 → report workspace ref; exit 3 → relay printed instructions; exit 1 → fix precondition, re-run; then STOP. Closing note: same script serves early handoff at the soft nudge.
- `validate-all-skills.py` excludes `external-skills/`; `verify-symlink-install.sh` checks the 4 symlinks + VENDOR.md SHA; e2e gains Step 14 (banner 14→15); unit suite = `tests/unit/test_spawn_handoff.py` (stub `cmux` + stub `claude-usage-pace` on PATH recording argv; case matrix in source §7).

## Open Decisions

| # | Decision | Options | Resolution Required By |
|---|----------|---------|----------------------|
| 1 | Quota check parameters: JSON field for remaining 5h-window capacity, refuse threshold, env var name (proposed `SUPERPOWERS_CMUX_QUOTA_MIN_PCT`), timeout for the nested call | Inspect live `claude-usage-pace --json` output | Plan writer, before Component B tasks |

## Decision Summary

| # | Decision | Chosen |
|---|----------|--------|
| 1 | Autonomy level | Fully automatic (successor launches and `/pickup` submits unattended) |
| 2 | Spawn logic placement | Deterministic script invoked by protocol step 4 |
| 3 | Skill install mechanism | Vendored at pinned SHA + per-skill symlink |
| 4 | Skill subset | 4: cmux, cmux-workspace, cmux-markdown, cmux-diagnostics |
| 5 | Launch mechanics | `new-workspace --command 'claude "/pickup"'` (no typed keystrokes) |
| 6 | Runaway guard | Hop counter file + `SUPERPOWERS_CMUX_MAX_HOPS` default 3 |
| 7 | Quota guard | Minimal fail-open cupace precondition |
| 8 | Spawn event log | Separate `reports/handoff-spawn.log` |
| 9 | Vendored-file policy | Pristine; fork guidance goes in CLAUDE.md only |
| 10 | Regression-suite treatment | Exclude `external-skills/` |

## Component Specifications

**A — Vendoring**: `sync-cmux-skills.sh` takes an upstream ref (default `main`), sparse-clones `manaflow-ai/cmux`, replaces the 4 vendored dirs wholesale, rewrites VENDOR.md with resolved SHA, prints diff summary. Never merges.
**B — Spawn script**: success path = preconditions 1–5 → spawn argv → increment `.handoff-hops` → notify → append spawn-log line → print workspace ref → exit 0; controller STOPs. **Plan ordering**: vendor A first and verify the cmux CLI surface against vendored docs or live `cmux --help` BEFORE freezing B's exact-argv unit assertions. Re-expand the post-merge live-smoke procedure from source §7.
**Docs**: CLAUDE.md new "cmux Integration" section (`SUPERPOWERS_CMUX_MAX_HOPS` joins env-var gotchas); customization-manifest inventory entries; BACKLOG row closing N43(D).

## Acceptance Criteria

- [ ] 4 cmux skills auto-list in a fresh Claude session
- [ ] `--dry-run` passes all preconditions in a real cmux SDD session
- [ ] One real spawn: workspace opens, `claude` launches via wrapper, `/pickup` ingests, SDD resumes at first unchecked task
- [ ] Non-cmux terminal: exit 3 + manual instructions (parity with today)
- [ ] Hop limit: attempt max+1 (4th, default max 3) falls back to manual with notification
- [ ] All suites green: unit, regression (unchanged counts), installation, e2e (15 steps)
- [ ] CLAUDE.md, customization manifest, BACKLOG updated; hook baseline untouched
