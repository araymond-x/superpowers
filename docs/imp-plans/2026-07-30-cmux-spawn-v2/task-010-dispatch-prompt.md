# Task 10 — implementer dispatch prompt

> **STRUCTURAL NOTE (2026-08-02, partner round 4).** An earlier version of this file RESTATED the plan's factual claims — anchor strings, capture counts, provenance labels. That made it a second source of truth, and across three amendment rounds the same defect recurred every time: the plan was corrected and this file was not, so a claim the partner had already blocked on survived here verbatim. **This file therefore no longer duplicates any factual claim from the plan. It POINTS.** If you are tempted to paste a fact from the plan into this file, don't — that is the exact mechanism that cost four review rounds.

You are an implementer subagent executing Task 10 of an SDD plan. You have NO prior session context — everything you need is below or in the files it names.

## Location

Worktree: `/Users/araymond/projects/claude-custom/superpowers/.worktrees/cmux-spawn-v2` (branch `cmux-spawn-v2`). Work ONLY there. Tree is clean.

Read the worktree root `CLAUDE.md` AND any subdirectory `CLAUDE.md` covering files you touch.

## Your task — the plan is the source of truth

`docs/imp-plans/2026-07-30-cmux-spawn-v2/module-3-spawn-script.md`, **"Task 10: wait-for handshake, re-wait, read-screen diagnosis"**.

**Read the entire task**, including: the ROUTING note at its head, Steps 1, 2, 3, 3b and 4 (Step 4 has five lettered parts, (a)–(e), and each is an obligation), every `AMENDED 2026-08-02` note, and the **Module 3 Acceptance Criteria** at the end of the file. Also read the module header: Contract Constraints, File Map, and the Write-Scope Partitioning table.

Task 10 replaces Task 9's placeholder timeout tail with: a bounded `wait-for` token handshake, exactly one re-wait at the same duration, and `read-screen` diagnosis enrichment that classifies WHY a handshake timed out.

**The single most important semantic: a received token is the ONLY success signal.** `diagnose_target` NEVER selects the exit code — it is enrichment only. A stubbed banner on screen with no token is NOT success; that mistake caused three live incidents.

**Contract Constraints:** read them verbatim from the module header — deliberately not restated here. They are derived from source and frozen into Task 0 fixtures. **If your implementation contradicts them, STOP and report BLOCKED. Do not work around a constraint — surface the conflict.**

**Source Contracts:** None. External contracts were frozen into fixtures by Module 1's Task 0. The binding fixtures are `tests/unit/fixtures/spawn-handoff/cmux-verb-shapes.json` and `cold-start-timing.json` — both **READ-ONLY source of truth**. **If anything you write disagrees with `cmux-verb-shapes.json`, you are wrong, not the fixture.**

## Write scope

The Write-Scope Partitioning table's Task 10 row says "same set" — resolve it there and enumerate the paths yourself rather than trusting any list, including this one. It comes to **six** writable paths (the five in the File Map plus `test_spawn_handoff_hardening.py`), and `tests/unit/fixtures/spawn-handoff/` includes the new `screens/` subdir Step 1 creates.

READ-ONLY, never edit: `skills/subagent-driven-development/scripts/_handoff_support.py`, `tests/unit/test_handoff_support.py`, every plan/module file, `BACKLOG.md` (owned by a concurrent session), and the two Task 0 fixture JSONs.

`tests/integration/sdd-e2e-test.sh` is RED right now by design and stays red until Task 17, which owns that rewrite. **Do not touch it, do not run it, do not report it as a Task 10 failure.**

## Why this task took four partner rounds — read this before Step 1

You are inheriting a task whose *evidence* was wrong four times over. The specifics are all in the plan's `AMENDED` notes; what follows is the shape, because it bears on your work.

1. The original fence told the implementer to grep for a screen anchor **that appears nowhere in the frozen capture.** It would have shipped GREEN, because Step 1 also told the implementer to author a fixture containing that invented phrase. **A fixture authored to match the code under test proves only that you can spell the same string twice.**
2. The fix for that **contained its own false claim** — that no live capture existed for the other branches — when two live running-session captures were sitting in the fixture. **When you correct an evidence defect, your correction is itself an evidence claim and must be measured to the same standard. "No capture exists" is a NEGATIVE claim, and negative claims are what a broken instrument manufactures.**
3. Fixing the anchor then **dissolved the hazard a companion test existed to guard** — the prescribed positive control could no longer fire. **A correct fix can retire another test's subject, leaving a test that still reads as a guard while pinning nothing.**
4. And the corrections kept landing in one document but not its twin.

**Concretely for you:** derive fixtures from captures, never author them to match your code; label anchor provenance per-anchor and honestly (Step 3b); and when you fix something, look for the twin of every claim you touched.

## Obligations that are easy to miss — pointers, not restatements

Each is written into the plan. They are listed here only so you go and read them, because several contradict what a careless reading would conclude. **Read the plan's own words for each; do not act on the one-line gloss.**

