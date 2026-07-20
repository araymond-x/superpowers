---
name: honesty-sdd
description: SDD honesty check — verbatim subagent-driven-development accountability questions (skill invocation, reviews, partner dispatch, deviations), then prioritized remediation
---

<!--
  Canonical source: skills/subagent-driven-development/honesty-check-prompt.md
  (the dispatch version) in this same repo. If the SDD honesty questions change
  there, update this command to match. See also references/honesty-check-block.md.
-->

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
10. Save the COMPLETE, VERBATIM output of your answers to questions 1-9 above to this feature's `reports/honesty-check-<YYYY-MM-DD>.md` (append a `-module-N` or `-session-N` suffix if you run more than one honesty check in a day, so none is overwritten — the pre-completion gate and stop hook match `honesty-check-*.md`, which the undated `honesty-check.md` does not). Do not summarize, paraphrase, or omit any part of your responses.

After saving the honesty check, review your answers holistically and prepare a remediation recommendation grouped by priority:

- **High-priority** — Must be addressed before declaring the feature complete.
- **Medium-priority** — Reduces tech debt; should be scheduled soon.
- **Low-priority** — Hygiene improvements with no immediate risk.
- **Inform** — Context the user should be aware of but that requires no action.
- **Warning** — Risks or patterns that could cause problems if left unaddressed in future work.

For each item, state what was found, which task or file it relates to, and the recommended action. Present this recommendation to the user before taking action.
