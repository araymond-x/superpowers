# Partner Review — Task 8 dispatch (round 5)

**Status:** APPROVED — the dispatch is ready to send.

Reviewed at HEAD `fd7bf9b`. Model: opus. Everything below was executed against the running code.

## Round-4 findings — all three CLOSED

**F1 (P7-3/P7-7 vacuous as a pair): CLOSED, re-measured rather than re-read.** The reviewer's first probe was itself defective — it wrote `task-001-implementation.md`, which does not match `_REPORT_GLOB = "task-*-implementer-report*.md"`, so its "populated" dir counted `0` *without* the shim. A positive control (populated + no shim → must print `1`) caught it. Corrected fixture matrix:

| fixture | today | assigned to |
|---|---|---|
| populated + no shim | `1` | positive control — probe works |
| **empty** + ImportError shim | **`0`** ← the defect | **P7-3's pin** ✓ |
| **absent** + shim | `0` | P7-3 ("empty or absent") ✓ |
| **populated** + shim | **`unknown`** ← already correct | **P7-7's positive control** ✓ |

Fixture assignment is the **right way round**; two distinct fixtures; P7-7 carries the explicit prohibition against standing in for both.

**F2 (P7-1(ii) unpinned): CLOSED, and the fix is stronger than round 4 asked for.** All five shapes print `auto` today, so every prescribed assertion discriminates. The positive control exists and says what the plan claims. Beyond that: `pol = h.get("spawn_policy") if isinstance(h, dict) else None` means **three of the pinned shapes (no `handoff`, `spawn_policy: null`, `handoff: 5`) all yield `pol is None` today yet require different outputs** — so the implementer cannot satisfy the battery by switching on `pol` and is forced into the correct key-presence distinction. The control genuinely kills a blanket fail-closed (it would flip the legacy case to `ask` → RED).

**F3 (count): CLOSED.** Dispatch now reads EIGHT with all ids, names Step 2b authoritative, annotates why "seven" was false. Both counts re-derived independently from the register's gate cells: **eleven** scheduled (STANDING RULE correctly excluded), of which **eight** require support-pair edits (B1 → hardening file; P7-4 → verification-only; OP-1 → discharged).

## New defects introduced by `fd7bf9b`: NONE FOUND

Checked: every new citation, the P7-1(ii) assertion list against live behavior, the P7-3/P7-7 split by measurement, the Step 6 override for contradiction, the eight-vs-eleven arithmetic, and all four new `deviations.md` rows for false claims — **every factual claim in those rows is true as written**, including the `:112`/`:113` re-verification.

## Citation audit

| citation | verdict |
|---|---|
| `test_floor_factor_and_none` | **VERIFIED** — exists at `:110` |
| its `hop_ceiling(8) == 16` assertion, NOT `hop_ceiling(None)` | **VERIFIED, and it IS the factor pin** — `:112` is `hop_ceiling(8) == 16` (16 = 2×8, clears floor 6, so `CEILING_FACTOR` mutations go RED); `:113` pins the floor. The correction is exactly right |
| `test_handoff_support.py:198` (P7-1(ii) control) | **VERIFIED correct today** — asserts `auto` for `{"total_tasks":5,"tier":"standard"}`. See nit 1 |
| quoted AC-5 checkbox text | **VERIFIED verbatim** at `module-2-models-budget.md:653`; positive control (`degradation` → 3 hits) confirms `AC-5` → 0 hits is real. Its hold condition reads "P7-3, P7-6 and P7-8", matching the dispatch |
| "the Shared Constants section" | **VERIFIED, resolves** — not dangling |
| Step 6 `-m` override | **No contradiction** — names the plan's form, states the override, gives the reason, declares itself the one exception |

## Coherence pass

Two **drifted duplicates**, both harmless (authoritative statement correct, drift annotated at point of use): plan `:66` still said "seven"; dispatch's "differ by exactly that row" understates (they differ by two — STANDING RULE and OP-1). **No unfollowable instruction and no instruction whose subject no longer exists.**

## Final vacuousness sweep

| pin | discriminates? |
|---|---|
| P7-1(ii) — 4 shapes → `ask` | **Yes** (all `auto` today) + control forbids blanket fail-closed |
| P7-3 — empty/absent + shim → `unknown` | **Yes** (`0` today) — measured |
| P7-7 — populated + shim, mutation `print("unknown")`→`print(0)` | **Yes**, explicitly barred from covering P7-3 |
| P7-6 — non-UTF-8, assert `rc == 0` | **Yes** — measured `rc=1` + empty stdout today |
| P7-8 — unreadable → `indeterminate` **with** missing-log → `0` control | **Yes** — the paired control kills the blanket handler |
| Ceiling `expected_hops=5` | **Yes** — read `spawn-handoff-session.sh:190` (`-ge`) directly rather than accept round 4's word: ceiling 10, `"9"` proceeds, `"10"` refuses; `*1`/`*3`/deletion all RED |
| P7-2, P7-5, P7-9(A)(D) | Contract/regression pins on already-correct branches — **non-discriminating by design and labelled as such** |
| P7-9(B) placement invariant | **Yes** — unpinned today, and P7-3 edits that exact function |

