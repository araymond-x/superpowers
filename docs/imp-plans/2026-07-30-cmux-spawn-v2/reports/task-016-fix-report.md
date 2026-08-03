---
schema_version: 1
task_id: 16
task_type: implementation
status: DONE
files_changed:
  - path: "skills/subagent-driven-development/references/context-handoff-protocol.md"
    description: "reworded exit-0 picker-manual note to be consistent with the handshake=ok precondition"
tests:
  written: 0
  passing: 0
  command: "python3 tests/ARaymond-skill-regression/validate-all-skills.py"
  result: PASS
contract_compliance:
  - constraint: "doc-only; single-bullet reword; no other sections/files touched"
    status: compliant
    detail: "Edited only the exit-0 picker-manual sub-bullet; exit-1/exit-3/all other sections untouched; committed only the explicit doc path (1 file changed, 6 insertions, 3 deletions)."
---

**Implementation Summary:**

Reworded the exit-0 `picker-manual` sub-bullet so it no longer contradicts the exit-0 precondition (`handshake=ok`). The old text asserted the user must finish the picker "or the successor never starts" — impossible at exit 0, since the shipped script gates exit 0 on the child's readiness token unconditionally, and that token only fires after the child boots (which in `picker-manual` mode requires the human to have already finished the picker). The genuine unfinished-picker case surfaces as exit 3 `handshake=timeout`, already handled by the exit-3 branch.

BEFORE:
> **If `picker-manual`, tell the user in so many words that they must go finish the picker in that tab or the successor never starts** — the notification will not tell them. Otherwise nothing more to do here.

AFTER:
> At exit 0 the handshake already succeeded (`handshake=ok`), so a `picker-manual` launch means the attended picker was used AND completed — the child booted and the pickup is running. Nothing further is required of the user on this path; "the picker is still unfinished" cannot surface at exit 0 (it appears instead as **exit 3 `handshake=timeout`**, handled by that branch). Since the notification doesn't name the mode, it's still worth telling the user which one occurred. Otherwise nothing more to do here.

The surrounding exit-0 text (the `auto` vs `picker-manual` definitions, the surface-ref/launch-mode reporting) is preserved unchanged.

**Source Files Read:**
- `skills/subagent-driven-development/references/context-handoff-protocol.md` (exit-code section) — confirmed the exit-0 wording and that exit-3 `handshake=timeout` already covers the go-to-existing-tab case.

**CLAUDE.md Files Read:**
- Repo-root CLAUDE.md "cmux Auto-Spawn Handoff" section (via session context) — its "picker-manual exits 0 while a human finishes" note reflects pre-handshake v1 behavior; the v2 runtime contract lives in the doc under edit.

**Deviations from Plan:**
None. Single-bullet reword performed exactly as specified; no other sections or files touched.

**Self-Review Findings:**
- AFTER text keeps the true claims (notification fires either way, does not name the mode; still worth telling the user which mode occurred) and drops the false "or the successor never starts" imperative.
- Consistent with the exit-3 branch ("GO TO THE EXISTING TAB … never start a fresh session" for `handshake=timeout`).
- Regression suite: PASS 161, FAIL 0, WARNING 2 (advisory, allowed).
- Commit staged only the explicit doc path; 1 file changed, 6 insertions, 3 deletions.

**Concerns:**
None.
