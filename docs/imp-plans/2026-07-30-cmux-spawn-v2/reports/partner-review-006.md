# Partner Review — Task 6 dispatch quality (rounds 1 and 2)

**Round 1: BLOCKED. Round 2: APPROVED** (after two PLAN amendments + four prompt fixes).
Reviewer: general-purpose subagent (opus), SDD controller-partner protocol. Repo unmodified in both
rounds; all probes in scratchpad / `mktemp` dirs.

## Round 1 — BLOCKED

### B1 (Blocker) — the "Shared test helpers" are Task 6's deliverable and the dispatch never mentioned them
The module section is headed *"added when Task 6 creates the file, consumed by Task 7's tests"*, and
Task 7 Step 1 says they *"must already be in the file"* — but Task 6's own Step 1 block does NOT
contain them and the proposed prompt never mentioned them. An implementer told "implement all 8 steps,
do not improvise beyond them" would ship the file without `import subprocess`, `VENV_PY`, `SUPPORT`,
`_write_report`, `_log`, **breaking Task 7 one dispatch later**. Compounded: the dispatch's own scope
fence pushed AGAINST them (`VENV_PY`/`SUPPORT` are CLI seams, and the fence forbade CLI work), and if
ruff fires, `ruff check --fix` deletes the intentionally-unused `import subprocess` (F401 default-fixable)
while Task 6's tests stay green.

### M1 (Major) — `frontmatter.get("handoff_spawn") or "auto"` is an over-permissive CONSENT BYPASS
**PyYAML is YAML 1.1: bare `handoff_spawn: off` parses to boolean `False`, and `False or "auto"`
silently turns a REFUSAL into spawn-without-asking.** The plan's own Step 6 parenthetical ("an invalid
frontmatter value fails materialization loudly") was factually WRONG for falsy values, because `or`
normalizes before the model ever sees it. Rated Major not Blocker because it is not a live hole:
`plan-validation-gate-hook.sh` runs the Pydantic validator with `$PYTHON` (the venv), which rejects
`handoff_spawn: False` at plan-gate time — defense-in-depth. **But none of the three prescribed
materialize tests exercised `off` at all** — precisely the over-permissive gap Task 5's quality review
found at the CLI and script layers.

### M2 — the hard `686` equality punishes the implementer for doing the right thing (becomes 687 once M1 lands)
### M3 — no e2e baseline handed over, after four vacuous-harness incidents this sprint
### m1 — "top, beside the `_midpoint` import" is self-contradictory (the import is mid-file, ~line 59)
### m2 — "match `_midpoint.py`'s style" vs "add no annotations" reads as a conflict; `_midpoint.py` DOES annotate (3.9-safely)
### m3 — Step 2's red state is a collection ERROR, not a FAIL (0 tests collected)

## Round 2 — APPROVED

### Round-1 closure

