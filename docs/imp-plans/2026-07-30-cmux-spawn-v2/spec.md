# cmux-spawn-v2 — SDD Auto-Spawn Handoff, Second Pass

**Date:** 2026-07-30
**Archetype:** Extension + targeted refactor of the shipped N43(D) integration. Nothing is
removed; the workspace spawn is demoted to a fallback path.
**Repo scope:** this fork only. No handoff-toolkit (claude-codex-handoff) changes; no picker
(telemetry-exp) changes.

## 1. Evidence base

This spec is grounded in the first full live SDD run over the integration (2026-07-29/30,
claude-codex-handoff `cmux-transport` worktree, 5 sessions, 3 auto-spawn hops), analyzed via
transcript mining and the telemetry store, plus the 2026-07-28 cmux capability audit
(`docs/process-improvement-findings/2026-07-28-cmux-capability-usage-matrix.md`) re-verified
against the installed binary (`cmux 0.64.20 (100) [14e3400b9]`) on 2026-07-30.

Headline measurements driving the design:

- **Transport reliability:** 3/3 spawns `launch=auto`, pickup unattended in 4–6 s, zero cmux/
  picker/API failures. The mechanical layer needs no rework.
- **Topology mismatch:** the user's model is repo = workspace, session = top tab (surface);
  the script spawns sibling workspaces. The surface chain (`new-surface` → `send` launch →
  `rename-tab`) is exercised-proven on this build, twice.
- **Knowledge-transfer failure:** hop-0 derived the working `/rename`+`/rc` recipe; hop-1
  could not find it anywhere loadable and declined. The recipe exists in zero runtime artifacts.
- **Hop budget shape:** plan = 22 tasks; measured throughput ~2–5 tasks/hop (declining 5→3→2);
  fixed `MAX_HOPS=3` exhausted at 41% of the plan and stalled a healthy chain ~11.5 h. The
  mid-chain raise path the successor tried (`settings.local.json`) is dead — only an inline env
  var at spawn time works.
- **Re-discovery tax:** 70–96% of each successor's pickup window (10–19 min, 47–95 tool calls)
  re-derives state the predecessor held; ~1 avoidable user round-trip per hop; checkpoint CLI
  re-derived by trial-and-error every hop (5 cwd-reset failures across 3 sessions).
- **Protocol adherence variance:** spawn step skipped once, permission-asked once, autonomous
  once — consent and step-completion are unmodeled.
- **Screen-scrape failure class (3 live instances):** cold surfaces are unreadable until driven;
  a blocking modal reads as a normal screen; and (2026-07-30, toolkit repo) an unanchored `›`
  readiness match over the whole screen can be satisfied by a shell prompt/branch name/scrollback,
  with the shell echo defeating a composer verify. Screen reading is NEVER a success signal.
- **Report first-write schema failures (3 live instances):** two implementer reports in this
  chain and one dispatch prompt in the toolkit run (invented frontmatter enums) failed
  `validate-report.py` on first write.

## 2. Goals

1. Successors spawn as **top tabs (surfaces) in the caller's repo workspace**, named for the
   phone and the tab bar, with the spawn loop **closed** by a deterministic handshake.
2. The successor is **phone-visible without human setup**: `/rename` + `/rc` driven by the
   script, not re-derived by each controller.
3. The hop budget **measures progress, not count**: a healthy chain never stalls; a
   non-progressing chain stops within two hops.
4. The **re-discovery tax shrinks structurally**: a generated mechanics card carries exact
   commands, state, and recipes to the successor.
5. Spawn **consent is declarative** and step-completion is checked.

## 3. Non-goals / out of scope — do not build

- N74 label composition in the pickers (three-repo scope) → future cross-repo feature.
- N68 `cmux claude-hook` lifecycle push → separate decision (S) after this sprint.
- N71 todo-list mirroring; N72 capability-drift guard → later sprints.
- N66 sidebar telemetry → deliberately dropped (touches the baselined pre-dispatch hook for
  cosmetic value); candidate ride-along in a later hook-touching sprint.
