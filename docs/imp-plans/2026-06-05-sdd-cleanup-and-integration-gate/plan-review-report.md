## Plan Review

**Status:** Approved (after 2 review rounds — 3 internal + 4 Codex blocking issues found and fixed)

### Blocking Issues Found (RESOLVED)

1. **[CONTRACT ACCURACY]: Task 2, Step 5 — `_task_ids_where` return unpacking**: The `_verification_task_ids` call site returns a bare `set`, but `_task_ids_where` returns `(set, bool)`. Without explicit unpacking, `verification_ids` would be a tuple, causing `TypeError` at the set intersection. **Fixed:** Added explicit unpack instruction (`verification_ids, _ = _task_ids_where(...)`).

2. **[SNIPPET SAFETY]: Task 3 — `get_task_checkbox_range` unfenced routing**: The plan said to apply `_unfenced_content` "for header search" but the test also requires fenced checkboxes to be excluded from counts. **Fixed:** Clarified that the entire function must operate on unfenced content, not just the header search.

3. **[CANONICAL NAMES]: Task 1 pattern reference file**: Plan referenced `test_implementer_report.py` but actual file is `test_implementer_report_model.py`. **Fixed:** Corrected at all 3 occurrences (parent plan, module-1 YAML, module-1 pattern references header).

### Snippet Verification

- **Snippet 1** (Task 1 — ImplementerReport `task_type` field + validator): **VERIFIED** against `implementer_report.py` L31-54.
- **Snippet 2** (Task 4 — `source_contracts` fix at L682-699): **VERIFIED** against `controller-checkpoint.py`.
- **Snippet 3** (Task 3 — `_unfenced_content` helper): **VERIFIED** as standalone. **ILLUSTRATIVE** for routing claims (implementer adapts per site).

### Size and Complexity Assessment

| Metric | Parent | Module 1 | Module 2 | Verdict |
|--------|--------|----------|----------|---------|
| Lines | 120 | ~940 | 444 | OK |
| Tasks | — | 7 (1-7) | 4 (8-11) | OK |
| Largest task | — | Task 3: ~178 lines | Task 9: ~119 lines | Under 200 |
| Task 0 | No | No | No | Consistent with spec (D9) |
| Source Contracts | None | None | None | Consistent |
| Write-Scope Partitioning | Present | Present | Present | Correct |

---

### Codex Review (Round 2) — Blocking Issues Found (RESOLVED)

4. **[BLOCKER]: Parent plan `tasks: []` blocks materialize-manifest.py**: The materializer exits with "No tasks found" when `tasks` is empty. Parent plans need all task IDs populated for the materializer to compute task ranges. **Fixed:** Added all 11 task IDs to parent frontmatter.

5. **[BLOCKER]: Test imports use invalid hyphenated module names**: Plan tests used `from controller_checkpoint import ...` but the file is `controller-checkpoint.py` (hyphen). Python can't import hyphenated filenames with standard import syntax. **Fixed:** Switched to `importlib.util.spec_from_file_location` pattern, matching existing test conventions (`test_pre_completion_gates.py:37-39`).

6. **[BLOCKER]: Task 7 `make_hook_input` wrong signature**: Plan passed `tool_name`/`tool_input` kwargs that don't exist. Actual signature: `make_hook_input(description, prompt, cwd, subagent_type)`. Also double-serialized JSON. **Fixed:** Corrected args and pass returned string directly.

7. **[BLOCKER]: Task 10 `_in_changeset` uses raw base ref, not merge-base**: `git diff --name-only <base> -- <path>` includes unrelated base-branch drift. **Fixed:** Added merge-base computation (`git merge-base <ref> HEAD`) to isolate feature changes.

### Codex Review — Other Findings (advisory, accepted)

- **Major 1-2 (stub test bodies for Tasks 5/6/10):** Acknowledged. Pattern references point to existing test files with the exact workspace patterns. TDD backstops any gaps.
- **Major 3 (N16 validate-report CLI fixture):** **Fixed:** Added Step 7 to Task 1 — write a complete markdown report file and validate via CLI.
- **Minor 1 (Task 3 vs Task 2 for N9):** **Fixed** in parent plan.
- **Minor 2 (validate-report.py scope):** **Fixed** — reclassified as read-only, removed from write scope.
- **Nit 1 ("Write 4 tests" → 6):** **Fixed**.

### Recommendations (advisory)

1. **SDD SKILL.md word ceiling**: Currently at 4904 words; Task 1 adds ~15. Plan's `wc -w` self-check is correct practice.
2. **Test style**: Plan uses `pytest.raises(ValueError)` while codebase uses `ValidationError`. Consider consistency.
3. **Task 5/6 test bodies are stubs**: Pattern-reference pointers to `test_transition_module.py` are sufficient mitigation.
4. **Task 10 `_run` helper is fully stubbed**: Pointer to `test_pre_completion_gates.py` patterns is sufficient but highest-risk stub.
5. **Task 7 (N1) workspace setup**: Complex fixture; TDD backstops any gate-ordering changes.
6. **`_resolve_base_ref` returning None**: Task 10 should handle gracefully (infra error FAIL, not crash). Implementer should add a guard.
