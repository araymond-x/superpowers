## Planning disposition for cmux-spawn-v2-remediation

This is a SMALL, well-scoped remediation — edits to a handful of skill docs, two
Pydantic models, two hook scripts, and one card generator. It is NOT a greenfield
feature. Match the plan's weight to the size of the change.

RIGHT-SIZE, don't inflate:
- The spec's 4-module structure is a CEILING, not an invitation to decompose further.
  Prefer fewer, well-bounded tasks over many small ones.
- Use `review_tier: minimum` for the pure-documentation tasks (SKILL.md edits, the
  "Declaring handoff_spawn" author section, the env-registry doc updates). Reserve full
  spec+quality review for the three tasks that actually carry risk: the N83 model-boundary
  coercion (plan.py + sdd_session.py + materialize), the SUPERPOWERS_CMUX_AUTOSPAWN
  precondition-0, and the baselined-hook changes (N84/N86 in sdd-stop-hook.sh).
- Do NOT expand into the fenced-out cmux capability backlog (N56/N58/N60/N64/N66-N74/N51)
  or change the default VALUE (auto stays auto). The spec's "Out of scope" list is binding.

These are NOT overthinking — do them fully (a lean plan is not a corner-cutting plan):
- Verify the N83 coercion per reader (validate-plan.py, materialize, the script), with a
  positive control (`handoff_spawn: on` rejected) and a negative control (quoted "off").
- Offset every SKILL.md addition by extracting existing content to references/ FIRST
  (the bodies are near the 5000-word ceiling; the regression test enforces it).
- Re-capture the hook baseline in the SAME commit as any baselined-hook edit.

When in doubt, the smaller plan that still satisfies the acceptance criteria is the right one.
