# Deviations Register

> Auto-maintained by controller during subagent-driven-development execution.
> Review all entries before merge.

| Task | Type | Description | Disposition |
|------|------|-------------|-------------|
| Ingestion | ScopeChange | Parent `plan.md` frontmatter had `tasks: []`; `materialize-manifest.py` requires a non-empty flat `tasks:` list even for modular plans (guard at line 112 precedes the modules block). Populated the flat list with all 9 tasks (id+title) to match the established modular convention shown in `tests/integration/sdd-e2e-test.sh` (which lists tasks flat AND in modules). No `review_tier` added (field not in model until Task 1). | Accepted |
| Ingestion | ProcessNote | Run executed with `subagent_type: general-purpose` per user decision. Live main-checkout hook passes general-purpose dispatches through (Item-1 bug being fixed), so hook enforcement is a no-op this run; controller runs `controller-checkpoint.py` manually at each phase and dispatches all spec+quality reviews by hand. Worktree isolation confirmed: live hook = main checkout, not worktree. | Accepted |
| Pre-exec checkpoint | ToolFalsePositive | `controller-checkpoint.py --phase pre-execution` reports BLOCKER `source_contracts` FAIL on "Source Contracts: None". Documented false positive (CLAUDE.md): `validate-plan.py` accepts "None" (PASSed); the checkpoint treats the literal "None" as non-empty content. The `writing-plans` skill requires the section present and "None" is the correct value (this feature has no external contracts). Tool-improvement opportunity: checkpoint should treat "None" as valid no-contracts, matching validate-plan.py. Not patched (out of scope; untested mid-run change to enforcement system). | Accepted |
| Pre-exec checkpoint | ToolFalsePositive | `stale_artifacts` WARNING (non-blocking) flags this session's own ingestion artifacts (deviations.md content + the 2 pre-execution-audit files just created) as "prior session" artifacts. Verified: no uppercase DEVIATIONS.md exists; workspace was clean (self-assessment Q8); baseline was 328 green. Inherent ordering tension — the audit must exist before dispatch but the check assumes reports/ empty at pre-execution. | Accepted |

## Deferred Work
[Items deferred from plan scope]

## Independent Decisions
[Decisions made by subagents without plan guidance]

## Scope Changes
[Requirements that changed during execution]
