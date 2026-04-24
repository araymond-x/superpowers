# Handoff Package Specification

> **For agents producing handoff packages**: Follow this spec to create a handoff package that will pass the `superpowers:handoff-acceptance` gate. Packages that don't follow this structure will be returned for revision before any downstream planning or implementation begins.

---

## Why This Matters

Handoff packages feed into a multi-agent pipeline (brainstorming → planning → implementation). Each downstream agent has no session context — it knows only what the handoff document tells it. Information that is buried, ambiguous, or assumed will propagate as wrong assumptions through plans, tests, and code. A single type declared in prose on line 200 that should have been on line 10 caused 3 production bugs in a real project.

## Required Structure

Your handoff package is a directory containing at minimum:

```
your-handoff-package/
├── README.md              # Main document (required)
├── samples/               # Machine-readable fixtures (required)
│   └── sample_output.json
├── schemas/               # Schema files if applicable (recommended)
└── scripts/               # Reference implementations if applicable (recommended)
```

## YAML Frontmatter (Required)

Handoff package README.md files must begin with YAML frontmatter:

```yaml
---
schema_version: 1
package_name: "your-package-name"
feeds_into: "brainstorming"  # which skill consumes this
one_sentence_purpose: "Describe the package in one sentence."
contract_constraints:
  - name: "field_name"
    kind: "string"  # string | integer | float | boolean | date | enum
    format_hint: "YYYY-MM-DD"  # optional
    nullable: false  # optional, default false
format_rules:
  - applies_to: ["field_name"]
    rule: "Must be positive"
samples:
  - path: "samples/example.csv"
    description: "Example data file"
---
```

The validator checks that format_rules reference declared fields and that sample files exist on disk.

## README.md Structure

The README must follow this structure. The order matters — the first 50 lines are mechanically checked.

### Lines 1-50: Contract Constraints (REQUIRED, BLOCKING)

The very first substantive section of the README, after the title and a brief one-sentence purpose statement, must be a **Contract Constraints** section. This section contains non-negotiable facts that every downstream consumer must honor.

```markdown
# [Package Name]

[One sentence: what this package provides and what it feeds into.]

## Contract Constraints

These are non-negotiable facts. Every downstream plan, implementation, and test must honor them.

**Field Types:**
- All amounts are `string` type (e.g., `"-11,350.00"`) — not numeric
- All dates are `string` type in `MM/DD/YY` format
- All APR/APY values are `string` type (e.g., `"29.99"`) — no `%` symbol

**Format Rules:**
- Amounts include commas for thousands (e.g., `"1,500.00"`)
- Negative amounts use a leading minus (e.g., `"-500.00"`)
- No `$` prefix on any amount field

**Required Fields:**
- `detected_account_source` (string) — present in every response
- `transactions` (array of objects) — always present, may be empty

**Invariants:**
- [Any rules that must always hold, e.g., "balance checksum must equal sum of transactions"]

**Known Gotchas:**
- [Specific traps, e.g., "Model sometimes converts 29.99% to 0.2999 — validate APR range"]
```

**Why first 50 lines**: The `check-handoff.sh` script greps the first 50 lines for contract-related headers. If your Contract Constraints section starts after line 50, the automated check will fail.

### Rest of Document: Supporting Detail

After the Contract Constraints section, include whatever detail is needed:

- Architecture and context
- API invocation patterns
- Validation pipeline
- Known issues and pitfalls
- Cost and performance data

This content is valuable but is NOT checked by the acceptance gate — only the Contract Constraints section is mechanically verified.

## Code Snippets (REQUIRED, BLOCKING)

Every code snippet in the README must be one of:

### Executable (default assumption)
```python
# This snippet can be copied into a file and run
import boto3
import json

def invoke_bedrock(pdf_bytes, schema):
    client = boto3.client("bedrock-runtime", region_name="us-west-2")
    response = client.converse(
        modelId="us.anthropic.claude-haiku-4-5-20251001-v1:0",
        messages=[...],
    )
    return json.loads(response["output"]["message"]["content"][0]["toolUse"]["input"])
```

