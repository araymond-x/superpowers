# Adversarial Code Quality Review — Task 3 (SP3 + SP4 design docs + BACKLOG rows)

**Dispatched:** 2026-08-01 (`reports/.dispatch-log`: `task=3 type=quality-review`)
**Model:** opus
**Reviewing:** commit `0e4b420`
**Verdict:** **CHANGES_REQUESTED** — 2 BLOCKING, 1 IMPORTANT, 3 MINOR.

**This is the SEVENTH consecutive task in this feature where the adversarial quality review found a real defect on a fully-green upstream** (implementer DONE_WITH_CONCERNS with detailed self-verification, spec review PASS, install suite 104/0/0).

---

## Controller adjudication summary

Every finding below was independently re-verified by the controller before being accepted. **One BLOCKING finding was substantially re-scoped because the reviewer inverted its own measurement** — see finding 1. Findings 2–6 are upheld as written.

---

## `[BLOCKING] 1` — SP3's negative-result sweep prints a command that reaches **4 of 7** observation logs. **RE-SCOPED by the controller: the doc's RESULT and NUMBERS are correct; only its stated METHOD under-reaches.**

### The real defect (verified)

`grep` in this environment is **not** `/usr/bin/grep`:

```
$ type grep
grep is a shell function from /Users/araymond/.claude/shell-snapshots/snapshot-zsh-*.sh
    → exec -a ugrep … -G --ignore-files --hidden …
```

`--ignore-files` makes recursive greps honor `.gitignore`, and `.worktrees/` is gitignored. **Controller-measured, three ways:**

