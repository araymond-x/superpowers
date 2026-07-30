# cmux-spawn-v2 — Distilled Implementation Spec

> **Source**: `docs/imp-plans/2026-07-30-cmux-spawn-v2/spec.md` (20 decisions)
> **Distilled**: 2026-07-30
> **For**: Plan writer and implementation agents ONLY. For full rationale, see source.

## Out of scope — do not build

- N74 label composition in the pickers → future cross-repo feature.
- N68 `cmux claude-hook` lifecycle push → separate decision after this sprint.
- N71 todo-list mirroring → later sprint.
- N72 capability-drift guard → later sprint.
- N66 sidebar telemetry → deliberately dropped; candidate ride-along in a later hook-touching sprint.
- N59 pace-aware quota windows → unchanged; existing minimal quota gate stays.
- Codex telemetry metric gap → telemetry-exp repo concern.
- Any handoff-toolkit (claude-codex-handoff) or bundle-format change — the mechanics card is committed in-repo under `reports/`.
- Any picker (telemetry-exp) change.
- Non-SDD session context guarding → SP3 design doc ONLY, no implementation.
- Cross-module carry-forward fix lane → SP4 design doc ONLY, no implementation.
- `new-surface --type agent-session --provider claude` — never; it bypasses claude-picker (version pinning, telemetry, labels, append-prompt).
- Anything built on `cmux rpc` — CLI verbs only.

## Contract Facts

- **Repo scope:** this fork only. Archetype: extension; nothing removed — workspace spawn demoted to fallback.
- **Exit ladder is unchanged in shape:** 0 spawned / 3 manual fallback / 1 refused. New exit-3 reasons: `reason=policy`, `reason=stall`, `handshake=timeout`. New exit-0 outcome states: `handshake=ok|late|dialog`; `dialog` and `picker-manual` both carry a mandatory tell-the-user contract.
- **Reservation ordering unchanged:** reserve (`.handoff-hops`, intent record) BEFORE spawn; hop stays consumed on any post-spawn failure; messages must never claim "nothing was spawned" after a spawn.
- **`.handoff-hops`:** stays a single integer; existing malformed-value fail-closed guard untouched.
- **`handoff-spawn.log` record format (append-only fields):** intent records gain `tasks_done=<N>`; outcome records gain `surface=<ref>`, `tasks_done=<N>`, `handshake=<state>`, optional `topology=workspace-fallback`, `post_spawn=partial:<step>`, `budget=over-expected`; `workspace=<ref>` field RETAINED. New record type `decline` (controller-written, documented one-liner).
- **`tasks_done` counting:** implementer report files across `reports/` + `archive-*/`.
- **Manifest:** optional `handoff: {expected_hops: int, spawn_policy: "auto"|"ask"|"off"}`. Absent block → `spawn_policy=auto`; `expected_hops` re-derived at spawn time from manifest task ranges via the same formula — over-expected notify fires identically for pre-v2 manifests. No schema-version bump.
- **`expected_hops` formula:** `ceil(total_tasks / 2.5)` standard tier; `1` micro.
- **Ceiling:** `SUPERPOWERS_CMUX_MAX_HOPS` keeps name + fail-closed validation; default becomes derived `max(6, 2 × expected_hops)`; explicit env value wins absolutely.
- **Stall rule:** consecutive zero-progress hops > `SUPERPOWERS_CMUX_MAX_STALL_HOPS` (default 1) → refuse exit 3.
- **Plan model:** optional top-level `handoff_spawn: Literal["auto","ask","off"] = "auto"` in `plan.py`. `Plan` is `extra="forbid"` → **model change MUST land before/with any plan frontmatter using the field.** No schema bump.
- **Env knobs (new):** `SUPERPOWERS_CMUX_SPAWN_WAIT_TIMEOUT` (default = Task 0 cold-start measurement p95 × 2), `SUPERPOWERS_CMUX_MAX_STALL_HOPS` (default 1), `SUPERPOWERS_CMUX_POST_SPAWN` (default `rename,rc`; empty disables), post-spawn title format override. All follow existing validate-warn-revert conventions.
- **cmux verbs used (installed build 0.64.20 verified):** `new-surface --workspace --type terminal --working-directory --focus false`; `rename-tab --surface`; `send` (`\n` = Enter); `send-key … Enter`; `wait-for [-S] --timeout`; `read-screen --surface --scrollback`; fallback path `workspace create` (canonical verb replaces legacy `new-workspace` on that path only).
- **`OK <ref>` parsing is per-verb** (source: capability matrix §4.2, a-run on 0.64.20): `new-workspace` → field 2; `new-surface` → `OK surface:N pane:M workspace:K` (field 2 = surface); `rename-tab` → field 2 is `action=rename`, NOT a ref; `close-surface` returns a plausible WRONG ref — never reuse a generic field-2 parser.
- **Sent-command env rule:** a `cmux send` command runs in the workspace shell env, not the parent session's — everything the successor needs rides inline in the command string (`SUPERPOWERS_SPAWN_ID=<uuid>` prefix + any `SUPERPOWERS_CMUX_*` overrides).
- **Readiness signal:** `cmux wait-for` token `sdd-hop-$SPAWN_ID`, signaled by `hooks/session-start` when `SUPERPOWERS_SPAWN_ID` is set. **Screen reading is NEVER a success signal** — diagnosis only (3 recorded live failures of screen-scrape readiness, incl. an unanchored `›` match satisfied by shell prompts/scrollback with shell echo defeating composer verify).
- **Cold-surface behavior:** `read-screen` on a never-driven surface errors (`internal_error`) — diagnosis code must treat as "no diagnosis", not crash.
- **Baselined hooks changing:** `hooks/session-start`, `sdd-stop-hook.sh`, `sdd-pre-dispatch-hook.sh` → one `check-hooks.sh --capture` + committed `baseline.txt` in the same change.
- **Interference audit (verified, do not re-audit):** report-forgery guard, stale-artifact scan, `transition-module.py` archive sweep (`task-<NNN>-*` only), report-file globs — all clear of the new artifacts. `ctx_byte_estimate` counts the card in the advisory byte-proxy — accepted.
- **Bash constraints (inherited; source: CLAUDE.md "Hook Development Gotchas" + "cmux Auto-Spawn Handoff"):** no `set -u`/`set -e`/pipefail; bash ≥ 3.2 floor; never pipe a producer into `grep -q`; `printf` not `echo` for composed strings.
- **SDD SKILL.md word ceiling:** protocol additions land in `references/`, never the SKILL body.

