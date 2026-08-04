# Module 4 — Co-located hook papercuts + baseline recapture

**Goal:** Ship the three co-located papercuts while the files are open — N84 (`$BID` regex-unsafe grep), N86 (checkpoint-prerequisite gate swallows a genuine FAIL), N85 (mechanics-card display inconsistencies) — plus an AUTOSPAWN e2e step, doc maintenance, and a full-suite verification. N84 and N86 both edit `sdd-stop-hook.sh` (baselined), so they are ONE task with ONE baseline recapture.

**Source Contracts:** None

(See the parent plan; `spec-distilled.md` §C5. The bug sites were verified during orientation.)

**Contract Constraints:**
- `sdd-stop-hook.sh` is **baselined** — Task 11 re-captures `baseline.txt` in the same commit. `write-mechanics-card.py` is **not** baselined.
- N86 fix: the gate must key off emptiness ALONE (`-z "$CHECKPOINT_OUTPUT"`), dropping the `[ $? -ne 0 ] ||` disjunct — a real infra crash prints to stderr (stdout empty), so `-z` still guards it. The pre-written `xfail(strict=True)` test `test_composes_with_checkpoint_fail_message` (`tests/unit/test_honesty_log_capture.py`) asserts the FIXED behavior — it MUST be un-`xfail`ed in the same change (strict xfail → XPASS failure once fixed).
- N84: `$BID` must be regex-escaped before interpolation into `grep -qE` (the pattern needs alternation/anchors/`.*`, so plain `grep -qF` cannot replace it). Bundle ids are validated `^[A-Za-z0-9_.-]+$`, so `.` is the live metachar.
- N85: card display must match the script — `{sys.executable}` (not literal `$PYTHON`) and the script's validated `MAX_HOPS` value (numeric-or-derived-default).
- Declared `integration_test: tests/integration/sdd-e2e-test.sh` must be modified in this feature's changeset (C2 Check 10) — Task 13's e2e step satisfies it.

**Pattern References:**
- `tests/unit/test_honesty_log_capture.py` — `TestSpawnOutcomeWarning` (N84 matching behavior) + the N86 xfail tripwire (Task 11).
- `tests/integration/sdd-e2e-test.sh` — the Step-14 stub structure for the AUTOSPAWN e2e step (Task 13).

## File Map

| File | Responsibility |
|------|----------------|
| `skills/subagent-driven-development/scripts/sdd-stop-hook.sh` | N84 grep escape (line ~89) + N86 fail-closed gate (line ~181) (Task 11) |
| `tests/unit/test_honesty_log_capture.py` | Un-xfail N86 test + add N84 metachar test (Task 11) |
| `tests/ARaymond-hook-baseline/baseline.txt` | Re-capture after Task 11 |
| `skills/subagent-driven-development/scripts/write-mechanics-card.py` | N85 sys.executable + validated ceiling (Task 12) |
| `tests/unit/` card test | N85 coverage (Task 12) |
| `tests/integration/sdd-e2e-test.sh` | AUTOSPAWN precondition e2e step (Task 13) |
| `CLAUDE.md` (+ manifest if warranted) | Doc maintenance (Task 13) |

## Write-Scope Partitioning

| Task | Owned Files (write) | Read-Only | Depends On |
|------|---------------------|-----------|------------|
| Task 11 | `sdd-stop-hook.sh`, `tests/unit/test_honesty_log_capture.py`, `tests/ARaymond-hook-baseline/baseline.txt` | controller-checkpoint.py | Task 10 |
| Task 12 | `write-mechanics-card.py`, card test file | `_handoff_support.py`, spawn-handoff-session.sh | Task 11 |
| Task 13 | `tests/integration/sdd-e2e-test.sh`, `CLAUDE.md`, `docs/ARaymond-customization-manifest.md` | all changed files | Task 12 |

> **Serialization note:** `tests/ARaymond-hook-baseline/baseline.txt` was owned by Task 7 (Module 3) and is owned by Task 11 here. Sequential module order (M3 before M4) guarantees this. Task 11's recapture re-pins ALL seven hook hashes, correctly keeping Task 7's updated pre-dispatch hash.

---

