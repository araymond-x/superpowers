### Strengths

- Both bug fixes are minimal, targeted, and correctly located: the `sys.executable` substitution in the regen-line now matches the checkpoint invocation lines a few lines below it in the same generated card, and the `MAX_HOPS` validation is a faithful `re.fullmatch(r"[0-9]+", ...)` port of `spawn-handoff-session.sh`'s `^[0-9]+$` bash regex — independently verified the two are behaviorally identical across leading zeros (`"007"` matches both), negatives, decimals, empty string, and whitespace-padding (all rejected by both).
- The large textual diff to `write-mechanics-card.py` (88 changed lines) is confirmed to be almost entirely a formatter reflow (black). No hidden scope creep in the noise.
- The `env_extra` parameter on `_run_card` is correctly merged in *after* the ambient `SUPERPOWERS_CMUX_*` strip, so the two new tests inject their env var without leaking into the other 7 pre-existing call sites in the file, all of which still pass `env_extra=None` implicitly and are unaffected.
- `test_card_regen_line_uses_real_interpreter`'s adjusted assertion (resolving the interpreter path via an actual subprocess call rather than hardcoding `VENV_PY` or using `os.path.realpath()`) is a legitimate fix, not a dodge — independently confirmed the test still fails if `{sys.executable}` were reverted to the literal `$PYTHON` string, and still fails if the wrong path were interpolated. Exactly as strict as the plan's illustrative pseudocode intended.
- Commit `65ae978` touches exactly the two intended files.
- All 9 relevant unit tests pass live (`.venv/bin/python3 -m pytest tests/unit/ -k "card" -v`).
- No dead code, no unused imports, no unreachable branches introduced.

### Issues

#### Critical (Must Fix)
None found.

#### Important (Should Fix)
None found.

#### Minor (Nice to Have)

- `skills/subagent-driven-development/scripts/write-mechanics-card.py` — when `SUPERPOWERS_CMUX_MAX_HOPS` is set but fails the regex, `spawn-handoff-session.sh` prints a WARNING to stderr, but the Python card silently falls back with no diagnostic. Low-stakes since the card is a read-only display artifact generated after the bash script has already validated (and warned about) the same env var during the actual spawn — but a standalone run of `write-mechanics-card.py` with a bad value gives no signal the override was ignored. Not worth reopening the task; worth a one-line follow-up if this file is touched again.

### Recommendations

- No structural or process changes needed. The validation logic is a small, self-contained duplication of the bash regex — appropriate given it's crossing a language boundary for a two-line check, not worth extracting into a shared helper.

### Assessment

**Ready to merge?** Yes

**Reasoning:** Both N85 fixes are correct, minimal, and verified to match the reference implementation's (`spawn-handoff-session.sh`) behavior on all tested edge cases; the one documented deviation is a legitimate correction to the plan's illustrative pseudocode rather than a weakened assertion; tests pass live; no dead code or scope creep.
