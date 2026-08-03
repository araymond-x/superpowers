---
schema_version: 1
task_id: 1
task_type: implementation
status: DONE
files_changed:
  - path: "docs/process-improvement-findings/BACKLOG.md"
    description: "Row N76 only: completed the `cmux rpc` residual closure condition (two requirements → three, with the silent-ignore indistinguishability), and folded in the clause (3) NEW-6 alignment (drop the 'one real per-surface channel' exclusivity claim; name both contract channels and dispose of the SSH half at a-help strength)."
tests:
  written: 0
  passing: 0
  command: "bash tests/ARaymond-installation/verify-symlink-install.sh"
  result: PASS
contract_compliance:
  - constraint: "Write scope = BACKLOG.md row N76 only"
    status: compliant
    detail: "Single commit ad4a058, single file, single hunk `@@ -123 +123 @@`, 1 insertion / 1 deletion. Disposition doc, deviations.md and all reports/ files untouched and unstaged."
  - constraint: "Do NOT invoke cmux (no --help, --version, rpc, probes)"
    status: compliant
    detail: "Zero cmux invocations. Every fact came from the disposition doc, the round-3 review, and the existing BACKLOG rows. Commands run: git, grep, python3 counters, one repo test script."
  - constraint: "Do not fix or propagate N54/N57 pipe corruption"
    status: compliant
    detail: "Both rows byte-identical across HEAD~1..HEAD; still 9 and 11 unescaped pipes; absent from the diff."
  - constraint: "Never `git add -A`; never `git stash`"
    status: compliant
    detail: "Staged exactly `docs/process-improvement-findings/BACKLOG.md`. No stash."
---

## Implementation Summary

Closes MINOR-1 from the round-3 adversarial re-review (verdict: APPROVED). Two clause-sized edits inside N76, applied one at a time with the pipe gate run between them so a dropped pipe would be attributable to a single edit.

