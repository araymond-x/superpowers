# Pre-Execution Audit — Verdict + Remediation

**Verdict:** ORDERS_ISSUED → both orders RESOLVED before any task dispatch.

## Order 1 — Task 3 TDD-cycle assumption (Moderate)

**Finding:** Because Pydantic runs nested-model field validators during parent construction, once Task 2's `Handoff` `mode="before"` validator lands, `SddSession(handoff={"spawn_policy": False, ...})` already coerces to `"off"` on its own. Task 3's "verify failure" step likely finds no red state — the plan's own hedge anticipated a *different* failure mode, not *no failure at all*.

**Resolution:** Edited `module-1-consent-model-coercion.md` Task 3 Step 2 to state plainly that the assertion may already PASS after Tasks 1+2 land (expected, not a violation), that Task 3's normalization is defense-in-depth (protects a manifest constructed via a path other than the plan-frontmatter dict), and that the implementer should proceed to Step 3 regardless and note the pre-passing state in the task report. RESOLVED.

## Order 2 — Task 12 test-harness env-isolation gap (Moderate)

**Finding:** `tests/unit/test_mechanics_card.py`'s `_run_card(wt, feat)` (line ~34) strips all `SUPERPOWERS_CMUX_*` env vars by design; the plan's pseudocode called `_render_card(..., env=...)` without disclosing this isolation guarantee or how to extend it safely.

**Resolution:** Edited `module-4-hook-papercuts.md` Task 12 Step 1 to explicitly instruct extending `_run_card`'s signature with `env_extra=None` merged in after the ambient-strip, and to explicitly avoid a plain unfiltered `env=` passthrough that would leak ambient values into other tests in the file. RESOLVED.

## Self-Assessment Cross-Reference

The auditor independently verified the plan's line-number, word-count, test-class, function-signature, and grep-target claims against live repo state (plan.py, sdd_session.py, materialize-manifest.py, spawn-handoff-session.sh, sdd-pre-dispatch-hook.sh, sdd-stop-hook.sh, write-mechanics-card.py, writing-plans/SKILL.md, SDD SKILL.md word counts, BACKLOG rows) — all matched with high fidelity. The N84 regex-escape fix was verified end-to-end by constructing both the buggy and fixed regex against the plan's own decoy test case. No other gaps found.

**Proceeding to Task 0.**
