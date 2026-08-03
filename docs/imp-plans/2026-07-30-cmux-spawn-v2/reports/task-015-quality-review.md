# Code Quality Review — Task 15 (Check 9 `:(exclude)` pathspec) — FIRST quality review

Range: `4510aad..85e4190`. Full unit suite independently re-run: **842 passed, 1 xfailed, 0 failed**.
Repo left byte-identical to HEAD after all mutation work (sha256 verified on both changed files).

## Strengths

- **The round-2 fix is real and load-bearing, not test-shaped.** Positive control: shipped code FAILs Check 9 on a real source commit under an unresolved (`tempfile.mkdtemp`) repo path; the `abspath` variant PASSes.
- **Both round-1 BLOCKING findings are genuinely closed for the scenarios they name.** Reverting the whole fix (M1) is killed by two tests.
- **Manifest branch is structurally safer by construction** — `feature_dir` is already git-root-relative, so no `relpath` arithmetic and no symlink surface. Round 2 was right to mirror it rather than invent.
- **The fix silently improved the missing-git case** — nobody claimed this, so I measured it. With `git` absent from `PATH`: HEAD exits 3 with an explicit JSON error, while the pre-Task-15 baseline exits 1 reporting `verification_git_reality: PASS`. `_resolve_git_root`'s unguarded subprocess propagates to `main`'s catch-all, converting a silent fail-open into a loud infrastructure error.
- **Verified-good behaviors nobody asked about:** git worktrees (source→FAIL, bookkeeping→PASS) and cwd = a subdirectory *inside* the repo (→FAIL, correct).
- **No dead code.** All 8 `exclude_dir` references live; one definition, one call site.

## Mutation Log (10 mutations against the Round-2 fix)

| # | Mutation | Result | Killed by |
|---|---|---|---|
| M1 | Revert fix entirely (`git_root=None` + `relpath` vs `os.getcwd()` — exact round-1 code) | KILLED | `…ReportsDirMode::test_source_commit_fails`; `TestGitRealityCwdIndependence` |
| M2 | `realpath`→`abspath` on **both** sides of `relpath` | **SURVIVED** | — (47/47 green) |
| M3 | `realpath`→`abspath` on the **reports_dir** side only | **SURVIVED** | — |
| M4 | `realpath`→`abspath` on the **git_root** side only | SURVIVED — verified *equivalent* | — |
| M5 | Drop the `.` anchor from the pathspec | SURVIVED — verified *equivalent* | — |
| M6 | Invert: include-only-feature-dir instead of exclude | KILLED | all 3 `…bookkeeping_commit_passes` |
| M7 | Remove the `if exclude_dir:` guard (`if True:`) | KILLED | `test_no_exclude_dir_does_not_add_exclude_pathspec` |
| M8 | Manifest mode: exclude `reports_dir` instead of `feature_dir` | **SURVIVED** | — |
| M9 | reports_dir mode: exclude reports_dir itself, not its parent | **SURVIVED** | — |
| M10 | Manifest mode: drop the exclude entirely | KILLED | `…ManifestMode::test_bookkeeping_commit_passes` |

4 killed / 6 survived. M4 and M5 verified equivalent. M2, M3, M8, M9 are genuine gaps.

## Critical

### C1 — M2/M3 survived: the `realpath` fix has ZERO coverage, and round 2's stated basis for believing otherwise is false

`controller-checkpoint.py:1701-1704`. Round-2 review states the derivation tests *"use `tmp_path`, which lands under the symlinked `/tmp`, so they organically exercise this path."* Measured — false:

```
PYTEST tmp_path    = /private/var/folders/.../pytest-847/test_show0
realpath(tmp_path) = /private/var/folders/.../pytest-847/test_show0   EQUAL = True
tempfile.mkdtemp() = /var/folders/.../tmpihoxmhgb
realpath(mkdtemp)  = /private/var/folders/.../tmpihoxmhgb             EQUAL = False
```

`abspath == realpath` in every derivation test — which is why M2/M3 pass 47/47. Not equivalent; positive control on an unresolved path:

```
SHIPPED (realpath)  -> verification_git_reality = FAIL   (gate works)
M2 MUTANT (abspath) -> verification_git_reality = PASS   (fail-open on a real source commit)
```

**Fix:** one derivation test on `tempfile.mkdtemp()` (the existing `_init_temp_git_repo()` already uses it) or a deliberate symlink alias.

### C2 — `exclude_dir == "."` silently disables Check 9 entirely

