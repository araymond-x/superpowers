---
schema_version: 1
task_id: 9
status: DONE_WITH_CONCERNS
files_changed:
  - path: "docs/process-improvement-findings/2026-05-31-ssot-audit.md"
    description: "Created — SSOT audit findings (15 SKILL.md vs 4 active hooks; 8 prescriptions, 0 retire / 1 strengthen / 7 keep; 0 live threshold drift; methodology, findings table, summary, Sprint-3 quick wins)."
  - path: "docs/process-improvement-findings/BACKLOG.md"
    description: "N2 open→done; B6 + P1 open→done (implemented by this feature, pending merge); added N3-N9 rows for audit findings + execution-discovered hook/checkpoint gaps; kept the living-ledger internally consistent."
tests:
  written: 0
  passing: 0
  command: "n/a — read-only investigation"
  result: PASS
contract_compliance:
  - constraint: "Read-only: modify ONLY the 2 doc files (findings + BACKLOG)"
    status: compliant
    detail: "git status confirms exactly BACKLOG.md (M) + ssot-audit.md (new); no SKILL.md/hook/code touched."
  - constraint: "Audit 15 SKILL.md + exactly the 4 active hooks; exclude sdd-skill-enforcement + sdd-stop"
    status: compliant
    detail: "All 15 SKILL.md read; 4 active hooks read; exclusions named in the doc header and used as Finding 3 (pre-completion rides the excluded Stop hook)."
  - constraint: "Cite real line ranges; honest overlap count"
    status: compliant
    detail: "Line numbers verified against the actual files via grep (Check 6 L634-669, Check 5c L578-596, ratios L1234/L1267, transition L168); explicitly reported 0 retire and why (the token-estimation retire was already done by C6a)."
  - constraint: "N2 done; B6/P1 done (implemented this feature, pending merge); add N* rows for findings + deviations.md gaps"
    status: compliant
    detail: "N2→done w/ doc ref; B6/P1→done w/ pipeline-flexibility branch note; N3-N9 cover the 6 deviations.md gaps + the _task_ids_where dedup."
---

**Implementation Summary**
Audited all 15 `skills/*/SKILL.md` against the 4 settings.json-registered hooks (pre-dispatch, report-guard, plan-validation-gate, session-start), cross-referencing `controller-checkpoint.py`/`validate-plan.py`/`transition-module.py` for exact thresholds. Wrote `docs/process-improvement-findings/2026-05-31-ssot-audit.md` and updated `BACKLOG.md`. Committed `793b9e3`.

**Headline numbers:** 8 manual prescriptions found (concentrated in the two hook-backed skills — SDD + writing-plans; the other 13 skills are advisory-only with zero hook overlap, stated plainly rather than padded). Classification: **0 retire / 1 strengthen / 7 keep**. **0 live threshold drift** — verified the verification-ratio (SKILL ≤30% == code `>0.3`) and minimum-tier ratio (SKILL ≤50% == code `>0.5`) match; the "20%" the project CLAUDE.md warned about appears only in historical prose, not the live SKILL body. The one true "retire" anti-pattern (manual token estimation) was already retired by C6(a) on 2026-05-30 — no second instance found, reported honestly.

**Key result:** the SSOT picture is healthier than the C6 finding implied — the real gaps are not redundant ceremony but two structural problems, both hit first-hand this execution and captured from `deviations.md`: (1) `transition-module.py` truncates the live dispatch log (L168) → breaks the next module's first-task Check 4c provenance; (2) the pre-completion gate has no registered hook (rides the excluded `sdd-stop-hook.sh`) and isn't archive-aware. Spun out as actionable rows N3-N9 with concrete line numbers + fixes.

**Source Files Read**
- 15 SKILL.md: brainstorming, dispatching-parallel-agents, executing-plans, finishing-a-development-branch, handoff-acceptance, receiving-code-review, requesting-code-review, subagent-driven-development, systematic-debugging, test-driven-development, using-git-worktrees, using-superpowers, verification-before-completion, writing-plans, writing-skills.
- 4 hooks: sdd-pre-dispatch-hook.sh, sdd-report-guard.sh, plan-validation-gate-hook.sh, hooks/session-start.
- Threshold cross-ref: controller-checkpoint.py, validate-plan.py, transition-module.py. Plus BACKLOG.md + deviations.md.

**CLAUDE.md Files Read**
- Global `~/.claude/CLAUDE.md` + rules; project worktree `CLAUDE.md` (hook architecture, threshold history, exclusion rationale). No CLAUDE.md in `docs/process-improvement-findings/`.

**Deviations from Plan**
None on the deliverable. Two presentational notes: (1) the new P1 row uses an escaped literal pipe `\|` inside a cell — correct GitHub-Markdown, renders as one column (verified intentional). (2) Made small additional BACKLOG edits beyond the literal row list (ID legend, I2 note, recommended-sequencing, Sources) to keep the living ledger internally consistent with B6/P1/N2 now done.

**Self-Review Findings**
- Verified every cited line number against the actual file via grep before writing it.
- git working tree shows exactly the 2 intended files changed (no SKILL.md/hook/code) — read-only constraint satisfied.
- Table pipe-count check flagged only the one intentional escaped-pipe cell.

**Concerns**
- **Concern A (now findings N3/N4, open):** the most important audit results are *strengthen* items the read-only audit can't fix — the `transition-module.py` ↔ Check 4c incompatibility and the non-archive-aware pre-completion gate. Until N3+N4 ship, multi-module SDD requires the manual manifest-advance workaround this execution used.
- **Concern B:** the pre-completion gate (honesty check, trace audit, checkpoint ratios) is enforced only by the *unregistered* `sdd-stop-hook.sh` + controller discipline — at the live PreToolUse layer it's effectively advisory. Flagged as Finding 3; latent gap, not resolved by N2.
- Both are open structural gaps surfaced by the audit (captured in BACKLOG), not defects in this deliverable.
