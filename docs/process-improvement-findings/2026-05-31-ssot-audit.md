# SSOT Audit: SKILL.md Manual Prescriptions vs Hook Enforcement

**Date:** 2026-05-31
**Author:** pipeline-flexibility Task 9 (read-only investigation)
**Scope:** 15 SKILL.md files vs 4 active hooks
**Excluded:** `sdd-skill-enforcement-hook.sh`, `sdd-stop-hook.sh` (present on disk but NOT registered in `~/.claude/settings.json`, so auditing them would misrepresent live enforcement)

## Methodology

**Files read in full (15 SKILL.md):** brainstorming, dispatching-parallel-agents, executing-plans, finishing-a-development-branch, handoff-acceptance, receiving-code-review, requesting-code-review, subagent-driven-development, systematic-debugging, test-driven-development, using-git-worktrees, using-superpowers, verification-before-completion, writing-plans, writing-skills.

**Active hooks read in full (4):**
1. `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` (PreToolUse → Agent) — Checks 1, 1b, 2, 3, 3b, 4, 4b, 4c, 5, 5b, 5c, 5d, 6, 6b, 7.
2. `skills/subagent-driven-development/scripts/sdd-report-guard.sh` (PreToolUse → Bash) — report-file / dispatch-log forgery warnings.
3. `skills/writing-plans/scripts/plan-validation-gate-hook.sh` (PreToolUse → Skill) — plan-quality gate (validate-plan.py + Pydantic + review report).
4. `hooks/session-start` (SessionStart) — skill bootstrap + symlink integrity.

**Cross-referenced scripts** (read for threshold/argument verification, not themselves hooks): `controller-checkpoint.py`, `validate-plan.py`, `transition-module.py`.

**What counts as a "manual prescription":** a SKILL.md instruction directing the controller/agent to *manually* perform a deterministic action — run a named script, create a named file, or verify a named precondition — where that action is also (or could be) mechanically checked by a hook. Pure judgment guidance (declare a review tier and state rationale, ask clarifying questions, classify a fix as point-vs-structural) is NOT a manual prescription in this sense; it has no mechanical equivalent and is correctly skill-only.

**How overlap was determined:** for each manual prescription in SDD/writing-plans, I located the corresponding hook check by name and line, then compared the prescribed action (and any threshold/argument) against what the hook actually enforces. Drift = the SKILL and the hook describe the same gate but disagree on an argument, threshold, or precondition.

**Honest scope note:** the richest overlap is concentrated almost entirely in `subagent-driven-development/SKILL.md` and `writing-plans/SKILL.md` — the only two skills with a backing PreToolUse hook. The other 13 skills are advisory-only (no hook), so by definition they have zero "hook overlap"; their guidance is the single source of truth for their domain and nothing there is redundant ceremony. The findings table below is therefore deliberately short — this is a real result, not a thin audit.

## Findings

