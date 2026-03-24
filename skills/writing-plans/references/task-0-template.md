# Task 0: Contract Verification Template

> Part of the writing-plans skill. Referenced from SKILL.md.

### Task 0: Contract Verification (BLOCKING)

**Files:**
- Read: [list each source schema/contract/handoff file with exact path]
- Create: `tests/fixtures/<feature>/contract_samples.json`
- Create: `tests/unit/test_<feature>_contracts.py`

- [ ] **Step 1: Read source contracts**
  Read each source file listed above. For each contract, extract:
  - Field names (exact spelling and case)
  - Field types (string, int, decimal, datetime format, enum values)
  - Required vs. optional fields
  - Format constraints (e.g., "YYYY-MM-DD", currency as string, etc.)
  - Any invariants or constraints documented in the source

- [ ] **Step 2: Create ground-truth fixtures**
  Create `tests/fixtures/<feature>/contract_samples.json` with sample data
  derived from ACTUAL source file content — not from plan descriptions.
  Fixtures must include: real field types, real format patterns, and edge
  cases observed in the source (nulls, empty lists, boundary values).

- [ ] **Step 3: Write contract verification test**
  Write a test that loads the fixtures and verifies they conform to the
  source contract's required shape and types. This test anchors all
  subsequent implementation to ground truth.

```python
def test_contract_sample_has_required_fields():
    with open("tests/fixtures/<feature>/contract_samples.json") as f:
        sample = json.load(f)
    assert "field_name" in sample
    assert isinstance(sample["field_name"], expected_type)
    # ... one assertion per non-negotiable contract fact
```

- [ ] **Step 4: Verify plan snippets against source**
  If the plan contains code snippets that reference contract fields (type checks,
  parsers, validators), compare each snippet against the source contract facts
  extracted in Step 1. For each snippet, confirm:
  - Field names match exactly (spelling, case, underscores)
  - Type assumptions match (string vs numeric, list vs scalar)
  - Format handling matches (commas, decimals, sign conventions)
  If any snippet contradicts the source contract, report DONE_WITH_CONCERNS and
  list the specific discrepancies. The plan may need updating before other tasks run.

- [ ] **Step 5: Run and verify**
  Run: `pytest tests/unit/test_<feature>_contracts.py -v`
  Expected: PASS — all contract assertions hold for the fixture data.
  **Do not proceed to Task 1 until this test passes.**

- [ ] **Step 6: Commit**
  ```bash
  git add tests/fixtures/<feature>/contract_samples.json tests/unit/test_<feature>_contracts.py
  git commit -m "test: add contract verification fixtures for <feature>"
  ```
