# Context Handoff Protocol (controller block-response)

The pre-dispatch hook has BLOCKED the next new-task implementer dispatch because
the controller's context reached the hard threshold (default 400k tokens). This
is a deterministic stop at a clean task boundary — the previous task is fully
committed and reviewed. Follow this protocol. Do NOT improvise.

**1. This is NOT a fix-and-retry.** Retrying the dispatch is wrong — the block
is not caused by a missing report or a failed review. Do not edit files to "get
past" it, and do not set `SUPERPOWERS_CTX_HANDOFF_BYPASS` unless you have a
specific reason to run without the gate (a diagnosed probe fault). The correct
response is to hand off, not to push through.

**2. Commit pending state.** Ensure the completed task's code, its reports under
`reports/`, updated plan checkboxes, and `deviations.md` are all committed. The
fresh session resumes from committed state only.

**3. Build the fresh-session handoff.** Invoke the `handoff` skill to create a
bundle whose entry skill is `superpowers:subagent-driven-development` (the N39
flow). The bundle captures the goal, the plan/manifest, and next-action context.

**4. Tell the user how to resume.** Instruct them to start a FRESH session FROM
the worktree (so the enforcement hooks bind to the worktree CWD) and run
`/pickup`. The new session invokes SDD via the entry skill and resumes mid-plan
per `references/session-recovery.md` (plan checkboxes + `deviations.md` +
`reports/` → first unchecked task).

**5. STOP.** Do not dispatch the next task in this session.

**Why a block, not just advice:** a context-heavy controller is exactly the one
that rationalizes "just one more task." The hook removes the choice at the
boundary. The block guarantees the next task will not dispatch here; the *clean*
handoff still depends on you following steps 2–5.

**A soft nudge** (context ≥ soft, < hard) is the same guidance offered earlier,
without the stop — handing off at the nudge is preferred to waiting for the block.
