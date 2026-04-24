---
schema_version: 1
feature_archetype: migration
source_contracts: "docs/specs/example-spec.md"
shared_constants:
  - path: "app.config.RETENTION_DAYS"
    value: "90"
    reason: "Used in cleanup task"
pattern_references:
  - name: "db-migration-pattern"
    source_files: ["migrations/001.py"]
    reason: "Follow existing migration style"
modules:
  - id: 1
    title: "Core"
    task_ids: [0, 1]
  - id: 2
    title: "Integration"
    task_ids: [2]
tasks:
  - id: 0
    title: "Setup"
    module_id: 1
    shared_constants_used: ["app.config.RETENTION_DAYS"]
  - id: 1
    title: "Implement"
    module_id: 1
    depends_on: [0]
    pattern_references: ["db-migration-pattern"]
  - id: 2
    title: "Integrate"
    module_id: 2
    depends_on: [1]
---

# Full-Featured Plan

> **For agentic workers:** Invoke SDD first.

**Goal:** Example full plan.
