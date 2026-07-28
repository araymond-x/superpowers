# Task 8 — Spec Compliance Review

**Verdict: PASS** (2 advisory notes, no fix required)

---

PASS

## Verification method

Reviewed `git diff 80a118e..7a46dae` (4 files) in full, read the current `spawn-handoff-session.sh`
regions, `tests/unit/spawn_handoff_helpers.py` (unchanged), `tests/unit/conftest.py`, and the
implementer report. Ran the full suite and four mutations myself.

**Full suite at HEAD `7a46dae`:** `.venv/bin/python3 -m pytest tests/unit/ -q` → **625 passed** in
145s (616 pre-existing + 9 new). Confirms the Step-4d autouse fixture did not break the other 616.

## Mutations I re-ran (script restored by copy from a pre-mutation snapshot; `git diff --name-only` verified clean after each — no `git stash` used)

| ID | Mutation | Observed |
|---|---|---|
| **M1** | Removed the `if !` guard on the `.handoff-hops` write | **RED** — `test_hops_write_failure_exits_3_without_spawning` FAILED. Critically, the captured stderr shows the *intent*-write warning WAS emitted and rc was still 3; the test failed anyway because `_reservation_warning_lines(r, "cannot record hop")` returned `[]`. This is direct proof the implementer's own hollow-assertion fix works: leg A discriminates the hops branch specifically, not "some exit-3 with instructions". |
| **M2** | Removed the `if !` guard on the intent-log append | **RED** — `test_intent_write_failure_exits_3_without_spawning` FAILED (leg A still passed, so the two legs are independently pinned). |
| **M6** | `{ [ -f … ] && [ -x … ]; }` → bare `[ -x … ]` at `:309` | **RED** — `test_version_installed_as_directory_degrades_to_picker_manual` FAILED; the mutated run's stderr reads `launch=auto … (no hop increment, no spawn)`. |
| **M7** | `^[0-9]+(\.[0-9]+)?$` → `^[0-9]+$` | **RED, both legs** — `..._is_accepted` (warning fired) and `..._threshold_is_honoured` (rc 3, `quota=low:13.0 below threshold`). The 13.0 leg flips an outcome, so MX-B is a genuine behavioral discriminator, not an absence check. |

**MX-A positive control specifically verified.** `preflight_ok()` is a five-way AND, so I checked both
directions: (a) the control leg is asserted inside the passing test
(`assert "launch=auto" in (r2.stdout + r2.stderr)`), and it passes at baseline with the *only* delta
being `rmdir` → `install_version`; (b) under M6 the primary leg itself reaches `launch=auto`. Both
directions agree that `-f` is the sole discriminator in that fixture.

## Contract compliance (verified by reading code, not tests)

- **Exit ladder 0/3/1 frozen** — `grep -n "exit [0-9]"` over the script yields only 0, 1, 3. The
  `exit 4` token at `:242` is inside a Python comment in the heredoc and predates Task 8. The new
  `sys.exit(5)` at `:261` is **genuinely decoder-internal**: it lives in the `"$PYTHON" - <<'PY'`
  block whose result the shell consumes only as `if [ $? -ne 0 ]; then ARGS_OK=0`. It cannot surface
  as a script exit code. Both new reservation branches call `print_manual_instructions` **before**
  `exit 3`. ✔
- **No `set -u`/`set -e`/`pipefail`** — `grep -n "set -"` returns only two comment lines (`:6`, `:442`). ✔
- **`sdd-pre-dispatch-hook.sh` and `tests/ARaymond-hook-baseline/baseline.txt`** — not in the diff. ✔
- **`tests/unit/spawn_handoff_helpers.py`** — not in the diff (READ-ONLY honored). ✔
- **Version predicate** — `:309` is still the `-f` **AND** `-x` conjunction, unweakened; M6 proves the
  test pins it. ✔
- **Reserve-before-spawn** — reservation block at `:440-456` precedes `spawn_claude_workspace` at
  `:458`. ✔
- **Shared constants** — `QUOTA_MIN_PCT_DEFAULT=15` / `MAX_HOPS:-3` untouched, not re-literalled
  anywhere in the diff. ✔

## Step-by-step coverage

- **Step 1** ✔ Both writes checked; discriminating triple present in both legs: distinctive warning
  (prefix `[spawn-handoff] reservation write failed:` + branch needle), `rc == 3`, and
  `assert "new-workspace" not in _cmux_log_text(...)` reading the **stub's recorded argv**, not
  stdout. Leg A uses an existing reports dir at `chmod 0555` (not a missing dir under an unwritable
  parent), so it exercises the write, not the `mkdir`. Leg B's EISDIR fixture does exactly what is
  claimed — I confirmed `.handoff-hops` is asserted `== "1"`, i.e. the first write succeeded and only
  the second failed.