- N59 pace-aware quota windows → unchanged; the existing minimal quota gate stays.
- Codex telemetry metric gap → telemetry-exp repo concern.
- Any change to the handoff toolkit or bundle format — the mechanics card is committed
  in-repo under `reports/`, not bundled.
- Non-SDD session context guarding (the $127 planning session) → **SP3 design doc only.**
- Cross-module carry-forward fix lane → **SP4 design doc only.**
- `new-surface --type agent-session --provider claude` — bypasses claude-picker (version
  pinning, telemetry, labels, append-prompt). Standing rejection, unchanged.
- Building anything on `cmux rpc` — CLI verbs only, per the fork's source-hierarchy rule.

## 4. Decisions

| # | Decision | Chosen |
|---|---|---|
| 1 | Sprint composition | All six items + spikes SP1–SP4 |
| 2 | Successor placement | Surface (top tab) in the caller's workspace; legacy workspace spawn retained as one-shot fallback (`topology=workspace-fallback`), then manual. **Both topologies go through ONE shared launch-and-handshake wrapper** — the fallback gets the same inline env, token handshake, timeout ladder, post-spawn setup, and outcome fields. Fallback is permitted only when the surface path fails BEFORE its launch command is accepted (`new-surface`/`rename-tab`/`send` non-zero); after a successful `send`, a token timeout must NEVER trigger a second spawn |
| 3 | Surface launch driver | `cmux send` of the composed command + `\n` (NOT `respawn-pane`: a fast-failing launch must leave a readable tab) |
| 4 | Readiness signal | Deterministic `cmux wait-for` token signaled by `hooks/session-start` when `SUPERPOWERS_SPAWN_ID` is set; parent blocks with timeout. Screen reading is diagnosis-only, never success |
| 5 | Timeout handling | **A received wait-for token is the ONLY exit-0 path (`handshake=ok`).** On timeout: one bounded re-wait of the same duration (covers slow cold starts); still no token → **exit 3, `handshake=timeout`**, hop consumed. `read-screen` then enriches the outcome record and the manual instructions with `diagnosis=banner\|trust-dialog\|picker-error\|unreadable\|none` — it never selects the exit code. `diagnosis=trust-dialog` instructions say: answer the NAMED dialog in tab `<ref>` — the successor may exist; do NOT start a fresh session yet. `diagnosis=banner` instructions say: successor may be alive but unconfirmed; check the tab before any fresh session. Notify fires on every timeout, naming the diagnosis |
| 6 | Post-spawn setup | Script-driven after handshake: `send "/rename <title>"` → `send-key Enter` → `read-screen` verify → `send "/rc"` → `send-key Enter` → verify `/remote-control is active`. Default title `hop<N> SDD <feature>`; `cmux rename-tab` gets the same title |
| 7 | Post-spawn knobs | `SUPERPOWERS_CMUX_POST_SPAWN` (default `rename,rc`; empty disables); title format override env |
| 8 | Hop budget semantics | Progress-aware: `tasks_done` recorded per spawn; consecutive zero-progress hops > `SUPERPOWERS_CMUX_MAX_STALL_HOPS` (default 1) → refuse. `expected_hops` advisory (notify when exceeded). Absolute ceiling `SUPERPOWERS_CMUX_MAX_HOPS`, default derived `max(6, 2 × expected_hops)`; explicit env wins |
| 9 | `expected_hops` formula | `ceil(total_tasks / 2.5)` standard tier; `1` micro. Computed by `materialize-manifest.py`, stored in manifest `handoff` block |
| 10 | Hop-state storage | `.handoff-hops` stays a single integer (guards unchanged); per-hop `tasks_done=<N>` rides new fields on `handoff-spawn.log` intent/outcome records |
| 11 | `tasks_done` counting | Deterministic: **unique task IDs** across `reports/` + `archive-*/` whose implementer report's YAML frontmatter parses AND records completed status (`verification` reports count under their own rules — empty `files_changed` valid). A filename alone never counts: BLOCKED/incomplete/duplicate reports must not inflate progress. Value persisted in the intent record at reservation |
| 12 | Mechanics card | Script-generated `reports/handoff-mechanics.md`: absolute-path checkpoint invocations (`--manifest`), key paths, hop state, gate state, cmux refs, `/rename`+`/rc` recipe pointer, and a valid report-frontmatter skeleton emitted from the actual Pydantic model |
| 13 | Bookkeeping commits | The spawn script commits its own bookkeeping post-spawn (`chore(sdd): record handoff hop N`); `--no-commit` escape for tests |
| 14 | Consent dial | Plan frontmatter `handoff_spawn: auto\|ask\|off` (default `auto`) → manifest. `off` → **exit 3** `reason=policy-off`; `ask` without `--user-approved` → **exit 3** `reason=policy-ask`, **retryable** (re-run with the flag after asking the user), and the policy check runs as a precondition BEFORE reservation — no hop is consumed on a policy refusal |
| 15 | Step-completion check | Stop-hook WARNING-level `systemMessage` when a handoff bundle was created this session but no spawn outcome or recorded decline exists |
| 16 | Check 3b compatibility | Pre-dispatch hook naming allowlist gains a `handoff-` prefix |
| 17 | Check 9 compatibility | `_check_verification_git_reality` git log gains `:(exclude)<feature-dir>` pathspec — feature-dir bookkeeping is legitimate SDD churn; source changes still flag |
| 18 | Model ordering | `plan.py` (`handoff_spawn`) and `sdd_session.py` (`handoff` block) changes land BEFORE any plan/manifest uses the fields (`Plan` is `extra="forbid"`); no schema-version bump (optional fields, defaults) |
| 19 | Legacy verb migration (N70) | Only on the workspace-fallback path this sprint touches (`new-workspace` → `workspace create`), tests updated with it |
| 20 | Outcome record fields | Outcome gains `surface=<ref>` alongside `workspace=<ref>`; `workspace=` retained for consumer compatibility; per-command `OK <ref>` parsing re-derived per verb (field positions differ; `close-surface` returns a plausible wrong ref) |

