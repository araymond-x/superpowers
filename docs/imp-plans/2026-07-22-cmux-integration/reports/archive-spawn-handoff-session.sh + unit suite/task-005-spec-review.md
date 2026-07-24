# Task 5 Spec Compliance Review — Launch composition B (auto preflight + compose-side quoting)

**Reviewer:** general-purpose spec compliance auditor
**Date:** 2026-07-24
**Range:** `9edb259..e7d5fe1` (2 files, +148/-0)

**Verdict: PASS.** No blocking findings. Advisory observations below; Task 6 is cleared to proceed.

Verified by reading `spawn-handoff-session.sh` in full (not just the diff), reading spec.md §5.4a–d / §5.5 / §7, and by **driving the script directly** with hand-built environments — not by re-running the implementer's tests.

---

## Answers to the seven required questions

**1. Preflight condition list vs §5.4c — COMPLETE, exactly matching.**
spec.md:161 enumerates: metadata usable (VERSION non-empty; ARGS decodes under v1 or absent; LABEL may be empty; TELEMETRY absent ⇒ off) AND version binary exists at `~/.local/share/claude/versions/<version>` AND `claude-picker` resolves on PATH AND `--handoff-contract` prints exactly `1`. The implementation's five conditions (`spawn-handoff-session.sh:288-296`) are a 1:1 mapping — VERSION non-empty, `ARGS_OK=1` (the "ARGS decodes" clause, set by Task 4), `-f` AND `-x` on the version file, `command -v claude-picker`, string-equality contract probe. LABEL and TELEMETRY are correctly **not** consulted (§5.4c says LABEL may be empty and telemetry absence "never blocks auto"); confirmed empirically that a telemetry-absent, otherwise-complete environment still yields `launch=auto`. No condition missing, none extra.

**2. Composed flag set and ORDER vs §5.4c — EXACT MATCH.**
spec.md:157 pins `claude-picker --non-interactive --pick-version <v> --telemetry <on|off> [--session-label <label>] <decoded forwarded args> "/pickup <BUNDLE_ID>"`. Live run produced, verbatim:

```
claude-picker --non-interactive --pick-version 2.1.218 --telemetry on --session-label Proj-Session-3 \
  --append-system-prompt-file '/tmp/a b.md' --foo 'he said "hi"; rm -rf /tmp/PWNED' '/pickup b1' \
  || { printf '%s %s runtime-picker-failure hop=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" spawn "1" >> /…/handoff-spawn.log; claude-picker '/pickup b1'; }
```

Order, optionality of `--session-label`, forwarded-args placement, trailing `/pickup`, and the `|| { … }` residual chain all conform. Hostile input (`he said "hi"; rm -rf …`) survives as one quoted literal — no injection surface.

**3. Fallback-chain shape vs §5.4d — shape correct; the literal `spawn` spawn-id is a LEGITIMATE Task-6 carry-forward, not a Task-5 defect.**
§5.4d's log format requires `ISO-8601 timestamp, spawn id, record type, hop number`. The composed line emits the literal word `spawn` in the spawn-id field. Judgment: **carry-forward, correctly handled.** The uuid is generated in Task 6 (`module-1-spawn-script.md` Step 2 places `SPAWN_ID="$(… uuid4 …)"` *after* the dry-run short-circuit, i.e. after the compose block), so Task 5 could not interpolate it without annexing Task 6's territory. The implementer flagged it as Concern 1 and the controller logged it as a **CRITICAL carry-forward** in `deviations.md`.

> **⚠ Load-bearing caveat for Task 6:** its plan text as written will **not** fix this — `SPAWN_ID` is still created *after* composition. Task 6 must deviate (generate the id before the compose block, or re-compose the fallback tail). If it doesn't, the §5.4d log contract ships violated.

**4. The 6th test rests on a REAL §7 requirement — not [EXTRA].** spec.md:196 (repo-3 matrix) states verbatim:

> "a space/quote-bearing decoded argv driven through composition → **survives intact in the `--command` string** (compose-side quoting, §5.4c)"

"Survives intact" is an arity claim, not a substring claim. The controller's identity-`shq()` mutation proves the plan's own `assert "a b.md" in cmd` passes with the quoter completely broken; only `test_composed_command_reparses_with_correct_arity` fails. Without it, the compose-quoting Contract Constraint would have **zero** real coverage. This is spec-mandated work the plan under-specified, not scope creep.

**5. No regression to Tasks 1–4.** The script diff is a single hunk `@@ -279,6 +279,46 @@` containing only `+` lines, inserted after the Task-4 `forwarded=` echo at line 281. Nothing in the Task-4 block (199–284) is modified. The Task-6 placeholder comment survives.

**6. Out-of-scope list respected.** `git diff --stat 9edb259..e7d5fe1` = exactly 2 files, 148 insertions, 0 deletions. All three declined Task-4 cleanups (`max(0, …)` label slice at :274, surrogate `try`-wrap at :250-251, `mkdir` gating at :221) are untouched. `sdd-pre-dispatch-hook.sh`, the hook baseline, SDD `SKILL.md`, `verify-symlink-install.sh`, `spawn_handoff_helpers.py`, the plan files, and `context-observations.log` are all absent from the commit. `deviations.md` rows were added by the controller outside this commit — correct ownership.

**7. `_successor_cmd` `lines[0]` — safe, no first-vs-last significance.** `[spawn-handoff] successor command: ` is emitted exactly once (`:318`); Task 6's fence adds no second emitter. The only way a second matching line appears is a forwarded arg containing a newline followed by that exact prefix — and even then the genuine line is still first. Minor: an embedded newline would truncate the returned string, a helper-robustness nit with no production impact.

