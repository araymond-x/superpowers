# Adversarial Quality Re-Review (round 3) — Task 3

**Reviewing:** fix commit `00f54bb` (`git diff 7fe3931..00f54bb`), SP4 + N81, +118/−44
**Model:** opus
**Verdict:** **CHANGES_REQUESTED** — **A, B, C, D all CLOSED**; **2 new IMPORTANT, 0 BLOCKING**. Both are one-clause text corrections inside SP4 and its N81 fence.

Every number in this review was measured this round; the reviewer inherited none, including from the dispatch brief. All recursive sweeps used `/usr/bin/grep` or `find … -print0 | xargs -0`.

---

## Closure table

| # | Verdict | Evidence run |
|---|---|---|
| **A** — omitted Checks 4b/4c; N81's "blocks BOTH gates" | **CLOSED** | Own isolated fixture (`git init` in scratchpad, never the live repo), `task_range [4,8]`, slot 6 reserved, task 7's artifacts pre-satisfied. **Positive control FIRST: slot 6 used → `rc=0`**; then deleted only slot 6's three reports + its two `task=6` provenance rows → **`rc=2` with exactly the five BLOCKED strings**. Third independent reproduction. Table now carries the third row with an `applies when` column; §Candidate A's checklist requires "a **live-hook dispatch of the successor task**"; placement named as an open axis in three places. **"BOTH gates" residue: zero** — controller re-verified. Last-in-range also reproduced: task 9 against `[4,8]` returns only the range-guard message. |
| **B** — "seven `type=fix` rows" | **CLOSED** | `grep -ci 'seven'` over SP4 → **0**; over the N81 row → **0** (controller re-verified: 0). Replacement gives the command plus a revision-anchored figure, whose anchor checks out: `git show 0e4b420:….dispatch-log \| grep -c 'type=fix'` → **7**. The printed command run as printed → **9** live (8 at `00f54bb`, 7 at `0e4b420`). The doc's own prose — "every fix round appends to it — including the rounds that edited this very sentence" — is demonstrably true across 7→8→9. |
| **C** — shape-dependence of `all_tasks_have_reports` | **CLOSED (text)** — but the promotion's reasoning does not fully hold → **IMPORTANT 1** | Reproduced with a negative control: manifest-only → `{'pass': True, 'missing': []}`; headered → `{'pass': False, 'missing': [6]}`; negative control (task 5 report also gone) → `{'pass': False, 'missing': [5, 6]}`. Keying asymmetry source-confirmed: `TASK_HEADER_PATTERN = re.compile(r"^###\s+Task\s+(\d+)")` over `_unfenced_content` vs `for task_id in module.task_ids:`. |
| **D** — "two provenance rows" → three | **CLOSED** | Both sites corrected. Source-confirmed at Check 5d's `PARTNER_FILE=` and its `grep -q "task=$TASK_NUMBER type=partner-review"`. The disambiguating clause is **correct**: the positive control restored exactly **two** `task=6` rows and reached `rc=0`. Minimum-tier zero-row branch confirmed at `PARTNER_FILE_MIN`. |

---

## `[IMPORTANT] 1` — the two new axes contradict each other at the manifest-only-interior cell, and N81 carries the wrong side

The full cross-product:

| placement | plan shape | gates catching an unused slot |
|---|---|---|
| interior | headered | 4b/4c + `validate_module_completion` + `all_tasks_have_reports` = **3** |
| **interior** | **manifest-only** | **4b/4c + `validate_module_completion` = 2** |
| last-in-range | headered | 2 (both terminal) |
| last-in-range | manifest-only | 1 |

**The contested cell was measured** (same fixture, slot 6 unused *and* its `### Task 6` header removed; headers verified present for 4, 5, 7, 8):

```
manifest-only + INTERIOR, dispatch task 7  -> rc=2, 5 BLOCKED lines
all_tasks_have_reports (manifest-only)     -> {'pass': True, 'missing': []}
```

So a manifest-only interior slot is caught **two** ways, and the earliest catcher is the hook, not either terminal gate.

Against that, **controller-verified site-by-site**:
- SP4 §Placement bullet — "caught **three** ways", unconditioned.
- SP4 §What could not be established, placement bullet — same, unconditioned.
- **N81** — "an INTERIOR unused slot is caught **all three ways**", unconditioned. **False for the manifest-only shape.**
- SP4 §What could not be established, plan-shape bullet — "caught by `validate_module_completion` **alone**" — **false for interior placement**; not rescuable by a charitable reading, since it names both gates and then says "alone".

