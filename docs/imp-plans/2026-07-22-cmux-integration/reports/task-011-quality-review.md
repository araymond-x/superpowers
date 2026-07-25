# Task 11 — Code Quality Review

**Status: PASS** (no Critical, no Important; 3 Minor — **Finding 1 is a real defect introduced by this task**)

> Reviewer model: opus. Spec compliance was already verified separately; this review judged whether the change is the
> right one, well made, and still true in six months.

## Q1 — Proportionality / durability: right size and altitude; two clauses should move

Adjudicated bullet by bullet against "durable, routing-oriented, points at the authority."

**Belongs, unambiguously (7 of 9):** the interface/pointer bullet; **"Run it FROM the target worktree"** (silent wrong-repo targeting, not discoverable from the script you are reading); the **notify asymmetry** with "do not 'fix' them into consistency" (a future agent *will* read `:125` vs `:464` as an inconsistency — the rationale is not derivable from the code, which is the definition of CLAUDE.md content); **not-a-hook / no baseline entry** (a negative fact preventing wasted work under the 7-baselined-hooks rule); the **bash 3.2 / `set -u` / `FORWARDED`** trap (the script's own header at `:6-7` points *here*, so this completes an existing pointer); **cross-repo split** (routing across three repos is literally routing); **append-prompt accumulation, no reaper** (unbounded growth with no owner).

**Two clauses are reference material, not routing:**
1. **Bullet 3's six-site line enumeration.** The durable content is the *shape* — 0/3/1, "0 has two causes", and the picker-manual caveat. The six `:NNN` coordinates are re-derivable with one `grep -n 'exit 3'` and they rot (Q2).
2. **Bullet 5's field grammar.** A transcription of the script's own `printf` — a second source of truth.

~100 of 632 words. Explicitly **not** a call for a wholesale trim: this file's established altitude is dense (the N43 bullet is ~300 words alone; the context-gate env bullet ~280), the new section's footprint is *smaller* than N43's, and holding it to a standard the file has never met would delete the checkable precision that is the point. Separate note: CLAUDE.md went 7107 → 7969 words (+12%) with this task. **The file is the proportionality problem; this section isn't.**

## Q2 — Line-number citations: trade correct for 5 of 11, incorrect for 6

The `sdd-skill-enforcement-hook.sh:76` precedent is **not comparable** — one cite attached to a *quoted regex*, so if the line moves the reader still has the pattern to grep. Same for the `FORWARDED` trio here (constructs named alongside their cites): construct-anchored, self-healing. Those are fine.

The six exit-3 sites are bare coordinates. The positive control below shows a **one-line** insertion silently repoints `:125` from `exit 3` to `print_manual_instructions` — a plausible-looking line in the same branch. Mitigating: each cite is accompanied by a cause name, so a rotted cite is recoverable from the prose. That defuses it from Important to **Minor**.

## Q3 — Test counts: correct call, and Task 11 did NOT entrench the anti-pattern

`grep -c '625' CLAUDE.md` → **0**. CLAUDE.md carries no unit/regression/install counts. The only number Task 11 added there is the e2e **step index** (Step 14, banner 15) — a structural reference, not a pass count. Commit `da7e367` *removed* stale-count surface by killing the historical `13→14`.

The volatile counts went into the **manifest header** — a maintained project doc, exactly where the global rule puts them. **Right call.** The adjacent defect **predates Task 11** — see Finding 2.

## Q4 — `N43(D)` format: good convention, keep it

Confirmed nothing parses BACKLOG (`grep -rln 'BACKLOG' tests/ hooks/ skills/*/scripts/ skills/scripts/` → zero hits). The ID is a pointer into a namespace **N43's own row already defines** (A/B/C/D), not a new namespace — inventing `N52` would sever that. Residual risk is precedent creep (`N45(a)`, `C2(b)`), but this is the only lettered parent in the ledger and the alternative violated the 0-deletions constraint. **Accept.**

## Q5 — Stale heading: set it to `(16 active)`; the implementer's Concern 1 is wrong

"active" has **never** meant total rows — it means the count of `subagent-driven-development/scripts/` rows. Three independent historical snapshots plus the pre-task state:

```
14e1070  heading (11 active)  total rows 13  SDD rows 11   ✓
e9db8a2  heading (14 active)  total rows 16  SDD rows 14   ✓
768656a  heading (15 active)  total rows 17  SDD rows 15   ✓
78dcd25  heading (15 active)  total rows 17  SDD rows 15   ✓  ← immediately before Task 11
HEAD     heading (15 active)  total rows 18  SDD rows 16   ✗
```

It does **not** mean "non-hook": non-hook rows were 13 and 14 when the heading read 14 and 15.

**So the heading was exactly correct before Task 11, and this task introduced the drift by 1** (it added `spawn-handoff-session.sh`, an SDD script). Nothing pre-existing. **Controller independently reproduced this at `768656a` / `78dcd25` / `HEAD` before accepting it.**

## Q6 — Other risks

- Manifest "authoritative counts" misdirection (Finding 2).
- **Inconsistent delegation in the manifest's `spawn-handoff-session.sh` row:** it *delegates* the bash/`set -u` fact (`see CLAUDE.md "cmux Auto-Spawn Handoff"`) but *duplicates* the full exit ladder and all four env-var defaults. The author knew the pattern and applied it unevenly — two places to edit when the ladder changes (Finding 3).
- **Process note (controller error, since fixed):** `task-011-spec-review.md` did not exist on disk at review time, so zero-overlap with the spec review could not be guaranteed. The controller had failed to persist it; written before the fix round.
- **Not findings:** N43's row still calling (D) deferred is handled by the new row's supersession sentence; `done-pending-merge` matches N43's own convention; the manifest header's `2026-07-25, post-cmux-integration` framing pre-merge matches prior features.

## Positive control

Inserted one comment line at index 10 of `spawn-handoff-session.sh`, then re-checked the cites: `:125` went from `  exit 3` to `  print_manual_instructions`; `:484` from `  exit 0` to the `spawned successor…` echo; `sed -n '125p' | grep -c 'exit 3'` → `0`. Restored with `git checkout -- <file>`; `:125` is `  exit 3` again and `git diff --name-only` no longer lists the script. **No `git stash` used** — controller re-verified the restore independently (`git diff --name-only 78dcd25..HEAD` shows the script untouched).

Second control: the heading-convention hypothesis made falsifiable predictions at three historical commits, hit **3/3**, then correctly flagged HEAD as the one mismatch.

## Findings

1. **Minor — `## Deterministic Scripts (15 active)` drift was INTRODUCED by this task, not inherited.** Evidence: the heading tracked SDD-script rows exactly at 4 prior snapshots including `78dcd25` (15/15); HEAD has 16. *Fix:* set the heading to `(16 active)`; correct implementer Concern 1 in the record — it measured total rows against a heading that never counted them. → **ACCEPTED, fixed in the `[task 11 fix]` round.**
2. **Minor — false pointer in the manifest header.** `"The authoritative running counts are maintained in `CLAUDE.md` Testing"` — CLAUDE.md Testing contains no unit/regression/install counts (`grep -c '625' CLAUDE.md` → 0). Pre-existing at `78dcd25`; Task 11 made it maximally misleading by refreshing the numbers directly above it. *Fix:* invert the pointer. → **ACCEPTED, fixed in the `[task 11 fix]` round.**
3. **Minor — six bare `:NNN` cites + a transcribed log grammar are the rot surface**, and the manifest row duplicates the exit ladder it elsewhere delegates. *Fix:* drop the six exit-site line numbers (keep cause names, anchor the cmux one on `cmux ping` ≠ `PONG`); compress bullet 5; make the manifest row point at CLAUDE.md for the ladder.
   → **PARTIALLY ACCEPTED.** The six bare exit-site cites and the manifest's ladder duplication are fixed. **The bullet-5 field grammar is retained — controller decision, with evidence the reviewer did not check:** CLAUDE.md *already* documents `context-observations.log`'s field grammar inline (`format: <ISO-8601> task=<N> type=<...> tokens=<T> source=<probe|byte-proxy|bypass> tier=<below|soft|hard> action=<allow|nudge|block|fallback>`). Documenting a sibling log's grammar inline is therefore established house style, not a novel second source of truth — **and the "do not conflate these two logs" warning is only actionable if a reader can see how the formats differ.** Removing one of the two grammars would weaken the exact warning the bullet exists to give.

**No Critical or Important findings.** The notify-asymmetry, `set -u`/3.2, cwd, and not-a-hook bullets are the strongest content in the section and were not touched by the fix round.
