# Advantages

> Part of the Subagent-Driven Development skill (`skills/subagent-driven-development/SKILL.md`).
> Comparison against manual execution and executing-plans.

**vs. Manual execution:**
- Subagents follow TDD naturally
- Fresh context per task (no confusion)
- Parallel-safe (subagents don't interfere)
- Subagent can ask questions (before AND during work)

**vs. Executing Plans:**
- Same session (no handoff)
- Continuous progress (no waiting)
- Review checkpoints automatic

**Efficiency gains:**
- No file reading overhead (controller provides full text)
- Controller curates exactly what context is needed
- Subagent gets complete information upfront
- Questions surfaced before work begins (not after)

**Quality gates:**
- Plan ingestion catches contract mismatches before implementation begins
- Task 0 verifies contract assumptions before any code is written
- DEVIATIONS.md surfaces accumulated drift before it reaches merge
- Self-review catches issues before handoff
- Two-stage review: spec compliance, then code quality
- Review loops ensure fixes actually work
- Spec compliance prevents over/under-building
- Code quality ensures implementation is well-built
- Pre-Completion Gate prevents silent gaps from reaching finishing

**Cost:**
- More subagent invocations (implementer + 2 reviewers per task)
- Controller does more prep work (full plan ingestion, source file reading)
- Review loops add iterations
- But catches issues early (cheaper than debugging later)
- Plan ingestion cost is fixed and front-loaded; bugs found in ingestion cost less than bugs found in review or production
