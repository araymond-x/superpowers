# Context Handoff Protocol (controller block-response)

The pre-dispatch hook has BLOCKED the next new-task implementer dispatch. The
usual cause is context pressure: the controller's context reached the hard
threshold (default 400k tokens) at a clean task boundary — the previous task is
reviewed and committed. Follow this protocol. Do NOT improvise. (A
different block — "the context gate has run blind for N consecutive dispatches" —
means `context-probe.py` itself is failing; that one is NOT a handoff. Fix the
probe or set `SUPERPOWERS_CTX_HANDOFF_BYPASS`, per the blind-streak message,
rather than following the steps below.)

**1. This is NOT a fix-and-retry.** Retrying the dispatch is wrong — the block
is not caused by a missing report or a failed review. Do not edit files to "get
past" it, and do not set `SUPERPOWERS_CTX_HANDOFF_BYPASS` unless you have a
specific reason to run without the gate (a diagnosed probe fault). The correct
response is to hand off, not to push through.

**2. Commit pending state.** Ensure the completed task's code, its reports under
`reports/`, updated plan checkboxes, and `deviations.md` are all committed. The
fresh session resumes from committed state only.

**3. Build the fresh-session handoff and capture its id.** Invoke the `handoff`
skill to create a bundle whose entry skill is
`superpowers:subagent-driven-development` (the N39 flow). The bundle captures the
goal, the plan/manifest, and next-action context. **Capture the bundle id** the
`/handoff` output prints (e.g. `2026-07-23T01-19-43Z-<repo>`) — step 4 needs it.

**Before step 4 — preconditions the script does NOT set up for you.**

*Where to run it:* from the **repo root of the target worktree**. The script takes no path
argument — it resolves the worktree with a bare `git rev-parse --show-toplevel` against
*your current directory*. Run it from anywhere else and it silently targets a different
repo; run it outside a repo and it exits 1.

*What must already be true:* a **clean tree**, an existing **`.active-feature`** (non-empty,
worktree-relative, no `..` segment, not resolving outside the worktree), and a
`/handoff` bundle of type `work` whose entry skill is
`superpowers:subagent-driven-development`, in this same repo. Any of these missing → exit 1
with the cause printed. Fix and re-run; nothing was consumed.

*What the session must be:* launched via **`claude-picker`, inside cmux**. That is not
ceremony — the picker exports `CLAUDE_CODE_PICKER_VERSION`, `_ARGS`, `_LABEL` and
`_APPEND_PROMPT`, and those four ARE the input to the successor command. cmux supplies
`CMUX_WORKSPACE_ID`.

