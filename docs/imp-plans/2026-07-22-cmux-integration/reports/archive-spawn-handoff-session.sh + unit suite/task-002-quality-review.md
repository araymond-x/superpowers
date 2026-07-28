# Task 2 Quality Review — Bundle validation + cmux/hop preconditions

**Scope:** `git diff 2557250..c176b4e`, focused on code quality (spec compliance already PASSED per `task-002-spec-review.md`). Files: `skills/subagent-driven-development/scripts/spawn-handoff-session.sh`, `tests/unit/test_spawn_handoff.py`.

Verified independently: `.venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -v` → **14/14 PASSED**. `bash -n` syntax check clean. `shellcheck --severity=warning --external-sources` on the full file surfaces only pre-existing SC2034 warnings on foundation vars from Tasks 1/3+ (`QUOTA_MIN_PCT`, `QUOTA_TOOL_DEFAULT`, `PICKER_CONTRACT`, `DRY_RUN`, `FEATURE_NAME`, `SPAWN_LOG`, `SP_HOP`) — none originate in the Task-2 diff itself, and per the review brief these are explicitly out of scope.

## Strengths

- **`validate_bundle()` is clean, single-responsibility, and correctly `local`-scoped.** All four parameters (`bid exp_type exp_skill wt`) and every intermediate (`real_bundles real_bdir manifest btype bskill brepo active_id`) are declared `local`; nothing leaks into the caller's namespace beyond the function's return status. The signature is genuinely reusable — a future review-bundle spawn path can call `validate_bundle "$id" "review" "some-skill" "$wt"` without modification, matching the plan's stated parameterization intent.
- **Defense in depth on path containment.** The charset gate (`^[A-Za-z0-9_.-]+$`) rejects `/` outright, and the `pwd -P` + `case "$real_bdir" in "$real_bundles"/*)` containment check is a second, independent barrier — even a charset-legal `bid=".."` is caught by containment because `cd "$BUNDLES_DIR/.." && pwd -P` resolves outside `$real_bundles`. Verified this reasoning holds; no traversal gap.
- **Fail-closed JSON parsing.** The three `$PYTHON -c` one-liners have no explicit try/except, but that's fine by construction: a malformed manifest (bad JSON, non-dict top level, `"session"` present but not a dict) makes `json.load(...).get(...)` raise, the traceback goes to stderr, and the command substitution captures empty stdout. Empty `btype`/`bskill` then fail the subsequent `!=` comparisons and REFUSE — the script never crashes uncaught or silently accepts malformed input. Confirmed the `.get("session") or {}` guard also correctly handles an explicit `"session": null`.
- **The quoted heredoc (`<<'PY'`) for `active_id` is injection-safe.** `$wt` is passed as `sys.argv[1]` to the python process, not string-interpolated into the heredoc body (which is single-quote-delimited, so the shell does zero expansion inside it anyway). A worktree path containing spaces, `$`, backticks, or quotes cannot reach python source-code context — it can only ever be a positional argv string. This is the correct pattern and matches the pickup-guard mirror the report claims.
- **Precondition ordering and exit codes match the acceptance criteria exactly.** Bundle validation (a static, input-driven check) precedes cmux-reachability and hop-limit (environment/session-state checks) — sensible ordering, cheapest/most-deterministic check first. Exit 1 for validation failures (caller-fixable, bad input) vs. exit 3 for cmux/hop (environment-dependent, triggers the manual-fallback path) is the correct split per the plan's exit-code contract.
- **Test-fixture deviation in `test_hop_limit_exits_3` is clean and consistent.** The added `git add -A && git commit -qm "seed hops"` mirrors the exact idiom already used by `test_missing_active_feature_exits_1` two tests earlier in the same file. Confirmed test isolation: `tmp_path` is a fresh pytest fixture per test, `ctx["wt"]` is a `git init`'d directory scoped entirely under that `tmp_path`, so the commit is invisible to and unaffected by any other test. The inline comment explaining *why* the commit is needed (spec.md L164 tracked-file invariant, avoiding a spurious Precondition-1 trip) is genuinely useful — it tells a future reader why this test doesn't match the plan's literal text without them having to dig.
- **Trivial-dependency discipline preserved.** No new dependency on PyYAML/Pydantic/the `_report_utils`/`validators.py` machinery — the inline `json`/`base64`-only one-liners keep this script's fallback-to-system-`python3` promise (Layer 0 comment: "this script needs only json/base64 stdlib") intact. Reasonable choice not to route through the heavier shared validation modules for a 3-field manifest read.

