---
schema_version: 1
task_id: 3
task_type: implementation
status: DONE
files_changed:
  - docs/process-improvement-findings/2026-07-30-sp4-carry-forward-fix-lane-design.md
  - docs/process-improvement-findings/BACKLOG.md
tests:
  written: 0
  passing: 104
  failing: 0
contract_compliance: |
  Write scope honored exactly: the two files named in the dispatch and no others.
  SP3 and N80 untouched. reports/* treated as immutable. Out-of-scope items (the
  hook's rotted comment, the --ignore-files CLAUDE.md gotcha) not touched — reported
  below. Every fence edit made in SP4 only; the BACKLOG N81 row regenerated
  programmatically from that fence, never hand-edited twice. No :NNN citations added.
  All recursive sweeps used /usr/bin/grep. Staged the two explicit paths; no git add -A,
  no git stash. Verification: verify-symlink-install.sh 104/0/0 PASSED.
---

## Implementation Summary

Two IMPORTANT findings from the round-3 quality re-review, both narrow text corrections
in SP4 and its N81 fence. Zero BLOCKING carried in.

**Fix 1 — conditioned the "three ways" claim on the plan-shape axis.** The dispatch
enumerated four defective sites. My own post-edit sweep confirmed those four and found a
**fifth in-class site the dispatch's enumeration missed** — N81's own plan-shape sentence
("caught by the latter alone"), the exact mirror of the S4 defect, inside the row that
ships to `main`. Fixed it under Fix 1's explicit instruction to sweep for further bare
gate counts. I also conditioned the **paired "last-in-range → two terminal gates"
bullets**, which over-attribute for the manifest-only cell by the same arithmetic
(details in Deviations).

**Fix 2 — added Check 4's N-1 globs as the third flat lookup.** Re-titled the section
from "Two flat lookups" to "Three", added a leading bullet for Check 4's globs (they fire
first), added them to §Candidate A's must-skip list naming the constructs, added them to
N81's flat enumeration, and qualified the "Check 4c is the exception" sentence with its
sibling's `-eq` keying — including the reachable-domain equivalence and the fact that
Candidate A's out-of-range admission is what separates the two guards. This absorbs fix
round 2's Concern 4 as instructed; not filed separately.

Byte-identity between SP4's fence and BACKLOG's N81 row was re-established by
regeneration, not by parallel editing.

## Source Files Read

- `docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/task-003-quality-review-round-3.md` (in full)
- `docs/process-improvement-findings/2026-07-30-sp4-carry-forward-fix-lane-design.md` (in full)
- `docs/process-improvement-findings/BACKLOG.md` (N81 row)
- `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` — `task_report_glob`,
  Check 4's N-1 sub-block, Check 4c, `T0_GLOB`
- `skills/subagent-driven-development/scripts/controller-checkpoint.py` — `TASK_HEADER_PATTERN`,
  `all_tasks_have_reports`
- `skills/subagent-driven-development/scripts/transition-module.py` — `validate_module_completion`

## CLAUDE.md Files Read

- `/Users/araymond/.claude/CLAUDE.md` (global) and rules `workflows.md`,
  `architectural-principles.md`, `git-workflow.md`, `project-structure.md`, `tools.md`
- `/Users/araymond/projects/claude-custom/superpowers/.worktrees/cmux-spawn-v2/CLAUDE.md`
  (project) — the no-`:NNN`, cite-constructs, and give-the-command-not-the-number rules
  governed every citation added this round.

## Claims Verified

**The four "three ways" sites — checked independently, not inherited.** Whitespace-normalized
sweep (sentences wrap, so a line-anchored pattern misses them):

```
for f in <SP4> <BACKLOG>; do
  tr '\n' ' ' < "$f" | tr -s ' ' | /usr/bin/grep -oiE \
  '.{0,120}(three ways|all three|both terminal|both gates|one to three|two terminal|two flat|three flat|(caught|blocked|policed|satisfied|invisible)[^.]{0,80}\balone\b).{0,120}'
done
```

Pre-edit this confirmed the dispatch's four sites verbatim, confirmed §Cost fork as the one
correctly-conditioned site, and surfaced the fifth (N81's "caught by the latter alone").
Post-edit, every surviving hit is either conditioned or a claim that is correct as written:
`Three gates bite` / `THREE gates bind` (which gates exist across cells, not a per-cell
catcher count), `one to three gates depending on those two axes` (a correct range), and
`rather than only the two terminal gates` (naming a category, not counting catchers). I
deliberately did not churn those three.

**Check 4's flat globs — verified at source, by construct.** `task_report_glob` builds
`"${REPORTS_DIR}/task-${padded}-${report_type}*"` with no `archive-*` term, and all three
Check-4 N-1 lookups route through it:

```
/usr/bin/grep -nE '(IMPL_GLOB|SPEC_GLOB|QUAL_GLOB)=\$\(task_report_glob' <hook>
```

returns exactly the three. The hook's only archive-aware lookup remains `T0_GLOB`
(`/usr/bin/grep -n 'archive-' <hook>` → two hits, one comment + `T0_GLOB`), so the doc's
existing instrument and its "exactly one archive-aware lookup" claim both still hold and
were kept.

**The skip-keying divergence — verified at source.** Check 4's N-1 sub-block skips on
`[ "$TASK_NUMBER" -eq "$MANIFEST_TASK_START" ]`; Check 4c skips on
`[ "$PREV" -lt "$MANIFEST_TASK_START" ]`. Both read directly. The equivalence-over-the-
reachable-domain argument (range guard runs first ⇒ `TASK_NUMBER >= START` ⇒ `-eq START`
⟺ `PREV -lt START`) follows from those two constructs plus the range guard's position.

**Scope note on method:** I verified the Check-4 claim **structurally, by construct — I did
not re-run the reviewer's X/Y/Z hook fixture.** For a claim of the form "this glob has no
archive term and these three lookups use it", source is the decisive evidence and a fixture
is a weaker proxy. I am stating this rather than implying I reproduced the runs.

**Supporting keying claims re-read at source:** `TASK_HEADER_PATTERN =
re.compile(r"^###\s+Task\s+(\d+)", ...)` consumed by `all_tasks_have_reports` via
`_unfenced_content` (⇒ blind to a header-less slot), versus `for task_id in
module.task_ids:` in `validate_module_completion` (⇒ manifest-keyed, sees it regardless).
This is the arithmetic behind both the dispatch's cross-product and my paired-bullet fix.

**Byte-identity — positive control FIRST, `cmp` on files.** Fence bounds located
tail-anchored (SP4 has one fence; `/usr/bin/grep -c '^\`\`\`'` → 2), extracted, and the
BACKLOG row replaced programmatically from it by a script asserting exactly one `^| N81 |`
line existed. Then:

```
cp n81-sp4.txt n81-mut.txt && printf 'x' >> n81-mut.txt
cmp n81-sp4.txt n81-mut.txt     # control: DIFFERS (proves cmp can fail)
cmp n81-sp4.txt n81-backlog.txt # live: identical
```

Control differed; live identical. Compared as **files**, not `$(...)` captures — command
substitution strips trailing newlines and would mask exactly the convention difference
round 3 saw in its 4873/6200 vs 4872/6199 byte counts. Sizes via
`wc -c n81-sp4.txt n81-backlog.txt` (equal; reporting the command rather than a number
that goes stale).

**Regressions round 3 verified — all still holding.** Zero `:NNN` citations in SP4 and its
fence; zero `handoff-spawn.log`/`context-observations.log` mentions (no conflation);
BACKLOG header/N80/N81 all `NF=9`; SP4's tables intact and **untouched by the diff** — the
3-column case-A table is `NF=5` on all 8 rows and the 4-column reserved-slot table is
`NF=6` on all 10 rows (my first pass at this check used a loose row pattern that spanned
both tables and reported a misleading 9×NF=5 + 10×NF=6; scoping each table with an
address range resolved it — the counts were consistent, not defective); N54/N57 untouched
(`git diff -- BACKLOG.md` is a single changed line, the N81 row);
`/usr/bin/grep -cE '^\| 0→' deviations.md` → 4 anchored versus 7 bare, still vindicating
the anchoring; SP4's two "grep that phrase" promises resolve 1/1 each.

**Verification:** `bash tests/ARaymond-installation/verify-symlink-install.sh` → 104 passed,
0 failed, 0 warnings, STATUS: PASSED.

## Deviations from Plan

**Deviation 1 — fixed a fifth site the dispatch did not enumerate.** N81's plan-shape
sentence ("...invisible to the former and caught by the latter alone") carries the identical
defect to S4, unconditioned, in the copy-forward row. The dispatch listed four sites but
also instructed a paraphrase-inclusive sweep for further bare gate counts including the
pattern "caught by … alone"; finding and fixing this executes that instruction rather than
exceeding scope. It is in-scope by file (the N81 row) and in-class by defect. Not filed as
a separate Concern, per the dispatch's instruction not to double-file in-class items.

**Deviation 2 — conditioned the paired "last-in-range → two terminal gates" bullets, which
the dispatch did not name.** "Caught only by the two terminal gates" over-attributes for
the last-in-range × manifest-only cell, where only `validate_module_completion` catches it
(the cross-product's fourth row, = 1). This follows from facts I verified at source:
manifest-only ⇒ no `### Task N` ⇒ invisible to `TASK_HEADER_PATTERN`; last-in-range ⇒
successor id out of range ⇒ Checks 4b/4c never run. I fixed it because leaving one member
of a matched placement pair conditioned and its sibling bare **recreates precisely the
asymmetry that produced this finding** (§Cost fork conditioned, the other three not) — it
would be the sprint's propagation under-count for a fourth time, for the price of one
clause. Both bullets now follow §Cost fork's framing: state the headered-shape figure and
let the plan-shape axis carry the remainder. Two sites (SP4 §Candidate A placement block,
SP4 §What could not be established) plus their N81 mirror.

**Deviation 3 — left both enforcement-interaction tables unedited.** The case-A table is
self-scoping via its "Not reached in case A" cells, and the reserved-slot table already
carries a "Checks 4b/4c on the *following* task" row with an `applies when` column. Editing
them was not required by either finding and would have risked the `NF` integrity the
regression battery pins. Recorded as a decision rather than performed.

## Self-Review Findings

- **Adjacent claim I checked rather than assumed:** the doc's "exactly **one** archive-aware
  lookup in the hook" and its `grep -c 'archive-'` → 2 instrument survive the Fix-2 edit
  unchanged. Adding a third *flat* lookup does not change the count of *archive-aware* ones;
  I confirmed at source before keeping both sentences, since a careless edit here would have
  made the section internally inconsistent.
- **Wording chosen to resist rot:** every construct I added is a greppable name
  (`IMPL_GLOB`, `SPEC_GLOB`, `QUAL_GLOB`, `task_report_glob`, `TASK_NUMBER -eq
  MANIFEST_TASK_START`, `PREV -lt MANIFEST_TASK_START`). No line numbers, no counts over
  live artifacts stated as literals.
- **The `-eq`/`-lt` clause is stated with its scope.** I wrote the equivalence *and* the
  divergence, because stating only the divergence would be misleading about today's
  behavior, and stating only the equivalence would reproduce the original error.
- **Sweep honesty:** my first sweep attempt was repo-wide and drowned in "alone" matches
  from unrelated docs. I narrowed the pattern to gate-count contexts rather than declaring
  the broad run clean — a broad run I could not read is not evidence.

## Concerns

1. **Out of scope, already routed — reported not fixed, per dispatch.** The hook's rotted
   `— :324` comment (baselined; a fix obliges a same-change `check-hooks.sh --capture`) and
   the `--ignore-files` sweep gotcha belonging in `CLAUDE.md`. Both untouched.

2. **An error in an immutable report, reported rather than edited.** The round-3 review's
   **IMPORTANT-1 `**Fix.**` line** frames the work as "Four one-clause edits; regenerate N81 from
   the fence so byte-identity survives." That undercounts by the two paired last-in-range bullets
   and the fifth N81 site (Deviations 1 and 2). The
   review is a contemporaneous record and I did not modify it; noting it so the count is not
   inherited a fourth time. The pattern is now three rounds deep and consistent: **every
   enumeration of propagation sites in this task has undercounted, including the ones written
   to correct an undercount.** A future controller should treat any such enumeration as a
   lower bound and run the sweep, not the list.

3. **Not verified this round, and I am flagging rather than asserting.** I did not re-run the
   reviewer's hook fixture (X/Y/Z) or the `all_tasks_have_reports` fixture measurements. My
   edits rest on source-construct verification plus the cross-product arithmetic, which is
   sufficient for the structural claims I wrote but is *not* an independent reproduction of
   the reviewer's runtime results. Those results remain single-sourced from round 3 for the
   runtime half (that Check 4c is silent while Check 4 blocks under an out-of-range
   admission); the *structural* half — why that must be so — I confirmed directly.

4. **N81 is long and still growing.** The row is now approaching the point where its density
   works against the reader it exists to serve. Not a defect and not in scope, but a future
   costing task may be better served by the design doc than by the row; the row's own opening
   sentence already points there.
