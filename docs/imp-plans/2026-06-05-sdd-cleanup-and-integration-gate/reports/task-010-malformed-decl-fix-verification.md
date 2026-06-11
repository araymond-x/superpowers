# Post-Fix Verification Review — commit 911f025 (Check 10 malformed-declaration fail-open)

> Dispatched 2026-06-10 (final-review Important #1 fix; H1 re-review precedent). First dispatch
> died on an API ConnectionRefused after substantial work; this is the fresh retry's report.

## Verdict: VERIFIED — combined PASS

### 1. Diff review / reformat neutrality — PASS
Exactly the 2 prescribed files. Every reformat hunk outside the new code checked: comprehension wraps, call wraps, two adjacent string literals merged byte-identically. No expression, condition, or string content changed — the auto-format pass is behavior-neutral. `Tuple` already imported; single caller of `_integration_test_paths` (line 1583) — no other consumer broken by the tuple return.

### 2. Shape-matrix probe (in-process, new vs pre-fix code) — PASS

| Shape | NEW bucket | OLD (pre-fix) bucket |
|---|---|---|
| valid dict+path | PATHS | PATHS |
| flat string | MALFORMED ("a bare string… expected a mapping") | NOT-DECLARED (fail-open) |
| {path: ""} | MALFORMED ("empty") | NOT-DECLARED |
| {path: "  "} | MALFORMED ("empty") | NOT-DECLARED |
| {} (no path key) | MALFORMED ("no 'path' key") | NOT-DECLARED |
| list | MALFORMED ("a list") | NOT-DECLARED |
| null | NOT-DECLARED | NOT-DECLARED |
| absent | NOT-DECLARED | NOT-DECLARED |
| {path: 123} | MALFORMED ("a int") | NOT-DECLARED |
| {path: null} / true | MALFORMED | NOT-DECLARED |
| valid + malformed coexist | paths=1, malformed=1 | n/a |

Exactly per prescription; null/absent stay not-declared; valid-path extraction and dedup unchanged.

### 3. Check 10 semantics — PASS
Lines 1577-1658: malformed-only → FAIL + declarations named + shape guidance + blocker `integration_test_present` (== check key in all three FAIL branches, satisfying the CheckpointResult validator). Nothing-declared → PASS "check skipped". Valid+malformed → FAIL wins while valid paths still changeset-checked. Base-ref infra-error branch appends malformed details.

### 4. The 2 new tests — PASS
Conventions matched; assertions specific (FAIL, shape-guidance substrings, blocker membership). RED-plausibility proven mechanically: pre-fix function buckets both shapes NOT-DECLARED and pre-fix Check 10 emitted PASS "skipped" — both new FAIL assertions would have failed pre-fix.

### 5. Test runs (actuals) — PASS
Targeted: **53 passed**. Full suite: **458 passed, 1 warning**. E2e: **12 steps PASS**.

### 6. Self-hosting checkpoint — PASS
STATUS PASS; integration_test_present PASS "check skipped"; blockers [].

### Advisory (non-blocking)
- Malformed descriptions don't name the source plan FILE (function receives contents, not filenames) — in a multi-module plan a malformed message isn't traceable to a specific module file. BACKLOG candidate.
