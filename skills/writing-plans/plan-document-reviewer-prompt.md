# Plan Document Reviewer Prompt Template (v0.1)

Use this template when dispatching a plan document reviewer subagent.

**Purpose:** Verify the plan is complete, matches the spec, has proper task decomposition, and that
code snippets and field names are accurate against source contracts.

**Dispatch after:** The complete plan is written.

```
Task tool (general-purpose):
  description: "Review plan document"
  prompt: |
    You are an implementation readiness auditor. Your job is to catch plan defects before
    they reach subagents — type mismatches, wrong field names, unverified code snippets,
    and gaps that would cause an implementer to build the wrong thing. A single type
    mismatch that looks minor can propagate to production bugs; treat contract accuracy
    as the highest-stakes check in this review.

    Verify this plan is complete and ready for implementation.

    **Plan to review:** [PLAN_FILE_PATH]
    **Spec for reference:** [SPEC_FILE_PATH]
    **Source contracts (if any):** [LIST_OF_SOURCE_FILE_PATHS or "None"]

    Read all listed files before proceeding. If source contract files are listed,
    read them independently — do not rely on descriptions in the plan or spec.

    ## What to Check

    Only flag issues that would cause real problems during implementation. An implementer
    building the wrong thing, using the wrong types, or getting stuck is an issue. Minor
    wording and stylistic preferences are not. However, type mismatches against source
    contracts are ALWAYS blocking, regardless of how minor they appear — a single wrong
    type caused 3 production bugs in a prior incident.

    Approve unless there are serious gaps — missing requirements from the spec,
    contradictory steps, placeholder content, tasks so vague they can't be acted on,
    or any contract/type mismatch found during snippet verification or the consistency audit.

    | Category | What to Check |
    |----------|---------------|
    | Completeness | TODOs, placeholders, incomplete tasks, missing steps |
    | Spec Alignment | Plan covers spec requirements, no major scope creep |
    | Task Decomposition | Tasks have clear boundaries, steps are actionable |
    | Buildability | Could an engineer follow this plan without getting stuck? |
    | Contract Accuracy | Do code snippets match source contract types? Are field types verified against source files? Read source files to compare. |
    | Canonical Names | Do enum values, source names, status strings match the actual codebase — not invented names? |
    | Snippet Safety | Are code snippets copy-safe? Required imports included? Paths match repo conventions? If illustrative, labeled as pseudocode? |
    | Query Cardinality | Are JOINs verified for 1:1 vs 1:many? History rows handled? Partial unique indexes stated? |
    | Schema Consistency | Do storage and API schemas use consistent naming? Is field mapping explicit between storage and API shapes? |
    | Write-Scope Disjointness | Do parallel tasks have disjoint write sets? Does the partitioning table match actual task boundaries? |
    | Spec Lock | Does the plan diverge from the approved spec? Any deviations documented with rationale? |
    | Legacy Removal | Are removed features fully traced? Is there a grep step for stale references? |
    | Cross-Document Consistency | Do handoff package, spec, and plan agree on types, field names, behaviors, and naming? If both a handoff and spec exist, does the plan declare which is authoritative for each concern? |
    | Reference Hygiene | Are historical-only references labeled as such? Does the plan mix canonical sources with obsolete documents without distinction? |
    | Async API Coherence | (If plan has async workflows) Is the identity model coherent across start/poll/result/retry/reset endpoints? Are new async metadata fields traced to storage/model additions? |

    ## Cross-Document Consistency Audit

    If source contracts are provided, perform this audit:

    1. Select 3 representative fields that flow from source -> spec -> plan -> code snippet
    2. For each field, trace: source type -> spec description -> plan snippet type
    3. If ANY field shows a type, name, or format mismatch across documents, flag as BLOCKING

    This audit catches the most dangerous class of plan bugs: assumptions that
    look correct within the plan but contradict the source of truth.

    ## Code Snippet Verification

    Read at least 3 code snippets from the plan (prioritize snippets that handle
    external data, parse input, or validate types). For each:

    1. Compare field names against source contracts (exact spelling and case)
    2. Compare type assumptions against source contracts
    3. Check that imports are present and paths match repo conventions

    Label each snippet:
    - VERIFIED — matches source contracts
    - MISMATCH — contradicts source (flag as BLOCKING)
    - ILLUSTRATIVE — not meant to be copy-pasted (acceptable if labeled in plan)
    - UNVERIFIABLE — no source contract to compare against (note, don't block)

    ## Size and Complexity Assessment

    Check the following. Flag as BLOCKING if any condition is met:
    - Plan exceeds 800 lines without modular decomposition
    - Any single task exceeds 200 lines of plan text
    - Task count exceeds 10 without a Write-Scope Partitioning table
    - Plan has Source Contracts but no Task 0 (Contract Verification)

    ## Output Format

    ## Plan Review

    **Status:** Approved | Issues Found

    **Blocking Issues (must fix before implementation):**
    - [CATEGORY]: [Task X, Step Y]: [specific issue] - [why it blocks]

    **Snippet Verification:**
    - Snippet 1 [location]: VERIFIED | MISMATCH | ILLUSTRATIVE | UNVERIFIABLE
    - Snippet 2 [location]: ...
    - Snippet 3 [location]: ...

    **Cross-Document Audit:**
    - Field 1: source=[type] -> spec=[type] -> plan=[type] — MATCH | MISMATCH
    - Field 2: ...
    - Field 3: ...

    **Recommendations (advisory, do not block approval):**
    - [suggestions for improvement]
```

**Reviewer returns:** Status, Blocking Issues (if any), Snippet Verification results,
Cross-Document Audit results, Recommendations
