# Context Summary — cmux-integration repo-3 SDD (Module 2 active, Tasks 9+10 done)

> Flight-recorder digest. Rich resume guidance is in the handoff bundle's CONTINUE.md.

## Status: **Module 1 complete + transitioned. Tasks 7–10 complete. Resume at Task 11 (the LAST task).**

| Task | State | Commit | Notes |
|------|-------|--------|-------|
| 0–6 | ✅ done (reviewed) | thru `cfe8c27` | Module 1: script + 58-test unit suite. Archived to `reports/archive-…/`. |
| — | ✅ plan surgery | `518875c` | Sweep promoted from unnumbered round → gated Tasks 7-8; old 7/8/9 renumbered → 9/10/11. |
| 7 | ✅ done (reviewed) | `8ea8509` + `4f1328f` | Sweep A: 2 harness knobs + 5 mutation-proven tests. |
| 8 | ✅ done (reviewed) | `7a46dae` + `53318b5` | Sweep B: reservation hardening + 9 tests. Quality found MX1 → fix → re-review PASS. |
| 9 | ✅ **done (reviewed, 2 fix rounds)** | `f787039`+`2fe7a50`+`19096af`, artifacts `f95912c` | Protocol steps 3–5 now DRIVE the script. Quality found 2 Important; fix round A then introduced its OWN false claim, caught by re-review → fix round B. |
| 10 | ✅ **done (reviewed, no fix round)** | `607033a`, artifacts `0a421af` | e2e Step 14 real (non-dry-run) spawn path + banner 15. **THREE defects in the plan's block** — 2 controller pre-dispatch, 1 implementer mid-task. Quality PASS, no findings. |
| 11 | ⬜ **NEXT — LAST TASK** | — | Docs: CLAUDE.md, manifest, BACKLOG N43(D). **7 steps** (1, 1b, 1c, 2, 3, 4, 5). `review_tier: minimum`. |

Suites (controller-verified this session): `validate-all-skills.py` **PASS 159 / FAIL 0 / WARNING 2**; `sdd-e2e-test.sh`
→ **`E2E PIPELINE PASS - 15 steps composed correctly`**. Working tree clean at `0a421af`. **0 pending deviations.**
Module-2 checkboxes: **31 ticked / 9 unchecked** (Task 11: 7, Acceptance criteria 76 + 81: 2).
Manifest: `task_range [7,11]`, `total_tasks 12`, `midpoint`/`context_summary_at` **9**.

**⚠ `spawn-handoff-session.sh` IS FROZEN** (since Task 8). Tasks 9–11 read it only. Task 10's e2e assertions and
Task 11's docs both depend on its current observable behavior.

## ⚠ READ FIRST

1. **The quality review found a real defect on FOUR consecutive tasks (6, 7, 8, 9) and then legitimately found nothing
   on Task 10** — on the *hardest* brief of the run (an assigned mutation re-run, a named high-value hypothesis, and a
   demand to demonstrate rather than speculate). Two lessons, not one: **never thin the review**, and **a clean PASS
   from a hard review is a real result** — do not manufacture findings to keep a streak alive.

2. **THREE separate defects were found in the plan's Task 10 Step 14 block, by three different parties.** (a) Controller
   pre-dispatch: the fixture created the picker version as a **directory**; `preflight_ok()` tests `[ -f ] && [ -x ]`, so
   it degraded to `launch=picker-manual` where the composed command is never built — every composed-command assertion
   vacuous, all six of the plan's assertions still green. (b) Controller: added the `launch=auto` assertion to stop that
   recurring. (c) **The IMPLEMENTER found the block never `cd`s into the fixture worktree** — `WORKTREE_ROOT` is a bare
   `git rev-parse --show-toplevel` (`:53`) against the *caller's* cwd, and the harness `cd "$WORK"` at `:14` and never
   leaves. **The plan's Step 14 as written could not have run at all.** Neither the controller's verification nor the
   partner's independent chain-check caught it — both reasoned about launch-mode semantics; neither asked which
   *directory* the script would resolve. **Ask the dumb question too.**

3. **THREE citation errors in one dispatch, all the same shape: a TRUE fact attributed to the WRONG source.** The MX-A
   rule (cited to Task 7's deviations row — actually the handoff bundle's `CONTINUE.md:39`); stub-on-PATH (credited to
   e2e Step 13 — exists nowhere in the file); the vacuous-lint gotcha (credited to CLAUDE.md — `grep -in 'vacuous'
   CLAUDE.md` returns nothing). The partner caught two and volunteered the third. **A mis-citation is indistinguishable
   from a fabrication to anyone who checks the named source.** Rule: cite the source you actually read it in, or cite
   nothing and state the evidence directly.

4. **A fix round can introduce its own defect.** Task 9 fix round A closed two Important findings and asserted "Step 2
   covers them"; step 2's possessive "**its** reports" binds to the *completed* task, so the claim was false. Round B
   fixed it. Fixed rather than waved through **because Task 9 exists partly to correct a false claim the plan made** —
   two standards for one kind of error would be incoherent.

