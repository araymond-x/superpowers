"""Shared Pydantic models for the Superpowers custom fork.

Modules:
  _base.py - Base classes (StrictModel, SchemaVersionedModel) and CURRENT_SCHEMA_VERSION
  plan.py - Plan artifact model (YAML frontmatter)
  handoff.py - HandoffPackage artifact model (YAML frontmatter)
  implementer_report.py - ImplementerReport artifact model (YAML frontmatter)
  checkpoint_result.py - CheckpointResult artifact model (pure JSON)
  errors.py - Human-readable error formatters
  validators.py - CLI entry points (plan, handoff, report subcommands)
"""
