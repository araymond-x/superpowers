---
schema_version: 1
task_id: 8
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/subagent-driven-development/scripts/spawn-handoff-session.sh"
    description: "Steps 4(a)-(f): --user-approved flag; Precondition 2b consent gate (pre-reservation); Layer-0 MAX_HOPS block deleted and its validate-warn-revert moved into a derived max(6, 2x expected_hops) ceiling; MAX_STALL_HOPS knob + stall gate; advisory over-expected notify; intent record carries tasks_done="
  - path: "skills/subagent-driven-development/scripts/_handoff_support.py"
    description: "P7-1(ii) spawn-policy fails closed to ask on present-but-invalid declarations (key-presence discriminator); P7-3 yaml probed once before the glob; P7-6 UnicodeDecodeError joins the per-file skip; P7-8 FileNotFoundError split from other OSError"
  - path: "tests/unit/test_handoff_support.py"
    description: "+15 tests: P7-2 stall-streak CLI coverage, P7-1(ii)/P7-5 consent batteries with positive control, P7-3/P7-7 yaml-less pair, P7-6, P7-8 pair, P7-9(A)(B)(D), and the SSOT constants assertion that makes the seam imports load-bearing"
  - path: "tests/unit/test_spawn_handoff_v2.py"
    description: "+19 tests: TestPolicyDial (6) and TestStallAndCeiling (13), incl. the unknown-branch pin and two positive controls"
  - path: "tests/unit/spawn_handoff_helpers.py"
    description: "Step 1 helpers (write_manifest, write_done_report, append_outcome, _commit, _spawn_log_text_or_empty) + NO_AMBIENT_HOP_KNOBS neutralizer"
  - path: "tests/unit/test_spawn_handoff.py"
    description: "Three of B1's four breaking-consumer migrations: explicit MAX_HOPS=3 on test_hop_limit_exits_3, rendered Hop 1/3 -> Hop 1/6, intent field-set equality gains tasks_done"
  - path: "tests/unit/test_spawn_handoff_hardening.py"
    description: "B1's fourth consumer: seed raised 3 -> 6 (the derived ceiling) so the fail-open regression is pinned; docstring corrected"
  - path: "docs/imp-plans/2026-07-30-cmux-spawn-v2/deviations.md"
    description: "Two rows: the seam-import strip recurrence (mitigation changed to structural) and three silent instrument failures"
tests:
  written: 34
  passing: 34
  command: ".venv/bin/python3 -m pytest tests/unit/ -q -p no:cacheprovider"
  result: PASS
contract_compliance:
  - constraint: "Bash >= 3.2; NO set -u/set -e/pipefail; printf not echo for composed strings; never pipe a producer into grep -q"
    status: compliant
    detail: "bash -n passes on /bin/bash 3.2.57. No set flags added. The intent record uses printf. No new grep in the shell at all this task."
  - constraint: "All env knobs validate-warn-revert; .handoff-hops's fail-closed numeric guard is the ONE fail-closed guard and stays untouched; SUPERPOWERS_CMUX_MAX_HOPS keeps validate-warn-revert but its validation MOVES into the ceiling derivation"
    status: compliant
    detail: "MAX_STALL_HOPS follows the existing pattern verbatim. The .handoff-hops guard is byte-identical (its 4 hardening tests still pass). The MAX_HOPS knob warns and reverts to the DERIVED ceiling instead of a fixed 3."
  - constraint: "Reservation BEFORE spawn; policy-off/policy-ask are pre-reservation (no hop consumed); exit codes stay 0/3/1"
    status: compliant
    detail: "The gate sits immediately after validate_bundle, before the cmux-reachable check. Both policy tests assert .handoff-hops does not exist and no intent record was written. Exit ladder unchanged."
  - constraint: "Shared Constants: import HOP_DIVISOR/CEILING_FLOOR/CEILING_FACTOR; the shell's 6 and *2 are the one sanctioned duplication, NAMED by a comment citing _handoff_support.py as SSOT"
    status: compliant
    detail: "Comment present at the derivation. Both sides re-verified consistent, and the duplication is now test-enforced by test_shared_constants_are_the_ssot_the_shell_mirrors."
  - constraint: "A received token is the ONLY exit-0 path; fallback fires ONLY before the launch command is accepted"
    status: not_applicable
    detail: "Handshake and topology are Tasks 9-10. Task 8 did not touch the spawn sequence beyond the intent record."
---

