---
schema_version: 1
task_id: 1
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "docs/process-improvement-findings/2026-07-30-sp2-workspace-env-probe.md"
    description: "Round-3 prose remediation: replaced the invalid 'third leg' absence-of-evidence inference at both doc sites with the narrower true claim plus an explicit statement of what the configured view cannot adjudicate; corrected the §Axis 3 `cmux rpc` false contrast (the `workspace` key is itself ignored) and strengthened the residual to require a correctly-guessed param name; added Axis 4 scope limit 3 (127 = unique first tokens, seven alternation siblings probed separately) and qualified the three 'all 127' sites; qualified §Disposition's branch summary with 'any documented CLI verb reaches'; retitled the per-surface section and disposed of the SSH half."
  - path: "docs/process-improvement-findings/BACKLOG.md"
    description: "N76 clause (1): third-leg inference replaced with the narrow rules-out claim; N76 Residual: sweep population qualified. N67 UPDATE: narrowed the 'both spellings x both halves' cross-product to name the `new-workspace`-only re-capture and `workspace create`'s un-re-verifiable inherited half. Rows N67 and N76 only."
tests:
  written: 0
  passing: 0
  command: "bash tests/ARaymond-installation/verify-symlink-install.sh"
  result: PASS
contract_compliance:
  - constraint: "Per-verb `OK` shapes (parent plan Shared Contract Section item 1)"
    status: not_applicable
    detail: "Documentation-only round; no probe run, no OK-shape parsing added or changed."
  - constraint: "Measurement method is pinned (true cold start; shipped default = measured p95 x 2)"
    status: not_applicable
    detail: "No timing measurement in scope."
  - constraint: "Screen polling allowed as a measurement instrument only, never the production readiness signal"
    status: not_applicable
    detail: "No polling code or claim touched."
  - constraint: "HARD CONSTRAINT: do not invoke `cmux` at all"
    status: compliant
    detail: "Zero cmux invocations. Every datum new to the doc this round is either already-recorded a-run evidence or explicitly labeled reviewer-sourced."
  - constraint: "Write scope = the disposition doc + BACKLOG rows N67/N76 only"
    status: compliant
    detail: "Commit a71dfba touches exactly two files; BACKLOG diff hunks are at lines 114 and 123 only (Gate 2). deviations.md and the task-001 reports untouched."
---

## Implementation Summary

Six reasoning/legibility defects fixed across two files, no probe re-run, disposition unchanged. Committed as `a71dfba`.

**NEW-1 (BLOCKING).** The "third leg" argued that `SP2_SURF`'s absence from `cmux workspace env` proved the flag is "never recorded at all" — an absence-of-evidence inference the same document refutes, since `--layout` `surfaces[].env` demonstrably works and is equally invisible to that view. Both editable doc sites and the N76 clause now state only what the probe establishes (`new-surface --env` is not a covert *workspace*-env setter) and say explicitly that the configured view cannot adjudicate a surface-scoped implementation either way, with Step D's read-back carrying the conclusion. The transcripts are untouched.

**NEW-2 (IMPORTANT).** The §Axis 3 `cmux rpc` "it works" transcript is now labeled as what it is: the `workspace` key it passes is not honored by that method, so the matching `workspace_ref` is a coincidence of the session's no-param default. Presented as making the silent-ignore point twice over rather than as an erratum, with the reviewer's param table summarized and provenance-labeled, and with an explicit note that `{"workspace_id":"<uuid>"}` *is* honored so the withdrawn bound stays withdrawn. The residual was upgraded at **both** sites (§Axis 3 bullet and §"What could not be established" item 1): settling `rpc surface.create` needs a correctly-guessed param name *plus* create *plus* read-back, and that strengthens do-not-adopt.

**NEW-3 (MINOR).** Added Axis 4 scope limit 3 naming the extraction artifact and the seven collapsed alternation siblings (reviewer-probed, zero hits), and qualified the three "all 127" sites (Axis 4 headline, Bottom line item 3, deviations row 10) plus N76's Residual. §Disposition's "127-verb sweep in §Axis 4" left alone — it cites the section that now carries the limit.

**NEW-4 (MINOR).** §Disposition's branch summary now reads "no env channel any *documented CLI verb* reaches".

**NEW-5 (MINOR).** N67's UPDATE no longer reads as a cross-product; it names the `new-workspace`-only re-capture, marks `workspace create`'s inherited-process half as resting on the first session's un-re-verifiable capture, and states that only the evidence label (not the claim) was wrong.

