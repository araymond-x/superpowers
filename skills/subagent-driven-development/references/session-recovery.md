# Session Recovery

> Part of the subagent-driven-development skill. Referenced from SKILL.md.

If a controller session is interrupted (context overflow, crash, or manual stop), a new session can resume execution by:

1. **Read the plan file** -- checked-off checkboxes show what was completed
2. **Read DEVIATIONS.md** -- shows accumulated drift and pending dispositions
3. **Read `reports/` directory** -- shows detailed implementer and reviewer output for each completed task
4. **Read TodoWrite** (if still in session) or reconstruct from plan checkboxes
5. **Resume from the first unchecked task** -- all prior context is in files

This is why file-based persistence matters: the plan file, DEVIATIONS.md, and `reports/` directory together form a complete execution log that survives session loss.