### Task 11: sdd-stop-hook.sh — N84 grep escape + N86 fail-closed gate + un-xfail (baselined, recapture)

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-stop-hook.sh` (line ~89 grep, line ~181 gate)
- Modify: `tests/unit/test_honesty_log_capture.py` (un-xfail one test, add N84 metachar test)
- Modify: `tests/ARaymond-hook-baseline/baseline.txt` (recapture — same commit)

**Pattern References:** `stop-hook-tests`, `regen-check-hooks-baseline`.

- [x] **Step 1: Un-xfail the N86 fixed-behavior test + write the N84 metachar test**

In `tests/unit/test_honesty_log_capture.py`:
(a) Remove the `@pytest.mark.xfail(strict=True, reason=...)` decorator from `test_composes_with_checkpoint_fail_message` (it already asserts the FIXED behavior: a checkpoint FAIL + unmatched bundle land in one `systemMessage` containing both).
(b) Add an N84 metachar test to `TestSpawnOutcomeWarning` (a `.` in the this-session bundle id must NOT match a DIFFERENT bundle's outcome record):

```python
def test_bundle_id_metachar_does_not_false_match(self):
    tmpdir, home, vault_dir = self._new_dirs()
    try:
        _clean_workspace(tmpdir)
        transcript = os.path.join(tmpdir, "transcript.jsonl")
        _write_transcript(transcript)
        repo_id = _repo_id_for(tmpdir)
        # This-session bundle id contains a regex metachar '.'
        bid = "2026-07-30T00-00-00Z-test.bundle"
        _write_bundle(home, bid, repo_id)
        # A DIFFERENT bundle's outcome record that would match if '.' were unescaped
        _append_spawn_log(
            os.path.join(tmpdir, "reports"),
            "2026-07-30T00:00:01Z uuid-1 outcome hop=1 workspace=w surface=s "
            "launch=auto bundle=2026-07-30T00-00-00Z-testXbundle quota=ok "
            "tasks_done=0 handshake=ok",
        )
        result = _run_stop_hook(tmpdir, vault_dir, transcript_path=transcript, home=home)
        assert result.returncode == 0, result.stderr
        # The warning MUST still fire — the decoy record is for a different bundle.
        assert bid in json.loads(result.stdout).get("systemMessage", "")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
        shutil.rmtree(home, ignore_errors=True)
        shutil.rmtree(vault_dir, ignore_errors=True)
```

- [x] **Step 2: Run to verify failure**

Run: `.venv/bin/python3 -m pytest tests/unit/test_honesty_log_capture.py -k "composes_with_checkpoint_fail or metachar" -v`
Expected: `test_composes_with_checkpoint_fail_message` FAILs (gate still swallows the FAIL; was xfail, now live) and `test_bundle_id_metachar_does_not_false_match` FAILs (unescaped `.` false-matches the decoy).

- [x] **Step 3: Fix N86 — drop the `$? -ne 0` disjunct**

In `sdd-stop-hook.sh`, change the checkpoint-prerequisite gate (line ~181) from:

```bash
if [ $? -ne 0 ] || [ -z "$CHECKPOINT_OUTPUT" ]; then
  exit 0
fi
```

to:

```bash
# Key off emptiness ALONE. controller-checkpoint.py prints its JSON to stdout
# BEFORE choosing an exit code and returns 1 on status=FAIL / 2 on advisory
# WARNING — so a non-zero exit with non-empty output is a real gate result that
# must be surfaced below, not swallowed. Only a genuine crash (except-path prints
# to stderr) leaves stdout empty; that alone is the don't-block case.
if [ -z "$CHECKPOINT_OUTPUT" ]; then
  exit 0
fi
```

- [x] **Step 4: Fix N84 — regex-escape `$BID`**

In `sdd-stop-hook.sh`, just before the `grep -qE` at line ~89, compute a regex-safe bundle id and use it:

```bash
    # Regex-escape $BID: it is interpolated into an ERE below, and a validated
    # bundle id may contain '.', which would otherwise match any char (N84).
    BID_RE=$(printf '%s' "$BID" | sed 's/[][\\.^$*+?(){}|/]/\\&/g')
    if [ -f "$SPAWN_LOG_FILE" ] && grep -qE "( outcome .*bundle=$BID_RE( |$))|( decline bundle=$BID_RE( |$))" "$SPAWN_LOG_FILE"; then