**Implementation Summary:**
Built the supply side first (Step 2b's eight `_handoff_support.py` rows), then the shell that consumes it — step (e) branches on the new `unknown`/`indeterminate` returns, so building them in the other order would have meant debugging two layers at once. Every guard was mutation-tested RED with a paired positive control; the four B1 breaking consumers were confirmed empirically by running them before migrating (three failed while an identifier grep for `MAX_HOPS` scores them 0).

**Register enumeration (done independently, not inherited):** `deviations.md` lines 158, 166–175, 179 carry exactly **eleven** scheduled rows — B1, P7-1…P7-9, OP-1 — plus the STANDING RULE at line 171, which is a constraint on the work rather than a unit of it. That matches the dispatch's count.

**Per-row disposition:**

| Row | Status | Evidence |
|---|---|---|
| **B1** | **PARTIALLY discharged — Task 9's half is outstanding by design** | Task 8's clause (pin the moving default) is done across all four consumers. Line 158's *second* clause — rewrite `_did_not_spawn` to assert absence of every spawn verb plus a positive control — belongs to Task 9, because `"new-workspace" not in log` only goes fail-open once Task 9 switches to `new-surface`. **Do not close this row.** |
| **P7-1(i)** | already applied to the plan; implemented as written | `*) SPAWN_POLICY="ask"`, stderr not discarded. Mutation to `"auto"` → RED. |
| **P7-1(ii)** | fixed | Key **presence** is the discriminator, not `.get()`: `handoff: null` and an absent `handoff` key both yield `None` through `.get()` yet must resolve oppositely. 8 invalid forms → `ask`; positive control (legacy no-key manifest, and explicit `auto`) → still `auto`. Two mutations RED. |
| **P7-2** | fixed | 3 new `stall-streak` CLI tests, incl. P7-8's degraded return. |
| **P7-3** | fixed | Probe before the glob. Pinned on **empty AND absent** reports dirs with yaml shadowed; mutation (probe → `None`) RED. |
| **P7-4** | **already-satisfied — measurement AGREES with the disclosed expectation** | `stall-streak --tasks-done unknown` → exit 2 (run directly). Shell branches on `unknown` at line 253, before the call at 256. **Bonus finding: that branch was itself unpinned** — deleting it left `STREAK` empty, matching neither arm, so the script proceeded silently. Now pinned by `test_unknown_tasks_done_skips_the_stall_check_and_is_recorded` + its control; mutation RED. |
| **P7-5** | fixed | `5` / `null` / `[1,2]` / `"auto"` / `true` → `ask`. |
| **P7-6** | fixed | `except (OSError, UnicodeDecodeError)`. **Chose skip over `errors="replace"`**: undercounting biases toward a spurious stall *refusal* (fail-closed), while decoded garbage biases toward disabling the guard. Function + CLI tests; mutation RED. |
| **P7-7** | fixed | `ImportError`-raising `yaml.py` on `PYTHONPATH`, positive-controlled (the venv ships PyYAML). Populated-dir fixture, kept **separate** from P7-3's empty-dir pin. |
| **P7-8** | fixed | `FileNotFoundError` → `0` **before** `except (OSError, UnicodeDecodeError)` → `indeterminate`. Unreadable fixture is a **directory** (what the register measured). Two mutations RED: blanket-OSError and reversed order. Also added `assert "stall=indeterminate" not in r.stderr` to `test_first_hop_baseline_not_stall` — without it that test passes under both handlers. |
| **P7-9** | fixed (A, B, D) | (A) unreadable manifest → `unknown`. (B) behavioral pin: importing the module with yaml shadowed must succeed; a real hoist → RED. (D) non-dict `handoff` re-derives; mutation RED. |
| **OP-1** | already discharged by the controller | Acknowledged; no action. |
| **STANDING RULE** | complied, not vacuously | No count-based bool fixture was added. The one bool JSON body (`true` in the non-object battery) discriminates via the non-dict guard, not by set-collapse — so the `True == 1` aliasing trap is not reachable in anything written here. |

**Source Files Read:**
- The plan (whole), `deviations.md`, `_handoff_support.py`, `test_handoff_support.py`, `spawn-handoff-session.sh`, `spawn_handoff_helpers.py`, `test_spawn_handoff_v2.py`, `test_spawn_handoff_hardening.py`, and the four relevant regions of `test_spawn_handoff.py`.

**CLAUDE.md Files Read:**
- Repo root — B7 directory inversion (no annotations were added to `_handoff_support.py` at all, so B7 is moot rather than remembered); never `git stash`; `--no-verify` + diffstat procedure; the ugrep/`grep` gitignore trap (used `/usr/bin/grep` throughout).

**Deviations from Plan:**
- **Two comment blocks outside the fences**, declared so the mechanical fence diff does not report them: (1) a `# NOTE:` stub where step (b) deleted the Layer-0 `MAX_HOPS` block, explaining that its validation moved; (2) the deleted block's **fail-open rationale** preserved immediately above step (e)'s fenced derivation. Everything inside the fences is verbatim.
- **`test_ceiling_derived_from_expected_hops` split into two tests.** The proceeding half consumes a hop and dirties the fixture tree, so the refusing half cannot share it. Both halves land, and the `* 2` pin is intact (`hops 9` proceeds, `hops 10` refuses at a derived ceiling of 10 — above the floor, as the plan requires).
- **Two tests beyond Step 2's list**: `test_unknown_tasks_done_skips_the_stall_check_and_is_recorded` + its control (P7-4's shell branch was unpinned), and `test_ambient_hop_knob_neutralizer_actually_bites` (positive control on the env neutralizer — an empty override and an absent ambient var are otherwise indistinguishable).
- **B1's register token departed from deliberately.** Line 158 says "Task 8 pins `SUPERPOWERS_CMUX_MAX_HOPS=3`". Done for `test_hop_limit_exits_3`, but for `test_nonnumeric_max_hops_reverts_to_default_and_still_refuses` the seed was raised to `.handoff-hops=6` instead — setting the knob there destroys the test's premise, which *is* an invalid knob. Surfaced rather than reconciled (the R3-2 pattern).
- **Wrote `deviations.md`**, outside the listed write scope but explicitly directed by the dispatch. Two rows, no existing rows touched.
- **Plan checkboxes left unticked** — the plan file is not in implementer write scope; the controller's call.
- `module-2-models-budget.md` untouched, as instructed.

