# Plan Review Report — cmux-spawn-v2-remediation

**Reviewer:** plan-document-reviewer (general-purpose, sonnet), independent source-file verification
**Plan set reviewed:** `plan.md` (parent) + `module-1-consent-model-coercion.md` + `module-2-consent-ux-docs.md` + `module-3-discoverability-killswitch.md` + `module-4-hook-papercuts.md`
**Spec:** `spec-distilled.md`
**Final status:** **APPROVED** (initial pass: Issues Found → 3 blocking; all fixed and confirmed)

---

## Round 1 — Issues Found (3 blocking, all empirically verified against live source)

1. **[CONTRACT-MISMATCH] Wrong test file paths (Module 1 Tasks 1 & 2, File Map, Write-Scope, parent Code Footprint).** Plan directed tests to `tests/unit/test_plan_model.py` / `tests/unit/test_sdd_session_model.py`, which do not exist — the real files are under `tests/unit/test_models/`, with existing `TestHandoffSpawn` / `TestHandoffBlock` classes already covering `handoff_spawn`/`spawn_policy`. Creating flat-path duplicates produces a pytest `import file mismatch` (no `__init__.py`, no `--import-mode` override) that **aborts collection of the whole unit suite** — verified empirically. Module 4 Task 13 runs `pytest tests/unit/ -q`, so the blast radius is the entire suite.

2. **[GAP] Pre-fix conflicting test not surfaced/flipped (Module 1 Task 0 & Task 3).** `tests/unit/test_materialize_manifest.py::TestHandoffBlockMaterialization::test_off_survives_and_bare_off_is_never_coerced_to_auto` asserts the *pre-fix* (buggy) behavior as correct (unquoted `off` → materialize FAILS), currently green. The N83 fix inverts it. Task 3 didn't mention updating it, and directed the implementer to an invented `_materialize_plan` helper instead of the adjacent real `_mf()` helper that already contains the conflicting assertion.

3. **[CONTRACT-MISMATCH, minor] `run_spawn` kwarg (Module 3 Task 8).** Test sketches used `env=`; the real harness signature (`spawn_handoff_helpers.py:311`) is `env_extra=` — literal copy-paste would `TypeError`.

**Snippet Verification (Round 1):** 5 snippets checked — plan.py validator, materialize normalization, AUTOSPAWN precondition, N84 grep-escape, N86 gate fix — **all VERIFIED** against live source (line numbers, existing constructs, idioms all accurate).

**Cross-Document Audit (Round 1):** 3 facts traced source→spec→plan — consent value set `Literal["auto","ask","off"]`, reason codes `policy-off`/`policy-ask`/`autospawn-disabled`, and the N83 Gate-1-vs-Gate-1b test-layer distinction — **all MATCH** (independently confirmed by reading both hook-gate files).

---

## Fixes applied (dispatching agent)

1. Module 1 Tasks 1 & 2 rewritten to **extend the existing `TestHandoffSpawn` / `TestHandoffBlock` classes** at `tests/unit/test_models/…`, using the files' real idioms (`Plan.model_validate(MINIMAL_PLAN)`, direct `Handoff(expected_hops=1, spawn_policy=…)`). validators.py CLI proof placed in `test_models/test_plan_model.py` with corrected 3-level repo-root depth. File Map, Write-Scope, Files headers, and parent Code Footprint all updated to nested paths + an explicit "do NOT create flat-path duplicate (collision)" guard.
2. Module 1 Task 3 rewritten to use the real `TestHandoffBlockMaterialization._mf(extra_frontmatter=…, ok=…)` helper and to **rename + flip** `test_off_survives_and_bare_off_is_never_coerced_to_auto` → `test_bare_off_coerces_to_off_policy` (unquoted `off` now asserts success). Task 0 carries a note surfacing the pre-fix test and the extend-existing-classes rule.
3. Module 3 Task 8 test sketches switched to `env_extra=`.
4. (Secondary) Module 3 Task 7 Step 3 tightened to name `test_context_gate_tier.py` as the true positive (add a `spawn-handoff-session.sh` assertion; keep existing assertions) and `test_spawn_handoff.py` as a false positive to leave alone.

---

## Round 2 — Confirmation → APPROVED

Reviewer re-read the changed sections and confirmed:
- **Test paths — RESOLVED** (all Steps, File Map, Write-Scope, Code Footprint, and — after a final one-line fix — both `**Files:**` headers now cite the nested `test_models/` paths; VALIDATORS depth correct).
- **Pre-fix conflicting test — RESOLVED** (real `_mf` helper; test renamed and assertion flipped to match verified pre/post-fix semantics).
- **`run_spawn` kwarg — RESOLVED** (`env_extra=`).
- Secondary notes addressed. N84 regex-escape-and-keep-`grep -qE` confirmed the technically correct choice, within the spec's "`grep -qF` **or** escape" wording.

**None of the three original blocking issues survive in the actionable instructions an implementer would follow.**

## Advisory (non-blocking) recommendations carried into execution
- Implementers extend existing test classes; never create flat-path `tests/unit/test_*.py` duplicates of files under `tests/unit/test_models/`.
- Task 3 owns flipping the pre-fix materialize test; Task 0 only surfaces it.
- Confirm `run_spawn`'s exact kwarg by reading `spawn_handoff_helpers.py` before writing Task 8's tests.

**Verdict: APPROVED — ready for implementation.**
