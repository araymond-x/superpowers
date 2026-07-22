# cmux Integration — Distilled Implementation Spec
> **Source**: `docs/imp-plans/2026-07-22-cmux-integration/spec.md` (rev 4, 22 decisions) · **Distilled**: 2026-07-22 · **For**: plan writer and implementation agents ONLY. Full rationale in source.

## Out of scope — do not build

- SDD sidebar telemetry (`set-progress`/`set-status` from controller or hooks) → future feature
- Live artifact panels (`cmux markdown open`, `cmux diff` at finish) → future feature
- Worktree-workspace customization (one-click worktree agent buttons) → future feature
- Fleet orchestration (parallel Claude sessions as cmux workspaces) → own design later
- The other 3 cmux skills (`cmux-browser`, `cmux-settings`, `cmux-customization`) → install later if needed
- Codex-side symlinks (`~/.agents/skills`) and codex-picker parity → later
- N43 component (C) full pace-aware pause/resume via cupace (`claude-usage-pace`) → its own spec; ONLY the §Quota spawn-time session-window check here; weekly windows (`week_all`, `week_premium`) NOT consulted
- B10 pressure-conditional context-summary gate → separate fast-follow
- Any change to context-gate thresholds, tiers, probe, or observation-log format
- Auto-spawn from `writing-plans`/`brainstorming` sessions → later; SDD controller seam only (two ready seams: layered spawn core + parameterized bundle validation)
- Spawning review-type bundles (`/handoff-review … plan|code`; toolkit `bundle_type=review`) → arrives with the brainstorming/writing-plans auto-spawn work; §validation parameterization deliberately sufficient
- Codex auto-review dispatch (`/handoff-review auto-cdx`) integration → excluded: currently non-functional; revisit when fixed
- Extracting the generic spawn core to `skills/scripts/` → when a second consumer arrives
- User-authored custom cmux skills in the new repo → later (layout leaves room; only vendored skills ship now)
- Successor pickup ACK/liveness confirmation beyond the spawn outcome record → later if multi-hop telemetry shows a need

## Contract Facts

**Three ordered repo-local deliverables (Decision 19):** (1) telemetry-exp picker contract lands FIRST; (2) NEW repo `~/projects/claude-custom/cmux-custom-skills` second; (3) superpowers SDD plan last — opens with Task-0-style prerequisite assertions (`claude-picker --handoff-contract` prints exactly `1`; 4 skill symlinks resolve; `cmux ping`) and consumes repos 1–2 without modifying them.

