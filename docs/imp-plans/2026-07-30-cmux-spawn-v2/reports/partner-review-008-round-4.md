# Partner Review — Task 8 dispatch (round 4)

**Status:** BLOCKED

Reviewed at HEAD `8c2d90b`. Model: opus. Everything below was executed, not reasoned about.

## Round-3 findings — all three CLOSED

**F1 (no Step writes the support pair): CLOSED.** Step 2b exists as a real `- [ ]` checkbox with eight row-labelled bullets; the dispatch names it. Step 6's staging list walked by producer: `spawn-handoff-session.sh`→Step 4(a–f); `_handoff_support.py`→**Step 2b**; `test_spawn_handoff.py`→Step 2 migration items 2–4; `test_spawn_handoff_v2.py`→Step 2; `test_spawn_handoff_hardening.py`→Step 2 migration item 1; `test_handoff_support.py`→**Step 2b**; `spawn_handoff_helpers.py`→Step 1; `tests/unit/fixtures/spawn-handoff/`→**none** (Step 1 says "nothing new is needed yet" — a no-op `git add`, no lost scope). **Mapping total but for the fixtures dir.**

**F2 (`exec python3` self-recursion): CLOSED, reason correct.** Re-measured with a fresh argv-dispatching stub first on PATH: bare `exec python3 "$@"` → 3s watchdog, `rc=137`; `exec /usr/bin/python3 "$@"` → `rc=0`. Seam premise confirmed at `spawn-handoff-session.sh:16-18` (`PYTHON="$SUPERPOWERS_ROOT/.venv/bin/python3"`, `[ -x ] || PYTHON="python3"`).

**F3 (ceiling test): CLOSED, arithmetic AND boundary verified.** `expected_hops=5` → `max(6, 2×5) = 10`. **Read the actual comparison rather than assuming:** `spawn-handoff-session.sh:190` is `[ "$HOPS" -ge "$MAX_HOPS" ]`, so `"9"` proceeds and `"10"` refuses — no off-by-one. Mutations now discriminate both directions: `* 1`→ceiling 6→`"9"` refuses (RED); `* 3`→15→`"10"` proceeds (RED); deletion→6 (RED).

## Step 2b — bullet-by-bullet against the running code

| row | accurate? | vacuous? |
|---|---|---|
| **P7-1(ii)** | YES — `"OFF"`/`"Off"`/`false`/`null`/`{"handoff":5}` all print `auto`; controls `"off"`→`off`, `5`/`null`/`[1,2]`→`ask` | Not vacuous, **but no assertion prescribed — Finding 2** |
| **P7-3** | YES, reproduced — with an `ImportError`-raising `yaml.py`: empty dir → `0`, populated → `unknown` | **VACUOUS as a pair with P7-7 — Finding 1** |
| **P7-6** | YES, reproduced — `\xff\xfe` byte → traceback, `rc=1`, empty stdout, escaping `except OSError` | Adequate |
| **P7-8** | YES — `except OSError: return 0`, docstring "no log yet: first hop" | Not vacuous; the required missing-log positive control kills the blanket handler. **Best-specified bullet in the set** |
| **P7-2** | YES — `TestCli` is exactly two tests; `stall-streak` invoked by neither | Adequate |
| **P7-5** | YES — `5`/`null`/`[1,2]`→`ask` today, unasserted | Adequate |
| **P7-7** | YES, and its caveat holds: `/usr/bin/python3` DOES ship PyYAML | **Fixture shape unspecified — Finding 1** |
| **P7-9** | YES on all three: (A) unpinned; (B) no placement pin; (D) guard unpinned while its `_cli` twin IS pinned | Adequate |

No contradictions between Step 2b, the dispatch's P7 summaries, and the register rows.

## Independent count: EIGHT

