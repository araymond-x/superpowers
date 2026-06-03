---
name: honesty
description: Honesty check — surface skipped steps, shortcuts, and unflagged uncertainties in the current session, then prioritize remediation
---

Be completely honest about the work in this session. Answer each question directly and specifically — cite the actual files, tasks, commands, or steps involved, not generalities. If the honest answer is "yes I cut a corner" or "I'm not sure," say so plainly:

1. Did you skip any step that the task — or your own stated plan/approach — required? List each one.
2. Were you blocked by any check, hook, test, linter, type checker, or gate at any point? What happened, and how did you resolve it — did you fix the root cause, or work around the symptom?
3. Did you take any shortcuts to save time or tokens that deviated from the process you should have followed?
4. Is there anything in the code or output you're uncertain about that you have NOT explicitly flagged to me?
5. Did you verify behavior against reality — actually ran the code, ran the tests, checked the output, inspected the real data — or are you trusting that it "should work"?
6. What did you defer or leave incomplete, and is it genuinely acceptable to leave until later?
7. If you were a skeptical code reviewer looking at this work, what would concern you most — and what is the single weakest part of your reasoning?

After answering, give me a prioritized remediation recommendation grouped by:

- **High** — must be addressed before this work is considered complete
- **Medium** — reduces tech debt; should be scheduled soon
- **Low** — hygiene improvements, no immediate risk
- **Inform** — context I should be aware of, no action needed
- **Warning** — risks or patterns that could cause problems in future work if left unaddressed

For each item, state what was found, which file or task it relates to, and the recommended action. Present this recommendation to me before taking any action.
