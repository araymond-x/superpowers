# cmux Integration — Distilled Implementation Spec
> **Source**: `docs/imp-plans/2026-07-22-cmux-integration/spec.md` (rev 2, 15 decisions) · **Distilled**: 2026-07-22 · **For**: plan writer and implementation agents ONLY. Full rationale in source.

## Out of scope — do not build

- SDD sidebar telemetry (`set-progress`/`set-status` from controller or hooks) → future feature
- Live artifact panels (`cmux markdown open`, `cmux diff` at finish) → future feature
- Worktree-workspace customization (one-click worktree agent buttons) → future feature
- Fleet orchestration (parallel Claude sessions as cmux workspaces) → own design later
- The other 3 cmux skills (`cmux-browser`, `cmux-settings`, `cmux-customization`) → install later if needed
- Codex-side symlinks (`~/.agents/skills`) and codex-picker parity → later
- N43 component (C) full pace-aware pause/resume via cupace (`claude-usage-pace`) → its own spec; ONLY the minimal spawn-time quota precondition here
- B10 pressure-conditional context-summary gate → separate fast-follow
- Any change to context-gate thresholds, tiers, probe, or observation-log format
- Auto-spawn from `writing-plans`/`brainstorming` sessions → later; SDD controller seam only (layered spawn core = future extraction seam)
- Extracting the generic spawn core to `skills/scripts/` → when a second consumer arrives
- User-authored custom cmux skills in the new repo → later (layout leaves room; only vendored skills ship now)

## Contract Facts

**Three repos:** (1) superpowers = spawn script + protocol + tests + docs; (2) NEW repo `~/projects/claude-custom/cmux-custom-skills` = vendored skills; (3) telemetry-exp = `launchers/claude-picker` extension.

