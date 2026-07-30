# First Full Live SDD Auto-Spawn Run — Analysis (2026-07-29/30)

**Date:** 2026-07-30
**Subject:** the first complete production run of the N43(D) cmux auto-spawn handoff, observed
end-to-end in the `claude-codex-handoff` repo (`.worktrees/cmux-transport`, feature
`2026-07-29-cmux-transport`, 22 tasks / 7 modules, standard tier).
**Method:** transcript mining of the 5-session hop chain + read-only DuckDB telemetry
(`telemetry-exp`, `session_identity`/`metric_fact`/`log_fact` grains) + the feature's flight
recorders (`context-observations.log`, `handoff-spawn.log`, `.handoff-hops`).
**Consumer:** the `cmux-spawn-v2` sprint (`docs/imp-plans/2026-07-30-cmux-spawn-v2/spec.md`)
was designed directly from this analysis; its spec §1 summarizes these numbers.

Sessions (chronological): planning `c5c245f2…`; SDD hop 0 `08d5a306…`; hop 1 `d8a9d842…`;
hop 2 `942fee60…`; hop 3 `2328844e…` (all full UUIDs in the telemetry store).

## The chain at a glance

| Hop | Session | Tasks done | End ctx (controller) | Cost | Active min | Cost/task |
|---|---|---|---|---|---|---|
| 0 | 08d5a306 | 0–4 (5) | ~356k | $30.78 | 67 | $6.16 |
| 1 | d8a9d842 | 5–7 (3) | ~375k | $54.08 | 109 | $18.03 |
| 2 | 942fee60 | 8–9 (2) | ~353k | $52.55 | 111 | $26.28 |
| 3 | 2328844e | 10+ (in flight) | — | $20.15+ | 43+ | — |
| — | c5c245f2 (planning) | — | peak 569k | **$127.08** | 103 | — |

Chain total at capture: **$284.64**, 55 commits, ~12k LoC delta. Model note: hop 0 ran
sonnet-dominant; hops 1+ ran opus-1M-dominant — most of the per-hop cost jump is model mix,
not output volume.

## What worked (do not redesign)

1. **The spawn transport was flawless.** 3/3 auto-spawns `launch=auto`; successor `/pickup`
   ran unattended 4–6 s after spawn; quota gate 87–96%; zero cmux CLI failures, zero picker
   degradations, zero API errors across ~1,825 tool calls. The "Enter is flaky" theory was a
   misattribution to the one hand-rolled (non-scripted) launch.
2. **The context gate worked as designed.** Three soft nudges (344k / 346k / 331k), each
   followed by finishing the task's reviews and a *voluntary* handoff at a clean module
   boundary (353–375k). The 400k hard block never fired. Zero probe fallbacks, zero bypasses.

## Findings

**F1 — Topology mismatch.** User's model: repo = workspace, session = top tab. The script
spawns sibling workspaces (workspace:25/26/27). Three user utterances said "pane/surface";
none said "workspace". The planning session itself hand-launched the first SDD session as a
`new-surface` + `send` picker launch — proving the surface path live. → sprint item 2 (N73).

**F2 — Knowledge fails to travel between hops.** Hop 0 derived the full `/rename` + `/rc`
recipe (send text → `send-key Enter` → `read-screen` verify; confirmed by the successor's
session title). Hop 1, asked for the same thing 2 h later, searched `~/.claude/commands/`,
found nothing named `rc`, conflated `--session-label` with `/rename`, and declined. The
recipe existed in zero artifacts a successor loads. → sprint item 3.

**F3 — Hop budget has the wrong shape.** Fixed `MAX_HOPS=3` vs measured throughput of 2–5
tasks/hop on a 22-task plan (~6–7 hops needed): the chain exhausted its budget at 41% of the
plan and stalled ~11.5 h overnight awaiting a human raise. The attempted raise path
(`settings.local.json`) is dead — a running session does not read it; only an inline env var
at spawn time works (hop 3 proved this itself). → sprint item 4 (progress-aware stall rule +
advisory expected_hops + derived ceiling).

**F4 — The re-discovery tax dominates the handoff cost.** Per successor pickup window
(session start → first dispatch): 47–95 tool calls over 10–19 min, of which **70–96% re-derive
state the predecessor held** (same four SDD reference docs re-read per hop; checkpoint CLI
re-derived by trial-and-error every hop — 5 cwd-reset failures across 3 sessions; hop-state
and cmux re-discovery — 19 cmux calls on hop 3 of an identical topology). Plus ~1 avoidable
user round-trip per hop. → sprint item 5 (generated `handoff-mechanics.md`).

**F5 — Protocol adherence varies per hop.** Spawn step 4: hop 0 forgot it entirely (84 min
idle until the user asked), hop 1 asked permission, hop 2 ran it autonomously. Consent and
step-completion are unmodeled. → sprint item 6 (`handoff_spawn` dial + stop-hook WARNING).

