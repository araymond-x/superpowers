---
schema_version: 1
feature_archetype: extension
enforcement_tier: standard
entry_mode: brainstorming
source_contracts: null
integration_test:
  path: tests/integration/sdd-e2e-test.sh
shared_constants: []
pattern_references:
  - name: "checkpoint-tests"
    source_files: ["tests/unit/test_pre_completion_gates.py"]
    reason: "Pre-completion Check 7 (ratio) and Check 9 (git-reality) test patterns: reports_dir setup, run_pre_completion helper, _check_verification_git_reality direct calls"
  - name: "c2-tests"
    source_files: ["tests/unit/test_c2_integration_gate.py"]
    reason: "Check 10 (integration_test) + validate-plan risk-surface WARNING test patterns; _load_script importlib loader"
  - name: "fence-tests"
    source_files: ["tests/unit/test_fence_aware_parsing.py"]
    reason: "_unfenced_content characterization + validate-plan fence-aware test patterns; _load_script importlib loader"
  - name: "transition-tests"
    source_files: ["tests/unit/test_transition_module.py"]
    reason: "transition-module.py validate_module_completion / manifest-workspace test patterns"
  - name: "hook-tests"
    source_files: ["tests/unit/test_sdd_classification.py"]
    reason: "Bash hook subprocess testing (make_hook_input, manifest-mode workspace, dispatch-log assertions)"
  - name: "archive-precedent"
    source_files: ["skills/subagent-driven-development/scripts/controller-checkpoint.py"]
    reason: "find_report_file/find_all_report_files (lines 125-197) already glob archive-*/ with live-wins via sorted()[-1] — N27 extends this exact precedent"
  - name: "e2e-step-pattern"
    source_files: ["tests/integration/sdd-e2e-test.sh"]
    reason: "Step 5 transition + Step 11 Check-10 assertion patterns to mirror for the new archive-aware Step 12"
