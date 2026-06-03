---
schema_version: 1
task_id: 0
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/subagent-driven-development/scripts/sdd-skill-enforcement-hook.sh"
    description: "Promoted advisory→blocking: tightened SDD-request detection to an imperative-only, word-boundary-anchored regex; replaced the advisory additionalContext/exit-0 block with a SUPERPOWERS_SDD_BYPASS check + exit 2; de-piped the detection (here-string, not grep|grep -q) so it works on large transcripts; updated header + inline comments."
  - path: "tests/unit/test_sdd_skill_enforcement.py"
    description: "Created: 10 subprocess tests — block/allow/casual/non-impl/bypass/no-request (6) plus C1 large-transcript regression (>64KB) and 3 I1 word-boundary false-positive tests."
tests:
  written: 10
  passing: 10
  command: ".venv/bin/python3 -m pytest tests/unit/test_sdd_skill_enforcement.py -v"
  result: PASS
contract_compliance:
  - constraint: "Block convention: exit 2 + stderr; bypass mirrors SUPERPOWERS_VALIDATOR_BYPASS (set => allow + stderr warning)"
    status: compliant
    detail: "Block path: echo WARNING_MSG >&2; exit 2. Bypass path: SUPERPOWERS_SDD_BYPASS set => stderr warning naming the var + exit 0. set -o pipefail kept; set -u not added; defensive ${VAR:-} expansion."
  - constraint: "Promote to blocking must actually block in production (the task goal)"
    status: compliant
    detail: "C1 fix: de-piped detection so the hook blocks on >64KB transcripts. Controller independently verified exit 2 at 200KB/1MB/4MB (was exit 0 pre-fix)."
---

**Implementation Summary**

Task 0 promotes `sdd-skill-enforcement-hook.sh` from advisory (`exit 0` + additionalContext) to blocking (`exit 2`), with a `SUPERPOWERS_SDD_BYPASS` escape hatch. Implemented across two cycles:

Cycle 1 (commit 2b3c5b1): tightened the SDD-request grep to the imperative-only pattern, replaced the advisory heredoc emission with the bypass-check + `exit 2`, removed the now-orphaned `CONTEXT_MSG`/`ENCODED` variables, and corrected the header exit-codes comment. 6 TDD tests, all passing.

Cycle 2 (commit 8b7a95c) — remediation of two defects found by code quality review and independently verified by the controller:
- **C1 (Critical):** the pre-existing `grep '"role":"user"' | grep -qiE …` under `set -o pipefail` returned non-zero on large transcripts (downstream `grep -q` exits early → upstream grep SIGPIPE → pipefail propagates), so `SDD_REQUESTED` stayed false and the promoted hook FAILED TO BLOCK on any transcript >~64KB (every real SDD session). Fixed by de-piping: `USER_LINES=$(grep '"role":"user"' "$T")` then `grep -qiE "PATTERN" <<< "${USER_LINES:-}"` (here-string — no producer→grep-q pipe, so no SIGPIPE; pipefail doesn't apply to a non-pipeline). The prohibited `echo "$VAR" | grep -q` antipattern was NOT used.
- **I1 (Important, user-approved):** the regex lacked `\b` on both alternation groups, so `use` matched inside `reuse`/`misuse` and `sdd` matched inside `assddata`, false-blocking those phrases. Fixed by anchoring both groups: `\b(invoke|use|run|follow|start|let'?s use)\b.{0,20}\b(subagent-driven-development|sdd)\b`.

Detection regex (final): `\b(invoke|use|run|follow|start|let'?s use)\b.{0,20}\b(subagent-driven-development|sdd)\b`. C1 regression-test transcript: ~196KB (line-1 imperative + 3000 padding user lines, ~3x the 64KB pipe buffer). All early exits, the SKILL_LOADED allow, and the impl-file path filter preserved. No dead code; `bash -n` clean.

**Source Files Read**
- `skills/subagent-driven-development/scripts/sdd-skill-enforcement-hook.sh` (full, both cycles)
- `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` (bypass-env-var pattern)
- `tests/unit/test_sdd_classification.py` + `tests/unit/sdd_test_helpers.py` (bash-hook-subprocess-test pattern)

**CLAUDE.md Files Read**
- Root project `CLAUDE.md` and `~/.claude/CLAUDE.md` + `~/.claude/rules/*` — Hook Development Gotchas (no `set -u`; defensive `${VAR:-}`; avoid pipe-into-`grep -q`), architectural-principles (no dead code; automated gate FAILs never expected).
- No CLAUDE.md in `skills/`, `skills/subagent-driven-development/scripts/`, `tests/`, or `tests/unit/`.

**Deviations from Plan**
1. Header exit-codes comment rewritten (advisory→blocking) — required to avoid a false claim. [Accepted]
2. Removed orphaned `CONTEXT_MSG`/`ENCODED` variables — required by no-dead-code. [Accepted]
3. **C1: de-piped the SDD-detection construct** — beyond the plan's literal steps, but necessary to achieve the plan's stated goal ("promote to blocking"); the plan-specified code blocked only on tiny transcripts. Pre-existing pipe bug, latent while advisory. [Accepted]
4. **I1: anchored the regex with `\b…\b`** — diverges from the plan's explicitly-specified regex (which the plan claimed was "verified to discriminate correctly"). The quality review + controller verification proved 3 real false-positives. User approved the tighten. [Accepted — plan's "verified" claim was incomplete]

**Self-Review Findings**
- `test_allows_when_skill_loaded` passes via the SKILL_LOADED path regardless of detection, so it doesn't itself guard the regex; the true positives are covered by the block tests and were verified to still block. The `\b` change is strictly narrowing and no true positive relies on a mid-word match.
- Line 46 (`echo "$FILE_PATH" | grep -qiE …`) is the same pipe shape but SAFE (a file path is far under 64KB → echo finishes before grep -q exits → no SIGPIPE). Correctly left unchanged; C1 fix scoped to transcript detection only.
- 10/10 file tests pass; 13/13 classification (no regression); `bash -n` clean.

**Concerns**
- Semantic false-positives remain inherent to the regex heuristic (e.g., "run the sdd tests" still blocks). This is the documented, intended trade-off; `SUPERPOWERS_SDD_BYPASS` is the escape valve, now noted in an inline comment. Not a defect — flagged for awareness.