**NEW-6 (MINOR).** Heading retitled to "Per-surface env channels — both the contract names, and why neither helps"; the SSH half is now disposed of via `cmux ssh --help` (reviewer-read). SSH is stated **negatively** (not a channel into an already-existing workspace's surfaces) rather than as "creation-time only" — zero `env` mentions supports the negative claim, not the positive one. The Bottom-line cross-reference at the old heading was updated to match.

### Per-finding disposition

| Finding | What changed | Where |
|---|---|---|
| NEW-1 | Inference replaced by the narrow rules-out claim + explicit non-adjudication, citing the layout finding | doc §Axis 2 parenthetical; doc §Step C; BACKLOG N76 clause (1) |
| NEW-2a | `workspace` key stated as ignored; reviewer param table summarized; "does not resurrect the bound" | doc §Axis 3 corrected-limit blockquote |
| NEW-2b | Residual upgraded to three requirements incl. correct param name; framed as strengthening do-not-adopt | doc §Axis 3 bullet; doc §"What could not be established" item 1 |
| NEW-3 | New scope limit 3; four "all 127" phrasings qualified | doc §Axis 4 (x2), Bottom line item 3, deviations row 10, BACKLOG N76 Residual |
| NEW-4 | Qualifier added | doc §Disposition branch summary |
| NEW-5 | Cross-product narrowed to the actual evidence labels | BACKLOG N67 UPDATE |
| NEW-6 | Heading retitled; SSH half disposed of (negative claim) | doc §Per-surface env channels; Bottom line item 3 |

### NEW-1 occurrence set (complete)

Sweep command:

```
grep -niE 'never recorded|not merely unexported|unexported|third leg|consumed and discard|does not appear in the configured view|absent from the configured view' \
  docs/process-improvement-findings/2026-07-30-sp2-workspace-env-probe.md \
  docs/process-improvement-findings/BACKLOG.md
```

Broadened with a second pass on `configured view|SP2_SURF` across both files, and §Step E, §Disposition and §"What could not be established" were read in full rather than trusted to grep. **Five occurrences, three of them mine:**

| # | Site | Disposition |
|---|---|---|
| 1 | Doc §Axis 2, "adds a third leg the first session did not have (… not merely unexported — it is never recorded)", labeled **a-run** | **FIXED.** Not named by the review — found by the sweep. Rewritten to the rules-out claim; the **a-run** label is *kept* on the observation itself (the datum is this doc's own; only the inference was defective — a provenance downgrade would be as wrong as an upgrade). |
| 2 | Doc §Step C, "The third leg the first session lacked … never recorded at all. The flag is consumed and discarded." | **FIXED.** Replaced with the narrow claim + explicit non-adjudication + pointer to Step D. |
| 3 | BACKLOG N76 clause (1), "A third leg: `SP2_SURF` never appears in `cmux workspace env` either…" | **FIXED.** Same replacement, no unescaped pipes introduced (Gate 1). |
| 4 | `docs/imp-plans/2026-07-30-cmux-spawn-v2/deviations.md` row at line 64 | **NOT MINE — controller-owned**, and confirmed as the review's own third named site (`task-001-quality-review-round-2.md`, NEW-1 `Where:` clause names "doc §'Re-capture' Step C; N76 clause (1); `deviations.md` row at line 64"). Untouched per the task's hard constraint. |
| 5 | `reports/task-001-fix-implementer-report.md`, "a third leg the first session did not have: the surface-level `--env` is not merely unexported, it is **never recorded**" (and a second mention in its round-1 disposition prose) | **IMMUTABLE — corrected here, not there.** See Concerns 1. |

Post-edit re-run of the sweep over the two in-scope files returns exactly one hit: the deliberate disavowal inside the new §Step C text ("an earlier draft of this section overreached by concluding the flag was therefore 'never recorded at all.'"). No assertion of the inference survives in either file.

### Mechanical gates — raw output

**Gate 1 — unescaped-pipe count (negative lookbehind, so `\|` does not count).** Command:

```
python3 - <<'EOF'
import re
lines=open('docs/process-improvement-findings/BACKLOG.md').read().split('\n')
pat=re.compile(r'(?<!\\)\|')          # negative lookbehind: escaped \| does not count
edited=(114,123); controls=(22,23,119,122,124); untouched=(101,104)
for label,rows in (("EDITED",edited),("CONTROL",controls),("MUST-NOT-CHANGE",untouched)):
    for i in rows:
        print(f"{label:16} line {i:>3}: {len(pat.findall(lines[i-1])):>2} unescaped pipes | {lines[i-1][:34]}")
EOF
```

Output:

```
EDITED           line 114:  8 unescaped pipes | | N67 | Use `cmux new-workspace --
EDITED           line 123:  8 unescaped pipes | | N76 | SP2 disposition — cmux `--
CONTROL          line  22:  8 unescaped pipes | | ID | Title | Source | Improves |
CONTROL          line  23:  8 unescaped pipes | |---|---|---|---|---|---|---|
CONTROL          line 119:  8 unescaped pipes | | N72 | Add a capability-drift gua
CONTROL          line 122:  8 unescaped pipes | | N75 | WATCH ITEM: cmux "Fork Con
CONTROL          line 124:  8 unescaped pipes | | N51 | codex-picker parity → code
MUST-NOT-CHANGE  line 101:  9 unescaped pipes | | N54 | `SKILL.md`'s trace-extract
MUST-NOT-CHANGE  line 104: 11 unescaped pipes | | N57 | Successor topology: worksp
```

The counter was validated against the header + controls **before** the first BACKLOG edit, and re-run immediately after each of the three BACKLOG edits (not once at the end), so a dropped pipe would have been attributable to a single edit.

**Gate 2 — diff containment.**

```
$ git diff --unified=0 48322a9..HEAD -- docs/process-improvement-findings/BACKLOG.md | grep -E '^@@'
@@ -114 +114 @@ Living ledger of open, in-flight, and completed process/tooling improvements for
@@ -123 +123 @@ Living ledger of open, in-flight, and completed process/tooling improvements for
```

Two hunks, at the N67 row (114) and the N76 row (123). Nothing else.

**Gate 3 — N54/N57 untouched.**

```
$ git diff 48322a9..HEAD -- docs/process-improvement-findings/BACKLOG.md | grep -cE '^[+-]\| N5[47] '
0
```

Zero added/removed lines for either row; Gate 1 confirms they still read 9 and 11. Not fixed, not propagated.

**Install verification.**

```
$ bash tests/ARaymond-installation/verify-symlink-install.sh
  Passed:   104
  Failed:   0
  Warnings: 0

STATUS: PASSED
```

**Fence hygiene.** 26 fences opened, balanced, zero left/up-arrow annotations inside any fence (checked with a blockquote-aware scanner, since two insertions sit inside the §Axis 3 blockquote alongside nested fences; the `>` prefix survives on every inserted line).

### Controller-side independent verification

The controller re-ran all three gates against the committed tree rather than accepting the pasted output: commit `a71dfba` touches exactly 2 files; `git diff --unified=0 48322a9..HEAD -- BACKLOG.md` shows hunks only at 114 and 123; the N54/N57 add/remove count is 0; the pipe counter reproduces 8 on the header, N67, N76, N72, N75, N51 and 9/11 on N54/N57; and the post-edit inference sweep returns only the deliberate disavowal. The NEW-1 replacement text was read at all three sites and confirmed to state the narrow claim, the explicit non-adjudication, and the cross-reference to the layout finding.

## Source Files Read

- `docs/process-improvement-findings/2026-07-30-sp2-workspace-env-probe.md` (full, 894 lines pre-edit)
- `docs/process-improvement-findings/BACKLOG.md` (rows N67, N76, N72, N75, N51, N54, N57; full-file pipe scan)
- `docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/task-001-quality-review-round-2.md` (NEW-1 through NEW-6 sections, the reviewer's measurement summary table, and the NEW-1 `Where:` clause) — read-only, for exact reviewer measurements and provenance wording
- `docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/task-001-fix-implementer-report.md` (grep for inference markers) — read-only
- `docs/imp-plans/2026-07-30-cmux-spawn-v2/deviations.md` (grep only, to confirm the controller-owned site) — read-only, not edited

## CLAUDE.md Files Read

- Repo-root `CLAUDE.md` — the "cmux Auto-Spawn Handoff" standing rules bind directly: **no line-number citations in durable artifacts** (every new citation names a construct or a quoted string; the line references in this report's occurrence table are report-local and quote the reviewer's own phrasing), and **no hardcoded counts where a command computes them** (the surviving "127" is a recorded probe output whose extraction command is printed immediately above it — qualified rather than churned).
- `~/.claude/CLAUDE.md` + rules — evidence-backed claims, no fabricated runtime state.
- No `CLAUDE.md` exists in `docs/process-improvement-findings/` (checked).

## Deviations from Plan

1. **NEW-2's option 1 was unavailable.** The reviewer offered "re-run the transcript with the honored `workspace_id` form" or "state that the `workspace` key is ignored". Option 1 requires a live `cmux rpc` call, which this round forbids, so option 2 was taken as instructed. The doc now carries a stated correction rather than a corrected transcript.
2. **NEW-6's heading was changed, not just annotated.** The finding left this to judgment. "The one per-surface env channel that does exist" could not survive a clause disposing of a second channel, and the Bottom-line cross-reference used the same wording, so both were updated. Two sites, both editable, both in scope.
3. **A fifth NEW-1 occurrence was found beyond the review's three and the dispatch's four.** The dispatch predicted the sweep would find sites the review did not name; it found one editable (§Axis 2) plus one immutable (the round-2 fix implementer report). Recorded rather than silently absorbed.

## Self-Review Findings

- The occurrence sweep ran on both files before editing and again after; §Step E, §Disposition and §"What could not be established" were read in full, not grepped. §Step E carries no restatement; §Disposition's only unqualified restatement was NEW-4, fixed; §"What could not be established" item 1 needed the NEW-2b residual upgrade, applied.
- **Three** reviewer-sourced data entered the doc, each carrying an explicit provenance label naming the round-2 adversarial re-review, the date, and the pinned binary: the `cmux rpc` param table (NEW-2), the seven alternation-sibling probes (NEW-3), and `cmux ssh --help` (NEW-6). Nothing else was imported. No reviewer datum is labeled **a-run** as this document's own.
- **No provenance downgrade either.** The §Axis 2 `SP2_SURF`-absent observation is this document's own Step C capture, so it retains **a-run**; only the inference drawn from it was replaced.
- **A first draft of the SSH clause was corrected before writing:** it said the SSH channel is "workspace-creation-time only" — an unearned *positive* claim inferred from help-text silence, i.e. a fresh instance of the very defect this round exists to remove. Rewritten as the negative claim the reviewer actually measured. Similarly, "silent by construction" in §Step C was changed to "as measured", since implementation knowledge was not available.
- Internal consistency after edits: no surviving sentence leans on the withdrawn inference; the layout finding and the Step C limit now cite each other in both directions; the "no env channel" claim carries the documented-CLI-verb qualifier at every site that asserts it (the one bare `**Answer:**` in §"The primary path" is the reviewer-accepted deliberate mitigation with its adjacent read-the-limit instruction, left unchanged).
- Two things deliberately **not** changed, both graded correct by the reviewer: the doc's Bottom line item 1 ("both halves verified... **and** both spellings exercised" — not a cross-product), and §Disposition's "the 127-verb sweep in §Axis 4" (cites the section that now carries scope limit 3).
- Only the two in-scope files are in the commit; `deviations.md` and all `task-001-*` reports are untouched in the working tree and in the diff.

## Concerns

1. **Two corrections are stranded in this report because their host file is immutable.** `reports/task-001-fix-implementer-report.md` carries (a) the NEW-1 inference — "a third leg the first session did not have: the surface-level `--env` is not merely unexported, it is **never recorded**" — and (b) NEW-5's cross-product overclaim, "Both spellings are now genuinely a-run on **both** halves". Both are corrected in the durable artifacts (doc + N76 + N67); anyone reading that report should treat those two passages as superseded by this round. Cited by quoted phrase rather than line number, per the repo's anchor-rot rule.
2. **Three reviewer-sourced imports are un-re-derived by this document.** The `cmux rpc` param table, the seven-command probe, and `cmux ssh --help` are labeled as reviewer measurements and were not re-run — the round's hard constraint forbids it. This feature's standing preference is to re-run first-hand; the labels make the dependency visible rather than laundering it, but a future reader wanting first-hand confirmation must re-probe. `cmux ssh --help` in particular resolves NEW-6 on **help prose**, not on running `cmux ssh` (the reviewer noted this limit too), so the SSH half is dispositioned at a-help strength while the layout half is a-run.
3. **The `cmux rpc surface.create` residual is now larger than it was recorded as, not smaller.** Closing it needs a correct parameter-name guess in a vocabulary that demonstrably differs from the CLI's, with silent failure on a wrong guess. This does not change the disposition (it reinforces do-not-adopt) but it does mean the residual is less likely to be cheaply closed by a future probe than the previous wording implied.
4. **`deviations.md` row 64 still carries the withdrawn inference** at the time of the implementer's report. It is the controller's to fix and was confirmed as the review's own third named propagation site; flagged so the round is not declared closed while that clause stands. *(Controller: fixed in the same window — see the deviations register.)*