---

## Contract Constraints — the three Task 5 owns

| Constraint | Verdict | Evidence |
|---|---|---|
| `--handoff-contract` prints `1` **exactly**; string equality, not `-ge` | **Compliant** | `:295` `[ "$(claude-picker --handoff-contract 2>/dev/null)" = "$PICKER_CONTRACT" ]`. Uses the shared `PICKER_CONTRACT` constant (`:35`), never a literal. Discriminating test: stub echoing `2` → `picker-manual` (a `-ge` would have admitted it). Command substitution trims trailing newlines only, not arbitrary whitespace — but the failure direction is **safe** (unexpected probe output degrades, never false-auto). |
| Version predicate is `-f` **AND** `-x`, not lenient `-e` | **Compliant** | `:292` `{ [ -f … ] && [ -x … ]; } \|\| return 1`. Mirrors the picker's `find -type f -perm -u+x`. |
| Compose-side quoting of **every** interpolated element | **Compliant** | `shq()` (`:302`, `shlex.quote`) applied to the version, the label, every `FORWARDED` element, `/pickup <id>` (both branches), and `$SPAWN_LOG`. Verified by live run, not inspection. `--telemetry`'s value is correctly not `shq`'d — it is script-derived `on`/`off` and §5.4c enumerates only version/label/forwarded-args. |

**No regression to the Tasks 1–4 constraints.** Worktree-invariant repo identity, no-eval `v1:` decode, `APPEND_PROMPT` substitution, telemetry mapping, quota fail-open, hop reservation, and the 255 label ceiling are all outside the added hunk and untouched. Corrupt-`v1:` degradation is *consumed* correctly here (`ARGS_OK=1` is a preflight precondition), which is the intended enforcement point for "never a silent arg-drop on auto".

---

## Independent empirical verification (beyond the controller's two mutations)

- **Live composed command with hostile argv** — quoting holds; shown above.
- **`claude-picker` absent from PATH** (the one preflight condition with **no** test): correctly yields `launch=picker-manual` + `successor command: claude-picker '/pickup b1'`, exit 0. Implementation is correct.
- **Telemetry absent, otherwise complete**: correctly yields `launch=auto` with `--telemetry off`. Implementation is correct.
- **Full unit suite**: `594 passed` — matches the report's claim exactly.
- **bash 3.2 floor**: re-ran the 41-test file with `bash` shimmed to `/bin/bash 3.2.57` → **41 passed**. The 3.2-sensitive constructs (multiline `local parts=(…)`, `parts+=`, `"${FORWARDED[@]}"` on an empty array with no `set -u`) hold. Claim verified.
- **CLAUDE.md claim verified, not trusted**: `find skills/subagent-driven-development tests -name CLAUDE.md -o -name AGENTS.md` returns nothing. Root `CLAUDE.md` is the only applicable instruction file, and the block honors its gotchas (no `set -u`, no producer piped into `grep -q`, `$PYTHON` for Python calls).

---

## Advisory observations (non-blocking — no defect, no action required for Task 5)

These are **§7 test-matrix gaps the plan omitted**, not missing behavior. Each behavior was verified present and correct, so none is a MISSING requirement. Recorded so Task 6's test-debt sweep can absorb them.

1. **`picker missing` → `picker-manual` is untested.** spec.md:196 lists it explicitly ("metadata absent / version binary missing / **picker missing** / contract probe failing → `launch=picker-manual`"). The harness always installs a `claude-picker` stub and exposes no knob to remove it, so `command -v claude-picker` (`:294`) can never be false in the suite. Behavior confirmed correct by manual run.
2. **`--telemetry off` on the *composed* line is untested.** spec.md:196: "telemetry-off but otherwise-complete metadata → `launch=auto` with `--telemetry off`". `test_telemetry_on_and_off` asserts only Task-4's `telemetry=off` diagnostic, which predates composition. Behavior confirmed correct by manual run.
3. **The `-x` half of the owned version predicate has no discriminating test.** `install_version()` always `chmod 0o755`, and `test_picker_manual_when_metadata_degraded[9.9.9]` fails on `-f` (file absent), never on `-x`. Deleting `&& [ -x … ]` leaves the suite green. Same family as (1)–(2); worth a line because this is a constraint Task 5 *owns*.
4. **Task 6 must actively fix the spawn-id placeholder** — see Q3. Its plan text does not.

## Report completeness

All required sections present and substantive: Status (`DONE_WITH_CONCERNS`), Implementation Summary, Files Changed (2, with per-file descriptions), Source Files Read (5, with line-number anchors spot-checked and found accurate), CLAUDE.md Files Read, Tests, Contract Compliance (8 entries incl. one `not_applicable`), Deviations from Plan (4), Self-Review Findings (5), Concerns (4). Nothing suspiciously empty. The `DONE_WITH_CONCERNS` status is honestly earned — all four concerns are real, correctly triaged, and mirrored into `deviations.md`.

The report's "no fence defect this time" claim is **true** — the Step-2 fence's nested-quoting semantics were independently re-derived and the result executed; the plan fence was correct as written, breaking the Task-3/Task-4 pattern. The `tests: written 6 / passing 6` count is accurate for this task's own tests (7 collected cases due to the 2-way parametrize; the frontmatter constraint `passing ≤ written` is satisfied).