**P7-1(ii), P7-2, P7-3, P7-5, P7-6, P7-7, P7-8, P7-9.** P7-4 requires no edit (verification only); B1 lands in `test_spawn_handoff_hardening.py`, not the support pair; OP-1 dispositioned. Register enumeration by gate cell: **eleven** (B1, P7-1…P7-9, OP-1); the STANDING RULE row's gate reads "every future test touching this family" and is correctly **not** one of the eleven — **the dispatch's authoritative-set sentence is accurate.**

## P7-4 disclosure — VERIFIED, not refuted

```
stall-streak --tasks-done unknown → argparse "invalid int value: 'unknown'", rc=2
stall-streak --tasks-done 3       → 0, rc=0                      (positive control)
```
Plan step (e) branches `if [ "$TASKS_DONE" = "unknown" ]` **before** the only `stall-streak` invocation. Correct on both halves; the row closes as already-satisfied.

## Standard checks

**Completeness PASS** · **Accuracy PASS** (Contract Constraints byte-identical; `validate-plan.py` → WARNING, blockers 0, "246 lines", matching the commit message) · **Prior Task Awareness PASS** · **Escalation PASS** · **Architectural Alignment PASS** · **Pattern Completeness PASS**

## Findings

**1 — [BLOCKING, vacuousness, measured] P7-3 and P7-7 can BOTH be satisfied by one test that cannot detect whether the P7-3 fix was made.** P7-7 prescribes the technique but not the **fixture shape**, and the natural fixture — mirroring the adjacent `test_tasks_done_cli`, which writes a report — is *populated*. Measured against **today's unfixed code**: shim + EMPTY dir → `0` (the defect); shim + POPULATED dir → `unknown` (already correct). So a P7-7 test on a populated dir **passes before and after the P7-3 fix** — revert the probe and it stays green. P7-3 would then be the one row in Step 2b with no discriminating pin at all. *Fix:* P7-3's pin is the EMPTY/absent dir; the populated case is P7-7's positive control. Two fixtures, one battery.

**2 — [BLOCKING] P7-1(ii) is the only bullet that changes production behavior on the SOLE consent gate and prescribes no assertion.** Six of eight bullets name their pin explicitly. P7-1(ii) says only "Fail closed to `ask`." After the fix nothing asserts `"OFF"`/`false`/`null`/non-dict → `ask`; no shell test covers it either. **The register schedules a whole row (P7-5) to pin an adjacent already-correct branch while the fix that creates new consent behavior ships unpinned** — in the over-permissive direction where every real defect in this feature has lived. *Fix:* require the four assertions, with the existing no-`handoff`-block → `auto` case as the positive control forbidding a blanket fail-closed.

**3 — [BLOCKING, count] The dispatch states two different counts for the same set, and the unannotated one is the known-false one.** Dispatch `:31` still read "seven scheduled rows are edits to them" flatly, while `:84` says Step 2b carries eight. The plan's "seven" at `:66` is annotated inline; the dispatch's was not. The omitted row is **P7-2 — the exact row round 1 BLOCKED on.**

## Non-blocking nits

- Plan Step 6 prescribes `git commit -m` while the dispatch says "never `-m`". The plan's literal message is `-m`-safe, so nothing breaks, but the dispatch also says fences are the contract.
- `test_handoff_support.py:113` is cited as the Python `CEILING_FACTOR` pin; `:113` is `hop_ceiling(None) == CEILING_FLOOR` (the FLOOR). The factor pin is **`:112`** (`hop_ceiling(8) == 16`).
- **The string `AC-5` does not occur in `module-2-models-budget.md`** (positive control: `Acceptance` matches once). It is the 5th checkbox at `:653`. An implementer told to "note that AC-5's condition is met" has no string to find.
- Step 2b sits between Step 2 (failing tests) and Step 3 (run to verify failures) but bundles production edits with their tests, so eight rows skip the red phase as written. The mandatory mutation run is a superset of fail-first — process tidiness, not a coverage hole.
- Step 2b is not a fenced block while the dispatch says the spec reviewer diffs fences. Delivered exactly as round 3 asked; the fence half is not addressable without turning prose into code.
- `tests/unit/fixtures/spawn-handoff/` is staged by Step 6 with no producer step — harmless, but it is the one residue of the standing rule round 3 minted.