**Nothing in the battery makes the code accept something it should not.**

## Standard checks

**Completeness PASS** · **Accuracy PASS** · **Prior Task Awareness PASS** · **Escalation PASS** · **Architectural Alignment PASS** · **Pattern Completeness PASS**

Gates re-run at `fd7bf9b` (not inherited): **token estimate OK, 7,421/200,000**; **`validate-plan.py` WARNING**, `blockers: []`, sole warning the advisory 248-line notice. `rc=2` is the script's documented WARNING code; the gate hook blocks only on `FAIL`.

## Non-blocking nits (all four ACTIONED by the controller before dispatch)

1. **The `:198` citation is an anti-rot self-inconsistency** — the same commit rewrote the ceiling citation *from* a line number *to* a construct, then introduced a fresh line-number citation into `test_handoff_support.py`, the very file the implementer is about to edit for P7-2, P7-5 and P7-9. Any test added above `:198` rots it mid-task. → rewritten to cite `test_expected_hops_and_policy_cli_on_legacy_and_garbage`.
2. Plan `:66` still said "seven". → corrected to EIGHT with ids.
3. Dispatch "differ by exactly that row" → corrected to name both differing rows.
4. `AC-5` persists as shorthand where the string is unfindable → left as shorthand; the only *lookup* instruction already supplies the searchable text.

## Premises verified first-hand vs. accepted

**First-hand:** `fd7bf9b` in full; the dispatch in full; `_handoff_support.py`'s `_frontmatter`/`count_tasks_done`/`stall_streak`/`_cli`; `test_handoff_support.py:105-120,190-206`; `spawn-handoff-session.sh:186-194`; `module-2-models-budget.md:653`; `validate-plan.py`'s exit-code convention and the gate hook's blocking condition; register gate cells enumerated individually. **Executed:** `tasks-done` under an ImportError shim across four fixture shapes plus two no-shim controls; `spawn-policy` across eleven manifests; `tasks-done` on a non-UTF-8 report; both gates at HEAD. All recursive sweeps via `/usr/bin/grep`.

**Accepted without re-measuring:** the 707-green suite; hardening 10/10; the four-item migration list's completeness.

**Two corrections owed.** *Mine:* the first P7-3/P7-7 measurement used a filename that did not match the glob and produced `0` everywhere — a clean, plausible, entirely false result that would have contradicted round 4. The positive control caught it. **Twelfth instrument failure this sprint**; round 4's finding stands as written. *To round 4:* its claim that plan `:66` "is annotated inline" was **inexact** — that parenthetical routes the reader for *execution* and does not correct the count. The controller's decision to fix only the dispatch rested on that reading. Operationally harmless, but it is why nit 2 existed.

**Why I am not blocking a fifth time.** Both remaining issues are prose that misdescribes a relationship without misdirecting work — the operative instructions (Step 2b's eight enumerated bullets, the authoritative eleven-row sentence) are correct and complete. Meanwhile **the consent gate is fail-open in production right now**: `"OFF"`, `false`, `null` and a non-dict `handoff` all print `auto`, as measured. Another round costs a round of that. **That asymmetry, not the streak, is the argument.**

---

## Controller disposition (round 5)

**APPROVED — dispatch proceeds.** The stopping rule required both conjuncts and both are met: the reviewer approves, and its four findings are prose-level. All four were actioned anyway (they were one-line edits), so the implementer receives the corrected text rather than a known-stale one.

**The reviewer caught its own instrument failure mid-review and reported it** — a fixture filename that did not match `_REPORT_GLOB`, producing `0` everywhere and a clean, plausible result that would have *contradicted* round 4 and reopened a closed finding. A positive control caught it. **Twelfth instrument failure of the sprint, and the second in two rounds where the false result would have looked like a legitimate disagreement with a prior round.** The standing rule holds: an empty or passing probe is a claim, not a fact.

**Nit 1 deserves recording as a pattern, not just a fix.** The same commit that rewrote one citation *away from* a line number, explicitly invoking the repo's anti-rot policy, introduced a *new* line-number citation two edits later — into the exact file the implementer is about to add tests to, where it would rot mid-task. Applying a policy in the place you are thinking about it while violating it in the place you are not is the ordinary shape of this failure. Fixed by citing the construct.

**Round-count outcome:** five partner rounds on one dispatch (1–4 BLOCKED, 5 APPROVED), yielding fifteen findings — a fail-open regression, four count defects, two vacuous prescriptions, a nonexistent test seam, a hang, a floor-dominated pin, an unpinned consent change, and a false consumer-closure claim, plus a retraction and two self-corrections. Every round after the first found defects the previous round's *fixes* had introduced or left half-landed. The streak ended when the findings became cosmetic, which is exactly what the stopping rule specifies.
