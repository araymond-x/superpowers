# Code Quality Re-Review — Task 4 — ROUND 2 (the closing round)

Dispatched: 2026-08-01, model sonnet, `general-purpose` agent, read-only, adversarial.
Subject: the fix round `fe2437e` (over `ab1ffd2`).

## Round-1 closure

**CLOSED.** Round 1's Minor #1 (Literal not pinned as a closed set) is fixed by `test_literal_is_closed_set` in `tests/unit/test_models/test_plan_model.py`, added between `test_rejects_invalid_value` and `test_schema_version_not_bumped` in `TestHandoffSpawn`. I reproduced the full mutation battery myself in an isolated scratch copy (`skills/scripts/models/` + the test file, `PYTHONPATH`-imported, no repo files touched):

| Mutation | My result | Fix report's claim | Match |
|---|---|---|---|
| Baseline (unmutated) | `52 passed` | `52 passed` | yes |
| Widened `Literal["auto","ask","off","manual"]` | `1 failed, 51 passed` (only the new test) | same | yes |
| Narrowed `Literal["auto","ask"]` | `2 failed, 50 passed` | same | yes |
| Reordered `Literal["off","auto","ask"]` | `1 failed, 51 passed` (only the new test — the case no pre-existing test catches) | same | yes |
| Field deleted (positive control) | `4 failed, 48 passed` | same | yes |

Real suite at HEAD: `tests/unit/test_models/ -q` → `167 passed, 1 warning` (I ran it — matches). Full `tests/unit/ -q` → `663 passed, 1 warning in 148.00s` (I ran it — matches).

Round-1 Minor #2 (`test_schema_version_not_bumped` as a third verbatim copy, deliberately not fixed): confirmed untouched. `git show ab1ffd2:...` vs `git show fe2437e:...` — the method's three lines are byte-identical; ruff's reformat didn't even touch it (already short enough to not need rewrapping).

## The ruff-attribution claim — independently verified, not just re-checked

This was the load-bearing claim, so I redid it from scratch rather than trusting the report's replay: I took `git show ab1ffd2:tests/unit/test_models/test_plan_model.py` (parent), ran `~/Library/Python/3.9/bin/ruff format` then `ruff check --fix` on it directly (same binary, same order, since `ruff` is absent from interactive PATH — confirmed), and diffed the result against `git show fe2437e:...` (HEAD). The **only** difference was the `from typing import get_args` import line and the new `test_literal_is_closed_set` method — exactly the implementer's stated intent.

I went one step further than the report: I parsed both files with `ast.parse` and compared `ast.dump()` of the two module bodies with import statements stripped out. **They are structurally identical** — this rules out not just "no extra hand-edits" but "no semantic change hiding inside a reformatted line," since AST dump is blind to whitespace/line-wrapping but would catch a reordered argument, a changed operator, an altered string, etc. This is a stronger proof than diff-based comparison and it comes back clean.

I also independently re-derived the five-import-removal claim: `SharedConstant`, `PatternReference`, `FeatureArchetype`, `Tier`, `Module` are all zero-occurrence in the file body at HEAD (`\bModule\b` matches only a comment and a `pytest.raises(match=...)` regex string, not the class name as a symbol), and none of the five appear in the pre-`ab1ffd2` version either (`53c00bd`) — so they were pre-existing dead imports, not introduced by Task 4. `ab1ffd2` never touched the import block at all. Documented in `deviations.md` row 123 (`ContractDiscovery`, disposition "Accepted") — satisfies the "dead code must be documented or it's Critical" rule.

I also spot-checked the sprint's separate PEP-604/ruff-config claim (`deviations.md` row 124), since it bears on whether this hook is safe for Tasks 5/6: no `pyproject.toml`/`ruff.toml`/`.ruff.toml` exists in the repo, and a probe file with `Optional[int]`/`Dict[str,int]`/`List[str]` survived `ruff check --fix` untouched (only a deliberately-planted unused `import os` was removed) — confirms the default rule set doesn't include `UP007`. Not central to this round but worth recording since I checked it rather than inheriting it.

## Strengths

- Fix is precisely scoped to the declared write-scope file; `plan.py` was never staged (`git diff --stat ab1ffd2..fe2437e` shows exactly one file).
- The new assertion is placed idiomatically, in the position the report says, and reads naturally as the class's closed-set pin.
- The assertion form (tuple equality on `get_args`) is the right level of strictness: it's what actually discriminates reordering from a `set`-based equality, which the fix report demonstrated and I reproduced.
- Static-annotation pinning plus the three existing behavioral tests (`test_defaults_to_auto`, `test_accepts_ask_and_off`, `test_rejects_invalid_value`) jointly cover both the type's shape and its runtime validation semantics — a plausible bypass (a `mode="before"` coercing validator masking a widened annotation) would already break `test_rejects_invalid_value`, so it isn't a real gap.
- Contract constraints hold: `extra="forbid"` (`skills/scripts/models/_base.py:10`), `CURRENT_SCHEMA_VERSION == 1` (`_base.py:4`), unchanged by this commit.
- The implementer surfaced the hook-driven diff expansion proactively and gave a verification method, rather than letting the reviewer discover a 94-line diff cold.

