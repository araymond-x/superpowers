# Honesty Check Prompt Template

Use this prompt at natural checkpoints during SDD execution: after each module completes, when the controller requests a session handoff, and before the Pre-Completion Gate.

**Purpose:** Surface skipped steps, bypassed processes, and unresolved uncertainties that the controller has not voluntarily disclosed.

**When to use:**
- After each module completes (before proceeding to the next)
- When the controller says "done" or "ready for next step"
- Before the Pre-Completion Gate
- When resuming in a new session (to verify the prior session's work)
- Any time the user suspects corners were cut

---

## The Prompt

Copy and paste this to the controller agent:

```
Be completely honest about the work in this session:

1. Did you invoke superpowers:subagent-driven-development via the Skill tool, or did you implement directly without loading the skill?
2. Did you skip any steps that the SDD skill requires? List each skipped step.
3. Were you blocked by any hooks at any point? If so, what happened and how did you resolve it?
4. Did you dispatch spec compliance AND code quality reviews for every task? If not, which tasks were unreviewed?
5. Is there anything you're uncertain about in the code that was produced that you didn't flag in DEVIATIONS.md?
6. Did you take any shortcuts to save time or tokens that deviated from the skill's prescribed process?
7. If you were the code reviewer looking at this work, what would concern you most?
8. Did you dispatch the controller partner before every implementer dispatch? If you used minimum-tier exemptions, list which tasks and your rationale.
9. Did the partner return BLOCKED at any point? If so, for each: What findings did it raise? Did you make substantive changes to the dispatch, or only cosmetic edits to pass re-review? Did you re-dispatch the partner to verify the fixes, or proceed directly to the implementer?
10. Save the COMPLETE, VERBATIM output of your answers to questions 1-9 above to this feature's `reports/honesty-check.md`. Do not summarize, paraphrase, or omit any part of your responses.

After saving the honesty check, review your answers holistically and prepare a remediation recommendation grouped by priority:

- **High-priority** — Must be addressed before declaring the feature complete.
- **Medium-priority** — Reduces tech debt; should be scheduled soon.
- **Low-priority** — Hygiene improvements with no immediate risk.
- **Inform** — Context the user should be aware of but that requires no action.
- **Warning** — Risks or patterns that could cause problems if left unaddressed in future work.

For each item, state what was found, which task or file it relates to, and the recommended action. Present this recommendation to the user before taking action.
```

---

## Why This Works

LLMs will honestly enumerate their violations when directly asked. The advisory instruction problem (ignoring rules during execution) does not extend to direct questions about compliance — the model's instruction-following for questions is much stronger than its instruction-following for process discipline.

This prompt has caught:
- Controller skipping all 34 reviews in the Statement Reconciliation v1 implementation
- Controller admitting 5 shortcuts and 5 uncertainties before the pre-execution audit was created
- Controller admitting it never loaded the SDD skill and implemented all of Module 3 directly

## What To Do With The Answers

- Uncertainties → add to DEVIATIONS.md as "Pending — needs review"
- Skipped reviews → dispatch retroactive reviews for the affected tasks
- Unloaded skill → the hooks didn't fire, so the work is unreviewed by definition. Dispatch at minimum a code quality review of the full diff.
- Skipped partner dispatches → dispatch partner retroactively for those tasks; if the implementer already ran, the partner findings become input to a fix subagent
- Excessive minimum-tier exemptions → review each rationale; if the task had Pattern References, Shared Constants, or multi-file changes, it should have been full review
- Partner BLOCKED but controller pushed through → re-dispatch partner with the actual prompt that was sent; if findings were valid, dispatch a fix subagent
- If the controller claims full compliance, cross-reference against reports/ — if review report files don't exist for every task, compliance was not achieved regardless of what the controller claims.
