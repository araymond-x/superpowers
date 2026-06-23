---
schema_version: 1
task_id: 9
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/subagent-driven-development/scripts/controller-checkpoint.py"
    description: "N25b: added _frontmatter_block SSOT helper (line-anchored fence-close via re.MULTILINE); both _task_ids_where and _integration_test_paths now use it instead of the naive content.find first-substring match. N25d: Check 10 not-a-file branch distinguishes a directory ('is a directory, not a file') from missing. N25f: Check-10 caller prefixes all three malformed-detail branches (malformed-only, infra-error, mixed it_problems) with the plan filename via os.path.basename(args.plan_file)."
  - path: "tests/unit/test_c2_integration_gate.py"
    description: "Added TestN25Diagnostics (5 tests): line-anchored frontmatter for _task_ids_where and _integration_test_paths, directory-path FAIL detail, helper-level malformed 'bare string', and Check-10 detail naming the plan file. Reuses the TestC2Check10 git-repo harness via method aliases."
tests:
  written: 5
  passing: 5
  command: ".venv/bin/python3 -m pytest tests/unit/test_c2_integration_gate.py::TestN25Diagnostics -v"
  result: PASS
contract_compliance:
  - constraint: "behavior-preserving for well-formed frontmatter"
    status: compliant
    detail: "Full unit suite (497) green; the two target files (74) green incl. all pre-existing C2 fixtures. _frontmatter_block returns the same body as content.find for well-formed plans; differs only when a triple-dash appears inside a value/hr (the bug being fixed)."
  - constraint: "_frontmatter_block is a single shared helper (SSOT, no duplicate line-anchor logic)"
    status: compliant
    detail: "One helper added; both consumers call it. No regex duplicated into either function."
  - constraint: "Python 3.9 compat (no PEP-604 unions; Category-8 scanner)"
    status: compliant
    detail: "Helper annotated -> Optional[str] (Optional already imported). validate-all-skills.py: 145 PASS / 0 FAIL."
  - constraint: "write scope = controller-checkpoint.py + test_c2_integration_gate.py only"
    status: compliant
    detail: "git show --stat confirms exactly those 2 files in commit 077cd92."
---

# Task 9 — N25(b,d,f): line-anchored frontmatter scan + directory/malformed diagnostics

## Implementation Summary

Three diagnostics fixes to the SDD pre-completion gate, all TDD (RED confirmed: 4 of 5 new tests failed before the change; the 5th pinned existing-correct helper behavior).

- **N25b** — added `_frontmatter_block(content) -> Optional[str]` that closes the frontmatter at the first *line-anchored* `^---$` (via `re.search(..., re.MULTILINE)` on `content[3:]`), instead of `content.find("---", 3)` which matched the first `---` anywhere (inside a YAML value or a markdown hr). Both `_task_ids_where` and `_integration_test_paths` now delegate to it — single source of truth.
- **N25d** — Check 10's not-a-file branch now reports `"<path>: is a directory, not a file"` when the declared path resolves to a directory (previously the misleading "missing on disk").
- **N25f** — the Check-10 caller names the source plan file in all three malformed-detail branches (malformed-only, infra-error-plus-malformed, and the mixed valid+malformed `it_problems` list).

## Source Files Read
- `skills/subagent-driven-development/scripts/controller-checkpoint.py` (full file — `_task_ids_where`, `_integration_test_paths`, the Check-10 block incl. the not-a-file branch, and surrounding helpers added by Tasks 7/8: `_git_run`, `_EMPTY_TREE_SHA`, `_merge_base_is_head`, `_feature_window_base`, `effective_base` logic).
- `tests/unit/test_c2_integration_gate.py` (full — reused `_load_script`, `_vp_ckpt`, `_c2_plan`, `IT_PATH`, `_H`, and the `TestC2Check10` `_git`/`_setup_repo`/`_run_checkpoint` harness).
- `tests/unit/sdd_test_helpers.py` (`_load_script`, `_write_manifest`, manifest fixture shape).

## CLAUDE.md Files Read
- Repo-root `CLAUDE.md` (SDD scripts inventory, `$PYTHON`/stdlib rules, Category-8 3.9-compat scanner, `.venv/bin/python3` for pytest).
- Global `~/.claude/CLAUDE.md` and rules (`architectural-principles.md` SSOT, `coding-style.md`) — noted the project's Category-8 rule overrides the global "prefer PEP-604" guidance, so I used `Optional[str]`, not `str | None`.

## Deviations from Plan

1. **N25f design choice (documented per task instruction): option (b) — caller-side attribution.** `_integration_test_paths` was left with its single `plan_contents` parameter (no signature change). The Check-10 caller derives `_plan_label = os.path.basename(args.plan_file)` and prefixes all malformed details. Rationale: minimal blast radius — threading a parallel filename list into `_integration_test_paths` (option a) would have touched the helper signature and rippled to the direct-helper-assertion tests (`test_flat_string_declaration_fails`, `test_empty_path_declaration_fails`, `test_malformed_names_source_plan_file`) that pin the helper's message text. Option (b) keeps the helper's `"bare string"` message intact (so `test_malformed_names_source_plan_file` passes unchanged) and adds the filename only at the gate boundary. **Limitation worth noting:** in a multi-module plan where the malformed declaration lives in a non-active module file, `args.plan_file` names the active module being driven, not necessarily the file containing the bad declaration — the label is a useful pointer to the plan set, not a precise file attribution. Precise per-declaration attribution would require option (a)'s parallel-list threading.

2. **Two extra tests beyond the plan's three skeletons.** Added `test_integration_test_frontmatter_line_anchored` (line-anchoring proof for the second consumer, `_integration_test_paths` — the plan's `test_frontmatter_line_anchored` only covered `_task_ids_where`) and split N25f into both a helper-level test (`test_malformed_names_source_plan_file`, the plan's skeleton) and a Check-10-caller test (`test_malformed_check10_detail_names_plan_file`, satisfying the NOTE's "Check-10 detail must name the plan file").

## Self-Review Findings
- Completeness: all 5 sub-requirements (line-anchor both consumers via one helper, directory detail, plan-file naming in malformed messages) implemented and tested. Behavior-preserving verified across the full 497-test unit suite.
- Quality: SSOT respected (one helper); the three malformed branches use the same `_plan_label`; no logic duplicated. `Optional[str]` keeps 3.9 compat.
- Edge cases checked by hand: frontmatter with no closing line-anchored `---` → helper returns None (skipped), same conservative outcome as before; `args.plan_file` is always set in both phases (argparse path or manifest-resolved), with a `"the plan"` fallback guarding the None case.
- Discipline: TDD followed (RED then GREEN); commit scoped to exactly the 2 files; no scratch files.

## Concerns
- The N25f multi-module attribution limitation (Deviation 1) — `args.plan_file` names the active module, not necessarily the declaring file. Acceptable for the minimal change this task scoped, and the label still narrows the author to the plan set. If precise attribution is later wanted, that's the option-(a) thread-filenames refactor. Flagging for the spec reviewer to confirm the caller-side choice is acceptable.
