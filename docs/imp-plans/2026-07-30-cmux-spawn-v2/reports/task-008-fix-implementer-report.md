---
schema_version: 1
task_id: 8
task_type: implementation
status: DONE
files_changed:
  - path: "skills/subagent-driven-development/scripts/spawn-handoff-session.sh"
    description: "Major 1: ceiling derived ONCE into DERIVED, valid env value then overrides; the fence's second copy is gone. Minor 3: elastic-ceiling rationale recorded in the comment (no clamp). Minor 4: usage string + header name --user-approved. Nit: TOTAL_DISP assigned through a temp so the ? placeholder survives an unreadable manifest."
  - path: "tests/unit/test_spawn_handoff_v2.py"
    description: "+7 tests: TestCeilingDerivationIsSingle (2, the invalid-knob path onto the shared derivation), TestMaxStallHopsKnob (2, both halves of the validate-warn-revert contract), TestPolicyOffIsNotBypassable (1), TestTasksDoneFallbackAndDenominator (2, the numeric fallback + the denominator placeholder)"
  - path: "tests/unit/test_handoff_support.py"
    description: "Minor 1: test_shared_constants_are_the_ssot_the_shell_mirrors now READS spawn-handoff-session.sh, extracts floor/factor from the executable lines and asserts exactly one of each; HOP_DIVISOR documented as deliberately Python-only"
  - path: "docs/imp-plans/2026-07-30-cmux-spawn-v2/deviations.md"
    description: "Three rows: the Major 1 fence divergence, the Minor 3 considered-and-rejected clamp, and the fix-round review-efficacy note"
tests:
  written: 7
  passing: 7
  command: ".venv/bin/python3 -m pytest tests/unit/ -q -p no:cacheprovider"
  result: PASS
contract_compliance:
  - constraint: "Bash >= 3.2; NO set -u/set -e/pipefail; never pipe a producer into grep -q"
    status: compliant
    detail: "bash -n clean on /bin/bash 3.2.57. No set flags added, no new pipelines. The collapsed derivation uses if/fi rather than the compound && form, so no statement's exit status is load-bearing."
  - constraint: "All env knobs validate-warn-revert; .handoff-hops's fail-closed numeric guard is the ONE fail-closed guard and stays untouched"
    status: compliant
    detail: "MAX_HOPS keeps warn-and-revert; the revert target is now the single derived ceiling. MAX_STALL_HOPS's contract is unchanged and now has BOTH halves pinned. The .handoff-hops guard is byte-identical."
  - constraint: "Shared Constants: the shell's floor and factor are the one sanctioned duplication, NAMED by a comment citing _handoff_support.py as SSOT"
    status: compliant
    detail: "The comment stays and is now backed by a test that actually reads the shell. Divergence in either literal, and re-duplication of the derivation, both FAIL."
  - constraint: "Reservation BEFORE spawn; policy-off/policy-ask are pre-reservation; exit codes stay 0/3/1"
    status: compliant
    detail: "No change to ordering or the exit ladder. The new off-with-flag test asserts exit 3, no .handoff-hops, no intent record."
  - constraint: "Write scope: spawn-handoff-session.sh, _handoff_support.py, the five test files, fixtures, deviations.md"
    status: compliant
    detail: "Four files touched, all in scope. _handoff_support.py needed no change. module-2-models-budget.md, BACKLOG.md and references/context-handoff-protocol.md untouched."
---

**Implementation Summary:**
Closed all four surviving mutations plus the four smaller findings. The only structural change is Major 1: the ceiling derivation is now computed once and the plan's second copy is deleted. Everything else is a test that did not exist, one comment that recorded a decision, and two one-line honesty fixes (usage string, denominator placeholder).

**Per-finding disposition, with mutation evidence.** Every mutation was applied by an exact-string replacer that asserts the anchor matches EXACTLY ONCE and refuses otherwise (a 0- or 2-match `sed` reads as SURVIVED); the mutation diff was printed against a file-copy baseline on every run — never `git diff`, whose output was polluted by legitimate uncommitted work, and never `git checkout --`/`git stash` for restore. Each restore was byte-verified with `diff -q`.

