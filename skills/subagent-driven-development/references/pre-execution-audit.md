# Pre-Execution Audit (Mandatory)

> Part of the Subagent-Driven Development skill (`skills/subagent-driven-development/SKILL.md`).
> The pre-execution audit is hook-enforced: the SDD enforcement hook blocks all task dispatches until `<feature-dir>/reports/pre-execution-audit.md` exists with substantive content. The detailed steps below describe how to satisfy that gate.

Before dispatching any task, complete the self-assessment and audit gate. The SDD enforcement hook blocks all task dispatches until `<feature-dir>/reports/pre-execution-audit.md` exists with substantive content.

**Step 1: Write the self-assessment.**
Save to `<feature-dir>/reports/pre-execution-audit-self-assessment.md`. Answer every question honestly — the auditor will cross-reference your answers against the actual artifacts.

1. Did you follow every step of each skill used before this point? List any steps you skipped and why.
2. Did you dispatch all required reviewer subagents? If you batched or skipped any, state which and why.
3. Did you re-dispatch reviewers after fixing issues they found?
4. Are there any type ambiguities in the plan that you're uncertain about? List each with the specific fields.
5. Are there any plan sections where you wrote code quickly and aren't confident in the logic? List each.
6. Are there any implicit assumptions in the plan that an implementer might miss? List each.
7. What is the single highest-risk item in this plan?
8. Were stale SDD artifacts found in the workspace from a prior session? If so, what was found and how were they archived? (FYI — not a blocker, but the auditor needs to know the workspace was reused.)

**Step 2: Dispatch the pre-execution auditor.**
See `pre-execution-audit-prompt.md` for the dispatch template. Provide: your self-assessment, all plan file paths, the distilled spec path, and the Contract Constraints.

**Step 3: Address remediation orders.**
If the auditor issues ORDERS_ISSUED: address every order. For each order, document the resolution in `<feature-dir>/reports/pre-execution-audit.md` with:
- Order #, finding, and what you did to fix it
- RESOLVED status

If the auditor returns CLEAR: write `<feature-dir>/reports/pre-execution-audit.md` with the audit verdict and proceed.

The pre-execution audit report must exist before any task dispatch. This is enforced by the hook — not optional.
