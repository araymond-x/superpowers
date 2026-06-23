# Upstream v6 Sync Assessment (obra/superpowers → our fork)

**Date:** 2026-06-22
**Assessor:** Claude (Opus 4.8) + advisor review
**Upstream HEAD:** `896224c` — Release v6.0.3 (2026-06-18)
**Our last documented sync:** `80fc5c5` (2026-05-07), merge-base `f2cbfbe`
**Divergence:** 169 commits upstream not in us · 319 commits us not in upstream

---

## Bottom line

**This is curated cherry-pick territory, NOT `git merge upstream/main`.** All 13 SKILL.md
files upstream touched are files we have already rewritten, so every one is a guaranteed
conflict — and the headline v6 feature (the SDD review rewrite) collides head-on with our
hook-based enforcement architecture. A wholesale merge would be days of conflict surgery
against our own direction. Instead: port a handful of high-value, low-risk content fixes by
hand, and treat the SDD rewrite as one strategic decision to make deliberately.

The single most valuable finding is a **confirmed latent bug in our own fork** (see A1).

---

## What v6 actually is

v6.0.0 (2026-06-16) is a major release. Headlines:
1. **SDD review rewrite** — two per-task reviewers collapsed to one; file-based handoff;
   enforced model naming; anti-gaming rules. Eval-claimed ~2× faster, ~50% fewer tokens.
2. **Three new harnesses** — Kimi Code, Pi, Antigravity.
3. **Brainstorm visual companion security model** — per-session key auth, sandboxed file
   server, restart/reconnect survival.
4. **Vendor-neutral rewrite** — "use the Task tool" → "dispatch a subagent"; "Claude" →
   "your agent"; per-harness tool reference. Touches all 13 SKILL.md files.

v6.0.1–v6.0.3 are install/Codex fixes + moving SDD scratch out of `.git/`.

---

## Category A — Take now (high value, low risk)

