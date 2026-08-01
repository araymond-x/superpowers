# Task 7 — Controller Partner Review (round 1)

**Verdict: BLOCKED** — one over-permissive defect in the plan's own Step 3 code (the consent
gate), plus one false claim in the dispatch prompt. Everything else verified clean.

This is the **second time on this feature** a partner review has blocked a dispatch by finding an
over-permissive consent bypass in the plan's own code (the first was the Task 6 YAML-1.1 `or`
bypass). Both were fixed in the plan text, not in a dispatch.

## Verified sound (measured by the partner, do not re-run)

| Claim | Result |
|---|---|
| Unit baseline 697 passed | **CONFIRMED** — `697 passed, 1 warning in 154.81s` |
| Regression 160 / 0 / 2 | **CONFIRMED** — `PASS: 160 FAIL: 0 WARNING: 2` |
| Task 7 at 199 lines, cap 200 | **CONFIRMED** — PASS / 0 blockers / 0 warnings; tasks 4/5/6/7 = 47/128/197/**199** |
| Write scope (`_handoff_support.py` + `test_handoff_support.py` own; `implementer_report.py` read-only) | **CONFIRMED** — exact match to the Write-Scope Partitioning row |
| Contract Constraints paragraph | **Faithful** — trims only the Task 5 `Handoff \| None` clause and a trailing rationale; no distortion |
| B9 discharged in plan text | **CONFIRMED** — `_write_report(r, 1, "DONE", task_type="verification", files_changed="[]")` |
| R3-2 discharged in plan text | **CONFIRMED** — `if not isinstance(manifest, dict): manifest = {}` |
| R3-1 carried in prompt | **CONFIRMED** — matches the deviations row in intent; test-only, one token |
| Shared-helper block matches the real file | **CONFIRMED** — plan block == `test_handoff_support.py`, populated `files_changed` default present in both |
| `task_id: int` in `ImplementerReport` | **CONFIRMED** — the `isinstance(tid, int)` guard is correct, not an under-count |
| `validate-report.py --report-file`; bare `python3` has pydantic | **CONFIRMED** (pydantic 2.12.5) |

## BLOCKING — Finding 1: `spawn-policy` returns consent on a manifest it could not read

Plan Step 3, `_cli`: a **missing, unreadable, or corrupt-JSON** manifest lands in `manifest = {}`
→ `pol = None` → prints **`auto`**, the spawn-without-asking value. Simulated against the exact
expressions:

```
{"handoff": {"spawn_policy": "off"}}  -> off
{"handoff": {"spawn_policy": "OFF"}}  -> auto
{"handoff": {"spawn_policy": false}}  -> auto
{"total_tasks":5}                     -> auto     # legit: spec pins absent-block -> auto
```

Three reasons this is a block, not a nit:

1. **It is the sole consent gate.** Module 3 runs `spawn-policy` and refuses only on exactly
   `off`/`ask`. There is no second check downstream.
2. **It contradicts the module's own AC** — "CLI prints `unknown`/`indeterminate` as values
   (exit 0) — degradation is observable." The sibling subcommand on the identical corrupt input
   prints `unknown`. `spawn-policy` had no degraded value: its degradation was invisible *and*
   permissive.
3. **It is the same defect the partner already blocked once on this feature** — an unusable or
   falsy policy silently becoming `auto`.

**Controller note (verified while acting on this):** the defaults also **STACK**. Module 3's
`case "$SPAWN_POLICY" in auto|ask|off) : ;; *) SPAWN_POLICY="auto" ;; esac` independently coerces
any unrecognized value to `auto`, so every failure mode of the gate resolved to "yes."

### Disposition — FIXED in plan text

The spec pins only *"Absent block → `spawn_policy=auto`"* and is **silent on an unreadable
manifest**, so failing closed there fills a gap rather than contradicting a contract.

`ask` was chosen over a new sentinel because a sentinel would be swallowed by module 3's
`*) → auto` coercion, whereas `ask` is already honored (exit 3 `reason=policy-ask`, retryable,
checked **before** reservation so no hop is consumed). `except` now yields `None` rather than
`{}`; the non-dict guard yields `None`; the final print returns `auto` only when
`manifest is not None`. A pinning CLI assertion was added.

Budget: 199 → 200 (at cap, valid); the four lines were bought back by compressing the `_cli` and
`stall_streak` docstrings.

## BLOCKING — Finding 2: the "three seams" claim is false for two of three

The prompt claimed `subprocess`, `HOP_DIVISOR`, `CEILING_FACTOR` are seams "your Step 1 consumes."
Measured against Task 7's Step 1 block: **only `subprocess` is consumed** (`TestCli._run`).
`HOP_DIVISOR` and `CEILING_FACTOR` appear nowhere in Task 7's tests. `CEILING_FLOOR` *is* already
used and was never at risk.

An implementer who checks finds the claim false and may conclude the instruction is stale and drop
the imports — reintroducing exactly what the format hook already deleted once.

### Disposition — FIXED

Prompt corrected to state that Step 1 consumes `subprocess`, while `HOP_DIVISOR`/`CEILING_FACTOR`
are intentionally-unused imports preserved by Task 6's deviation record. **The deviations row
carried the same overstatement (inherited from the handoff warning) and was corrected too**, so it
does not propagate into Module 3.

## Minor — fixed in the prompt, no re-review needed

- **Missing subdirectory-`CLAUDE.md` instruction.** The prompt mandated the `CLAUDE.md Files Read`
  report section but never told the implementer to read them.
- **Import placement.** Step 3's `import glob, json, os, re, sys` lands mid-file; hoist one-per-line
  beside the existing `import math`, matching the file's own header.

## New deferred orders — filed in `deviations.md` as P7-1 and P7-2

- **P7-1 (Module 3, Task 12)** — the shell half of Finding 1: `2>/dev/null` swallows a CLI failure
  into an empty string and `*)` coerces it to `auto`. Must treat empty/unrecognized as non-consent.
- **P7-2 (Module 3)** — `stall-streak` has zero CLI coverage, and it is the subcommand the Module 3
  stall gate calls. Coverage, not a live bug; costs Task 7 budget it does not have.

## Observations, no action

- `stall_streak` truncates the streak (rather than returning `indeterminate`) when a *non-newest*
  outcome record lacks `tasks_done`. That understates stalls — the permissive direction — but the
  docstring pins it and `.handoff-hops` remains the fail-closed backstop.
- `derive_expected_hops` still raises `TypeError` if `manifest["modules"]` is a non-iterable scalar
  (R3-2 closed only the non-dict *manifest* case). Reachable only by hand-edit; exits non-zero
  rather than fail-open.

---

# Task 7 — Controller Partner Review (round 2)

**Verdict: APPROVED**, contingent on one precondition (a `deviations.md` address fix, outside
Task 7's write scope), now discharged.

## Finding 1 — CLOSED, measured by EXECUTION not by reading

The partner materialized the plan's Step 3 block onto a copy of the real `_handoff_support.py`
and ran the CLI across a 15-case matrix:

| Manifest | `spawn-policy` | `expected-hops` |
|---|---|---|
| `{"handoff":{"spawn_policy":"off"}}` | `off` | unknown |
| `{"handoff":{"spawn_policy":"ask"}}` | `ask` | unknown |
| `{"handoff":{"spawn_policy":"auto"}}` | `auto` | unknown |
| **`{"total_tasks":5,"tier":"standard"}` (legacy pin)** | **`auto`** | **`2`** |
| corrupt JSON | **`ask`** | unknown |
| non-object (`[1,2,3]` / `null` / `"hello"`) | **`ask`** | unknown |
| **missing file** | **`ask`** | unknown |

The legacy pinned case still yields `auto` AND `2` — both halves hold. `expected-hops` is
unchanged: `manifest or {}` reproduces the old `{}` in every degraded case.

**`ask` is genuinely non-permissive, verified through the shell layer:** the `ask` arm sits
immediately after `validate_bundle` and BEFORE the cmux-reachable check, exits 3 without
reserving, and module 3's test asserts `.handoff-hops` does not exist. The CLI exits **0** while
printing `ask`, so the shell's `$( … 2>/dev/null)` capture receives it and the `case` matches a
recognized arm — the fix survives the shell rather than dying in it.

## Finding 2 — CLOSED, measured

Symbol counts in Task 7 Step 1 vs the landed test file: `subprocess` 1 occurrence (`TestCli._run`)
— claim accurate; `HOP_DIVISOR` / `CEILING_FACTOR` **zero** — correctly described as preserved by
Task 6's record rather than by Step 1; `CEILING_FLOOR` used at line 113 — correctly described as
already in use. The `deviations.md` row carries the correction, so it will not reach Module 3.

## Precondition raised and DISCHARGED — P7-1 was misaddressed

P7-1 targeted "Module 3, Task 12". The `SPAWN_POLICY` block is at module-3 lines 180/183, inside
**Task 8** (58–251); **Task 12 is in module 4 entirely** (`write-mechanics-card.py`). Controller
verified both facts and corrected the address.

> "The address resolves to a wrong-but-existing target, which is the worst shape — it reads as
> valid. Since `transition-module.py` consumes this register at the boundary, a misaddressed order
> is functionally a dropped one, and what would be dropped is the shell half of a consent
> fail-open."

The error originated in the partner's round-1 text and the controller transcribed it faithfully —
a reminder that a faithful transcription of a wrong premise is still a wrong premise.

## Residual over-permissive case — folded into P7-1, not filed separately

A **readable** manifest with a **present but invalid** `spawn_policy` still yields `auto`: `"OFF"`,
`"Off"`, JSON `false`, `null`, or a non-dict `handoff`. Graded non-blocking on **measured**
reachability: both manifest writers reject invalid values (`materialize-manifest.py` fails loudly
on bare `off`; `transition-module.py` routes through `SddSession.model_validate`; `spawn_policy` is
a closed `Literal`), so it needs an out-of-band hand-edit — materially weaker than round 1's, which
needed only a missing file. **Recorded with the reason it is not redundant with P7-1's shell fix:
changing `*) → ask` cannot help, because `auto` is a recognized value matching its own arm.**

## Budget, validation, baseline

All 5 plan files PASS / 0 blockers / 0 warnings. Tasks 4/5/6/7 = 47/128/197/**200** (at cap).
`git diff --stat 64ba56a..441d3a4 -- '*.py' '*.sh'` is **empty**, so the 697 baseline holds by
construction and needed no re-run.

**One controller claim corrected:** the docstring compression did lose a clause — `stall_streak`
dropped `(fail-closed stays with .handoff-hops)`. No behavioral contract was lost (0 = progress/
first hop, `indeterminate` = newest malformed, caller SKIPs all survive) and the clause is
recoverable from module-3's Contract Constraints, but "content unchanged" was not exactly right.

## Examined and cleared

`_REPORT_GLOB = "task-*-implementer-report*.md"` — the trailing `*` is repo convention
(`context-summary.py`, `controller-checkpoint.py`) and this version is tighter, requiring `.md`. It
matches the real fix-round filenames on disk via the leading `*`. A superseded report could let a
task count as done when its latest round is BLOCKED, but that is the pinned contract, not a
deviation from it. Observation only.
