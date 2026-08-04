### Strengths
- Diff is minimal and single-file — exactly the two additions the spec called for (step 3.6 + one Rule 4 sentence), no incidental restructuring of surrounding checklist items.
- Prompt text and format (own message, blockquote, "press enter to accept default") match the adjacent step 3.5 feature-name prompt's tone precisely.
- The `handoff_spawn: <auto|ask|off>` field name and value set are identical between the step 3.6 instruction and the Rule 4 sentence — the data path traces cleanly end to end within this task's scope.
- Explicitly names the carrier mechanism precedent (`entry_mode` / `enforcement_tier`) rather than inventing new plumbing.
- `not_applicable` disposition on the unquoted/quotable constraint correctly reasoned — deferred to Task 5 where it belongs.
- Numbering (`3.6.` between `3.5.` and `4.`) is consistent with the file's existing convention.

### Issues

#### Critical (Must Fix)
None.

#### Important (Should Fix)
None.

#### Minor (Nice to Have)
- Step 3.6's lead-in sentence compresses a two-hop journey (brainstorming records in spec → Task 5 materializes into plan frontmatter) into one clause — terse but resolved by the following parenthetical on a second read. Polish, not a blocking ambiguity.
- The blockquote in step 3.6 contains a markdown bullet list inside it — some renderers may flatten bullets inside blockquotes. Worth a visual check in cmux-markdown someday; content is unambiguous either way since each bullet is bold-prefixed.

### Recommendations
No changes required before merge.

### Assessment

**Ready to merge?** Yes

**Reasoning:** Faithful, minimal, single-responsibility implementation of Task 4's spec — correct placement, correct field/value-set alignment with the Contract Facts consumer, no duplication of existing carrier machinery, no dead or stale prose. Only cosmetic polish items found.
