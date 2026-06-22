# finishing-feature-archiving — Design Spec

> **Status**: Design approved in principle (brainstorming 2026-06-22); Codex spec review completed and addressed (2 blockers + 3 major + 1 minor — all folded in, ref bundle `2026-06-22T21-04-06Z-superpowers`); pending user review.
> **Archetype**: Extension (adds behavior to the existing `finishing-a-development-branch` skill; no existing behavior removed).
> **Home**: `skills/finishing-a-development-branch/` — a new helper script + SKILL.md changes. **Not** a new skill.
> **Hard dependency**: the cross-skill *convention audit* (separate prerequisite feature, in flight on `main`) must merge first so this feature can *assert* — rather than establish — that every durable artifact a completed feature produces lives under `docs/imp-plans/<feature>/`.

---

## 1. Problem

When a superpowers plan execution completes, **nothing archives the feature's artifacts**. The only existing archiver, `transition-module.py`, runs solely at *multi-module boundaries* (mid-run housekeeping) and never touches a single-module plan or a multi-module plan's final module. `finishing-a-development-branch` — the shared terminal skill for both `subagent-driven-development` and `executing-plans` — only removes `.active-feature`/`.allow-main` and cleans the worktree; it leaves the committed `docs/imp-plans/<feature>/` directory (spec, distilled spec, plan, ~60 reports, deviations, manifest) flat in place forever, and never cleans the gitignored visual-companion litter under `.superpowers/brainstorm/`.

Result: completed features accumulate as flat clutter in `docs/imp-plans/`, and ephemeral mockup dirs accumulate indefinitely (one in this repo dates to March). There is no "leave the workspace clean and logical" step.

## 2. Goal

On successful completion, `finishing-a-development-branch` archives the entire completed feature directory to `docs/imp-plans/archive/<feature>/`, purges the gitignored visual-companion litter, records both actions in a durable ledger, and commits — **deterministically, via a helper script** — for **any** completed execution path (SDD or executing-plans) and **any** of the user's workflows (worktree, branch, or direct-on-main). When it finishes, `docs/imp-plans/` lists only active work and the tree is clean.

## 3. Core invariant (the design's spine)

> **Archive exactly when the finish action lands the work on the base branch in this same operation.**

Anchoring on *"work reaches base"* rather than *"which menu option was clicked"* makes one mechanism serve all three workflows, and naturally excludes the cases that shouldn't archive:

| Finish action | Work lands on base now? | Archive? |
|---|---|---|
| Option 1 — Merge locally | Yes (the merge) | **Yes** — archive on the feature branch *before* merge, so it rides the merge into base |
| On-main "Archive & finalize" (new) | Already on base | **Yes** — commit the archive directly on base |
| Option 2 — Push + PR | No (branch up for review; not merged) | No |
| Detached-HEAD — push as new branch + PR | No (branch up for review) | No |
| Keep as-is / Keep active | No (deferred) | No |
| Discard | No (work destroyed) | No |

PR and detached-HEAD push are excluded *because the work is not on base yet* — `finishing` runs at PR-*creation*, not PR-*merge*, so archiving then would be premature and would force awkward PR iteration on an already-moved directory. (Flippable later if desired; recorded in the Decision Log.)

## 4. Why before-merge, reading the LOCAL `.active-feature` (advisor decision #1)

In a worktree finish there are **two** `.active-feature` files: the worktree's (correct — points at the feature being finished) and the main checkout's (which currently points at unrelated `sprint-4`). If the archive ran *after* the merge on the main checkout and read *main's* `.active-feature`, it would archive the **wrong feature**.

Therefore: **archive runs in the current checkout, on the feature branch, before the merge/push, reading that checkout's `.active-feature`.** The normal merge then carries `docs/imp-plans/archive/<feature>/` into base. This sidesteps the cross-checkout pointer entirely.

It also does not violate the skill's existing "verify merge success before *cleanup*" safety rule: archiving is a *commit on the branch*, not a deletion. Worktree/branch deletion stays after merge-verification, unchanged. If a merge later conflicts, the archive commit is intact and recoverable on the branch.

