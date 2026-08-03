# Adversarial Quality Re-Review (round 2) — Task 3

**Dispatched:** 2026-08-01 (`reports/.dispatch-log`: `task=3 type=quality-review`, round 2)
**Model:** opus
**Reviewing:** fix commit `7fe3931` (`git diff 0e4b420..7fe3931`, 3 files, +145/−32)
**Verdict:** **CHANGES_REQUESTED** — findings 1–6 all CLOSED; **1 new BLOCKING, 1 IMPORTANT, 3 MINOR**, all introduced or left by the fix round.

---

## Round-1 finding closure

| # | Verdict | Evidence the reviewer ran |
|---|---|---|
| **1** SP3/N80 sweep | **CLOSED** | Ran SP3's printed `find … -print0 \| xargs -0 /usr/bin/grep` **verbatim** → `539691`, `621072`. Ran N80's pipe-free form → identical. Wrapped-`grep` 4-file form → top two `523426/621072`, exactly as the doc now states. `find`=7 / wrapped `grep -rl`=4 / `/usr/bin/grep -rl`=7; the 3 skipped all under `.worktrees/`. `tokens=56[0-9]{4}` → empty; positive control → 479 rows, locates `621072`. **Round 1's BLOCKING 1 was false; the doc's numbers and conclusion were always right.** |
| **2** SP4/N81 wrong gate | **CLOSED**, but the replacement enumeration is incomplete → **BLOCKING A** | Read both constructs. Also corroborated structurally: `validate-plan.py`'s only cross-module task-id check is **collision** (duplicates), not gaps — so "does not police this" holds independent of the fixture. |
| **3** attempts-not-dispatches | **CLOSED — the fix's correction of round 1 is upheld** | Stage-2 comment sits directly above `if [ "$IS_IMPLEMENTER" = true ] && [ "$MARKED_FIX" = false ]` → governs the `type=implementer` write only; the `type=fix` write is at the Stage 0 marked-fix branch under a different comment. Quoting one as evidence for the other **would have been an overclaim**; the doc now describes the split accurately. |
| **4** `archive-` | **CLOSED** | `grep -c 'archive-'` → **2** (comment + `T0_GLOB=`). |
| **5** `0→` count | **CLOSED — the fix's refusal was correct** | Bare `grep -c '0→'` → **5** today, **4** at `0e4b420`; anchored `grep -cE '^\| 0→'` → **4** at both. The 5th hit is a review-round-1 row *quoting* the notation. Shipping the review's literal command would have written a fresh self-invalidating count. |
| **6** `$127` self-invalidation | **CLOSED** | `git grep -e '\$127' 553bbe3 -- '*.md'` → exactly **3**, so the historical claim is accurate; today 23/9 files. Doc discloses and instructs re-running. |

---

## `[BLOCKING] A` — the reserved-slot analysis omits the gate that fires **first and hardest**; N81's "blocks BOTH gates" is a wrong bounded count

**What is wrong.** §Candidate A and the new reserved-slot table name exactly two binding gates — both **terminal** (module close, pre-completion). An **unused interior** reserved slot blocks much earlier: it hard-blocks the **next in-module dispatch**.

