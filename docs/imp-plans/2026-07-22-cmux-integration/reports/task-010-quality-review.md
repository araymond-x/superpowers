# Code Quality Review — Task 10 (e2e Step 14 + banner 14→15)

**Reviewer:** dispatched adversarial quality reviewer (sonnet), round 1
**Range reviewed:** `f95912c..607033a` · **Output budget given:** 700–1100 words
**Returned assessment: PASS** — **no Critical, no Important, one Minor observation, zero findings requiring a fix round.**

**Controller framing:** the reviewer was told it is the gate that has paid on four consecutive tasks and that the spec
review's PASS is not evidence for it. It was told explicitly NOT to re-confirm what the spec review settled, was
**assigned** the mutation proof the spec review had left `[UNVERIFIED]`, and was pointed at the single highest-value
open question: the stub `cmux` never emits `OK <ref>`, so does `SPAWN_WORKSPACE_REF` silently fall back to `(spawned)`
— making Step 14 assert a degraded path while claiming to assert the real one? It was also told to demonstrate any
loose-assertion claim rather than speculate.

---

## Reviewer output (verbatim, as returned)

**Assigned mutation re-run:** Reran proof #3 — changed `parts+=("$(shq "$a")")` to `parts+=("$a")` in the `FORWARDED` loop at `skills/subagent-driven-development/scripts/spawn-handoff-session.sh:342` (dropping shlex re-quoting), then ran the full `bash tests/integration/sdd-e2e-test.sh`. Real output: Step 14 went RED exactly as claimed — `FAIL: composed command missing forwarded arg (re-quoted) + trailing /pickup b14`, with the dumped successor-command line showing `--append-system-prompt-file /tmp/a b.md '/pickup b14'` (unquoted, split on the space, matching the implementer's report verbatim). Restored via `git checkout -- skills/subagent-driven-development/scripts/spawn-handoff-session.sh`; `git diff --stat` on that path is empty and `git status --short` shows only the pre-existing controller SDD artifacts — no residue.

**Strengths:** The implementer independently found and empirically proved a real third plan defect (missing `cd "$SPAWN_WT"`) with a positive control (reproduced the `REFUSED: worktree not clean` failure before fixing it) — genuinely strong. All three mutation proofs pasted real FAIL output. `HOME`/`PATH` are fully overridden so the fixture doesn't depend on ambient state; the fixture's own git identity is set explicitly.

**Issues:**
- **[NEEDS_CONTEXT → resolved, no finding]** I built an isolated repro of Step 14 and inspected `$CMUX_LOG` byte-for-byte: it contains exactly two lines, `new-workspace --name SDD resume: feat --cwd ... --command ... --focus false` and `notify --title SDD handoff --body Hop 1/3 — successor spawned in (spawned)`. Neither line's content overlaps the other's grep target (`new-workspace`, `--focus false`, `notify` each appear in exactly one line, with no ambiguous substring). The loose-assertion hypothesis does not hold — checked, not manufactured.
- I also confirmed the cmux stub never emits `OK <ref>` on stdout (it only appends `"$@"` to `$CMUX_LOG`), so `SPAWN_WORKSPACE_REF` always falls back to `(spawned)` in this fixture — the `awk '/^OK[ \t]/{print $2; exit}'` parsing branch is never exercised by Step 14. This looked like a real gap ("the highest-value question"), but checking `tests/unit/test_spawn_handoff.py:897,916` shows that exact branch IS unit-tested (`echo "OK workspace:42"` / `printf 'OK workspace:9'` → asserted captured correctly), alongside the `(spawned)`-fallback branch (`:1211`). So this is deliberate, correct test-pyramid layering — e2e proves the real-invocation integration path, unit tests own the ref-parsing branch coverage — not a hole. No finding.
- **Minor:** `tests/integration/sdd-e2e-test.sh:379` — `grep -q "launch=auto"` and the final `[spawn-handoff] spawned successor in ... (launch=auto)` line both derive from the same `$LAUNCH_MODE` variable (script lines 313/329/379/483), so they can never diverge under any single-point mutation — the "first assertion" isn't independently pinning a second property, it's just an earlier echo of the same fact. Not a defect, just worth noting it's not actually two data points.
- No dead code, unused variables, or unreachable branches found in the added block; `shellcheck --severity=warning --external-sources` returns exit 0 on the full file, matching the implementer's claim (re-verified independently).
- File changed: only `tests/integration/sdd-e2e-test.sh`, hook and baseline both untouched (confirmed empty diff on both paths) — Contract Constraints honored.