modules:
  - id: 1
    title: "aggregate-visibility"
    task_ids: [1, 2, 3, 4]
    file: module-1-aggregate-visibility.md
  - id: 2
    title: "calibration"
    task_ids: [5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
    file: module-2-calibration.md
tasks:
  - id: 1
    title: "N27: Check 7 archive-aware review-tier inputs"
    module_id: 1
    pattern_references: ["checkpoint-tests", "archive-precedent"]
  - id: 2
    title: "N27: Check 9 archive-aware dispatch-log merge"
    depends_on: [1]
    module_id: 1
    pattern_references: ["checkpoint-tests", "archive-precedent"]
  - id: 3
    title: "N26: dispatch-log classification + Check 3b allowlist + baseline recapture"
    depends_on: [2]
    module_id: 1
    pattern_references: ["hook-tests"]
  - id: 4
    title: "N19: transition module.file AND-exists fallback + cleanup"
    depends_on: [3]
    module_id: 1
    pattern_references: ["transition-tests"]
  - id: 5
    title: "N20: fence-helper tilde + unclosed-fence WARNING + _load_script hoist"
    depends_on: [4]
    module_id: 2
    pattern_references: ["fence-tests"]
  - id: 6
    title: "N22: risk-surface stem patterns + unfenced scan"
    depends_on: [5]
    module_id: 2
    pattern_references: ["c2-tests"]
  - id: 7
    title: "N25c: _git_run subprocess consolidation (SSOT)"
    depends_on: [6]
    module_id: 2
    pattern_references: ["c2-tests", "checkpoint-tests"]
  - id: 8
    title: "N25a: Check 10 feature-window fallback"
    depends_on: [7]
    module_id: 2
    pattern_references: ["c2-tests", "checkpoint-tests"]
  - id: 9
    title: "N25b+d+f: frontmatter line-anchored scan + directory/malformed diagnostics"
    depends_on: [8]
    module_id: 2
    pattern_references: ["c2-tests"]
  - id: 10
    title: "N6: SDD SKILL.md hook-enforces-this framing pass"
    depends_on: [9]
    module_id: 2
    review_tier: minimum
  - id: 11
    title: "N8: intent-based F6 regression check"
    depends_on: [10]
    module_id: 2
  - id: 12
    title: "Archive-awareness inventory docs (5 sites)"
    depends_on: [11]
    module_id: 2
    review_tier: minimum
  - id: 13
    title: "Verification: archive-awareness inventory audit"
    depends_on: [12]
    module_id: 2
    task_type: verification
    review_tier: minimum
  - id: 14
    title: "e2e Step 12 (archive-aware proof) + BACKLOG flips + final suites"
    depends_on: [13]
    module_id: 2
    pattern_references: ["e2e-step-pattern"]
---

# SDD Aggregate-Gate Visibility — Implementation Plan (Parent)

> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first — direct implementation bypasses review enforcement, quality gates, and hooks.

**Goal:** Make the SDD pre-completion AGGREGATE gates (Check 7 min-tier ratio, Check 9 git-reality) archive-aware so they police ALL modules after a `transition-module.py` run, close the dispatch-log classification gaps that hide fix cycles from provenance, align the transition↔hook `module.file` fallback, and ship the deferred Check-10/risk-surface/fence calibration batch — executed as a 2-module SDD feature that itself live-exercises a transition and a non-last verification task.

**Architecture:** Three coordinated changes in Module 1 widen the *inputs* of two existing pre-completion checks (no new state, no schema bump) by globbing `reports/archive-*/` and merging archived dispatch logs — extending the `find_report_file`/`find_all_report_files` archive-aware precedent (controller-checkpoint.py:125-197) to two more lookups. Module 2 is calibration + hygiene: fence-helper edge cases, risk-surface stemming, a Check-10 follow-up batch (on-main false-block fix, frontmatter scan, git-subprocess SSOT, diagnostics), two doc-only passes, and an intent-based regression check. The feature is self-hosting: it edits the very scripts that gate it, so it runs in a worktree and pre-logs the resulting self-blindness as accepted deviations.

**Tech Stack:** Python 3.9-compatible stdlib (the gate scripts run with bare `python3`; only Pydantic models import pydantic), Bash (the pre-dispatch hook), pytest (unit), Bash e2e harness.

**Source Contracts:** None

No external schema/API/handoff is consumed. Per N7 (on main) a bare `None` value is valid-absent at pre-execution, so there is no Task 0; the no-Task-0 first task is covered by N3a (hook) + N18 (checkpoint), both on main.

**Contract Constraints:** None (no external contracts). The one cross-task internal contract — the dispatch-log line grammar shared by N26 (writer) and N27 (Check 9 reader) — is documented in **Shared Internal Contract** below and re-stated in each consuming task.

**Shared Constants:** None (no importable Python constant is shared across tasks). The dispatch-log line grammar is a string/regex convention, not a Python constant — see **Shared Internal Contract**.

**Pattern References:**
- `skills/subagent-driven-development/scripts/controller-checkpoint.py:125-197` — `find_report_file`/`find_all_report_files` already glob `archive-*/` with live-wins via `sorted()[-1]`; N27 (Tasks 1-2) extends this exact pattern.
- `tests/unit/test_pre_completion_gates.py` — Check 7/9 test harness (`run_pre_completion` helper, reports_dir setup, direct `_check_verification_git_reality` calls).
- `tests/unit/test_c2_integration_gate.py` — Check 10 + validate-plan WARNING tests; the duplicated `_load_script` importlib loader (hoisted by Task 5, D15).
- `tests/unit/test_fence_aware_parsing.py` — `_unfenced_content` characterization tests; second `_load_script` copy.
- `tests/unit/test_transition_module.py` — transition manifest-workspace + `validate_module_completion` tests.
- `tests/unit/test_sdd_classification.py` — Bash hook subprocess test patterns (`make_hook_input`, manifest workspace).
- `tests/integration/sdd-e2e-test.sh:130-162` (Step 5 transition) and `:390-444` (Step 11 Check-10 assertion) — patterns to mirror for the new archive-aware Step 12.

**Feature Archetype:** Extension (no obsolescence — purely widens existing check inputs and adds calibration; targeted refactor elements in N19 dead-code removal and N25c git-subprocess consolidation, with all callers audited).

**Code Footprint:**

| Category | Files / Functions | Action | Dependencies to Verify |
|----------|------------------|--------|----------------------|
| Modified | `controller-checkpoint.py` :: `_review_tiers_per_task` (Check 7), `_check_verification_git_reality` (Check 9), Check 10 block, `_resolve_base_ref`/`_in_changeset`/inline git calls (N25c) | Extend | Callers: `_ratio_check` (:1468), Check 9 caller (:1553), Check 10 (:1602) — all internal to `run_pre_completion` |
| Modified | `sdd-pre-dispatch-hook.sh` :: classification pipeline (new Stage 0), Stage 2 log write, Stage 3 passthrough, Check 3b allowlist, additionalContext | Extend | Hook baseline `tests/ARaymond-hook-baseline/baseline.txt` (re-capture SAME commit) |
| Modified | `transition-module.py` :: `validate_module_completion` (N19) | Refactor (dead-code removal) | None (verif_ids reassigned in both branches today) |
| Modified | `_report_utils.py` :: `_unfenced_content` (+ new `ends_in_open_fence`) | Extend | Consumers: validate-plan.py, controller-checkpoint.py (fence-aware parsing); behavior pinned by characterization tests |
| Modified | `validate-plan.py` :: `_C2_RISK_PATTERNS`, `check_integration_test_risk`, new unclosed-fence WARNING | Extend | Imports `_unfenced_content`/`ends_in_open_fence` from `_report_utils` |
| Modified | `tests/ARaymond-skill-regression/validate-all-skills.py` :: F6 (:569) | Extend | Scope stays `writing-plans/SKILL.md` ONLY |
| Modified | `skills/subagent-driven-development/SKILL.md` (N6 framing; N26 marker doc) | Extend (doc) | Net `wc -w` MUST NOT increase (5000 hard limit; current 4911) |
| Modified | `tests/integration/sdd-e2e-test.sh` (new Step 12) | Extend | Final echo step count 12 → 13 |
| Modified | `tests/unit/sdd_test_helpers.py` (+ `_load_script`, D15), `test_fence_aware_parsing.py`, `test_c2_integration_gate.py`, `test_pre_completion_gates.py`, `test_transition_module.py`, `test_sdd_classification.py` | Extend | `_load_script` becomes single-source in helpers |
| Modified | `CLAUDE.md`, `docs/ARaymond-customization-manifest.md`, `docs/process-improvement-findings/BACKLOG.md` | Extend (doc) | Inventory "3 sites" → "5 sites" at CLAUDE.md:206 AND manifest:329; BACKLOG rows flipped |

## Module Inventory

| Module | File | Goal | Items | Tasks |
|--------|------|------|-------|-------|
| 1 | `module-1-aggregate-visibility.md` | Make Check 7 + Check 9 archive-aware, close dispatch-log fix-cycle blind spots, align transition `module.file` semantics | N27 (Check 7), N27 (Check 9), N26(a)+(b)+baseline, N19 | 1-4 |
| 2 | `module-2-calibration.md` | Calibration & hygiene: fence edges, risk-surface stemming, Check-10 batch, framing/F6 doc passes, the inventory docs, the live verification task, and the in-sprint e2e proof | N20→N22, N25(a-d,f), N6, N8, inventory docs, verification task, e2e Step 12 + BACKLOG | 5-14 |

## Module Dependency Graph

```
Module 1 (aggregate-visibility)   ← Tasks 1-4
  │  (controller-checkpoint.py Check 7/9, hook, transition)
  │  COMPLETES + transitions via transition-module.py
  ▼
Module 2 (calibration)            ← Tasks 5-14
     Task 5 (N20 fence helper) ──► Task 6 (N22 scan uses _unfenced_content)
     Task 7 (N25c _git_run SSOT) ──► Task 8 (N25a feature-window) ──► Task 9 (N25b+d+f)
       [Tasks 7-9 all edit controller-checkpoint.py]
     Task 10 (N6 doc) ; Task 11 (N8) ; Task 12 (inventory docs)
     Task 13 (verification — audits Task 12's docs vs code) [NON-LAST]
     Task 14 (e2e Step 12 + BACKLOG + final suites) [LAST]
```

**No tasks run in parallel.** SDD executes tasks sequentially in ID order, and Module 1 fully completes (and transitions) before Module 2 begins. Several tasks legitimately share an Owned File across the serialized sequence (e.g. `controller-checkpoint.py` is touched by Tasks 1, 2, 7, 8, 9; `validate-plan.py` by Tasks 5, 6). This is safe precisely because there is no parallelism — each shared file is handed off in dependency order, never written concurrently. The Write-Scope table below records per-task ownership; the `depends_on` chain enforces the serialization.

## Shared Internal Contract — dispatch-log line grammar

`reports/.dispatch-log` lines (the contract between N26 the writer and N27/Check-9 the reader):

| Line | Written by | Read by |
|------|-----------|---------|
| `<ISO> DISPATCH implementer task=N type=implementer` | hook Stage 2 (existing) | Check 9 parser (controller-checkpoint.py:324) — **opens/moves a verification window** |
| `<ISO> DISPATCH reviewer task=N type={spec\|quality\|partner\|trace-audit}-review` | hook Stage 1 (existing) + Stage 0 marked re-review (new) | Check 4c / transition provenance (substring grep) |
| `<ISO> DISPATCH fix task=N type=fix` | hook Stage 0 marked fix (NEW, N26a) | provenance audit only — **NEVER matched by Check 9's `type=implementer` regex** |
| `<ISO> DISPATCH adhoc type=fix-unattributed` | hook Stage 3 markerless-fix fallback (NEW, N26a; no `task=`) | tamper-evidence record only |

**The load-bearing invariant (Tasks 2 + 3 must both honor it):** Check 9's parser (`controller-checkpoint.py:324`) matches ONLY `type=implementer`. A marked fix dispatch (`[task N fix]`) MUST emit ONLY the Stage-0 `type=fix` line and MUST skip Stage 2's `type=implementer` write — otherwise it would move task N's verification window. Task 3's fixture asserts the **absence** of a `type=implementer` line for a marked fix, not merely the presence of `type=fix`.

## Resolved Open Decisions (O1–O4)

| # | Decision | Resolution |
|---|----------|-----------|
| **O1** | Stage-0 marker regex | Fix: `\[task[[:space:]]+[0-9]+[[:space:]]+fix\]`; re-review: `\[task[[:space:]]+[0-9]+[[:space:]]+re-review:(spec\|quality\|partner)\]`. Both matched with `grep -iE`; task id via `grep -oE 'task[[:space:]]*[0-9]+' \| grep -oE '[0-9]+' \| head -1`; re-review kind via the alternation capture. (See Task 3.) |
| **O2** | Stage-3 fix-heuristic regex | Baseline `\bfix\b\|remediat`, matched with `grep -iE`. CLAUDE.md confirms `\b` behaves identically under BSD `/usr/bin/grep -iE` and ugrep, so the heuristic is grep-implementation-independent. (See Task 3.) |
| **O3** | F6 structural heading form | Structural signal = a "Direct entry" **bold label or heading**: Python regex `(?im)^#{1,6}.*direct entry\|\*\*\s*direct entry`. The existing `2. **Direct entry** —` in `writing-plans/SKILL.md` already satisfies it, so **no SKILL.md edit is needed** — zero cost against the ~273-word headroom. (See Task 11.) |
| **O4** | `_git_run` in-scope set | Consolidate the **3** sites with identical `timeout=10` + swallow-`(TimeoutExpired, OSError)` semantics: the inline call in `_check_verification_git_reality` (~:353), `_resolve_base_ref`'s inner `_git` (~:454), and `_in_changeset`'s inner `_git` (~:505). **Exclude `_resolve_git_root` (~:703)** — it has materially different semantics (no timeout; lets errors propagate to trigger its explicit `parent.parent.parent` fallback-with-warning; bootstraps git_root before it is known). Folding it in would silently add a timeout and swallow OSError → change behavior. Justified exclusion per the audit-ALL-callers rule. (See Task 7.) |

## Write-Scope Partitioning

| Task | Owned Files (write) | Read-Only | Depends On |
|------|---------------------|-----------|------------|
| 1 | `controller-checkpoint.py` (`_review_tiers_per_task`), `tests/unit/test_pre_completion_gates.py` | `find_report_file` precedent | — |
| 2 | `controller-checkpoint.py` (`_check_verification_git_reality` + new helper), `tests/unit/test_pre_completion_gates.py` | Task 1's func | 1 |
| 3 | `sdd-pre-dispatch-hook.sh`, `tests/ARaymond-hook-baseline/baseline.txt`, `skills/subagent-driven-development/references/dispatch-markers.md` (new), `tests/unit/test_sdd_classification.py` | controller-checkpoint.py:324 (contract) | 2 |
| 4 | `transition-module.py` (`validate_module_completion`), `tests/unit/test_transition_module.py` | hook `get_task_type` | 3 |
| 5 | `_report_utils.py`, `validate-plan.py` (WARNING), `tests/unit/sdd_test_helpers.py` (+`_load_script`), `tests/unit/test_fence_aware_parsing.py` | — | 4 |
| 6 | `validate-plan.py` (`_C2_RISK_PATTERNS`), `tests/unit/test_c2_integration_gate.py` | Task 5's `_unfenced_content` | 5 |
| 7 | `controller-checkpoint.py` (`_git_run` SSOT), `tests/unit/test_c2_integration_gate.py` | the 3 git call sites | 6 |
| 8 | `controller-checkpoint.py` (Check 10 feature-window), `tests/unit/test_c2_integration_gate.py` | Task 7's `_git_run` | 7 |
| 9 | `controller-checkpoint.py` (frontmatter scan + diagnostics), `tests/unit/test_c2_integration_gate.py` | Task 8's edits | 8 |
| 10 | `skills/subagent-driven-development/SKILL.md` | — | 9 |
| 11 | `tests/ARaymond-skill-regression/validate-all-skills.py` | `writing-plans/SKILL.md` | 10 |
| 12 | `CLAUDE.md`, `docs/ARaymond-customization-manifest.md` | controller-checkpoint.py, hook | 11 |
| 13 | (none — `task_type: verification`, grep-only audit) | code + Task 12's docs | 12 |
| 14 | `tests/integration/sdd-e2e-test.sh`, `docs/process-improvement-findings/BACKLOG.md` | all | 13 |

## File Map

This parent is a coordination document — the implementation tasks (with complete code) live in the two module files. See:
- `module-1-aggregate-visibility.md` — Tasks 1-4
- `module-2-calibration.md` — Tasks 5-14

## Self-Hosting Hazards (pre-log these as accepted deviations at execution time)

Live enforcement during this run resolves to **main's (pre-fix) scripts** via the `~/.claude/skills/superpowers` symlinks. Pre-log each of these in `deviations.md` BEFORE execution:

1. **This run's own pre-completion Check 7/9 stay blind to Module-1 archives** (they run main's pre-fix code). Not blocking — blindness only narrows the ratio denominator to Module-2 evidence (same posture as sprint 3). The fix first protects the NEXT multi-module run; the **new e2e Step 12 (Task 14) is the in-sprint proof** that this checkout's code is archive-aware.
2. **The plan/module text quotes risk-surface keywords** (N22's pattern list, N25 prose). Main's pre-N22 `check_integration_test_risk` is fence-blind and reads per-file frontmatter, so it would self-WARN. Mitigation: all three plan files declare `integration_test: {path: tests/integration/sdd-e2e-test.sh}` in frontmatter (advisory WARNING suppressed; the e2e step genuinely IS the integration test — honest declaration).
3. **Check 9 visibility for the verification task** (Task 13) depends on its implementer dispatch entry being in the LIVE log at pre-completion — guaranteed by placing it in Module 2 (its dispatch is logged after the Module-1→2 transition truncates the live log).
4. **N7/N3a/N18/N16 are all on main** → the sprint-3 hazards (Source Contracts None FAIL, no-Task-0 start, verification-report rejection for empty `files_changed`) do NOT recur this run.

## Acceptance Criteria

- [x] Check 7 FAILs on the archived-minimum-tier fixture; single-module workspaces unchanged.
- [x] Check 9 FAILs on the archived-window file-modification fixture; silent-skip class closed.
- [x] Three live sprint-3 fix-cycle shapes WITH markers → fully attributed log entries; markerless fix → `fix-unattributed` line; marked fix emits NO `type=implementer` line; `fix-n18-*`-style names no longer trip Check 3b.
- [x] Check 10 PASSes for a committed integration test in an on-main remoteless feature window; still FAILs pre-window files and malformed declarations.
- [x] Risk-surface WARNING matches inflected forms (`migrations`/`caches`/`routers`/`authentication`); ignores fence-only keywords.
- [x] `_unfenced_content` handles `~~~` fences; unclosed-fence behavior pinned; validate-plan WARNs on an unclosed fence.
- [x] N6 lands with net SDD SKILL.md word count ≤ current (4911); regression suite green.
- [x] F6 intent-based, scoped to `writing-plans/SKILL.md`; full regression suite green.
- [x] Sprint executed as 2 modules with a live transition AND a non-last verification task whose report validates.
- [x] Archive-awareness inventory (5 sites) consistent across code, CLAUDE.md, manifest — verified by Task 13.
- [x] Hook baseline re-captured in the same commit as the hook edit (Task 3).
- [x] All four suites green (unit, regression, install, e2e); BACKLOG rows N19/N20/N22/N25(a-d,f)/N26/N27/N6/N8 flipped with commit refs; N25(e,g) + N21/N23/N24/N28(a,b,d) remain open with a pointer to this feature.
