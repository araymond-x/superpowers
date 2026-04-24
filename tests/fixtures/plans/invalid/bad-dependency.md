---
schema_version: 1
feature_archetype: greenfield
tasks:
  - id: 0
    title: "Setup"
  - id: 1
    title: "Implement"
    depends_on: [5]
---

# Bad Dependency — Task 1 depends on non-existent Task 5
