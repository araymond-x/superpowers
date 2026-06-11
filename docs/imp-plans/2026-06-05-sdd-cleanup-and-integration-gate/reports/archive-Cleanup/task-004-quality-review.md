# Task 4 Code Quality Review (N7 + SSOT consolidation)

> Dispatched 2026-06-10 (provenance: `.dispatch-log` task=4 type=quality-review).
> Reviewed: commits 1179654 + 9799438 against module-1-cleanup.md Task 4 (base 1584112).

### Strengths

- **Exact plan conformance on N7**: the replaced check block at `controller-checkpoint.py:698-714` is character-for-character the block prescribed in Task 4 Step 3, including the `blockers.append` removal. The three-way semantics (non-empty → PASS, None/empty → OK, absent → OK) are all present.
- **"OK" is an established status**: `checkpoint_result.py:9` declares `CheckStatus = Literal["PASS", "FAIL", "SKIP", "OK", "WARNING"]`, and `controller-checkpoint.py` already uses `"OK"` at 12+ sites. No downstream consumer treats OK as a blocker — blockers are tracked via the explicit `blockers` list, which this change correctly no longer appends to.
- **Clean SSOT consolidation**: `_unfenced_content` now exists exactly once (`_report_utils.py:48`), byte-identical body, with a docstring noting the SSOT role and both consumers. Repo-wide grep confirms zero leftover copies; all 9 call sites across both scripts resolve to the import. No dead code, no unused imports (`re` remains load-bearing in both scripts).
- **Sibling import done correctly**: `sys.path.insert(0, <script dir>)` placed immediately before the import in both scripts, commented with the reason, `# noqa: E402` applied. No stdlib-shadowing risk.
- **Exemplary deviation hygiene**: deviations.md rows document the scope fold-in, the transitive-pydantic concern with the corrected exposure mechanism, and the sys.path decision — all before this review.
- **Real-context verification confirmed**: `python3 validate-plan.py --plan-file module-1-cleanup.md` (bare python3, no venv) emits valid JSON, status PASS, exit 0.

### Issues

#### Critical (Must Fix)
None.

#### Important (Should Fix)

1. **`validate-plan.py` transitive pydantic dependency → latent Gate 1 fail-open** — `_report_utils.py:18-21` does a module-level `from implementer_report import Status`, which imports pydantic. `validate-plan.py` was previously stdlib-only and is invoked by `plan-validation-gate-hook.sh:165` with bare `python3` plus `|| echo ""` and an empty-output `continue` — on a pydantic-less machine, Gate 1 structural validation silently skips. This is a **plan-prescribed home** (Step 3b names `_report_utils.py` explicitly), the implementer flagged it, the spec review advisory corrected the mechanism, and deviations.md logs the BACKLOG candidate — so this is a plan-level issue, not an implementer error. But the fix is small and context is perishable: defer `from implementer_report import Status` into a lazy accessor in `_report_utils.py` (or extract `_unfenced_content` to a dependency-free `_fences.py`), making the shared helper pydantic-free. It works on this machine (system python3 has pydantic 2.12.5), which is exactly why the fail-open will go unnoticed elsewhere. Recommend fixing at merge reconcile at the latest, per the logged follow-up.

#### Minor (Nice to Have)

2. **New test assertion is weaker than it could be** — `tests/unit/test_fence_aware_parsing.py:115` asserts `sc["status"] != "FAIL"`, which would also pass on `"WARNING"` or a typo'd status. It also doesn't assert `"source_contracts" not in result["blockers"]` — the blocker removal is the actual behavioral payload of N7. Assert `sc["status"] == "OK"` and blocker absence. (The prescribed test in the plan had the same weakness — inherited, not introduced.)
3. **The other two arms of the three-way check are untested** — `run_pre_execution` is exercised by exactly one test in the suite (the new one). present+non-empty → PASS and absent → OK have no unit coverage. Exercised indirectly by the live SDD session and e2e script; a 3-line parametrize would pin all three arms. Pre-existing gap.
4. **sys.path.insert is not deduplicated** — each importlib load prepends another copy. Harmless; completeness note.

### Recommendations

- At merge reconcile, prioritize the pydantic-decoupling follow-up (Issue 1) over the tilde-fence/unclosed-fence BACKLOG candidates — it's the only one with a silent-failure mode in a live enforcement path.
- When touching the test next, upgrade the assertion per Issue 2 in the same pass.

### Assessment

**Ready to merge?** Yes

**Reasoning:** Implementation matches the plan exactly (including the 2026-06-10 Step 3b amendment), all four implementer-reported deviations are justified and logged, no dead code remains, and the one real concern (transitive pydantic in a bare-python3 hook path) is plan-prescribed, machine-dependent-latent, and already logged with the correct mechanism. Observed test counts: targeted files **67 passed**; full suite **427 passed, 1 warning** (matches implementer report).