1. **Step 2's wait-timeout import assertion — VERIFY it, do NOT re-add it.** Task 9 pre-empted it and it is already landed. Following the original wording literally ships a duplicate. Report the line numbers you actually read.
2. **Step 4(a) runs the FULL unit suite**, not "both unit files" — the old phrasing contradicted this module's own Acceptance Criteria. Re-measure the baseline; **do not inherit a count.**
3. **Step 4(b): record the trust-preflight DECISION** and flip the corresponding register row off `Pending`. A decision to record, not necessarily a preflight to build — and the plan explicitly forbids one particular way of declining.
4. **Step 4(c): record a DECISION on the five inline log-readers.** They are a different *shape*, not a duplicate — swapping them changes failure semantics. Judgment call; fix or decline with reasoning.
5. **Step 3b is a checkbox, not prose: record anchor PROVENANCE.** Read Step 3b for the category rubric and which anchors fall where — it is precise, and its absence caused failure #1 above.
6. **Step 4(d): resolve the ROUTING of the orphaned register row** naming Tasks 10/13 with no producing step in either.
7. **Two vacuity traps are called out inside Step 2's own fence** — one about which helper resolves which invocation, one about a two-disjunct condition. Read the fence comments; they say what not to reach for and what to write instead.

## Method discipline — each of these is a scar from this sprint

**TDD.** Step 2's tests come before Step 3's implementation. Steps 1–2 are expected RED until Step 3 lands.

**Positive-control every probe.** A command that failed to look produces the same silence as one that looked and found nothing. Before concluding something is absent, run something that MUST match and confirm it does. A "no X" arm that still contains X makes both arms identical and prints a plausible wrong answer either way.

**A probe that fails in argument parsing rather than in the code teaches NOTHING** about the question. Read raw output, not the verdict line.

**Attribute every RED to a single assertion** before claiming that assertion pins anything.

**Mutation hygiene, if you mutate to check a pin:** restore by FILE COPY and `diff -q` — NEVER `git checkout --`, NEVER `git stash` (the stash stack is shared across worktrees and will sweep in-flight SDD artifacts). PRINT the diff and READ it rather than the pass/fail line. Assert your anchor matches EXACTLY ONCE before mutating; a no-op mutation reads as SURVIVED and manufactures a false finding. **Beware repeated anchors** — `[ $rc -eq 0 ] || return 1` occurs THREE times in this script and only one sits in the function you probably mean.

**Grep:** use `/usr/bin/grep` or `find -print0 | xargs -0` for every recursive sweep. The shell's `grep` is a function wrapping `ugrep -G --ignore-files --hidden`, which honors `.gitignore` and therefore SILENTLY SKIPS `.worktrees/` — where this work lives. BRE treats `$` as literal (use `-E`/`-F`). An identifier grep gives a false closure when a consumer depends on a VALUE rather than naming it — sweep the RENDERED form.

**Do not trust the editor's diagnostics panel over the artifact.** On this feature it has already accused a correct fix of being half-applied, with exact line numbers, because it was snapshotted mid-edit. There is also standing pre-existing Pyright noise in `test_spawn_handoff_v2.py` (bytes-vs-str inference around `dict(p.split(...))`) — **pre-existing, not yours, do not "fix" it.**

**Bash floor is 3.2, NOT 4.x.** Do NOT add `set -u`, `set -e`, or `pipefail`. Never pipe a producer into `grep -q` — under pipefail SIGPIPE makes it read as NO-match, i.e. fail-OPEN. Use here-strings, as the plan's fences do.

**Suite timing:** the full unit suite takes ~200-240s — never time it out under 300s; a truncated run reads as a failure. The three spawn files alone are much faster for iteration.

**Git:** never `git add -A` — stage explicit paths enumerated against what you ACTUALLY changed. NEVER `git stash` in this tree. The worktree `.venv` is a SYMLINK to the main checkout's venv — never delete or recreate it; ~60 tests spawn `.venv/bin/python3` by relative path. For commit messages containing backticks or `$`, use a QUOTED heredoc (`git commit -F -`), NOT `-m`.

## Deliverable

1. Implement Steps 1, 2, 3, 3b and 4(a)–(e). Commit with explicit staged paths.
2. Report the FULL-SUITE count you MEASURED, before and after.
3. Answer each of the seven obligations above explicitly, with the evidence you actually gathered.
4. Write your report to `docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/task-010-implementer-report.md`.

Report format — YAML frontmatter, then ATX `## Section` headings (NOT `**Section:**`). Frontmatter is strictly typed; extra keys are rejected:
- `task_type: implementation`
- `status`: DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED
- `files_changed`: a LIST of `{path, description}` objects — not bare path strings
- `tests`: `{written, passing, command, result}` — `written` is an INT
- `contract_compliance`: a LIST of `{constraint, status, detail}`, status from the ENUM `compliant|non_compliant|partial|not_applicable` ("PASS" is NOT valid)

Required prose sections: Summary, Implementation, Testing, Deviations from Plan, Self-Review. Add a Concerns section if status is DONE_WITH_CONCERNS. Run `validate-report.py` against your report and fix what it flags. **Known validator defect: it reports `has_deviations:false`/`has_concerns:false` on reports that plainly have both when sections open with bold text — use ATX headings and do not be misled by that field.** If its section names disagree with the list above, follow the validator and declare the departure.

**Declare EVERY departure from the plan's fences explicitly in "Deviations from Plan."** An undeclared departure FAILed this task's predecessor's first spec review. If a prescribed step turns out to be wrong or impossible, say so with evidence rather than forcing it green — that has been the right call twice on this task already, including once when a reviewer's own prescription could not be satisfied.
