# Contract facts from spec-distilled.md (verified against source files in Task 0):
# - CURRENT_SCHEMA_VERSION = 1 (from _base.py)
# - StrictModel uses extra="forbid" (from _base.py)
# - SchemaVersionedModel extends StrictModel with schema_version field + validator (from _base.py)
# - checkpoint_result.py uses Literal types and model_validator(mode="after")
# - Plan.Module has: id: int, title: str, task_ids: list[int] (from plan.py)
# - Plan has: feature_archetype: FeatureArchetype, modules: list[Module] | None (from plan.py)
# - module_task_ids_are_consistent validator exists (from plan.py)
# - validators.py CLI uses choices=["plan", "handoff", "report"]
#
# Tier = Literal["micro", "standard"]
# ArtifactPaths fields: feature_dir, reports_dir, dispatch_log, deviations_file (all git-root-relative str)
# Enforcement fields: pre_execution_audit, partner_review, dispatch_provenance, context_summary_at, checkpoint_files
# ProcessRequirements fields: subagent_dispatch, spec_review_mode, quality_review_mode, partner_review_mode, deviations_log, checkpoint_script
# SddSession.tier, .enforcement, .process_requirements are immutable after creation
# Midpoint formula: task_range[0] + (range_size + 1) // 2
#
# Tests will be added in Task 2.