*The failure that does not look like one:* if any picker variable is missing (or its
version file isn't executable, or the picker isn't on PATH, or its `--handoff-contract`
probe doesn't return `1`), the script **does not error**. It degrades to
`launch=picker-manual`, drops `--non-interactive`, and reports a spawned
successor — but that successor sits on an interactive menu until a human finishes it. The
notification does not mention the mode. **Read the `launch=` value; do not infer success
from exit 0.** A plain terminal, or any non-picker session, degrades this way by default.

*Hop budget (per-feature, not global).* `.handoff-hops` lives in the ACTIVE FEATURE's
`reports/` dir — a different project starts fresh at 0. Three numbers govern the chain:
the **ceiling** (the hard kill switch — see `SUPERPOWERS_CMUX_MAX_HOPS` below),
**`expected_hops`** (advisory only —
exceeding it logs `budget=over-expected` and notifies, never refuses), and the **stall**
guard (consecutive zero-progress hops). Every spawn attempt is recorded in
`reports/handoff-spawn.log` — check it first when diagnosing.

**4. Spawn the successor (or fall back).** Run:

    ~/.claude/skills/superpowers/subagent-driven-development/scripts/spawn-handoff-session.sh <bundle-id>

The script verifies the clean tree, validates the bundle, checks the spawn policy,
cmux reachability, the stall guard and hop ceiling, and session quota; then it
**spawns the successor as a new SURFACE — the top tab — in the CALLER's own cmux
workspace** (a sibling tab of this session), drives it through `claude-picker`, and
waits for the successor to signal a `cmux wait-for` readiness token. Only the received
token is success (`handshake=ok`). If the surface path fails *before* the launch
command is accepted, the script makes exactly one fallback attempt to create a new
*workspace* instead (logged `topology=workspace-fallback` — this is the ONLY case where
the successor is a new left-sidebar entry rather than a top tab); after that, manual.
Act on its exit code:

- **Exit 0** — spawned AND the readiness token was received (`handshake=ok`), or
  `--dry-run` completed. Report the surface ref (the tab) and the launch mode
  (`auto` = unattended non-interactive pickup; `picker-manual` = the successor opened
  the interactive picker (at exit 0 that picker has already been completed — see below) —
  the spawn notification fires either way and does not name the mode).
  Exit 0 means success: the handshake already succeeded (`handshake=ok`), so a
  `picker-manual` launch means the attended picker was used AND completed — the child
  booted and the pickup is running. Nothing further is required of the user here; the
  "picker still unfinished" case cannot surface at exit 0 (that is **exit 3
  `handshake=timeout`**, handled by its own branch). Since the notification doesn't name
  the mode, still tell the user which launch mode occurred.
- **Exit 3** — manual fallback (or a retryable refusal). The cause is in the printed
  `[spawn-handoff]` message and, for most causes, a `reason=`/`handshake=` field in the
  spawn log. The causes:
  - **not in a reachable cmux workspace** — no `CMUX_WORKSPACE_ID`, or `cmux ping` ≠ `PONG`.
    (This branch cannot notify — `cmux notify` is the very transport that just failed.)
  - **`reason=policy-off`** — the manifest sets `spawn_policy=off`; auto-spawn is disabled
    for this plan. Resume manually.
  - **`reason=policy-ask`** — the manifest sets `spawn_policy=ask` and you did not pass
    `--user-approved`. **This is RETRYABLE and consumed no hop**: ASK THE USER, then
    re-run `spawn-handoff-session.sh <bundle-id> --user-approved`.
  - **`reason=stall`** — too many consecutive zero-progress hops (the message reports
    `tasks X/Y, hops N`). If the chain is legitimately slow, raise the limit **via inline
    env on the spawn invocation** — `SUPERPOWERS_CMUX_MAX_STALL_HOPS=2 spawn-handoff-session.sh <bundle-id>`
    — then re-run. `settings.local.json` is NOT read by a running session.
  - **hop ceiling reached** — `HOPS ≥ ceiling`. The runaway guard fired; resume manually.
  - **quota low** — session quota below `SUPERPOWERS_CMUX_QUOTA_MIN_PCT` (default 15%).
    Resume manually (or wait for quota to recover), then re-run.
  - **malformed hop counter** — `.handoff-hops` holds a non-integer. The runaway guard
    fails CLOSED rather than bypass itself: repair the file (a single non-negative integer)
    or delete it to reset the chain to 0, then re-run.
  - **reservation write failed** — the hop counter or the intent record could not be
    written (two sites, one cause). Nothing was spawned; these branches deliberately do
    NOT notify — the exit code plus the printed manual instructions carry it.
  - **spawn failed after reservation** — the hop was consumed but no successor could be
    launched. Notifies.
  - **`handshake=timeout`** — a successor WAS launched (the hop is spent) but no readiness
    token arrived within the wait (one bounded wait + one re-wait). The log carries a
    `diagnosis=` field from a screen scrape (`trust-dialog`, `banner`, `picker-error`,
    `unreadable`, `none`). **For `trust-dialog` or `banner`: GO TO THE EXISTING TAB and
    finish it there — never start a fresh session.** A spawn happened; a second one is a
    double-spawn. Only after inspecting that tab should you fall back to manual resume.

  For every exit-3 cause the script prints the manual resume instructions (start a fresh
  session from the worktree, run `/pickup <bundle-id>`) — except the two silent reservation
  branches and the policy refusals, which print their own guidance. Relay what it printed.
- **Exit 1** — refused (bad args, not a git repo, missing/invalid `.active-feature`, dirty
  tree, or bundle validation failed). Fix the printed precondition and re-run the script.
  The usual dirty-tree cause is **this** blocked task's own bookkeeping — the
  `reports/checkpoint-pre-dispatch-NNN.json` and `reports/partner-review-NNN.md`
  written before the dispatch that got blocked. Step 2's "its reports under
  `reports/`" reads as the *completed* task's; commit **all** of `reports/`,
  including the blocked task's own files.

  *N64 — the successor's clean-tree precondition:* a SUCCESSFUL spawn commits its own
  bookkeeping (`.handoff-hops`, `handoff-spawn.log`, `handoff-mechanics.md`) with the
  message `chore(sdd): record handoff hop N`, so the successor does not trip its own
  clean-tree check on the hop that spawned it. If you pass `--no-commit`, those artifacts
  are left uncommitted and **the successor's step-2 commit must fold them in** — otherwise
  the next hop's clean-tree precondition refuses.

**5. STOP.** Do not dispatch the next task in this session.

**Why a block, not just advice:** a context-heavy controller is exactly the one
that rationalizes "just one more task." The hook removes the choice at the
boundary. The block guarantees the next task will not dispatch here; the *clean*
handoff still depends on you following steps 2–5.

**A soft nudge** (context ≥ soft, < hard) is the same guidance offered earlier,
without the stop — handing off at the nudge is preferred to waiting for the block.
The **same** `spawn-handoff-session.sh` serves it: build the bundle early (step 3)
and run the script (step 4) at the nudge rather than pushing to the block.

---

## Post-spawn setup: the `/rename` + `/rc` recipe

After `handshake=ok`, the script runs two cosmetic setup steps in the successor tab
(controlled by `SUPERPOWERS_CMUX_POST_SPAWN`, default `rename,rc`; an empty value disables
both). Each is best-effort — a failure only WARNs (`post_spawn=partial:<step>`) and never
changes the exit code, because the successor is already alive.

- **`/rename`** sets the phone-visible session name to the tab title. The script sends
  `/rename <title>`, presses Enter, and verifies the screen shows `Session renamed to: <title>`.
- **`/rc`** turns on remote control. The script sends `/rc`, presses Enter, and verifies
  the screen shows `/remote-control is active`.

To redo either by hand against the successor's surface ref (from the spawn log's
`surface=` field):

    cmux send --surface <surface-ref> "/rename <title>"
    cmux send-key --surface <surface-ref> enter
    # then verify the screen shows: Session renamed to: <title>

    cmux send --surface <surface-ref> "/rc"
    cmux send-key --surface <surface-ref> enter
    # then verify the screen shows: /remote-control is active

