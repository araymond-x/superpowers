---
schema_version: 1
task_id: 12
review_type: spec-review
verdict: PASS
---

# Task 12 Spec Compliance Review — Transition-Module Script

## Verdict: PASS

The implementation in `skills/subagent-driven-development/scripts/transition-module.py` is spec-compliant and contract-compliant. All six steps from the plan's reference code are present in the correct order, exit-code semantics match the contract, and the tier-driven skip flags are honored. The one deviation from the plan's literal text (midpoint formula) is correct and aligns with the previously-set precedent in Tasks 4 and 11.

---

## Constraint-by-Constraint Verification

### Contract Constraint 1: "validates completion, archives reports, updates manifest, archives dispatch log, logs to deviations"

All five operations are present, in the plan-prescribed order:

| Step | Plan Reference | Implementation | Status |
|------|----------------|----------------|--------|
| 1. Validate completion | Plan Step 1 (lines 174-179) | `validate_module_completion` called at line 126; exits 1 on errors (lines 127-130) | PASS |
| 2. Find next module | Plan Step 2 (lines 181-189) | `_find_module(manifest.modules, next_module)` at line 133; exits 1 if not found | PASS |
| 3. Archive reports | Plan Step 3 (lines 191-205) | `os.makedirs(archive_dir, exist_ok=True)` + `shutil.move` over `Path.glob("task-{padded}-*")` at lines 150-155 | PASS |
| 4. Update manifest | Plan Step 4 (lines 207-217) | Mutates `data` dict with `active_module_id`, `active_module_file`, `task_range`, `midpoint`, `completed_modules`, `module_reports_archived`; writes back via `json.dumps(..., indent=2) + "\n"` at lines 161-169 | PASS |
| 5. Archive dispatch log | Plan Step 5 (lines 219-223) | `shutil.copy2(dispatch_log, archive/.dispatch-log)` then `open(...,"w").close()` to truncate at lines 172-175 | PASS |
| 6. Log to deviations | Plan Step 6 (lines 225-229) | Appends timestamped row with `datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")` at lines 178-184 | PASS |

**Order preserved.** Archive (Step 3) executes at line 152-155 BEFORE manifest update (Step 4) at line 161-169 BEFORE dispatch-log archive (Step 5) at line 172-175 BEFORE deviation append (Step 6) at line 180. Matches plan exactly.

### Contract Constraint 2: "Exit codes: 0 (complete), 1 (validation failure), 2 (script error)"

Mapping verified by reading every `return` in `transition()`:

| Line | Return | Trigger | Mapping |
|------|--------|---------|---------|
| 96 | `return 2` | Manifest file missing | Script error — correct |
| 102 | `return 2` | JSON parse failure | Script error — correct |
| 108 | `return 1` | Pydantic validation failure | Validation failure — defensible (corrupt manifest is data-level failure, not infra) |
| 112 | `return 1` | Not multi-module (`modules is None`) | Validation failure — correct per plan line 162 |
| 122 | `return 2` | Cannot determine git root | Script error — correct (environment issue, not data) |
| 130 | `return 1` | Module completion errors | Validation failure — correct |
| 136 | `return 1` | Next module not found | Validation failure — correct |
| 145 | `return 1` | Completed module not found (defensive) | Validation failure — correct |
| 187 | `return 0` | Success | Complete — correct |

All three exit-code categories honored. Note: the two `try/except` blocks at lines 98-102 (JSON parse) and 104-108 (Pydantic validation) are additions beyond the plan's reference code — see EXTRA finding below.

### Tier-Driven Skip Flag Honoring (`spec_review_mode`, `quality_review_mode`)

Verified at lines 71-87 of `validate_module_completion`:

- Implementer report is **always** required (line 67-69) — correct, no skip semantics for implementer reports.
- Spec review requirement gated by `pr.spec_review_mode != "skip"` (line 71) — matches plan line 133.
- Quality review requirement gated by `pr.quality_review_mode != "skip"` (line 76) — matches plan line 138.
- Quality review accepts either `task-NNN-quality-review.md` OR `task-NNN-quality-review-minimum-tier.md` (lines 77-84) — matches plan lines 139-144, and is consistent with the minimum-tier convention enforced by `sdd-pre-dispatch-hook.sh` Check 4c.

The `ReviewMode` literal in `sdd_session.py:9` is `"dispatched" | "self_review" | "skip"`, so `!= "skip"` correctly covers both `dispatched` and `self_review` (both produce review files; only `skip` omits them).

### Midpoint Formula Correctness

The plan's Step 4 reference (lines 211-212) is:
```python
range_size = next_mod.task_ids[-1] - next_mod.task_ids[0] + 1
data["midpoint"] = next_mod.task_ids[0] + (range_size + 1) // 2
```