## Issues

### Critical (Must Fix)
None.

### Important (Should Fix)
None.

### Minor (Nice to Have)

1. **Three separate `$PYTHON -c` subprocess spawns re-open and re-parse the same `manifest.json`.**
   - File: `skills/subagent-driven-development/scripts/spawn-handoff-session.sh:89-91`
   - Each of `btype`/`bskill`/`brepo` forks a fresh python interpreter and calls `open(sys.argv[1])`/`json.load(...)` independently. Functionally correct and safe (verbatim-matches the approved plan, so not a spec deviation), but it's 3x the process-spawn and file-I/O cost of a single call that reads the manifest once and prints three fields (e.g. newline- or NUL-delimited). Given this runs once per spawn invocation (not a hot loop), the cost is negligible in absolute terms — flagging only as a low-priority future cleanup, not a blocker.

2. **Charset-rejection message omits the offending bundle id.**
   - File: `skills/subagent-driven-development/scripts/spawn-handoff-session.sh:75-76`
   - `"REFUSED: bundle id fails charset ^[A-Za-z0-9_.-]+$"` doesn't echo `$bid`, while the very next failure message two lines later (`"REFUSED: bundle dir not found for id: $bid"`) does. Minor inconsistency — including the rejected value (even if it contains stray characters; it's only ever echoed to stderr, never executed) would make a future debugging session slightly faster. Not risky to fix, not urgent to fix.

3. **`import pytest` is inserted mid-file rather than consolidated at the top of the module.**
   - File: `tests/unit/test_spawn_handoff.py:98`
   - Not a regression — this continues the exact pattern Task 1 already established (`import os`/`import subprocess`/`from spawn_handoff_helpers import ...` at lines 60-62, also mid-file). The convention trades PEP 8 import-grouping for git-diff locality (each task's diff is self-contained and appends at the bottom). Since Task 1 set this precedent, Task 2 following it is the *consistent* choice, not a new smell. Noting only because a later consolidation pass (post Task 6, once the file is final) might want to hoist all imports to the top in one pass — not this task's job.

## Recommendations

- No action required before proceeding to Task 3. The two file:line items above are optional polish; item 1 (consolidating the three python reads) would be a nice one-line-diff cleanup to bundle into a later pass (e.g. Task 9 docs/cleanup) but isn't worth interrupting the Task 3-6 serialization for.
- Confirmed nothing in this diff makes Tasks 3-6 harder: the `# (Task 3 inserts the quota check here.)` marker (and the Task 4-5/Task 6 markers after it) are untouched and immediately follow the new Precondition 4 block, `MAX_HOPS`/`SP_HOP` are available as expected inputs for later logic, and no new global variable names collide with anything the plan's later tasks are known to introduce (`QUOTA_TOOL`, `QCLASS`, `FORWARDED`, `LABEL`, etc.).

## Assessment

**Ready to proceed to Task 3?** Yes.

**Reasoning:** `validate_bundle()` is a clean, correctly-scoped, defense-in-depth function; the python one-liners and heredoc are robust against both malformed manifests and shell-injection via the worktree path; precondition ordering/exit codes match the acceptance criteria; and the test-fixture deviation is a faithful, isolated, well-documented correction. Only cosmetic/efficiency nits found, none blocking.