`controller-checkpoint.py:423-431, 1701-1704`. When reports_dir's parent *is* the git root, `relpath` yields `"."`, and `git log -- . ':(exclude).'` returns rc=0 with empty output — the whole repository excluded. Through the real CLI, with a real `src/feature.py` commit inside the verification window:

```
verification_git_reality: {"status": "PASS", "detail": "No file modifications during 1 verification window(s)"}
in blockers: False
```

No symlinks, no fallback, no contrivance — the gate affirmatively certifies a source modification as clean. Reachability: `--reports-dir` is free-form and unvalidated; unreachable under the documented `docs/imp-plans/<feat>/reports` layout, fully reachable for any other. Manifest mode has the same shape via `feature_dir: "."`.

**Fix:** reject or skip an `exclude_dir` normalizing to `"."`, `""`, or starting with `..`, and say so in the check detail.

## Important

- **I1 — the gate cannot distinguish "couldn't look" from "found nothing."** `if result is not None and result.returncode == 0 and result.stdout.strip():` collapses git failure and a clean window into the same outcome, then reports *"No file modifications"*. `:(exclude)../..` exits 128 (`is outside repository`) → PASS. I reproduced this end-to-end with a feature dir symlinked outside the repo (HEAD → PASS; pre-Task-15 baseline → FAIL). **Calibration:** the three-way table has *different causes* per row, and this reproducer's precondition also trips the already-accepted `_resolve_git_root` shallow-fallback advisory — so it is not a clean "regressed vs baseline" claim, and the round-2 fix genuinely *narrowed* reachability here. The durable point is structural: Task 15 added new ways for git to exit non-zero, and the gate has no way to say so. Surface `result is None or returncode != 0` as its own status or a warning in `detail`.
- **I2 — M8/M9: nothing pins *which* directory is excluded.** Swapping `feature_dir`→`reports_dir` (both branches) leaves 47/47 green, because every bookkeeping fixture lives under `reports/`. A refactor could narrow the exclusion to `reports/` (re-tripping Check 9 on `deviations.md`/`plan.md` commits SDD controllers routinely make inside a verification window) or widen it to `docs/imp-plans/` (exempting *every* feature dir) with no test objecting. Fix: one fixture committing a feature-dir file *outside* `reports/`.
- **I3 — cwd-independence is only tested for cwd OUTSIDE the repo.** `TestGitRealityCwdIndependence` pins an unrelated tempdir, where git fails outright. The nastier variant — cwd a subdirectory *inside* the repo, where git succeeds but `.` silently narrows scope — has no test. I verified HEAD handles it correctly, so this is a coverage gap, not a defect.

## Minor

- **M4 equivalent, verified:** `git rev-parse --show-toplevel` returns the physical path and the fallback uses `.resolve()`, so `realpath()` on that operand is a no-op. Correct to keep for symmetry; just not discriminable.
- **M5 equivalent, and the `.` anchor is redundant** — with only exclude pathspecs git includes everything else. Verified identical from repo root; from a subdir the anchor-less form is *strictly more robust*. The `.` is the token that made cwd load-bearing in round 1; dropping it removes the coupling by construction rather than by careful `-C` discipline.
- **`_resolve_git_root`'s `subprocess.run` has no `timeout`**, unlike `_git_run`'s 10s. A hung git blocks the checkpoint indefinitely. (The *missing*-git case is handled well — see Strengths.)
- **~22 lines of comment for 5 lines of code** in the reports_dir branch. Justified by the bug history, but it now out-masses the logic; would survive a trim to ~6 lines plus a pointer to the deviations row.
- **Round-1 implementer report's `files_changed` text ("relpath … against `os.getcwd()`") is stale** vs HEAD. Historical record, superseded — noted only so a future reader doesn't take it as current.

## Report accuracy

Fix report: 2 files changed, 6 tests written — verified (exactly 6 new `def test_` in `ddebe69..85e4190`). Round-1 report: 3 tests + `_commit_files_at` helper — accurate. The three accepted advisories reproduce as documented; the shallow fallback is re-cited only as the mechanism inside I1, not as a new finding.

## Assessment

**Ready to merge?** With fixes.

The round-2 fix meets the positive-control bar it set for itself, and it closed the bug it targeted. But its load-bearing half is unguarded by any test (C1), and the pathspec it introduced can silently certify a modified repository as clean under an unvalidated but legal `--reports-dir` layout (C2). Both are small, contained fixes.