**`--session-label` is telemetry; `/rename` is the phone-visible session name.** The
successor command carries a `--session-label` derived from the parent's label — that name
is for telemetry attribution, not the app. The name you see in the Claude phone app is the
one `/rename` sets. They are different mechanisms; do not conflate them.

**`settings.local.json` is NOT read by a running session.** A settings file cannot change
the behavior of a session that is already up, and `cmux send` delivers a shell line, not an
environment. To change any knob for the successor, set it as **inline env on the spawn
invocation** — the script forwards the `SUPERPOWERS_CMUX_*` knobs it sees into the successor
command's `export …;` prefix.

## Env knobs (defaults)

All follow the validate-warn-revert convention: an invalid value WARNs to stderr and
reverts to the default (it never exits).

- **`SUPERPOWERS_CMUX_MAX_HOPS`** — the hop ceiling. Default is DERIVED: `max(6, 2 × expected_hops)`
  from the manifest (falls back to `6` when `expected_hops` is unknown). An explicit valid
  value overrides the derivation absolutely; `0` is a valid "refuse everything" setting.
- **`SUPERPOWERS_CMUX_MAX_STALL_HOPS`** — consecutive zero-progress hops tolerated before a
  `reason=stall` refusal. Default `1`.
- **`SUPERPOWERS_CMUX_SPAWN_WAIT_TIMEOUT`** — seconds to wait for the successor's readiness
  token (per wait; the script does one wait + one re-wait). Default `60`. Provenance: this is
  the spec floor. Task 0 measured 8–11s cold start; the derivation `max(60, 2 × 11)` = 60, so
  the floor dominates (60 was NOT itself measured). Pinned to
  `tests/unit/fixtures/spawn-handoff/cold-start-timing.json` by the unit suite.
