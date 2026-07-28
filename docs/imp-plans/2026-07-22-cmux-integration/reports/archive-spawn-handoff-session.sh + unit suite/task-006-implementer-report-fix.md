---
schema_version: 1
task_id: 6
task_type: implementation
status: DONE
files_changed:
  - path: "skills/subagent-driven-development/scripts/spawn-handoff-session.sh"
    description: "spawn_claude_workspace() captures cmux's `OK <ref>` stdout into SPAWN_WORKSPACE_REF and substitutes a generic {workspace} placeholder into the notify body; caller uses the ref in the outcome record and the printed result line; false code comment corrected"
  - path: "tests/unit/test_spawn_handoff.py"
    description: "5 new tests covering ref propagation to all three consumers, the no-trailing-newline parse, the empty-capture fallback, stdout relay, and rc survival under capture"
tests:
  written: 5
  passing: 5
  command: ".venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -q"
  result: PASS
contract_compliance:
  - constraint: "spec 5.4d steps 3-4 - workspace ref in outcome record, notify body, and stdout"
    status: compliant
    detail: "Ref parsed from cmux's `OK <ref>` stdout token, then used in `workspace=<ref>`, `... successor spawned in <ref>`, and the final stdout line. `(spawned)` remains only as the empty-capture fallback."
---

> `[task 6 fix]` round — closes the single BLOCKING `[MISSING]` finding from
> `task-006-spec-review.md`. Commit `3491171` (follows the Task-6 feature commit `5c6e4d9`).

**Implementation Summary:**
`spawn_claude_workspace()` now runs `CMUX_QUIET=1 cmux new-workspace … >"$out_f"` (argv held in a
`local -a` array so it stays SSOT across the mktemp-failure branch), captures `rc=$?` immediately
from the redirected command — no substitution, no pipe — then parses
`awk '/^OK[ \t]/{print $2; exit}'`, relays the captured bytes verbatim to stderr, and publishes
`SPAWN_WORKSPACE_REF`. On `rc==0` an empty capture degrades to `(spawned)` before the notify
substitution, so the body is never `spawned in `. The notify text parameter accepts a literal
`{workspace}` token, replaced via `${notify_text//\{workspace\}/…}` — the core learns nothing
about hops, bundles, or feature dirs, so Decision 15 holds. The caller passes
`"Hop $SP_HOP/$MAX_HOPS — successor spawned in {workspace}"`, writes
`workspace=$SPAWN_WORKSPACE_REF` in the outcome record, and prints
`spawned successor in $SPAWN_WORKSPACE_REF …` (step 4). The failure branch is untouched
(`workspace=spawn-failed`).

**Source Files Read:**
- `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` (full)
- `tests/unit/test_spawn_handoff.py`
- `tests/unit/spawn_handoff_helpers.py` (read-only, untouched)
- `docs/imp-plans/2026-07-22-cmux-integration/spec.md` — §5.4d + Log format + §5.5
- `docs/imp-plans/2026-07-22-cmux-integration/reports/task-006-spec-review.md`

**CLAUDE.md Files Read:**
- repo root `CLAUDE.md` — no subdirectory CLAUDE.md exists under
  `skills/subagent-driven-development/` or `tests/unit/` (verified).

**Deviations from Plan:**
None. Two deliberate design choices beyond the finding's literal text:
1. **Capture to a temp file rather than `$(…)`** — a command substitution would put the
   assignment's rc in front of cmux's, and the exit ladder depends on `$?`.
2. **Parse with `awk`, not a `while read` loop** — `read` skips a final line lacking a trailing
   newline, which would degrade **every real spawn** to `(spawned)` while echo-based stubs stayed
   green. Mutation M-E proves the guarding test is the sole discriminator for this hazard.