| # | SKILL.md | Location | Prescription | Hook | Check | Drift | Classification |
|---|----------|----------|--------------|------|-------|-------|----------------|
| 1 | subagent-driven-development | §258–265 ("Context Budget Management") | Hook runs `estimate-task-tokens.py` automatically; "there is no manual step for you to run." | sdd-pre-dispatch-hook.sh | Check 6 (L634–669) | None — the SKILL was already reconciled (C6(a), 2026-05-30) to *defer* to the hook. Residual: hook passes `--plan-file --task`; the script also accepts `--constraints-file` (unused) and neither counts injected source/CLAUDE.md context. | **keep** (already-retired manual step; the *measurement-strengthening* half is tracked as C6(b), not an SSOT redundancy) |
| 2 | subagent-driven-development | §282–286 ("Controller Health Checkpoints" — pre-dispatch) | "Run `controller-checkpoint.py --phase pre-dispatch` … save its output." | sdd-pre-dispatch-hook.sh | Check 5c (L578–596) | None on the gate itself (hook requires `reports/checkpoint-pre-dispatch-NNN.json`). The SKILL prose still reads as a self-discipline instruction rather than "the hook requires this file" — softer framing than C6(a) applied to token estimation. | **keep** (complementary: SKILL tells you to *produce* the artifact, hook *enforces* its presence) — but a §258-style "the hook enforces this" rewrite would remove residual skip-guilt (see Quick Win SSOT-2). |
| 3 | subagent-driven-development | §288–292 ("Controller Health Checkpoints" — pre-completion) + §461–481 (Pre-Completion Gate) | "Run `controller-checkpoint.py --phase pre-completion`"; manually verify checkboxes/reports/deviations; run `extract-execution-trace.py` + trace auditor (step 8). | *(no active hook)* | — | The pre-completion checkpoint, honesty check, and trace audit are **gated by `sdd-stop-hook.sh`** (Stop event) and the controller's own discipline — and `sdd-stop-hook.sh` is **excluded** (unregistered). So at the *live* PreToolUse layer there is **no enforcement** of pre-completion. | **keep** (no overlapping active hook to be redundant with) — but see Concern A: the pre-completion gate is effectively advisory-only in the registered hook set. |
| 4 | subagent-driven-development | §286 + Check-6b reference; "Context Health Protocol" | "If WARNING about context load, run the context summary script." Hook Check 6b enforces `context-summary.md` past `context_summary_at`. | sdd-pre-dispatch-hook.sh | Check 6b (L671–687) | None on the gate. The threshold is now manifest-driven (`enforcement.context_summary_at`), not a fixed "midpoint" as the prose still implies; minor staleness, not drift. | **keep** (SKILL = when/why to compress; hook = hard floor). Candidate for the same "hook enforces this" framing pass. |
| 5 | subagent-driven-development | §426–428 (File-Based Report Persistence) | "Validate report completeness using `validate-report.py` … If INCOMPLETE, do not proceed to review." | sdd-pre-dispatch-hook.sh | Check 4b (L437–456) | None — the hook runs `validate-report.py` on the **previous** task's implementer report before allowing the **next** dispatch (Item 2: embeds `head -n 12` of validator output). The manual run is a *faster local* check; the hook is the backstop. | **keep** (defense-in-depth: manual run catches it one task earlier; hook guarantees it) |
| 6 | subagent-driven-development | §444–455 (Module Transition) | "Run `transition-module.py` … Do not manually archive reports or update the manifest — the script handles all five steps." | *(no hook)* + interacts w/ sdd-pre-dispatch-hook.sh Check 4c | — | **Active defect, not redundancy:** the prescribed script's Step 5 (`open(dispatch_log,"w").close()`, transition-module.py L168) truncates the live dispatch log, which makes the *next* module's first-task **Check 4c** (L495–536, dispatch provenance for task N-1) BLOCK — the genuinely-dispatched prior reviews vanish from the live log. This execution had to bypass `transition-module.py` with a manual manifest advance (deviations.md, Module 1→2 & 2→3). | **strengthen** (the SKILL correctly says "use the script," but the script is incompatible with the current 3-stage hook's module-boundary Check 4c — fix the script/hook, not the SKILL) |
| 7 | writing-plans | §55, §472–476 (Plan Review Loop) | "Run `validate-plan.py` on every plan/module file — fix all FAIL and WARNING." | plan-validation-gate-hook.sh | Gate 1 (L156–184) + Gate 1b Pydantic (L186–206) | None — the hook re-runs `validate-plan.py` (FAIL → block) and Pydantic on every scoped plan file at SDD/executing-plans invocation. The manual run during authoring is the natural place to fix WARNINGs the hook only treats advisorily. | **keep** (authoring-time fix-it loop vs. execution-time gate — both needed; the hook does NOT block on WARNING, only FAIL) |
| 8 | writing-plans | §57–58, §70–73 (Plan Completion Gate) | "Save plan review report to `plan-review-report.md`"; "Write `plan-manifest.txt`." | plan-validation-gate-hook.sh | Gate 2 (L208–271) + `.active-feature`/scope (L59–69) | None — hook blocks if `plan-review-report.md` is missing/<50 bytes or `.active-feature` absent. The manifest is read for *scoping*; its absence degrades to git-diff scoping (not a block). | **keep** (hook enforces the report; SKILL prescribes producing both report + manifest) |

### Drift-of-threshold check (no row above needed, but verified)

These were checked specifically because the project CLAUDE.md warned that *older docs* cite stale numbers (e.g., "20%"). The current SKILL body and the current code **agree**:

- **Verification-task ratio cap:** SKILL.md §363 ("verification tasks capped at ≤30% of total tasks") == `controller-checkpoint.py` Check 8 `verif_count / total_tasks > 0.3` (L1267). **Match.**
- **Minimum-tier review-ratio cap:** SKILL.md §336 / Pre-Completion docs == `controller-checkpoint.py` Check 7 `minimum / total > 0.5` (L1234). **Match.** (The "20%" appears only in *historical* prose called out as superseded in CLAUDE.md — not in the live SKILL body.)
- **Token budget thresholds:** SKILL.md §261–263 (WARNING ≥25%, TOO_LARGE ≥50%) == hook Check 6 verdict handling (L657–661). **Match.**

So the C6 "drifted args" finding (skill passed `--task-file --constraints-file`, hook passed `--plan-file --task`) was **already fixed** when C6(a) rewrote §258–265 to defer to the hook. No live threshold drift remains.

## Summary

- **Manual prescriptions found (in the two hook-backed skills):** 8 distinct prescriptions overlapping or adjacent to a hook check.
- **Retire:** 0. (The one true "retire" case — manual token estimation — was already retired by C6(a) on 2026-05-30. Nothing else is pure redundant ceremony: every other manual step either produces an artifact the hook only *checks*, or runs at a different lifecycle phase.)
- **Strengthen:** 1 (Finding 6 — `transition-module.py` log truncation vs. Check 4c; this is the highest-signal item and was hit first-hand this execution).
- **Keep:** 7 (genuinely complementary: authoring-time vs. execution-time, or produce-vs-enforce).
- **Threshold drift:** 0 live (all three ratios verified to match between SKILL body and code).

**Headline:** the SSOT picture is *healthier than the C6 finding implied*. C6 found one genuine redundant-manual-step (token estimation), which has since been retired. This audit found no second instance of that exact anti-pattern. What it did surface is a different class of problem — **the manifest/multi-module hook path (Check 4c) is incompatible with the prescribed `transition-module.py` script**, and the **pre-completion gate has no live (registered) hook** because it rides on the excluded `sdd-stop-hook.sh`. Those are *strengthen* items, not *retire* items.

A secondary, cheap improvement: SDD SKILL.md §282–286, §286/Check-6b, and §426–428 still phrase hook-enforced gates as self-discipline ("run X and save its output") rather than "the hook enforces X automatically" the way §258–265 now does. Re-framing them (no behavior change) removes residual skip-guilt and clarifies that these are *backstopped*, mirroring the successful C6(a) edit.

## Recommended Sprint 3 Quick Wins

Top items by leverage. Each maps to a BACKLOG row (added by this task).

1. **N3 — Fix `transition-module.py` ↔ Check 4c module-boundary incompatibility (strengthen).** Either (a) have `transition-module.py` preserve the prior task's review provenance across the boundary (don't truncate the live log; or seed the new log with a synthetic "module N reviews archived" provenance line that Check 4c accepts), or (b) make Check 4c module-boundary-aware (look in `archive-<module>/.dispatch-log` for task N-1 when N is the module's first task). This execution had to abandon the prescribed script (deviations.md Module 1→2, 2→3) — the single highest-signal finding.

2. **N4 — Make the pre-completion gate archive-aware (strengthen).** `controller-checkpoint.py` `find_all_report_files` / `find_report_file` (L186–189, L121–127) glob only `reports_dir`, not `archive-<module>/`. After a `transition-module.py` archive, completed-module reports read as "missing" at the final gate. Recurse into `archive-*` subdirs (or read `module_reports_archived` from the manifest and trust prior gates). Pairs with N3 — together they make multi-module SDD actually runnable through the prescribed scripts.

3. **N5 — Make the fence-blind task-header regex fence-aware (strengthen).** `^###\s+Task\s+(\d+)` exists as TWO identically-valued regexes that must BOTH be fixed: `TASK_HEADER_RE` (validate-plan.py:48) and `TASK_HEADER_PATTERN` (controller-checkpoint.py:58). It matches `### Task 91/93/94/95` *inside fenced code fixtures* in a plan, inflating the verification-ratio denominator (Check 8), the pre-completion checkbox count, AND `all_tasks_have_reports` (it demanded reports for fixture task ids — a confirmed false-positive that blocked THIS feature's own pre-completion checkpoint; the real tasks 0-9 all had reports). Fix BOTH sites: skip headers inside ``` fenced blocks (sibling of the N9 dedup). Low risk, removes a silent miscount.

4. **N6 — "Hook enforces this" framing pass on SDD SKILL.md (retire-flavored, doc-only).** Apply the C6(a) treatment to §282–286 (pre-dispatch checkpoint), §286/Check-6b (context summary), and §426–428 (report validation): state that the hook enforces the gate automatically, so the manual run is an optional early check, not a required ceremony. No behavior change; removes skip-guilt and the false impression these are controller-only honor-system steps. (Smallest effort; pairs naturally with any future SDD SKILL edit since the file is at its word-count ceiling.)

5. **N7 — Pre-execution `source_contracts: FAIL` false positive (strengthen).** `controller-checkpoint.py --phase pre-execution` reports FAIL on a legitimately-empty prose `Source Contracts: None` (it treats "None" as a present-but-malformed section). Read the frontmatter `source_contracts` field (or treat prose "None" as valid-absent) instead. Documented as an accepted deviation every run (deviations.md Ingestion row; CLAUDE.md Hook Development Gotchas) — recurring friction with a known fix.

### Lower-priority / opportunistic (also added to BACKLOG)

6. **N8 — F6 regression check is literal-substring brittle.** `validate-all-skills.py:569` greps for the literal `"invoked directly"` / `"skipping brainstorming"` to assert standalone-invocation guidance exists. A semantically-equivalent rewording silently FAILs the check (this execution hit it — deviations.md Task 6). Key on intent (e.g., presence of a "Direct entry" section) rather than an exact phrase.

7. **N9 — Extract `_task_ids_where(plan_contents, field, value)` single-source-of-truth helper.** `controller-checkpoint.py` `_declared_minimum_task_ids` (L228) and `_verification_task_ids` (L263) are near-verbatim frontmatter parsers. Collapse into one `_task_ids_where(...) -> (set, parsed_any)` helper. ~20 lines, behavior-preserving (both ratio paths are tested). Flagged by Task 4 quality review; mirrors the architectural-principles "single source of truth for logic" rule.