### A1. systematic-debugging extended-thinking keyword fix ⭐ CONFIRMED BUG IN OUR FORK
- **Upstream:** `90e1721` (#1558). Changes `"Ultrathink this"` → `"Ultra-think this"`.
- **Our state:** `skills/systematic-debugging/SKILL.md:263` contains the literal string
  `"Ultrathink this"` — the exact keyword Claude Code's scanner watches for. Loading our
  systematic-debugging skill silently trips **max-budget extended thinking** on the session.
  Swept all skills: this is the only occurrence (genuinely one line).
- **Risk:** zero. The hyphen reads identically.
- **Action:** hand-edit line 263 to `"Ultra-think this"`. One character.

### A2. Shell-lint harness (`scripts/lint-shell.sh`)
- **Upstream:** `21b44e4`. A standalone ShellCheck + shfmt wrapper (lint changed/all/explicit
  shell files, optional `--format`/`--strict`).
- **Why it fits US specifically:** our CLAUDE.md catalogs a *string* of shell-hook bugs —
  the SIGPIPE fail-open in `sdd-skill-enforcement-hook.sh`, `set -u` empty-var exits, BSD
  `sed` brace failures. A shellcheck-based linter targets exactly that bug class. It would
  cover our 13 shell scripts under `skills/` + `hooks/`. Arguably higher value for our fork
  (7 baselined enforcement hooks) than it was for upstream.
- **Do NOT take** upstream's `.pre-commit-config.yaml` verbatim — it lints the `evals/`
  submodule (`ruff`/`ty` on `evals/*.py`), which we don't have.
- **Action:** port `scripts/lint-shell.sh` (near-clean, standalone). Optionally wire into our
  existing test harness rather than pre-commit. Re-baseline hooks if it prompts any fixes.

### A3. writing-skills authoring additions
- **Upstream:** `cbc8273` (+ follow-ups `fdb0f42`, `1aa45d2`). Adds "Match the Form to the
  Failure" (a table for picking prohibition vs. worked-example guidance) and "Micro-Test
  Wording" (sample a phrasing N times against a no-guidance control before committing).
- **Why it fits:** we author/maintain skills constantly; both are pure authoring guidance,
  no behavioral coupling. Aligns with `docs/prompting-best-practices.md`.
- **Caveat:** the commit is entangled with the vendor-neutral prose rewrite (A-phase). **Port
  the two new sections' content by hand** — do not `git cherry-pick` the commit (it drags in
  CSO→SDO renames and "your agent" prose we don't want — see D3).

### A4. Worktree global-dir removal (aligns SKILL.md with our OWN convention)
- **Upstream:** `d00f4ad` (#1476) removes the legacy `~/.config/superpowers/worktrees/`
  global fallback; `ce95985` (#1522) fixes step numbering.
- **Our inconsistency:** `skills/using-git-worktrees/SKILL.md` lines 79/97/106 STILL reference
  the global `~/.config/superpowers/worktrees/` path — but our CLAUDE.md "Worktree Convention"
  says worktrees go in `<project-root>/.worktrees/<feature>/` **ONLY**. Upstream's removal
  brings the SKILL.md in line with our own stated rule. We're fixing our own drift.
- **Action:** hand-port the global-path removal into our SKILL.md (our copy is heavily
  customized; manual port, not cherry-pick).

---

## Category B — The one strategic decision: the v6 SDD review rewrite

This is the centerpiece of the whole assessment. Do not pre-decide it — it carries
eval-backed evidence (~2× faster, ~50% fewer tokens in upstream's runs) that it solved the
**same** "expensive and easy to game" problems our hooks target. Convergent, not just
colliding. Decompose:

### B-neutral — cost wins that are architecture-independent (takeable regardless of 1-vs-2 reviewers)
- **File-based handoff** (`task-brief`, `review-package` scripts): task text and review diff
  written to files instead of pasted into context. Upstream calls the pasted diff "the single
  biggest reviewer cost." We already move some artifacts to files (reports/, context-summary);
  this extends the pattern. Compatible with our model.
- **Enforced model naming per dispatch:** every dispatch must state its model, with guidance
  toward cheaper tiers. Our `~/.claude/rules/workflows.md` already *wants* this ("pin
  `opts.model` per step or subagents inherit the session model and risk rate limits") —
  upstream made it an enforced template requirement. Strong fit; consider adopting the
  enforcement.
- **Progress ledger for resume:** lets a controller that lost context resume instead of
  redoing finished work. Compare to our `context-summary.py` + checkpoint files — may be
  redundant with what we have, or may improve it. Worth a side-by-side.

### B-fork — the genuine strategic fork (one decision, real stakes)
- **Upstream v6:** ONE `task-reviewer-prompt.md` per task → two verdicts (spec + quality) in
  one pass, plus one broad whole-branch review at the end on the top model.
- **Our fork:** TWO reviewers per task (`spec-reviewer-prompt.md` +
  `code-quality-reviewer-prompt.md`) + partner review + dispatch-provenance enforcement.
- **The hard dependency (confirmed in code):**
  `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` classifies dispatches
  into `spec-review`/`quality-review`/`trace-audit`/`partner-review` (lines 163–166), logs
  each by type (169), and **line 478 hard-blocks** any task dispatch missing a separate
  `task-NNN-spec-review.md`. Dropping in v6's combined prompt would make our hook reject every
  dispatch. So adopting v6's review model is **not a prompt swap — it's rearchitecting the
  enforcement layer** (hook checks 4b/4c, dispatch provenance, partner gate, the two retired
  prompt files we still ship).
- **The decision for the user:** upstream brings outside eval data suggesting our
  two-reviewer + partner + provenance model may now be **over-engineered on cost**. Weigh
  discipline-and-auditability (our investment) vs. cost-and-speed (their evidence). This is
  the real call in this entire sync. Options:
  - (a) Keep our model; selectively adopt only B-neutral cost wins.
  - (b) Pilot v6's one-reviewer model in a throwaway branch, measure against our enforcement
    suite, decide on evidence.
  - (c) Full migration to v6 SDD — largest effort; unwinds significant fork investment.

---

## Category C — Evaluate, lower priority

### C1. Brainstorm visual companion security hardening
- **Upstream:** per-session key auth (cookie + WS), sandboxed file server (no symlinks/
  dotfiles/path-escape, owner-only key files), 4h idle timeout, restart/reconnect survival,
  safe `stop-server.sh` process-ownership check.
- **Calibrate to OUR threat model:** we run single-user on localhost. The headline wins
  (DNS-rebinding, routable remote hosts, shared machines) only bite if you brainstorm from a
  remote/shared box — not our normal case. The *non*-security pieces (reuse-port-on-restart,
  reconnect overlay, ownership-checked shutdown that won't kill an unrelated `node`) are
  quality-of-life wins that DO apply locally.
- **Action:** low urgency. If we ever run the companion off-localhost, the auth model becomes
  important. The lifecycle/restart improvements are nice-to-have now. Sizable change to the
  brainstorm server — only worth it if we're actively using the companion.

---

## Category D — Skip / not applicable

- **D1. v6.0.3 `.git/` SDD-scratch fix** — N/A. We write artifacts to
  `docs/imp-plans/<feature>/reports/`, never `.git/`. Upstream's new `.superpowers/sdd/`
  layout diverges from ours entirely.
- **D2. New harness support (Kimi, Pi, Antigravity)** — N/A. We're a Claude-Code symlink
  install (+ Codex via the handoff bridge). No value; adds harness manifests/tests we'd never
  exercise.
- **D3. Vendor-neutral prose rewrite** ("your agent", CSO→SDO, per-harness tool refs) — SKIP.
  It runs *counter* to our deliberately Claude-Code-specific fork, and it is the **primary
  source of the 13 SKILL.md conflicts**. Taking it would be churn against our direction. This
  is why A3/A4 must be content-ported by hand, not cherry-picked (the good content rides in
  the same commits as this prose rewrite).
- **D4. Evals submodule split + `.pre-commit-config.yaml`** — N/A. We don't carry the evals
  submodule (our testing is the symlink-install suite documented in CLAUDE.md).

---

## Merge mechanics note

- Do **not** `git merge upstream/main` or `git cherry-pick` the SKILL.md commits. Every SKILL
  we'd touch (systematic-debugging, writing-skills, using-git-worktrees) is heavily customized;
  the upstream commits are tangled with the D3 prose rewrite.
- **Method:** hand-port the specific content deltas (A1 one char, A3 two sections, A4 path
  removal) into our copies. A2 lint script is a near-clean standalone add.
- After any SKILL edit: run `python3 tests/ARaymond-skill-regression/validate-all-skills.py`.
- After any hook edit (if B is pursued): re-baseline via
  `bash tests/ARaymond-hook-baseline/check-hooks.sh --capture` + commit `baseline.txt`.
- Update `docs/ARaymond-customization-manifest.md` "Upstream Sync Log" and the "Last sync"
  line in CLAUDE.md with whatever we actually take.

---

## Recommended sequence

1. **A1 now** (confirmed bug, one char) — highest value/effort ratio in the whole set.
2. **A2 + A4** (small, self-contained, A4 fixes our own drift).
3. **A3** (authoring guidance, content-port).
4. **B** — schedule a deliberate decision session; default to (a)/(b), not (c).
5. **C1 / D-items** — note and defer / skip.