**Reviewer measurement** (live hook, scratchpad fixture, `task_range: [4,8]`, slot 6 reserved, tasks 4–5 complete, all of task 7's own artifacts pre-satisfied so 4b/4c were the only variable):

```
UNUSED interior slot 6  -> rc=2
   BLOCKED: No implementer report found for Task 6 …
   BLOCKED: No spec review found for Task 6 …
   BLOCKED: No quality review found for Task 6 …
   BLOCKED: No spec-review dispatch recorded for Task 6 …
   BLOCKED: No quality-review dispatch recorded for Task 6 …
POSITIVE CONTROL: slot 6 used -> rc=0
```

**Controller independently confirmed the structural half:** the N3a skip-guard is `elif [ "$PREV" -lt "$MANIFEST_TASK_START" ]` — with `PREV=6`, `MANIFEST_TASK_START=4` it does **not** arm, so Checks 4b/4c genuinely run against the empty slot. Controller also confirmed N81 currently reads *"blocks BOTH gates"*.

**Placement is load-bearing and the doc never states it.** A **last-in-range** unused slot is caught only by the two terminal gates (the dispatch that would test it is refused by the range guard first); an **interior** one is caught three ways. The fix implementer's own fixture was interior yet measured only the terminal gates.

**Why it matters.**
1. **N81 ships to `main` with a bounded count that is wrong** — a scheduled propagation, not a local error.
2. §Candidate A hands a future task a prescriptive test checklist that **omits the earliest-firing gate**, materially understating cost: the reader expects to discover the problem at module close, but is actually stopped at the next dispatch.
3. It is the same *shape* as round-1 BLOCKING 2 — a gate pointer that does not cover the case — one level up.

**Not wrong:** the conclusion is unchanged and strengthened; every row currently in the table is individually correct (checked against source).

**Fix.** Add a third blocking row (Checks 4b/4c on the *following* task, when an interior slot goes unused); extend §Candidate A's checklist to include a live-hook dispatch of the successor task; state that **placement (interior vs last-in-range) is a design variable**; correct N81's "BOTH gates". Also label the table's rows — 2–4 describe **slot-used**, 5–6 **slot-unused**, unlabeled, which is what makes 4c read as benign.

*Reviewer's own severity note, recorded as offered: a reasonable reviewer could call this IMPORTANT, since following the doc still yields the right decision. BLOCKING was chosen because the wrong element is a quantified claim inside a copy-forward row headed for `main`, and the checklist is prescriptive.*

---

## `[IMPORTANT] B` — SP4 prints "seven `type=fix` rows" beside the command that now returns **8**

**Controller-verified:** live log **8**, committed log **8**, at `0e4b420` **7**. The 8th row is `2026-08-01T01:57:38Z DISPATCH fix task=3 type=fix` — **the fix round's own dispatch**. The doc still says "seven" in **2** places (§Bottom line and §The observed friction item 4).

**Why it matters.** This is exactly finding 6's defect — a printed count on a live append-only artifact, beside the command that refutes it — **reintroduced in the round that fixed finding 6**, whose own self-review claims it *"Applied finding 6's treatment consistently rather than locally."* Failure mode 6 on the brief: reasoning that violates the doc's own thesis at the moment it claims rigor.

**Capped at IMPORTANT because it is not in N81** (controller-verified: `grep -c -i 'seven'` on the N81 row → **0**), so it does not propagate to `main`. Fix: apply the doc's own rule — give the command, drop the number, or add "as of that count".

---

## `[MINOR] C` — "two different keys, both catching the same unused slot" is shape-dependent

Measured against `all_tasks_have_reports`:

```
slot 6 WITH a '### Task 6' header    : {'pass': False, 'missing': [6]}
slot 6 with NO header (manifest-only): {'pass': True,  'missing': []}
negative control (task 5 report gone): {'pass': False, 'missing': [5, 6]}
```

A reserved slot existing only as a widened manifest `task_ids` range with **no `### Task N` section is invisible** to that gate — only `validate_module_completion` catches it. The doc correctly identifies the two keys differ, then asserts both catch; that holds only for the both-keys-populated shape its fixture had. One clause fixes it.

## `[MINOR] D` — "two provenance rows" undercounts; should be **three**

A fully-reviewed task owes `type=spec-review` + `type=quality-review` (Check 4c) **plus** `type=partner-review` (Check 5d). SP4's own new 5d row names the third — *"a real partner review plus a real `type=partner-review` provenance row"* — so **the doc contradicts itself**, in both §Candidate A and N81. (Check 5d's minimum-tier branch avoids the provenance row entirely; not mentioned.)

## `[MINOR] E` — the hook's own `:324` citation has rotted (confirmed; correctly out of scope)

`sdd-pre-dispatch-hook.sh` line 240 reads `# Check 9's window isn't moved — :324)`. The Stage-2 `type=implementer` writes it names are at **297/300**; line 324 today is an `exit 2` in the unrelated range-guard block. Introduced by `7dc7812` (N26). **Controller confirmed independently.** Correctly scoped out — baselined hook, so a fix obliges a same-change `check-hooks.sh --capture`. Worth a BACKLOG row.

---

## What held up

- **Every measurement round 1 disputed.** Reproduced from scratch in all four sweep forms. The controller and fix implementer were right; **round 1 was wrong**.
- **Byte-identity**, with the reviewer's own positive control (mutated block → DIFFER): N80 and N81 both IDENTICAL. Noted: SP3 has 2 fenced blocks, SP4 has 1 — a naive first-fence extractor is wrong on SP3.
- **N80's declared dependency resolves** — the architecture-recommendation doc exists with every section cited; its §7 does say the field inventory is *"documentation-sourced via a research subagent, not verified first-hand"*, exactly as SP3 characterizes it; its §2 confirms `PreToolUse` carries no context data. **SP3's `UserPromptSubmit` handling is genuinely careful** — it refuses to infer the field inventory.
- **Every SP3 factual claim checked:** settings.json keys; `UserPromptSubmit` carries 2 commands; `check-hooks.sh` 7-path `HOOKS=()`; `context-probe.py` imports; `sdd-stop-hook.sh` reads only `.cwd`; `claude-usage-pace` exists, dated 2026-07-02.
- **Every SP4 source-construct claim:** `transition-module.py`'s six `def` names complete; `_merged_dispatch_times` regex + docstring exact; Check 5c's flat `CHECKPOINT_FILE=`; Check 5d reads the dispatch log itself; the N3a guard; the range-guard message.
- **No regressions.** Zero `:NNN` citations; zero `handoff-spawn.log` mentions; N54/N57 untouched; BACKLOG numstat exactly `2/2`; table integrity header/N80/N81 all NF=9. SP4's "grep that phrase" promises resolve **as printed**.
- **The fix's out-of-scope propagation catch was real** — §What could not be established now carries the correction and is consistent with §Candidate A.
- **The reviewer's own paraphrase-inclusive sweep found no *further* propagation site** for findings 2–6. Finding B is a new site, not a missed one.

## What could not be established

- **`validate-plan.py` → `blockers: []` on a reserved-slot plan** — not rebuilt this round. Two independent parties measured it with a negative control and agree; corroborated structurally (only cross-module check is collision, not gaps).
- **Whether a stale `type=implementer` row has ever perturbed a live Check 9 window.** Mechanism proven; incidence unmeasured, and the doc says so.
- **Whether the reserved slot is intended interior or last-in-range.** Now doubly open — it decides both the cost and whether finding A applies. The doc names always-used-vs-unused but not placement.