- Script: `skills/subagent-driven-development/scripts/spawn-handoff-session.sh BUNDLE_ID [--dry-run]`. `BUNDLE_ID` REQUIRED (captured from `/handoff` output in protocol step 3). `--dry-run` evaluates preconditions + preflight, prints composed commands, spawns nothing, increments nothing. Internal layering: generic `spawn_claude_workspace()` core (cmux detection, spawn, notify; params: cwd, launch command, workspace name, notify text) marked extraction-ready + SDD policy shell.
- Bundle validation (Decisions 16+22): `BUNDLE_ID` matches `^[A-Za-z0-9_.-]+$` AND resolves to a dir under `~/.claude-codex-handoff/bundles/` AND manifest has expected `bundle_type` + entry skill + workspace repo matching current worktree root (pickup-guard repo-match rule). Implemented as a PARAMETERIZED function (expected type + entry skill are inputs); the SDD shell pins `work` + `superpowers:subagent-driven-development`. Any failure → exit 1. The pickup prompt ALWAYS carries the validated id: `"/pickup <BUNDLE_ID>"` — no latest-resolution anywhere.
- Exit codes: `0` spawned (`launch=auto` — preflight passed; OR `launch=picker-manual` — preflight failed: workspace opens INTERACTIVE `claude-picker "/pickup <BUNDLE_ID>"` + notify; NEVER bare `claude`) · `3` manual fallback (not-in-cmux / hop limit / quota low / spawn-failed after reservation) · `1` refused (dirty tree / bundle validation / missing `.active-feature`). Every non-spawn path prints the manual resume instructions; exit-3 with cmux reachable also notifies.
- Preconditions in order (worktree root = `git rev-parse --show-toplevel`; feature dir = `.active-feature`): (1) clean tree else exit 1; (2) bundle valid else exit 1; (3) `CMUX_WORKSPACE_ID` + `cmux ping`=PONG else exit 3; (4) hops < `SUPERPOWERS_CMUX_MAX_HOPS` (default 3) else exit 3; (5) quota per below.
- Quota check (pinned; schema verified live 2026-07-22): `~/.claude/bin/claude-usage-pace --json --no-log`, 60s timeout. Field `windows[key=="session"].remaining_pct`. Refuse (exit 3, `quota=low:<pct>`) when < `SUPERPOWERS_CMUX_QUOTA_MIN_PCT` (default 15). At/above → proceed `quota=ok:<pct>`. Tool absent / non-zero exit / timeout / unparseable / window or field missing/non-numeric → proceed `quota=unchecked` (fail-open).
- Forwarding metadata (inherited env): `CLAUDE_CODE_PICKER_VERSION` → `--pick-version`; `CLAUDE_CODE_PICKER_ARGS` = **v1 codec** `v1:` + base64(JSON array of argv strings), decoded WITHOUT eval (python3 stdlib), absent ⇒ empty argv; `CLAUDE_CODE_PICKER_LABEL` → incremented; `CLAUDE_CODE_ENABLE_TELEMETRY` `1`=on, absent ⇒ off (never blocks auto). Hop-recursion guard: after decoding, strip any trailing positional beginning `/pickup` from the argv array.
- Label rule (Decision 18 — spawn script owns final label): strip existing trailing `-Session-<n>` → sanitize base with picker's attr charset rule → suffix = `-Session-<n+1>` (if counter stripped) else `-Session-2` → truncate base to `255 − len(suffix)` → concat. Empty or empty-after-sanitize base → no label. Result is picker-sanitizer-stable.
- Successor launch command: `claude-picker --non-interactive --pick-version <v> --telemetry <on|off> [--session-label <label>] <decoded forwarded args> "/pickup <BUNDLE_ID>"`. Compose-side quoting REQUIRED: every interpolated element (each decoded arg, version, label) is shlex-style re-quoted when building the `--command` string (the codec covers decode; this covers re-embedding — naive space-join breaks `--append-system-prompt-file <path with space>` on the auto path).
- Auto-mode preflight (`launch=auto` iff ALL): metadata usable (VERSION non-empty; ARGS v1-decodes or absent; LABEL may be empty; ENABLE_TELEMETRY absent ⇒ off) AND version binary exists at `~/.local/share/claude/versions/<version>` AND `claude-picker` on PATH AND `claude-picker --handoff-contract` prints exactly `1` (a future v2 must FAIL preflight, not pass). Fail → `launch=picker-manual`. Residual runtime guard embedded in auto command: `<picker cmd> || { <append runtime-picker-failure line>; claude-picker "/pickup <BUNDLE_ID>"; }`.
- Spawn sequence (Decision 21 — reserve BEFORE spawn): (1) increment `reports/.handoff-hops` + append `intent` line (spawn id = uuid) to `reports/handoff-spawn.log`; (2) `cmux new-workspace --name "SDD resume: <feature>" --cwd <worktree-root> --command '<successor launch command>' --focus false` — failure → append `outcome=spawn-failed`, hop stays consumed, exit 3; (3) append `outcome` line (workspace ref, launch mode, bundle id, quota status) + `cmux notify --title "SDD handoff" --body "Hop N/<max> — successor spawned in <workspace-ref>"` — failures here non-retryable: stderr warn, still exit 0; (4) print workspace ref, exit 0; controller STOPs.
- Log format (`handoff-spawn.log`): ISO-8601, spawn id, record type `intent|outcome|runtime-picker-failure`, hop; outcomes add workspace ref, launch mode, bundle id, quota status. Both state files **tracked** (reports/ convention); successor's step-2 commit folds them in; next hop's clean-tree check self-corrects. Separate from `context-observations.log` — do not touch its format.
- Picker extension (telemetry-exp `launchers/claude-picker`): pinned flags `--non-interactive`, `--pick-version <v>`, `--session-label <label>`, `--telemetry <on|off>`, `--handoff-contract` (prints `1`, exit 0). Exports `CLAUDE_CODE_PICKER_VERSION` + `_ARGS` (v1 codec, faithful; stripping is spawn script's job) + `_LABEL` on EVERY launch path (telemetry on/off/no-repo). Non-interactive: no `read` ever fires; Docker down → telemetry off; unknown version → non-zero exit. Interactive path unchanged when flags absent. Testability refactor REQUIRED: selection/telemetry/launch-composition become pure functions above the `CLAUDE_PICKER_TEST_MODE` seam + subprocess tests (stubbed read/exec/docker) assert exports at the exec boundary.
- Vendored skills: `cmux-custom-skills/skills/{cmux,cmux-workspace,cmux-markdown,cmux-diagnostics}/` — pristine upstream copies (NEVER locally edited) from `manaflow-ai/cmux` at a pinned SHA in `VENDOR.md`. Symlinks: `~/.claude/skills/<name> → <repo>/skills/<name>` (no command stubs). Repo also gets `sync-cmux-skills.sh` + `verify-install.sh`.
- `sdd-pre-dispatch-hook.sh`: **NO change**, no baseline re-capture (block message already points to the protocol doc, line 840 — verified). SDD SKILL.md body: **NO change** (word ceiling). Superpowers `verify-symlink-install.sh`: **NO change**.
- Protocol doc `references/context-handoff-protocol.md`: steps 1–2 unchanged; step 3 ends by capturing the bundle id from `/handoff` output; steps 4–5 → run spawn script WITH the id; exit 0 → report workspace ref + launch mode; exit 3 → relay printed instructions; exit 1 → fix precondition, re-run; STOP. Closing note: same script serves early handoff at the soft nudge.
- Env vars (join Hook Development Gotchas list): `SUPERPOWERS_CMUX_MAX_HOPS` (3), `SUPERPOWERS_CMUX_QUOTA_MIN_PCT` (15).
- Tests: repo-3 unit = `tests/unit/test_spawn_handoff.py` (stub `cmux` + stub `claude-picker` incl. `--handoff-contract` + stub `claude-usage-pace`, recording argv; case matrix in source §7 incl. bundle-validation failures, all quota classes, all label cases incl. 255 boundary, both launch modes, reservation ordering, strip guard, dry-run); e2e Step 14 (banner 14→15); repo-1 subprocess tests incl. v1-codec round-trip of spaces/quotes/backslashes/empty/option-values/`/pickup <arg>`/hostile input; `validate-all-skills.py` unaffected.

## Open Decisions
None — all resolved in rev 3 (quota parameters pinned; execution split chosen; picker flags pinned).

## Decision Summary

| # | Decision | Chosen |
|---|----------|--------|
| 1 | Autonomy level | Fully automatic (successor `/pickup <id>` submits unattended) |
| 2 | Spawn logic placement | Deterministic script invoked by protocol step 4 |
| 3 | Skill install mechanism | Vendored at pinned SHA + per-skill symlink |
| 4 | Skill subset | 4: cmux, cmux-workspace, cmux-markdown, cmux-diagnostics |
| 5 | Launch mechanics | `new-workspace --command` (no typed keystrokes) |
| 6 | Runaway guard | Hop counter file + `SUPERPOWERS_CMUX_MAX_HOPS` default 3 |
| 7 | Quota guard | Minimal session-window check, parameters pinned |
| 8 | Spawn event log | Separate `reports/handoff-spawn.log` |
| 9 | Vendored-file policy | Pristine; fork guidance goes in superpowers CLAUDE.md only |
| 10 | Regression-suite treatment | Vendored skills outside the fork; repo-2 `verify-install.sh` checks links |
| 11 | Skills home | Dedicated sibling repo `~/projects/claude-custom/cmux-custom-skills` |
| 12 | Successor launch command | claude-picker, forwarding version + args + telemetry label |
| 13 | Forwarding metadata channel | Picker-exported `CLAUDE_CODE_PICKER_*` env |
| 14 | Missing-metadata behavior | Interactive picker in spawned workspace, attended (`launch=picker-manual`) |
| 15 | Script generality | Layered single script; extraction-ready `spawn_claude_workspace()` core |
| 16 | Bundle resolution | Required explicit id + manifest validation; `/pickup <id>` everywhere |
| 17 | ARGS encoding | v1 codec: `v1:` + base64(JSON array of argv strings), no eval |
| 18 | Label boundary ownership | Spawn script emits final label; suffix space reserved before truncation |
| 19 | Cross-repo execution split | Ordered repo-local: telemetry-exp → cmux-custom-skills → superpowers |
| 20 | Picker non-interactive interface | Pinned: `--non-interactive`, `--pick-version`, `--session-label`, `--telemetry`, `--handoff-contract` |
| 21 | Spawn state ordering | Reservation (hop + intent record) before spawn; post-spawn failures non-retryable |
| 22 | Bundle-validation shape | Parameterized (expected type + entry skill as inputs); SDD shell pins `work` + SDD entry skill |

## Component Specifications

**Repo 1 — telemetry-exp**: claude-picker extension per Contract Facts (exports, non-interactive flags, contract probe, testability refactor). Own small plan in that repo.
**Repo 2 — cmux-custom-skills**: new git repo; `sync-cmux-skills.sh` takes an upstream ref (default `main`), sparse-clones `manaflow-ai/cmux`, replaces the 4 vendored dirs wholesale, rewrites VENDOR.md with resolved SHA, prints diff summary; never merges.
**Repo 3 — superpowers**: spawn script success path per Contract Facts; protocol rewrite; unit + e2e; docs (CLAUDE.md "cmux Integration" section, customization-manifest entries, BACKLOG row closing N43(D)). **Plan ordering**: repos 1–2 land first; verify the cmux CLI surface against vendored docs or live `cmux --help` BEFORE freezing exact-argv unit assertions. Re-expand the post-merge live-smoke procedure from source §7.

## Acceptance Criteria

- [ ] Repo 1: picker tests pass; `--handoff-contract` prints `1`; exports on every launch path
- [ ] Repo 2: 4 cmux skills auto-list in a fresh Claude session; `verify-install.sh` passes
- [ ] `<bundle-id> --dry-run` in a real picker-launched cmux SDD session: same version, decoded forwarded args (safely re-quoted), correctly incremented label
- [ ] One real spawn: workspace opens, picker non-interactive, `/pickup <bundle-id>` ingests, SDD resumes at first unchecked task
- [ ] Bundle validation: foreign-repo or non-SDD bundle id refused (exit 1) before any hop is consumed
- [ ] Metadata-absent session degrades to `launch=picker-manual` (interactive picker + notification), never bare `claude`
- [ ] Non-cmux terminal: exit 3 + manual instructions (parity with today)
- [ ] Hop limit: attempt max+1 (4th, default max 3) falls back to manual with notification
- [ ] All suites green: superpowers unit/regression/installation/e2e (15 steps), telemetry-exp picker tests, cmux-custom-skills verify-install
- [ ] CLAUDE.md, customization manifest, BACKLOG updated; hook baseline untouched