**F6 — Post-spawn bookkeeping dirties the successor's tree.** The spawn writes
`.handoff-hops` + `handoff-spawn.log` after the final commit; hop 2 inherited the dirt and
had to reason about it before committing; the hop-3 spawner self-corrected by committing
post-spawn. → sprint item 5 / Decision 13 (script commits its own bookkeeping). (BACKLOG N64
live-confirmed.)

**F7 — One poisoned probe row.** `context-observations.log` carries
`2026-07-30T00:56:54Z task=5 type=other tokens=373139` between neighbors reading 171k/210k —
coinciding with a `[task 5 fix]` dispatch; the value matches the *predecessor's* end-of-session
total. Harmless (`action=allow`) but threshold tuning consumes only `source=probe` rows, so
one misattributed row corrupts tuning. → sprint spike SP1 (BACKLOG N76).

**F8 — Planning sessions are unguarded.** The planning session ran to 569k context and
$127.08 — 45% of chain cost — with zero gate activity: the context gate fires only on SDD
implementer dispatches. → sprint spike SP3 (design only).

**F9 — No lane for carry-forward fixes across module boundaries.** A `[task 7 fix]` dispatch
after the module transition was hard-blocked as outside `task_range [8,9]`; the controller
re-homed the fixes as "Task 8 Step 0" (good judgment covering a structural hole). → sprint
spike SP4 (design only).

**F10 — Report first-writes fail schema.** Two implementer reports in this chain (plus one
dispatch prompt in the toolkit run inventing frontmatter enums) failed `validate-report.py`
on first write. → mechanics card ships a model-generated report skeleton (Decision 12).

**F11 — Error inventory is clean.** 21/1,825 failed tool results — roughly a third
intentional probes; the rest cwd-reset relative paths and gate scripts doing their jobs. One
benign Codex websocket close. No hook partial failures beyond the 4 known artifact-gate
blocks; no span errors. The only human-blocking failures all run through **trust/approval
dialogs** — which the sprint's `diagnosis=trust-dialog` rung now detects — and the hop-limit
escalation (F3).

## Screen-scrape failure class (third instance)

The in-flight toolkit sprint independently reported `cmux_await_ready` matching an unanchored
`›` over the whole screen (satisfiable by a shell prompt, branch name, or scrollback, with
shell echo defeating the composer verify). With the capability audit's two instances (cold
surfaces unreadable; a blocking modal reading as a normal screen), that is three live
failures of screen-pattern *readiness*. Consequence, encoded in the sprint spec: **a received
`wait-for` token is the only success signal; read-screen is post-timeout diagnosis only.**

## Disposition

All findings route to `cmux-spawn-v2` (items 1–6, spikes SP1–SP4) except F9/F8 which are
design-only spikes producing their own BACKLOG rows. BACKLOG rows corrected from this
analysis: N55 (MAX_HOPS defect fixed by `7425e38`), N61 (command-chain token design does not
work — corrected to the session-start-hook signal), N56/N57/N64/N67/N70/N73 (status/scope
updates), N76 (new, F7).

---

## Addendum — session-driving observations (2026-07-30 afternoon, live cross-session tests)

Gathered while relaying operator notes into the two in-flight sessions (plan + executor). All
a-run unless labeled.

**A1 — `read-screen` is viewport-only against an alt-screen TUI (measured).** Claude Code runs
on the terminal's alternate screen buffer: `read-screen --scrollback --lines 100000` against a
live session returned **42 lines** — the current frame. The TUI's own collapse chips
(`… +160 lines`, `… +18 tool uses`) are unexpandable from the screen side. Screen reads are a
liveness/state probe (running? dialog up? composer content?), never a history channel.

**A2 — the transcript is the complete observation channel.** A session's `.jsonl` under
`~/.claude/projects/<encoded-LAUNCH-cwd>/` carries every message, full uncollapsed tool
output, per-call usage, and subagent transcript pointers. Gotcha: the encoding keys on the
session's LAUNCH cwd — a session that enters a worktree after launch keeps writing under its
original project dir (the plan session's transcript sat in the main-checkout dir; its
executor's in the worktree dir).

**A3 — injected input can be silently captured; two distinct states observed.**
(i) An **AskUserQuestion selector overlay** consumes `cmux send` text (send returns `OK`,
nothing reaches the composer, nothing reaches the transcript). (ii) With the surface showing
the **"Jump to bottom" scrolled-viewport indicator**, sends were likewise swallowed — N=2
correlation, unreproduced (surface closed before a controlled probe), hypothesis: tmux-copy-
mode-style input capture. **Exonerated by transcript evidence: `/remote-control`** — a note
sent ~20 min after `/rc` activation landed and was acted on, so rc-active sessions accept
injected input normally. An earlier draft of the executor bundle's addendum blamed `/rc`; the
bundle carries the correction.

**A4 — the surviving driving discipline** (now the documented recipe): read-screen for overlay
state BEFORE driving; send text; read-screen VERIFY the composer holds it; only then Enter;
and when delivery matters, confirm receipt in the target's transcript — the only ground truth.
Sends during a busy turn queue fine (proven live); sends into menus/scrolled surfaces vanish
with `OK` status.
