---
schema_version: 1
task_id: 16
task_type: implementation
status: DONE
files_changed:
  - path: "skills/subagent-driven-development/references/context-handoff-protocol.md"
    description: "quality-review fixes: exit-0 picker-manual gloss, runnable card regen command, de-duplicated ceiling formula, quota-low next action, placeholder + wording nits"
tests:
  written: 0
  passing: 0
  command: "python3 tests/ARaymond-skill-regression/validate-all-skills.py"
  result: PASS
contract_compliance:
  - constraint: "doc-only; six scoped fixes; write-mechanics-card.py NOT touched"
    status: compliant
    detail: "Only context-handoff-protocol.md edited/committed (explicit path). write-mechanics-card.py untouched. Regression PASS 161/0/2."
---

**Implementation Summary:**

All six quality-review fixes applied to `context-handoff-protocol.md` (commit d12c434, +18/−13).

- **Fix 1 (Important):** exit-0 `picker-manual` parenthetical reworded — removed "a human must complete it there before the pickup runs"; now reads "the successor opened the interactive picker (at exit 0 that picker has already been completed — see below)". Follow-on paragraph lightly tightened, meaning preserved.
- **Fix 2 (Important):** mechanics-card regen command — added a `$PYTHON` definition (superpowers venv interpreter `$SUPERPOWERS_ROOT/.venv/bin/python3`; hook-internal, not in a reader's shell; card needs PyYAML+pydantic so plain python3 exits 2; substitute the venv python if unset). Replaced the circular "card prints an absolute-path form in its header" parenthetical (no card exists on the manual-fallback path) with a note that the shown `~/.claude/...` path is already the standalone form. No fragile hardcoded venv path.
- **Fix 3 (Minor):** hop-ceiling note now references `SUPERPOWERS_CMUX_MAX_HOPS` instead of restating `max(6, 2×expected)`; formula lives only in the env-knob entry.
- **Fix 4 (Minor):** quota-low exit-3 cause gained "Resume manually (or wait for quota to recover), then re-run."
- **Fix 5 (Nit):** the lone `<id>` placeholder standardized to `<bundle-id>`.
- **Fix 6 (Nit):** "reviewed and at a clean boundary" → "reviewed and committed."

**Source Files Read:**
- `skills/subagent-driven-development/references/context-handoff-protocol.md` (full)

**CLAUDE.md Files Read:**
- Project + global CLAUDE.md (in-context) — confirm context-handoff-protocol.md is the runtime-contract home and spawn-handoff-session.sh / write-mechanics-card.py are out of this doc-only task's scope.

**Deviations from Plan:**
None. Six fixes exactly as specified, single file.

**Self-Review Findings:**
- Verified write-mechanics-card.py NOT touched.
- Commit contains only the one doc file (`git show --stat`: 1 file changed).
- Regression suite PASS 161 / FAIL 0 / WARNING 2 (advisory only).

**Concerns:**
None. The `$PYTHON` note keeps the command robust (definition + substitution guidance) rather than pinning a machine-specific venv path.
