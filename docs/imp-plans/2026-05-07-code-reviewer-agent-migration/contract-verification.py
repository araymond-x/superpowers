#!/usr/bin/env python3
"""Pre-migration contract anchor: every `current` string in the handoff
snapshot must still appear at its documented location.
Exit 0 = matches; exit 1 = drift."""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "docs/handoffs/2026-05-07-general-purpose-migration/samples/current-state.json"

data = json.loads(FIXTURE.read_text())
failed = 0

for r in data["references_to_change"]:
    line = (ROOT / r["file"]).read_text().splitlines()[r["line"] - 1]
    if r["current"] in line:
        print(f"PASS: {r['file']}:{r['line']}")
    else:
        print(f"FAIL: {r['file']}:{r['line']}\n  expected: {r['current']}\n  actual:   {line}")
        failed += 1

for b in data["behaviors_to_add_to_code_reviewer_template"]:
    text = (ROOT / b["source_file"]).read_text()
    if b["verbatim"] in text:
        print(f"PASS: {b['source_file']} contains '{b['behavior']}' verbatim")
    else:
        print(f"FAIL: {b['source_file']} missing '{b['behavior']}'")
        failed += 1

print(f"\nSTATUS: {'FAILED' if failed else 'PASSED'} ({failed} drifts)")
sys.exit(1 if failed else 0)
