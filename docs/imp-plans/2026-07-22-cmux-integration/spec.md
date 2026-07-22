# cmux Integration — Design Spec

> **Feature:** `cmux-integration`
> **Status:** design, pending review (rev 2 — user-review-gate amendments: skills repo relocation, claude-picker launch contract)
> **Date:** 2026-07-22
> **BACKLOG:** closes N43 component **(D)** (cmux auto-spawn of the next session); component A of this spec is net-new (no prior BACKLOG row)
> **Archetype:** Extension — vendors external skills into a new sibling repo and extends the N43 context-handoff protocol. The only replaced content is the tail of `references/context-handoff-protocol.md` (steps 4–5).

---

## 1. Problem

Two gaps keep the fork's SDD pipeline from using cmux, the terminal environment every session already runs in.

**The handoff seam is manual.** N43 shipped the context-pressure gate: at the HARD block the controller commits, builds an N39 `/handoff` bundle, and STOPs — then the *user* must start a fresh session from the worktree and run `/pickup`. The N43 BACKLOG row anticipated the fix and deferred it as component (D): "cmux auto-spawn of the next session … unattended self-spawn carries runaway + quota-burn risk → needs safeguards." The live 2026-07-15 block (~757k tokens) proved the gate; the restart friction remains. Sessions are launched through `claude-picker` (version selection + telemetry labeling), so a faithful auto-restart must preserve the forwarding session's version, launch arguments, and telemetry labeling — not just run bare `claude`.

**Agents have cmux plumbing but no cmux knowledge.** The cmux Claude wrapper is active (session hooks, Feed bridge, notifications), and every session inherits `CMUX_WORKSPACE_ID` / `CMUX_SURFACE_ID` / a reachable socket. But no cmux skills are installed in `~/.claude/skills`, so no agent knows the CLI surface exists.

This feature closes both: vendor the official cmux agent skills into a dedicated sibling repo (A), and make the blocked SDD controller spawn its own successor through claude-picker (B).

## 2. Goals & Non-Goals

### In scope — three repos, one feature
- **A — Vendored cmux skills** (NEW repo `~/projects/claude-custom/cmux-custom-skills`): 4 official skills (`cmux`, `cmux-workspace`, `cmux-markdown`, `cmux-diagnostics`) from `manaflow-ai/cmux` at a pinned SHA under `skills/`; VENDOR.md; re-vendor sync script; the repo's own install-verify script; symlinks from `~/.claude/skills/`.
- **B — Auto-spawn handoff** (superpowers repo): a deterministic, internally-layered `spawn-handoff-session.sh` invoked by the rewritten protocol step 4. **Fully automatic** (user decision): the successor launches through claude-picker non-interactively and `/pickup` submits without human confirmation. Safeguards: fail-closed preconditions, hop limit, minimal fail-open cupace quota check, `cmux notify` on every hop, graceful degradation paths (§5.5).
- **B-picker — claude-picker forwarding contract** (telemetry-exp repo): export forwarding metadata at every launch; add a non-interactive mode.