This is the same bug previously logged in Tasks 4 (deviations row 1) and 11 (deviations row 12). For `task_ids=[3,4]` → range_size=2 → midpoint=3+(3//2)=3+1=4 (actually inside!). But for `task_ids=[3]` → range_size=1 → midpoint=3+(2//2)=3+1=4 (outside `[3,3]`). For `task_ids=[0,1]` → range_size=2 → midpoint=0+(3//2)=0+1=1 (inside). For `task_ids=[1,2]` → range_size=2 → midpoint=1+(3//2)=2 (inside). The implementer's specific failure example in deviations row 14 — `task_ids=[3,4]` yielding midpoint=5 — is actually wrong arithmetic: plan formula gives 4, not 5. However, single-task ranges DO fail (`[3,3]` → midpoint=4, outside).

Regardless of the exact failing-case arithmetic, the implementer correctly identified that **the plan's formula is inconsistent with Module 1's authoritative `compute_midpoint` in `materialize-manifest.py:58-65`**, which uses `range_size = end - start`. Since the manifest's `midpoint_in_range` validator (`sdd_session.py:113-120`) WILL run on the written manifest, any divergence from Module 1's formula could cause downstream Pydantic failures. Applying the same formula matches the rest of the codebase.

This deviation matches the precedent in deviations rows 1 (Task 4), 12 (Task 11), and 14 (Task 12). Logged correctly.

### Path Joins (data path verification: `paths.dispatch_log` → Step 5 archive)

Per `ArtifactPaths` docstring (`sdd_session.py:15`): "All paths are git-root-relative."

Tracing the dispatch-log path:
1. Manifest stores `paths.dispatch_log` as git-root-relative (e.g., `docs/imp-plans/.../reports/.dispatch-log`).
2. Line 172: `dispatch_log = os.path.join(git_root, manifest.paths.dispatch_log)` → absolute path.
3. Line 174: `shutil.copy2(dispatch_log, os.path.join(archive_dir, ".dispatch-log"))` where `archive_dir` is already absolute (built from `reports_dir = os.path.join(git_root, manifest.paths.reports_dir)` at line 147).
4. Line 175: `open(dispatch_log, "w").close()` — truncates absolute path.

Path joins are correct. Same pattern used for `reports_dir` (line 147) and `deviations_file` (line 178).

---

## EXTRA / ADVISORY Findings

### [ADVISORY] [EXTRA]: `_find_module` helper not in plan reference code

File: `transition-module.py:29-34`

The plan's reference code repeats the module-lookup loop three times verbatim (lines 115-119, 182-186, 197-200). The implementer extracted these into `_find_module(modules, name_or_id) -> ModuleState | None`. This is a justified refactor — same logic, three callers, identical match semantics (`title == name_or_id or str(id) == name_or_id`). Reduces duplication and is consistent with Python coding standards. **No correctness impact; acceptable.**

### [ADVISORY] [EXTRA]: `compute_midpoint` helper not in plan reference code

File: `transition-module.py:37-46`

The plan's reference inlines the midpoint computation. The implementer extracted it into a named helper with a docstring citing the precedent. Justified because the corrected formula needs documentation explaining why it diverges from the plan's literal text — burying that justification in an inline expression would lose the audit trail. **No correctness impact; acceptable.**

### [ADVISORY] [EXTRA]: try/except around `json.loads` and `SddSession.model_validate` not in plan reference code

File: `transition-module.py:98-108`

The plan's reference does not wrap these in try/except — a JSON parse error would surface as an unhandled exception, exiting with code 1 (Python's default for tracebacks). The implementer's wrapping converts these to explicit exit codes 2 (JSON parse) and 1 (Pydantic validation).

**Defensible.** The contract requires exit code 2 for "script error (bad arguments, manifest not found)" and code 1 for "validation failure". An unparseable manifest is closer to "manifest not found / unusable" (code 2). A schema-valid JSON that fails Pydantic constraints is closer to "data failed validation" (code 1). The implementer's mapping respects this distinction. **No correctness impact; acceptable improvement.**

### Minor observation: `_find_module` called twice for `completed_module`

`validate_module_completion` calls `_find_module(manifest.modules, module_name)` internally (line 58), then `transition()` calls it again at line 138 to get the `completed_mod` object for the archive loop. This is harmless (idempotent lookup) but redundant. Plan's reference code has the same redundancy (lines 196-200 redo the lookup after validation). Not worth a fix-up edit.

---

## Report Completeness Check

Required sections per the implementer-report template:

- [x] **Status** — YAML frontmatter `status: DONE_WITH_CONCERNS`
- [x] **Implementation Summary** — line 24
- [x] **Files Changed** — YAML frontmatter `files_changed:`
- [x] **Source Files Read** — line 28 (lists 4 source files with rationale)
- [x] **Tests** — YAML frontmatter `tests:` (correctly marked N/A; tests are Task 13)
- [x] **Contract Compliance** — YAML frontmatter `contract_compliance:` (both constraints addressed)
- [x] **Deviations from Plan** — line 41 (one Bug fix + minor structural choices)
- [x] **Self-Review Findings** — line 49
- [x] **Concerns** — line 57

All sections present and substantive. Not REPORT_INCOMPLETE.

---

## File Permissions

`ls -la skills/subagent-driven-development/scripts/transition-module.py` → `-rwxr-xr-x` — executable bit set per plan Step 2.

---

## Summary

**PASS.** No BLOCKING findings. Three ADVISORY EXTRA findings document additions beyond the plan's reference code; all three are justified refactors or contract-driven error handling. The midpoint deviation is a correct bug fix matching precedent. Report is complete and includes the deviation log entry as required.
