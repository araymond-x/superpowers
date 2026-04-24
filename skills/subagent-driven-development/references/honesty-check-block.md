# Honesty Check Block

> Part of the subagent-driven-development skill. Referenced from SKILL.md.
> Also available as `./honesty-check-prompt.md` for dispatch.

Before running the Pre-Completion Gate, present this prompt to the user and STOP. Wait for the user to copy it back to you. Do not self-answer these questions — the user must deliver them.

Output this block exactly:

```
════════════════════════════════════════════════════════════════
 HONESTY CHECK — Please paste this back to me:

 Be completely honest about the work in this session:

 1. Did you invoke superpowers:subagent-driven-development via
    the Skill tool, or did you implement directly without
    loading the skill?
 2. Did you skip any steps that the SDD skill requires? List
    each skipped step.
 3. Were you blocked by any hooks at any point? If so, what
    happened and how did you resolve it?
 4. Did you dispatch spec compliance AND code quality reviews
    for every task? If not, which tasks were unreviewed?
 5. Is there anything you're uncertain about in the code that
    you didn't flag in DEVIATIONS.md?
 6. Did you take any shortcuts to save time or tokens?
 7. If you were the code reviewer, what would concern you most?
 8. Did you dispatch the controller partner before every
    implementer dispatch? If you used minimum-tier exemptions,
    list which tasks and your rationale.
 9. Did the partner return BLOCKED at any point? If so, for each:
    - What findings did it raise?
    - Did you make substantive changes to the dispatch, or only
      cosmetic edits to pass re-review?
    - Did you re-dispatch the partner to verify the fixes, or
      proceed directly to the implementer?
════════════════════════════════════════════════════════════════
```

After answering honestly:
1. Save the complete response to `reports/honesty-check-YYYY-MM-DD.md` (required by the pre-completion gate).
2. Add any uncertainties from answers 5-9 to DEVIATIONS.md as "Pending — needs review."
3. Proceed to the Pre-Completion Gate.