```

(Keep the existing surrounding lines; only `$BID`→`$BID_RE` in the grep pattern plus the `BID_RE=` line change. Note: the original used `\$` inside the double-quoted string for the end-anchor; `( |$)` is equivalent and clearer — verify the anchor still matches end-of-line in your final form with the metachar test.)

- [x] **Step 5: Run to verify pass**

Run: `.venv/bin/python3 -m pytest tests/unit/test_honesty_log_capture.py -v`
Expected: all PASS (including the un-xfailed test and the new metachar test; no XPASS).

- [x] **Step 6: Re-capture the hook baseline (SAME commit)**

Run: `bash tests/ARaymond-hook-baseline/check-hooks.sh --capture`
Run: `bash tests/ARaymond-hook-baseline/check-hooks.sh` (verify in-sync).

- [x] **Step 7: Commit (hook + tests + baseline together)**

```bash
git add skills/subagent-driven-development/scripts/sdd-stop-hook.sh tests/unit/test_honesty_log_capture.py tests/ARaymond-hook-baseline/baseline.txt
git commit -m "fix(n84,n86): regex-escape \$BID + fail-closed checkpoint gate; un-xfail tripwire (baseline recaptured)"
```

---

### Task 12: write-mechanics-card.py — N85 sys.executable regen line + validated MAX_HOPS ceiling

**Files:**
- Modify: `skills/subagent-driven-development/scripts/write-mechanics-card.py` (lines ~76, ~93)
- Test: the existing card test (find it: `/usr/bin/grep -rln "write-mechanics-card\|handoff-mechanics\|mechanics_card" tests/unit/`)

- [ ] **Step 1: Write/extend the failing test**

Assert card↔script consistency:

```python
def test_card_regen_line_uses_real_interpreter(...):
    card = _render_card(...)  # use the file's existing render helper
    assert "$PYTHON " not in card                 # no literal $PYTHON in the regen line
    assert sys.executable in card                 # resolved interpreter, like the checkpoint lines

def test_card_ceiling_validates_max_hops(...):
    # Invalid env value -> card shows the derived default (matches the script's revert)
    card = _render_card(..., env={"SUPERPOWERS_CMUX_MAX_HOPS": "banana"})
    assert "ceiling: banana" not in card
    # Valid numeric -> card shows it
    card = _render_card(..., env={"SUPERPOWERS_CMUX_MAX_HOPS": "9"})
    assert "ceiling: 9" in card
```

Adapt to the file's actual render entry point and how it captures env.

**Pre-execution audit note (Order 2):** `tests/unit/test_mechanics_card.py`'s `_run_card(wt, feat)` (line ~34) currently strips **all** `SUPERPOWERS_CMUX_*` env vars by design before invoking the script (comment: ambient knobs would skew the card's ceiling line) — every existing call site (`test_card_deterministic_with_contents`, `test_report_skeleton_passes_validate_report`, etc.) relies on that isolation. Extend `_run_card`'s signature with an `env_extra=None` parameter, merged in **after** the ambient-strip, so the new ceiling tests can inject `SUPERPOWERS_CMUX_MAX_HOPS` without breaking that isolation guarantee for existing callers. Do not add a plain unfiltered `env=` passthrough — it would leak ambient `SUPERPOWERS_CMUX_*` values into every other test in the file.

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python3 -m pytest tests/unit/ -k "card and (regen or ceiling)" -v`
Expected: FAIL (literal `$PYTHON`; unvalidated ceiling shows `banana`).

- [ ] **Step 3: Fix the ceiling (validate like the script)**

In `write-mechanics-card.py`, change the `ceiling` computation (line ~76) from:

```python
    ceiling = os.environ.get("SUPERPOWERS_CMUX_MAX_HOPS") or hop_ceiling(expected)
```

to validate the env value the way `spawn-handoff-session.sh` does (numeric → use it, else derived default). Add `import re` if not present:

```python
    _raw_max_hops = os.environ.get("SUPERPOWERS_CMUX_MAX_HOPS")
    ceiling = _raw_max_hops if (_raw_max_hops and re.fullmatch(r"[0-9]+", _raw_max_hops)) else hop_ceiling(expected)
```

- [ ] **Step 4: Fix the regen line (`$PYTHON` → `{sys.executable}`)**

Change the regen-command line (line ~93) from the literal `$PYTHON` form to `{sys.executable}`, matching the checkpoint lines (~98-99):

