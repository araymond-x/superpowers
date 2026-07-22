# cmux Integration — Design Spec

> **Feature:** `cmux-integration`
> **Status:** design, approved (rev 4 — rev 3 resolved the external Codex review, bundle `2026-07-22T20-47-17Z-superpowers`: 2 blockers, 4 majors, 2 minors, 1 nit; rev 4 adds compose-side quoting + Decision 22 parameterized validation; all open decisions resolved; spec + distillation reviewers approved)
> **Date:** 2026-07-22
> **BACKLOG:** closes N43 component **(D)** (cmux auto-spawn of the next session); component A of this spec is net-new (no prior BACKLOG row)
> **Archetype:** Extension — vendors external skills into a new sibling repo and extends the N43 context-handoff protocol. The only replaced content is the tail of `references/context-handoff-protocol.md` (steps 3–5: step 3 gains the bundle-id capture; steps 4–5 are rewritten).

---

## 1. Problem

Two gaps keep the fork's SDD pipeline from using cmux, the terminal environment every session already runs in.

**The handoff seam is manual.** N43 shipped the context-pressure gate: at the HARD block the controller commits, builds an N39 `/handoff` bundle, and STOPs — then the *user* must start a fresh session from the worktree and run `/pickup`. The N43 BACKLOG row anticipated the fix and deferred it as component (D): "cmux auto-spawn of the next session … unattended self-spawn carries runaway + quota-burn risk → needs safeguards." The live 2026-07-15 block (~757k tokens) proved the gate; the restart friction remains. Sessions are launched through `claude-picker` (version selection + telemetry labeling), so a faithful auto-restart must preserve the forwarding session's version, launch arguments, and telemetry labeling — not just run bare `claude`.

**Agents have cmux plumbing but no cmux knowledge.** The cmux Claude wrapper is active (session hooks, Feed bridge, notifications), and every session inherits `CMUX_WORKSPACE_ID` / `CMUX_SURFACE_ID` / a reachable socket. But no cmux skills are installed in `~/.claude/skills`, so no agent knows the CLI surface exists.

This feature closes both: vendor the official cmux agent skills into a dedicated sibling repo (A), and make the blocked SDD controller spawn its own successor through claude-picker (B).

## 2. Goals & Non-Goals

