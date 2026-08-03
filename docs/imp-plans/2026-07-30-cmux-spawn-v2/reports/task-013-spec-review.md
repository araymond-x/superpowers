# Spec Compliance Review — Task 13 (durable outcome writes N63 + bookkeeping commit + card invocation)

**Model:** sonnet · **BASE** `8726d22` → **HEAD** `96c4d48` · **Verdict: PASS** (spec + contract compliant, re-derived by code inspection + independent test run)

## Verification
1. **`--no-commit`** — `NO_COMMIT=0` init + `--no-commit) NO_COMMIT=1 ;;` case arm + usage string. ✓
2. **N63 exit-code invariant held** (read all 3 branches): spawn-failed append (L829)→untouched `exit 3` (L839); timeout append (L854)→untouched `exit 3` (L879, in unchanged `case`); success append (L934)→new card/commit block→untouched `exit 0` (L969). No `then` body contains exit/return. The intent/reservation append (L793) was NOT wrapped (correct — not an outcome). ✓
3. **Card+commit success-branch-only** — grepped timeout + spawn-failed branches: no `git commit`/`write-mechanics-card` in either. ✓
4. **No `git add -A`** in executable code (only in a warning comment, L947); commit uses `git add "$HOPS_FILE" "$SPAWN_LOG"` + conditional third add. ✓
5. `--no-commit` skip + commit-failure paths are warn-only, never touch exit. ✓
6. No `set -u/-e/pipefail` added; `bash -n` clean. ✓
7. **BACKLOG N63 → `done`**; N64 correctly left `open` (Step 3 scopes the close to N63 only, though the same task implements N64's bookkeeping commit). ✓
8. `CMUX_SABOTAGE_ON_WAITFOR` stub extension additive + env-gated (unset in all existing tests). ✓
9. **Scope**: `git show --stat 96c4d48` = exactly the 4 files; no baselined hook/SKILL.md/baseline.txt. ✓
10. **Independent test run**: `pytest -k "TestDurableOutcome or TestBookkeepingCommit"` → **10/10 passed** (ran directly). Spot-checked `run_spawn` genuinely subprocess-execs the real `bash spawn-handoff-session.sh` against a real git fixture (only cmux/picker/usage-pace stubbed) — real behavioral tests, not logic mocks.

## Non-blocking notes (both self-disclosed by implementer)
- **[ADVISORY]** `spawn_handoff_helpers.py` edited outside Task 13's Owned-Files table — a plan-internal inconsistency, not overreach: Step 1's pseudocode says "extend the v2 stub," which lives only there. No collateral (test_spawn_handoff.py 73/73; knob env-gated).
- **[ADVISORY]** Bare `git commit` (no pathspec) commits the whole index — a narrow race between Precondition-1's clean-tree check and the commit. This is exactly the plan's fence shape, so not a deviation; correctly flagged as residual risk. (Routed to quality review for adjudication.)

**No BLOCKING, CONTRACT, or MISSING findings.** Report accurate; code matches the fenced pseudocode and the contract constraints.
