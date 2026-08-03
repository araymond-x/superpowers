# Spec Compliance Review — Task 12 (write-mechanics-card.py + golden-file test)

**Model:** sonnet · **BASE** `d1d5a1e` → **HEAD** `7479b29` · **Verdict: PASS** (spec-compliant + contract-compliant, verified by code inspection + independent execution)

## Spec compliance (line-by-line fence diff)
Diffed the generator body against the Step-3 fence and the test file against the Test-harness/Generator-helpers/Step-1 fences. **Exactly one substantive departure** — the single declared deviation:
- `write-mechanics-card.py` `## Paths` "Deviations" line uses the already-computed `deviations_abs` variable instead of re-deriving `os.path.join(git_root, paths.get("deviations_file", ""))`. Output-neutral for every real manifest: `deviations_file` is a non-optional `str` in `sdd_session.py` and always set by `materialize-manifest.py`, so the `.get()` default branch is unreachable; the only behavior difference (an unreachable fallback) can never fire. Properly recorded in `deviations.md` under Module 4/Task 12.

The four test functions match the fences, including the **amended** hook-reading `test_byte_proxy_interference_invariant` (confirmed it `read_text()`s `sdd-pre-dispatch-hook.sh` and asserts `'"$REPORTS_DIR"/*.md'` [hook line ~170] and `'task-${padded}-${report_type}'` [hook line ~336] present — not the old literals-only tuple). Imports are genuine shared-source (`ImplementerReport`, `REQUIRED_SECTIONS`, `derive_expected_hops`/`hop_ceiling`) — none redefined.

## Independent execution proof
- `pytest tests/unit/test_mechanics_card.py -v` → 4/4 PASS (ran directly).
- Built a fresh fixture repo, ran BOTH composed `controller-checkpoint.py` invocations from a generated card verbatim (`<N>`→1): both returned genuine checkpoint JSON (status FAIL, itemized checks, exit 1) — not argument errors. Confirmed `run_pre_dispatch`/`run_pre_completion` hard `sys.exit(3)` on missing `--deviations-file`/`--reports-dir`, so the N35 proof is real.
- Round-tripped the emitted skeleton through `validate-report.py` → `{"status":"COMPLETE","sections_missing":[]}`, exit 0.
- Full unit suite exited 0 — no regressions. No stray live `handoff-mechanics.md` (would be Check-3b-blocking pre-Task-14).

## Contract compliance
- `git show --stat 7479b29` → only the two owned files (258 insertions). No hook, SKILL.md, or baseline.txt touched.
- Import block does `try/except ImportError: sys.exit(2)` as required.

## Advisory notes (not blocking, not Task 12 defects)
- The `fnmatch(name, "*.md")` / `not fnmatch(name, "task-*")` half of the byte-proxy test remains a tautology over the literal `"handoff-mechanics.md"` — but the controller's pre-dispatch amendment ADDED non-vacuous `in hook` assertions, so the test overall has teeth (a hook-glob change breaks it). Flagged so the next reviewer does not re-litigate it as new.
- Implementer's recorded Concern: the card's `ceiling` reads `SUPERPOWERS_CMUX_MAX_HOPS` unvalidated while Task 13's script warns-and-reverts on non-numeric — a display/enforcement divergence to watch in Tasks 13/16, out of Task 12 scope (logged Pending → Task 13/16).

**No BLOCKING, CONTRACT, or MISSING findings.**