### Out of scope — do not build
- SDD sidebar telemetry (`set-progress`/`set-status` from controller or hooks) → future feature.
- Live artifact panels (`cmux markdown open` for plan/deviations, `cmux diff` at finish) → future feature.
- Worktree-workspace customization (one-click worktree agent buttons) → future feature.
- Fleet orchestration (parallel Claude sessions as cmux workspaces) → needs its own design; bypasses Agent-tool hook enforcement.
- The other 3 cmux skills (`cmux-browser`, `cmux-settings`, `cmux-customization`) → install later if needed.
- Codex-side symlinks (`~/.agents/skills`) and codex-picker parity → later.
- **N43 component (C)** — full pace-aware pause/resume via `cupace` (the user's `claude-usage-pace` personal CLI; "cupace" throughout this spec) with its sleep-until-reset remedy → its own spec. This feature takes only a minimal spawn-time quota precondition.
- **B10** — pressure-conditional context-summary gate → separate fast-follow.
- Any change to the context gate's thresholds, tiers, probe, or observation-log format.
- Auto-spawn from `writing-plans`/`brainstorming` sessions → later; this feature targets the SDD controller seam only (the layered spawn core is the future extraction seam).
- Extracting the generic spawn core to `skills/scripts/` → when a second consumer arrives.
- User-authored custom cmux skills in the new repo → later (the repo layout leaves room; only vendored skills ship now).

## 3. Affected Code

**Repo 1 — superpowers (primary; the SDD plan's home):**

| Path | Change |
|---|---|
| `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` | **NEW** — the auto-spawn tool (§5), layered: generic `spawn_claude_workspace()` core (detect, spawn, notify) marked extraction-ready + SDD policy shell |
| `skills/subagent-driven-development/references/context-handoff-protocol.md` | Rewrite steps 4–5: run the spawn script; degraded modes per §5.5; note the script also serves the soft-nudge early handoff |
| `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` | **No change** (verified at spec review: the HARD-block message already ends with a pointer to the protocol doc, sdd-pre-dispatch-hook.sh:840). No baseline re-capture |
| `tests/unit/test_spawn_handoff.py` | **NEW** — stub-cmux + stub-claude-picker unit suite (§7) |
| `tests/integration/sdd-e2e-test.sh` | **NEW Step 14** (banner 14→15) — end-to-end spawn with stubs |
| `CLAUDE.md`, `docs/ARaymond-customization-manifest.md`, `docs/process-improvement-findings/BACKLOG.md` | New "cmux Integration" section (`SUPERPOWERS_CMUX_MAX_HOPS` joins the Hook Development Gotchas env-var list; cross-repo pointers); inventory entries; close N43(D) lineage with a new row |

`skills/subagent-driven-development/SKILL.md` body: **no change** (word ceiling). `tests/ARaymond-installation/verify-symlink-install.sh`: **no change** — cmux symlink checks live in the new repo (repo decoupling; B does not depend on A).

**Repo 2 — cmux-custom-skills (NEW, `~/projects/claude-custom/cmux-custom-skills`):**

| Path | Change |
|---|---|
| `skills/{cmux,cmux-workspace,cmux-markdown,cmux-diagnostics}/` | **NEW** — pristine vendored copies (layout mirrors `big-build-patterns`: skills under `skills/`) |
| `VENDOR.md` | **NEW** — upstream repo URL, pinned SHA, vendor date, per-skill inventory |
| `sync-cmux-skills.sh` | **NEW** — re-vendor from upstream at a given ref; updates VENDOR.md |
| `verify-install.sh` | **NEW** — checks the 4 `~/.claude/skills/<name>` symlinks resolve here + VENDOR.md SHA recorded |
| `~/.claude/skills/{cmux,cmux-workspace,cmux-markdown,cmux-diagnostics}` | **NEW symlinks** → `<repo>/skills/<name>` (install step; no command stubs) |

**Repo 3 — telemetry-exp:**

| Path | Change |
|---|---|
| `launchers/claude-picker` | Export forwarding metadata on **every launch path** (telemetry on, telemetry off, and no-telemetry-repo alike): `CLAUDE_CODE_PICKER_VERSION` (selected version) and `CLAUDE_CODE_PICKER_ARGS` (shell-quoted passthrough args, exported faithfully — the spawn script owns prompt-positional stripping, §5.4a), alongside `CLAUDE_CODE_PICKER_LABEL` (currently telemetry-path-only; moves to every path). Add a **non-interactive mode** (flags; exact names follow that repo's conventions): version, label, telemetry on/off supplied up front; would-be prompts resolve deterministically (Docker down → telemetry off; invalid version → non-zero exit). Existing interactive behavior unchanged when flags absent. Tested via the existing `CLAUDE_PICKER_TEST_MODE` seam |

## 4. Key Design Decisions

| # | Decision | Options considered | Chosen | Why |
|---|----------|--------------------|--------|-----|
| 1 | Autonomy level | command-only · staged spawn (prefill, user submits) · fully automatic | **Fully automatic** | User decision. The SDD run continues unattended across the session boundary; safeguards (#6, #7, notify) carry the risk the BACKLOG named. |
| 2 | Spawn logic placement | in the hook · prose in the protocol doc · deterministic script | **Deterministic script** | The hook fires *before* the commit and bundle exist — wrong seam. Prose executed by a context-exhausted controller is exactly what N43 distrusts. A script is testable and owns the safeguards. |
| 3 | Skill install mechanism | `npx skills add` (upstream-managed) · vendored + symlink | **Vendored at pinned SHA + symlink** | Matches the established `big-*`/elements-of-style pattern; version-controls what agents ingest; re-vendor is explicit and reviewable. |
| 4 | Skill subset | all 7 · 4 (core, workspace, markdown, diagnostics) | **4** | Each skill adds per-session context weight. Browser duplicates claude-in-chrome; settings/customization are user-driven tasks, installable later. |
| 5 | Launch mechanics | spawn terminal + typed keystrokes (`cmux send`) · `new-workspace --command` | **`--command` launch** | No TUI keystroke-timing fragility. The new terminal goes through the cmux Claude wrapper shim, so session restore and Feed integration engage automatically. |
| 6 | Runaway guard | none · hop counter | **Hop counter file + `SUPERPOWERS_CMUX_MAX_HOPS` (default 3)** | Answers the BACKLOG's runaway risk. Exceeding the limit falls back to manual instructions — never a dead end. |
| 7 | Quota guard | none · full component C · minimal fail-open cupace check | **Minimal fail-open check** | User decision. Spawning into a nearly-exhausted 5h window burns the remainder unattended. Soft dependency: `claude-usage-pace` absent or erroring → proceed. |
| 8 | Spawn event log | append to `reports/context-observations.log` · separate file | **Separate `reports/handoff-spawn.log`** | The observations log format is pinned; threshold tuning consumes `source=probe` rows only. Spawn events get their own file and format. |
| 9 | Vendored-file policy | allow local edits · pristine | **Pristine** | Re-vendoring must never conflict. Fork-specific cmux guidance lives in CLAUDE.md, not in vendored files. |
| 10 | Regression-suite treatment | include vendored skills in `validate-all-skills.py` · exclude | **Exclude** (they live outside this repo entirely) | Vendored skills follow upstream's conventions, not the fork's. The new repo's `verify-install.sh` checks presence and link integrity. |
| 11 | Skills home | in-fork `external-skills/` · dedicated sibling repo | **`~/projects/claude-custom/cmux-custom-skills`** | User decision. Matches `big-build-patterns`/`telemetry-exp` (own repo, symlinked); keeps upstream-sync surface of the fork untouched; leaves room for future user-authored cmux skills. |
| 12 | Successor launch command | bare `claude "/pickup"` · claude-picker with forwarded context | **claude-picker, forwarding version + args + telemetry label** | User decision. Successor must be a faithful continuation: same Claude Code version, same launch args (e.g. `--append-system-prompt-file`), same telemetry labeling with an incremented session counter. |
| 13 | Forwarding metadata channel | parse process tree · picker exports `CLAUDE_CODE_PICKER_*` env | **Picker exports** | `CLAUDE_CODE_*` passes Claude Code's subprocess env filter (the picker already exports `_LABEL` for this reason); the spawn script reads inherited env — no fragile `ps` parsing. |
| 14 | Missing-metadata behavior | refuse · bare claude fallback · interactive picker in the spawned workspace | **Interactive picker, attended** | "Always claude-picker" (user requirement) even degraded: the workspace opens the picker with `/pickup` queued as its passthrough arg; a notification asks the user to complete the picker. |
| 15 | Script generality | split shared helper now · one script with layered interior | **Layered single script, extraction-ready core** | User decision (YAGNI). Generic `spawn_claude_workspace()` core + SDD policy shell in one file; extract to `skills/scripts/` when the second consumer (e.g. writing-plans handoff) arrives. |

## 5. Component B — `spawn-handoff-session.sh`

### 5.1 Interface

```
spawn-handoff-session.sh [BUNDLE_PATH] [--dry-run]
```

- `BUNDLE_PATH` (optional): explicit handoff bundle. Default: latest bundle under `~/.claude-codex-handoff`. If supplied, it must resolve under `~/.claude-codex-handoff` and contain no whitespace or quote characters (it is interpolated into the launch command).
- `--dry-run`: run every precondition, print the composed `cmux` + `claude-picker` commands, spawn nothing and increment nothing (`.handoff-hops` untouched). Used by tests and the post-merge live smoke.

Env: `SUPERPOWERS_CMUX_MAX_HOPS` (default `3`); quota knob per §5.3; forwarding metadata per §5.4a. Path resolution: worktree root = `git rev-parse --show-toplevel`; feature dir = `.active-feature` at that root (missing → refusal; SDD sessions always have one).

Internal layering (Decision 15): a generic `spawn_claude_workspace()` function (cmux detection, workspace spawn, notify; parameters: cwd, launch command, workspace name, notify text) marked extraction-ready, wrapped by the SDD policy shell (preconditions, hop counter, launch composition, exit-code contract).

### 5.2 Preconditions (checked in order; fail-closed)

1. **Clean tree** — `git status --porcelain` empty. The script *verifies* protocol step 2 rather than trusting a context-exhausted controller. Dirty → **refuse (exit 1)**.
2. **Bundle exists** — default-latest or explicit path present. Missing → **refuse (exit 1)**.
3. **cmux reachable** — `CMUX_WORKSPACE_ID` set AND `cmux ping` returns PONG. Otherwise → **manual fallback (exit 3)**; not an error — non-cmux terminals keep today's behavior.
4. **Hop limit** — read `<feature-dir>/reports/.handoff-hops`; count ≥ `SUPERPOWERS_CMUX_MAX_HOPS` → **manual fallback (exit 3)** with a "hop limit reached" notice.
5. **Quota (fail-open)** — run `~/.claude/bin/claude-usage-pace --json`; if the remaining 5h-window capacity is below threshold → **manual fallback (exit 3)** with a quota notice. Tool absent, erroring, or timing out → proceed, and record `quota=unchecked` in the spawn log.

### 5.3 OPEN DECISION — quota field + threshold

The plan writer must inspect live `claude-usage-pace --json` output and pin: (a) the JSON field expressing remaining 5h-window capacity, (b) the refuse threshold, (c) the env var name (proposed: `SUPERPOWERS_CMUX_QUOTA_MIN_PCT`), (d) a timeout for the nested headless call. Until pinned, the precondition is designed but not parameterized.

### 5.4 Launch composition and spawn sequence (success path)

**(a) Forwarding metadata**, read from the controller session's inherited env (exported by the extended claude-picker at the forwarding session's own launch):

| Var | Meaning | Used as |
|---|---|---|
| `CLAUDE_CODE_PICKER_VERSION` | Claude Code version the forwarding session runs | successor version-selection flag |
| `CLAUDE_CODE_PICKER_ARGS` | shell-quoted passthrough args of the forwarding launch | appended to successor launch |
| `CLAUDE_CODE_PICKER_LABEL` | telemetry label (may be empty) | incremented per (b) |
| `CLAUDE_CODE_ENABLE_TELEMETRY` | `1` when telemetry is on | successor telemetry on/off |

**Hop-recursion guard:** before composing, the script strips any trailing positional beginning `/pickup` from `CLAUDE_CODE_PICKER_ARGS`. A successor session's own forwarded args otherwise re-carry the previous hop's queued prompt — a duplicated `/pickup`, or a stale `/pickup <old-bundle>` ahead of the fresh one.

**(b) Label increment rule:** empty label → stays empty. Label ending `-Session-<n>` → counter incremented (`…-Session-3`). Any other non-empty label → `<label>-Session-2`. Result passes through the picker's own attr sanitization.

**(c) Successor launch command** (composed, then embedded in the workspace spawn):
`claude-picker <non-interactive flags: version, telemetry on|off, label> <forwarded args> "/pickup"` — or `"/pickup <path>"` when an explicit `BUNDLE_PATH` was supplied (default path is NEVER interpolated; `/pickup` resolves latest itself).

**Auto-mode preflight:** `launch=auto` is composed only when the metadata vars in (a) are usable (VERSION non-empty; ARGS/LABEL may be empty; `CLAUDE_CODE_ENABLE_TELEMETRY` absent ⇒ telemetry off — absence never blocks auto, since the picker sources it only on the telemetry-ON path) AND the forwarded version binary exists at `~/.local/share/claude/versions/<version>`. Preflight failure → compose `launch=picker-manual` instead (§5.5). As a residual guard against runtime picker failure inside the spawned workspace, the auto command embeds a fallback chain — `<non-interactive picker command> || claude-picker "/pickup"` — so an unexpected non-zero picker exit lands in the attended interactive picker, never a dead workspace (the spawn-log field stays `auto`; the notification text is unaffected).

**(d) Spawn sequence:**
1. `cmux new-workspace --name "SDD resume: <feature>" --cwd <worktree-root> --command '<successor launch command>' --focus false` — never steal focus.
2. Increment `<feature-dir>/reports/.handoff-hops`.
3. `cmux notify --title "SDD handoff" --body "Hop N/<max> — successor spawned in <workspace-ref>"`.
4. Append one line to `<feature-dir>/reports/handoff-spawn.log`: ISO-8601 timestamp, hop number, workspace ref, bundle path, quota status, launch mode (`auto` | `picker-manual`).
5. Print the workspace ref and exit 0. The controller reports it and **STOPs** (protocol step 5 unchanged).

**Git treatment of spawn artifacts:** `.handoff-hops` and `handoff-spawn.log` are **tracked** — the `reports/` convention (`.dispatch-log` and `context-observations.log` are committed; only root-level workspace state like `.active-feature` is gitignored). The dying session necessarily leaves them uncommitted (they are written *after* the clean-tree check); the successor's normal step-2 commit folds them in, and if it doesn't, the next hop's clean-tree refusal self-corrects.

### 5.5 Exit codes and degradation ladder

| Exit | Meaning | Behavior |
|---|---|---|
| 0 | Spawned, `launch=auto` | Full metadata present; non-interactive picker launch; `/pickup` submits unattended |
| 0 | Spawned, `launch=picker-manual` | Auto-mode preflight failed (§5.4c: metadata missing/incomplete, or forwarded version binary absent): workspace opens **interactive** `claude-picker "/pickup"`; notify asks the user to complete the picker (Decision 14) |
| 3 | Manual fallback (not-in-cmux · hop limit · quota) | Prints the manual resume instructions (today's protocol step 4 text) for the controller to relay; if cmux is reachable, also `cmux notify` explaining why manual intervention is needed |
| 1 | Refused (dirty tree · missing bundle · missing `.active-feature` · unsafe explicit bundle path) | Prints the failing precondition; controller fixes and re-runs |

Every non-spawn path prints the manual instructions — the protocol never dead-ends.

### 5.6 Protocol doc rewrite

`references/context-handoff-protocol.md` steps 4–5 become: *"4. Run `~/.claude/skills/superpowers/subagent-driven-development/scripts/spawn-handoff-session.sh`. Exit 0: report the workspace ref and launch mode. Exit 3: relay the printed manual instructions. Exit 1: fix the printed precondition and re-run. 5. STOP — do not dispatch the next task in this session."* A closing note documents the soft-nudge use: handing off early is preferred, and the same script serves it. Steps 1–3 are unchanged.

## 6. Component A — cmux-custom-skills repo

- **New git repo** at `~/projects/claude-custom/cmux-custom-skills`; layout mirrors `big-build-patterns`: vendored skills under `skills/<name>/` (SKILL.md, references/, scripts/, templates/ where present).
- **VENDOR.md:** upstream repo URL, pinned commit SHA, vendor date, the 4 skill names. Updated only by the sync script. The pristine rule applies to everything VENDOR.md lists; future user-authored sibling skills (out of scope now) would be exempt.
- **`sync-cmux-skills.sh`:** takes an upstream ref (default `main`); sparse-clones `manaflow-ai/cmux` at that ref into a temp dir; replaces the 4 vendored dirs wholesale; rewrites VENDOR.md with the resolved SHA; prints a diff summary. Never merges — pristine policy makes replacement safe.
- **`verify-install.sh`:** asserts the 4 `~/.claude/skills/<name>` symlinks resolve into this repo and VENDOR.md records a SHA.
- **Install:** `ln -s <repo>/skills/<name> ~/.claude/skills/<name>` for each of the 4. Flat personal skills appear in the `/skills` picker natively; no command stubs.
- **No fork/local edits to vendored files.** Fork-specific cmux guidance (e.g., "prefer `--focus false`", spawn-script pointers) lives in the superpowers CLAUDE.md's new section.

## 7. Testing

**Plan ordering note:** vendor component A first and verify the cmux CLI surface (`new-workspace --focus/--command`, `notify`, `ping`) against the vendored skill docs or live `cmux --help` *before* freezing component B's composed argv — otherwise the exact-argv unit assertions risk a rework loop. The claude-picker extension (repo 3) must also land before B's launch-composition tests are frozen.

- **Unit — `tests/unit/test_spawn_handoff.py`** (pytest; stub `cmux` AND stub `claude-picker` on PATH recording argv; stub `claude-usage-pace`): not-in-cmux → exit 3 + instructions; ping failure → exit 3; dirty tree → exit 1; missing bundle → exit 1; missing `.active-feature` → exit 1; hop limit reached → exit 3 + notice; quota below threshold → exit 3 + notice; quota tool absent → spawn proceeds with `quota=unchecked`; full metadata → `launch=auto` with exact picker flags, forwarded args, incremented label, and the embedded `|| claude-picker "/pickup"` residual fallback asserted (all three label cases: empty stays empty, unsuffixed gains `-Session-2`, `-Session-<n>` increments); forwarded args carrying a trailing `/pickup…` positional → stripped before the fresh prompt is appended (hop-recursion guard); telemetry-off but otherwise-complete metadata → `launch=auto` with telemetry off (ENABLE_TELEMETRY absence never degrades); metadata absent OR forwarded version binary missing → `launch=picker-manual` with interactive-picker command asserted; success → `new-workspace`/`notify` argv, `.handoff-hops` increment, spawn-log line; `--dry-run` → all preconditions evaluated, zero spawn argv recorded, no hop increment; unsafe explicit bundle path → exit 1.
- **telemetry-exp — picker extension tests** (that repo's conventions, via the existing `CLAUDE_PICKER_TEST_MODE` sourcing seam): metadata exports present on launch paths; non-interactive mode selects version/label/telemetry without prompting; deterministic no-prompt resolutions.
- **Installation — `cmux-custom-skills/verify-install.sh`:** 4 symlinks resolve; VENDOR.md SHA present. (Superpowers' `verify-symlink-install.sh` unchanged — repos stay decoupled.)
- **e2e — `sdd-e2e-test.sh` Step 14** (banner 14→15): fixture repo + fixture bundle + stub cmux + stub picker; drive the script end-to-end; assert composed spawn command, notify, hop counter.
- **Post-merge live smoke** (mirrors N43's discipline — the e2e proves the checkout path; the installed skill path resolves to the main checkout): in a real cmux session launched via claude-picker, `--dry-run` first (verify composed command shows the right version/args/incremented label), then one real spawn against a scratch bundle; confirm the workspace opens, the picker launches non-interactively, `/pickup` ingests; close the workspace. The first genuine HARD-block hop is the true acceptance test.
- **Hook baseline:** untouched (no hook change).

### OPEN DECISION — cross-repo execution split

The plan writer must decide how the three repos' work is sequenced and enforced: (i) one superpowers SDD plan with cross-repo tasks (accepted-deviation note for the git-reality check, whose dispatch↔commit cross-reference sees only the superpowers repo), or (ii) the telemetry-exp picker extension and/or cmux-custom-skills setup as small separate plans executed in their own repos, with the superpowers plan asserting their contracts as prerequisites. Constraint either way: repo-2 and repo-3 deliverables land before the superpowers tasks that depend on them (§7 ordering note).

## 8. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Runaway spawn chain (bad handoff → successor blocks → spawns again) | Hop counter, default max 3, manual fallback beyond; `cmux notify` on every hop |
| Unattended quota burn | Fail-open cupace precondition (§5.2.5); hop limit bounds total exposure |
| Bad handoff propagates without review | Same `/handoff` bundle flow as the manual path — no new bundle format; `/pickup` + SDD session-recovery re-validate against committed state (plan checkboxes, manifest, reports) |
| Successor runs a different version/args/label than the dying session | Forwarding contract (§5.4a) — picker-exported env, not inference; degraded `picker-manual` mode when metadata is absent rather than silently launching a mismatched session |
| Focus stealing during unattended operation | `--focus false` on every spawn; notification instead of focus |
| Vendored skills drift from upstream cmux CLI | Pinned SHA + explicit re-vendor script; `cmux-diagnostics` included for self-checks |
| Command injection via bundle path | Default path never interpolates; explicit path must resolve under `~/.claude-codex-handoff` with no whitespace/quotes |
| Picker non-interactive mode breaks interactive behavior | Extension is flag-gated; interactive path unchanged when flags absent; tested via `CLAUDE_PICKER_TEST_MODE` |
| Worktree development edits the live skill path | The spawn script is not a hook (no baseline), but live sessions resolve `~/.claude/skills/superpowers/...` to the main checkout — develop in a worktree, live-smoke after merge |

## 9. Acceptance Criteria

- [ ] The 4 cmux skills auto-list in a fresh Claude session; `cmux-custom-skills/verify-install.sh` passes.
- [ ] `spawn-handoff-session.sh --dry-run` in a real picker-launched cmux SDD session shows a composed successor command with the same version, forwarded args, and correctly incremented telemetry label.
- [ ] One real spawn: workspace opens, claude-picker launches non-interactively, `/pickup` ingests the bundle, SDD resumes at the first unchecked task.
- [ ] Metadata-absent session: spawn degrades to `launch=picker-manual` (interactive picker + notification), never a bare `claude` launch.
- [ ] Non-cmux terminal: script exits 3 and prints the manual instructions (behavior parity with today).
- [ ] Hop limit: spawn attempt max+1 (the 4th, with the default max of 3) falls back to manual with a notification.
- [ ] All suites green: superpowers unit/regression/installation/e2e (15 steps), telemetry-exp picker tests, cmux-custom-skills verify-install.
- [ ] CLAUDE.md, customization manifest, and BACKLOG updated; hook baseline untouched.