**Self-Review Findings:**
- The first mutation harness restored via `git checkout --` and **destroyed all uncommitted production edits**; the next four mutations then reported `ANCHOR-FAIL 0 matches`, which reads as a harness problem, not as "your work is gone". Re-applied and switched to file-copy restore.
- The agent shell is **zsh**, which does not word-split `$T` — a six-mutation battery ran against zero tests and reported `no tests ran in 0.00s` each time. Re-run with explicit paths and an unmutated positive control printed first; all six then went RED.
- `grep 'A$\|B'` in BRE treats `$` as a **literal**, so an SSOT-literal sweep missed the `MAX_HOPS=6` line it existed to find. `-E` returned it; both sides re-verified consistent.
- A formatter (not a git hook — this repo has none, so `--no-verify` is irrelevant) stripped the `HOP_DIVISOR`/`CEILING_FACTOR` seam imports a **fourth** time. Restoring an unused import invites a fifth, so they were made load-bearing via an SSOT constants assertion — which is also the guard the derivation's SSOT comment implied but nothing enforced.
- **Caller audit** on the three changed contracts (`count_tasks_done` now raises where it returned `0`; `stall_streak` gained a return value; `_frontmatter` gained a parameter): the only non-test callers are inside `_handoff_support.py` itself, and the CLI wraps `count_tasks_done` in `except ImportError`. The other `*frontmatter*` hits are unrelated same-named functions in `validators.py`, `materialize-manifest.py`, `context-summary.py`, `controller-checkpoint.py`, `validate-plan.py`. No regression surface.

**Concerns:**
1. **`BUDGET_FLAG` is a new SC2034** (baseline at `HEAD~3` had zero; now one). Deliberate forward reference — Task 9's outcome `printf` consumes it per the plan's fence (d). Consistent with the SC2034s BACKLOG N32 already tracks in this tree. Not fixed, to avoid churning a variable Task 9 will use.
2. **Module 2's `[~]` acceptance checkbox condition is now met** — P7-3, P7-6 and P7-8 all landed, so `tasks-done`/`stall-streak` print `unknown`/`indeterminate` as values at exit 0. `module-2-models-budget.md` was NOT edited; flipping it is the controller's call.
3. **`test_cli_failure_is_non_consent` is a hang risk if ever edited.** Its `python3` stub `exec`s by **absolute path** (`sys.executable`); a bare `exec python3 "$@"` re-enters the stub and spins forever inside the untimed suite. The reason is in a code comment.
4. The full suite ran **741 passed** (707 baseline + 34). Regression validator PASS (160/0/2 warnings), e2e PASS (15 steps, incl. Step 14 which drives this script), `bash -n` clean on bash 3.2.57.
5. Three commits: `239532a` (feature), `43ff224` (seam restoration), `31519be` (deviations rows).
