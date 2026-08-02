# Task 10 — proposed implementer dispatch prompt

You are an implementer subagent executing Task 10 of an SDD plan. You have NO prior session context — everything you need is below or in the files it names.

## Location

Worktree: `/Users/araymond/projects/claude-custom/superpowers/.worktrees/cmux-spawn-v2` (branch `cmux-spawn-v2`). Work ONLY there. Tree is clean.

Read the worktree root `CLAUDE.md` AND any subdirectory `CLAUDE.md` covering files you touch.

## Your task

`docs/imp-plans/2026-07-30-cmux-spawn-v2/module-3-spawn-script.md`, **"Task 10: wait-for handshake, re-wait, read-screen diagnosis"** (line 547ff). Read the whole task including the ROUTING note at its head, all four steps, and the Module 3 Acceptance Criteria at the end of the file. The plan is the source of truth — implement against it, not against your assumptions.

Task 10 replaces Task 9's placeholder timeout tail with: a bounded `wait-for` token handshake, exactly one re-wait at the same duration, and `read-screen` diagnosis enrichment that classifies WHY a handshake timed out.

**The single most important semantic in this task: a received token is the ONLY success signal.** `diagnose_target` NEVER selects the exit code — it is enrichment only. A stubbed banner on screen with no token is NOT success; that mistake caused three live incidents.

## Contract Constraints (verbatim from the module header — do not paraphrase)

