You are a focused implementation engineer. Your job is to build exactly what the spec asks — nothing more, nothing less. Follow TDD strictly (RED → GREEN → verify). When requirements are clear, execute them precisely; when ambiguous, ask before assuming.

You are implementing Task 0: Promote sdd-skill-enforcement-hook.sh to blocking.

Work from: `/Users/araymond/projects/claude-custom/superpowers/.worktrees/sdd-enforcement-hardening` (a git worktree on branch `sdd-enforcement-hardening` — this is the authoritative checkout for execution).

## Task Description (VERBATIM from plan.md, Task 0)

### Task 0: Promote sdd-skill-enforcement-hook.sh to blocking

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-skill-enforcement-hook.sh`
- Test: `tests/unit/test_sdd_skill_enforcement.py` (create)

**Pattern References:** `bypass-env-var` (mirror `SUPERPOWERS_VALIDATOR_BYPASS`), `bash-hook-subprocess-test` (subprocess `run_hook` style).

**Context:** Today this hook emits `additionalContext` and `exit 0` (advisory). The spec promotes it to blocking: explicit SDD imperative + impl-file + skill-not-loaded + no bypass ⇒ `exit 2`. The detection regex `(invoke|use|run|follow|start|let'?s use)\b.{0,20}(subagent-driven-development|sdd)` has been **verified to work and discriminate correctly under both ugrep 7.5 and stock `/usr/bin/grep -iE`** (BSD) — imperatives match, casual mentions ("reading about subagent-driven-development", "the SDD hook") do not. Keep the `SKILL_LOADED` allow, the impl-file path filter, and all early exits.

- [ ] **Step 1: Write the failing tests** in `tests/unit/test_sdd_skill_enforcement.py`

```python
"""C5: sdd-skill-enforcement-hook.sh promoted to blocking.
Run: .venv/bin/python3 -m pytest tests/unit/test_sdd_skill_enforcement.py -v
"""
import json
import os
import subprocess

HOOK_PATH = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..",
    "skills", "subagent-driven-development", "scripts", "sdd-skill-enforcement-hook.sh",
))


def _transcript(tmp_path, user_text, skill_loaded=False):
    """Write a JSONL transcript with one user line (+ optional Skill tool line).

    IMPORTANT: emit COMPACT JSON (separators=(",", ":")). The hook greps the
    transcript for the literal `"role":"user"` and `"name":"Skill"` (no spaces) —
    matching real Claude Code transcripts. json.dumps' default spacing
    (`"role": "user"`) would NOT match the hook's grep, so the hook would
    short-circuit at its early `exit 0` and the block tests could never go GREEN.
    """
    sep = (",", ":")
    lines = [json.dumps({"role": "user", "content": user_text}, separators=sep)]
    if skill_loaded:
        lines.append(json.dumps({"role": "assistant",
                                 "content": [{"type": "tool_use", "name": "Skill",
                                              "input": {"skill": "superpowers:subagent-driven-development"}}]},
                                separators=sep))
    p = tmp_path / "transcript.jsonl"
    p.write_text("\n".join(lines) + "\n")
    return str(p)


def run_hook(file_path, transcript_path, env_extra=None):
    payload = json.dumps({"tool_input": {"file_path": file_path},
                          "transcript_path": transcript_path})
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(["bash", HOOK_PATH], input=payload,
                          capture_output=True, text=True, timeout=10, env=env)


def test_blocks_when_sdd_requested_skill_not_loaded(tmp_path):
    t = _transcript(tmp_path, "please invoke subagent-driven-development", skill_loaded=False)
    r = run_hook("src/app/feature.py", t)
    assert r.returncode == 2, f"stdout={r.stdout} stderr={r.stderr}"
    assert "subagent-driven-development" in r.stderr


def test_allows_when_skill_loaded(tmp_path):
    t = _transcript(tmp_path, "let's use SDD", skill_loaded=True)
    r = run_hook("src/app/feature.py", t)
    assert r.returncode == 0


def test_casual_mention_does_not_block(tmp_path):
    t = _transcript(tmp_path, "I was reading about subagent-driven-development in the docs", skill_loaded=False)
    r = run_hook("src/app/feature.py", t)
    assert r.returncode == 0


def test_non_impl_file_does_not_block(tmp_path):
    t = _transcript(tmp_path, "invoke subagent-driven-development", skill_loaded=False)
    r = run_hook("docs/notes.md", t)
    assert r.returncode == 0


def test_bypass_env_var_recovers(tmp_path):
    t = _transcript(tmp_path, "invoke subagent-driven-development", skill_loaded=False)
    r = run_hook("src/app/feature.py", t, env_extra={"SUPERPOWERS_SDD_BYPASS": "1"})
    assert r.returncode == 0
    assert "SUPERPOWERS_SDD_BYPASS" in r.stderr


def test_no_sdd_request_allows(tmp_path):
    t = _transcript(tmp_path, "fix the login bug", skill_loaded=False)
    r = run_hook("src/app/feature.py", t)
    assert r.returncode == 0
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python3 -m pytest tests/unit/test_sdd_skill_enforcement.py -v`
Expected: `test_blocks_*` FAILS (current hook returns 0, not 2); `test_bypass_*` FAILS (no bypass handling yet); `test_casual_mention_*` likely FAILS (current bare-mention regex matches it but current hook returns 0 anyway, so it may pass vacuously — the block tests are the real RED).

- [ ] **Step 3: Tighten the detection regex.** In `sdd-skill-enforcement-hook.sh`, replace the SDD-request grep (currently `grep ... | grep -qiE '(subagent-driven-development|SDD|superpowers:subagent-driven|invoke.*sdd|use.*sdd|follow.*sdd)'`) with the imperative-only pattern:

```bash
  # Require an explicit SDD imperative (not a bare mention) to avoid false blocks.
  # Verified under ugrep 7.5 and stock /usr/bin/grep -iE (BSD): imperatives match,
  # casual mentions ("reading about subagent-driven-development", "the SDD hook") do not.
  if grep '"role":"user"' "$TRANSCRIPT_PATH" | grep -qiE "(invoke|use|run|follow|start|let'?s use)\b.{0,20}(subagent-driven-development|sdd)" 2>/dev/null; then
    SDD_REQUESTED=true
  fi
```

- [ ] **Step 4: Add the bypass + block.** Replace the advisory `additionalContext` JSON emission (the final `cat << HOOKJSON ... HOOKJSON; exit 0` block) with a `SUPERPOWERS_SDD_BYPASS` check followed by a blocking exit. Keep the same warning text on stderr:

```bash
# ─── SDD requested but skill NOT loaded — bypass or block ─────────────────
WARNING_MSG="BLOCKED: The user requested subagent-driven-development but you have not loaded the skill via the Skill tool. You are writing implementation code directly, bypassing the SDD review cycle, enforcement hooks, and quality gates. Load the skill now: invoke superpowers:subagent-driven-development. Direct implementation without the skill means zero spec reviews, zero code quality reviews, and no hook enforcement."

# Emergency escape hatch (mirrors SUPERPOWERS_VALIDATOR_BYPASS): allow + warn.
if [ -n "${SUPERPOWERS_SDD_BYPASS:-}" ]; then
  echo "WARNING: $WARNING_MSG (bypassed via SUPERPOWERS_SDD_BYPASS)" >&2
  exit 0
fi

echo "$WARNING_MSG" >&2
exit 2
```

> Note: this hook uses `set -o pipefail` but **not** `set -u` today; `${SUPERPOWERS_SDD_BYPASS:-}` is written defensively regardless. Do not add `set -u` (jq pipe chains produce empty vars — see CLAUDE.md Hook Development Gotchas).

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.venv/bin/python3 -m pytest tests/unit/test_sdd_skill_enforcement.py -v`
Expected: all 6 PASS.

- [ ] **Step 6: Commit**

```bash
git add skills/subagent-driven-development/scripts/sdd-skill-enforcement-hook.sh tests/unit/test_sdd_skill_enforcement.py
git commit -m "feat(sdd): promote skill-enforcement hook to blocking with bypass"
```

## Context (scene-setting)

This hook (`sdd-skill-enforcement-hook.sh`) is a global PreToolUse Write|Edit hook registered in `~/.claude/settings.json`. Today it is ADVISORY: it greps the session transcript and, when SDD was requested but the skill was never loaded and the file being written matches an implementation directory, it injects an advisory `additionalContext` and `exit 0`. You are promoting it to BLOCKING (`exit 2`), with a `SUPERPOWERS_SDD_BYPASS` escape hatch.

IMPORTANT: the LIVE hook resolves to the MAIN checkout, so your change here takes effect only at merge — you are editing the worktree copy, and the tests exercise the worktree copy via `__file__`-relative paths (`HOOK_PATH` resolves up two dirs from the test file to the worktree's `skills/...`). This is intentional and correct; do not try to point tests at the main checkout.

## Contract Constraints (verbatim — non-negotiable)

- **Dispatch-log provenance line format** (written by `sdd-pre-dispatch-hook.sh`): reviewer lines are `<ts> DISPATCH reviewer task=<N> type=<spec-review|quality-review|partner-review|trace-audit>`; implementer lines are `<ts> DISPATCH implementer task=<N> type=implementer`. Grep keyed on the substring `task=<N> type=<review_type>`.
- **Two distinct "minimum" signals — do not conflate:** FILE signal `reports/task-NNN-quality-review-minimum-tier.md` vs PLAN-DECLARATION `review_tier: minimum`.
- **Manifest is git-root-relative.** All `paths.*` resolve via `git rev-parse --show-toplevel`. `MANIFEST_TASK_START = task_range[0]`.
- **Module boundary lifecycle** (`transition-module.py`): Step 1 validate → Step 3 archive → Step 4 advance → Step 5 truncate; live log intact during Step 1.
- **Tier review modes:** `spec_review_mode` / `quality_review_mode` may be `"skip"`.
- **Block convention:** `exit 2` + a stderr message (matches `sdd-pre-dispatch-hook.sh`). The bypass env var mirrors `SUPERPOWERS_VALIDATOR_BYPASS` (set ⇒ allow + stderr warning). **← THE constraint governing your Step 4.**
- **Archive-awareness applies to EXACTLY two lookups** (N4 + N10). All other report globs stay flat.

If your implementation contradicts any constraint, STOP and report BLOCKED with the specific conflict — do not work around it.

## Source Files

None (the plan declares Source Contracts: None). BUT you MUST read the current hook before editing:
- `skills/subagent-driven-development/scripts/sdd-skill-enforcement-hook.sh`

Read it to confirm in place: `set -o pipefail` (NO `set -u`); the impl-file path filter (`src/|app/|frontend/|components/|hooks/|api/|types/|services/`); the `SKILL_LOADED` allow branch; the `SDD_REQUESTED` grep you will tighten in Step 3; and the final advisory `cat << HOOKJSON ... HOOKJSON; exit 0` block you will replace in Step 4. Make your edits in place — do not restructure unrelated parts. Never assume the file's shape; verify by reading.

## Shared Constants

None — no shared constants for this task.

## Pattern References (read BOTH before writing code)

- `bypass-env-var` → `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`: find how `SUPERPOWERS_VALIDATOR_BYPASS` is handled and mirror that exact style for `SUPERPOWERS_SDD_BYPASS` (set ⇒ stderr warning + `exit 0`). (Note: the canonical `SUPERPOWERS_VALIDATOR_BYPASS` implementation lives in the Python validators; the pattern to mirror is "env var set ⇒ emit a stderr warning and allow." Replicate that contract.)
- `bash-hook-subprocess-test` → `tests/unit/test_sdd_classification.py` + `tests/unit/sdd_test_helpers.py`: the `run_hook()` subprocess invocation pattern (`subprocess.run(["bash", HOOK_PATH], input=..., capture_output=True, text=True, timeout=10)`). Your test's `run_hook` mirrors this (with an `env` extension for the bypass test).

Your implementation should be structurally consistent with these existing patterns. Do not invent a new convention if one already exists.

## Subdirectory CLAUDE.md Files

No CLAUDE.md files exist in `skills/`, `skills/subagent-driven-development/scripts/`, `tests/`, or `tests/unit/`. The governing conventions are in the ROOT `CLAUDE.md` "Hook Development Gotchas": do NOT add `set -u` (jq pipe chains produce empty vars → silent exits with no stderr); use defensive `${VAR:-}` expansion. The plan's Step 4 note reiterates this.

## Before You Begin

If anything is unclear — the regex semantics, the bypass behavior, the exact location of the advisory block, or how the tests resolve the hook path — ask now before writing code. It is always OK to pause and clarify.

## Your Job (TDD — follow in order)

1. Read the current hook + both Pattern Reference files (in parallel).
2. Step 1: write the 6 tests EXACTLY as above — the compact-JSON `separators=(",", ":")` is load-bearing (spaced JSON makes the hook's grep miss and the block tests pass vacuously).
3. Step 2: run them; confirm RED (block + bypass tests fail).
4. Steps 3–4: tighten the regex; add the bypass + `exit 2` block, preserving the WARNING text, the `SKILL_LOADED` allow, the path filter, and all early exits. Replace the advisory block in place — leave NO dead code (the old `cat << HOOKJSON ... exit 0` advisory emission must be fully removed, not commented out).
5. Step 5: run tests; confirm all 6 GREEN.
6. Step 6: commit BOTH files with the exact commit message: `feat(sdd): promote skill-enforcement hook to blocking with bypass`
7. Clean up any scratch/temp files. Self-review (completeness, quality, discipline, testing, contract compliance). Report.

While you work: if you hit anything unexpected, ask. Don't guess.

## Report Format

Report using the exact structure from the SDD implementer-prompt template. Your report MUST begin with YAML frontmatter (between `---` delimiters):

```
---
schema_version: 1
task_id: 0
status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
files_changed:
  - path: "..."
    description: "..."
tests:
  written: <count>
  passing: <count>
  command: ".venv/bin/python3 -m pytest tests/unit/test_sdd_skill_enforcement.py -v"
  result: PASS | FAIL
contract_compliance:
  - constraint: "Block convention: exit 2 + stderr; bypass mirrors SUPERPOWERS_VALIDATOR_BYPASS"
    status: compliant | non_compliant | partial | not_applicable
    detail: "..."
---
```

Then the prose sections: **Implementation Summary**, **Source Files Read**, **CLAUDE.md Files Read**, **Deviations from Plan**, **Self-Review Findings**, **Concerns**. Do not omit any section. Use DONE_WITH_CONCERNS if you have any Deviations or Concerns. Use BLOCKED if you cannot complete. Never silently produce work you're unsure about.
