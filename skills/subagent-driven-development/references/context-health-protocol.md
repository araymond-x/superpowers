# Context Health Protocol

As the controller processes tasks, its own context accumulates. After 5+ tasks, the controller's context may be heavy enough to degrade decision quality — the exact failure mode that caused review-skipping in a prior incident.

**Signs of context pressure:**
- You feel the urge to "simplify" or "speed up" — this is often context fatigue, not efficiency
- You start summarizing instead of quoting — precision loss indicates context strain
- You skip reading a report and trust the status code — this is how deviations go unlogged

**When the checkpoint script warns about context load (>400KB accumulated):**

1. Run the context summary script:
   ```bash
   python ~/.claude/skills/superpowers/subagent-driven-development/scripts/context-summary.py --reports-dir reports/ --deviations-file DEVIATIONS.md --output reports/context-summary.md
   ```
2. Read `context-summary.md` — this is now your compressed execution state
3. You no longer need to hold individual report details in context
4. For subsequent tasks, reference `context-summary.md` instead of re-reading old reports

**At the halfway point of execution** (task count / 2), regardless of context load:
- Generate a context summary
- Review DEVIATIONS.md for accumulated drift
- Verify progress percentage matches expectations
- This is a natural checkpoint to assess whether the plan is on track or needs adjustment

**If you suspect your own context is degraded:**
- Save execution state to files (context-summary.md is sufficient)
- Report to the human: "I've completed N of M tasks. My context is heavy. Recommend continuing in a fresh session — all state is in plan checkboxes + DEVIATIONS.md + reports/."
- This is not failure — it is disciplined context management
