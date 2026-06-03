# Spec Review: Task 4 — SSOT agreement test for the file-based minimum signal (D6)

## Verdict: PASS

The shipped test (`tests/unit/test_ssot_minimum_agreement.py`, commit db7e25f) faithfully implements D6, is non-vacuous (mutation + differential proven), is TEST-ONLY, and the single logged deviation is test-setup-only. One non-blocking plan-hygiene concern carried forward.

### By criterion
1. **Drives BOTH sites via subprocess on the FILE signal** — hook driver (:25-57, needle :57 `quality-review dispatch recorded for Task 0`), transition driver (:60-102, needle :102 `Task 0: quality review not provenance-logged`). Both needles confirmed present in production (hook:537, transition:148) — anti-vacuous. Both sites waive on file-present OR provenance; identical truth tables.
2. **Truth table** — anchor `assert hook == (not min_file and not provenance)` (:118); 4 cases `[(T,F),(F,F),(F,T),(T,T)]` (:105).
3. **mkdir deviation = test-setup only** — difflib vs the plan's verbatim block: ONLY a 5-line insertion (3 comments + 2 mkdir) at the top of `test_minimum_signal_agreement` (:108-111). Driver bodies, needles, parametrize, both assertions byte-identical. Legitimate (drivers git-init-before-mkdir; pytest creates only base tmp_path).
4. **Non-vacuity — two ways:** (a) differential — `(False,False)` returns hook=True,trans=True (each needle literally appeared; both sites accumulate errors, no short-circuit); other 3 cases False. (b) mutation — corrupting the hook needle makes `(False,False)` fail with `hook_requires=False transition_requires=True` (exact disagreement signature) → assertion is load-bearing, not tautological.
5. **TEST-ONLY** — `git show db7e25f --name-only` = exactly one file; no skills/ change.
6. **Report completeness** — all sections present + valid frontmatter.

**Regression (beyond spec):** full unit suite 405 passed, 0 failed; the transition driver's process-scoped `sys.path.insert` does not shadow later tests.

### Non-blocking concern (does NOT downgrade PASS)
- **Plan-hygiene:** the canonical plan.md Task 4 snippet is still un-runnable (lacks the 2 mkdir lines; grep returns 0). The SHIPPED test is correct (4/4). Controller decision: logged as a tracked follow-up (deviations.md Task 4 FollowUp) + routed to BACKLOG; the committed plan is preserved as the approved record (divergence captured in deviations). Not ship-blocking — TEST-ONLY task, delivered artifact correct.