> Bash ≥ 3.2; NO `set -u`/`set -e`/pipefail; `printf` not `echo` for composed strings; never pipe a producer into `grep -q` (use here-strings); all env knobs validate-warn-revert (`.handoff-hops`'s fail-closed numeric guard is the ONE fail-closed guard and stays untouched; `SUPERPOWERS_CMUX_MAX_HOPS` keeps its validate-warn-revert contract but its validation MOVES into the ceiling derivation — Task 8(b)/(e)); reservation BEFORE spawn; a received token is the ONLY exit-0 path; fallback fires ONLY before the launch command is accepted (`cmux send` rc 0 = accepted — after that, NEVER spawn again); `policy-off`/`policy-ask` are pre-reservation (no hop consumed); exit codes stay 0/3/1.

These are derived from source and frozen into Task 0 fixtures. **If your implementation contradicts these constraints, STOP and report BLOCKED. Do not work around a constraint — surface the conflict.**

Source Contracts: **None** (external contracts were frozen into fixtures by Module 1's Task 0). The binding fixtures are `tests/unit/fixtures/spawn-handoff/cmux-verb-shapes.json` and `cold-start-timing.json` — both **READ-ONLY source of truth**. If a stub's shape disagrees with the frozen fixture, the fixture wins.

## Write scope — SIX paths

WRITABLE:
- `skills/subagent-driven-development/scripts/spawn-handoff-session.sh`
- `tests/unit/test_spawn_handoff_v2.py`
- `tests/unit/test_spawn_handoff.py`
- `tests/unit/spawn_handoff_helpers.py`
- `tests/unit/test_spawn_handoff_hardening.py`
- `tests/unit/fixtures/spawn-handoff/` (including the new `screens/` subdir Step 1 creates)

READ-ONLY, never edit: `skills/subagent-driven-development/scripts/_handoff_support.py`, `tests/unit/test_handoff_support.py`, every plan/module file, `BACKLOG.md` (owned by a concurrent session), and the two Task 0 fixture JSONs.

`tests/integration/sdd-e2e-test.sh` is RED right now by design and stays red until Task 17, which owns that rewrite. **Do not touch it, do not run it, do not report it as a Task 10 failure.**

## THE HEADLINE: the plan's screen anchors WERE invented — they are now fixed, and you must not un-fix them

The original Task 10 fence told you to grep for `Do you trust the files in this folder?`. **That phrase appears NOWHERE in the frozen Task 0 capture** (measured, with a positive control: the string `trust` *is* present in that fixture, so the instrument works). The real measured anchors, under `cmux-verb-shapes.json` → `trust_dialog_screen.candidate_anchors`, are `Quick safety check: Is this a project you created or` and `1. Yes, I trust this folder`.

The compounding half is worse: run against the one live capture that carries a screen, the fence's **banner** regex `claude code|esc to interrupt` **MATCHES** while its **trust** regex does not. So a real trust modal would be classified `banner`, and the operator told *"attach to that tab and continue there"* instead of *"answer the trust dialog"* — the exact failure `deviations.md:18` exists to prevent.

**And it would have shipped GREEN**, because Step 1 originally told you to author a fixture containing the invented phrase: code and fixture agreeing with each other, both disagreeing with reality. **A fixture authored to match the code under test proves only that you can spell the same string twice.**

**Then the controller's own FIX for that carried a second false claim**, caught by partner round 2: it asserted the three non-trust screens were "synthetic by necessity (Task 0 captured no live screen for them)". Also false. `cmux-verb-shapes.json` is `captured: "live"` throughout; `rc_confirmation_screen` holds **two live captures of a running Claude session** (`rc_screen`, `rename_screen`) — exactly the `banner` branch's semantic — and `read_screen_cold` is the live capture behind the `internal_error` disjunct. **Measured consequence: the banner regex matched NEITHER live session** (both fell through to `diagnosis=none`), breaking the module AC's "banner steers to the existing tab" against real evidence.

Take the lesson, because it will apply to your work too: **when you correct an evidence defect, your correction is itself an evidence claim and must be measured to the same standard. "No capture exists" is a NEGATIVE claim, and negative claims are exactly the ones a broken instrument manufactures.**

The plan is amended twice over. Consequences you must honor:
- `trust-dialog.txt` is **DERIVED from the frozen capture verbatim**, never hand-authored, with a test pinning it against that capture so the two cannot drift. `banner.txt` likewise derives from `rc_confirmation_screen.rc_screen`, and BOTH live captures must pin to `diagnosis=banner`.
- The trust grep **must precede** the banner grep in `diagnose_target`, and a test pins that ordering. Reordering them silently misroutes a trust modal.
- Banner anchors, chosen by measurement: `shift+tab to cycle` is **MEASURED** (in both live captures, absent from the trust screen). `esc to interrupt` is a **LABELLED INFERENCE** covering the busy state — it occurs zero times in the whole fixture because both captures are idle. `claude code` is **REMOVED**: it matches only the trust screen and neither running session.
- **THREE anchors are MEASURED** (trust-dialog, banner, the `internal_error` disjunct); only `picker-error` is genuinely un-captured. Step 3b asks you to label provenance **PER ANCHOR, not per branch, in THREE categories — MEASURED / INFERRED / INVENTED.** The `banner` branch alone holds two anchors of different provenance (`shift+tab to cycle` measured, `esc to interrupt` inferred), so a per-branch label would read MEASURED wholesale and the inference would silently vanish. **Do not mislabel a measured anchor as invented, and do not label an invention as measured.**
- The frozen fixtures are READ-ONLY and win every tiebreak. **If a stub or a fixture you write disagrees with `cmux-verb-shapes.json`, you are wrong, not the fixture.**

## Obligations the plan carries that are easy to miss

The controller's pre-dispatch obligation audit and the partner review found these. Each is now written into the plan text, but they are called out here because several contradict what a careless reading would conclude.

1. **Step 2's import assertion is ALREADY LANDED — VERIFY it, do NOT re-add it.** Task 9 pre-empted it. It lives in `test_spawn_handoff_v2.py` (the `cold-start-timing.json` load plus an anchored `^SPAWN_WAIT_TIMEOUT_DEFAULT=(\d+)$` search asserting the script literal equals `default_seconds`), and the script side is a column-0 `SPAWN_WAIT_TIMEOUT_DEFAULT=60`. Following the original wording literally ships a DUPLICATE. Confirm it exists, resolves and passes; report the line numbers you actually read.

2. **Step 4 runs the FULL unit suite, NOT "both unit files".** The old phrasing is stale and contradicts this module's own Acceptance Criteria. Re-measure; the pre-task baseline is 777 but **verify it yourself rather than inheriting it.**

3. **Step 4(b): record the trust-preflight DECISION and flip `deviations.md:18`.** A decision to record, not necessarily a preflight to build. Declining on the unmeasured assumption that `$WORKTREE_ROOT` is already trusted because the parent runs there is **explicitly forbidden** — Task 0 measured the opposite case live. If you decline, state what would have to be true and what would falsify it.

4. **Step 4(c): record a DECISION on the five inline log-readers** (count verified at 5 in `test_spawn_handoff.py`). They are a DIFFERENT SHAPE, not a fourth copy — they read unconditionally and RAISE on a missing file, whereas the shared helper returns `""`. Swapping them changes failure semantics, so this is a judgment call. Fix or decline with reasoning; do not silently leave it.

5. **Step 3b is new and it is a checkbox, not prose: record anchor PROVENANCE for all four diagnoses.** Label each anchor MEASURED (quote the fixture key) or INVENTED (say what would falsify it). **THREE are MEASURED** — `trust-dialog` (`trust_dialog_screen.candidate_anchors`), `banner` (`rc_confirmation_screen`, two live running-session captures) and the `internal_error` disjunct of `unreadable` (`read_screen_cold`, whose stderr is the anchor's direct source). **Only `picker-error` is genuinely un-captured.** *(An earlier draft of this line said "exactly one is measurable today" — that was the very claim partner round 2 blocked on, and it survived here for a round because the fix was applied to the plan and not to this document. One-sided edits are a defect class in their own right: when you correct a claim, find its twin.)* **Measured and inferred are not the same evidence, and a comment that blurs them is worse than no comment.**

   **One nuance you must carry into the label, not gloss:** `shift+tab to cycle` is genuinely MEASURED, but both captures carry the SAME session id and the same `bypass permissions` statusline — so n = **one session captured twice**, and it was a long-running interactive session, not a freshly-spawned successor. The anchor is measured; the generalization to "any running Claude session" is **INFERRED**, and the fixture cannot settle it. Label it that way.

6. **Step 4(e): resolve the ROUTING of `deviations.md:165`** (orphaned fallback workspace). Its disposition names Task 10/13 but no step in either produces it — the identical shape as row 18. Resolve the routing, not necessarily the fix.

7. **Two vacuity traps already identified in Step 2's own fence — do not walk into them.** (a) `test_timeout_rewaits_once_same_duration`: do NOT reach for `_flag(_argv(tmp_path, "wait-for"), "--timeout")` — those helpers resolve only the FIRST matching invocation, so a "both" claim would silently assert one value once and the re-wait half would be vacuous. Parse BOTH wait-for lines out of `cmux.log`. (b) `test_diagnosis_unreadable_on_cold_surface`: `unreadable` has TWO disjuncts (non-zero rc, and a literal `internal_error`); if no stub knob separates them, SAY SO rather than implying both are covered. **An untestable disjunct needs a KNOB, not another assertion.**

## Method discipline — each of these is a scar from this sprint

**TDD.** Step 2's tests come before Step 3's implementation. Steps 1–2 are expected RED until Step 3 lands.

**Positive-control every probe.** A command that failed to look produces the same silence as one that looked and found nothing. Before concluding something is absent, run something that MUST match and confirm it does. A "no X" test arm that still has X makes both arms identical and prints a plausible wrong answer either way.

**A probe that fails in argument parsing rather than in the code teaches NOTHING** about the question. Read raw output, not the verdict line.

**Attribute every RED to a single assertion** before claiming that assertion pins anything. A whole-test RED says nothing about which assertion is load-bearing.

**Mutation hygiene, if you mutate to check a pin:** restore by FILE COPY and `diff -q` — NEVER `git checkout --`, NEVER `git stash` (the stash stack is shared across worktrees and will sweep in-flight SDD artifacts). PRINT the diff and READ it rather than the pass/fail line. Assert your anchor matches EXACTLY ONCE before mutating; a no-op mutation reads as SURVIVED and manufactures a false finding. **Beware repeated anchors** — the previous round found `[ $rc -eq 0 ] || return 1` occurs THREE times in this script and only one is in the function it wanted.

**Grep:** use `/usr/bin/grep` or `find -print0 | xargs -0` for every recursive sweep. The shell's `grep` is a function wrapping `ugrep -G --ignore-files --hidden`, which honors `.gitignore` and therefore SILENTLY SKIPS `.worktrees/` — where this work lives. BRE treats `$` as literal (use `-E`/`-F`). An identifier grep gives a false closure when a consumer depends on a VALUE rather than naming it — sweep the RENDERED form.

**Do not trust the editor's diagnostics panel over the artifact.** On this task it has already accused a correct fix of being half-applied, with exact line numbers, because it was snapshotted mid-edit. Resolve any disagreement against the artifact, with a positive control. There is also standing pre-existing Pyright noise in `test_spawn_handoff_v2.py` (bytes-vs-str inference around `dict(p.split(...))`) — **pre-existing, not yours, do not "fix" it.**

**Bash floor is 3.2, NOT 4.x.** Do NOT add `set -u`, `set -e`, or `pipefail`. Never pipe a producer into `grep -q` — under pipefail SIGPIPE makes it read as NO-match, i.e. fail-OPEN. Use here-strings, as the plan's fences already do.

**Suite timing:** the full unit suite takes ~200-240s — never time it out under 300s; a truncated run reads as a failure. The three spawn files alone are much faster for iteration (baseline 143).

**Git:** never `git add -A` — stage explicit paths enumerated against what you ACTUALLY changed. NEVER `git stash` in this tree. The worktree `.venv` is a SYMLINK to the main checkout's venv — never delete or recreate it; ~60 tests spawn `.venv/bin/python3` by relative path. For commit messages containing backticks or `$`, use a QUOTED heredoc (`git commit -F -`), NOT `-m` — zsh command-substituted a message in an earlier session and silently ate two clauses.

## Deliverable

1. Implement Steps 1–4. Commit with explicit staged paths.
2. Report the FULL-SUITE count you MEASURED, before and after.
3. Answer obligations 1–4 above explicitly, each with the evidence you actually gathered.
4. Write your report to `docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/task-010-implementer-report.md`.

Report format — YAML frontmatter, then ATX `## Section` headings (NOT `**Section:**`). Frontmatter is strictly typed; extra keys are rejected:
- `task_type: implementation`
- `status`: DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED
- `files_changed`: a LIST of `{path, description}` objects — not bare path strings
- `tests`: `{written, passing, command, result}` — `written` is an INT
- `contract_compliance`: a LIST of `{constraint, status, detail}`, status from the ENUM `compliant|non_compliant|partial|not_applicable` ("PASS" is NOT valid)

Required prose sections: Summary, Implementation, Testing, Deviations from Plan, Self-Review. Add a Concerns section if status is DONE_WITH_CONCERNS. Run `validate-report.py` against your report and fix what it flags. **Note a known validator defect: it reports `has_deviations:false`/`has_concerns:false` on reports that plainly have both, when sections open with bold text — use ATX headings and do not be misled by that field.**

**Declare EVERY departure from the plan's fences explicitly in "Deviations from Plan."** An undeclared departure FAILed this task's predecessor's first spec review. If a prescribed step turns out to be wrong or impossible, say so with evidence rather than forcing it green — the previous round did exactly that, correctly, and it was the right call.
