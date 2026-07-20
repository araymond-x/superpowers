# Honesty Check Block

> Part of the subagent-driven-development skill. Referenced from SKILL.md.
> Also available as `./honesty-check-prompt.md` for dispatch.

Before running the Pre-Completion Gate, output this block exactly and STOP. Wait for the user to paste the questions back to you in a new message. When the user pastes them back, answer each question honestly based on what actually happened in this session. Do not answer the questions preemptively — wait for the user to deliver them.

Output this block exactly:

```
════════════════════════════════════════════════════════════════
 HONESTY CHECK — Copy the questions below and paste them back
 to me in your next message. I will answer them honestly.

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
    you didn't flag in deviations.md?
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
10. Save the COMPLETE, VERBATIM output of your answers to
    questions 1-9 above to this feature's
    `reports/honesty-check-<YYYY-MM-DD>.md` (add a `-module-N`
    suffix if you run more than one in a day). Do not
    summarize, paraphrase, or omit any part of your responses.

 After saving, prepare a remediation recommendation grouped by:
 - High-priority: Must address before declaring feature complete.
 - Medium-priority: Reduces tech debt; schedule soon.
 - Low-priority: Hygiene improvements, no immediate risk.
 - Inform: Context requiring no action.
 - Warning: Risks that could cause problems in future work.

 For each item, state what was found, which task or file it
 relates to, and the recommended action. Present to the user
 before taking action.
════════════════════════════════════════════════════════════════
```

After answering honestly:
1. Save the complete response to `reports/honesty-check-<YYYY-MM-DD>.md` — add a `-module-N` or `-session-N` suffix if you run more than one honesty check in a day (required by the pre-completion gate, which matches `honesty-check-*.md`; the undated `honesty-check.md` is rejected).
2. Prepare the prioritized remediation recommendation and present to the user.
3. Add any uncertainties from answers 5-9 to deviations.md as "Pending — needs review."
4. Proceed to the Pre-Completion Gate.
