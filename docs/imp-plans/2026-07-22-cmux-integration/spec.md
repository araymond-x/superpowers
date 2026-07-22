# cmux Integration — Design Spec

> **Feature:** `cmux-integration`
> **Status:** design, pending review
> **Date:** 2026-07-22
> **BACKLOG:** closes N43 component **(D)** (cmux auto-spawn of the next session); component A of this spec is net-new (no prior BACKLOG row)
> **Archetype:** Extension — vendors external skills alongside the fork and extends the N43 context-handoff protocol. The only replaced content is the tail of `references/context-handoff-protocol.md` (steps 4–5).

---

## 1. Problem

Two gaps keep the fork's SDD pipeline from using cmux, the terminal environment every session already runs in.

**The handoff seam is manual.** N43 shipped the context-pressure gate: at the HARD block the controller commits, builds an N39 `/handoff` bundle, and STOPs — then the *user* must start a fresh session from the worktree and run `/pickup`. The N43 BACKLOG row anticipated the fix and deferred it as component (D): "cmux auto-spawn of the next session … unattended self-spawn carries runaway + quota-burn risk → needs safeguards." The live 2026-07-15 block (~757k tokens) proved the gate; the restart friction remains.

**Agents have cmux plumbing but no cmux knowledge.** The cmux Claude wrapper is active (session hooks, Feed bridge, notifications), and every session inherits `CMUX_WORKSPACE_ID` / `CMUX_SURFACE_ID` / a reachable socket. But no cmux skills are installed in `~/.claude/skills`, so no agent knows the CLI surface exists.

This feature closes both: vendor the official cmux agent skills (A), and make the blocked SDD controller spawn its own successor (B).

## 2. Goals & Non-Goals

### In scope
- **A — Vendored cmux skills.** Vendor 4 official skills (`cmux`, `cmux-workspace`, `cmux-markdown`, `cmux-diagnostics`) from `manaflow-ai/cmux` at a pinned SHA into `external-skills/`; symlink each into `~/.claude/skills/`; a re-vendor sync script; installation-test coverage.
- **B — Auto-spawn handoff.** A deterministic `spawn-handoff-session.sh` in the SDD skill's `scripts/`, invoked by the rewritten protocol step 4. **Fully automatic** (user decision): the successor launches and `/pickup` submits without human confirmation. Safeguards: fail-closed preconditions, hop limit, minimal fail-open cupace quota check, `cmux notify` on every hop, manual-instructions fallback on every non-spawn path.

