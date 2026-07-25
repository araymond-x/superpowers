# Partner Review — Task 10 dispatch (e2e Step 14 + banner 14→15)

**Reviewer:** controller partner, dispatched agent (sonnet). **Round 1: BLOCKED. Round 2: APPROVED.**
**Output budgets given:** 800–1400 words (round 1), 400–700 (round 2, resumed via `SendMessage`).

**What this partner was asked to adjudicate:** the controller claimed it had found and empirically proved a defect in
the plan's OWN Step 14 fixture. The partner was told the whole dispatch turns on that claim and given the chain to
check link by link, told to run the predicate itself **with a positive control** rather than trust the controller's
empirical result, and told to verify premises in both directions and name anything taken on trust. It was also asked to
judge two controller decisions (withholding assertion strings; permitting temporary mutation of the frozen script).

---

## Round 1 — BLOCKED

**Status:** BLOCKED

**Verified independently:**
- Fixture creates version as a directory (`mkdir -p ".../versions/2.1.218"`, plan line 319, no trailing filename) — CONFIRMED by grep of `module-2-protocol-e2e-docs.md`.
- `preflight_ok()` is `[ -f … ] && [ -x … ]` at `spawn-handoff-session.sh:314-329`, `LAUNCH_MODE` defaults `"picker-manual"` at `:313`, upgraded to `auto` only via `preflight_ok()` at `:329` — CONFIRMED by reading the script myself.
- **Predicate + positive control, run myself in `/tmp`:** directory case → `-f false`, `-x true`, combined test FAIL (as claimed). Executable-file case → `-f true`, `-x true`, combined test PASS. Both outcomes as claimed — CONFIRMED, not taken on trust.
- Under `picker-manual`, `SUCCESSOR_CMD="claude-picker $PICKUP_ARG"` at `:377` — CONFIRMED, a bare, unadorned line, no TELEMETRY/ARGS/LABEL interpolation.
- Plan's six assertions (RC==0, new-workspace, `--focus false`, notify, intent<outcome, hop==1) — CONFIRMED none reference `SUCCESSOR_CMD` or the `successor command:` echo.
- Module Acceptance Criteria line 79 requires Step 14 to "assert composed spawn command + notify + reservation-then-outcome" — CONFIRMED, quoted verbatim.
- `preflight_ok()` is a **five**-way AND (five distinct `|| return 1` guard clauses) — CONFIRMED by counting them.
- Label increment: regex at `:283-291` turns `Proj-Session-2` into `Proj-Session-3`; worked-example comment at `:366-372` shows the same — CONFIRMED.
- Zero `| Pending |` rows in `deviations.md` — CONFIRMED (`grep -c` → 0).
- Task 9 "two fix rounds" — CONFIRMED via `task-009-implementer-report-fix.md` (round A `2fe7a50`, round B `19096af`); nothing from those rounds is substantively relevant to Task 10's fixture or assertions.
- Contract Constraints in the prompt are a verbatim match of the module header — CONFIRMED by direct comparison.
- `$PROJECT`/`$PYTHON` defined at lines 9-10, banner text is exactly `"E2E PIPELINE PASS - 14 steps composed correctly"`, insertion point is real — CONFIRMED by reading the file.
- No subdirectory `CLAUDE.md` under `tests/` — CONFIRMED (`find` empty).
- **REFUTED:** "Task 7's deviation row already states the rule verbatim — 'a real executable file must reach `launch=auto`, because `preflight_ok()` is a FIVE-way AND, so a picker-manual result proves nothing on its own.'" I grepped `deviations.md` for that sentence and every distinctive fragment (`FIVE-way AND`, `must reach \`launch=auto\``, `proves nothing on its own`) — the **only** hit in the whole file is the Task 10 row itself. Task 7's row (line 8) says something adjacent but different: "a version stored as a directory … would report `launch=auto` for a path the picker's own `find -type f -perm -u+x` can never discover." Same underlying principle, but not a verbatim prior recording. This is exactly the "right about the defect, wrong about a citation" pattern the brief warned to watch for.
- **REFUTED:** Pattern Reference claims Step 13 establishes "stub-on-PATH." I grepped the whole script for `PATH="`/`PATH=$` reassignments before Step 14 — zero hits. Step 13 has no stub binaries at all. It does establish `|| RC=$?`, the PASS echo, and temp-workspace cleanup (all three genuinely present at `:598-607`), but not stub-on-PATH. This claim originates in the plan's own Pattern Reference line and was carried into the dispatch unchecked.