**Self-Review Findings:**
Live-verified the finding's premise AND the implementation against real cmux (three throwaway
workspaces, each created → confirmed in `list-workspaces` → closed → confirmed gone):
- bare `new-workspace` → `OK workspace:7`
- byte probe → `4f4b 2077 … 3a38 0a` (`OK workspace:8\n`, LF-terminated)
- **the production command** `CMUX_QUIET=1 cmux new-workspace …` → `OK workspace:9\n` on stdout,
  stderr empty.

`CMUX_QUIET=1` is a real knob (string present in the cmux binary: "set CMUX_QUIET=1 to silence
this notice") and suppresses only the stderr alias-deprecation banner — it does **not** swallow
the `OK` line. The deprecation notice was already on stderr, so a stdout redirect swallows
nothing even without it. `shellcheck --severity=warning` clean on the modified script. No `set -u`
added; no pipe into `grep -q`.

**Concerns:**
None blocking. Two notes for the controller:
1. `cmux` reports `new-workspace`/`close-workspace` as deprecated aliases for
   `cmux workspace create`/`close`. Migrating is out of scope here but worth a BACKLOG row.
2. Per the harness constraint the implementer did not write its own report file; the returned
   message is the report and was persisted here by the controller.

**Mutation Results:** (each applied to the committed code, then reverted; scoped run of the 5 new tests)
- **M-A** drop the awk capture (`SPAWN_WORKSPACE_REF=""`) → **2 RED**
  (`..._reaches_outcome_notify_and_stdout`, `..._survives_missing_trailing_newline`); the
  fallback test correctly stays green.
- **M-B** notify body loses `{workspace}` → **3 RED**.
- **M-C** stdout line loses `$SPAWN_WORKSPACE_REF` → **3 RED**.
- **M-D** outcome record reverted to the `(spawned)` constant → **2 RED**.
- **M-E** `awk` → `while read` loop → **1 RED**, exactly and only
  `..._survives_missing_trailing_newline` (proves that test is the sole discriminator for the
  newline hazard).
- **M-F** `cmux … | cat >"$out_f"` (clobbers `$?`) → **1 RED**, `..._rc_survives_stdout_capture`
  (script returned 0 instead of 3).
- **M-G** remove `cat "$out_f" >&2` → **1 RED**, `..._is_relayed_not_swallowed`.

**Verification:**
`tests/unit/test_spawn_handoff.py` **56 passed** (51 pre-existing + 5 new); full `tests/unit/`
**609 passed**; `validate-all-skills.py` **PASS 159 / FAIL 0 / WARNING 2** (the 2 known
advisories); full spawn test file re-run under a `/bin/bash` **3.2.57** PATH shim → 56 passed;
`/bin/bash -n` syntax-clean, and `${var//\{workspace\}/…}` + `local -a` + env-prefix-on-array-
expansion all executed directly under 3.2.57. Forced-failure path executed, not inferred: cmux
exit 5 → script exit 3, `.handoff-hops` == 1, `workspace=spawn-failed`. Nothing on the deferred
list was touched (incl. the `:390-391` unchecked-reservation advisory).

---

## Controller independent verification

- Commit `3491171` scope is exactly the 2 in-scope files (+173/−14).
- Ref reaches all three §5.4d consumers: outcome record `:434`, notify body `:426` (via the
  `{workspace}` placeholder substituted at `:400`), stdout `:436`. `(spawned)` survives only as
  the empty-capture fallback at `:399`.
- `rc=$?` is taken from the redirected command directly (`:389`), with no substitution or pipe;
  the mktemp-failure branch spawns uncaptured rather than discarding cmux's output.
- **Controller re-ran mutation M-F independently** (`CMUX_QUIET=1 "${nw[@]}" | cat >"$out_f"`):
  **2 RED** — `test_spawn_failure_rc_survives_stdout_capture` AND the pre-existing
  `test_spawn_failure_keeps_hop_exits_3`. Confirms the rc capture is load-bearing and that
  clobbering it breaks the exit ladder, not just the new test.
- Script restored byte-clean after mutation; `test_spawn_handoff.py` 56 passed.