### In scope — three repos, three ordered repo-local deliverables (Decision 19)
1. **B-picker — claude-picker forwarding contract** (telemetry-exp repo, lands first): forwarding-metadata exports on every launch path; non-interactive mode; contract probe; testability refactor. Own small plan, committed and tested in its repo.
2. **A — Vendored cmux skills** (NEW repo `~/projects/claude-custom/cmux-custom-skills`, lands second): 4 official skills (`cmux`, `cmux-workspace`, `cmux-markdown`, `cmux-diagnostics`) from `manaflow-ai/cmux` at a pinned SHA under `skills/`; VENDOR.md; re-vendor sync script; the repo's own install-verify script; symlinks from `~/.claude/skills/`.
3. **B — Auto-spawn handoff** (superpowers repo, lands last; the SDD plan's home): a deterministic, internally-layered `spawn-handoff-session.sh` invoked by the rewritten protocol step 4. **Fully automatic** (user decision): the successor launches through claude-picker non-interactively and `/pickup <bundle-id>` submits without human confirmation. Consumes the repo-1/2 deliverables as asserted prerequisites, never builds them.

### Out of scope — do not build
- SDD sidebar telemetry (`set-progress`/`set-status` from controller or hooks) → future feature.
- Live artifact panels (`cmux markdown open` for plan/deviations, `cmux diff` at finish) → future feature.
- Worktree-workspace customization (one-click worktree agent buttons) → future feature.
- Fleet orchestration (parallel Claude sessions as cmux workspaces) → needs its own design; bypasses Agent-tool hook enforcement.
- The other 3 cmux skills (`cmux-browser`, `cmux-settings`, `cmux-customization`) → install later if needed.
- Codex-side symlinks (`~/.agents/skills`) and codex-picker parity → later.
- **N43 component (C)** — full pace-aware pause/resume via `cupace` (the user's `claude-usage-pace` personal CLI; "cupace" throughout this spec) with its sleep-until-reset remedy → its own spec. This feature takes only the §5.3 spawn-time session-window check; weekly-window pacing stays in component (C).
- **B10** — pressure-conditional context-summary gate → separate fast-follow.
- Any change to the context gate's thresholds, tiers, probe, or observation-log format.
- Auto-spawn from `writing-plans`/`brainstorming` sessions → later; this feature targets the SDD controller seam only. Two seams are left ready for it: the layered spawn core (extraction) and the parameterized bundle validation (§5.2.2 — future consumers pass their own expected bundle type + entry skill).
- Spawning **review-type** bundles (the user's regular `/handoff-review … plan` flow; toolkit `bundle_type=review`, `review_subject=plan|code`) → arrives with the brainstorming/writing-plans auto-spawn work above; the §5.2.2 parameterization is deliberately sufficient for it.
- Codex auto-review dispatch (`/handoff-review auto-cdx`) integration → **excluded: currently non-functional**; revisit once the dispatch backend works again.
- Extracting the generic spawn core to `skills/scripts/` → when a second consumer arrives.
- User-authored custom cmux skills in the new repo → later (the repo layout leaves room; only vendored skills ship now).
- Successor pickup ACK/liveness confirmation beyond the spawn outcome record → later if multi-hop telemetry shows a need.

## 3. Affected Code

**Repo 1 (ordered) — telemetry-exp:**

| Path | Change |
|---|---|
| `launchers/claude-picker` | (a) Export forwarding metadata on **every launch path** (telemetry on, telemetry off, and no-telemetry-repo alike): `CLAUDE_CODE_PICKER_VERSION` (selected version), `CLAUDE_CODE_PICKER_ARGS` (v1 argv codec, §5.4a — encoded faithfully; prompt-positional stripping is the spawn script's job), `CLAUDE_CODE_PICKER_LABEL` (currently telemetry-path-only; moves to every path). (b) **Non-interactive mode** via pinned flags (Decision 20): `--non-interactive`, `--pick-version <v>`, `--session-label <label>`, `--telemetry <on|off>`; would-be prompts resolve deterministically (Docker down → telemetry off; unknown version → non-zero exit); interactive behavior unchanged when flags absent. (c) **Contract probe:** `--handoff-contract` prints the integer contract version (`1`) and exits 0. (d) **Testability refactor** (Codex finding 6): version-selection, telemetry resolution, and launch composition move into pure functions ABOVE the `CLAUDE_PICKER_TEST_MODE` seam; subprocess tests with stubbed `read`/exec/docker assert no `read` fires in non-interactive mode and the three exports are present at the exec boundary on all launch paths |

**Repo 2 (ordered) — cmux-custom-skills (NEW, `~/projects/claude-custom/cmux-custom-skills`):**

| Path | Change |
|---|---|
| `skills/{cmux,cmux-workspace,cmux-markdown,cmux-diagnostics}/` | **NEW** — pristine vendored copies (layout mirrors `big-build-patterns`: skills under `skills/`) |
| `VENDOR.md` | **NEW** — upstream repo URL, pinned SHA, vendor date, per-skill inventory |
| `sync-cmux-skills.sh` | **NEW** — re-vendor from upstream at a given ref; updates VENDOR.md |
| `verify-install.sh` | **NEW** — checks the 4 `~/.claude/skills/<name>` symlinks resolve here + VENDOR.md SHA recorded |
| `~/.claude/skills/{cmux,cmux-workspace,cmux-markdown,cmux-diagnostics}` | **NEW symlinks** → `<repo>/skills/<name>` (install step; no command stubs) |

**Repo 3 (ordered) — superpowers (the SDD plan's home; consumes 1+2 as asserted prerequisites):**

| Path | Change |
|---|---|
| `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` | **NEW** — the auto-spawn tool (§5), layered: generic `spawn_claude_workspace()` core (detect, spawn, notify) marked extraction-ready + SDD policy shell |
| `skills/subagent-driven-development/references/context-handoff-protocol.md` | Rewrite steps 3–5: step 3 captures the bundle id from `/handoff`; step 4 runs the spawn script WITH that id; degraded modes per §5.5; note the script also serves the soft-nudge early handoff |
| `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` | **No change** (verified at spec review: the HARD-block message already ends with a pointer to the protocol doc, sdd-pre-dispatch-hook.sh:840). No baseline re-capture |
| `tests/unit/test_spawn_handoff.py` | **NEW** — stub-cmux + stub-claude-picker + stub-cupace unit suite (§7) |
| `tests/integration/sdd-e2e-test.sh` | **NEW Step 14** (banner 14→15) — end-to-end spawn with stubs |
| `CLAUDE.md`, `docs/ARaymond-customization-manifest.md`, `docs/process-improvement-findings/BACKLOG.md` | New "cmux Integration" section (`SUPERPOWERS_CMUX_MAX_HOPS` + `SUPERPOWERS_CMUX_QUOTA_MIN_PCT` join the Hook Development Gotchas env-var list; cross-repo pointers); inventory entries; close N43(D) lineage with a new row |

`skills/subagent-driven-development/SKILL.md` body: **no change** (word ceiling). `tests/ARaymond-installation/verify-symlink-install.sh`: **no change** — cmux symlink checks live in repo 2 (repo decoupling; B does not depend on A).

## 4. Key Design Decisions

| # | Decision | Options considered | Chosen | Why |
|---|----------|--------------------|--------|-----|
| 1 | Autonomy level | command-only · staged spawn (prefill, user submits) · fully automatic | **Fully automatic** | User decision. The SDD run continues unattended across the session boundary; safeguards (#6, #7, #16, #21, notify) carry the risk the BACKLOG named. |
| 2 | Spawn logic placement | in the hook · prose in the protocol doc · deterministic script | **Deterministic script** | The hook fires *before* the commit and bundle exist — wrong seam. Prose executed by a context-exhausted controller is exactly what N43 distrusts. A script is testable and owns the safeguards. |
| 3 | Skill install mechanism | `npx skills add` (upstream-managed) · vendored + symlink | **Vendored at pinned SHA + symlink** | Matches the established `big-*`/elements-of-style pattern; version-controls what agents ingest; re-vendor is explicit and reviewable. |
| 4 | Skill subset | all 7 · 4 (core, workspace, markdown, diagnostics) | **4** | Each skill adds per-session context weight. Browser duplicates claude-in-chrome; settings/customization are user-driven tasks, installable later. |
| 5 | Launch mechanics | spawn terminal + typed keystrokes (`cmux send`) · `new-workspace --command` | **`--command` launch** | No TUI keystroke-timing fragility. The new terminal goes through the cmux Claude wrapper shim, so session restore and Feed integration engage automatically. |
| 6 | Runaway guard | none · hop counter | **Hop counter file + `SUPERPOWERS_CMUX_MAX_HOPS` (default 3)** | Answers the BACKLOG's runaway risk. Exceeding the limit falls back to manual instructions — never a dead end. |
| 7 | Quota guard | none · full component C · minimal session-window check | **Minimal check, parameters pinned in §5.3** | User decision; Codex blocker 2 required pinning before planning. Spawning into a nearly-exhausted 5h window burns the remainder unattended. |
| 8 | Spawn event log | append to `reports/context-observations.log` · separate file | **Separate `reports/handoff-spawn.log`** | The observations log format is pinned; threshold tuning consumes `source=probe` rows only. Spawn events get their own file and format. |
| 9 | Vendored-file policy | allow local edits · pristine | **Pristine** | Re-vendoring must never conflict. Fork-specific cmux guidance lives in CLAUDE.md, not in vendored files. |
| 10 | Regression-suite treatment | include vendored skills in `validate-all-skills.py` · exclude | **Exclude** (they live outside this repo entirely) | Vendored skills follow upstream's conventions, not the fork's. Repo 2's `verify-install.sh` checks presence and link integrity. |
| 11 | Skills home | in-fork `external-skills/` · dedicated sibling repo | **`~/projects/claude-custom/cmux-custom-skills`** | User decision. Matches `big-build-patterns`/`telemetry-exp` (own repo, symlinked); keeps upstream-sync surface of the fork untouched; leaves room for future user-authored cmux skills. |
| 12 | Successor launch command | bare `claude "/pickup"` · claude-picker with forwarded context | **claude-picker, forwarding version + args + telemetry label** | User decision. Successor must be a faithful continuation: same Claude Code version, same launch args (e.g. `--append-system-prompt-file`), same telemetry labeling with an incremented session counter. |
| 13 | Forwarding metadata channel | parse process tree · picker exports `CLAUDE_CODE_PICKER_*` env | **Picker exports** | `CLAUDE_CODE_*` passes Claude Code's subprocess env filter (the picker already exports `_LABEL` for this reason); the spawn script reads inherited env — no fragile `ps` parsing. |
| 14 | Missing-metadata behavior | refuse · bare claude fallback · interactive picker in the spawned workspace | **Interactive picker, attended** | "Always claude-picker" (user requirement) even degraded: the workspace opens the picker with the pickup prompt queued as its passthrough arg; a notification asks the user to complete the picker. |
| 15 | Script generality | split shared helper now · one script with layered interior | **Layered single script, extraction-ready core** | User decision (YAGNI). Generic `spawn_claude_workspace()` core + SDD policy shell in one file; extract to `skills/scripts/` when the second consumer (e.g. writing-plans handoff) arrives. |
| 16 | Bundle resolution | default-latest with existence check · required explicit id + manifest validation | **Required id + validation (§5.2.2)** | Codex blocker 1: global-latest races with other repos' bundles — an unattended spawn against a foreign bundle dead-ends at pickup's guard. The protocol just created the bundle; passing its id is free and deterministic. |
| 17 | `CLAUDE_CODE_PICKER_ARGS` encoding | "shell-quoted string" · versioned lossless codec | **v1 codec: `v1:` + base64(JSON array of argv strings)** (§5.4a) | Codex major 3: a shell-quoted string needs `eval` to parse — inherited env becoming code execution. The codec round-trips arbitrary argv losslessly and decodes without eval. |
| 18 | Label boundary ownership | picker sanitizes whatever it gets · spawn script emits the final, already-safe label | **Spawn script owns the final label** (§5.4b) | Codex major 4: sanitize-then-truncate at 255 could silently drop the new `-Session-<n>` suffix. Reserving suffix space before concatenation makes the round-trip stable. |
| 19 | Cross-repo execution split | one superpowers SDD plan with cross-repo tasks · ordered repo-local deliverables | **Repo-local: telemetry-exp → cmux-custom-skills → superpowers** | Codex major 5: cross-repo commits bypass the SDD plan's git-reality evidence. Repo-local work preserves each repo's review/commit trail; the superpowers plan asserts the contracts as prerequisites (§7 Task-0-style assertions). |
| 20 | Picker non-interactive interface | defer flag names to plan time · pin now | **Pinned:** `--non-interactive`, `--pick-version <v>`, `--session-label <label>`, `--telemetry <on|off>`, `--handoff-contract` | Codex nit 9: unpinned names risk divergent repo-1/repo-3 implementations. `--pick-version` avoids the conventional print-and-exit meaning of `--version`. |
| 21 | Spawn state ordering | log/increment after spawn · reserve before spawn | **Reservation before spawn** (§5.4d) | Codex minor 7: a post-spawn write failure must not invite a retry that double-spawns. Reserving the hop and intent record first makes the hop consumption durable; post-spawn failures are non-retryable by construction. |
| 22 | Bundle-validation shape | hard-code SDD expectations · parameterized expected type + entry skill | **Parameterized; SDD shell pins `work` + SDD entry skill** | User requirement (prepared for `/handoff-review` plan flows reaching brainstorming/writing-plans later): future consumers change parameters, not the validator. The toolkit already models this (`bundle_type` choices `work|review`, `review_subject` `plan|code`, first-class `--entry-skill`). |

## 5. Component B — `spawn-handoff-session.sh`

### 5.1 Interface

```
spawn-handoff-session.sh BUNDLE_ID [--dry-run]
```

- `BUNDLE_ID` (**required**): the handoff bundle created by protocol step 3 (the step's `/handoff` output includes it). Validated per §5.2.2.
- `--dry-run`: run every precondition and the preflight, print the composed `cmux` + `claude-picker` commands, spawn nothing and increment nothing (`.handoff-hops` untouched). Used by tests and the post-merge live smoke.

Env: `SUPERPOWERS_CMUX_MAX_HOPS` (default `3`); `SUPERPOWERS_CMUX_QUOTA_MIN_PCT` (default `15`, §5.3); forwarding metadata per §5.4a. Path resolution: worktree root = `git rev-parse --show-toplevel`; feature dir = `.active-feature` at that root (missing → refusal; SDD sessions always have one).

Internal layering (Decision 15): a generic `spawn_claude_workspace()` function (cmux detection, workspace spawn, notify; parameters: cwd, launch command, workspace name, notify text) marked extraction-ready, wrapped by the SDD policy shell (preconditions, bundle validation, reservation, launch composition, exit-code contract).

### 5.2 Preconditions (checked in order; fail-closed)

1. **Clean tree** — `git status --porcelain` empty. The script *verifies* protocol step 2 rather than trusting a context-exhausted controller. Dirty → **refuse (exit 1)**.
2. **Bundle valid** (Decisions 16 + 22) — `BUNDLE_ID` matches `^[A-Za-z0-9_.-]+$` AND resolves to a directory under `~/.claude-codex-handoff/bundles/` AND its `manifest.json` satisfies: expected `bundle_type`; expected entry skill; the bundle's workspace repo matches the current worktree root under the same repo-match rule the pickup guard applies (worktree/main crossings of one repo count as a match). The validation is implemented as a **parameterized function** — expected bundle type and entry skill are its inputs; the SDD policy shell pins `work` + `superpowers:subagent-driven-development` for this feature. Future consumers (brainstorming/writing-plans auto-spawn; `/handoff-review` plan/code bundles with `bundle_type=review`) pass their own expected values — no redesign. Any check fails → **refuse (exit 1)** naming the failed check.
3. **cmux reachable** — `CMUX_WORKSPACE_ID` set AND `cmux ping` returns PONG. Otherwise → **manual fallback (exit 3)**; not an error — non-cmux terminals keep today's behavior.
4. **Hop limit** — read `<feature-dir>/reports/.handoff-hops`; count ≥ `SUPERPOWERS_CMUX_MAX_HOPS` → **manual fallback (exit 3)** with a "hop limit reached" notice.
5. **Quota (fail-open, parameters pinned in §5.3)** — below threshold → **manual fallback (exit 3)** with a quota notice; unreadable → proceed with `quota=unchecked`.

### 5.3 Quota check — pinned parameters (resolves Codex blocker 2; schema verified live 2026-07-22)

- **Invocation:** `~/.claude/bin/claude-usage-pace --json --no-log` (`--no-log` keeps automation out of the pace history), wrapped in a **60s timeout**.
- **Field:** `windows[key=="session"].remaining_pct` (percent of the 5h window remaining; live sample: `63.0`).
- **Threshold:** refuse when `remaining_pct < SUPERPOWERS_CMUX_QUOTA_MIN_PCT` (default **15**).
- **Classification:** parsed numeric below threshold → **exit 3**, log `quota=low:<pct>`. Parsed at/above → proceed, log `quota=ok:<pct>`. Tool absent, non-zero exit, timeout, unparseable JSON, `session` window missing, or `remaining_pct` missing/non-numeric → proceed, log `quota=unchecked` (fail-open class — a broken sensor must not strand the handoff; the hop limit still bounds exposure).
- Weekly windows (`week_all`, `week_premium`) are **not** consulted — that is component (C)'s domain.

### 5.4 Launch composition and spawn sequence (success path)

**(a) Forwarding metadata**, read from the controller session's inherited env (exported by the extended claude-picker at the forwarding session's own launch):

| Var | Meaning | Used as |
|---|---|---|
| `CLAUDE_CODE_PICKER_VERSION` | Claude Code version the forwarding session runs | successor `--pick-version` |
| `CLAUDE_CODE_PICKER_ARGS` | **v1 codec** (Decision 17): `v1:` + base64(JSON array of argv strings), the faithful passthrough argv of the forwarding launch | decoded **without eval** (python3 stdlib), then appended to the successor launch |
| `CLAUDE_CODE_PICKER_LABEL` | telemetry label (may be empty) | incremented per (b) |
| `CLAUDE_CODE_ENABLE_TELEMETRY` | `1` when telemetry is on; legitimately **absent** on telemetry-off launches (sourced only on the ON path) | successor `--telemetry on|off`; absence ⇒ `off`, never blocks auto |

**Hop-recursion guard:** after decoding, the script strips any trailing positional beginning `/pickup` from the argv array. A successor session's own forwarded args otherwise re-carry the previous hop's queued prompt — a duplicated `/pickup`, or a stale `/pickup <old-bundle>` ahead of the fresh one.

**(b) Label rule (Decision 18 — spawn script owns the final label):** strip any existing trailing `-Session-<n>` from the inherited label → sanitize the base with the picker's attr charset rule → compute the suffix (`-Session-<n+1>` if a counter was stripped, else `-Session-2`) → truncate the base to `255 − len(suffix)` → concatenate. Empty (or empty-after-sanitize) base → no label. The result is already picker-sanitizer-stable (round-trip is a no-op).

**(c) Successor launch command:**
`claude-picker --non-interactive --pick-version <v> --telemetry <on|off> [--session-label <label>] <decoded forwarded args> "/pickup <BUNDLE_ID>"` — the pickup prompt **always** carries the validated bundle id (Decision 16; no latest-resolution anywhere). The id's charset is validated in §5.2.2, so its interpolation is safe by construction.

**Compose-side quoting:** the command above is embedded as a single string in `new-workspace --command` and re-parsed by a shell inside the workspace — so **every interpolated element** (each decoded forwarded arg, the version value, the label) must be re-quoted shlex-quote-style when the string is composed. Decision 17's codec guarantees safe decode; this requirement closes the second surface (safe re-embedding). A naive space-join would break exactly the motivating case (`--append-system-prompt-file <path with space>`) on the primary auto path.

**Auto-mode preflight:** `launch=auto` is composed only when: metadata is usable (VERSION non-empty; ARGS decodes under the v1 codec or is absent ⇒ empty argv; LABEL may be empty; `CLAUDE_CODE_ENABLE_TELEMETRY` absent ⇒ off) AND the forwarded version binary exists at `~/.local/share/claude/versions/<version>` AND `claude-picker` resolves on PATH AND `claude-picker --handoff-contract` prints exactly `1` — the contract version this script implements; a future v2 picker with a breaking codec change must fail preflight (degrade to `picker-manual`), not pass it (Codex minor 8). Preflight failure → compose `launch=picker-manual` instead (§5.5). As a residual guard against runtime picker failure inside the spawned workspace, the auto command embeds a fallback chain — `<non-interactive picker command> || { <append runtime-picker-failure outcome line>; claude-picker "/pickup <BUNDLE_ID>"; }` — so an unexpected non-zero picker exit is recorded distinctly and lands in the attended interactive picker, never a dead workspace.

**(d) Spawn sequence (Decision 21 — reserve before spawn):**
1. **Reserve:** increment `<feature-dir>/reports/.handoff-hops`; append an `intent` line (spawn id = uuid) to `<feature-dir>/reports/handoff-spawn.log`.
2. `cmux new-workspace --name "SDD resume: <feature>" --cwd <worktree-root> --command '<successor launch command>' --focus false` — never steal focus. Spawn failure here → append `outcome=spawn-failed`, keep the hop consumed (over-counting is safer than a runaway retry), **exit 3** with the manual instructions.
3. Append the `outcome` line (workspace ref, launch mode `auto|picker-manual`, quota status); `cmux notify --title "SDD handoff" --body "Hop N/<max> — successor spawned in <workspace-ref>"`. Failures in this step are **non-retryable** (the successor already exists): warn on stderr, still exit 0.
4. Print the workspace ref and exit 0. The controller reports it and **STOPs** (protocol step 5 unchanged).

**Log format** (`handoff-spawn.log`, one line per record): ISO-8601 timestamp, spawn id, record type (`intent` | `outcome` | `runtime-picker-failure`), hop number, and for outcomes: workspace ref, launch mode, bundle id, quota status.

**Git treatment of spawn artifacts:** `.handoff-hops` and `handoff-spawn.log` are **tracked** — the `reports/` convention (`.dispatch-log` and `context-observations.log` are committed; only root-level workspace state like `.active-feature` is gitignored). The dying session necessarily leaves them uncommitted (they are written *after* the clean-tree check); the successor's normal step-2 commit folds them in, and if it doesn't, the next hop's clean-tree refusal self-corrects.

### 5.5 Exit codes and degradation ladder

| Exit | Meaning | Behavior |
|---|---|---|
| 0 | Spawned, `launch=auto` | Preflight passed; non-interactive picker launch; `/pickup <BUNDLE_ID>` submits unattended |
| 0 | Spawned, `launch=picker-manual` | Auto-mode preflight failed (§5.4c: metadata unusable, version binary absent, picker unresolvable, or contract probe failed): workspace opens **interactive** `claude-picker "/pickup <BUNDLE_ID>"`; notify asks the user to complete the picker (Decision 14) |
| 3 | Manual fallback (not-in-cmux · hop limit · quota low · spawn-failed after reservation) | Prints the manual resume instructions (today's protocol step 4 text) for the controller to relay; if cmux is reachable, also `cmux notify` explaining why manual intervention is needed |
| 1 | Refused (dirty tree · bundle validation failed · missing `.active-feature`) | Prints the failing precondition; controller fixes and re-runs |

Every non-spawn path prints the manual instructions — the protocol never dead-ends.

### 5.6 Protocol doc rewrite

`references/context-handoff-protocol.md`: step 3 now ends by **capturing the bundle id** from the `/handoff` output. Steps 4–5 become: *"4. Run `~/.claude/skills/superpowers/subagent-driven-development/scripts/spawn-handoff-session.sh <bundle-id>`. Exit 0: report the workspace ref and launch mode. Exit 3: relay the printed manual instructions. Exit 1: fix the printed precondition and re-run. 5. STOP — do not dispatch the next task in this session."* A closing note documents the soft-nudge use: handing off early is preferred, and the same script serves it. Steps 1–2 are unchanged.

## 6. Component A — cmux-custom-skills repo

- **New git repo** at `~/projects/claude-custom/cmux-custom-skills`; layout mirrors `big-build-patterns`: vendored skills under `skills/<name>/` (SKILL.md, references/, scripts/, templates/ where present).
- **VENDOR.md:** upstream repo URL, pinned commit SHA, vendor date, the 4 skill names. Updated only by the sync script. The pristine rule applies to everything VENDOR.md lists; future user-authored sibling skills (out of scope now) would be exempt.
- **`sync-cmux-skills.sh`:** takes an upstream ref (default `main`); sparse-clones `manaflow-ai/cmux` at that ref into a temp dir; replaces the 4 vendored dirs wholesale; rewrites VENDOR.md with the resolved SHA; prints a diff summary. Never merges — pristine policy makes replacement safe.
- **`verify-install.sh`:** asserts the 4 `~/.claude/skills/<name>` symlinks resolve into this repo and VENDOR.md records a SHA.
- **Install:** `ln -s <repo>/skills/<name> ~/.claude/skills/<name>` for each of the 4. Flat personal skills appear in the `/skills` picker natively; no command stubs.
- **No fork/local edits to vendored files.** Fork-specific cmux guidance (e.g., "prefer `--focus false`", spawn-script pointers) lives in the superpowers CLAUDE.md's new section.

## 7. Testing

**Ordering (Decision 19):** repo 1 (picker contract) lands first with its own tests; repo 2 second; the superpowers plan then opens with Task-0-style **prerequisite assertions** — `claude-picker --handoff-contract` prints exactly `1` (the same check the runtime preflight consumes), the 4 skill symlinks resolve, `cmux ping` works — before any B task, and consumes the pinned contracts without modifying repos 1–2. Verify the cmux CLI surface (`new-workspace --focus/--command`, `notify`, `ping`) against the vendored skill docs or live `cmux --help` before freezing B's exact-argv unit assertions.

- **Repo 1 — telemetry-exp picker tests** (subprocess + refactored-function tests per §3): exports present on ALL launch paths (telemetry on/off/no-repo) at the exec boundary; non-interactive mode never calls `read`; deterministic no-prompt resolutions; `--handoff-contract` prints `1`; v1 ARGS codec round-trips spaces, quotes, backslashes, empty args, option-values, an existing `/pickup <arg>` positional, and hostile-looking input.
- **Repo 2 — `cmux-custom-skills/verify-install.sh`:** 4 symlinks resolve; VENDOR.md SHA present. (Superpowers' `verify-symlink-install.sh` unchanged — repos stay decoupled.)
- **Repo 3 — unit, `tests/unit/test_spawn_handoff.py`** (pytest; stub `cmux`, stub `claude-picker` — including its `--handoff-contract` probe — and stub `claude-usage-pace` on PATH recording argv): not-in-cmux → exit 3 + instructions; ping failure → exit 3; dirty tree → exit 1; bundle validation failures (bad charset, outside bundles dir, wrong `bundle_type`, wrong entry skill, repo mismatch) → exit 1 each; missing `.active-feature` → exit 1; hop limit reached → exit 3 + notice; quota `low` → exit 3 + notice; quota `unchecked` classes (tool absent, timeout, malformed JSON, missing field) → spawn proceeds, logged; quota `ok` → proceeds; full metadata → `launch=auto` with exact picker flags, decoded forwarded args, incremented label, and the embedded runtime-failure fallback chain asserted (all label cases: empty stays empty, unsuffixed gains `-Session-2`, `-Session-<n>` increments, 255-boundary reserves suffix space, empty-after-sanitize drops the label); forwarded argv carrying a trailing `/pickup…` positional → stripped; a space/quote-bearing decoded argv driven through composition → survives intact in the `--command` string (compose-side quoting, §5.4c); telemetry-off but otherwise-complete metadata → `launch=auto` with `--telemetry off`; metadata absent / version binary missing / picker missing / contract probe failing → `launch=picker-manual`; reservation ordering → `intent` precedes `new-workspace` argv, spawn failure leaves the hop consumed + `outcome=spawn-failed` + exit 3; `--dry-run` → preconditions + preflight evaluated, zero spawn argv, no hop increment.
- **Repo 3 — e2e, `sdd-e2e-test.sh` Step 14** (banner 14→15): fixture repo + fixture bundle (valid manifest) + stub cmux + stub picker; drive the script end-to-end; assert composed spawn command, notify, reservation-then-outcome log records.
- **Post-merge live smoke** (mirrors N43's discipline — the e2e proves the checkout path; the installed skill path resolves to the main checkout): in a real cmux session launched via the extended claude-picker, `--dry-run` first (verify composed command shows the right version, decoded args, and incremented label), then one real spawn against a scratch bundle; confirm the workspace opens, the picker launches non-interactively, `/pickup <id>` ingests; close the workspace. The first genuine HARD-block hop is the true acceptance test.
- **Hook baseline:** untouched (no hook change).

## 8. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Runaway spawn chain (bad handoff → successor blocks → spawns again) | Hop counter, default max 3, manual fallback beyond; `cmux notify` on every hop |
| Unattended quota burn | Pinned session-window check (§5.3); hop limit bounds total exposure |
| Spawn against the wrong bundle (cross-repo latest race) | Required validated bundle id (§5.2.2); `/pickup <id>` everywhere — no latest-resolution |
| Inherited env becomes code execution via forwarded args | v1 codec decodes without eval (surface 1); compose-side shlex-style re-quoting of every interpolated element (surface 2, §5.4c); hostile-input cases in repo-1 (codec) and repo-3 (composition) matrices |
| Bad handoff propagates without review | Same `/handoff` bundle flow as the manual path — no new bundle format; `/pickup` + SDD session-recovery re-validate against committed state (plan checkboxes, manifest, reports) |
| Successor runs a different version/args/label than the dying session | Forwarding contract (§5.4a) — picker-exported env, not inference; degraded `picker-manual` mode when metadata is absent rather than silently launching a mismatched session |
| Double-spawn on post-spawn write failure | Reservation before spawn (Decision 21); post-spawn failures non-retryable, workspace ref reported |
| Telemetry label collision at the 255-char boundary | Suffix-space reservation before concatenation (§5.4b); boundary + multi-hop tests |
| Focus stealing during unattended operation | `--focus false` on every spawn; notification instead of focus |
| Vendored skills drift from upstream cmux CLI | Pinned SHA + explicit re-vendor script; `cmux-diagnostics` included for self-checks |
| Picker non-interactive mode breaks interactive behavior | Extension is flag-gated; interactive path unchanged when flags absent; subprocess tests per §3 |
| Worktree development edits the live skill path | The spawn script is not a hook (no baseline), but live sessions resolve `~/.claude/skills/superpowers/...` to the main checkout — develop in a worktree, live-smoke after merge |

## 9. Acceptance Criteria

- [ ] Repo 1: extended claude-picker ships with passing tests; `--handoff-contract` prints `1`; exports present on every launch path.
- [ ] Repo 2: the 4 cmux skills auto-list in a fresh Claude session; `verify-install.sh` passes.
- [ ] `spawn-handoff-session.sh <bundle-id> --dry-run` in a real picker-launched cmux SDD session shows a composed successor command with the same version, decoded forwarded args (safely re-quoted), and correctly incremented telemetry label.
- [ ] One real spawn: workspace opens, claude-picker launches non-interactively, `/pickup <bundle-id>` ingests the bundle, SDD resumes at the first unchecked task.
- [ ] Bundle validation: a foreign-repo or non-SDD bundle id is refused (exit 1) before any hop is consumed.
- [ ] Metadata-absent session: spawn degrades to `launch=picker-manual` (interactive picker + notification), never a bare `claude` launch.
- [ ] Non-cmux terminal: script exits 3 and prints the manual instructions (behavior parity with today).
- [ ] Hop limit: spawn attempt max+1 (the 4th, with the default max of 3) falls back to manual with a notification.
- [ ] All suites green: superpowers unit/regression/installation/e2e (15 steps), telemetry-exp picker tests, cmux-custom-skills verify-install.
- [ ] CLAUDE.md, customization manifest, and BACKLOG updated; hook baseline untouched.