| Finding | Status | Mutation applied | Result |
|---|---|---|---|
| **Major 1** (duplicated ceiling) | **Fixed — structural** | `DERIVED=$((EXPECTED_HOPS * 2))` → `* 99` (the review's M15, now against the single derivation) | **RED** — `TestCeilingDerivationIsSingle::…refuses_at_it` AND the pre-existing `test_ceiling_derived_from_expected_hops_refuses_at_the_ceiling`. Both paths now fail together, which is the point. |
| **Major 2a** (stall knob fail-open) | **Fixed** | deleted the `MAX_STALL_HOPS` validate-warn-revert block (the review's M11) | **RED** — `test_invalid_knob_warns_and_the_stall_gate_still_refuses` only. Confirms it is the invalid-knob half. |
| **Major 2b** (stall knob inert) | **Fixed** | `MAX_STALL_HOPS="${SUPERPOWERS_CMUX_MAX_STALL_HOPS:-$…}"` → `="$MAX_STALL_HOPS_DEFAULT"` (M13) | **RED** ×2 — including `test_raised_knob_is_honoured_and_the_same_chain_proceeds`, the test that exists for exactly this mutation. Two mutations, two distinct REDs, as the sibling-knob precedent has. |
| **Major 3** (`off` bypassable) | **Fixed** | `if [ "$SPAWN_POLICY" = "off" ]` → `… && [ "$USER_APPROVED" != "1" ]` (M12) | **RED** — `test_off_refuses_even_with_user_approved`; the six pre-existing policy tests all still PASSED under the mutation, which is the exposure the finding describes. |
| **Minor 1** (misleading SSOT test) | **Fixed — made real, not renamed** | (a) shell `DERIVED=6` → `9`; (b) `* 2` → `* 99`; (c) re-inserted a second `DERIVED=6` line | **RED** ×3 on `test_shared_constants_are_the_ssot_the_shell_mirrors`. It catches floor drift, factor drift, AND re-duplication. |
| **Minor 2** (`TASKS_DONE` fallback) | **Fixed** | deleted `[[ "$TASKS_DONE" =~ ^[0-9]+$ ]] \|\| TASKS_DONE="unknown"` (M14) | **RED** — `test_failed_tasks_done_cli_degrades_to_unknown_with_a_diagnostic`. Exit code stayed 0 under the mutation, so the assertion that bites is on the diagnostic string, not the return code. |
| **Minor 3** (no upper clamp) | **Deliberate non-change, justified** | n/a | See below. |
| **Minor 4** (usage/header) | **Fixed** | n/a (documentation strings) | Both now read `BUNDLE_ID [--dry-run] [--user-approved]`. |
| **Nit** (`TOTAL_DISP`) | **Fixed and pinned** | restored the one-line form | **RED** — `test_stall_refusal_keeps_its_denominator_placeholder`; the mutated run's stderr renders literally `at tasks 3/, hops 2`, reproducing the defect. |
| **Minor 5** (protocol doc) | **Not done — not my scope** | n/a | `references/context-handoff-protocol.md` is Module 4's write scope, scheduled at Task 16. Untouched, as instructed. |

**Minor 3 — the deliberate choice, and why.** Left unclamped, and recorded in the script's comment plus `deviations.md`. Two grounds: (a) `expected_hops` is **plan-author-declared and schema-validated**, so an author who writes 500 has declared a 500-hop plan — elasticity in it is the intended semantics, not an escape from the guard; (b) a `CEILING_MAX` has **no Python twin** — `hop_ceiling()` in `_handoff_support.py` has no clamp and `materialize-manifest.py` also consumes it — so clamping means either a fourth un-mirrored shell literal in the exact region Task 9 edits, or an unauthorized production edit to the shared formula. The runaway shape the ceiling cannot see (spawning without progressing) is the stall gate's job, and the stall gate is now pinned in both directions for the first time. Flagged as a candidate BACKLOG row in Concerns; `BACKLOG.md` was not touched.

**Source Files Read:**
- `reports/task-008-quality-review.md` (whole), `reports/task-008-implementer-report.md`, `module-3-spawn-script.md` Task 8 (incl. step (e)'s fence), `deviations.md` tail, `spawn-handoff-session.sh`, `_handoff_support.py`, `test_handoff_support.py`, `test_spawn_handoff_v2.py`, `spawn_handoff_helpers.py`, and the sibling-knob precedent in `test_spawn_handoff.py` (`test_invalid_quota_min_pct_warns_and_reverts_to_default` / `…timeout_warns_and_quota_gate_stays_live`) plus `test_spawn_handoff_hardening.py::test_nonnumeric_max_hops_…`.

**CLAUDE.md Files Read:**
- Repo root — no line numbers in the cmux section (cited constructs, not coordinates, throughout); `/usr/bin/grep` not the ugrep wrapper; zsh does not word-split, so every pytest invocation used explicit paths; never `git add -A`, never `git stash`, commit via `git commit -F -` with a quoted heredoc after checking `git diff --cached --stat`; bash floor 3.2 and no `set -u`/`set -e`/pipefail; B7 directory inversion (moot — `_handoff_support.py` needed no change).

**Deviations from Plan — read this before the spec re-review:**
1. **Major 1 makes the landed code diverge from step (e)'s fence, deliberately.** The fence has the derivation TWICE; the landed code has it ONCE. A mechanical fence diff will report three things: (a) the fence's `else MAX_HOPS=6 / [ … ] && { MAX_HOPS=$((EXPECTED_HOPS * 2)); … }` branch is **gone**; (b) the invalid-knob branch no longer contains a derivation; (c) the WARNING now interpolates `$SUPERPOWERS_CMUX_MAX_HOPS` instead of `$MAX_HOPS` — the same value, because `MAX_HOPS` is no longer pre-assigned to the invalid string before the check. Recorded as a `PlanDeviation` row in `deviations.md`. Every behavior the existing suite pins was preserved and re-verified: the `WARNING:`+`MAX_HOPS` assertion, `MAX_HOPS=0` as a deliberate kill switch, `SUPERPOWERS_CMUX_MAX_HOPS=""` falling through to derived (the `NO_AMBIENT_HOP_KNOBS` channel), env-wins-absolutely, and the `-ge` refusal boundary.
2. **Chose `if`/`fi` over the fence's compound `&&` form** for the derivation body. No behavior change without `set -e`, but the form is now what the SSOT test's regexes anchor on, so the shape is deliberate rather than incidental.
3. **`_handoff_support.py` was in write scope and needed no change** — every finding was in the shell or in the tests.
4. **Plan checkboxes left unticked** — the plan file is not in implementer write scope.

**Self-Review Findings:**
- **The Major 1 fix is only load-bearing because the derivation is single, and that is a fragile property.** `TestCeilingDerivationIsSingle`'s docstring says so explicitly, and the SSOT test now asserts `len(seed) == 1` / `len(factor) == 1` / `len(floor_cmp) == 1`, so re-duplicating the derivation fails a test rather than silently splitting coverage again. That assertion is the durable half of the fix; the two behavior tests are the visible half.
- **The SSOT test's regexes were nearly a false pass.** The derivation's own SSOT comment quotes both literals ("max(6, 2 x expected)", "the literals 6 and 2"), and the file also carries `MAX_STALL_HOPS_DEFAULT=1`, `QUOTA_MIN_PCT_DEFAULT=15`, `QUOTA_TIMEOUT_DEFAULT=60`. Anchoring on the executable lines was necessary, and positive-controlling it (three mutations) was the only way to know the anchor bites rather than merely matching something.
- **Anchor-uniqueness caught one real hazard**: a naive `DERIVED=6` anchor matches TWICE (the seed line and the floor-comparison tail), which would have silently no-op'd or double-mutated. The replacer's `!= 1` refusal surfaced it before it could read as SURVIVED.
- **Exit code could not distinguish the Minor 2 fix from its absence** — both spawn, both exit 0. The assertion had to be on `"tasks_done could not be counted"`. Same shape as the P7-4 finding the original implementer made: a fallback whose failure mode is silence needs a test on the message, not the status.
- No instrument failures this round: every mutation printed a diff against the file-copy baseline, every anchor count was asserted, every restore was byte-verified, and each of the seven new pins was shown green at HEAD before being shown RED under its mutation.

**Concerns:**
1. **Minor 3 is a recorded non-fix, not an oversight** — the elastic ceiling is a deliberate design position with the reasoning in the code and in `deviations.md`. **Candidate BACKLOG row for the controller** (a `CEILING_MAX` mirrored on both sides of the seam, if the position is ever revisited); `BACKLOG.md` is owned by a concurrent session and was not touched.
2. **Minor 5's window is still open.** `references/context-handoff-protocol.md` still says "Default limit 3" and omits `policy-off`/`policy-ask`/`stall` from its exit-3 list. Scheduled at Task 16; Tasks 9–15 sit in between, and `policy-ask` is the retryable cause a controller most needs the doc to be right about. Not mine to fix.
3. **`BUDGET_FLAG` remains the one new SC2034**, unchanged from the original report — Task 9 must consume it or remove it.
4. **Task 9 edits this exact region.** The single derivation, the `DERIVED` variable name, and the three SSOT-test regexes are now coupled: renaming `DERIVED` or reflowing the derivation onto one line will fail `test_shared_constants_are_the_ssot_the_shell_mirrors`. That is intended (the test is the seam guard) but Task 9's implementer should know the test reads the shell before it starts editing it.
5. **Measured suite: 748 passed** (741 baseline + 7 new), 189.60s. `bash tests/integration/sdd-e2e-test.sh` → **PASS, 15 steps** (incl. Step 14, which drives this script). `bash -n` clean on `/bin/bash` 3.2.57. Seam imports re-verified present at HEAD after committing (`git show HEAD:tests/unit/test_handoff_support.py`) — the formatter did not strip them a fifth time.
6. One commit: `2f677e6`.
