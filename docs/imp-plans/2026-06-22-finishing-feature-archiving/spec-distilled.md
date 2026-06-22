# finishing-feature-archiving — Distilled Implementation Spec

> **Source**: `spec.md` (200 lines, 14 decisions). **Distilled**: 2026-06-22.
> **For**: Plan writer and implementation agents ONLY. For full rationale, see source.
> **Archetype**: Extension of the existing `finishing-a-development-branch` skill (no behavior removed).

## Contract Facts

- **Core invariant**: archive exactly when the finish action lands the work on the base branch in this same operation.
- **Home**: `skills/finishing-a-development-branch/` — new helper `scripts/archive-feature.sh` + SKILL.md changes. **Not** a new skill; skill count stays 15.
- **Hard dependency**: the cross-skill *convention audit* feature must merge to `main` first (so this feature can assert that every durable artifact lives under `docs/imp-plans/<feature>/`). Distillation/planning may proceed; implementation waits on that merge.
- **Archive destination**: `docs/imp-plans/archive/<feature>/`.
- **Feature-name convention** (basename of `.active-feature`): `^[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9-]+$`.
- **Confinement**: canonicalized `SRC` must resolve strictly under `$ROOT/docs/imp-plans/` and **not** under `$ROOT/docs/imp-plans/archive/`.
- **Force-add allowlist** (gitignored stragglers permitted in the commit): `{.sdd-session.json, reports/.dispatch-log}`.
- **Purge target** (gitignored): `$ROOT/.superpowers/brainstorm/`.
- **Ledger**: `docs/imp-plans/archive/ARCHIVE-LOG.md`, append one entry per archive:
  ```
  ## <feature-name>
  - Archived: <date> · trigger: <merge|on-main>
  - Source: docs/imp-plans/<feature>/ → docs/imp-plans/archive/<feature>/ (<N> files)
  - Purged .superpowers/brainstorm/: <session-ids or "none"> (<M> sessions)
  ```
- **Commit message** (script owns the commit, via explicit pathspec):
  ```
  chore: archive completed feature <name>

  Archived docs/imp-plans/<feature>/ → docs/imp-plans/archive/<feature>/ (<N> files)
  Purged .superpowers/brainstorm/: <session-ids> (<M> sessions)
  Trigger: <merge|on-main>

  Prompted by Aaron; Co-Authored by Claude
  ```
- `.active-feature` is read in the **current checkout** for the archive **before** Step 7 of `finishing` deletes it.

## Open Decisions

None — all 14 decisions are resolved.

## Decision Summary

| # | Decision | Chosen |
|---|----------|--------|
| 1 | Archive unit | Whole feature dir → `docs/imp-plans/archive/<feature>/` |
| 2 | Trigger | "Work reaches base in this op" → merge + on-main only |
| 3 | Merge sequencing | Before merge, on the feature branch, reading local `.active-feature` |
| 4 | On-main UX | New "Archive & finalize" menu when `branch == base` |
| 5 | Visual litter | Silent auto-purge, recorded in ledger |
| 6 | Gitignored stragglers | Bounded force-add: allowlist `{.sdd-session.json, reports/.dispatch-log}` |
| 7 | Commit ownership | Script commits via pathspec, after clean-index assert + staged-subset verify |
| 8 | Records | Commit message + `ARCHIVE-LOG.md` ledger |
| 9 | PR / detached push | No archive (work not on base yet; flippable) |
| 10 | Home | Existing `finishing` skill + helper script |
| 11 | Path confinement | Canonicalize `SRC`; require strictly under `docs/imp-plans/`, not under `archive/`, dated-convention basename |
| 12 | Collision safety | No-op only when `DEST` exists **and** `SRC` gone; both-exist → fail loudly |
| 13 | Index safety | Assert clean index before move; verify staged set ⊆ allowed paths; commit by pathspec |
| 14 | Feature-context | Absent `.active-feature` + SDD artifacts → fail; else clean skip |

## Component Specifications

### Trigger invariant

Archive exactly when the finish action lands the work on base in this same operation. **Archive**: Option-1 merge (run on the feature branch **before** `git checkout base && merge`, so the archive rides into base) and on-main "Archive & finalize" (commit on base). **Skip**: Option 2 push+PR, detached-HEAD push, keep-as-is / keep-active, discard.

### `archive-feature.sh`

Path: `skills/finishing-a-development-branch/scripts/archive-feature.sh`. Inputs: none beyond CWD (optional `--feature-dir`, same confinement). The script owns the whole operation — no skipped step, no inconsistent commit.