5. **Positive controls are non-negotiable, and reviewers now run mutating ones.** The Task 9 spec reviewer appended a
   perturbation line to a committed file to prove its diff wasn't no-opping; the Task 10 spec and quality reviewers each
   mutated the FROZEN script. **All restored, and the controller VERIFIED each restore rather than trusting it.** Two
   implementers **elided** their control output as `[... real diff ...]` — an elision is indistinguishable from a check
   that never ran, and the controller re-ran everything. Require pasted output.

## What Task 11 must build on

- **Exit ladder is 0 / 3 / 1 with FIVE distinct exit-3 causes** (six sites): `:125` cmux unreachable, `:137` hop limit,
  `:195` quota low, `:464` + `:469` reservation-write failures, `:491` spawn failed after reservation.
- **The `cd` requirement is a real usage constraint of the script's interface, not a test artifact** — it resolves the
  worktree from the *caller's cwd*. **Add it to the CLAUDE.md section** (new, from Task 10's finding).
- **`cmux notify` asymmetry** (Step 1b): hop-limit / quota-low / spawn-failed DO notify; the two reservation-write
  branches deliberately do NOT. The success-path notify at `:429` is **mode-agnostic** — identical for `auto` and
  `picker-manual`, and never mentions a picker.
- **Step 1c** — four dispositioned doc obligations under the Deferred Work heading titled *"Task 9 doc obligations"*,
  which uses **PRE-RENUMBERING** ids: old-Task-9 = **Task 11**. It does NOT mean the protocol doc.
- Step 14's stub `cmux` never emits `OK <ref>`, so `SPAWN_WORKSPACE_REF` is `(spawned)` in the e2e fixture; the
  ref-parsing branch is unit-tested at `test_spawn_handoff.py:897`/`:916`. Deliberate layering, not a hole.

## Pre-completion gate — FOUR THINGS THAT WILL BITE

1. **The trace audit will silently cover 1 session out of 14.** `extract-execution-trace.py --session-file` takes ONE
   file and the documented discovery is `ls -t … | head -1`. **This run spans 14 jsonl files** under
   `~/.claude/projects/-Users-araymond-projects-claude-custom-superpowers--worktrees-cmux-integration/`. Run naively,
   the auditor sees Task 11 only and returns "no anomalies" — the exact hollow-check class hunted all run. Enumerate all
   14, extract per file, give the auditor everything — **or state partial coverage and which tasks went unaudited.**
2. **No honesty-check log exists anywhere** (`find reports -name 'honesty-check-*'` → nothing, not even archived), so a
   fresh one is required and there is no stale-log risk. The gate's glob (`controller-checkpoint.py:1534`) is
   `reports/honesty-check-*.md` — **FLAT, not archive-aware**; write it directly to `reports/`. **Output the block and
   STOP for the user to paste back — do NOT self-answer it** (same shape as the Task 8 pre-filled partner verdict).
3. **Acceptance criteria 77–80 are ticked and controller-verified.** Criterion 80 was checked **branch-wide** against
   `git merge-base main HEAD` = `4de2020` (empty diff for hook + baseline), not just per-task ranges. **76 and 81
   remain** — 76 needs confirming against the Task 7/8 reports (not personally verified this session), 81 is Task 11's.
4. **Task 11 is `review_tier: minimum`, and the hook DOES accept the exemption filename** —
   `partner-review-011-minimum-tier.md` (`sdd-pre-dispatch-hook.sh:744`, `PARTNER_FILE_MIN`). Verified; no block risk.
   **But minimum tier applies to the docs MECHANICS only — its spec review must verify every factual claim against the
   frozen script.** Claims of exactly that kind have been wrong three times this run.

## Contract facts frozen (unchanged)
- Composed flag order: `claude-picker --non-interactive --pick-version <v> --telemetry <on|off> [--session-label <l>] <args> "/pickup <id>"`. **The label is INCREMENTED** (`Proj-Session-2` → `Proj-Session-3`, `:284`).
- `cmux new-workspace` prints `OK <ref>` on stdout, LF-terminated, rc 0 — parse with `awk`, never `while read`.
- Repo identity = `realpath(git rev-parse --git-common-dir)`. Bash floor **3.2** (`/bin/bash` here IS 3.2.57).

## Process gotchas (still current)
1. `tests.written`/`tests.passing` are **per-round integers**, `passing ≤ written` — never a file total, never a list.
2. **`bash scripts/lint-shell.sh` with no args is VACUOUS post-commit** ("No shell files found."). Use `shellcheck --severity=warning --external-sources <file>` or `--all`. *(This gotcha is from session notes, NOT CLAUDE.md.)*
3. Do **not** add `set -u`/`set -e`/`pipefail` to the script (bash 3.2 `${FORWARDED[*]}` on empty array).
4. Tick plan checkboxes **before** running the next checkpoint; disposition deviations at write time (the hook hard-blocks on any `| Pending |` — including a row you wrote five minutes ago).
5. **Never call the advisor tool while a subagent is live** (unrecoverable API 400).
6. Give every reviewer an explicit **output budget** (700–1400 words; 400–1000 for a re-review). `SendMessage` resume from transcript is the recovery when one dies — used successfully this session for partner round 2.
7. Mutating the frozen script for a proof is fine — restore with `git checkout --`, **never `git stash`**, and **verify** the restore.
8. The manifest was HAND-EDITED at the Task 7/8 surgery. **Do NOT run `materialize-manifest.py`** — it would reset `active_module_id`/`completed_modules` and undo the Module-1 transition.