**Context Completeness:** PASS. **Context Accuracy:** FAIL (the MX-A citation). **Prior Task Awareness:** PASS.
**Escalation Check:** PASS — "a pre-dispatch, empirically-proven, positive-controlled fixture fix that stays inside Task 10's own write scope (test file only) and touches no frozen artifact is squarely a 'controller corrects and logs' case, consistent with how Tasks 7-9 handled equivalent findings."
**Architectural Alignment:** PASS — "Step 14 is the only place the composed command, notify, and reservation-then-outcome ordering are checked together against a real (non-`--dry-run`) invocation; that's a genuine integration seam distinct from the 72 unit tests, not duplicated coverage."
**Pattern Completeness:** FAIL (stub-on-PATH).

**Verdict on the fixture defect:** Real. Every link in the chain checks out. The corrected block (executable file + `launch=auto` assertion) is the right fix.
**Verdict on Decision A (no supplied assertion strings):** Sound — "specifies precisely which properties to pin … while forcing the literal text to come from a real run — a well-calibrated response to last session's self-inflicted 'verified facts' drift bug, not under-specification."
**Verdict on Decision B (mutating the frozen script for proofs):** Sound — forbids `git stash`, requires `git checkout --`, and is checked in four independent places.

**Findings:** (1) citation accuracy — MX-A rule not stated verbatim in Task 7's row. (2) Pattern Reference misattribution — Step 13 has no stub-on-PATH idiom. "Both findings are cheap, isolated wording fixes; the fixture correction, Decision A, and Decision B are all sound as designed and should be preserved once the two citations are corrected."

## Round 2 — APPROVED (after both fixes)

**Status:** APPROVED

**Fix 1 (MX-A citation):** ACCURATE — "I independently found the quoted sentence verbatim in `~/.claude-codex-handoff/bundles/2026-07-25T02-12-19Z-cmux-integration/CONTINUE.md:39`. The new attribution to 'the session handoff bundle's warnings list' is correct, not just a softened guess. `grep -rn "FIVE-way AND"` across the repo confirms it appears nowhere else."

**Fix 2 (Pattern References):** ACCURATE — lists only the three real idioms and states stub-on-PATH is new to Step 14, "backed by `grep -n 'PATH=' tests/integration/sdd-e2e-test.sh` → one hit (`PYTHONPATH=` at `:579`)."

**Controller's mutant-vs-un-mutated characterization of Task 7's row:** CORRECT — "Task 7's row frames the directory sentence explicitly under 'reducing the version predicate ... to a bare `[ -x … ]`' — the mutant — then states the consequence. That consequence is conditioned on the mutated predicate, not the shipped script's default `-f && -x` behavior. The new row's distinction matches the source text precisely."

**New inaccuracies introduced:** None. Plus one volunteered out-of-scope find: "the prompt's separate 'Subdirectory CLAUDE.md Files' section attributes the `lint-shell.sh`/'VACUOUS post-commit' wording to CLAUDE.md, but that exact sentence actually lives in the same handoff bundle's `CONTINUE.md:42`, not CLAUDE.md. This predates both fixes under review … flagging only so it isn't lost, not blocking."

**Pending deviations:** 0.

---

## Controller disposition

**Round 1 BLOCKED on two findings; both were CONFIRMED against me and both are fixed. Round 2 APPROVED. The
volunteered third finding was also confirmed and fixed. Proceeding to the implementer dispatch.**

**The partner gate paid again, and again against the controller.** Independent verification before accepting:
- `grep -c 'FIVE-way AND' deviations.md` → **1**, and that single hit was my own Task 10 row. My "states the rule
  verbatim" citation was false.
- `grep -n 'PATH=' tests/integration/sdd-e2e-test.sh` → **one** hit, a `PYTHONPATH=` at `:579`. No stub-on-PATH exists.
- `grep -in 'vacuous' CLAUDE.md` → **nothing**. The third citation was false too.

**All three were the same failure shape: a TRUE fact attributed to the WRONG source.** That is worse than it sounds — a
reader who checks the named source and finds nothing cannot distinguish a mis-citation from a fabrication, so the whole
citation chain becomes untrustworthy on one bad reference. Recorded in `deviations.md` with the carry-forward rule: cite
the source you actually read it in, or cite nothing and state the evidence directly.

Two things worth noting about how this round went:

1. **The partner did what it was asked and re-derived rather than ratified.** It ran the `-f`/`-x` predicate itself in
   `/tmp` **with a positive control** (executable file PASSES, not merely directory FAILS) instead of accepting my
   empirical claim — the exact discipline the dispatch demanded, applied to the dispatch's own author.
2. **Finding 2 was inherited, not authored.** The stub-on-PATH claim came from the plan's own Pattern References line
   and I carried it through without checking. A Pattern Reference pointing at a convention that does not exist is the
   Pattern References mechanism inverted — it exists to stop "built from scratch, corrected 10 times," and instead it
   would have sent the implementer hunting for a model that was never there.

The fixture correction, Decision A, and Decision B were all preserved unchanged — the partner judged each sound after
independent verification, and nothing in the technical substance of the dispatch was altered by the three fixes.
