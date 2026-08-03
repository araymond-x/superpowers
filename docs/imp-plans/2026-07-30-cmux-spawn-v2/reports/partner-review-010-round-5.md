# Partner review — Task 10 dispatch, ROUND 5 (final readiness check)

**Scope:** `git show 5b27f89`; current `module-3-spawn-script.md` (Task 10 + Module 3 AC), `task-010-dispatch-prompt.md`, `deviations.md`, `reports/partner-review-010-round-4.md`. Frozen fixture `tests/unit/fixtures/spawn-handoff/cmux-verb-shapes.json` treated as read-only truth. No repository file modified.

---

## 1. Did the structural fix work?

**Yes, and it is measured, not read.**

Sweep of the dispatch for every anchor string, fixture key, fixture filename, provenance label, count, and `deviations.md:<line>` citation (`/usr/bin/grep -nEi 'shift\+tab|esc to interrupt|claude code|quick safety check|trust this folder|rc_confirmation|trust_dialog_screen|read_screen_cold|candidate_anchors|777|143|banner\.txt|trust-dialog\.txt|noise\.txt|picker-error\.txt|both-anchors|deviations\.md:[0-9]+|MEASURED|INFERRED|INVENTED'`): **three hits, all narrative uses of the words "invented"/"measured", zero factual duplications.** Positive control: `grep -c -i anchor` on the same file returns 6, so the instrument reads the file.

The one residual factual restatement is *"two live running-session captures"* (line 40, historical narrative) — true (`rc_confirmation_screen.rc_screen` + `.rename_screen`), and against a frozen read-only fixture. Not a live drift surface.

**Pointer accuracy — every step reference in the obligations list resolved against the plan:**

| Dispatch gloss | Plan target | Resolves? |
|---|---|---|
| 1. Step 2 wait-timeout import assertion, VERIFY not re-add | Step 2's "VERIFY — DO NOT RE-ADD" block | ✅ and TRUE live: assertion at `test_spawn_handoff_v2.py:1265-1274`, script side `spawn-handoff-session.sh:54` column-0 |
| 2. Step 4(a) FULL unit suite, re-measure | 4(a), incl. "do not inherit a count" | ✅ |
| 3. Step 4(b) trust-preflight DECISION, one forbidden way of declining | 4(b), `$WORKTREE_ROOT`-is-trusted decline explicitly forbidden | ✅ |
| 4. Step 4(c) five inline log-readers, different shape | 4(c), count verified at 5, raise-vs-`""` | ✅ |
| 5. Step 3b checkbox, per-anchor provenance rubric | Step 3b, MEASURED/INFERRED/INVENTED per anchor | ✅ |
| 6. **Step 4(d)** orphaned register row naming Tasks 10/13 | 4(d) = `deviations.md:165` routing; 4(e) = Commit | ✅ — **round 4's LOW I is fixed** (old said 4(e) = Commit) |
| 7. Two vacuity traps in Step 2's fence | `test_timeout_rewaits_once_same_duration` (`_flag`), `test_diagnosis_unreadable_on_cold_surface` (two disjuncts) | ✅ |

Header claims also check out: Step 4 does have five lettered parts (a)–(e); 13 `AMENDED 2026-08-02` notes sit in the Task 10 range; Module 3 AC is at the file's end (`:812`, file is 821 lines); the module header does carry Contract Constraints, File Map and Write-Scope Partitioning.

**Sole-source risk the rewrite creates — checked.** The dispatch deliberately stopped repeating `deviations.md:18` and `:165`, so the plan is now the *only* carrier of the three register coordinates Task 10 must act on — and round 4's own commit appended a row to that file. Read raw (`sed -n '18p;165p;271p'`), all three still resolve to the described rows: **`:18`** = trust-preflight ContractDiscovery, still `Pending — Module 3 decision`; **`:165`** = orphaned fallback workspace, still `Open — surfaced for Task 10/13`; **`:271`** = five inline log-readers, still `Pending — TASK 10`. (Round 4's edit was a pure append at `@@ -281,3 +281,4 @@`, which is why nothing shifted.)

**Two dispatch-only factual claims (not in the plan) verified live:** `[ $rc -eq 0 ] || return 1` occurs **exactly 3 times** (`:630`, `:639`, `:654`; control: 21 `return 1` total); the import assertion is landed as described.

---

## 2. Round 4's findings

