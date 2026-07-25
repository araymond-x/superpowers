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

**4. Spawn the successor (or fall back).** Run:

    ~/.claude/skills/superpowers/subagent-driven-development/scripts/spawn-handoff-session.sh <bundle-id>

The script verifies the clean tree, validates the bundle, checks cmux reachability,
the hop limit, and session quota, then spawns the successor in a new cmux workspace
through the extended claude-picker. Act on its exit code:

- **Exit 0** — spawned. Report the workspace ref and launch mode (`auto` =
  unattended non-interactive pickup; `picker-manual` = the workspace opened the
  interactive picker and a human must complete it there before the pickup
  runs — the spawn notification fires either way and does not name the mode).
  Nothing more to do here.
- **Exit 3** — manual fallback (not in a cmux workspace, hop limit reached, quota
  low, a reservation write failed, or spawn failed after reservation). Relay the
  manual resume instructions the script printed (start a fresh session from the
  worktree, run `/pickup <bundle-id>`).
- **Exit 1** — refused (dirty tree, bundle validation failed, or missing
  `.active-feature`). Fix the printed precondition and re-run the script.

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