Exactly **one** site states it correctly — §Cost fork: *"all three for an interior slot **carrying a `### Task N` section**, down to `validate_module_completion` alone for a manifest-only **last-in-range** slot."*

**Why it matters.** N81 ships to `main` containing two mutually exclusive sentences; a manifest-only interior slot satisfies neither. N81's own "blocked by **one to three** gates depending on those two axes" implicitly concedes the range, making the contradiction internal to one paragraph. **Third consecutive round in which a bounded gate enumeration inside N81 was wrong.**

Fix round 2's own Deviation #2 identified this exact cell, wrote it into its report, applied the conditioning to §Cost fork — **and did not carry it to the two placement bullets or to N81.** Failure mode 4 (a propagation sweep that under-counts), again.

**Reviewer's calibration, recorded as offered:** round 2's BLOCKING was an *omission* (reader under-tests, finds out late); this is an *over-attribution* for one cell (reader over-tests). The prescriptive checklist is complete and unaffected, the "never a no-op" conclusion holds, and the recommendation is unchanged — hence IMPORTANT, though a reasonable reviewer could call it BLOCKING for being a self-contradiction in a propagating artifact.

**Fix.** Condition the three "interior → three ways" sites as §Cost fork already does; qualify the plan-shape bullet's "alone" with *last-in-range*. Four one-clause edits; regenerate N81 from the fence so byte-identity survives.

---

## `[IMPORTANT] 2` — the flat-lookup enumeration omits Check 4's N-1 globs, which fire first; Candidate A's must-skip list inherits the gap

SP4's section is titled **"Two flat lookups a re-opened task would trip"** and names Checks 5c and 5d; N81 mirrors it; Candidate A's sketch says the new class must "skip the flat **Check 5c/5d** lookups".