| Finding | Verdict |
|---|---|
| **BLOCKER N** — fence comment asserted "the banner regex MATCHES the real trust screen" | **CLOSED.** Re-derived from the fixture with controls in both directions: fixed pattern `shift\+tab to cycle\|esc to interrupt` → **0** on `trust_dialog_screen.screen`, **1** on each of `rc_screen`/`rename_screen`; deleted anchor `claude code` → **2** on trust, **0** on both live sessions; control pattern `quick safety check\|yes, i trust this folder` → 2 on trust, 0 elsewhere (instrument works). The rewritten fence comment says exactly this — ordering retained as defense-in-depth, pinned by a **synthetic** both-anchors fixture, not by any capture. **True as written.** |
| **MEDIUM O** — missing fifth synthetic fixture + stale "two" inventory line | **CLOSED.** Step 1 `:563` now produces three synthetics including **`both-anchors.txt`**, with its rationale. Sweep for `remaining (two\|three)` / `are synthetic` / `both-anchors` returns only the corrected line plus the fence reference at `:679`; control: 4 occurrences of "synthetic" in the file. No line still says "two". |
| **MEDIUM R** — no durable register row for rounds 3–4 | **CLOSED.** One row appended to `deviations.md`, carrying the root cause, N and O, and the standing rule. |
| **MEDIUM G** (carried) — dispatch re-opened the `internal_error` knob the plan closes | **CLOSED by removal.** The "SAY SO rather than" exit is gone; obligation 7 now points at the fence, which says write BOTH cases. |
| **LOW H** (carried) — `_argv`/`_flag` misattribution | **CLOSED by removal.** Gloss is now "one about which helper resolves which invocation". |
| **LOW I** (carried) — obligation 6 cited Step 4(e) | **CLOSED.** Now 4(d); verified against the plan. |
| **LOW P** — `banner.txt` "likewise derives" asymmetry | **CLOSED by removal** of the whole passage. |
| **LOW Q** — `:617-623` "Drive both verbatim from the fixture" ambiguity | **NOT CLOSED**, as round 4 anticipated. Round 4 itself downgraded it to harmless once `test_banner_fixture_matches_the_frozen_capture` pinned both readings together. Nit only. |

---

## 3. Removals from the rewrite (old dispatch → new)

Derived from `git diff --word-diff=porcelain 5b27f89^:… → …`, full removal list read, not sampled.

| Removed | Covered by plan? |
|---|---|
| `(line 547ff)` plan line reference | **N/A** — replaced by a step enumeration; line refs rot. Improvement. |
| Verbatim Contract Constraints block | **Y** — module header; dispatch points and repeats the STOP/BLOCKED rule |
| Explicit six-path WRITABLE list | **Y** — Write-Scope table Task 10 "same set" → Task 9 → Task 8 row; dispatch retains count + composition |
| "If a stub's shape disagrees … fixture wins" | **Y** — retained in stronger form |
| THE HEADLINE (invented anchor, real anchors, banner-matches-trust, fixture-derivation consequences) | **Y** — Step 1 `:551-563`, Step 3 fence `:668-682`, Step 3b `:696` |
| Import-assertion specifics (file, regex, column-0 rule) | **Y** — Step 2 VERIFY block |
| Baseline `777` | **Y** — Step 4(a), with "verify it yourself" |
| Step 4(b) forbidden-decline detail | **Y** — Step 4(b) verbatim |
| Step 4(c) count-of-5 + raise-vs-`""` shape | **Y** — Step 4(c) |
| Step 3b three-category rubric, three-MEASURED count, n=1 nuance | **Y** — Step 3b + Step 1 `:561` |
| Vacuity-trap specifics (a)/(b) | **Y** — Step 2 fence comments (and removing them is what closed G and H) |
| "A whole-test RED says nothing about which assertion is load-bearing." | **N** — rationale only; the instruction ("attribute every RED to a single assertion") is retained |
| "Resolve any disagreement against the artifact, with a positive control." | **N** — rationale; the standalone positive-control bullet is retained verbatim |
| "(baseline 143)" for the three spawn files | **N** — an iteration convenience, and a stale-count surface; the AC requires the full suite anyway. Deliberate loss |
| zsh-ate-two-clauses rationale on `git commit -F -` | **N** — instruction retained |

**No obligation, scope constraint, method-discipline item, or report-format requirement was dropped.** All ten method bullets survive (TDD, positive control, argument-parsing, RED attribution, mutation hygiene, grep, editor diagnostics, bash floor, suite timing, git). The report-format section *gained* a clause (follow the validator's section names and declare the departure), and the deliverable list was corrected from "obligations 1–4" (which undercounted the seven listed) to "each of the seven".

---

## 4. New findings

**None at BLOCKER or MEDIUM.**

- **NIT 1.** Write scope says "the five in the File Map plus `test_spawn_handoff_hardening.py`". The Write-Scope table's "same set" actually chains to the **Task 8 row**, not the File Map. The two lists happen to contain the same five paths (File Map globs `fixtures/spawn-handoff/*.json`, Task 8 globs `fixtures/spawn-handoff/*`), so the count and composition are right and the dispatch tells the implementer to enumerate it themselves. Cosmetic.
- **NIT 2.** LOW Q survives in the plan (`:617-623`). Harmless per round 4's own analysis.
- **NIT 3.** The STRUCTURAL NOTE says the file "no longer duplicates **any** factual claim". Lines 19 and 21 do retain scope summaries (the re-wait semantics; token-is-the-only-success-signal). Both are true and neither belongs to the drift-prone class the note enumerates (anchor strings, capture counts, provenance labels), but the absolute phrasing overstates by a hair.
- **Drafted and withdrawn.** I drafted a finding that the dispatch's surviving "two live running-session captures" (line 40) reinstates the duplication the rewrite exists to eliminate. Measured against the fixture it is true, it sits in a historical narrative rather than an instruction, and its source is a frozen read-only file — there is no drift surface. Reporting the draft rather than deleting it, per the round's own standing rule.

---

## Verdict

The structural fix holds: the dispatch carries zero duplicated facts, every pointer resolves, and the one pointer that was wrong (obligation 6) is now right. BLOCKER N's replacement text is true against a re-derivation with controls in both directions. MEDIUM O's fifth fixture is produced and the inventory line agrees. The rewrite dropped four pieces of *rationale* and one convenience number, and no obligation. Ready to send.

**APPROVED**