Verified precondition: SDD does **not** guarantee reports are committed during execution (SKILL.md mandates no commits; telemetry-exp's happened to be committed). So the archive mechanic must **not assume** committed state — it captures the feature dir's on-disk state regardless (see §6).

## 5. The new on-main completion path (the UX half)

`finishing` Step 2 currently distinguishes *normal repo / worktree / detached-HEAD* but **not** *"on a feature branch"* vs *"on the base branch itself."* That missing distinction is why direct-on-main development falls through: every existing option assumes a feature branch to integrate.

Add a detection: `GIT_DIR == GIT_COMMON` **and** `current_branch == base_branch`. In that state the "Merge back to main" option is a no-op, so present instead:

```
Implementation complete on main. What would you like to do?
1. Archive & finalize   (move feature dir → docs/imp-plans/archive/, commit)
2. Keep active          (more work coming — leave it in place)
3. Discard              (revert the work)
```

"Archive & finalize" → run the helper directly on main. "Keep active" / "Discard" → no archive.

## 6. The helper: `archive-feature.sh` (deterministic, atomic, owns its commit)

Path: `skills/finishing-a-development-branch/scripts/archive-feature.sh`. The skill calls it; the script does the whole operation so the agent cannot forget a step or write an inconsistent commit message.

**Inputs:** none required beyond CWD; resolves everything itself. (Optional `--feature-dir` override for testing.)

**Steps:**

1. **Resolve & guard — canonicalize and confine before any destructive op (Blocker B1 + advisor #2).**
   - `ROOT="$(git rev-parse --show-toplevel)"` — abort non-zero if empty or git fails; assert `ROOT` is a non-empty absolute path **and** `$ROOT/.git` resolves (real repo).
   - Read `FEATURE="$(cat "$ROOT/.active-feature")"` (or the `--feature-dir` override, subject to the *same* confinement below). If absent/empty → **feature-context branch (step 1a, Minor finding).**
     - **1a.** A run is "expected to have a feature" when SDD/closeout artifacts are present (a `docs/imp-plans/*/reports/` dir or a `.sdd-session.json` in the tree/changeset). If those are present but `.active-feature` is absent → **fail loudly** ("closeout invariant: SDD artifacts present but no .active-feature"). If none are present → clean skip, exit 0 (an ordinary non-superpowers branch).
   - **Canonicalize:** `SRC="$(cd "$ROOT/$FEATURE" 2>/dev/null && pwd -P)"`; `NAME="$(basename "${FEATURE%/}")"`; `DEST="$ROOT/docs/imp-plans/archive/$NAME"`.

2. **Determine archive state, then confine (Major M1 collision-safety + Blocker B1 confinement).** Branch on whether `SRC` and `DEST` exist:
   - **`SRC` exists, `DEST` absent** → normal path. Run the **confinement assertions** (all must pass or abort with error — no move):
     - `SRC` is a directory and resolves **strictly under `$ROOT/docs/imp-plans/`** (prefix check on the *canonicalized* path — defeats absolute paths, `..`, and symlink escapes that resolve outside the repo).
     - `SRC` is **not** under `$ROOT/docs/imp-plans/archive/` (never re-archive an archive).
     - `NAME` matches the convention `^[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9-]+$` (CLAUDE.md:286-293) — rejects empty/`.`/`..`/malformed basenames.
   - **`SRC` gone, `DEST` exists** → already archived (a prior run moved it; Step 7 just hadn't cleaned the pointer). Clean no-op, exit 0.
   - **`SRC` exists, `DEST` exists** → **collision / partial prior run.** Fail loudly (exit non-zero), surface both paths, do nothing destructive.
   - **`SRC` gone, `DEST` absent** → `.active-feature` points to a nonexistent dir (stale pointer) → feature-context branch (step 1a).
   - **No `rm`/`mv` runs until `ROOT`, `SRC`, `DEST` are non-empty and the confinement assertions have passed.** Every destructive command uses these resolved, asserted variables — never a bare or possibly-empty expansion.

3. **Move the whole feature dir (handles tracked + untracked + gitignored — advisor decision #3).**
   - `mkdir -p "$ROOT/docs/imp-plans/archive"`
   - Filesystem `mv "$ROOT/$FEATURE" "$DEST"` — moves *everything* on disk, including uncommitted reports and gitignored `.sdd-session.json` / `reports/.dispatch-log`. (A bare `git mv` would silently leave untracked/ignored files orphaned at the old path.)

4. **Purge visual-companion litter (silent, but recorded).**
   - Target `PURGE="$ROOT/.superpowers/brainstorm"`. Only if `ROOT` is asserted (step 1): if the dir exists, capture the list of session ids, then `rm -rf "$PURGE"` (operating on the asserted absolute path — never an empty var).

5. **Append the ledger entry.** Append to `$ROOT/docs/imp-plans/archive/ARCHIVE-LOG.md` (create if absent) one entry:
   ```
   ## <feature-name>
   - Archived: <date> · trigger: <merge|on-main>
   - Source: docs/imp-plans/<feature>/ → docs/imp-plans/archive/<feature>/ (<N> files)
   - Purged .superpowers/brainstorm/: <session-ids or "none"> (<M> sessions)
   ```
   The ledger is the **only** possible trace of the purge (gitignored files leave no git record), and doubles as the human-scannable index of every completed feature.

6. **Clean-index assertion, bounded staging, scoped commit (Blockers B2 + Major M2).**
   - **Pre-flight (B2):** at the *start* of the operation (before the move), assert `git -C "$ROOT" diff --cached --quiet` — the index must be **empty**. If anything is already staged (likely with a concurrent agent sharing the checkout), **abort with error** rather than risk committing it. Failing before touching anything keeps the op atomic.
   - Stage the rename + ledger by explicit pathspec: `git -C "$ROOT" add -A -- "$ROOT/$FEATURE" "$DEST" "$ROOT/docs/imp-plans/archive/ARCHIVE-LOG.md"`.
   - **Bounded force-add (M2):** do **not** `git add -f "$DEST"` wholesale (recursive, unbounded). **Pre-move** (in the step-2 assertion phase), enumerate ignored files under `$SRC` (`git status --ignored --porcelain`); the set must be a subset of the allowlist `{.sdd-session.json, reports/.dispatch-log}` — any *other* ignored file → **abort before the move** (or require an explicit `--allow-ignored <path>` override), so a stray `.DS_Store`/`__pycache__` never reaches the archive. After the move, force-add **only** those allowlisted paths at `$DEST`.
   - **Verify before commit (B2):** assert `git -C "$ROOT" diff --cached --name-only` is a **subset** of {old path, new path, ledger, allowlisted stragglers}. If anything else is staged, abort — never commit an unexpected path.
   - Commit with explicit pathspec (`git -C "$ROOT" commit -- <those paths>`, belt-and-suspenders with the clean-index assertion):
     ```
     chore: archive completed feature <name>

     Archived docs/imp-plans/<feature>/ → docs/imp-plans/archive/<feature>/ (<N> files)
     Purged .superpowers/brainstorm/: <session-ids> (<M> sessions)
     Trigger: <merge|on-main>

     Prompted by Aaron; Co-Authored by Claude
     ```

**Two records, distinct jobs:** the **commit** is the git-history record (the rename is a tracked diff); the **ledger** is the durable, queryable index *and* the sole trace of the gitignored purge.

## 7. Integration into `finishing-a-development-branch/SKILL.md`

- **Step 2 (detect environment):** add the `current_branch == base_branch` discriminator → routes to the on-main menu (§5).
- **Step 5 / Option 1 (merge):** insert "run `archive-feature.sh` on the feature branch" **before** the `git checkout base && merge`. The merge carries the archived dir into base. Worktree/branch cleanup (Step 6) and Step 7 unchanged, still after merge-verify.
- **New on-main menu:** "Archive & finalize" → run `archive-feature.sh` on base.
- **Step 7 (post-completion cleanup):** unchanged sequence — `.active-feature`/`.allow-main` removal runs **after** archiving (the script reads `.active-feature` before Step 7 deletes it).
- **Options 2/3/4 and detached-HEAD:** no archive call.

## 8. Error handling & edge cases

| Case | Behavior |
|---|---|
| `DEST` exists, `SRC` gone | Already archived — clean no-op, exit 0 |
| `DEST` exists, `SRC` still exists | **Collision/partial run — fail loudly** (M1); nothing destructive |
| `.active-feature` absent, no SDD artifacts | Clean skip (ordinary non-superpowers branch) |
| `.active-feature` absent, SDD artifacts present | **Fail loudly** — closeout invariant violation (Minor) |
| `.active-feature` malformed / escapes `docs/imp-plans/` / symlink-escape / bad basename | **Abort with error** before any move (B1) |
| `git rev-parse` fails / `ROOT` empty | Abort; **no destructive command runs** |
| Index already has staged changes | **Abort before move** (B2) — won't risk committing unrelated staged work |
| Unexpected ignored file under `$DEST` | **Abort** (M2) — only allowlisted stragglers force-added |
| Reports uncommitted in worktree | Captured anyway (filesystem mv + `git add -A`) |
| Allowlisted gitignored stragglers (`.sdd-session.json`, `reports/.dispatch-log`) | Force-added into the committed archive |
| `.superpowers/brainstorm/` absent | Skip purge, ledger records "none" |
| Concurrent agent on same checkout | Clean-index assert + staged-subset verify + pathspec commit prevent capturing their changes |

## 9. Out of scope (intentionally left)

- **Vault honesty-check copies** (`$VAULT_DIR/References/SDD/honesty-checks/`) — written by `sdd-stop-hook.sh` on purpose as a cross-session record. Not touched.
- **Handoff bundles** (`~/.claude-codex-handoff/bundles/`) — separate tool, own lifecycle.
- **Standalone archive invocation** outside `finishing` — user declined (scope question). Residual risk: a run that completes without invoking `finishing` won't archive — the same caveat that already applies to worktree cleanup and `.active-feature` removal. Documented, not closed.

## 10. Testing

- **Unit — `archive-feature.sh` over fixtures:** (a) tracked-only feature dir archives + commits; (b) allowlisted gitignored `.sdd-session.json` force-added into the commit; (c) **unexpected ignored file** (`.DS_Store`) under the dir → abort (M2); (d) `DEST` exists + `SRC` gone → clean no-op; (e) `DEST` exists + `SRC` exists → **fail loudly** (M1); (f) malformed `.active-feature` — absolute path, `../escape`, symlink-escape, non-`docs/imp-plans/` target, bad basename — each **aborts before any move** (B1); (g) empty/unresolved `ROOT` → no destructive command runs; (h) **pre-staged unrelated file** in the index → abort before move; an **unstaged** unrelated dirty file → present but NOT in the archive commit (B2); (i) `.active-feature` absent + SDD artifacts present → fail; absent + none → clean skip (Minor); (j) ledger entry shape; (k) `.superpowers/brainstorm/` purged + recorded.
- **Branch-matrix coverage (Major M3)** — the highest-risk surface is whether `finishing` *calls or skips* the helper per menu branch. Add scripted/integration fixtures asserting archive **fires** for linked-worktree merge, normal-branch merge, and direct-on-main "Archive & finalize"; and is **skipped** for PR (Option 2), detached-HEAD push, keep-as-is, discard, and missing/malformed `.active-feature`. The menu-routing itself lives in SKILL.md prose; cover the decision via the script's invocation conditions + the §13 per-branch acceptance criteria, and document explicitly that prose-routing is verified by acceptance check, not a unit test.
- **Integration**: extend `tests/integration/sdd-e2e-test.sh` — completed fixture feature dir → archive → assert it lands in `archive/<feature>/`, committed, ledger appended, `.superpowers/brainstorm/` gone, `git status` clean.
- **Regression / install**: `validate-all-skills.py` + `verify-symlink-install.sh` green (skill count stays 15; new script under the skill dir).
- **Hook baseline**: `archive-feature.sh` is **not** a hook → no baseline re-capture needed.

## 11. Implementation surface

1. `skills/finishing-a-development-branch/scripts/archive-feature.sh` — new, tested.
2. `skills/finishing-a-development-branch/SKILL.md` — env detection, on-main menu, Option-1 pre-merge call, Quick Reference/Red Flags updates.
3. Tests per §10.
4. Docs: `CLAUDE.md` + `docs/ARaymond-customization-manifest.md` (per the fork's doc-maintenance rule); BACKLOG row.

## 12. Decision Log

| # | Decision | Chosen | Note |
|---|----------|--------|------|
| 1 | Archive unit | Whole feature dir → `docs/imp-plans/archive/<feature>/` | Uniform across SDD + executing-plans (both have a feature dir) |
| 2 | Trigger | "Work reaches base in this op" → merge + on-main only | Excludes PR/detached/keep/discard by the invariant |
| 3 | Merge sequencing | **Before** merge, on the feature branch, reading local `.active-feature` | Sidesteps two-pointer bug; doesn't assume committed reports |
| 4 | On-main UX | New "Archive & finalize" menu when `branch == base` | Honest completion action vs. mislabeled "keep as-is" |
| 5 | Visual litter | Silent auto-purge, recorded in ledger | "Silent" = no prompt, not no trace |
| 6 | Gitignored stragglers | **Bounded** force-add: allowlist `{.sdd-session.json, reports/.dispatch-log}` | Complete archive without committing stray ignored files (M2) |
| 7 | Commit ownership | Script commits via pathspec, after clean-index assert + staged-subset verify | Deterministic; provably can't sweep a concurrent agent's changes (B2) |
| 8 | Records | Commit message + `ARCHIVE-LOG.md` ledger | Ledger is the only trace of the purge |
| 9 | PR / detached push | No archive | Work not on base yet; flippable |
| 10 | Home | Existing `finishing` skill + helper script | Not a new skill; SSOT for completion |
| 11 | Path confinement (review B1) | Canonicalize `SRC`; require strictly under `docs/imp-plans/`, not under `archive/`, dated-convention basename | A stale/malformed `.active-feature` can't move an arbitrary dir |
| 12 | Collision safety (review M1) | No-op only when `DEST` exists **and** `SRC` gone; both-exist → fail loudly | Partial/duplicate runs surface instead of silently skipping |
| 13 | Index safety (review B2) | Assert clean index before move; verify staged set ⊆ allowed paths; commit by pathspec | Pre-staged unrelated work can't ride the archive commit |
| 14 | Feature-context (review Minor) | Absent `.active-feature` + SDD artifacts → fail; else clean skip | Missing-pointer closeout failure no longer silent |

## 13. Acceptance Criteria

- [ ] On Option-1 merge (worktree & branch), the completed feature dir is archived to `docs/imp-plans/archive/<feature>/` and arrives on base via the merge.
- [ ] On direct-on-main, the new "Archive & finalize" action archives + commits on main.
- [ ] PR, detached-HEAD push, keep, and discard do **not** archive.
- [ ] The whole feature dir moves — including uncommitted reports and gitignored manifest — and the committed archive is complete (clean `git status`).
- [ ] `.superpowers/brainstorm/` is purged; the purge is recorded in `ARCHIVE-LOG.md`.
- [ ] Re-running on an already-archived feature (`DEST` exists, `SRC` gone) is a clean no-op; `DEST` exists with `SRC` still present **fails loudly** (collision).
- [ ] An empty/unresolved `ROOT` runs **no** destructive command.
- [ ] A malformed `.active-feature` (absolute, `..`, symlink-escape, target outside `docs/imp-plans/`, bad basename) **aborts before any move**.
- [ ] A pre-staged unrelated file in the index **aborts** the archive before any move; an unstaged dirty file is never in the archive commit.
- [ ] Only allowlisted ignored files are force-added; an unexpected ignored file under the archive path **aborts**.
- [ ] Absent `.active-feature` with SDD artifacts present **fails** (closeout invariant); absent with none is a clean skip.
- [ ] The finishing branch matrix is covered: archive **fires** for worktree/branch merge + on-main; **skipped** for PR, detached push, keep, discard.
- [ ] `finishing` reads `.active-feature` for the archive before Step 7 removes it.
- [ ] Skill count stays 15; all static + integration suites green.
