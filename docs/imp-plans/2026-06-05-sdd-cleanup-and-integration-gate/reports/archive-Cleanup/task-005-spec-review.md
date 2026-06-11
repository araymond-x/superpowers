# Task 5 Spec Compliance Review (N12)

> Dispatched 2026-06-10 (provenance: `.dispatch-log` task=5 type=spec-review).
> Reviewed: commit edc5ff2 against module-1-cleanup.md Task 5 (base 9799438).

## Verdict: PASS — Spec compliant AND contract compliant

## Independent Verification Performed

**1. Gating logic vs. spec (transition-module.py:122-152) — VERIFIED**
- Spec site: file-existence check unconditional within `pr.spec_review_mode != "skip"` (line 125-126); provenance error only when `manifest.enforcement.dispatch_provenance and not _has_dispatch_provenance(...)` (lines 127-130). Matches plan's prescribed shape exactly.
- Quality site: identical pattern (lines 132-152). File missing/empty → error regardless of dispatch_provenance; provenance only when enforcement flag truthy.
- `_has_dispatch_provenance` reused — single definition at line 38, no duplication. Diff touches only the two `elif` conditions (8 lines changed in the script).

**2. Both carve-outs preserved — VERIFIED by reading code-path order**
- Verification exemption: `if task_id in verif_ids: continue` sits upstream of both review blocks — untouched by the diff.
- Min-tier waiver: `elif has_min: pass` (lines 147-148) is evaluated **before** the new provenance `elif` — waiver still wins, untouched by the diff.

**3. Tests exercise the real scenario — VERIFIED against TIER_PROFILES ground truth**
- `sdd_session.py:47-62`: micro tier has `dispatch_provenance: False` AND `spec/quality_review_mode: "self_review"` (≠ "skip") — test 1 genuinely hits the file-checks-ON / provenance-OFF combination, not the "skip" branch.
- Test 1 fixture: review files written for all 4 module tasks; dispatch log contains only the sentinel line; asserts rc==0 and no "not provenance-logged" in stderr.
- Test 2: quality-review files omitted; asserts rc==1 AND the specific `"missing or empty quality review"` error — correctly pins the FILE check, not provenance.
- **Pre-fix RED confirmed empirically**: extracted the script at BASE_SHA (9799438) to /tmp and ran the exact test-1 fixture scenario — old script returned **rc=1 with `not provenance-logged` errors for all 8 spec+quality checks**. Test 1 was genuinely red before the fix.
- Test 2 "no pre-fix failing state" claim: **reasoning is sound** — the file-existence check was already unconditional pre-fix; the test is a regression guard against over-relaxation, logged as a deviation appropriately.

**4. Test runs — actual counts observed**
- `pytest tests/unit/test_transition_module.py tests/unit/test_ssot_minimum_agreement.py -v` → **16 passed** (both new N12 tests PASSED; SSOT truth table all 4 cases PASSED)
- `pytest tests/unit/ -q` → **429 passed, 1 warning** (matches implementer's claimed count)
- SSOT-unaffected claim verified by reading `test_ssot_minimum_agreement.py`: its manifests are built from `TIER_PROFILES["standard"]` (`dispatch_provenance: True`), so the new gate is transparent to it.

**5. Commit — VERIFIED**: subject exact match to plan Step 5; contents exactly the two prescribed files.

**6. Contract constraints** — None declared; report records `not_applicable` correctly.

**7. Module acceptance criterion** — satisfied. Note the test's log is sentinel-only rather than truly absent, but immaterial: when `dispatch_provenance` is False the gate short-circuits before `_has_dispatch_provenance` is called (and the helper returns False for a missing file anyway).

## Report Completeness
All required sections present and substantive; the Concerns item (`context_summary_at=2` helper override at test_transition_module.py:65) confirmed pre-existing, irrelevant to N12, out-of-scope judgment correct.

## Findings
No BLOCKING issues. No ADVISORY issues. Implementer claims held up in every particular, including the pre-fix red state, which was reproduced independently.