**Edit 1 — MINOR-1, applied verbatim as the reviewer wrote it.** `Closing it needs a create plus a read-back.` → `Closing it needs a correctly-guessed parameter name, a create, and a read-back — a wrong name is silently ignored and is indistinguishable from the feature not existing.` N76 now matches both doc sites (§Axis 3's "requires **three** things, not two" and §"What could not be established" item 1), closing the wrong-closure trap for a reader holding only the standalone row.

**Edit 2 — NEW-6 fold-in, clause (3).** `(3) the one real per-surface channel, …` → `(3) of the **two** per-surface channels the contract names, the `--layout` `surfaces[].env` one **works** (a-run: `SP2_LAYOUT=delta`) but is **workspace-creation-time only**, and SSH startup env creates its own workspace (a-help), so neither is a channel into this one.`

The exclusivity claim ("the one real") is gone; the contract's two-channel count and the SSH half's a-help disposition now match the doc's retitled §"Per-surface env channels". Kept deliberately as a *list item*, not a summary — a first draft opened with "neither reaches an existing workspace's surfaces", which restated the enclosing list's own premise and read as a conclusion rather than as item (3) of three.

**Cross-reference preserved.** Clause (1) contains the pointer *"the `--layout` channel in (3) below works and is equally invisible to it"*. Verified post-edit that clause (3) still names `--layout` explicitly, so the pointer resolves to exactly one referent despite now mentioning two channels.

## Source Files Read

- `docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/task-001-quality-review-round-3.md` (full)
- `docs/process-improvement-findings/BACKLOG.md` (row N76 in full; rows N67/N72/N75/N51/N54/N57 for controls and the sweep)
- `docs/process-improvement-findings/2026-07-30-sp2-workspace-env-probe.md` (read-only: §Axis 3's three-requirement blockquote and §"Per-surface env channels", to align wording — not edited)

## CLAUDE.md Files Read

- Repo-root `CLAUDE.md`, "cmux Auto-Spawn Handoff" section. Two conventions bound this edit and both were honored: **no line-number citations in durable artifacts** (the new clause (3) cites constructs — `--layout`, `surfaces[].env`, `cmux ssh` — and no coordinates), and **no hardcoded counts where a command can compute them** (the added word "two" is a count *quoted from the upstream contract sentence*, not a measured repo quantity; every measured count in this report is accompanied by the command that produced it).
- User global `CLAUDE.md` and `~/.claude/rules/*` loaded via system context.

## Deviations from Plan

None. Both edits were applied as specified (MINOR-1 verbatim, clause (3) minimally), the per-finding sweep was run across both in-scope rows, and all mandatory gates were executed rather than described.

One process note, not a deviation: the implementer trimmed its own first draft of clause (3) before applying it, for the list-item-vs-conclusion reason above. The applied text is the trimmed version.

## Self-Review Findings

### Per-finding propagation sweep — the root-cause instruction

The round-3 reviewer diagnosed *why* MINOR-1 existed: round 3's occurrence sweep was scoped to the BLOCKING finding's markers across both files, while the IMPORTANT and MINOR findings were fixed only at the doc sites the review named, with no equivalent sweep of `BACKLOG.md`. Its instruction was to sweep **per finding, not per severity**. Executed across N76 and N67, with a 260-character context window around every regex hit rather than a bare match count. Results, **including the no-ops**:

**NEW-2 — the `cmux rpc` residual.** Three `rpc` occurrences in N76, decomposing into one defect and two correct statements:
1. *"Closing it needs a create plus a read-back"* — **the MINOR-1 site. Fixed.**
2. *"an exit code cannot either (`cmux rpc` silently ignores unknown params — a-run)"* — correct as-is, and precisely the datum the new clause leans on. Unchanged.
3. *"the capability matrix §2.9 already recommends 'do not build on `rpc`'"* — a citation, not a closure condition. Unchanged.

No second occurrence of the understated bound. N67 contains zero `rpc` mentions. → one site, fixed.

**NEW-3 — the Axis 4 sweep population. Round 3's claim VERIFIED, not assumed.** One `127` occurrence in N76, in the Residual, already carrying all three qualifiers the doc adopted: the extraction artifact (*"127 unique names extracted from the `Commands:` block"*), the alternation collapse (*"the extraction collapses alternation rows to their first token"*), and the sibling probe (*"the seven names it drops were probed separately with zero `--env` hits"*). N67 contains no `127`. → **verified no-op, no change.**

**NEW-4 — the "no env channel" qualifier. Three hits in N76; exactly one is a live assertion, and it is qualified.** The decomposition is reported because a future reader grepping the literal string `"no env channel on any axis"` will find it and may think the sweep missed one:
1. **Live assertion, qualified** — *"**no env channel any documented CLI verb reaches gets to it** (read that qualifier literally — see the Residual below)"*. ✓
2. **Self-quote inside its own correction** — *"the \"no env channel on any axis\" claim covers **documented CLI verbs**"*. The Residual's opening, which exists to narrow the original wrong bound; the unqualified phrase appears only as the thing being corrected. ✓
3. **Different sense entirely** — *"fork the shared wrapper's env channel"*. About Decision 2's one-wrapper rule, not an absence claim. ✓

N67's counterpart — *"**no documented CLI verb carries env to it**"* — is already qualified. → **verified no-op, no change.**

**NEW-6 — the per-surface channel count.** Two `per-surface` occurrences in N76:
1. Clause (3), *"the one real per-surface channel"* — **the exclusivity claim. Fixed.**
2. The closing Consequence, *"shows no layout per-surface env — never treat the configured view as ground truth"* — a claim about what `cmux workspace env` displays, not a count of channels. Unchanged.

N67's nearest construct — *"the `--layout` `surfaces[].env` channel named above is **real and exercised** (a-run) but **workspace-creation-time only**"* — makes no exclusivity or count claim, so there is no contradiction with the contract's two channels to correct. → **verified no-op in N67, no change.**

**No propagation gap found beyond the two the brief named.** Nothing required escalation.

### Gate 1 — unescaped-pipe count, run after each edit

Counted with a negative lookbehind (`(?<!\\)\|`) so escaped `\|` does not count — N76 legitimately contains escaped pipes inside `SP2_WS_MARK=alpha\|beta\|file_plain\|file_export` and `SP2_SURF_MARK=\|alpha`, which a naive count would inflate.

```
GATE 1 — after EDIT 1 (MINOR-1 residual clause)
  line  22  header    unescaped_pipes=8
  line  23  separator unescaped_pipes=8
  line 101  N54       unescaped_pipes=9
  line 104  N57       unescaped_pipes=11
  line 114  N67       unescaped_pipes=8
  line 119  N72       unescaped_pipes=8
  line 122  N75       unescaped_pipes=8
  line 123  N76       unescaped_pipes=8
  line 124  N51       unescaped_pipes=8

GATE 1 — after EDIT 2 (clause (3) NEW-6 fold-in)
  line  22  header    unescaped_pipes=8
  line  23  separator unescaped_pipes=8
  line 101  N54       unescaped_pipes=9
  line 104  N57       unescaped_pipes=11
  line 114  N67       unescaped_pipes=8
  line 119  N72       unescaped_pipes=8
  line 122  N75       unescaped_pipes=8
  line 123  N76       unescaped_pipes=8
  line 124  N51       unescaped_pipes=8

clause (1) -> clause (3) pointer check:
  HIT: the `--layout` channel in (3) below works and is equally invisible to it)
  HIT: (3) of the **two** per-surface channels the contract names, the `--layout` `surfaces[]
```

### Gate 2 — diff containment

```
=== GATE 2: diff containment ===
--- a/docs/process-improvement-findings/BACKLOG.md
+++ b/docs/process-improvement-findings/BACKLOG.md
@@ -123 +123 @@ Living ledger of open, in-flight, and completed process/tooling improvements for
=== stat ===
 docs/process-improvement-findings/BACKLOG.md | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
```

One hunk, at the N76 row. Both edits collapse into this single hunk because they land on the same physical line — expected for an in-row table edit, not a scope leak.

### Gate 3 — N54 and N57 unchanged

```
=== GATE 3: N54 / N57 untouched ===
changed lines in diff body: 2
  - row=N76  pipes=8
  + row=N76  pipes=8
  N54: pipes 9 -> 9; byte-identical across commit = True; added/removed lines for this row = 0
  N57: pipes 11 -> 11; byte-identical across commit = True; added/removed lines for this row = 0
=== N54/N57 appear in diff? (expect no output) ===
  (none — confirmed untouched)
```

Stronger than "zero added/removed lines": both rows are byte-identical between `HEAD~1` and `HEAD`, and neither appears in the diff at all.

### Install suite

```
  Passed:   104
  Failed:   0
  Warnings: 0

STATUS: PASSED
```

### Controller-side independent verification

The controller re-ran the gates against the committed tree rather than accepting the pasted output: `ad4a058` touches exactly one file, 1 insertion / 1 deletion; the only hunk is `@@ -123 +123 @@`; pipe counts are 8 on the header, N67, N72, N75, N76, N51 and 9/11 on N54/N57; and both amended clauses read as reported in the committed row.

## Concerns

1. **Untracked / modified artifacts left unstaged by design.** At commit time `git status --short` showed the round-3 review file as untracked plus two modified controller-owned logs (`reports/.dispatch-log`, `reports/context-observations.log`). All three are outside the implementer's write scope, so only the explicit BACKLOG path was staged. *(Controller: the review file and register updates are committed in the immediately following commit.)*

2. **The disposition doc was verified consistent but not re-verified empirically.** N76's new wording was confirmed by reading to match the doc's §Axis 3 blockquote and §"Per-surface env channels". The underlying cmux facts were not re-derived — the no-`cmux` constraint forbids it, and the round-3 reviewer already independently reproduced the `cmux rpc` param table and the `cmux ssh --help` prose. This is a text-alignment edit resting on those verifications.

3. **The SSH half remains a-help strength in N76, matching the doc.** Clause (3) says SSH startup env "creates its own workspace (a-help)". That provenance label is inherited from the doc's own declared strength (prose read, `cmux ssh` never run) and is intentionally not upgraded — upgrading it would require running `cmux ssh`, out of scope and state-creating.

4. **Scope discipline held on the tempting adjacent fix.** N72 also carries a bare *"the headline '127 top-level commands'"* framing that the NEW-3 qualifier would improve. Out of scope for this amendment; not touched. Flagged as an observation only — arguably self-correcting, since N72's own text already concedes `--help` is not a complete enumeration.