## Premises verified first-hand vs. accepted

**First-hand:** all three prior reports incl. dispositions; `8c2d90b` in full; Task 8 in full; `_handoff_support.py` and `test_handoff_support.py` in full; `spawn-handoff-session.sh:10-31,171-192`; `module-2-models-budget.md:650-654`; every Deferred-Work gate cell read individually. **Executed:** `spawn-policy` on ten manifests plus controls; `stall-streak --tasks-done unknown` (rc 2) + valid-int control; `tasks-done` on a non-UTF-8 report (rc 1) + valid control; `tasks-done` under an ImportError yaml shim on **both** empty and populated dirs (the Finding-1 measurement); `/usr/bin/python3 -c "import yaml"`; the `exec` recursion both directions under a watchdog; `validate-plan.py`. All recursive sweeps used `/usr/bin/grep`; when the `AC-5` grep came back empty I ran a positive control before concluding — the emptiness was real, which became a nit rather than a false closure.

**Accepted without re-measuring:** the 707-green full suite (round 3 ran it); `test_spawn_handoff_hardening.py` 10/10 (rounds 2–3); round 3's `SUPERPOWERS_ROOT` invocation census (I re-derived the mechanism and re-measured the recursion half, not the census); the four-item migration list's completeness.

**Where I checked a prior round rather than trusting it, and it held:** round 3's F3 arithmetic. Its report asserted the fix works but never named the comparison operator. I read `:190` (`-ge`) specifically because a `-gt` would have made `"10"` proceed and silently un-fix the finding. It is `-ge`. Recording it because the instruction to check was right even though the answer was clean — that is the asymmetry that makes negative findings worth the extra call.

---

## Controller disposition (round 4)

**All three findings ACCEPTED; four of the six nits also fixed.** This is the fourth consecutive blocking round and the third consecutive round to find defects in the previous round's fixes.

**Finding 1 is the strongest single result of the whole sequence, because it was MEASURED rather than reasoned.** Three prior rounds all read the P7-3 and P7-7 bullets and passed them. Round 4 actually ran the unfixed code under an `ImportError` shim against two different fixture shapes and found that the natural fixture for P7-7 — the one that mirrors the adjacent existing test — is green *before* the P7-3 fix. Both rows would have been reported "fixed" with a test that proves nothing. **The generalization: when two rows share a mechanism, ask which FIXTURE each needs, not merely which technique** — a shared technique silently collapses two pins into one.

**Finding 2:** accepted without hesitation. The asymmetry the reviewer names is damning on its own — P7-5 exists purely to pin an already-correct branch, while the one bullet that *changes* consent behavior had no pin at all.

**Finding 3:** the **fourth** count defect on this single dispatch (nine-vs-eleven, two-vs-four, seven-vs-eight, and now the plan annotated while the dispatch was not). Fixed by making the dispatch carry the corrected count *and* the annotation.

**Nits actioned:** the `:112`/`:113` mis-citation was independently re-verified (`hop_ceiling(8) == 16` is indeed `:112`) and rewritten to cite the **construct** `test_floor_factor_and_none` rather than a line number, per the repo's own anti-rot policy — round 3's report and my own plan text had both propagated `:113`. The absent `AC-5` string was confirmed with a positive control and the dispatch now quotes the checkbox text instead of the label. Step 6's `-m` conflict is resolved by an explicit override clause. **Not actioned, deliberately:** the fixtures-dir staging (a no-op `git add`, and removing it would risk an implementer skipping a fixture it later does need), Step 2b's position relative to the red phase (the mandatory mutation run is a strict superset), and the not-a-fence observation (unaddressable as the reviewer itself notes).

Task 8 now 248 lines under the recorded exception; token-estimate gate re-run: OK, 7,421/200,000.
