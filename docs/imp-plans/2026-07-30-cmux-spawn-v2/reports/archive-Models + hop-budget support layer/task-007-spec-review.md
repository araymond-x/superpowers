# Task 7 — Spec Compliance Review (`83a9ccf`)

**Verdict: PASS**

The landed code is the plan's Step 3 text. The reviewer diffed it **mechanically rather than by
eye**: it extracted the fenced `Step 3: Implement` block from `module-2-models-budget.md` and
unified-diffed it against `_handoff_support.py:72-176`. The **only** differences are whitespace
statement-splits — **no token in any expression differs, including the consent line.** The test
file diff is the seven planned tests verbatim plus the one authorized R3-1 token.

## Evidence

**1. `count_tasks_done` vs Contract Constraints** — every clause holds: frontmatter must parse to a
dict (`_frontmatter` returns `None` otherwise) **and** `status in ("DONE","DONE_WITH_CONCERNS")`;
`task_type` is never consulted, so a verification report with `files_changed: []` counts; the
frontmatter-less `task-005-…` file is excluded (filenames never count); both `reports/` and
`reports/archive-*/` are globbed; accumulation into a `set` dedupes. Both `TestTasksDone` tests are
the plan's, unweakened.

**2. `stall_streak`** — trailing consecutive outcome records equal to the current count; `0` on
no-log / no-outcomes / progress; `'indeterminate'` only when the **newest** outcome lacks
`tasks_done=` (the `streak == 0` guard). Matches spec and the plan's three tests.

**3. `_cli` — the consent branch is byte-faithful.** The
`print(pol if pol in ("auto","ask","off") else ("auto" if manifest is not None else "ask"))` line is
character-identical to the plan, and both `manifest = None` assignments (the `except` and the
non-dict guard) are `None`, **not** `{}` — the implementer correctly implemented the plan over the
superseded R3-2 register token. Independently exercised on the installed CLI: `off`→`off`, JSON
list→`ask`, malformed JSON→`ask`, missing file→`ask`, readable-no-block→`auto`. Usage errors (no
subcommand / bad subcommand / missing required arg) all exit 2; every value path exits 0.
`stall-streak` on a malformed newest record prints `indeterminate` at exit 0.

**4. `ImportError` degradation is real, verified WITH A POSITIVE CONTROL** —
`PYTHONPATH=<dir with a yaml.py that raises ImportError>` + one report present → `unknown`
(control: yaml present → `1`). **Important correction the reviewer surfaced: `/usr/bin/python3` on
this machine DOES ship PyYAML**, so "a bare venv-less invocation" is not a valid probe for this
path. See the P7-3 row.

**5. Scope** — `git show --stat 83a9ccf`: exactly 2 files, **177 insertions / 1 deletion**, matching
the post-`--no-verify` expectation. `HOP_DIVISOR` and `CEILING_FACTOR` are present on the test
file's import line. `git status --porcelain` shows only the two hook-written logs — no stray third
file.

**6. Numbers — all three reproduced independently.** `test_handoff_support.py` → **26 passed**;
`tests/unit/` → **704 passed** (162s); `validate-all-skills.py` → **PASS 160 / FAIL 0 / WARNING 2**.
(Controller's own independent run also returned 704 passed in 157.69s — three concordant
measurements.)

**7. SSOT (AC4)** — swept with `/usr/bin/grep`, **positive-controlled** (the control returned the
`2.5` line). The literal `2.5`, `HOP_DIVISOR`, `CEILING_FLOOR`, `CEILING_FACTOR`, the precedence,
`count_tasks_done` and `stall_streak` exist in exactly one production file.
`materialize-manifest.py` imports `expected_hops` from it; all other hits are the Pydantic field
name or test data.

## Module 2 Acceptance Criteria

| AC | Verdict |
|---|---|
| 1. `Plan.handoff_spawn` default `auto` | Met — `Literal[...] = "auto"`; the 704-test suite green means all pre-existing plan fixtures still validate |
| 2. Optional `SddSession.handoff` | Met — `Handoff \| None = None` (PEP-604 correct **here**; that directory is not py39-scanned) |
| 3. `materialize-manifest.py` writes the block | Met — with the `is None` (not `or`) guard the Contract Constraints demand |
| 4. Formula / precedence / tasks_done / stall SSOT | Met (sweep above) |
| 5. `unknown` / `indeterminate` as values at exit 0 | **Met for every path the plan's Step 3 text specifies.** Not unconditionally green: the empty-`reports/` + no-PyYAML path prints `0`. That is a **plan defect**, already filed as **P7-3** — confirmed plan-faithful, not re-filed |
| 6. Full unit suite + e2e 1-13 | Met — 704 passed; e2e `PASS - 15 steps`, exit 0 |

## Non-findings (recorded, not filed)

- **Deviation-ledger arithmetic.** The implementer's report says "two `print(...); return 0`
  one-liners split." The actual count is **three** print-splits (`stall-streak`, `expected-hops`,
  `spawn-policy`) plus the compound `if not isinstance(manifest, dict): manifest = None`. Purely
  cosmetic; the mechanical diff proves nothing else moved.
- **`spawn-policy` on a readable manifest with an invalid value** (`"bogus"`, `"OFF"`) prints
  `auto`. Reproduced independently; byte-faithful to the plan and already covered by **P7-1(ii)**.
- **Checkbox bookkeeping**: Task 7's Steps 1-5 and the six Module 2 ACs were still `- [ ]`.
  Controller-side close-out, flagged so it is not lost at the module transition.

**No planned behavior is absent or weakened, nothing beyond the two owned files was touched, and
every reported number reproduces.**