1. **Resolve & guard.** `ROOT="$(git rev-parse --show-toplevel)"` — abort if empty/git fails; assert `ROOT` absolute and `$ROOT/.git` resolves. Read `FEATURE` from `$ROOT/.active-feature` (or `--feature-dir`). Canonicalize `SRC="$(cd "$ROOT/$FEATURE" 2>/dev/null && pwd -P)"`, `NAME="$(basename "${FEATURE%/}")"`, `DEST="$ROOT/docs/imp-plans/archive/$NAME"`.
2. **Feature-context** (`.active-feature` absent/empty, **or** `SRC` gone + `DEST` absent → stale pointer): SDD artifacts present (`docs/imp-plans/*/reports/` or `.sdd-session.json`) → **fail loudly**; none present → clean skip, exit 0.
3. **Archive-state branch + confine** — no `rm`/`mv` until `ROOT`/`SRC`/`DEST` non-empty and asserts pass:
   - `SRC` exists, `DEST` absent → normal: assert confinement (Contract Facts — under `docs/imp-plans/`, not under `archive/`, `NAME` matches regex) or abort with no move.
   - `SRC` gone, `DEST` exists → already archived; clean no-op, exit 0.
   - `SRC` exists, `DEST` exists → collision / partial run; **fail loudly**, nothing destructive.
4. **Move whole feature dir.** `mkdir -p "$ROOT/docs/imp-plans/archive"`; filesystem `mv "$ROOT/$FEATURE" "$DEST"` (tracked + untracked + gitignored together).
5. **Purge litter.** `PURGE="$ROOT/.superpowers/brainstorm"`; if present, capture session ids then `rm -rf "$PURGE"` (asserted absolute path); absent → skip, ledger records "none".
6. **Append ledger** (Contract Facts shape) to `ARCHIVE-LOG.md` (create if absent).
7. **Clean-index, bounded staging, scoped commit.**
   - Before the move, assert `git -C "$ROOT" diff --cached --quiet` (empty index) or abort.
   - Pre-move, ignored files under `$SRC` (`git status --ignored --porcelain`) must be ⊆ allowlist; any other → abort (or `--allow-ignored <path>`).
   - Stage by pathspec (`git add -A -- <old> <DEST> <ledger>`); force-add only allowlisted stragglers at `$DEST`.
   - Verify staged set (`git diff --cached --name-only`) ⊆ {old, new, ledger, allowlisted stragglers} or abort; commit by pathspec with the Contract-Facts message.

### `finishing-a-development-branch/SKILL.md` integration

- **Step 2 (detect environment)**: add the `current_branch == base_branch` discriminator → routes to the on-main menu.
- **On-main menu** (new, when `branch == base`): `1. Archive & finalize` → run the script on base; `2. Keep active` / `3. Discard` → no archive.
- **Step 5 / Option 1 (merge)**: run `archive-feature.sh` on the feature branch **before** `git checkout base && merge`. Worktree/branch cleanup (Step 6) and Step 7 unchanged, still after merge-verify.
- **Step 7 (cleanup)**: `.active-feature`/`.allow-main` removal runs **after** archiving.
- **Options 2/3/4 and detached-HEAD**: no archive call.

### Out of scope

- Vault honesty-check copies (`$VAULT_DIR/References/SDD/honesty-checks/`) — cross-session record, not touched.
- Handoff bundles (`~/.claude-codex-handoff/bundles/`) — separate tool, own lifecycle.
- Standalone archive invocation outside `finishing` — declined. Residual risk: a run completing without invoking `finishing` won't archive (same caveat as existing worktree cleanup / `.active-feature` removal).

## Acceptance Criteria

- [ ] On Option-1 merge (worktree & branch), the feature dir is archived to `docs/imp-plans/archive/<feature>/` and arrives on base via the merge.
- [ ] On direct-on-main, the new "Archive & finalize" action archives + commits on main.
- [ ] PR, detached-HEAD push, keep, and discard do **not** archive.
- [ ] The whole feature dir moves — including uncommitted reports and gitignored manifest — and the committed archive is complete (clean `git status`).
- [ ] `.superpowers/brainstorm/` is purged; the purge is recorded in `ARCHIVE-LOG.md`.
- [ ] Re-running on an already-archived feature (`DEST` exists, `SRC` gone) is a clean no-op; `DEST` exists with `SRC` still present **fails loudly**.
- [ ] An empty/unresolved `ROOT` runs **no** destructive command.
- [ ] A malformed `.active-feature` (absolute, `..`, symlink-escape, target outside `docs/imp-plans/`, bad basename) **aborts before any move**.
- [ ] A pre-staged unrelated file in the index **aborts** before any move; an unstaged dirty file is never in the archive commit.
- [ ] Only allowlisted ignored files are force-added; an unexpected ignored file under the archive path **aborts**.
- [ ] Absent `.active-feature` with SDD artifacts present **fails**; absent with none is a clean skip.
- [ ] The finishing branch matrix is covered: archive **fires** for worktree/branch merge + on-main; **skipped** for PR, detached push, keep, discard.
- [ ] `finishing` reads `.active-feature` for the archive before Step 7 removes it.
- [ ] Skill count stays 15; all static + integration suites green.
