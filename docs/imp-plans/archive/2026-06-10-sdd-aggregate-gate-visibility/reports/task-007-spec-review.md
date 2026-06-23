# Task 7 (N25c) Spec Review — `_git_run` subprocess consolidation (SSOT)

**Verdict: PASS** — spec + contract (behavior-preservation) compliant.

Audited BASE `efc9204` (Task 6) → HEAD `c06b230` (Task 7) by reading code, not by accepting the report.

## Contract: SEMANTIC IDENTITY (behavior-preserving refactor)

### `_git_run` correctness (`controller-checkpoint.py:483-498`) — PASS
- Builds `cmd = ["git", "-C", cwd] + args if cwd else ["git"] + args` — `-C cwd` only when `cwd` truthy, bare `["git"]+args` otherwise.
- `try: return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)` / `except (subprocess.TimeoutExpired, OSError): return None`. Byte-for-byte the prior swallow→None semantics.
- 3.9-safe `# type: (list, Optional[str], int) -> Optional[subprocess.CompletedProcess]` comment — NO PEP-604 `|` union. `Optional` is imported (`:43 from typing import Optional, Tuple`). Would not regress the Category-8 3.9-compat check.

### Site 1 — `_check_verification_git_reality` (`:396-410`) — SEMANTICALLY IDENTICAL — PASS
The load-bearing case. OLD code built `git_cmd = ["git","log",...]` then **conditionally** rebuilt as `["git","-C",git_root]+git_cmd[1:]` **only `if git_root:`** — so when `git_root` was falsy the command stayed `["git","log",...]` with NO `-C`. NEW builds `git_args` (no "git" prefix) and calls `_git_run(git_args, cwd=git_root)`, whose `if cwd else` branch reproduces BOTH cases exactly:
- `git_root` truthy → `["git","-C",git_root,"log",...]` (identical)
- `git_root` falsy → `["git","log",...]` (identical — the old `if git_root:` skip is preserved)

Timeout still 10. The guard was correctly updated `if result.returncode == 0 ...` → `if result is not None and result.returncode == 0 and result.stdout.strip()` to handle the new None return (old code raised inside try and hit `except…pass`; new code returns None and the `is not None` short-circuit replicates the no-append outcome). `findings.append` dict keys (`task=vid`, `start`, `end`, `commits`) UNCHANGED.

### Site 2 — `_resolve_base_ref._git` (`:518-519`) — IDENTICAL — PASS
`def _git(cmd_args): return _git_run(cmd_args, cwd=git_root)`. `git_root` is a required non-Optional param here (always truthy), so `_git_run` emits `["git","-C",git_root]+cmd_args`, timeout 10, except→None — exactly the deleted inline body. All downstream `result is None`/`returncode`/`stdout` gating in the resolver is unchanged.

### Site 3 — `_in_changeset._git` (`:561-562`) — IDENTICAL — PASS
Same delegation. The untracked-check, merge-base, and the `diff_base`/`diff` fallback tail (`:573-575`) all still route through the delegating `_git` — unchanged.

## O4 exclusion (load-bearing) — PASS
`_resolve_git_root` (`:744-757`) STILL uses raw `subprocess.run` (`:751`) with NO timeout and NO try/except — errors propagate to drive its `parent.parent.parent` fallback-with-warning. Untouched by the diff.

`grep -nE "subprocess\.run" controller-checkpoint.py` returns EXACTLY 2 lines: `:496` (inside `_git_run`) and `:751` (inside `_resolve_git_root`). No third/missed/over-folded site.

## Behavior-preserving proof — PASS
`.venv/bin/python3 -m pytest tests/unit/test_pre_completion_gates.py tests/unit/test_c2_integration_gate.py -q` → **65 passed**. Every pre-existing Check-9 (git-reality) and Check-10 (changeset) behavior guard passes unchanged. New `TestGitRunSSOT` (2 tests) is verbatim from the plan and green. Module exec-loads clean and exposes `_git_run(args, cwd=None, timeout=10)`.

## Scope — PASS
`git show --stat c06b230` lists EXACTLY 2 files: `controller-checkpoint.py` (+54/-38) and `test_c2_integration_gate.py` (+20). Diff hunks touch only `_check_verification_git_reality`, the new `_git_run` insertion (above `_resolve_base_ref`), `_resolve_base_ref._git`, and `_in_changeset._git`. No changes to `_review_tiers_per_task`/`_merged_dispatch_times` (Tasks 1-2) or the Check 10 / `integration_test_present` block (Task 8) — the only `integration_test_present` lines in the diff are UNCHANGED context inside the pre-existing `TestC2Check10`, adjacent to the appended `TestGitRunSSOT`.

## Report completeness — PASS
All required sections present: Implementation Summary, Source Files Read, CLAUDE.md Files Read, Deviations from Plan (the intentional non-application of the modern-type-hint rule, correctly justified by the 3.9 pin), Self-Review Findings, Concerns (none). Status DONE; frontmatter `task_type: implementation`, two `files_changed` entries matching the committed files.

## Findings
None blocking. None advisory. The refactor is a true SSOT consolidation with verified semantic identity at all 3 sites, the O4 exclusion held, and the behavior is guarded by 65 passing tests.