### Out of scope — do not build
- SDD sidebar telemetry (`set-progress`/`set-status` from controller or hooks) → future feature.
- Live artifact panels (`cmux markdown open` for plan/deviations, `cmux diff` at finish) → future feature.
- Worktree-workspace customization (one-click worktree agent buttons) → future feature.
- Fleet orchestration (parallel Claude sessions as cmux workspaces) → needs its own design; bypasses Agent-tool hook enforcement.
- The other 3 cmux skills (`cmux-browser`, `cmux-settings`, `cmux-customization`) → install later if needed.
- Codex-side symlinks (`~/.agents/skills`) → later.
- **N43 component (C)** — full pace-aware pause/resume via `cupace` (the user's `claude-usage-pace` personal CLI; "cupace" throughout this spec) with its sleep-until-reset remedy → its own spec. This feature takes only a minimal spawn-time quota precondition.
- **B10** — pressure-conditional context-summary gate → separate fast-follow, unchanged by this feature.
- Any change to the context gate's thresholds, tiers, probe, or observation-log format.
- Auto-spawn from `writing-plans`/`brainstorming` sessions → later; this feature targets the SDD controller seam only.

## 3. Affected Code

| Path | Change |
|---|---|
| `external-skills/{cmux,cmux-workspace,cmux-markdown,cmux-diagnostics}/` | **NEW** — vendored skill dirs (SKILL.md + references/ + scripts/), pristine copies |
| `external-skills/VENDOR.md` | **NEW** — upstream repo, pinned SHA, vendor date, per-skill file inventory |
| `external-skills/sync-cmux-skills.sh` | **NEW** — re-vendor from upstream at a given ref; updates VENDOR.md |
| `~/.claude/skills/{cmux,cmux-workspace,cmux-markdown,cmux-diagnostics}` | **NEW symlinks** (install step, documented in CLAUDE.md; outside the repo) |
| `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` | **NEW** — the auto-spawn tool (§5) |
| `skills/subagent-driven-development/references/context-handoff-protocol.md` | Rewrite steps 4–5: run the spawn script; manual path becomes the documented fallback; note the script also serves the soft-nudge early handoff |
| `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` | **No change** (verified at spec review: the HARD-block message already ends with a pointer to the protocol doc, sdd-pre-dispatch-hook.sh:840). No baseline re-capture |
| `tests/unit/test_spawn_handoff.py` | **NEW** — stub-cmux unit suite (§7) |
| `tests/integration/sdd-e2e-test.sh` | **NEW Step 14** (banner 14→15) — end-to-end spawn with stub cmux |
| `tests/ARaymond-installation/verify-symlink-install.sh` | Add: 4 symlink checks, `external-skills/` presence, VENDOR.md SHA recorded |
| `CLAUDE.md`, `docs/ARaymond-customization-manifest.md`, `docs/process-improvement-findings/BACKLOG.md` | New "cmux Integration" section; inventory entries; close N43(D) lineage with a new row |

`skills/subagent-driven-development/SKILL.md` body: **no change** (at its word ceiling; the protocol reference doc is the integration point, already reached from the hook's block message).

## 4. Key Design Decisions

| # | Decision | Options considered | Chosen | Why |
|---|----------|--------------------|--------|-----|
| 1 | Autonomy level | command-only · staged spawn (prefill, user submits) · fully automatic | **Fully automatic** | User decision. The SDD run continues unattended across the session boundary; safeguards (#6, #7, notify) carry the risk the BACKLOG named. |
| 2 | Spawn logic placement | in the hook · prose in the protocol doc · deterministic script | **Deterministic script** | The hook fires *before* the commit and bundle exist — wrong seam. Prose executed by a context-exhausted controller is exactly what N43 distrusts. A script is testable and owns the safeguards. |
| 3 | Skill install mechanism | `npx skills add` (upstream-managed) · vendored + symlink | **Vendored at pinned SHA + symlink** | Matches the established `big-*`/elements-of-style pattern; version-controls what agents ingest; re-vendor is explicit and reviewable. |
| 4 | Skill subset | all 7 · 4 (core, workspace, markdown, diagnostics) | **4** | Each skill adds per-session context weight. Browser duplicates claude-in-chrome; settings/customization are user-driven tasks, installable later. |
| 5 | Launch mechanics | spawn terminal + typed keystrokes (`cmux send`) · `new-workspace --command 'claude "/pickup"'` | **`--command` launch** | No TUI keystroke-timing fragility. The new terminal goes through the cmux Claude wrapper shim, so session restore and Feed integration engage automatically. |
| 6 | Runaway guard | none · hop counter | **Hop counter file + `SUPERPOWERS_CMUX_MAX_HOPS` (default 3)** | Answers the BACKLOG's runaway risk. Exceeding the limit falls back to manual instructions — never a dead end. |
| 7 | Quota guard | none · full component C · minimal fail-open cupace check | **Minimal fail-open check** | User decision. Spawning into a nearly-exhausted 5h window burns the remainder unattended. Soft dependency: `claude-usage-pace` absent or erroring → proceed. |
| 8 | Spawn event log | append to `reports/context-observations.log` · separate file | **Separate `reports/handoff-spawn.log`** | The observations log format is pinned; threshold tuning consumes `source=probe` rows only. Spawn events get their own file and format. |
| 9 | Vendored-file policy | allow local edits · pristine | **Pristine** | Re-vendoring must never conflict. Fork-specific cmux guidance lives in CLAUDE.md, not in vendored files. |
| 10 | Regression-suite treatment | include `external-skills/` in `validate-all-skills.py` · exclude | **Exclude** | Vendored skills follow upstream's conventions, not the fork's. The installation test checks presence and link integrity instead. |

## 5. Component B — `spawn-handoff-session.sh`

### 5.1 Interface

```
spawn-handoff-session.sh [BUNDLE_PATH] [--dry-run]
```

- `BUNDLE_PATH` (optional): explicit handoff bundle. Default: latest bundle under `~/.claude-codex-handoff`. If supplied, it must resolve under `~/.claude-codex-handoff` and contain no whitespace or quote characters (it is interpolated into the launch command).
- `--dry-run`: run every precondition, print the composed `cmux` commands, spawn nothing. Used by tests and the post-merge live smoke.

Env: `SUPERPOWERS_CMUX_MAX_HOPS` (default `3`); quota knob per §5.3. Path resolution: worktree root = `git rev-parse --show-toplevel`; feature dir = `.active-feature` at that root (missing → refusal; SDD sessions always have one).

### 5.2 Preconditions (checked in order; fail-closed)

1. **Clean tree** — `git status --porcelain` empty. The script *verifies* protocol step 2 rather than trusting a context-exhausted controller. Dirty → **refuse (exit 1)**.
2. **Bundle exists** — default-latest or explicit path present. Missing → **refuse (exit 1)**.
3. **cmux reachable** — `CMUX_WORKSPACE_ID` set AND `cmux ping` returns PONG. Otherwise → **manual fallback (exit 3)**; not an error — non-cmux terminals keep today's behavior.
4. **Hop limit** — read `<feature-dir>/reports/.handoff-hops`; count ≥ `SUPERPOWERS_CMUX_MAX_HOPS` → **manual fallback (exit 3)** with a "hop limit reached" notice.
5. **Quota (fail-open)** — run `~/.claude/bin/claude-usage-pace --json`; if the remaining 5h-window capacity is below threshold → **manual fallback (exit 3)** with a quota notice. Tool absent, erroring, or timing out → proceed, and record `quota=unchecked` in the spawn log.

### 5.3 OPEN DECISION — quota field + threshold

The plan writer must inspect live `claude-usage-pace --json` output and pin: (a) the JSON field expressing remaining 5h-window capacity, (b) the refuse threshold, (c) the env var name (proposed: `SUPERPOWERS_CMUX_QUOTA_MIN_PCT`), (d) a timeout for the nested headless call. Until pinned, the precondition is designed but not parameterized.

### 5.4 Spawn sequence (success path)

1. `cmux new-workspace --name "SDD resume: <feature>" --cwd <worktree-root> --command 'claude "/pickup"' --focus false` — never steal focus.
2. Increment `<feature-dir>/reports/.handoff-hops`.
3. `cmux notify --title "SDD handoff" --body "Hop N/<max> — successor spawned in <workspace-ref>"`.
4. Append one line to `<feature-dir>/reports/handoff-spawn.log`: ISO-8601 timestamp, hop number, workspace ref, bundle path, quota status.
5. Print the workspace ref and exit 0. The controller reports it and **STOPs** (protocol step 5 unchanged).

**Git treatment of spawn artifacts:** `.handoff-hops` and `handoff-spawn.log` are **tracked** — the `reports/` convention (`.dispatch-log` and `context-observations.log` are committed; only root-level workspace state like `.active-feature` is gitignored). The dying session necessarily leaves them uncommitted (they are written *after* the clean-tree check); the successor's normal step-2 commit folds them in, and if it doesn't, the next hop's clean-tree refusal self-corrects.

When `BUNDLE_PATH` was supplied, the launch prompt becomes `claude "/pickup <path>"`; the default path avoids interpolation entirely (`/pickup` resolves latest itself).

### 5.5 Exit codes and fallback behavior

| Exit | Meaning | Behavior |
|---|---|---|
| 0 | Spawned | Workspace ref printed; controller STOPs |
| 3 | Manual fallback (not-in-cmux · hop limit · quota) | Prints the manual resume instructions (today's protocol step 4 text) for the controller to relay; if cmux is reachable, also `cmux notify` explaining why manual intervention is needed |
| 1 | Refused (dirty tree · missing bundle · missing `.active-feature`) | Prints the failing precondition; controller fixes and re-runs |

Every non-spawn path prints the manual instructions — the protocol never dead-ends.

### 5.6 Protocol doc rewrite

`references/context-handoff-protocol.md` steps 4–5 become: *"4. Run `~/.claude/skills/superpowers/subagent-driven-development/scripts/spawn-handoff-session.sh`. Exit 0: report the workspace ref. Exit 3: relay the printed manual instructions. Exit 1: fix the printed precondition and re-run. 5. STOP — do not dispatch the next task in this session."* A closing note documents the soft-nudge use: handing off early is preferred, and the same script serves it. Steps 1–3 are unchanged.

## 6. Component A — Vendored cmux skills

- **Layout:** `external-skills/<skill-name>/` mirrors upstream's `skills/<skill-name>/` exactly (SKILL.md, references/, scripts/, templates/ where present).
- **VENDOR.md:** upstream repo URL, pinned commit SHA, vendor date, the 4 skill names. Updated only by the sync script.
- **`sync-cmux-skills.sh`:** takes an upstream ref (default `main`); sparse-clones `manaflow-ai/cmux` at that ref into a temp dir; replaces the 4 vendored dirs wholesale; rewrites VENDOR.md with the resolved SHA; prints a diff summary. Never merges — pristine policy makes replacement safe.
- **Install:** `ln -s <repo>/external-skills/<name> ~/.claude/skills/<name>` for each of the 4 — the `big-*` pattern. Flat personal skills appear in the `/skills` picker natively; no command stubs.
- **No fork edits to vendored files.** Fork-specific cmux guidance (e.g., "prefer `--focus false`", spawn-script pointers) lives in CLAUDE.md's new section.

## 7. Testing

**Plan ordering note:** vendor component A first and verify the cmux CLI surface (`new-workspace --focus/--command`, `notify`, `ping`) against the vendored skill docs or live `cmux --help` *before* freezing component B's composed argv — otherwise the exact-argv unit assertions risk a rework loop.

- **Unit — `tests/unit/test_spawn_handoff.py`** (pytest, stub `cmux` on PATH recording argv; stub `claude-usage-pace`): not-in-cmux → exit 3 + instructions; ping failure → exit 3; dirty tree → exit 1; missing bundle → exit 1; missing `.active-feature` → exit 1; hop limit reached → exit 3 + notice; quota below threshold → exit 3 + notice; quota tool absent → spawn proceeds with `quota=unchecked`; success → exact `new-workspace`/`notify` argv asserted, `.handoff-hops` incremented, spawn-log line appended; `--dry-run` → all preconditions evaluated, zero spawn argv recorded; unsafe explicit bundle path → exit 1.
- **Installation — `verify-symlink-install.sh`:** 4 symlinks resolve into `external-skills/`; VENDOR.md exists with a SHA; vendored SKILL.md files present.
- **e2e — `sdd-e2e-test.sh` Step 14** (banner 14→15): fixture repo + fixture bundle + stub cmux; drive the script end-to-end; assert composed spawn command, notify, hop counter.
- **Post-merge live smoke** (mirrors N43's discipline — the e2e proves the checkout path; the installed skill path resolves to the main checkout): in a real cmux session, `--dry-run` first, then one real spawn against a scratch bundle; confirm the workspace opens, `claude` launches through the wrapper, `/pickup` ingests; close the workspace. The first genuine HARD-block hop is the true acceptance test.
- **Hook baseline:** re-capture only if the block message is edited (§3).

## 8. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Runaway spawn chain (bad handoff → successor blocks → spawns again) | Hop counter, default max 3, manual fallback beyond; `cmux notify` on every hop |
| Unattended quota burn | Fail-open cupace precondition (§5.2.5); hop limit bounds total exposure |
| Bad handoff propagates without review | Same `/handoff` bundle flow as the manual path — no new bundle format; `/pickup` + SDD session-recovery re-validate against committed state (plan checkboxes, manifest, reports) |
| Focus stealing during unattended operation | `--focus false` on every spawn; notification instead of focus |
| Vendored skills drift from upstream cmux CLI | Pinned SHA + explicit re-vendor script; `cmux-diagnostics` included for self-checks |
| Command injection via bundle path | Default path never interpolates; explicit path must resolve under `~/.claude-codex-handoff` with no whitespace/quotes |
| Worktree development edits the live skill path | The spawn script is not a hook (no baseline), but live sessions resolve `~/.claude/skills/superpowers/...` to the main checkout — develop in a worktree, live-smoke after merge |

## 9. Acceptance Criteria

- [ ] The 4 cmux skills auto-list in a fresh Claude session's available-skills.
- [ ] `spawn-handoff-session.sh --dry-run` passes all preconditions in a real cmux SDD session.
- [ ] One real spawn: successor workspace opens, `claude` launches via the wrapper, `/pickup` ingests the bundle, SDD resumes at the first unchecked task.
- [ ] Non-cmux terminal: script exits 3 and prints the manual instructions (behavior parity with today).
- [ ] Hop limit: spawn attempt max+1 (the 4th, with the default max of 3) falls back to manual with a notification.
- [ ] All suites green: unit, regression (`validate-all-skills.py` unchanged counts), installation, e2e (15 steps).
- [ ] CLAUDE.md, customization manifest, and BACKLOG updated; hook baseline re-captured only if the hook changed.