- **Step 2** ✔ `assert "Spawn failed after reservation" in _notify_line(tmp_path)` — `_notify_line`
  parses `cmux.log`, so this is immune to the test-echo collision class.
- **Step 3** ✔ `mktemp` stubbed via `tmp_path/"stubs"`, which `run_spawn` **prepends** to `PATH` —
  non-vacuous. Two legs: uncaptured spawn (rc 0, `workspace=(spawned)`) and rc propagation (cmux
  `exit 5` → script exit 3, hop consumed).
- **Step 4** ✔ `max(0, …)` at `:286` with a test pinning "no fragment of the old base leaks";
  lone-surrogate `try`-wrap; Task-6 `mkdir` sub-item explicitly declared as needing nothing, **no
  invented test** — exactly as instructed.
- **Step 4b** ✔ Both residuals covered (see M6/M7).
- **Step 4c** ✔ Decision stated and reasoned in-code at `:310-313` (**KEEP**, because spec §5.4c
  enumerates PATH resolution as its own predicate) and in the report. Requirement was to decide
  explicitly, not to pick a particular side.
- **Step 4d** ✔ Exactly **one** `PICKER_ENV_VARS` definition (`conftest.py:23`);
  `test_spawn_handoff.py` only references it in a pointer comment. `conftest.py` imports only `sys`,
  `pathlib`, `pytest` — **no test module**. The explanatory comment survived and was extended. The
  `MODELS_DIR` `sys.path.insert` is preserved above the new code. Fixture demonstrably applies to
  `test_spawn_handoff.py` (all its env-absence tests still pass at HEAD).
- **Step 5** ✔ I diffed the plan-doc snippet against `git show 7131698:…` — the replacement
  `check_quota` block is **verbatim identical** to the shipped implementation. Bash caveat corrected
  4.x → **≥ 3.2** with the `set -u`/`${FORWARDED[*]}` rationale. Task 6 Step 2 spawn-id line removed
  with a §5.4d note — verified against the script: `SPAWN_ID=` at `:349`, `SUCCESSOR_CMD=` compose at
  `:365`, so generation genuinely precedes the compose block. **No checkbox state changed**:
  `git diff … | grep -E "^[-+].*- \["` shows a single `[x]` → `[x]` pair differing only in the
  trailing annotation.
- **Steps 6-7** ✔ Suite green (my own run); `bash -n` OK; `shellcheck --severity=warning
  --external-sources` on the script → **CLEAN**; hook + baseline untouched.

## Report completeness

All required sections present and substantive: Status, Implementation Summary, Files Changed, Source
Files Read, CLAUDE.md Files Read, Tests, Contract Compliance, Deviations (6, incl. the honest
`sys.exit(5)` disclosure), Self-Review Findings (5), Concerns (5). No empty sections. The report's
self-caught hollow assertion is corroborated by my M1 run.

## Advisory notes (non-blocking, no fix required)

- `[ADVISORY] [EXTRA]` — `scripts/lint-shell.sh` printed **"No shell files found."** on this working
  tree, i.e. the Step-6 lint was **vacuous** (it selects changed-vs-base files and matched none
  post-commit). Not an implementer defect and not a gap in coverage — I lint-checked the script
  directly (`shellcheck` clean, `bash -n` OK) — but the controller should not read "lint passed" as
  evidence the harness examined this diff.
- `[ADVISORY] [EXTRA]` — `tests/unit/conftest.py` is a 4th file beyond the plan's Files list.
  Declared as Deviation 1 with sound reasoning (Step 4d mandates the edit; the plan's file list is
  the defect). Committing it is entailed, not scope creep.

---

## Controller verification of this review

Both advisory notes independently re-checked:

```
$ bash scripts/lint-shell.sh
No shell files found.
$ shellcheck --severity=warning --external-sources .../spawn-handoff-session.sh   # rc=0, CLEAN
$ /bin/bash -n .../spawn-handoff-session.sh                                       # OK
$ /bin/bash --version | head -1
GNU bash, version 3.2.57(1)-release (arm64-apple-darwin25)
```

The vacuous-lint finding is **confirmed**. The substantive property still holds — `shellcheck` is
clean and `bash -n` passes — and note the syntax check ran under **3.2.57**, which is the plan's
verified bash floor, so that leg is stronger than the harness would have been. What is retracted is
only the *evidentiary value* of Step 6's lint line, not the script's cleanliness. Logged to
`deviations.md`.
