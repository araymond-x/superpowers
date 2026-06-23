# Task 12 — Spec Compliance Review (archive-awareness inventory docs 3→5)

**Verdict:** PASS
**Range:** `86ddb95..f3cfd72` (verified by reading both docs + grepping the actual code — this task gates the Task 13 audit, so the docs↔code match was checked independently)

## Findings

1. **Both statements say FIVE, correctly attributed** — PASS.
   - CLAUDE.md:206: "exactly five lookups (N4: `find_report_file` + `find_all_report_files`; N10: hook Check 5 Task-0 lookup; N27: `_review_tiers_per_task` for Check 7 + `_merged_dispatch_times` for Check 9)". Every lookup tied to the right BACKLOG id + Check.
   - manifest:329: "FIVE sites total: `find_report_file` + `find_all_report_files` (N4) + hook Check 5 Task-0 lookup (N10) + `_review_tiers_per_task` + `_merged_dispatch_times` (N27)". Same correct attribution.
2. **Manifest row intact** — PASS. Single 1-line hunk; word-level diff isolates the change to the one inventory sentence; everything before/after in the long table row is byte-identical.
3. **No stale statement remains** — PASS. Step-3 grep returns only the two updated FIVE-site sentences (matched on the unchanged "stays flat" tail); zero matches for "two lookups"/"three lookups"/"exactly these two"/"these two are the ONLY".
4. **DOCS MATCH CODE (critical for the downstream audit)** — PASS. Measured archive-aware-site count = **exactly 5**:
   - controller-checkpoint.py: `find_report_file` (:133), `find_all_report_files` (:196), `_review_tiers_per_task` (:248, Check 7), `_merged_dispatch_times` (:365, Check 9) — 4 distinct named functions globbing `archive-*/`.
   - sdd-pre-dispatch-hook.sh: Check 5 Task-0 lookup (`T0_GLOB`, :606) — 1.
   - Checked for a hidden 6th via non-`archive-*` idioms: remaining hits are comments, the `_classify_dir` sub-helper of `_review_tiers_per_task` (not a separate lookup), and the N18 boundary skip-guard (doesn't glob archives). No 6th site. 4 + 1 = 5.
5. **Scope** — PASS. `git diff --name-status` = only `CLAUDE.md` + `docs/ARaymond-customization-manifest.md`. No code, no other docs.

result: PASS — both inventory statements now state FIVE archive-aware lookups with correct function↔BACKLOG-id↔Check mapping; manifest row byte-identical except the one sentence; no stale statement survives; code independently confirmed at exactly 5 archive-aware sites (docs match code); scope = the 2 docs only.
