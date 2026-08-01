# Partner Review — Task 5 dispatch quality

**Verdict: APPROVED** (with 1 Major, 4 Minor, 1 Nit — all actioned by the controller before dispatch)

Reviewer: general-purpose subagent (opus), dispatched via SDD controller-partner protocol.
Scope: quality of the PROPOSED implementer dispatch prompt for Task 5, not code.
Repo left unmodified (`git status --porcelain` identical before/after); all experiments in scratchpad copies.

## Findings

### Major

**M1 — Step 2's predicted red state is wrong, and the wrong prediction invites a fix that violates two pinned facts.**

The prompt implied eight per-test failures. The real Step 2 state, with `Handoff` imported top-level
(as pinned facts #2/#3 require) and the model not yet changed, is a collection-time ImportError that
takes down the entire 29-test file:

```
tests/unit/test_models/test_sdd_session_model.py:5: in <module>
    from sdd_session import (
E   ImportError: cannot import name 'Handoff' from 'sdd_session'
!!!!!! Interrupted: 1 error during collection !!!!!!
```

Why Major, not cosmetic: the tidiest way to convert a collection error into "proper" per-test TDD
failures is to move the import inside a method — contradicting fact #2 (no method-level re-import)
and fact #3 (add to the top-level list) — and it would SURVIVE review, because all eight tests pass
afterward. Three plan amendments have already closed exactly this shape of hole.

### Minor

**m1 — The NameError claim named one test too many (a confidently-stated wrong fact).**
`test_extra_key_rejected` never references `Handoff`; it goes through `SddSession.model_validate`.
Measured by deleting `Handoff` from the import list in a scratch copy: `1 failed, 28 passed`, the
single failure being `test_spawn_policy_literal_is_closed_set`. (deviations.md:131 gets this right;
the prompt over-generalized it.)

**m2 — The `validators.py session` manifest is verifiably absent.**
`docs/imp-plans/2026-07-22-cmux-integration/.sdd-session.json` does not exist. Leaving this as a
conditional makes the implementer discover it — the `_minimal_session()` failure mode one level up.

**m3 — Task 5 silently changes `materialize-manifest.py`'s output.**
That script serializes via `model_dump_json()` with no `exclude_none`, so the moment
`handoff: Handoff | None = None` lands, every newly materialized manifest gains `"handoff": null` —
from a task that does not own that file. Confirmed to regress nothing today (see V8), but the
implementer must expect it and not act on it.

**m4 — Give the implementer the arithmetic self-check.** 663 + 8 = 671. Any other number means a
test did not run or something regressed. Converts "don't regress it" into a falsifiable assertion.

### Nit

**n1 — "corrected twice" undercounts.** Three `| 5 | PlanAmendment |` rows plus the `| 4→5 |`
carry-forward.

## Verified-correct (claims actively checked, with method)

| Claim | How |
|---|---|
| Contract Constraints quote is verbatim | `diff` vs the module plan's line 33 with prefix stripped → identical; POSITIVE CONTROL run (`echo bogus \| diff -`) confirmed the harness can report a difference |
| Commit hashes `ab1ffd2` / `fe2437e` exist and are Task 4 | `git show --stat`: `ab1ffd2` = plan.py +1 / test_plan_model.py +22; `fe2437e` = closed-set test, 94+/28- (the reformat signature) |
| Full suite 663 passed at `fe2437e` | re-ran → `663 passed`; `git diff --stat fe2437e HEAD -- . ':!docs'` empty, so the four commits since are docs-only |
| Import list exactly as quoted | `test_sdd_session_model.py:5-8` |
| `CURRENT_SCHEMA_VERSION` + `ValidationError` already top-level | lines 9 and 3 |
| `_minimal_session()` does not exist | file builds from module-level `MINIMAL_SESSION` (:19) → `MINIMAL_PATHS` (:12) |
| **`Handoff \| None` is correct here** | `check_python39_compat` builds its list from a flat `os.listdir` of `skills/subagent-driven-development/scripts` — never reaches `skills/scripts/models/`. venv is Python 3.14.5. House idiom: `plan.py` 6 uses, `checkpoint_result.py` 5, `sdd_session.py` itself 3 |
| **The `BaseModel` discriminating control behaves exactly as predicted** | Applied Steps 1+3 verbatim in scratch → `175 passed` (test_models). Swapped `Handoff(StrictModel)` → `Handoff(BaseModel)`: `1 failed, 28 passed`, the sole failure `test_extra_key_rejected` (DID NOT RAISE ValidationError). Reverted → `29 passed`. The prompt's most load-bearing claim, and it is right |
| **V8 — Task 5 as planned regresses nothing** | Full unit suite against the scratch implementation: **671 passed**, zero FAILED/ERROR. Confirms 663+8=671 and clears m3 as a live risk |
| Pre-commit reformat will fire and will strip unused imports | Registered as a Claude Code PreToolUse/Bash hook in `~/.claude/settings.json` (NOT a git hook — `core.hooksPath` unset, `.git/hooks/pre-commit` absent, so the prompt's "not this repo's" phrasing is right). `ruff check --select F401` flags `ArtifactPaths` and `ModuleState` as unused — they will be removed on commit, exactly as `fe2437e` removed five from `test_plan_model.py` |
| `test_sdd_session_model.py` untouched this sprint | `git log -- <file>` → last touched at `ad1b817` |

**Completeness / prior-task / scope:** no gaps. Shared Contract Section item 4's shape matches the
Step 3 snippet; its "absent → re-derived at spawn time" half is Module 3's reader and correctly
excluded. Task 4 context well conveyed. Write scope tightly fenced; the only non-owned file an
implementer might reach for (`materialize-manifest.py`) is explicitly forbidden, hardened by m3.

## Controller disposition

All six actioned into the dispatched prompt before the implementer went out: M1 (red state is a
collection ImportError, and that IS correct — do not defer the import), m1 (named only the
closed-set test), m2 (stated the manifest is absent as fact), m3 (expect `"handoff": null`, do not
touch materialize-manifest.py), m4 (671 arithmetic), n1 (count corrected to three).