**Conjunction-trap analysis:**
- `launch=auto` grep on `out`: pins the real preflight outcome (5-way AND in `preflight_ok()`); demonstrated red under the MX-A-class mutation in the implementer's own proof #1. No stand-in property found.
- `new-workspace` / `--focus false` on `cmux.log`: pins that the real spawn call with the real flag was made. Demonstrated the log has exactly one line containing each, with no cross-line ambiguity. Sound.
- `notify` on `cmux.log`: pins that the notify path fired. Demonstrated it's the literal first token of a distinct log line, not a substring hit inside the workspace name or command body (both checked, neither contains "notify"). Sound.
- Composed-command assertions (#1 flag order/telemetry/label, #2 forwarded-arg re-quoting/trailing `/pickup`): both anchored to the specific `successor command:` line via `grep -qF`, not bare-file grep. #2 empirically reproduced red (this review's assigned re-run); #1 not independently reproduced here but is structurally the same anchor and was derived from a real run per the implementer's pasted verbatim evidence, cross-checked against the script's actual token order at `:334-348`.
- Hop file (`.handoff-hops`): only the script itself writes it in this fixture (fresh `mktemp -d` tree, no other writer) — nothing else could produce a false `1`.
- Reservation ordering (intent-before-outcome): both lines come from a single log file written sequentially by the script itself under the documented reserve-before-spawn contract; no alternate writer in the fixture.

**Files mutated and restored:** `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` — mutated once (FORWARDED-loop re-quoting drop), restored via `git checkout --`. Verified via `git diff --stat` (empty) and `git status --short`.

**Assessment:** PASS

---

## Controller disposition

**PASS accepted with no fix round. Task 10 is complete.** Controller verification of this review's own claims:

| Claim | What the controller ran | Result |
|---|---|---|
| Frozen script restored after the reviewer's mutation | `git diff --name-only -- spawn-handoff-session.sh` | **empty** — restored |
| The `OK <ref>` branch really is unit-tested | `grep -n 'OK workspace' tests/unit/test_spawn_handoff.py` | **CONFIRMED** — 5 hits incl. `:897` `echo "OK workspace:42"` and `:916` `printf 'OK workspace:9'`, exactly as cited |
| Suite still green end-to-end | `bash tests/integration/sdd-e2e-test.sh` | **`PASS: Step 14 …`** then **`E2E PIPELINE PASS - 15 steps composed correctly`** |

**The four-task streak of quality-review defects ends here — honestly, not by thinning the review.** This round was
given a harder brief than any before it (an assigned mutation, a named high-value hypothesis, and a demand to
*demonstrate* rather than speculate), and it came back with no Critical and no Important. What makes that credible:

1. **It chased the assigned high-value question to a real answer instead of reporting it as a risk.** The `OK <ref>`
   fallback IS a genuine observation — the stub never emits it, so `SPAWN_WORKSPACE_REF` really is `(spawned)`
   throughout Step 14. A lazier review would have banked that as an Important finding ("e2e asserts a degraded path").
   Instead it went and checked whether the branch is covered elsewhere, found it at
   `test_spawn_handoff.py:897/:916` plus the fallback at `:1211`, and correctly reclassified it as **deliberate
   test-pyramid layering**. The controller verified those line citations. **That is the opposite of the citation
   sloppiness that got three findings against the controller earlier in this task.**
2. **It refused to manufacture the loose-assertion finding it was pointed at.** Asked whether `grep -q "notify"` could
   be satisfied by a substring inside the `new-workspace` line, it built an isolated repro, dumped `$CMUX_LOG`
   byte-for-byte, and showed the log has exactly two lines with no cross-target overlap — reporting "the hypothesis does
   not hold — checked, not manufactured." A speculative Critical here would have cost a whole fix round.
3. **Its one Minor is a real epistemics point, not filler.** `launch=auto` appears twice in the output, but both echoes
   derive from the same `$LAUNCH_MODE` variable — so they are one data point wearing two hats, and no single-point
   mutation can make them disagree. That does not weaken the assertion (proof #1 showed it goes red), but it correctly
   deflates any impression that Step 14 pins launch mode twice. **Accepted as-is, no change**: the assertion's value is
   failing early with a clear cause, which it does.

**Mutation-proof coverage across the two reviews is now 2 of 3 independently reproduced** — spec review re-ran #1
(`preflight_ok` → `return 1`), quality review re-ran #3 (dropped `shq` re-quoting), both matching the implementer's
pasted output. Only #2 (flag-order swap) rests on the implementer's own evidence, and it shares its anchor with #3.
Recorded so the residual is visible rather than implied.