- **`SUPERPOWERS_CMUX_POST_SPAWN`** — post-handshake setup steps. Default `rename,rc`; the
  empty string disables both (an explicit empty value is respected, distinct from unset).
  Order is canonicalized to `/rc` last, duplicates collapsed.
- **`SUPERPOWERS_CMUX_TITLE_FORMAT`** — the successor tab title. Default `hop{hop} SDD {feature}`;
  `{hop}` and `{feature}` are substituted at spawn time. An empty value reverts to the default.
- **`SUPERPOWERS_CMUX_QUOTA_MIN_PCT`** — session-quota refusal threshold (may be fractional).
  Default `15`.
- **`SUPERPOWERS_CMUX_QUOTA_TIMEOUT`** — seconds bounding the quota tool. Default `60`.
- **`SUPERPOWERS_CMUX_QUOTA_TOOL`** — the quota binary. Default `$HOME/.claude/bin/claude-usage-pace`
  (an explicit override is authoritative — a bad override classifies `unchecked`, it never
  silently falls back).
- **`SUPERPOWERS_CMUX_AUTOSPAWN`** — the plan-less, per-run kill switch. Default enabled. Set to `0`/`false` to disable auto-spawn entirely: the script exits 3 with `reason=autospawn-disabled` at **Precondition 0** (before the cmux-reachability probe), and you resume manually. Invalid values warn and leave it enabled. Complementary to the plan-level `handoff_spawn: off` (durable) — this is the per-run opt-out.

## The mechanics card (`reports/handoff-mechanics.md`)

On a successful spawn the script also generates a **mechanics card** at
`reports/handoff-mechanics.md` — everything a fresh SDD controller needs for its first
checkpoint: the exact `controller-checkpoint.py` pre-dispatch and pre-completion invocations
(absolute paths, `--manifest`); manifest/plan/module/deviations paths; hop state
(used / expected / ceiling); the last `context-observations.log` line and the Check 6b
midpoint status; the last spawn outcome (workspace/surface refs); the `/rename`+`/rc` recipe
pointer; and a `validate-report.py`-clean implementer-report skeleton. It is committed with
the hop bookkeeping (N64).

On the **manual-fallback path** the card is not generated for you — regenerate it standalone:

    $PYTHON ~/.claude/skills/superpowers/subagent-driven-development/scripts/write-mechanics-card.py --manifest <feature-dir>/.sdd-session.json

Here `$PYTHON` is the superpowers **venv** interpreter (`$SUPERPOWERS_ROOT/.venv/bin/python3`) —
`$PYTHON` is a hook-internal variable and is NOT defined in an interactive/agent shell, so
substitute that venv python if it is unset. The card needs PyYAML + pydantic; a plain
`python3` lacks them and exits 2. The `~/.claude/...` path shown above is already the
standalone form to run.

## Recording a decline

If a `/handoff` bundle was built this session but you deliberately do NOT spawn (you resumed
by hand, or the run is being abandoned), record a `decline` so the stop hook does not WARN
about an unspawned bundle:

    printf '%s - decline bundle=%s reason=<word>\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" <bundle-id> >> reports/handoff-spawn.log