There is a third, and it fires first: **Check 4's N-1 report globs.** `task_report_glob` builds `"${REPORTS_DIR}/task-${padded}-${report_type}*"` with **no `archive-*` term** — corroborated by the doc's own instrument (`grep -c 'archive-'` over the hook → **2**, both belonging to Check 5's `T0_GLOB`). For a task whose predecessor was archived, all three of Check 4's lookups miss.

The doc then makes this actively misleading: *"Check 4c is the exception that already handles the boundary: it skips when `PREV < MANIFEST_TASK_START`."* True of 4c — but its sibling sub-block inside Check 4 skips on a **different** condition, `TASK_NUMBER -eq MANIFEST_TASK_START`, which does not cover an arbitrary below-range id.

**Measured, not reasoned.** Candidate A's premise is admitting ids below `MANIFEST_TASK_START`, so the reviewer simulated exactly that: copied the hook to scratch, deleted **only** the seven-line range-guard block (`diff` confirms; `bash -n` clean), with a completed module archived into `archive-module-1/`:

```
X  dispatch task 2 (archived module), range [4,8]     -> rc=2
     BLOCKED: No implementer report found for Task 1 …
     BLOCKED: No spec review found for Task 1 …
     BLOCKED: No quality review found for Task 1 …
     (Check 4c: SILENT)
Y  POSITIVE CONTROL — task 1's reports copied live,
   with ZERO `task=1` provenance rows                 -> rc=0
Z  POSITIVE CONTROL that 4c CAN fire in this hook copy —
   task 5 (PREV=4 >= START=4), task=4 rows removed    -> rc=2 "No spec-review dispatch recorded for Task 4"
```

**Y is decisive:** `rc=0` with no `task=1` provenance proves Check 4c genuinely skips; **Z** proves it was not skipping for an unrelated reason. Under Candidate A the two guards **diverge** — Check 4 blocks on archived files while Check 4c waves the same task through.

**Why it matters.** A future task following the must-skip list skips 5c/5d and is stopped by a gate the doc called boundary-aware. Same shape as round-1 BLOCKING 2 and round-2 BLOCKING A, one level down, and it is in the copy-forward row. SP4's hedge ("case A shows a dispatch does not get that far") protects the *descriptive* section but not the *prescriptive* sketch, since Candidate A is precisely the world where it does.

**Fix.** Re-title/re-count to three flat lookups; add Check 4's N-1 sub-block to Candidate A's must-skip list and to N81's "Also flat" enumeration; qualify the "Check 4c is the exception" sentence with its sibling's `-eq` keying.

---

## Fix round 2's six Concerns — assessed

| Concern | Verdict |
|---|---|
| **1(a)** round 2 recorded `type=fix` as 8; now 9 | **Correct, not a finding.** Drift on a live artifact is the finding's own thesis; the review is immutable and self-disclosing. |
| **1(b)** round 2's `missing: [6]` not reproducible from its text | **Correct, and it bit the reviewer** — task 7/8 reports had to be added before slot 6 was the only variable. Not a defect in the deliverable; SP4 does not print that figure. |
| **2** MINOR E (`— :324`) survived | **Confirmed rotted, correctly out of scope.** *Aside:* round 2's own text said "line 324 today is an `exit 2`" — it is `fi` (the `exit 2` is at 322). A tidy demonstration of why this repo bans `:NNN`. Route to BACKLOG. |
| **3** `--ignore-files` gotcha belongs in `CLAUDE.md` | **Real, outside the three-file scope.** Divergence reproduced exactly: `find` → 7, `/usr/bin/grep -rl` → 7, wrapped → **4**; the truncated form reports `523426/621072` versus the true `539691/621072`. BACKLOG-worthy repo hygiene. |
| **4** Check 4's `-eq` skip vs Check 4c's `-lt` skip | **Real substance attached to the wrong scenario — and it is the same substance as IMPORTANT 2, so do not file it twice.** A *reserved slot* cannot separate them: the range guard runs first, so every dispatch reaching Check 4 has `TASK_NUMBER >= START`, where `-eq START` ⟺ `PREV -lt START`. They are equivalent over the reachable domain. Candidate A's **out-of-range** admission is what separates them. |
| **5, 6** dirty logs; fixture retained | **Procedurally correct.** |

---

## What held up

- **Finding A's core measurement, reproduced from scratch by a third party**, passing-first with a positive control; structural half confirmed at source (`elif [ "$PREV" -lt "$MANIFEST_TASK_START" ]` does not arm at `PREV=6, START=4`; the `-eq` skip does not arm at `7 ≠ 4`).
- **Last-in-range and plan-shape**, both reproduced with controls, matching two prior independent measurements.
- **Byte-identity, positive-controlled first** — mutated `N80` → DIFFER (+7 bytes, matching the mutation exactly); live → **N80 IDENTICAL, N81 IDENTICAL**. The reviewer's byte counts (4873/6200) differ by 1 from the fix report's (4872/6199): a trailing-newline convention. Content identical; **no genuine divergence.**
- **No regressions.** Zero `:NNN` citations; zero `handoff-spawn.log` mentions (no conflation); BACKLOG table integrity header/N80/N81 all **NF=9**; N54/N57 untouched; SP4's 4-column table **NF=6 on every row**.
- **Every printed command runs as printed.** SP3's sweep → exactly `539691`/`621072`; `tokens=56[0-9]{4}` negative control empty; unrestricted positive control → 482 rows, locates `621072`. SP4's two "grep that phrase" promises → 1 / 1. SP4's anchored `grep -cE '^\| 0→'` → **4** as printed, while bare `grep -c '0→'` → **6** — grown from 5 since round 2, **vindicating the anchoring**.
- **Every source construct named:** `transition-module.py`'s six `def` names; `for task_id in module.task_ids:`; `find_report_file`'s archive-aware glob pair; `TASK_HEADER_PATTERN`; Check 5c's flat `CHECKPOINT_FILE=`; Check 5d's `PARTNER_FILE=` + `PARTNER_FILE_MIN`; `T0_GLOB` as the hook's sole archive-aware lookup.

**What the reviewer attacked that held.** It expected the label **"Checks 4b/4c"** to be wrong — the three file-existence errors come from Check 4's un-lettered N-1 sub-block, while `# Check 4b` is the `validate-report.py` structural check nested under `[ "$RESULT" = "OK" ]` and cannot fire when the report is missing. **Not a finding:** `CLAUDE.md` uses the identical shorthand, and both SP4's prose and N81 enumerate the five literal error strings, so the reference resolves.

## What could not be established

- **`validate-plan.py` → `blockers: []` on a reserved-slot plan** — not rebuilt this round; two independent measurements with a negative control agree, corroborated structurally.
- **Whether a stale `type=implementer` row has perturbed a live Check 9 window** — mechanism proven, incidence unmeasured; the doc says so.
- **Whether the reserved slot is intended always-used / interior-vs-last / headered-vs-manifest-only** — all correctly left open. Note IMPORTANT 1 means one of the four cells is currently mispriced in N81, so the axes cannot be priced from the row as written.