## 5. Component specifications

### 5.1 `spawn-handoff-session.sh` (core rework)

Layer structure preserved (config → preconditions → composition → spawn core → sequence).
Changes:

- **Preconditions** gain: policy check (Decision 14; after bundle validation, before cmux
  reachability) and stall check (Decision 8; replaces the flat hop-count check, which becomes
  the ceiling check). Precondition order: clean tree → bundle → policy → cmux reachable →
  stall/ceiling → quota.
- **`spawn_claude_surface()`** (new, alongside the extraction-ready workspace core):
  `cmux new-surface --workspace "$CMUX_WORKSPACE_ID" --type terminal --working-directory
  "$WORKTREE_ROOT" --focus false` → parse `OK surface:N …` (field 2 of THIS verb's shape) →
  `cmux rename-tab --surface <ref> "<title>"` → `cmux send --surface <ref> "<SUCCESSOR_CMD>\n"`.
  The sent command string is prefixed with inline env: `SUPERPOWERS_SPAWN_ID=<uuid>` plus any
  `SUPERPOWERS_CMUX_*` overrides that must survive into the successor (a sent command runs in
  the workspace shell env, not the parent session's).
- **Handshake**: after the send, block on `cmux wait-for "sdd-hop-$SPAWN_ID" --timeout
  "$SUPERPOWERS_CMUX_SPAWN_WAIT_TIMEOUT"` (default measured in Task 0 of the plan — a **true
  cold start**: fresh surface, no warm claude process, picker version download excluded;
  shipped default = measured p95 × 2, pinned in the plan from that measurement; do not guess). Timeout → one bounded re-wait of the
  same duration, then Decision 5: exit 3 with `read-screen --scrollback` diagnosis
  ENRICHMENT only — the scrape never selects the exit code.
- **Fallback ladder**: `new-surface` or `rename-tab`/`send` failure → one attempt via the
  legacy workspace path (now `cmux workspace create`, Decision 19), logged
  `topology=workspace-fallback` → then manual fallback. No `CMUX_WORKSPACE_ID` → manual
  (unchanged).
- **Reservation ordering unchanged** (Decision 21 of the original spec): reserve → spawn.
  New: reservation intent record carries `tasks_done=<N>`; after a successful spawn +
  handshake, the script generates the mechanics card, then commits `.handoff-hops`,
  `handoff-spawn.log`, `handoff-mechanics.md` (Decision 13).
- **Exit ladder**: 0 spawned AND token received (`handshake=ok`; auto | picker-manual
  launch modes unchanged); 3 manual fallback (existing causes + `reason=policy-off`,
  `reason=policy-ask`, `reason=stall`, and the token-timeout rung `handshake=timeout` with
  `diagnosis=<state>` in the outcome record — its instructions vary by diagnosis and must
  never claim nothing was spawned); 1 refused (unchanged causes).

### 5.2 `hooks/session-start` (handshake signal)

When `SUPERPOWERS_SPAWN_ID` is present in the environment and `cmux` is on PATH:
`cmux wait-for -S "sdd-hop-$SUPERPOWERS_SPAWN_ID"` (backgrounded, output discarded, never
affects hook exit). Baselined hook → `check-hooks.sh --capture` in the same change.

### 5.3 Post-spawn setup (in the spawn script, after handshake success)

Decision 6 sequence, each `send` verified by `read-screen` before the next step; verification
failure is WARNING-level (logged in the outcome record as `post_spawn=partial:<step>`), never
a spawn failure — the successor is alive; naming is cosmetic. `references/context-handoff-protocol.md`
changes: the recipe; the "`--session-label` is telemetry; `/rename` is the phone-visible
session name" distinction; the `settings.local.json`-not-read-mid-session warning; and a
**rewrite of the existing step-4 text and exit-code table**, which currently say "spawns the
successor in a new cmux workspace" and describe workspace-topology causes — the doc must
describe the surface default, the workspace fallback, and the new `handshake=` outcome
states, or it will contradict the shipped behavior.

### 5.4 Hop budget (`materialize-manifest.py`, `sdd_session.py`, spawn script)

- Manifest gains optional `handoff: {expected_hops: int, spawn_policy: str}`. Old manifests
  remain valid (no schema bump) with pinned absent-block behavior: `spawn_policy` defaults to
  `auto`; `expected_hops` is re-derived at spawn time via the Decision 9 formula with pinned
  **input precedence**: (1) a validated manifest total-task count when present; (2) the union
  of unique task IDs across module declarations; (3) the inclusive active `task_range`.
  Invalid/zero totals → refuse the derivation and treat `expected_hops` as absent-with-warning
  (advisory notify suppressed, WARN logged) — never divide by garbage. So the over-expected
  notify fires identically for pre-v2 manifests with sane data, and degrades loudly otherwise.
- **First-hop and malformed-history semantics (stall check):** hop 1's baseline is
  `tasks_done=0` (no prior record ≠ stall). A missing or malformed previous outcome record →
  stall check SKIPs for that spawn with `stall=indeterminate` logged — the fail-closed guard
  for counter corruption remains `.handoff-hops`'s own numeric check, not this.
- Spawn script stall logic: read previous outcome record's `tasks_done`; count current;
  equal → stall candidate; consecutive stalls > `SUPERPOWERS_CMUX_MAX_STALL_HOPS` → refuse
  exit 3 with notify "chain spawning without progress". Exceeding `expected_hops` → notify +
  `budget=over-expected` log field, never refuse. Ceiling per Decision 8; refusal message
  includes plan progress (`tasks X/Y, hops N`) and the inline-env raise instruction; the
  protocol doc warns that `settings.local.json` writes are NOT read by a running session.

### 5.5 Mechanics card generator

`skills/subagent-driven-development/scripts/write-mechanics-card.sh` (or `.py` — plan
decides; must run under the venv-less constraint the plan-validation gate imposes only if
invoked from hooks, which it is not). Inputs: manifest path. Output: deterministic
`reports/handoff-mechanics.md` containing: exact `controller-checkpoint.py` pre-dispatch and
pre-completion invocations with absolute paths and `--manifest`; manifest/plan/module/
deviations paths; hop state (used / expected / ceiling); last `context-observations.log`
line + Check 6b midpoint status; cmux workspace/surface refs from the spawn log; pointer to
the `/rename`+`/rc` recipe; report-frontmatter skeleton emitted from
`skills/scripts/models/implementer_report.py` (Decision 12). Invoked by the spawn script
pre-commit; also invocable standalone by the protocol's manual-fallback path.

### 5.6 Consent + enforcement

- `plan.py`: optional `handoff_spawn: Literal["auto","ask","off"] = "auto"` (top-level plan
  field). `validate-plan.py`: no new gate; field validated by the model.
- `materialize-manifest.py` copies it into `handoff.spawn_policy`.
- Spawn script: Decision 14 mechanics (`ask` ⇒ require `--user-approved`).
- `sdd-stop-hook.sh`: WARNING `systemMessage` when a bundle for the active feature was
  created during the session but the spawn log has no matching outcome and no `decline`
  record. **Matching key is the bundle id** (outcome records already carry `bundle=<id>`),
  not mtime alone — an mtime-only heuristic false-positives on unrelated bundles in the
  shared `~/.claude-codex-handoff/bundles/` dir; mtime only bounds the candidate set. New record type `decline` writable by the
  controller via a documented one-liner in the protocol. Baselined hook → same-change
  re-capture.

### 5.7 Compatibility changes (from the interference audit)

- `sdd-pre-dispatch-hook.sh` Check 3b allowlist: add `handoff-` prefix (Decision 16).
- `controller-checkpoint.py` Check 9: `:(exclude)<feature-dir>` pathspec (Decision 17), unit
  tests pinning: bookkeeping-commit-in-window passes; source-commit-in-window still FAILs.
- Verified non-collisions (no action, recorded so nobody re-audits): report-forgery guard
  (`reports/task-*` + `.dispatch-log` scoped); stale-artifact scan (`task-*`,
  `pre-execution-audit*`); `transition-module.py` archive sweep (`task-<NNN>-*` only —
  spawn log/hops/card survive transitions); report-file globs (pattern-scoped);
  `ctx_byte_estimate` counts the card in the advisory byte-proxy (accepted, it is real
  context).

## 6. Spikes

| ID | Question | Deliverable | Gate? |
|---|---|---|---|
| SP1 | Why did a `[task 5 fix]` dispatch log `tokens=373139` between 171k/210k neighbors? (`source=probe` row poisoning) | Root cause + fix to `context-probe.py` attribution, or documented exclusion rule for tuning consumers | Blocks threshold tuning only, not this sprint |
| SP2 | Do `new-workspace --env`/`--env-file` work as documented (a-help only)? Any surface-scoped equivalent? | Probe transcript + disposition on env-vs-command-string for the fallback path | No |
| SP3 | Where should a context guard for non-SDD sessions live? ($127/569k unguarded planning session) | Design doc + BACKLOG row; NO implementation | No |
| SP4 | Sanctioned carry-forward-fix lane across module transitions | Design doc + BACKLOG row; NO implementation | No |

## 7. Error handling summary

- Every new failure path maps to the existing 0/3/1 ladder; no new exit codes.
- `handshake=timeout` is the only post-spawn failure (exit 3): hop stays consumed
  (reservation is durable); the outcome record carries `diagnosis=<state>`; messages must
  never claim "nothing was spawned", and the `trust-dialog`/`banner` diagnoses must steer
  the human to the existing tab before any fresh-session resume (double-spawn prevention).
- Post-spawn setup failures are cosmetic WARNINGs (`post_spawn=partial`).
- All cmux verbs remain best-effort-guarded as today (`2>/dev/null || true` only where a
  precondition has already proven reachability; the notify asymmetry rules are unchanged).
- The screen-reading code path (diagnosis) must tolerate `internal_error: Failed to read
  terminal text` (cold surface) and treat it as "no diagnosis available", not a crash.

## 8. Testing

- **Unit** (`tests/unit/test_spawn_handoff*.py` + new files): surface happy path; per-verb
  `OK` parsing with an exit-status + verb-specific response predicate for EVERY
  state-changing verb, plus negative/malformed-response fixtures for `new-surface`,
  `rename-tab`, `send`, `send-key` (incl. the `close-surface` wrong-ref hazard; never reuse
  `rename-tab`/`close-surface` output as a target ref); workspace fallback **through the
  shared launch-and-handshake wrapper** (fallback success + fallback token-timeout cases;
  a token timeout after a successful `send` never spawns twice); **a banner with no token
  is non-success**; timeout → re-wait → exit 3 with each `diagnosis=` branch via stub
  `read-screen` fixtures; stall detection (progress, 1 stall allowed, 2 stalls refused,
  first-hop baseline, `stall=indeterminate` on missing/malformed prior outcome);
  `tasks_done` counting (BLOCKED/incomplete report not counted, duplicate files deduped by
  task ID, archived reports counted, verification-report rules); `expected_hops` input
  precedence + legacy-manifest shapes + invalid/zero-total degradation;
  ceiling derivation + env override; policy dial (`auto`/`ask`±`--user-approved`/`off`,
  `reason=policy-ask` retryable, hop counter untouched by policy refusals);
  mechanics-card content (golden-file); report-skeleton validity (generated skeleton passes
  `validate-report.py` structurally); model round-trips for `handoff_spawn`/`handoff` block;
  Check 3b allowlist (card allowed, junk still blocked); Check 9 pathspec (both directions);
  interference invariant pinned: `handoff-mechanics.md` contributes to the byte-proxy
  estimate while matching neither task-report nor stale-artifact scans.
- **E2E**: Step 14 rewritten for surface topology + handshake (stub `cmux` signals the token)
  + `tasks_done` fields + policy dial; stubs updated for `new-surface`/`send`/`send-key`/
  `rename-tab`/`wait-for`/`read-screen`/`workspace create`.
- **Hook baseline**: `hooks/session-start`, `sdd-stop-hook.sh`, `sdd-pre-dispatch-hook.sh`
  all change → one `check-hooks.sh --capture` ships with them.
- **Regression**: `validate-all-skills.py` after protocol/SKILL doc edits (watch the SDD
  SKILL.md word ceiling — protocol additions land in `references/`, not the SKILL body).
- **Live smoke (post-merge)**: hooks and the installed skill path resolve to the main
  checkout, so worktree coverage is never final proof. The next real SDD run is the
  acceptance test; a minimal scripted smoke (dry-run + one real surface spawn into a
  throwaway workspace) runs immediately post-merge.

## 9. Acceptance criteria

- [ ] A HARD/soft handoff spawns the successor as a top tab in the caller's workspace,
      `--focus false` held, tab renamed `hop<N> SDD <feature>`.
- [ ] The successor is visible in the Claude phone app with that name and `/rc` active,
      with zero human keystrokes.
- [ ] `handoff-spawn.log` outcome records carry `surface=`, `tasks_done=`, launch mode,
      and handshake status; e2e Step 14 asserts them.
- [ ] A chain completing tasks every hop is never refused below the ceiling; a chain with
      two consecutive zero-progress hops is refused with a progress-bearing message.
- [ ] `expected_hops` appears in the manifest and the over-expected notify fires (e2e stub).
- [ ] The successor's first dispatch requires no report-naming, checkpoint, or Check 9
      remediation caused by handoff artifacts (interference audit holds under test).
- [ ] `handoff_spawn: ask` blocks scripted spawn without `--user-approved`; `off` refuses
      with `reason=policy`.
- [ ] The wait-for token is the only exit-0 path: a stubbed banner/dialog screen with no
      token exits 3 with the matching `diagnosis=` field; a received token exits 0
      (`handshake=ok`).
- [ ] All suites green: unit, e2e (banner count updated), regression, install;
      hook baseline re-captured in the same change.
- [ ] SP1–SP4 deliverables committed under `docs/process-improvement-findings/` (SP1 may
      instead land as a `context-probe.py` fix with tests).
