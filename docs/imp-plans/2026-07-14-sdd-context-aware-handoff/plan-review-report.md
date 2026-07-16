# Plan Review Report — SDD Context-Aware Auto-Handoff

**Reviewed:** parent `plan.md` + `module-1-probe.md` + `module-2-hook-gate.md` + `module-3-docs-integration.md`
**Reviewer:** general-purpose plan-document-reviewer (dispatch via `plan-document-reviewer-prompt.md`)
**Date:** 2026-07-15
**Outcome:** Issues Found (1 blocking) → **all fixed** → APPROVED for execution (see Resolution).

---

## Reviewer Output (verbatim)

**Status:** Issues Found

**Blocking Issues (must fix before implementation):**

- **[Canonical Names / Contradictory Step]: Module 2, Task 3, Step 5 (hoist location):** The plan places the `SESSION_ID` hoist "right after `INPUT=$(cat)` (~L44)" — i.e. ~L51. But the hook has an **unconditional** re-initializer `SESSION_ID=""` at **L95** (top-level, not inside any conditional). A hoist inserted at L51 is therefore **clobbered back to empty at L95**. Consequences: (1) the reviewer sentinel hash silently degrades to `"unknown-<timestamp>"`; (2) the implementer `--session-id "$SESSION_ID"` fallback always receives `""`, always drops to byte-proxy — defeating the entire purpose of the hoist, and making **Task 4's `test_implementer_logs_via_session_id_fallback`** fail. **Fix:** place the hoist *after* the variable-init block (after L98), or delete/replace the `SESSION_ID=""` line at L95 in the same edit.

**Snippet Verification:**
- **Snippet 1 — probe core (Module 1 Task 1 Step 3 + Task 2 Step 3):** VERIFIED. The four field names, scan-from-end loop, `JSONDecodeError`-skip, and `message`/`usage` dict guards mirror `claude-ctx-check` exactly. `_coerce_int` divergence documented; differential test correctly restricted to well-formed fixtures. `--json` shape matches tests.
- **Snippet 2 — hook helper block (Module 2 Task 3 Steps 4–7):** VERIFIED for placement (`OBS_LOG` after `REPORTS_DIR=` at L108; helpers after the manifest guard at L142; threading before reviewer L208 / re-review L165 / passthrough L242 exits; Check-7 deletion at L754-789 + L814-816 with byte-sum moved into `ctx_byte_estimate`; orphan grep). Caveat: helpers depend on the `SESSION_ID` broken by the hoist defect above.
- **Snippet 3 — tier/block logic (Module 2 Task 5 Steps 3–4):** VERIFIED. HARD block is its own `exit 2` after the `ERRORS[@]` report (not folded in); soft nudge via `${CTX_NUDGE:-}` at the L810 site; `MARKED_FIX` reaches the tail and logs `type=other` with no gating; K-streak escalation is `exit 2` only in the implementer fallback arm, counted with `awk` (no `tac`).

**Cross-Document Audit:**
- `T = input_tokens + cache_creation_input_tokens + cache_read_input_tokens + output_tokens`: spec → parent → probe `FIELDS` → claude-ctx-check L127-132. All agree. ✓
- `SOFT=300000 / HARD=400000`: spec → parent shared_constants → hook env defaults + `HARD ≤ SOFT` revert guard. Consistent; tests override via env. ✓
- observation-log `source=/tier=/action=`: spec → parent → `ctx_log` printf. Consistent. Minor non-blocking: reviewer path logs `type=partner-review`/`trace-audit` (hook's `REVIEW_TYPE`) vs spec's illustrative `partner`/`other` — harmless (tuning filters on `source=probe`, not `type`).

**Recommendations (advisory):**
1. Module 2 Task 3 Step 4 threshold-block: anchor "after ~L27" risks placement before `SUPERPOWERS_ROOT` (L31) → `set -u` unbound-var abort. Instruct placement after **L41** unambiguously.
2. Add `OBS_LOG=""` (and `CTX_NUDGE=""`) to the L70–98 var-init block for `set -u` hygiene.
3. e2e (Task 9): the manual `git init` + `checkout -b ctx-feature` before `setup_full_sdd_workspace` (which git-inits itself) is redundant; trim it. Banner 13→14 correct.

**Size/complexity:** Within bounds — modular, no task > ~200 lines, 11 tasks (0–10) with Write-Scope tables at parent + every module, serial `depends_on` correctly serializes shared-file writes. Only Module 1 declares external Source Contracts and owns Task 0; parent + Modules 2/3 declare "None" per the modular convention. All insertion points, classification vars, exit-path line numbers, the `make_hook_input` top-level seam, the `setup_full_sdd_workspace` signature, SKILL.md word count (4918), and the §272–292 extraction target were verified against source.

---

## Resolution (plan author)

All items addressed in the plan before execution:

1. **BLOCKING — hoist collision (Module 2 Task 3 Step 5):** FIXED per the reviewer's prescription. Step 5 now instructs **replacing the existing `SESSION_ID=""` initializer at ~L95** with the `jq` extraction (a single, clobber-proof edit), with an explicit "do NOT insert at ~L44" warning naming the clobber + the failing Task 4 test. Verified against source: `SESSION_ID=""` is indeed at L95, `SUPERPOWERS_ROOT` at L31.
2. **Advisory 1 — threshold-block placement:** FIXED. Step 4 now states "after the `VALIDATE_REPORT_SCRIPT` line (~L41)… after `SUPERPOWERS_ROOT` is defined (L31)" with the `set -u` unbound-var rationale.
3. **Advisory 2 — `set -u` hygiene:** FIXED. Step 5 now also adds `OBS_LOG=""` and `CTX_NUDGE=""` to the var-init block.
4. **Advisory 3 — redundant e2e git init:** FIXED. Task 9 drops the manual `git init`/`checkout -b ctx-feature`; `setup_full_sdd_workspace` handles git setup.
5. **Non-blocking `type=` enum divergence:** accepted as harmless (documented — threshold tuning filters on `source=probe`, not `type`).

No design changes (the spec is review-closed). All four files re-validated post-fix: `validate-plan.py` → parent PASS, modules WARNING with **zero blockers and zero oversized tasks**. The single blocking issue was a wrong line-number instruction on a TDD-backstopped path; the fix is mechanical and matches the reviewer's own recommended remedy, so no full re-dispatch was warranted.
