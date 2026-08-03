# Task 9 — Spec Re-Review (round 2), scope: commit `7080521` only

**VERDICT: PASS**

Question: is the log-reader consolidation complete and behavior-preserving?

## Findings

1. **Exactly one definition.** `/usr/bin/grep -rn "def.*cmux_log" tests/ skills/` → single hit, `spawn_handoff_helpers.py:111`. The three local `def`s are gone.
2. **Zero orphaned call sites.** No live reference to `_cmux_log_text`/`_cmux_log` survives in `tests/`, `skills/` or `docs/` except in prose. `cmux_log_text` has 25 references across the three files; the 16 renamed sites (4+4+8) reconcile exactly. Positive-controlled: the same ERE pattern class found `_spawn_log_text`/`_cmux_v2_stub`, so the empty result means absence, not a dead probe.
3. **No site silently unbound.** `test_spawn_handoff.py` imported `cmux_log_text` at :95 already — that import predates the fix and is exactly the drift the spec review flagged (import AND local def coexisting). The other two gained the name in existing multi-name import blocks.
4. **The equivalence reasoning verified, not accepted.** The three pre-fix bodies were byte-identical to the helper. The caution "textual identity ≠ semantic identity across module boundaries" is right, and the discharging fact is that the body has **no free variables**: it references only the `tmp_path` parameter and attributes on it — no module-level global, no import, **not even `Path`** (the commit message over-states slightly by naming `Path`; the body never touches it, which makes the argument STRONGER). With no name resolved against `__globals__`, the defining module is provably irrelevant to behavior.
5. **No test semantics shifted.** 773 before and after — but the load-bearing evidence is (4), not the count: a suite holding at 773 is consistent with a behavior change nothing asserts. The free-variable argument is what rules that out.
6. **The five inline sites are genuinely pre-existing and untouched** — `test_spawn_handoff.py` :686/:840/:867/:957/:996 byte-identical between `b3ca14f` and `7080521`. (A sixth existed at `b3ca14f~1:634`, consumed by the Task 9 code commit, not this fix.) Correctly excluded: they read unconditionally and raise `FileNotFoundError` on a missing log where the helper returns `""`, so swapping them would convert a hard failure into a silent empty string in tests whose premise is that the log exists.