## Open Decisions

| # | Decision | Options | Resolution Required By |
|---|----------|---------|----------------------|
| 1 | Mechanics-card generator language | bash vs python (not hook-invoked, so venv available either way) | Plan writer |
| 2 | `SUPERPOWERS_CMUX_SPAWN_WAIT_TIMEOUT` shipped default value | measured p95 × 2 per pinned method (true cold start: fresh surface, no warm claude process, picker version download excluded) | Task 0 measurement |

## Decision Summary

| # | Decision | Chosen |
|---|----------|--------|
| 1 | Sprint composition | Six items + spikes SP1–SP4 |
| 2 | Successor placement | Surface (top tab) in caller's workspace; one-shot workspace fallback (`topology=workspace-fallback`), then manual |
| 3 | Surface launch driver | `cmux send` of composed command + `\n` (NOT `respawn-pane`) |
| 4 | Readiness signal | `wait-for` token signaled by session-start hook on `SUPERPOWERS_SPAWN_ID`; parent blocks with timeout |
| 5 | Timeout diagnosis | banner → exit 0 `handshake=late`; trust/permission dialog → exit 0 `handshake=dialog` + mandatory tell-the-user, and the notify must NAME the dialog seen; error/other/unreadable → exit 3 `handshake=timeout`, notify + manual instructions, hop consumed |
| 6 | Post-spawn setup | Script-driven after handshake: `send "/rename <title>"` → `send-key Enter` → `read-screen` verify → `send "/rc"` → `send-key Enter` → verify "/remote-control is active". Title default `hop<N> SDD <feature>`; `rename-tab` gets same title |
| 7 | Post-spawn knobs | `SUPERPOWERS_CMUX_POST_SPAWN` (default `rename,rc`); title format env override |
| 8 | Hop budget semantics | Progress-aware stall rule + advisory `expected_hops` (notify only) + absolute ceiling |
| 9 | `expected_hops` formula | `ceil(total_tasks / 2.5)` standard; `1` micro; computed by `materialize-manifest.py` into manifest `handoff` block |
| 10 | Hop-state storage | `.handoff-hops` unchanged; per-hop data as new `handoff-spawn.log` record fields |
| 11 | `tasks_done` counting | Implementer report files across `reports/` + `archive-*/` |
| 12 | Mechanics card | Script-generated `reports/handoff-mechanics.md` (contents per §5.5 below) |
| 13 | Bookkeeping commits | Spawn script commits post-spawn (`chore(sdd): record handoff hop N`); `--no-commit` escape |
| 14 | Consent dial | `handoff_spawn: auto|ask|off` → manifest `spawn_policy`; `off` → exit 3 `reason=policy`; `ask` → refuse without `--user-approved` |
| 15 | Step-completion check | Stop-hook WARNING `systemMessage`: bundle created this session, no matching outcome/decline — matched by **bundle id** (mtime only bounds candidates) |
| 16 | Check 3b compatibility | Pre-dispatch hook naming allowlist gains `handoff-` prefix |
| 17 | Check 9 compatibility | `_check_verification_git_reality` git log gains `:(exclude)<feature-dir>` pathspec |
| 18 | Model ordering | `plan.py` + `sdd_session.py` field additions land BEFORE/with first use; no schema bump |
| 19 | Legacy verb migration | `new-workspace` → `workspace create` on the fallback path only; tests updated with it |
| 20 | Outcome record fields | `surface=` added; `workspace=` retained; per-verb `OK` parsing |