| method | `context-observations.log` files reached |
|---|---|
| `find … -name context-observations.log` | **7** |
| `grep -rl 'tokens=' ~/projects/claude-custom/` (the doc's instrument) | **4** |
| `/usr/bin/grep -rl 'tokens=' …` | **7** |

The three skipped files are all under `.worktrees/` — i.e. **exactly where this repo executes SDD work**. And `539691` lives *only* in this feature's own worktree log, one of the three the printed command cannot see.

### Where the reviewer was wrong — and why it changes the fix

The reviewer wrote: *"Re-running the full 7-file sweep, the second-largest is `523426`, not `539691`."* **That is backwards.** Controller measurement:

```
4-file sweep (doc's printed command):  … 513612  523426  621072
7-file sweep (corrected):              … 523426  539691  621072
```

`523426` is the **truncated** sweep's answer. The **corrected** sweep's top two are `539691` and `621072` — **precisely what SP3 states.** The reviewer's further claim that `539691` was "stitched in from SP1's doc as though the sweep produced it" is also unsupported: it is a genuine hook-written observation row in this feature's own `context-observations.log`. SP1 discusses the same event; that is one number in two places, not a laundered citation.

**Consequence for the fix:** do **not** change the numbers and do **not** re-attribute `539691`. The defect is that the printed command is **not reproducible as written** — a reader who runs it gets `523426/621072` and concludes the doc is wrong.

### Why it still matters (the transferable part)

**Independence of reviewer is not independence of instrument.** The spec review re-ran this sweep and reported *"Exact match … It holds up"* — two agents in the same shell calling the same wrapped `grep` reproduce the same truncation indefinitely. That is corroboration, not verification.

**The conclusion survives.** Controller ran the full 7-file sweep: **no `tokens=56xxxx` row exists anywhere** (positive control: same pipeline returns 477 matches overall and locates `621072`). "No primary artifact for 569k" stands.

### Fix

- Replace the printed command with one that reaches all 7: `find … -print0 | xargs -0 /usr/bin/grep -hoE 'tokens=[0-9]{6,}'`.
- State that the wrapped `grep` reaches 4 of 7 and why (`--ignore-files` + gitignored `.worktrees/`) — this is a repo-wide gotcha worth recording.
- **Keep `539691` / `621072` and keep the conclusion.**
- Add one sentence of coverage honesty: SP3 itself establishes that a non-SDD session exits before any observation row is written, so a null result in these logs is **largely predetermined** for the very session class the figure describes. The null is weak coverage, not strong.
- Mirror the method correction into **N80**.

---

## `[BLOCKING] 2` — SP4's "costed alternative" points the future reader at the wrong gate. In the **N81 copy-forward row**. *(Upheld as written.)*

N81 says: *"**Costed alternative:** reserve a carry-forward task id inside every module's declared range at plan time — the range check then passes with no hook change; **verify it survives `validate-plan.py` first**."* §Candidate A adds *"the reserved id carries the normal gate stack. This keeps enforcement intact."*

**Measured — the named gate does not bite.** A plan with a reserved slot: `validate-plan.py` → `blockers: []`, `status: WARNING`. Negative control (`enforcement_tier: bogus`) → 2 blockers. The validator *can* block; it does not block this.

**Measured — two unnamed gates do.** Controller independently confirmed both constructs:
- `transition-module.py:validate_module_completion` — `for task_id in module.task_ids:` then `errors.append(f"Task {task_id}: missing or empty implementer report")`. An **unused** reserved slot hard-blocks the module transition.
- `controller-checkpoint.py:all_tasks_have_reports` — a pre-completion check whose failure sets `checks["all_tasks_have_reports"]`; reviewer measured `{'pass': False, 'missing': [5]}` with a positive control (`{'pass': True}` once a task-005 report exists).

**The other reading is not free either.** If the slot is *always used*, every module owes an extra implementer report, spec review, quality review, partner review, checkpoint file and two provenance rows — which contradicts "cheapest variant" **as a cost claim**.

Supporting: SP4's enforcement-interaction table analyses only the **out-of-range** form (every row qualified "Not reached in case A") and never analyses the variant the doc tells the reader to cost first.

**Why it matters.** A reader runs `validate-plan.py`, sees PASS, builds the lane, and hits a hard transition block the first time a module doesn't need its slot. This is the exact failure mode behind this repo's two false-premise BACKLOG rows.

**Fix.** In §Candidate A and N81, replace `validate-plan.py` with the binding gates (`validate_module_completion`, `all_tasks_have_reports`); state that an unused slot blocks both and an always-used slot carries a full per-module review cost, so "cheapest variant" needs re-costing.

---

## `[IMPORTANT] 3` — "Attempts, not dispatches" is under-scoped, and its "benign" verdict does not carry to the sibling class SP4's own control produced.

SP4 frames the pre-gate log write as a `type=fix` property, *"benign today (see Check 9 below)"*.

**Reviewer rebuilt an independent fixture** (`task_range: [4,8]`, never the live repo). All three of SP4's cases reproduce — **but it also read the log after each, which SP4 did not:**

| case | rc | stderr | log row left behind |
|---|---|---|---|
| A `[task 2 fix]` | 2 | range message only | `DISPATCH fix task=2 type=fix` |
| B `[task 5 fix]` (control) | 2 | full check stack | `DISPATCH fix task=5 type=fix` |
| C `Implement task 2` | 2 | range message only | **`DISPATCH implementer task=2 type=implementer`** |

Case C leaves a **`type=implementer`** row for a dispatch that never happened — and `_merged_dispatch_times` compiles exactly `r"…DISPATCH\s+implementer\s+task=(\d+)\s+type=implementer"`, so a stale row **can open or shift a Check 9 verification window**. The behavior is deliberate: the hook's Stage-2 comment reads *"Written here in Stage 2 — BEFORE the enforcement gate below — so the timestamp is recorded even when the dispatch is ultimately blocked."*

**Fix.** Generalize: the log records dispatch *attempts* for **both** classes, by design (quote the Stage-2 comment); note the `type=implementer` case is Check-9-visible and therefore **not** benign in the same sense. Adjust N81's one-line version.

---

## `[MINOR] 4` — `grep -n 'archive-'` over the hook returns **2** hits, not "a single hit"

Two hits: a comment line and the `T0_GLOB=` code line. The conclusion (one archive-aware lookup in the hook) is correct. Not in N81. Fix: say "two hits, one comment and one glob", or narrow the command.

## `[MINOR] 5` — "Three rows carry a two-number Task column" — there are **four**

`git show 0e4b420:…/deviations.md | grep -c '0→'` → **4** (three `0→9`, one `0→17`). Fix: give the command rather than the number — the `CLAUDE.md` convention this repo states directly.

## `[MINOR] 6` — SP3's "`grep … -e '\$127'` returns exactly three hits" is self-invalidating

It now returns 15 across 7 files, six of them inside SP3 itself. One clause — "three at the time of writing, before this doc existed" — closes it.

---

## What the review verified that held up

- **SP4's centerpiece measurement, reproduced independently** in a fresh fixture: cases A/B/C reproduce exactly, including the ordering claim — A and C emit *only* the range message while B accumulates the full `ERRORS+=` stack, proving the range guard exits before Checks 4b/4c/5c/5d.
- **SP4's contradiction of the plan on Check 9 is correct — verified a third time.** `_check_verification_git_reality` opens `if not verification_ids: return []`; `_merged_dispatch_times` parses only `type=implementer`. The plan's framing was wrong; SP4 was right to refuse it.
- **`transition-module.py`**: `shutil.move` into `archive-<module>/`, `shutil.copy2` + `open(dispatch_log,"w").close()`, `task_range` rewrite; the six `def` names the doc lists are complete — no inverse operation.
- **SP3's manifest-gating claim** — early exit precedes dispatch classification, the context gate, and any `OBS_LOG` assignment.
- **Context gate scope** — banner and nested `IS_IMPLEMENTER`/`MARKED_FIX` structure quoted verbatim, matching source.
- **`check-hooks.sh`** pins a hardcoded 7-path `HOOKS=()` array.
- **`settings.json` keys** `PreToolUse SessionStart Stop UserPromptSubmit`; `UserPromptSubmit` carries two unrelated commands.
- **Seven `type=fix` rows** in this feature's dispatch log. Exact.
- **The `UserPromptSubmit`/`transcript_path` handling is genuinely careful** — SP3 declines to infer the field inventory from a documentation-sourced table and routes it to the spike. **This is where "inference from absence" was most available, and the doc refused it.**
- **`$127`/569k is disclosed honestly and is never load-bearing** — no threshold, sizing or urgency claim rests on it.
- **Byte-identity**, with a negative control on the reviewer's own extractor (mutated copy → `differ`): N80 4021 bytes, N81 2717 bytes. Not re-litigated.
- **Table integrity** (checked by nobody else): `awk -F'|'` → header NF=9, N80 NF=9, N81 NF=9 — both render at the header's 7 columns. N79's NF=13 is 4 escaped `\|`, pre-existing.
- **No line-number citations** in either doc; **no `handoff-spawn.log` / `context-observations.log` conflation.**
- **The in-repo `$127` sweep is instrument-independent** — wrapped and `/usr/bin/grep` agree. Only the cross-repo observation-log sweep was truncated.

## What the review could not establish

- Whether `539691` was intended as a sweep result or imported from SP1. **Controller resolved this**: it is a genuine hook-written row in this feature's own log. The reviewer's "laundered citation" reading is rejected.
- Whether the reserved-slot variant was meant as always-used or may-be-unused. The wrong-gate pointer stands under either reading; which correction to write depends on intent.
- Whether a stale `type=implementer` row has ever perturbed a **real** Check 9 run. Mechanism proven in a fixture; no live instance searched.
- Whether the `$127`/569k record exists outside `~/projects/claude-custom/`. A sweep of `~/.claude/projects/*/` transcripts would be the next place to look.

*No repo file modified by the reviewer; fixtures built in the session scratchpad.*