```python
`{sys.executable} {Path(__file__).resolve()} --manifest {manifest_abs}`
```

- [ ] **Step 5: Run to verify pass**

Run: `.venv/bin/python3 -m pytest tests/unit/ -k "card" -q`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add skills/subagent-driven-development/scripts/write-mechanics-card.py tests/unit/
git commit -m "fix(n85): mechanics card uses sys.executable + validated MAX_HOPS ceiling"
```

---

### Task 13: e2e AUTOSPAWN step + doc maintenance + full-suite verification

**Files:**
- Modify: `tests/integration/sdd-e2e-test.sh` (add an AUTOSPAWN precondition step)
- Modify: `CLAUDE.md` (cmux auto-spawn section: discoverability + kill switch + N83)
- Modify: `docs/ARaymond-customization-manifest.md` (if a documented inventory entry changed)

- [ ] **Step 1: Add the AUTOSPAWN e2e step**

In `tests/integration/sdd-e2e-test.sh`, add a step (mirror the Step-14 stub structure and its `policy=ask` sub-run) that drives `spawn-handoff-session.sh` with `SUPERPOWERS_CMUX_AUTOSPAWN=0` and asserts exit 3 + `reason=autospawn-disabled` fires **before** the cmux-reachability probe (the refusal message is autospawn-disabled, not cmux-unreachable). Update the run's closing step-count banner if the harness prints one.

- [ ] **Step 2: Run the e2e suite**

Run: `bash tests/integration/sdd-e2e-test.sh`
Expected: all steps PASS, including the new AUTOSPAWN step; closing banner reflects the new count.

- [ ] **Step 3: Doc maintenance**

Update `CLAUDE.md`'s cmux auto-spawn coverage to reflect: (a) auto-spawn is now the documented default with proactive discoverability (SDD SKILL.md + hook messages), (b) the `SUPERPOWERS_CMUX_AUTOSPAWN` kill switch (already added to the env registry in Task 9 — cross-reference, don't duplicate), (c) the N83 unquoted-`off` coercion. Keep edits tight and routing-oriented per the repo's instruction-hygiene rules. Update `docs/ARaymond-customization-manifest.md` only if an inventory entry (scripts/hooks/skills) materially changed.

- [ ] **Step 4: Full-suite verification**

Run all suites and record results:

```bash
.venv/bin/python3 -m pytest tests/unit/ -q
python3 tests/ARaymond-skill-regression/validate-all-skills.py 2>&1 | tail -6
bash tests/ARaymond-installation/verify-symlink-install.sh 2>&1 | tail -4
bash tests/integration/sdd-e2e-test.sh 2>&1 | tail -4
bash tests/ARaymond-hook-baseline/check-hooks.sh
```

Expected: unit all PASS (prior 849 + new tests, 1 xfailed becomes 0 xfailed since N86's xfail was removed — confirm the count); regression no new FAIL; install PASS; e2e all steps PASS; hook baseline in-sync.

- [ ] **Step 5: Commit**

```bash
git add tests/integration/sdd-e2e-test.sh CLAUDE.md docs/ARaymond-customization-manifest.md
git commit -m "test(e2e)+docs: AUTOSPAWN precondition e2e step + cmux auto-spawn doc maintenance"
```

## Acceptance Criteria (Module 4)

- [ ] N84: a bundle id containing `.` does not false-match a different bundle's log record (metachar test green); `$BID` regex-escaped.
- [ ] N86: the checkpoint-prerequisite gate keys off `-z "$CHECKPOINT_OUTPUT"` alone; `test_composes_with_checkpoint_fail_message` is un-`xfail`ed and PASSES; a real checkpoint FAIL now surfaces "Pre-Completion Gate FAILED".
- [ ] Hook baseline re-captured in the same commit as the sdd-stop-hook.sh edit; `check-hooks.sh` in-sync.
- [ ] N85: card regen line uses `{sys.executable}` (no literal `$PYTHON`); ceiling validates `SUPERPOWERS_CMUX_MAX_HOPS` like the script (invalid → derived default).
- [ ] e2e has an AUTOSPAWN precondition step (exit 3 `reason=autospawn-disabled` before cmux reachability); the declared `integration_test` is in the changeset (C2 Check 10).
- [ ] All suites green (unit, regression, install, e2e, hook baseline); CLAUDE.md doc maintenance done.
