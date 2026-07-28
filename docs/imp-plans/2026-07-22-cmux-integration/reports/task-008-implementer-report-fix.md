---
schema_version: 1
task_id: 8
task_type: implementation
status: DONE
files_changed:
  - path: "tests/unit/test_spawn_handoff.py"
    description: "FIX 1: replaced the hollow chmod-based fixture in test_hops_write_failure_exits_3_without_spawning with an isolating one (.handoff-hops occupied by a directory => EISDIR on that write alone), so the downstream intent guard can no longer supply the rc 3 and absent spawn; swapped a dead .exists() assertion for leg A's real signature (no intent record). FIX 2: added _decode_warning_lines helper + DECODE_WARN constant, and asserted the new diagnostic in test_lone_surrogate_arg_degrades_without_traceback."
  - path: "skills/subagent-driven-development/scripts/spawn-handoff-session.sh"
    description: "FIX 2: one prefix-anchored warn line inside the decoder's existing rc branch, restoring the diagnostic Task 8's try-wrap removed. FIX 3: softened the hops-failure message from 'no hop consumed' to 'hop not recorded — counter may have been truncated', with a comment explaining the > truncate-at-open partial-failure case."
  - path: "docs/imp-plans/2026-07-22-cmux-integration/module-1-spawn-script.md"
    description: "FIX 4: in-fence annotation on Task 6 Step 2's superseded unchecked reservation pair, pointing at Task 8 Step 1's rc-checked form. No checkbox touched."
tests:
  written: 0
  passing: 0
  command: ".venv/bin/python3 -m pytest tests/unit/ -q"
  result: PASS
contract_compliance:
  - constraint: "Exit-code ladder frozen at 0/3/1"
    status: compliant
    detail: "No exit statement added, removed, or renumbered. Only an echo and message wording changed."
  - constraint: "No set -u / set -e / pipefail"
    status: compliant
    detail: "None added; the script's bash 3.2 ${FORWARDED[*]} empty-array behavior is untouched."
  - constraint: "Do not touch spawn_handoff_helpers.py, sdd-pre-dispatch-hook.sh, baseline.txt"
    status: compliant
    detail: "git diff --name-only on all three returned EMPTY."
  - constraint: "Never use git stash; restore mutations by copy-restore"
    status: compliant
    detail: "Pristine snapshot cp'd to scratchpad; restored by cp after each of 3 mutations, verified by sha256."
  - constraint: "Stage only the script, test file, and module-1 doc"
    status: compliant
    detail: "git diff --name-only --cached showed exactly those 3; no reports/ artifacts staged."
  - constraint: "Out-of-scope items not performed"
    status: compliant
    detail: "No cmux notify on reservation branches, no _cmux_log_text/_notify_line dedup, no mkdir -p check, no temp+mv rewrite."
---

**Implementation Summary:** All four authorized fixes landed in commit `53318b5`. The reason for the
round — a hollow assertion that let the hops guard's `exit 3` be deleted without turning the suite
red — is closed by switching to an isolating fixture, and I re-ran the reviewer's MX1 to confirm it
now fails. FIX 2's diagnostic, FIX 3's wording, and FIX 4's doc annotation are in, with the new
stderr line audited both directions against existing assertions.

**Source Files Read:** `spawn-handoff-session.sh` — the reservation pair at 447-457, the decoder's
`$?` consumption at 265, and `HOPS="$(cat "$HOPS_FILE" 2>/dev/null)"` at 129, which is what makes a
directory fixture safe (cat of a dir yields empty ⇒ `HOPS=0`, so the hop-limit gate is not what stops
the run). `test_spawn_handoff.py` — the prefix-anchoring idiom in `_warning_lines` /
`_reservation_warning_lines`, and leg B's EISDIR technique that FIX 1 mirrors.
`module-1-spawn-script.md:1105-1108` — the superseded snippet.

**CLAUDE.md Files Read:** Project `CLAUDE.md` — the hook-baseline re-capture rule (not triggered; I
touched no baselined hook), the "never pipe into `grep -q` under pipefail" and `set -u` gotchas
(respected), and the direct-`shellcheck`-vs-`lint-shell.sh` note.

**Mutation Proofs:**

- **MX1 (mandatory re-run)** — line 464 `exit 3` → `:` in the hops guard. *Positive control:* printed
  lines 462-470, showing `:` under the hops `echo`/`print_manual_instructions` and `exit 3` still
  intact in the intent guard below. *Result:* **RED** — `AssertionError: assert 0 == 3`. The rc came
  back **0**, not 1, confirming the run reached the guard rather than dying on a precondition; the
  warning assertion above it passed first (the guard still *detects*), so the failure is precisely
  the *stopping* leg. Leg B passed unaffected. *Restored:* `cp` from snapshot, sha256 `edc31c0c…`
  matched pre-mutation.
- **MX2 (leg B under its own mutation)** — line 469 `exit 3` → `:` in the intent guard, positive
  control printed. *Result:* **RED** (`assert 0 == 3`, stderr showing `handoff-spawn.log: Is a
  directory`), with leg A passing. The two legs are now independently pinned.
