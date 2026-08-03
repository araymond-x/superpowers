---
schema_version: 1
task_id: 12
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: skills/subagent-driven-development/scripts/write-mechanics-card.py
    description: "NEW. Deterministic generator for reports/handoff-mechanics.md — the successor SDD controller's mechanics card (checkpoint invocations, paths, hop state, context status, cmux outcome, validate-report.py-clean implementer-report skeleton). One deliberate one-line deviation from the plan fence (see Deviations)."
  - path: tests/unit/test_mechanics_card.py
    description: "NEW. Module-level harness (_fixture_feature/_run_card/_materialize_minimal_plan) + 4 tests: golden-file determinism/content, skeleton validate-report.py roundtrip, missing-input degradation, byte-proxy/report-glob non-collision invariant (pinned against the live hook text)."
tests:
  written: 4
  passing: 4
  command: ".venv/bin/python3 -m pytest tests/unit/test_mechanics_card.py -v (4 passed); full-suite regression: .venv/bin/python3 -m pytest tests/unit/ -q (809 passed, 0 failed); .venv/bin/python3 -m pytest tests/ARaymond-skill-regression/validate-all-skills.py (161 PASS, 0 FAIL, 2 pre-existing unrelated WARNINGs — writing-plans/SDD SKILL.md word-count soft threshold)"
  result: PASS
contract_compliance:
  - constraint: "Baselined hooks (hooks/session-start, sdd-stop-hook.sh, sdd-pre-dispatch-hook.sh) change ONLY in Task 14"
    status: compliant
    detail: "git diff confirms zero changes to any baselined hook or SKILL.md; only the two owned new files were created and committed."
  - constraint: "Card generator is Python; venv (PyYAML + pydantic) is a hard dependency, exit 2 if imports fail"
    status: compliant
    detail: "try/except ImportError around yaml/ImplementerReport/REQUIRED_SECTIONS imports prints to stderr and sys.exit(2), exactly as fenced."
  - constraint: "N35 — composed checkpoint invocations must satisfy run_pre_dispatch/run_pre_completion's runtime-required args (--deviations-file, --reports-dir), not just argparse-optional"
    status: compliant
    detail: "Read both functions in controller-checkpoint.py: both sys.exit(3) when args.deviations_file or args.reports_dir is None, despite argparse marking them optional. Ran BOTH composed commands verbatim (with --task-number substituted for <N>) against a materialized fixture manifest outside the test suite: both returned real checkpoint JSON (status: FAIL with itemized checks, exit 1) — not an argument/usage error (which would be exit 3 with a bare {\"error\": ...} shape). This is the behavioral proof the guidance required."
  - constraint: "Reproduce the plan's fenced Test harness / Generator helpers / Step 1 tests / Step 3 generator byte-for-byte"
    status: partial
    detail: "All four fences reproduced verbatim except one line: the `## Paths` section's Deviations line was changed from re-deriving `os.path.join(git_root, paths.get(\"deviations_file\", \"\"))` to reusing the already-computed `deviations_abs` variable, per explicit dispatch guidance to avoid double-derivation. Verified byte-identical output for the present-key case before and after (both the golden test and a standalone script confirmed the two expressions produce the same string when `deviations_file` is present in the manifest, which it always is via materialize-manifest.py's ArtifactPaths). The only behavior change is the missing-key fallback (now `git_root/<feature_dir>/deviations.md` instead of a bare `git_root/`), which cannot occur with any manifest materialize-manifest.py produces."
  - constraint: "Use the CURRENT on-disk (amended) version of test_byte_proxy_interference_invariant, not the original vacuous form"
    status: compliant
    detail: "Test file uses the read_text()-based hook assertions ('\"$REPORTS_DIR\"/*.md', 'task-${padded}-${report_type}') exactly as they appear in the current plan file, confirmed against sdd-pre-dispatch-hook.sh source before writing."
---

## Implementation Summary

