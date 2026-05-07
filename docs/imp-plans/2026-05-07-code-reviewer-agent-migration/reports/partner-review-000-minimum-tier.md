---
task: 0
tier: minimum
date: 2026-05-07
---

# Partner Review — Task 0 (Minimum Tier)

**Rationale for minimum tier:** Task 0 creates a single standalone Python script (`contract-verification.py`) that reads a JSON fixture and greps live files. No external contract dependencies, no integration points, no shared constants, no pattern references. The script is self-contained and its correctness is verified by running it (Step 2).

The plan provides the complete script verbatim — the implementer copies it, runs it, and commits. Dispatch quality verification adds no value beyond confirming the plan text was copied correctly, which the test run itself verifies.