## Component Specifications

### `spawn-handoff-session.sh`
Layer structure preserved (config → preconditions → composition → spawn core → sequence).
Precondition order: clean tree → bundle → **policy** → cmux reachable → **stall/ceiling** → quota.
New `spawn_claude_surface()`: `new-surface` (parse `OK surface:N` field 2) → `rename-tab` → `send` composed command prefixed with inline env (`SUPERPOWERS_SPAWN_ID=<uuid>`, needed `SUPERPOWERS_CMUX_*` overrides). Then handshake: `cmux wait-for "sdd-hop-$SPAWN_ID" --timeout "$SUPERPOWERS_CMUX_SPAWN_WAIT_TIMEOUT"`; on timeout, diagnose via `read-screen --scrollback` per Decision 5. Surface-path failure → one workspace-fallback attempt (`workspace create`, logged `topology=workspace-fallback`) → manual. No `CMUX_WORKSPACE_ID` → manual (unchanged). After successful spawn + handshake: generate mechanics card, then commit `.handoff-hops` + `handoff-spawn.log` + `handoff-mechanics.md` (Decision 13). Stall check per Contract Facts; refusal messages include plan progress (`tasks X/Y, hops N`) and the inline-env raise instruction.

### `hooks/session-start`
When `SUPERPOWERS_SPAWN_ID` set and `cmux` on PATH: `cmux wait-for -S "sdd-hop-$SUPERPOWERS_SPAWN_ID"` backgrounded, output discarded, never affects hook exit.

### Post-spawn setup (inside spawn script, after handshake success)
Decision 6 sequence; each `send` verified by `read-screen` before the next step; verification failure → WARNING (`post_spawn=partial:<step>`), never a spawn failure.

### Hop budget (`materialize-manifest.py`, `sdd_session.py`, spawn script)
Manifest `handoff` block per Contract Facts. Spawn script: read previous outcome `tasks_done`; equal to current → stall candidate; consecutive stalls over limit → refuse exit 3 + notify "chain spawning without progress". Over `expected_hops` → notify + `budget=over-expected` log field, never refuse.

### Mechanics card generator (`skills/subagent-driven-development/scripts/write-mechanics-card.{sh|py}`)
Input: manifest path. Output: deterministic `reports/handoff-mechanics.md` containing: exact `controller-checkpoint.py` pre-dispatch + pre-completion invocations with absolute paths and `--manifest`; manifest/plan/module/deviations paths; hop state (used/expected/ceiling); last `context-observations.log` line + Check 6b midpoint status; cmux workspace/surface refs from the spawn log; `/rename`+`/rc` recipe pointer; report-frontmatter skeleton emitted from `skills/scripts/models/implementer_report.py` (skeleton must pass `validate-report.py` structurally). Invoked by spawn script pre-commit; also invocable standalone for the manual-fallback path.

