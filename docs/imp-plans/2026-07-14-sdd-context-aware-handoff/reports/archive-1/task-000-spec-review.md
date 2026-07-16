# Task 0 — Spec Compliance Review

**Reviewer:** general-purpose spec compliance auditor (dispatched)
**Task:** Contract verification + fixture transcripts
**Verdict:** **PASS** — spec compliant AND contract compliant.

## Independent Verification Results

**1. Hand-computed fixture totals (independent of the test's own sum):**

| Fixture | Fields (in/cc/cr/out) | Hand sum | Documented T | Threshold band |
|---|---|---|---|---|
| below | 100000+50000+90000+10000 | 250000 | 250000 ✓ | < SOFT (300k) ✓ |
| soft | 150000+50000+140000+10000 | 350000 | 350000 ✓ | [300k,400k) ✓ |
| hard | 200000+50000+190000+10000 | 450000 | 450000 ✓ | ≥ HARD (400k) ✓ |
| malformed-trailing | valid line 100000+50000+90000+10000 | 250000 | 250000 ✓ | — |
| missing-fields | 100000+10000 (2 absent→0) | 110000 | 110000 ✓ | — |
| non-numeric | 100000+"n/a"→0+0+0 | 100000 | 100000 ✓ | — |
| no-usage | (no usage block) | None | None ✓ | — |
| empty | (0 bytes) | None | None ✓ | — |

The three known-total fixtures correctly straddle SOFT=300000/HARD=400000.

**2. Fixture shape matches the real tool.** Every usage block sits at `message.usage.{4 fields}` on an assistant entry — exactly what `find_latest_usage` (claude-ctx-check L57–76) scans for and what the 4-field sum (L127–132) reads.

**3. malformed-trailing byte order confirmed** (`cat -v`): valid line is physically line 1, malformed line is line 2 (last). Reverse-scan hits the malformed line first (exercises the JSONDecodeError skip path), then finds the valid line → 250000. Test does NOT pass for the wrong reason.

**4. Fingerprint verified:** `shasum -a 256 ~/.claude/bin/claude-ctx-check | cut -c1-12` = `f83727ff80c0`, matching the report. Safe for Task 1 SOURCE_VERSION.

**5. Test re-run:** 8/8 PASSED (0.01s), committed `6f4eff6`.

**6. Stdlib-only confirmed:** test imports only `json` + `pathlib`. `_coerce_int` correctly excludes `bool`. `FIX` path resolves relative to `__file__` (runs from any CWD).

## Notes (non-blocking)

- Report is complete: all required sections present.
- The intentional parity divergence at `non-numeric.jsonl` is honestly documented (source would raise TypeError on `"n/a"`; probe/test coerce to 0 per spec). Task 2's differential parity test must account for this deliberate difference — downstream awareness only, not a Task 0 defect.

No BLOCKING, CONTRACT, or MISSING issues. Task 0 fully satisfies its specification.
