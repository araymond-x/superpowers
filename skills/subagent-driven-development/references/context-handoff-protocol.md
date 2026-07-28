# Context Handoff Protocol (controller block-response)

The pre-dispatch hook has BLOCKED the next new-task implementer dispatch. The
usual cause is context pressure: the controller's context reached the hard
threshold (default 400k tokens) at a clean task boundary — the previous task is
reviewed and at a clean boundary. Follow this protocol. Do NOT improvise. (A
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

*What must already be true:* a **clean tree**, an existing **`.active-feature`**, and a
`/handoff` bundle of type `work` whose entry skill is
`superpowers:subagent-driven-development`, in this same repo. Any of these missing → exit 1
with the cause printed. Fix and re-run; nothing was consumed.

*What the session must be:* launched via **`claude-picker`, inside cmux**. That is not
ceremony — the picker exports `CLAUDE_CODE_PICKER_VERSION`, `_ARGS`, `_LABEL` and
`_APPEND_PROMPT`, and those four ARE the input to the successor command. cmux supplies
`CMUX_WORKSPACE_ID`.

*The failure that does not look like one:* if any picker variable is missing (or its
version file isn't executable, or the picker isn't on PATH, or its `--handoff-contract`
probe doesn't return `1`), the script **does not error**. It falls back to
`launch=picker-manual`, drops `--non-interactive`, **exits 0**, and reports a spawned
successor — but that successor sits on an interactive menu until a human finishes it. The
notification does not mention the mode. **Read the `launch=` value; do not infer success
from exit 0.** A plain terminal, or any non-picker session, degrades this way by default.

*Hop budget:* `.handoff-hops` lives in the ACTIVE FEATURE's `reports/` dir, so it is
**per-feature**, not global — a different project starts fresh at 0. Default limit 3
(`SUPERPOWERS_CMUX_MAX_HOPS`). Sibling knobs: `SUPERPOWERS_CMUX_QUOTA_MIN_PCT` (default 15),
`_QUOTA_TIMEOUT` (60), `_QUOTA_TOOL`. Every spawn attempt is recorded in
`reports/handoff-spawn.log` — check it first when diagnosing.

**4. Spawn the successor (or fall back).** Run:

    ~/.claude/skills/superpowers/subagent-driven-development/scripts/spawn-handoff-session.sh <bundle-id>

The script verifies the clean tree, validates the bundle, checks cmux reachability,
the hop limit, and session quota, then spawns the successor in a new cmux workspace
through the extended claude-picker. Act on its exit code:

- **Exit 0** — spawned. Report the workspace ref and launch mode (`auto` =
  unattended non-interactive pickup; `picker-manual` = the workspace opened the
  interactive picker and a human must complete it there before the pickup
  runs — the spawn notification fires either way and does not name the mode).
  **If `picker-manual`, tell the user in so many words that they must go finish
  the picker in that workspace or the successor never starts** — the
  notification will not tell them. Otherwise nothing more to do here.
- **Exit 3** — manual fallback (not in a cmux workspace, hop limit reached, quota
  low, a reservation write failed, or spawn failed after reservation). Relay the
  manual resume instructions the script printed (start a fresh session from the
  worktree, run `/pickup <bundle-id>`).
- **Exit 1** — refused (dirty tree, bundle validation failed, or missing
  `.active-feature`). Fix the printed precondition and re-run the script. The
  usual dirty-tree cause is **this** blocked task's own bookkeeping — the
  `reports/checkpoint-pre-dispatch-NNN.json` and `reports/partner-review-NNN.md`
  written before the dispatch that got blocked. Step 2's "its reports under
  `reports/`" reads as the *completed* task's; commit **all** of `reports/`,
  including the blocked task's own files.

**5. STOP.** Do not dispatch the next task in this session.

**Why a block, not just advice:** a context-heavy controller is exactly the one
that rationalizes "just one more task." The hook removes the choice at the
boundary. The block guarantees the next task will not dispatch here; the *clean*
handoff still depends on you following steps 2–5.

**A soft nudge** (context ≥ soft, < hard) is the same guidance offered earlier,
without the stop — handing off at the nudge is preferred to waiting for the block.

**Soft-nudge use:** handing off at the soft nudge (context ≥ soft, < hard) is
preferred to waiting for the hard block, and the **same** `spawn-handoff-session.sh`
serves it — build the bundle early (step 3) and run the script (step 4) at the
nudge rather than pushing to the block.