Created `write-mechanics-card.py` — a standalone, venv-dependent Python CLI that reads an SDD session manifest (`.sdd-session.json`) and generates `reports/handoff-mechanics.md`: the deterministic mechanics card a freshly-spawned successor controller reads on arrival. The card composes copy-pasteable `controller-checkpoint.py` invocations for both `pre-dispatch` and `pre-completion` phases (with the N35-required `--deviations-file`/`--reports-dir` flags always present), lists resolved absolute paths (manifest, plan, active module if any, deviations, reports dir), reports hop-budget state (`hops used` / `expected` / `ceiling`, sourced from `_handoff_support.derive_expected_hops`/`hop_ceiling`), context-pressure status (last observation line + Check 6b midpoint due-date), the last recorded cmux spawn outcome line, a pointer to the `/rename`+`/rc` post-spawn recipe, and a fenced, `validate-report.py`-clean implementer-report skeleton (built from the real `ImplementerReport` Pydantic model and `REQUIRED_SECTIONS` list, so model/section drift breaks this generator's own tests rather than silently producing an invalid skeleton).

Followed strict TDD: wrote the 4-test file (with the shared module-level fixture harness) first, confirmed RED (`ModuleNotFoundError`/`FileNotFoundError` for the non-existent generator — 3 of 4 tests failed as expected; the 4th, `test_byte_proxy_interference_invariant`, only reads the already-existing hook file and passed immediately since it doesn't depend on the generator), then implemented the generator from the plan's Step-3 fence plus the "Generator helpers" fence inserted below the imports, and confirmed GREEN (4/4).

Applied one dispatch-guided fix: the `## Paths` section's Deviations line originally re-derived the deviations path independently of the already-computed `deviations_abs` variable used in the checkpoint-invocation block. Replaced the re-derivation with the shared variable per the "avoid double-derivation" guidance, verified byte-identical rendered output in the normal (key-present) case both by hand-computation and by re-running the golden test (still green, no assertion changed).

Behaviorally verified the N35 concern (argparse-optional vs. runtime-hard-required flags) by running both composed `controller-checkpoint.py` invocations verbatim against a real materialized fixture manifest outside pytest: both returned genuine checkpoint JSON results (`status: FAIL`, itemized `checks`/`blockers`, exit 1) rather than an argument-parsing error (which would surface as exit 3 with a bare `{"error": ...}` body) — proving the composed commands are correctly formed, not merely argparse-legal.

## Source Files Read

- `skills/subagent-driven-development/scripts/_handoff_support.py` — confirmed `derive_expected_hops` (reads `manifest["handoff"]["expected_hops"]` when a valid int ≥1, else re-derives) and `hop_ceiling` (`max(CEILING_FLOOR=6, CEILING_FACTOR=2 * expected)`) match the verified facts (expected=2 → ceiling=6).
- `skills/scripts/models/implementer_report.py` — confirmed `ImplementerReport` field names/types (`task_id`, `task_type`, `status`, `files_changed: list[FileChange]`, `tests: TestSummary`) and the `files_changed_non_empty_for_done` validator, so the skeleton's `files_changed` list (one entry) plus `status: DONE` is model-valid.
- `skills/subagent-driven-development/scripts/_report_utils.py` — confirmed `REQUIRED_SECTIONS` is a list of `(canonical_name, patterns)` 2-tuples, so `for name, _ in REQUIRED_SECTIONS` in `_skeleton()` is a correct unpack; confirmed `validate_report_sections`'s exit-relevant field is `sections_missing` only (not `has_deviations`/`has_concerns`), so the skeleton's terse `(fill in)` placeholder bodies do not fail validation.
- `skills/subagent-driven-development/scripts/controller-checkpoint.py` — read `run_pre_dispatch`/`run_pre_completion` in full: both hard-`sys.exit(3)` when `args.deviations_file`/`args.reports_dir` is `None`, confirming the N35 concern is real (argparse marks them optional but the functions require them); read `_load_manifest_config` to confirm `--manifest` alone (no `--plan-file`) suffices, since it mutates `args.plan_file` from the manifest.
- `skills/subagent-driven-development/scripts/materialize-manifest.py` — confirmed the manifest shape: `plan_file` top-level, `feature_dir`/`reports_dir`/`deviations_file` nested under `paths` (via `ArtifactPaths`); confirmed the CLI house style (argparse, `sys.exit(main())`-equivalent, stdlib-first with PyYAML as the sole non-stdlib import at module scope).
- `skills/subagent-driven-development/scripts/validate-report.py` — confirmed the two-layer validation (Pydantic frontmatter via `validators.validate_report`, then `validate_report_sections`) and that the exit code depends only on `result["status"] == "INCOMPLETE"` (missing sections), not on `has_deviations`/`has_concerns` — so the skeleton's placeholder bodies are safe.
- `skills/scripts/models/validators.py` (`validate_report`) — confirmed it calls `ImplementerReport.model_validate(data)` on the extracted frontmatter, matching the self-check `_skeleton()` performs before returning.
- `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` — grepped and read the exact lines containing `"$REPORTS_DIR"/*.md` (line ~170, inside `ctx_byte_estimate()`) and `task-${padded}-${report_type}` (line ~336, inside `task_report_glob()`) to confirm the amended `test_byte_proxy_interference_invariant` assertions are pinned against real, currently-present constructs.
- `skills/scripts/models/sdd_session.py` — confirmed `active_module_file: str | None = None` is a top-level manifest field (bare filename), matching `manifest.get("active_module_file")` usage in the generator.
- `docs/imp-plans/2026-07-30-cmux-spawn-v2/module-4-card-hooks-docs.md` — read the full Task 12 section (Test harness, Generator helpers, Step 1 tests, Step 3 implementation) and reproduced the fences verbatim except the one documented deviation.

## CLAUDE.md Files Read

Checked for subdirectory `CLAUDE.md` files in `skills/subagent-driven-development/scripts/` and `tests/unit/` (and their parents `skills/`, `tests/`) — none exist. No subdirectory-specific instructions to apply beyond the root project `CLAUDE.md` (already loaded via the dispatch prompt) and the global rules.

## Deviations from Plan

One deliberate, dispatch-guided one-line deviation from the plan's Step-3 fence (which the task brief explicitly designates authoritative/byte-for-byte): the `## Paths` section's Deviations line was changed from

```
{module_line}- Deviations: `{os.path.join(git_root, paths.get("deviations_file", ""))}`
```

to

```
{module_line}- Deviations: `{deviations_abs}`
```

reusing the `deviations_abs` variable already computed above (and already used in the checkpoint-invocation block), instead of re-deriving the same path with a different (bare-string) fallback default. This closes the "double-derivation" consistency gap the dispatch guidance flagged.

**Proof this does not change golden output for the normal case:** `materialize-manifest.py`'s `ArtifactPaths` always sets `deviations_file`, so in every real (and fixture) manifest the two expressions — `paths.get("deviations_file", os.path.join(feature_dir, "deviations.md"))` and `paths.get("deviations_file", "")` — evaluate to the *same* string (the `.get()` default is never reached in either form). Verified this both by direct computation (`python3 -c` comparing the two expressions with a representative `paths` dict → `True`) and empirically: the golden-file test (`test_card_deterministic_with_contents`, which asserts `"deviations.md" in card`) still passes unchanged after the edit. The only behavior difference is the fallback when `deviations_file` is absent from `paths` — previously `git_root/` (a bare, almost-certainly-wrong path), now `git_root/<feature_dir>/deviations.md` (matching the checkpoint-invocation block's own fallback) — a case that cannot arise from any manifest `materialize-manifest.py` produces.

No other deviations. The plan's own note that `test_byte_proxy_interference_invariant` was pre-dispatch-amended (vacuous → hook-reading) was already resolved in the plan file and `deviations.md` before this task began; I used the current on-disk (amended) form verbatim, as instructed, and independently verified both hook constructs (`"$REPORTS_DIR"/*.md`, `task-${padded}-${report_type}`) are present in `sdd-pre-dispatch-hook.sh` before trusting the assertion.

## Self-Review Findings

- **Completeness:** All four Step-1 test functions are present with the harness at module level, exactly matching the "Test harness" and Step-1 fences. The generator implements every section the golden test asserts on (checkpoint invocations, paths, hop state, context status, cmux outcome, `/rename`/`/rc` pointer, report skeleton).
- **Non-vacuousness (positive control):** Ran a mutation test on `_skeleton()` (changed `"passing": 1` → `"passing": 2`, violating the model's `test_counts_consistent` validator) and confirmed 3 of the 4 tests correctly go RED (the model's own self-check raises `pydantic_core.ValidationError` inside the script, so the card is never written and the dependent tests fail — `test_report_skeleton_passes_validate_report`, `test_card_deterministic_with_contents`, `test_missing_inputs_degrade_not_crash`). Restored the original file via file copy + `diff -q` confirming byte-identical restoration (never `git checkout --`/`git stash`, per repo convention). This rules out a false-green from an ambient `SUPERPOWERS_VALIDATOR_BYPASS` or similar — confirmed no such env var is set ambiently and no autouse fixture in `tests/unit/conftest.py` sets one (only a picker-env scrub fixture exists, unrelated).
- **Regression check:** Ran the full unit suite (`809 passed, 0 failed`, `391s`) and the skill regression validator (`161 PASS, 0 FAIL, 2 pre-existing unrelated WARNINGs` — the documented writing-plans/SDD SKILL.md word-count soft thresholds, untouched by this task). `write-mechanics-card.py` specifically passed the Python 3.9-compatibility check.
- **Scope discipline:** Confirmed via `git diff --stat` that no baselined hook (`hooks/session-start`, `sdd-stop-hook.sh`, `sdd-pre-dispatch-hook.sh`) or `SKILL.md` was touched. Confirmed via `git status --porcelain` that only the two owned files (`write-mechanics-card.py`, `test_mechanics_card.py`) were staged and committed; pre-existing controller-owned artifacts (`deviations.md`, the plan file, `.dispatch-log`, `context-observations.log`, `checkpoint-pre-dispatch-012.json`, `partner-review-012.md`) were left untouched/unstaged.
- **No stray artifact:** Confirmed `docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/handoff-mechanics.md` does not exist in the live feature reports dir (a stray copy there would be blocked by Check 3b's allowlist until Task 14 adds the `handoff-` prefix).
- **House style:** Matched `materialize-manifest.py`/`context-probe.py` conventions — shebang, argparse, module docstring stating usage + exit-code semantics inline, `sys.path.insert` for sibling/model imports, `if __name__ == "__main__": sys.exit(main())`.

## Concerns

- The plan's "byte-for-byte authoritative" instruction was not followed for one line (the `deviations_abs` consistency fix), per explicit dispatch guidance that pre-authorized this exact class of change ("small consistency fix, not a redesign") and pre-specified the fallback: keep the fence as written if the change risks altering golden output. I judged the risk to be zero (proven above) and applied it; flagging as a Concern per the `status: DONE_WITH_CONCERNS` convention since it is still a literal deviation from a fence marked byte-for-byte authoritative, and a future reviewer diffing against the plan text will see a one-line mismatch that is intentional and pre-approved rather than drift.
- The generator's `ceiling` computation (`os.environ.get("SUPERPOWERS_CMUX_MAX_HOPS") or hop_ceiling(expected)`) reads an env var that Task 13's `spawn-handoff-session.sh` also consumes for the same purpose; if that script's default or validation logic for `SUPERPOWERS_CMUX_MAX_HOPS` ever diverges from the card's bare `os.environ.get` (e.g. the shell script warns-and-reverts on a non-numeric override per the CLAUDE.md env-var registry, but this generator would render whatever string is present, numeric or not), the card could display a value the shell script would actually reject. This is exactly what the golden test's `_run_card` env-scrub (stripping `SUPERPOWERS_CMUX_*`) is designed to keep deterministic in the *test*, but the live generator has no such validation. Not in Task 12's scope (the fence doesn't validate it either), but worth Task 13/16's authors being aware of when documenting the knob.
- I did not add type hints to `write-mechanics-card.py` — the plan fence itself has none, and `materialize-manifest.py` (the designated pattern reference) has only light typing (`Optional[str]`, `List[ModuleState]`) on its own functions, not inline argparse/CLI glue. Matched the fence as the more specific authority for this file.