## Issues

**Critical:** none.

**Important:** none.

**Minor**

- `tests/unit/test_models/test_plan_model.py` `TestHandoffSpawn` — the new assertion guards `plan.py`'s `handoff_spawn` Literal only. Task 5 is specified to add an independent `SpawnPolicy = Literal["auto","ask","off"]` in `skills/scripts/models/sdd_session.py` (confirmed: zero `spawn` occurrences there today, so this is prospective, not a current defect). If that second declaration drifts from this one (widened, narrowed, or reordered), nothing in this test class — or any test I found — would catch it independently; Round 1's mitigation claim ("fails loudly at Task 6's `Handoff(spawn_policy=...)` call") concerns code that doesn't exist yet at this commit and I cannot verify it here. Concrete fix: when Task 5 lands, add the symmetric `get_args(...) == ("auto","ask","off")` assertion against `sdd_session.py`'s Literal, not as a Task-4 fix but as a carry-forward for Task 5's own test file.
- `deviations.md:123` enumerates the ContractDiscovery import removals as "SharedConstant/PatternReference/FeatureArchetype/Tier" and treats `Module`'s removal separately (via the "only surviving Module tokens are a comment and a regex string" sentence). This is accurate but reads as inconsistent counting at a glance — a future reader skimming just the enumeration could miss that `Module` is the fifth removed import. Not a defect requiring action, just a documentation-clarity note.

## Assessment: **APPROVED**

This round lands on the convergence signal the dispatch defined for this feature: findings that are cosmetic and a clean verdict. Both round-1 items are resolved as claimed (one fixed and reproducibly verified, one deliberately and verifiably untouched). The large mechanical diff was read hunk-by-hunk via independent AST-level comparison — the strongest check available — and nothing non-mechanical rode along inside it. No dead code is unaccounted for. No scope violation. All commands were re-run by me from this worktree's own `.venv`, not taken from any report.

**How I verified every claim**: `git show`/`git diff ab1ffd2..fe2437e` for the exact commit contents; independent `ruff format` + `ruff check --fix` replay against the parent commit in an isolated scratch dir diffed against HEAD; `ast.dump()` structural equality check (import-stripped) between the replay and the pre-fix parent to rule out semantic drift; `/usr/bin/grep` (not the ugrep-wrapped `grep`) word-boundary searches for all five removed import names, both at HEAD and at the pre-`ab1ffd2` parent; my own four-mutation + one-positive-control battery run against the real `.venv`'s pydantic/pytest, matching every number in the fix report; `tests/unit/test_models/ -q` and `tests/unit/ -q` run fresh; `_base.py` read directly for `extra="forbid"`/`CURRENT_SCHEMA_VERSION`; `deviations.md` read for the Task-4-tagged rows; a standalone ruff-config/PEP-604 probe to check the sprint's separate forward-looking claim. No repository file was modified during this review (`git status --short` afterward shows only pre-existing untracked/modified SDD process artifacts).

---

## Controller disposition — STOP. This is the convergence signal.

Both Minors are cosmetic-or-carry-forward and the verdict is APPROVED, so the stopping rule
fires and Task 4 closes at round 2. Trajectory: round 1 APPROVED with one substantive Minor the
controller actioned anyway → fix → round 2 APPROVED with nothing substantive.

Two things this round did that are worth keeping as method:

1. **It replaced a diff-based attribution proof with an AST-based one.** The dispatch asked it to
   confirm the 94-line auto-format diff hid nothing; it parsed both revisions and compared
   `ast.dump()` with imports stripped. That is blind to the reformatting *by construction* and
   would still catch a reordered argument, a flipped operator, or an altered string literal — a
   strictly stronger instrument than the one requested, aimed at exactly the risk (a substantive
   change hiding inside a large mechanical diff).
2. **It checked a claim it was not asked to check** — the PEP-604/ruff-config finding in register
   row 124 — because that claim governs whether the same commit hook is safe for Tasks 5-7, and
   it re-derived it rather than inheriting it.

**Disposition of the two Minors** (disposition is not done — both are recorded, one is routed):

- **Minor 1 (SpawnPolicy drift) is a real carry-forward and is routed to the plan, not left in
  this report.** It will land as an explicit test step in Task 5's plan text in the same
  amendment window as deferred order B4. A residual that lives only in a report is unfindable by
  the task that must act on it — this sprint has been bitten by exactly that.
- **Minor 2 (register enumeration clarity) is the controller's own row and was corrected in
  place**, naming `Module` as the fifth removed import.