- **MX3 (FIX 2's added assertion)** — neutralized the new echo (`: echo …`), positive control
  printed. *Result:* **RED** on `_decode_warning_lines`. The failure message is the strongest
  artifact of the round — it dumps the full stderr under the mutant: `quota=ok:63.0 / forwarded=
  label=[…] / launch=picker-manual / successor command: … / --dry-run: …`. That verbatim output shows
  both pre-existing assertions (`"launch=picker-manual" in (stdout+stderr)` and `"Traceback" not in
  stderr`) still held while the diagnostic was absent — direct proof the added assertion
  discriminates rather than duplicating.
- **Restoration verified:** after all three, sha256 `edc31c0c…` and `git diff --stat` = 15 insertions
  / 1 deletion, consistent with exactly the two intended hunks. `git diff --name-only` on the
  do-not-touch trio: **empty**.

**Test-echo collision audit (FIX 2):** Grepped three ways. (a) All 11 `picker-manual` assertions use
the literal `"launch=picker-manual"`; my message says "degrading to picker-manual (forwarded args
dropped)" and contains no `launch=` anywhere, so it cannot satisfy them. (b) Collisions run both
directions — the only negative assertion in the file is `"Traceback" not in r.stderr` (line 1285),
unaffected by a plain warn line. (c) Positional/exact parsers: `_successor_cmd` filters by `MARKER`
prefix rather than line position, so a new line cannot shift it (line 1216's exact-equality assertion
is safe); the `label=\[([^\]]*)\]` regex at 1303 needs a literal `label=[`, absent from my text.
Conclusion: no collision in either direction. Confirmed empirically — full suite unchanged at 625.

**Deviations from Plan:** None. One judgment call inside FIX 1: the reviewer's sketch included
`assert not (…/".handoff-hops").is_file()`, which is dead weight under this fixture (the path is
created as a directory, so it can never be a file). In a round whose purpose is removing hollow
assertions I replaced it with `assert "intent" not in _spawn_log_text(ctx)` — leg A's genuinely
distinguishing signature (nothing reserved at all), mirroring leg B's `hops == "1"` on the other
side. The brief explicitly framed the sketch as "not necessarily literal."

**Self-Review Findings:** Two things worth stating for the next reviewer. First, the FIX 2 echo sits
**inside** the `if [ $? -ne 0 ]` branch, after `[` has already consumed the decoder's status —
placing it before the `if`, or adding `rc=$?` inside the body, would capture `[`'s status instead of
the decoder's. Getting the exit code (3/4/5) into the message would require a `DECODE_RC=$?` line
immediately after `PY`, which is a larger edit on a freezing script; I kept the no-rc one-liner.
Second, `os` remains imported and used (`os.access`, line 66) after FIX 1 removed the last `os.chmod`
calls in that region — no dangling import.

**Concerns:** No concerns.

**Verification run:** `tests/unit/` **625 passed** and `test_spawn_handoff.py` **72 passed** — both
exactly the stated baselines, as expected for a round that adds no test functions. `shellcheck
--severity=warning --external-sources` rc **0** and `/bin/bash -n` rc **0**, run **directly** (not
via `lint-shell.sh`, which selects changed-vs-base and finds nothing post-commit). `validate-plan.py`
on `module-1-spawn-script.md`: **0 blockers**; the 3 warnings (Task 0 and Task 4 exceeding the
200-line limit, no YAML frontmatter) are pre-existing and **Task 6 is not among them**, despite my
annotation adding 4 lines to it. FIX 1's bonus held: leg A no longer depends on `chmod` semantics,
retiring the implementer's own root-binding concern.

---

## Controller verification of the fix round

MX1 independently re-run by the controller with a positive control, at commit `53318b5`:

```
$ grep -n "cannot record hop" spawn-handoff-session.sh      # locate by CONTENT, not line number
462:  echo "[spawn-handoff] reservation write failed: cannot record hop in $HOPS_FILE (hop not
      recorded — counter may have been truncated; no spawn attempted) — manual fallback." >&2
$ sed -i '' '464s/^  exit 3$/  :/' spawn-handoff-session.sh
$ sed -n '461,470p' spawn-handoff-session.sh                 # positive control: `:` replaced exit 3
$ .venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -q
  FAILED test_hops_write_failure_exits_3_without_spawning — assert 0 == 3
  1 failed, 71 passed
$ cp /tmp/spawn-pristine2.sh spawn-handoff-session.sh        # copy-restore, NOT git stash
$ git diff --name-only <script>                              # EMPTY
$ .venv/bin/python3 -m pytest tests/unit/ -q                 # 625 passed
```

**CONFIRMED CLOSED.** Under MX1 exactly ONE test now fails, and it is the right one — leg A — with
`assert 0 == 3`, i.e. the script fell through the hops guard and continued instead of stopping.
Before the fix this same mutation left 72/72 green. Leg B was unaffected, so the two legs are
independently pinned rather than jointly satisfying one condition.

Also verified: `git diff --name-only` EMPTY for `sdd-pre-dispatch-hook.sh`,
`tests/ARaymond-hook-baseline/baseline.txt`, and `tests/unit/spawn_handoff_helpers.py` (the
read-only/do-not-touch set), and the full `tests/unit/` suite is **625 passed** at `53318b5`.