### Labeled Pseudocode
```python
# pseudocode — do not copy directly
# Illustrates the validation pipeline concept
for gate in gates:
    result = gate.check(extracted_data)
    if result.failed and gate.is_hard:
        return reject(result)
```

If a snippet looks executable but is missing imports, uses wrong types, or references functions that don't exist, it will fail the acceptance check.

## Acceptance Fixtures (REQUIRED, BLOCKING)

Include at least one machine-readable sample in `samples/` or `fixtures/`:

```json
{
  "detected_account_source": "AMZN-VISA",
  "opening_date": "01/05/26",
  "closing_date": "02/04/26",
  "new_balance": "-1,350.00",
  "transactions": [
    {
      "date": "01/10/26",
      "description": "AMAZON.COM",
      "amount": "-45.99",
      "category": "PURCHASE"
    }
  ]
}
```

Requirements:
- **Types must match Contract Constraints** — if the contract says amounts are strings, the fixture must have string amounts
- **Include edge cases** — empty transactions array, null optional fields, boundary values
- **At least one sample per major variant** (e.g., one per account type if the package covers multiple)

## Acceptance Test (RECOMMENDED)

A runnable test that loads a fixture and verifies it matches the contract:

```python
import json

def test_fixture_matches_contract():
    with open("samples/sample_output.json") as f:
        data = json.load(f)

    # Contract: detected_account_source is always a string
    assert isinstance(data["detected_account_source"], str)

    # Contract: amounts are strings, not numbers
    assert isinstance(data["new_balance"], str)
    assert "," in data["new_balance"] or data["new_balance"].replace("-", "").replace(".", "").isdigit()

    # Contract: transactions is always an array
    assert isinstance(data["transactions"], list)

    for txn in data["transactions"]:
        assert isinstance(txn["amount"], str)
        assert isinstance(txn["date"], str)
```

If you don't include a test, the receiving agent will create one — but your test is better because you know the edge cases.

## Document Authority Declaration (RECOMMENDED)

If both a handoff package and a design spec exist for the same feature, declare which is authoritative:

```markdown
## Document Authority

| Concern | Authoritative Document |
|---------|----------------------|
| Field types and formats | This handoff package |
| UI behavior and user flows | Design spec |
| Validation gate severity | Design spec (handoff has experiment-era severity) |
| API invocation pattern | This handoff package |
```

## Open Decisions (RECOMMENDED)

List anything you intentionally left unresolved:

```markdown
## Open Decisions

| # | Decision | Options | Must Be Resolved By |
|---|----------|---------|-------------------|
| 1 | Rate field mapping for LOC-WF | See LOC-WF section | Plan writer |
| 2 | Shared-PDF extraction order | Sequential vs parallel | Implementation |
```

Do NOT bury open decisions in prose — if a plan writer has to read 400 lines to discover an unresolved question, they will make an assumption instead.

## Automated Validation

The receiving agent will run this check against your README:

```bash
bash ~/.claude/skills/superpowers/handoff-acceptance/scripts/check-handoff.sh README.md
```

This checks for "Contract Constraints", "Contract Summary", "Contract Facts", "field types", or "non-negotiable" in the first 50 lines. If none are found, the handoff is rejected.

## Checklist Before Submitting

- [ ] Contract Constraints section is within the first 50 lines of README.md
- [ ] All field types explicitly declared (string, int, array, etc.)
- [ ] All format constraints documented (date formats, number formats, etc.)
- [ ] All code snippets are executable or labeled pseudocode
- [ ] At least one machine-readable sample fixture in samples/ or fixtures/
- [ ] Fixture types match Contract Constraints exactly
- [ ] Open decisions listed in a table (not buried in prose)
- [ ] Document authority declared (if a companion spec exists)