- Script: `skills/subagent-driven-development/scripts/spawn-handoff-session.sh [BUNDLE_PATH] [--dry-run]`. `--dry-run` evaluates all preconditions, prints composed `cmux` + `claude-picker` commands, spawns nothing, increments nothing (`.handoff-hops` untouched). Internal layering: generic `spawn_claude_workspace()` core (cmux detection, spawn, notify; params: cwd, launch command, workspace name, notify text) marked extraction-ready + SDD policy shell.
- Exit codes: `0` spawned (`launch=auto` — preflight passed: metadata usable (VERSION non-empty; ARGS/LABEL may be empty; ENABLE_TELEMETRY absent ⇒ off, never blocks auto) AND forwarded version binary exists at `~/.local/share/claude/versions/<version>`; auto command embeds residual fallback `<non-interactive picker cmd> || claude-picker "/pickup"`. OR `launch=picker-manual` — preflight failed: workspace opens INTERACTIVE `claude-picker "/pickup"` + notify asks user to complete it; NEVER bare `claude`) · `3` manual fallback (not-in-cmux / hop limit / quota) · `1` refused (dirty tree / missing bundle / missing `.active-feature` / unsafe explicit bundle path). Every non-spawn path prints the manual resume instructions; exit-3 paths with cmux reachable also `cmux notify` the reason.
- Preconditions, in order (worktree root = `git rev-parse --show-toplevel`; feature dir = `.active-feature` at that root): (1) `git status --porcelain` empty else exit 1; (2) bundle exists else exit 1; (3) `CMUX_WORKSPACE_ID` set AND `cmux ping`=PONG else exit 3; (4) hops < `SUPERPOWERS_CMUX_MAX_HOPS` (default 3) else exit 3; (5) quota fail-open — below threshold exit 3; cupace absent/error/timeout → proceed, log `quota=unchecked`.
- Forwarding metadata (inherited env, exported by extended picker at the forwarding session's launch): `CLAUDE_CODE_PICKER_VERSION` → successor version; `CLAUDE_CODE_PICKER_ARGS` (shell-quoted passthrough args) → appended to successor launch; `CLAUDE_CODE_PICKER_LABEL` → incremented; `CLAUDE_CODE_ENABLE_TELEMETRY` (`1`=on) → successor telemetry. Hop-recursion guard: strip any trailing positional beginning `/pickup` from `_ARGS` before appending the fresh prompt.
- Label increment: empty → empty; ends `-Session-<n>` → `-Session-<n+1>`; other non-empty → `<label>-Session-2`. Result passes the picker's attr sanitization.
- Successor launch command: `claude-picker <non-interactive flags: version, telemetry on|off, label> <forwarded args> "/pickup"` (or `"/pickup <path>"` iff explicit BUNDLE_PATH; default is NEVER interpolated). Explicit path must resolve under `~/.claude-codex-handoff`, no whitespace/quotes, else exit 1. Bundle default: latest under `~/.claude-codex-handoff`.
- Spawn sequence: `cmux new-workspace --name "SDD resume: <feature>" --cwd <worktree-root> --command '<successor launch command>' --focus false` → increment `<feature-dir>/reports/.handoff-hops` → `cmux notify --title "SDD handoff" --body "Hop N/<max> — successor spawned in <workspace-ref>"` → append spawn-log line → print workspace ref, exit 0; controller STOPs.
- State files (both **tracked**, committed by successor's normal step-2 commit; next hop's clean-tree check self-corrects): `reports/.handoff-hops` (counter); `reports/handoff-spawn.log` (one line/spawn: ISO-8601, hop, workspace ref, bundle path, quota status, launch mode `auto|picker-manual`). Separate from `context-observations.log` — do not touch its format.
- claude-picker extension (telemetry-exp `launchers/claude-picker`): export `CLAUDE_CODE_PICKER_VERSION` + `CLAUDE_CODE_PICKER_ARGS` (faithful `"$@"`; stripping is the spawn script's job) + `_LABEL` on EVERY launch path (telemetry on/off/no-repo); add flag-gated non-interactive mode (version, label, telemetry on/off up front; Docker down → telemetry off, no prompt; invalid version → non-zero exit); interactive path unchanged when flags absent; test via existing `CLAUDE_PICKER_TEST_MODE` sourcing seam.
- Vendored skills: `cmux-custom-skills/skills/{cmux,cmux-workspace,cmux-markdown,cmux-diagnostics}/` — pristine upstream copies (NEVER locally edited) from `manaflow-ai/cmux` at a pinned SHA in `VENDOR.md`. Symlinks: `~/.claude/skills/<name> → <repo>/skills/<name>` (no command stubs). Repo also gets `sync-cmux-skills.sh` + `verify-install.sh`.
- `sdd-pre-dispatch-hook.sh`: **NO change**, no baseline re-capture (block message already points to the protocol doc, line 840 — verified). SDD SKILL.md body: **NO change** (word ceiling). Superpowers `verify-symlink-install.sh`: **NO change** (cmux checks live in the new repo).
- Protocol doc `references/context-handoff-protocol.md`: steps 1–3 unchanged; steps 4–5 rewritten to: run the spawn script; exit 0 → report workspace ref + launch mode; exit 3 → relay printed instructions; exit 1 → fix precondition, re-run; then STOP. Closing note: same script serves early handoff at the soft nudge.
- Tests: superpowers unit = `tests/unit/test_spawn_handoff.py` (stub `cmux` + stub `claude-picker` + stub `claude-usage-pace` on PATH recording argv; case matrix in source §7 incl. all three label cases + both launch modes); e2e gains Step 14 (banner 14→15); telemetry-exp picker tests per that repo's conventions; `validate-all-skills.py` unaffected (vendored skills live outside the fork).

## Open Decisions

| # | Decision | Options | Resolution Required By |
|---|----------|---------|----------------------|
| 1 | Quota check parameters: JSON field for remaining 5h-window capacity, refuse threshold, env var name (proposed `SUPERPOWERS_CMUX_QUOTA_MIN_PCT`), timeout for the nested call | Inspect live `claude-usage-pace --json` output | Plan writer, before Component B tasks |
| 2 | Cross-repo execution split | (i) one superpowers SDD plan with cross-repo tasks + accepted-deviation note for the git-reality check; (ii) telemetry-exp and/or cmux-custom-skills as small separate plans, superpowers plan asserts their contracts as prerequisites. Either way: repo-2/3 deliverables land before dependent superpowers tasks | Plan writer |
| 3 | Exact claude-picker non-interactive flag names | Follow telemetry-exp repo conventions | Plan writer, with repo-3 work |

## Decision Summary

| # | Decision | Chosen |
|---|----------|--------|
| 1 | Autonomy level | Fully automatic (successor launches and `/pickup` submits unattended) |
| 2 | Spawn logic placement | Deterministic script invoked by protocol step 4 |
| 3 | Skill install mechanism | Vendored at pinned SHA + per-skill symlink |
| 4 | Skill subset | 4: cmux, cmux-workspace, cmux-markdown, cmux-diagnostics |
| 5 | Launch mechanics | `new-workspace --command` (no typed keystrokes) |
| 6 | Runaway guard | Hop counter file + `SUPERPOWERS_CMUX_MAX_HOPS` default 3 |
| 7 | Quota guard | Minimal fail-open cupace precondition |
| 8 | Spawn event log | Separate `reports/handoff-spawn.log` |
| 9 | Vendored-file policy | Pristine; fork guidance goes in superpowers CLAUDE.md only |
| 10 | Regression-suite treatment | Vendored skills outside the fork; new repo's `verify-install.sh` checks links |
| 11 | Skills home | Dedicated sibling repo `~/projects/claude-custom/cmux-custom-skills` |
| 12 | Successor launch command | claude-picker, forwarding version + args + telemetry label |
| 13 | Forwarding metadata channel | Picker-exported `CLAUDE_CODE_PICKER_*` env (passes subprocess filter) |
| 14 | Missing-metadata behavior | Interactive picker in spawned workspace, attended (`launch=picker-manual`) |
| 15 | Script generality | Layered single script; extraction-ready `spawn_claude_workspace()` core |

## Component Specifications

**A — cmux-custom-skills repo**: new git repo; `sync-cmux-skills.sh` takes an upstream ref (default `main`), sparse-clones `manaflow-ai/cmux`, replaces the 4 vendored dirs wholesale, rewrites VENDOR.md with resolved SHA, prints diff summary; never merges. `verify-install.sh` asserts the 4 symlinks resolve into the repo + VENDOR.md SHA present.
**B — Spawn script**: success path = preconditions 1–5 → compose successor launch (§Contract Facts) → spawn argv → increment `.handoff-hops` → notify → append spawn-log line → print workspace ref → exit 0; controller STOPs. **Plan ordering**: vendor A AND land the repo-3 picker extension first; verify the cmux CLI surface against vendored docs or live `cmux --help` BEFORE freezing B's exact-argv unit assertions. Re-expand the post-merge live-smoke procedure from source §7.
**Docs**: superpowers CLAUDE.md new "cmux Integration" section (`SUPERPOWERS_CMUX_MAX_HOPS` joins Hook Development Gotchas env-var list; cross-repo pointers); customization-manifest inventory entries; BACKLOG row closing N43(D).

## Acceptance Criteria

- [ ] 4 cmux skills auto-list in a fresh Claude session; `cmux-custom-skills/verify-install.sh` passes
- [ ] `--dry-run` in a real picker-launched cmux SDD session shows same version, forwarded args, correctly incremented label
- [ ] One real spawn: workspace opens, picker launches non-interactively, `/pickup` ingests, SDD resumes at first unchecked task
- [ ] Metadata-absent session degrades to `launch=picker-manual` (interactive picker + notification), never bare `claude`
- [ ] Non-cmux terminal: exit 3 + manual instructions (parity with today)
- [ ] Hop limit: attempt max+1 (4th, default max 3) falls back to manual with notification
- [ ] All suites green: superpowers unit/regression/installation/e2e (15 steps), telemetry-exp picker tests, cmux-custom-skills verify-install
- [ ] CLAUDE.md, customization manifest, BACKLOG updated; hook baseline untouched