### Consent + enforcement
`plan.py` field per Contract Facts; `materialize-manifest.py` copies to `handoff.spawn_policy`; spawn script enforces Decision 14; `sdd-stop-hook.sh` WARNING per Decision 15 with `decline` record type documented in the protocol.

### Protocol doc (`references/context-handoff-protocol.md`)
Add: post-spawn `/rename`+`/rc` recipe; "`--session-label` is telemetry; `/rename` is the phone-visible session name"; `settings.local.json` is NOT read by a running session — raise via inline env at spawn invocation; rewrite existing step-4 text and exit-code table for surface default + workspace fallback + `handshake=` states.

### Compatibility changes
`sdd-pre-dispatch-hook.sh` Check 3b: allowlist `handoff-` prefix. `controller-checkpoint.py` Check 9: `:(exclude)<feature-dir>` pathspec; tests pin both directions (bookkeeping-commit-in-window passes; source-commit-in-window FAILs).

### Spikes
| ID | Deliverable |
|---|---|
| SP1 | Root cause of the `[task 5 fix]` `tokens=373139` probe row (between 171k/210k neighbors); fix `context-probe.py` attribution or document the exclusion rule for tuning consumers. Blocks threshold tuning only — NOT sprint-blocking |
| SP2 | Probe transcript for `new-workspace --env`/`--env-file` + any surface-scoped equivalent; disposition on env-vs-command-string for the fallback path |
| SP3 | Design doc + BACKLOG row: context guard for non-SDD sessions. NO implementation |
| SP4 | Design doc + BACKLOG row: carry-forward fix lane across module transitions. NO implementation |

## Testing Requirements

- Unit (`tests/unit/test_spawn_handoff*.py` + new): surface happy path; per-verb `OK` parsing incl. `close-surface` wrong-ref negative fixture; workspace fallback; handshake success/timeout × `late`/`dialog`/`error` branches via stub `read-screen` fixtures; stall detection (progress / 1 stall allowed / 2 refused); ceiling derivation + env override; policy dial (`auto`/`ask`±`--user-approved`/`off`); mechanics-card golden-file; generated report skeleton passes `validate-report.py` structurally; model round-trips; Check 3b (card allowed, junk blocked); Check 9 pathspec both directions.
- E2E: Step 14 rewritten (surface topology, handshake via token-signaling stub, `tasks_done` fields, policy dial); stubs for all new verbs.
- Hook baseline: one `check-hooks.sh --capture` covering all three changed hooks, same change.
- Regression: `validate-all-skills.py` after doc edits.
- Post-merge live smoke: dry-run + one real surface spawn into a throwaway workspace; the next real SDD run is the acceptance test.

## Acceptance Criteria

- [ ] A HARD/soft handoff spawns the successor as a top tab in the caller's workspace, `--focus false` held, tab renamed `hop<N> SDD <feature>`.
- [ ] The successor is visible in the Claude phone app with that name and `/rc` active, with zero human keystrokes.
- [ ] `handoff-spawn.log` outcome records carry `surface=`, `tasks_done=`, launch mode, and handshake status; e2e Step 14 asserts them.
- [ ] A chain completing tasks every hop is never refused below the ceiling; two consecutive zero-progress hops are refused with a progress-bearing message.
- [ ] `expected_hops` appears in the manifest and the over-expected notify fires (e2e stub).
- [ ] The successor's first dispatch requires no report-naming, checkpoint, or Check 9 remediation caused by handoff artifacts.
- [ ] `handoff_spawn: ask` blocks scripted spawn without `--user-approved`; `off` refuses with `reason=policy`.
- [ ] Handshake diagnosis branches behave per Decision 5 under stubbed `read-screen` fixtures: `late`/`dialog` exit 0 with distinct outcome fields; `timeout` exits 3.
- [ ] All suites green (unit, e2e with updated banner count, regression, install); hook baseline re-captured in the same change.
- [ ] SP1–SP4 deliverables committed under `docs/process-improvement-findings/` (SP1 may instead land as a `context-probe.py` fix with tests).
