# Task 007 Report — validate-report.py Pydantic Pre-Check
# Date: 2026-04-27
# Status: DONE

**Status:** DONE

**Implementation Summary:**
Replaced validate-report.py with 2-layer validation: Layer 1 calls validate_report() for Pydantic frontmatter check, Layer 2 runs prose section check. Reports without frontmatter hard FAIL at Layer 1. Added Layer 3 done_with_concerns warning.

**Files Changed:**
- `skills/subagent-driven-development/scripts/validate-report.py` — full replacement

**Source Files Read:**
- `skills/subagent-driven-development/scripts/validate-report.py` — original
- `skills/scripts/models/validators.py` — provides validate_report()
- `skills/subagent-driven-development/scripts/_report_utils.py` — provides validate_report_sections()

**CLAUDE.md Files Read:**
- Project root CLAUDE.md

**Tests:**
- Valid fixture: Pydantic passes, prose check INCOMPLETE (expected — old 9-section list, Task 8 fixes)
- No-frontmatter: exit 1, stderr has "Phase 2 Pydantic cutover" message
- 222 unit tests pass

**Contract Compliance:**
- Calls validate_report() from validators.py: YES
- No frontmatter → hard FAIL with "Phase 2 cutover": YES
- Exit codes 0/1/2: YES
- yaml import is unconditional (audit Order #2): YES

**Deviations from Plan:**
- Valid fixture returns INCOMPLETE because _report_utils still has 9-section list — expected intermediate state before Task 8

**Self-Review Findings:**
- No issues found

**Concerns:**
- No concerns
