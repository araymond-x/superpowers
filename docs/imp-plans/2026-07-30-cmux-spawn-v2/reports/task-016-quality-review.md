# Task 16 Code-Quality Review — context-handoff-protocol.md (doc)

Factual accuracy vs the shipped script was verified separately (spec review, PASS). This review is DOC QUALITY: will a blocked controller reading under pressure be helped?

## Round 1 — CHANGES_REQUESTED (2 Important, 2 Minor, 2 Nit)

**Strengths:** step spine 1–5 intact; reference material parked after the spine behind `---`; double-spawn danger handled correctly (`handshake=timeout` → go to existing tab, never a fresh session); "failure that does not look like one" register preserved; surface/tab used consistently.

**Findings:**
1. [Important] Exit-0 `picker-manual` gloss still asserts pending completion ("a human must complete it there before the pickup runs") in the most-skimmed region, contradicting the reworded paragraph below it. The prior fix added the reconciling paragraph but left the contradicting clause in the parenthetical. → reword the gloss so it doesn't assert pending completion at exit 0.
2. [Important] Mechanics-card regen command is not copy-pasteable (`$PYTHON` is hook-internal, undefined in a reader's shell; card needs venv/pydantic → plain python3 exits 2) AND the fallback ("the card prints an absolute-path form in its header") is circular — the card isn't generated on the manual-fallback path. → define `$PYTHON` + de-circularize the parenthetical.
3. [Minor] Hop-ceiling formula `max(6, 2×expected)` duplicated verbatim (preconditions note + env-knob entry) → drift risk; reference the env-knob instead of restating.
4. [Minor] `quota low` exit-3 cause gives no next action while every sibling does → add one for parity.
5. [Nit] Bundle placeholder spelled three ways (`<bundle-id>` / bare / `<id>`) → standardize.
6. [Nit] "reviewed and at a clean boundary" says "clean boundary" twice (line 6) → tighten.

Controller note: the card's OWN regen line (`write-mechanics-card.py:93`) also emits literal `$PYTHON` while its checkpoint lines use resolved `sys.executable` — a coupled inconsistency in Task 12's committed file, OUT OF Task 16's write scope; logged to deviations as a deferred follow-up, not fixed here.

## Round 2 — APPROVED (re-review after [task 16 fix] d12c434)
All six fixes verified closed in the current file:
- **Important #1 (exit-0 picker-manual):** skim-target gloss no longer asserts pending action; agrees with the follow-up paragraph. Genuinely resolved — reader acting on the bolded gloss alone is no longer misdirected.
- **Important #2 (`$PYTHON` regen cmd):** circular "card prints it" line gone; replacement names `$PYTHON` = `$SUPERPOWERS_ROOT/.venv/bin/python3`, warns it's hook-internal/absent in a shell, warns plain python3 exits 2. Actionable on the manual-fallback path. (Marginal residual: `$SUPERPOWERS_ROOT` is itself a var, but the concept + in-install relative location is sufficient — not worth reopening.)
- **Minor #3:** ceiling formula de-duplicated (single source in env-knob entry).
- **Minor #4:** quota-low has a concrete next action.
- **Nit #5:** placeholder standardized to `<bundle-id>`.
- **Nit #6:** "reviewed and committed" (redundancy gone).
Reviewer agrees the coupled `write-mechanics-card.py:93` `$PYTHON` issue is correctly DEFERRED (Task 12's committed file, out of a doc-only task's write scope; logged to deviations). validate-all-skills.py PASS 161/0/2. **Quality review APPROVED — no further changes.**
