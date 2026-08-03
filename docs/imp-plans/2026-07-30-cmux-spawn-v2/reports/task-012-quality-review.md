# Code Quality Review — Task 12 (write-mechanics-card.py + golden-file test)

**Model:** opus (adversarial + mutation testing) · **BASE** `d1d5a1e` → **HEAD** `7479b29` · **Verdict: Ready to merge — YES** (0 Critical, 0 Important)

## Strengths
- Tests genuinely non-vacuous — proven by **11 mutations (10 planned + 1 advisor-prompted), every one flipped the suite RED** as expected (measured, not claimed).
- Both composed `controller-checkpoint.py` invocations extracted from a generated card and run verbatim (`<N>`→1) → genuine checkpoint JSON, not argparse errors (N35 contract works).
- SSOT imports real, not decorative: `_skeleton()` builds body from imported `REQUIRED_SECTIONS` (drop one → validate-report RED) and self-checks frontmatter via `ImplementerReport.model_validate` (bad frontmatter → RED). Model/section drift breaks the test.
- Determinism structural: no `datetime`/`time`/`random`/`uuid`; `yaml.safe_dump(sort_keys=False)` over an insertion-ordered dict; two-runs-equal assertion genuinely re-runs + compares.
- Degrades, doesn't crash: `_read` swallows OSError→None, `(none recorded)` fallbacks, `main` returns 2 on unreadable manifest.
- No dead code: all helpers + imports used; `try/except ImportError: sys.exit(2)` present; `git show --stat 7479b29` touched only the two owned files.
- Pre-authorized `deviations_abs` deviation verified output-neutral by evidence (materialize-manifest.py always sets `deviations_file`).

## Issues
**Critical:** None. **Important:** None (two candidate concerns empirically refuted — see below).

**Minor (all non-blocking):**
- `write-mechanics-card.py` `--output` has no caller yet (Task 13 uses `--manifest` only) — fence-mandated argparse contract, not dead code.
- Test hermeticity (defense-in-depth): `validate-report.py` subprocess inherits full `os.environ`; harmless today (bypass doesn't reach the prose layer), but adding `SUPERPOWERS_VALIDATOR_BYPASS` to the conftest scrub list would future-proof. Test-only, no generator change.
- Fixture-unreachable branches (`expected None→"unknown"`, `csum_at None→micro`, `module_line` true-branch) untested — consistent with the fence-defined test set; not blocking.

## Refuted candidate concerns (raised, then disproved by mutation)
- *git-root resolution unpinned*: forcing the `str(mp.parent)` fallback turned 3/4 tests RED (the card's output location shifts too); only `test_byte_proxy` (never runs the generator) stayed green, correctly.
- *`SUPERPOWERS_VALIDATOR_BYPASS` makes the skeleton test vacuous*: validate-report.py's prose layer ignores the bypass, and the generator's own `model_validate` self-check blocks bad frontmatter from ever being written.

## Assessment
**Ready to merge: Yes.** Deterministic, degrades safely, imports SSOT rather than retyping, produces copy-verbatim checkpoint commands that were run and returned real results. All four tests mutation-proven; the additional concerns were empirically refuted, not assumed.

### Mutation log (all restored via `cp` backup + `diff -q` — never `git checkout`/`stash`)
| # | Test | Mutation | Result |
|---|------|----------|--------|
| 1a | deterministic | inject `os.urandom` into outcome line | RED (determinism) |
| 1b | deterministic | drop `--reports-dir` from both composed cmds | RED |
| 1c | deterministic | ceiling line prints `expected`(2) not `ceiling`(6) | RED |
| 1d | deterministic | redact outcome line (kills workspace:5/surface:7) | RED |
| 2a | skeleton | `passing:2 > written:1` | RED (self-check) |
| 2b | skeleton | drop Concerns from body (`REQUIRED_SECTIONS[:-1]`) | RED (validate-report prose) — load-bearing |
| 3a | degrade | `_read` re-raises OSError | RED (crash) |
| 3b | degrade | remove both `(none recorded)` fallbacks | RED |
| 4a | byte-proxy | expected `"$REPORTS_DIR"/*.md` → absent | RED (in-hook has teeth) |
| 4b | byte-proxy | expected `task-${padded}-${report_type}` → absent | RED (in-hook has teeth) |
| 11 | all 4 | force git-root fallback to `""` | 3 RED, 1 GREEN (byte-proxy, correct) |

Positive control: baseline 4 passed, no ambient `SUPERPOWERS_*` env, conftest scrubs only picker vars (does not neutralize validation). Note: mutation 2a proved the generator's self-check has teeth but crashed before writing; **2b is the load-bearing proof** the body round-trips through the real validator.