| ID | Closed? | Evidence |
|---|---|---|
| B1 | **Yes** | Prompt names the section heading verbatim, gives placement ("after Step 1's `SCRIPTS` assignment" — correct, `SUPPORT` references `SCRIPTS`), flags the unused-import hazard. `VENV_PY`'s path arithmetic verified to resolve to the real `.venv/bin/python3`. |
| M1 | **Yes — EMPIRICALLY** | Applied the amended Step-6 patch to a sandbox copy of `materialize-manifest.py` and ran all four cases: default → exit 0, `{'expected_hops': 2, 'spawn_policy': 'auto'}`; `"off"` quoted → exit 0, `'off'`; `ask` → exit 0; **bare `off` → exit 1, `Manifest validation failed: 1 validation error for SddSession / handoff.spawn_policy`**. Three exit-0 cases are the positive control proving the exit-1 discriminates. |
| M2 | **Yes** | Re-counted independently: Step 1 = 3+4+1+1 = **9**; Step 5 = **4**; 674 + 13 = **687**. |
| M3 | **Yes** | Ran e2e at HEAD: `E2E PIPELINE PASS - 15 steps composed correctly`. |
| m1 | see disposition | **Controller disposition (recorded here per round 2's request): ACTIONED anyway** — the prompt now says "mid-file, ~line 59, beside the `_midpoint` import, NOT the file top" and explicitly notes the plan's inline comment says "top". Round 1 rated it no-change-needed; actioning it was free. |
| m2 | **Yes** | "Plain annotations are FINE" is correct — `_midpoint.py` has `def compute_midpoint(start: int, end: int) -> int:` and passes. |
| m3 | **Yes** | Reproduced: module-scope bad import → `ERROR`, `Interrupted: 1 error during collection`, 0 collected, no FAIL line. |

### Plan-amendment verification
- **Line budget re-measured, not trusted:** Task 6 spans 254-450 → **197 lines**, under 200.
- **Gate PASS / 0 warnings / 0 blockers** on all five files, run from the repo root with an explicit `cd`.
- **The fourth test pins both halves and `_mf(ok=False)` works as written.** `run_materialize` returns a
  dict and does not raise internally, so `assert (r["exit_code"] == 0) is ok` and
  `return r["manifest"] if ok else r` both resolve. The failure mode is the RIGHT one, not merely
  non-zero: `materialize-manifest.py` never validates through the `Plan` model (it reads raw
  frontmatter), so bare `off` survives as `False` to `SddSession(...)`, is caught by the
  `except ValidationError`, prints `Manifest validation failed:` and returns 1.
- **The plan's reference code EXECUTES.** Extracted Step 3 + Step 1 verbatim into a sandbox → **9 passed**.
  Ran the real `check_python39_compat` against it with a deliberately-bad control alongside: control
  produced 2 FAILs (union syntax, builtin generic), the plan's code produced PASS. **B7 compliance of
  the plan's code is proven, not assumed.**
- `"handoff": null` confirmed live at HEAD (line 38 of a fresh manifest) — the discharge is real work.
- No golden-shape regression risk: no exact-dict / `keys()` / `sorted()` manifest comparisons exist.

### New findings (all actioned into the dispatch)

**J1 (Major, conditional) — the prompt specifies a status WORD but not the report ARTIFACT.** It never
mentions `reports/task-006-implementer-report.md`, the required YAML frontmatter, or `deviations.md`.
`validate-report.py` hard-FAILs a report without frontmatter, and Check 4b turns that into a hard BLOCK
on Task 7's dispatch. **Controller disposition: NOT a blocker here — this fork's controller persists
the report on the subagent's behalf** (as it did for Tasks 4 and 5), copying the strict frontmatter
shape from `implementer-prompt.md`. Confirmed rather than assumed; no prompt change needed.

**N1 (Minor) — the amendment introduced a code fence that is not valid Python.** Compressing Step 6 to
buy 2 lines merged a module-level import and function-body-indented lines into ONE fence. An implementer
told "copy it exactly" can paste it and hit `IndentationError`. Task 6 has only 3 lines of headroom, so
this was fixed **in the prompt**, not by re-splitting the fence.

**N2 (Minor) — `ruff check --fix` will strip THREE names, not one.** `HOP_DIVISOR` and `CEILING_FACTOR`
are imported by Step 1's test file and used by NONE of the nine tests (only `CEILING_FLOOR` is
referenced). Measured: `ruff check --fix` on the plan's verbatim test file → `Found 2 errors (2 fixed)`.
With `subprocess`, three names at risk.

**N3 (Minor) — the ruff hazard is MORE live than the prompt implied, and the regression baseline shifts.**
(a) `ruff` is not on `PATH`, but `pre-commit-format.sh` has a second lookup at
`$HOME/Library/Python/3.9/bin/ruff` **which exists on this machine** — so it IS wired. Task 5 touched
two files with no unused imports, so "didn't fire" was **"found nothing," not "wasn't wired."** Task 6
gives it something to delete. (b) `validate-all-skills.py` will report **`PASS: 160`, not 159** —
category 8 emits one PASS per scanned `.py` and Task 6 adds a file to the scanned directory.

**N4 (Nit) — "there is no `tmp_path` fixture in that file" is true-but-misleading.** `tmp_path` is a
pytest builtin available everywhere; what's absent is its USE in that file's house idiom. Task 7's tests
land in the file Task 6 creates and use it heavily.

### Controller disposition
All actioned before dispatch: N1 (fence has two destinations), N2 (all three names), N3 (expect the hook
to fire; expect `160/0/2`), N4 (reworded), m1 (recorded above), J1 (confirmed, no change).
