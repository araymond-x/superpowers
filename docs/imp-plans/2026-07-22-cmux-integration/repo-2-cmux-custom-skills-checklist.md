# Repo-2 — cmux-custom-skills — Creation Checklist (standalone, NOT part of the SDD manifest)

> **Scope boundary (Decision 19):** This is a **separate repo-local deliverable**. It is created in a **different repo** (`~/projects/claude-custom/cmux-custom-skills`), which has **no SDD enforcement hooks**, so it is deliberately **not** a task in the superpowers `plan.md` and **not** in `plan-manifest.txt`. Cross-repo commits would bypass the SDD plan's git-reality evidence. Execute this as direct work in the new repo, **before** the superpowers repo-3 plan's Task 0 can pass (Task 0 asserts these symlinks resolve).
>
> **Ordering:** repo-1 (telemetry-exp picker) → **repo-2 (this)** → repo-3 (superpowers plan). This is mechanical vendoring; treat it as a short checklist, not a gated plan.
>
> **Pristine rule:** vendored files under `skills/` are NEVER locally edited. Fork-specific cmux guidance lives in the superpowers `CLAUDE.md`, not here.

## What ships

| Path | What |
|---|---|
| `skills/{cmux,cmux-workspace,cmux-markdown,cmux-diagnostics}/` | Pristine vendored copies from `manaflow-ai/cmux` at a pinned SHA (layout mirrors `big-build-patterns`: skills under `skills/<name>/`) |
| `VENDOR.md` | Upstream repo URL, pinned commit SHA, vendor date, the 4 skill names |
| `sync-cmux-skills.sh` | Re-vendor from upstream at a given ref (default `main`); replaces the 4 dirs wholesale; rewrites `VENDOR.md` with the resolved SHA; prints a diff summary; never merges |
| `verify-install.sh` | Asserts the 4 `~/.claude/skills/<name>` symlinks resolve into this repo AND `VENDOR.md` records a SHA |
| `~/.claude/skills/{cmux,cmux-workspace,cmux-markdown,cmux-diagnostics}` | NEW symlinks → `<repo>/skills/<name>` (install step; no command stubs — flat personal skills auto-list in `/skills`) |

## Checklist

- [ ] **1. Create the repo.**
  ```bash
  mkdir -p ~/projects/claude-custom/cmux-custom-skills && cd ~/projects/claude-custom/cmux-custom-skills
  git init
  ```

- [ ] **2. Write `sync-cmux-skills.sh`** — takes an upstream ref (default `main`), sparse-clones `manaflow-ai/cmux` at that ref into a temp dir, copies the 4 skill dirs wholesale into `skills/`, resolves the ref to a concrete SHA, rewrites `VENDOR.md`, prints a `git status --short` / diff summary. Never merges (pristine replacement is safe). Behavior sketch:
  ```bash
  #!/usr/bin/env bash
  set -euo pipefail
  REF="${1:-main}"
  SKILLS=(cmux cmux-workspace cmux-markdown cmux-diagnostics)
  TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
  git clone --depth 1 --branch "$REF" --filter=blob:none --sparse \
    https://github.com/manaflow-ai/cmux.git "$TMP/cmux" 2>/dev/null \
    || git clone --filter=blob:none --sparse https://github.com/manaflow-ai/cmux.git "$TMP/cmux"
  ( cd "$TMP/cmux" && git checkout "$REF" 2>/dev/null || true )
  # Locate the skills in upstream (path TBD — verify against upstream layout at run time).
  SHA="$(cd "$TMP/cmux" && git rev-parse HEAD)"
  mkdir -p skills
  for s in "${SKILLS[@]}"; do
    rm -rf "skills/$s"
    cp -R "$TMP/cmux/<upstream-skills-path>/$s" "skills/$s"   # <-- resolve <upstream-skills-path> at run time
  done
  # rewrite VENDOR.md with URL, $SHA, date, skill list
  git status --short
  ```
  > **Resolve at run time:** the exact upstream path to the skill dirs (`<upstream-skills-path>`) must be confirmed against the live `manaflow-ai/cmux` layout — do not guess. Freeze the resolved SHA in `VENDOR.md`.

- [ ] **3. Run the sync once** to vendor the 4 skills and generate `VENDOR.md`:
  ```bash
  bash sync-cmux-skills.sh main
  ```
  Confirm `skills/cmux/SKILL.md` (and the other three) exist and `VENDOR.md` records the SHA.

- [ ] **4. Write `verify-install.sh`:**
  ```bash
  #!/usr/bin/env bash
  set -euo pipefail
  REPO="$(cd "$(dirname "$0")" && pwd)"
  fail=0
  for s in cmux cmux-workspace cmux-markdown cmux-diagnostics; do
    link="$HOME/.claude/skills/$s"
    tgt="$(readlink "$link" 2>/dev/null || true)"
    case "$tgt" in "$REPO/skills/$s") : ;; *) echo "FAIL: $link -> ${tgt:-(missing)}"; fail=1;; esac
    [ -e "$link/SKILL.md" ] || { echo "FAIL: $link/SKILL.md unresolved"; fail=1; }
  done
  grep -qiE 'sha|commit' VENDOR.md || { echo "FAIL: VENDOR.md records no SHA"; fail=1; }
  [ "$fail" = 0 ] && echo "OK: 4 cmux skill symlinks resolve + VENDOR.md SHA present"
  exit "$fail"
  ```

- [ ] **5. Install the symlinks:**
  ```bash
  for s in cmux cmux-workspace cmux-markdown cmux-diagnostics; do
    ln -s ~/projects/claude-custom/cmux-custom-skills/skills/$s ~/.claude/skills/$s
  done
  ```

- [ ] **6. Verify + commit:**
  ```bash
  bash verify-install.sh   # must print OK
  git add -A && git commit -m "feat: vendor 4 cmux skills at pinned SHA + sync/verify scripts"
  ```

- [ ] **7. Acceptance:** open a fresh Claude session and confirm the 4 cmux skills auto-list in the skill picker. This unblocks the superpowers repo-3 Task 0 symlink assertion.
