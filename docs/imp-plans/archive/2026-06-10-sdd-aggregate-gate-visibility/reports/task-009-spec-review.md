# Task 9 — Spec Compliance Review (N25b+d+f)

**Verdict:** PASS
**Range reviewed:** `c79531b..077cd92` (verified by reading code at HEAD, running tests, checking invariants independently)

## Findings

**N25b (line-anchored frontmatter, shared helper):** Confirmed. `_frontmatter_block(content) -> Optional[str]` (controller-checkpoint.py:256-265) uses `re.search(r"^---$", content[3:], re.MULTILINE)` as prescribed. Both `_task_ids_where` (:280) and `_integration_test_paths` (:447) delegate to it — grep confirms zero remaining `content.find("---", 3)` and no duplicated line-anchor logic. **SSOT invariant holds.** Behavior-preservation proven empirically: for all well-formed inputs the helper returns byte-identical bodies to the old `content.find`, differing only in the N25b hazard case (a `---` inside a YAML value no longer truncates early). Edge cases (no opening `---`, no closing line-anchored `---`, content before opening `---`) all return the correct conservative `None`.

**N25d (directory detail):** Confirmed (:1761-1767). The not-a-file branch checks `os.path.isdir(abs_path)` and emits "is a directory, not a file", falling back to "missing on disk" only when neither file nor dir.

**N25f (name the plan file):** Confirmed option (b), caller-side attribution. `_plan_label` (:1696) is prefixed into ALL three malformed branches — malformed-only (:1708), infra-error-plus-malformed (:1730), mixed `it_problems` list (:1756). The `--plan-file` arg is `required=False, default=None` (:1867), so the `"the plan"` None-fallback is genuinely reachable and correct (manifest-only mode) — the report's edge-case claim verified, not hand-waved.

**Required tests:** All 3 plan skeletons present and assert what the spec requires — including `test_directory_path_says_is_a_directory`, which genuinely `mkdir`s the declared path and asserts the FAIL detail + blocker. The 2 extra tests (line-anchoring proof for the second consumer; Check-10-caller test) close gaps the skeletons left — not scope creep.

**Invariants:** (1) one shared helper, no duplication — verified. (2) behavior-preserving — verified empirically. (3) 3.9-compat — `Optional[str]` not `str | None`; regression 145 PASS / 0 FAIL / 3 advisory WARNING.

**Scope:** Exactly the 2 owned files changed in `077cd92`; nothing outside.

**Tests run independently:** C2 suite 36 passed; checkpoint/fence 135 passed; full unit suite **497 passed**; regression scanner clean.

**N25f design choice — acceptable.** Plan delegated option (a) vs (b) to the implementer. Option (b) meaningfully satisfies "name the source plan file" (names the active plan, narrows the author to the plan set). The flagged multi-module limitation (a malformed declaration in a non-active module file would be labeled with the active module's filename) is real and honest, and acceptable for this minimal-change task.

**Report completeness:** All sections present and substantive.

result: PASS
