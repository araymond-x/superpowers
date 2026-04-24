# Pydantic Adoption — Positive Analysis & Candidate Inventory

**Date:** 2026-04-23
**Source context:** `2026-04-21-claude-code-production-guardrails.md` (LinkedIn infographic + post)
**Companion doc:** `2026-04-21-production-guardrails-gap-analysis.md`
**Status:** Discussion input — pre-brainstorm
**Thesis:** Pydantic is the highest-leverage single technology addition the fork can make to achieve deterministic outputs, explanatory error feedback, and cross-object contract validation.

---

## 1. Why Pydantic Is The Right Answer For This Fork

### 1.1 Boundary-layer fit

The LinkedIn infographic places Pydantic at exactly one position in the pipeline:

```
Input → Model → [Validation: Pydantic] → Output
```

The fork's SDD architecture has *many* such boundaries — every handoff from a subagent back to the controller is one. Today each is guarded by its own ad-hoc grep/regex layer. Pydantic offers a single, consistent vocabulary for all of them.

### 1.2 Schema-as-contract (replaces pattern-as-contract)

The fork currently enforces report shape via patterns:

```python
# Today: brittle, string-level
if "## Uncertainties" not in report_text: ...
```

Pydantic replaces this with:

```python
# Tomorrow: typed, structural
class ImplementerReport(BaseModel):
    uncertainties: list[Uncertainty]  # typed, required, each with sub-fields
```

The regex answers "does a string appear?" The schema answers "does a typed record exist with valid sub-fields and consistent cross-references?" The second is enforceable in ways the first never can be.

### 1.3 Explanatory errors are a *feature* — this is the big win

Pydantic's `ValidationError` is field-path-specific by design:

```
ImplementerReport
  contracts_implemented.0.signature
    Field required [type=missing, input_value={'name': 'foo'}, input_type=dict]
  uncertainties.2.confidence
    Input should be 'low', 'medium' or 'high' [type=literal_error, input_value='maybe']
```

**Why this matters to the fork specifically:** today when a hook blocks, it returns a shell error string that the subagent can't act on — it just says "something is wrong, re-run." A Pydantic-typed FAIL returns a structured diagnostic the subagent can iterate against. The enforcement layer transforms from a **gatekeeper** (binary pass/fail) into a **teacher** (here's the specific field that's wrong and what it should contain).

### 1.4 Cross-object validation is where the real leverage lives

Pydantic's `@model_validator` decorator turns relationship rules into declarative code:

```python
@model_validator(mode="after")
def contracts_match_plan(self) -> Self:
    plan_contracts = {c.name for c in self.plan.contracts}
    report_contracts = {c.name for c in self.report.contracts_implemented}
    missing = plan_contracts - report_contracts
    if missing:
        raise ValueError(f"Report missing required contracts: {missing}")
    return self
```

Today these relationships are either unenforced or enforced by fragile grep. Every such rule becomes a two-line validator.

### 1.5 Markdown becomes a *renderer*, not a *format*

The conceptual shift: today, markdown *is* the report. With Pydantic, the model *is* the report; markdown is one of several renderings (JSON for hooks, markdown for humans, HTML for reviewers). This separation of data and view is standard engineering practice everywhere else — adopting it here unlocks programmatic reasoning about reports without parsing prose.

### 1.6 Tool-use alignment

For Pydantic to enforce subagent output at emit-time (not just ingest-time), the subagent must produce JSON, not markdown. Claude's tool-use mechanism is the native path: define a tool whose input schema is your Pydantic model's JSON Schema, and the subagent is constrained to call that tool with its report. Libraries like **Instructor** automate exactly this. The fork's existing subagent dispatch layer is a clean injection point for this constraint.

---

## 2. Candidate Inventory — Where Pydantic Fits in The Fork

Identified via a systematic repo pass on 2026-04-23. Candidates ranked within tiers by ROI (volume × structural complexity × current-brittleness).

### Tier A — High Volume, Already Half-Schematized (Do These First)

| # | Asset | Current form | Pydantic model | Why this ROI |
|---|-------|--------------|---------------|--------------|
| A1 | **Implementer Report** | Markdown with 9 required section headers (`_report_utils.py:REQUIRED_SECTIONS`) + `VALID_STATUSES` enum | `ImplementerReport(BaseModel)` with typed `status: Status` (Literal["DONE", "DONE_WITH_CONCERNS", "BLOCKED", "NEEDS_CONTEXT"]), `files_changed: list[FileChange]`, `contracts_compliance: ContractCompliance`, `deviations: list[DeviationRef]`, `concerns: list[Concern]` | Highest-volume artifact; the 9-section check is *already* a schema in all but name |
| A2 | **Controller Checkpoint** | `controller-checkpoint.py` already emits JSON via `_build_result()` with `phase`, `checks{name: {status, detail}}`, `warnings[]`, `blockers[]`, `progress` | `CheckpointResult(BaseModel)` with `phase: Literal["pre-execution", "pre-dispatch", "pre-completion"]`, `checks: dict[str, CheckResult]`, typed `status: Literal["PASS", "FAIL", "WARN", "SKIP"]` | Already JSON. Literally zero migration cost for the emit side — just `.model_dump()` instead of `json.dumps()`. Downstream hook consumers get typed access for free. |
| A3 | **Plan Structure** | `validate-plan.py` checks headers via regex (TASK_HEADER_RE, MODULE_HEADER_RE, SOURCE_CONTRACTS_RE, CONTRACT_CONSTRAINTS_RE, FEATURE_ARCHETYPE_RE) | `Plan(BaseModel)` with `tasks: list[Task]`, `modules: list[Module] \| None`, `source_contracts: str \| None`, `feature_archetype: str`, `contract_constraints: list[str]` | Cross-task validation unlocks immediately (`Task.depends_on` must reference valid IDs; `Task.shared_constants` must be real imports). |

### Tier B — Structured Relationships Currently Uncaptured

| # | Asset | Current form | Pydantic model | Why this ROI |
|---|-------|--------------|---------------|--------------|
| B1 | **DEVIATIONS Register** | Markdown table + sections (`deviations-template.md`) | `DeviationsRegister(BaseModel)` with `entries: list[Deviation]` where each `Deviation` has typed `type: Literal["deferred", "independent", "scope_change"]`, `task_ref: TaskRef`, `disposition: Disposition` | Hook can verify referenced task IDs exist; disposition enum prevents free-text drift |
| B2 | **Honesty Check** | Markdown with 9 numbered questions (`honesty-check-block.md`) | `HonestyCheck(BaseModel)` with `answers: list[Answer]` where `len(answers) == 9` enforced by `@field_validator`; each `Answer` has `question_number: int`, `response: str`, `flagged_concerns: list[str]` | Today "9 questions answered" is a word count; Pydantic makes it structural. Concerns-feed-to-DEVIATIONS step becomes automatic. |
| B3 | **Trace Audit Record** | `extract-execution-trace.py` already builds structured events + anomaly detection | `ExecutionTrace(BaseModel)` with `events: list[TraceEvent]`, `per_task: dict[int, TaskTrace]`, `anomalies: list[Anomaly]` where each `Anomaly` has typed `rule: AnomalyRule` enum | Trace auditor subagent gets typed input instead of JSON-string-to-parse; downstream audit reports can be validated against anomaly catalog |
| B4 | **Handoff Package Contract** | Markdown with "Contract Constraints" section + lines-1-50 mechanical check (`handoff-package-spec.md`) | `HandoffPackage(BaseModel)` with `contract_constraints: ContractConstraints` (typed fields for `amounts`, `dates`, `apr`, `format_rules`) | This one is especially compelling — the spec already says "a single type declared in prose on line 200 caused 3 production bugs" — Pydantic eliminates the class of failure by making types declarable in JSON alongside the prose |

### Tier C — Simpler Structures, Quick Wins

| # | Asset | Current form | Pydantic model | Why this ROI |
|---|-------|--------------|---------------|--------------|
| C1 | **Spec Review Report** | Markdown produced by `spec-reviewer-prompt.md` | `SpecReview(BaseModel)` with `verdict: Literal["APPROVED", "REVISIONS_NEEDED"]`, `findings: list[Finding]`, `recommendations: list[str]` | Verdict string parsing today; typed enum tomorrow |
| C2 | **Quality Review Report** | Markdown produced by `code-quality-reviewer-prompt.md` | `QualityReview(BaseModel)` with `tier: Literal["full", "minimum"]`, `verdict`, `issues: list[Issue]` with typed `severity` | Tier enum prevents the "minimum-tier" filename hack from drifting |
| C3 | **Partner Review Report** | Markdown produced by `controller-partner-prompt.md` | `PartnerReview(BaseModel)` with `verdict: Literal["APPROVED", "BLOCKED"]`, `concerns: list[DispatchConcern]`, `context_completeness_score`, `plan_alignment_score` | Minimum-tier ratio logic in `controller-checkpoint.py` today uses filename grep — typed tier makes it structural |
| C4 | **Plan Review Report** | Markdown, path pinned to `docs/imp-plans/plan-review-report.md` | `PlanReview(BaseModel)` with `verdict`, `iteration: int`, `findings: list[Finding]` | Plan-validation-gate currently checks file >50 bytes; Pydantic makes it verdict-specific |
| C5 | **Pre-Execution Audit** | Markdown at `reports/pre-execution-audit.md` | `PreExecutionAudit(BaseModel)` with typed check results | Hook currently only checks file size |
| C6 | **Dispatch Log Entry** | Line-oriented text: `task=N type={spec-review\|quality-review} timestamp=...` | `DispatchLogEntry(BaseModel)` one-per-line JSONL | Trivial migration; eliminates the `grep -q "task=$PREV type=spec-review"` fragility in `sdd-pre-dispatch-hook.sh` |
| C7 | **Plan Manifest** | Newline-separated file paths in `plan-manifest.txt` | `PlanManifest(BaseModel)` with `files: list[Path]`, optional `base_branch: str` | Low-value but cheap; gives the gate hook a place to version-pin if schema evolves |
| C8 | **Context Summary** | Markdown at `reports/context-summary.md` | `ContextSummary(BaseModel)` with `completed_tasks: list[TaskSummary]`, `cumulative_token_estimate: int` | Midpoint gate currently only checks file size; structural check catches "summary exists but omits tasks" |

### Tier D — Stretch / Lower Priority

| # | Asset | Current form | Pydantic model | Note |
|---|-------|--------------|---------------|------|
| D1 | **Token Estimate Output** | Ad-hoc JSON from `estimate-task-tokens.py` | `TokenEstimate(BaseModel)` with `status: Literal["OK", "WARNING", "TOO_LARGE"]`, `estimated_tokens: int`, `budget: int` | Already JSON; small win |
| D2 | **Design Spec / Distilled Spec** | Markdown from brainstorming skill outputs | `DesignSpec(BaseModel)` / `DistilledSpec(BaseModel)` | Higher prose content; less schema-shaped. Consider only if brainstorming → planning handoff starts losing fidelity |

---

### 2.1 Proposed Order of Implementation

```
Phase 1 (prove the pattern):  A1 ImplementerReport  →  A2 CheckpointResult
Phase 2 (unlock cross-task):  A3 Plan  →  B1 DeviationsRegister
Phase 3 (close honesty loop): B2 HonestyCheck  →  B3 TraceAudit
Phase 4 (review pipeline):    C1 SpecReview + C2 QualityReview + C3 PartnerReview
Phase 5 (cleanup):            C4–C8 gate-adjacent artifacts
Phase 6 (stretch):            D1 token estimate, D2 specs (only if needed)
```

**Rationale for ordering:**
- **A1 first** because `_report_utils.py` already has `REQUIRED_SECTIONS` and `VALID_STATUSES` — the schema is implicit, so migrating is literally just making the implicit explicit.
- **A2 second** because it's already emitting JSON; Pydantic is a `.model_dump()` swap, not a format change.
- **A3 third** because Plan validation unlocks the big cross-object wins (depends_on checking, constants checking) — but it's the largest schema and benefits from Phases 1–2 experience.
- **B1–B3 next** because these close the feedback-loop gates (deviations, honesty, trace audit) that are currently the most grep-reliant and therefore highest-value schema wins.
- **C/D later** because they're individually smaller wins; bundling them once the pattern is proven is cheaper than bespoke work.

---

## 3. Color Commentary — Key Conceptual Wins

### 3.1 The "single source of truth" principle, applied

Your global rule says *"If two code paths need the same behavior, they call the same method."* Today, the fork violates this at the schema level: `REQUIRED_SECTIONS` is defined in `_report_utils.py`, but the *meaning* of those sections (what each field should contain) is scattered across `implementer-prompt.md`, `validate-report.py`, and `controller-checkpoint.py`. Pydantic makes the model file the single source — the prompt references the schema, the validator imports the schema, the checkpoint consumes the schema. The sign-normalization class of bug you've been burned by becomes structurally impossible for report schemas.

### 3.2 Hook errors stop being "cryptic"

Today's hook FAILs read like:

```
BLOCKED: No spec-review dispatch recorded for Task 3. The dispatch log
(reports/.dispatch-log) has no entry for a spec reviewer being dispatched
via the Agent tool.
```

Helpful, but hand-written, and inconsistent across the 15+ BLOCKED messages in `sdd-pre-dispatch-hook.sh`. With Pydantic, every gate FAIL has the same shape: *path to the broken field, expected value, actual value*. The subagent receiving this can write a re-dispatch against specific fields rather than re-reading the entire hook output to guess what went wrong.

### 3.3 Schema evolution becomes tractable

Today adding a new required section to implementer reports means:
1. Edit `_report_utils.py:REQUIRED_SECTIONS`
2. Edit `implementer-prompt.md` to tell the subagent
3. Edit `validate-report.py` if there's special logic
4. Edit tests
5. Hope nothing drifts

With Pydantic, the model file is the change surface. Prompts reference `ImplementerReport.model_json_schema()`. Validators import the model. Tests parameterize against the model. One change, five dependents update mechanically.

### 3.4 The honesty-check feedback loop finally closes

`honesty-check-block.md` says "Add any uncertainties from answers 5-9 to DEVIATIONS.md as 'Pending — needs review.'" This is an **instruction to a human/agent** — there's no enforcement. With Pydantic:

```python
class HonestyCheck(BaseModel):
    answers: list[Answer]

    @model_validator(mode="after")
    def concerns_feed_to_deviations(self, info) -> Self:
        deviations = info.context["deviations_register"]
        flagged = [a for a in self.answers if a.question_number in (5,6,7,8,9) and a.flagged_concerns]
        for concern in flatten(flagged):
            if not deviations.contains(concern):
                raise ValueError(f"Honesty check flagged concern not in DEVIATIONS: {concern}")
        return self
```

The rule goes from advisory to mechanical. This is the shape of every high-value validator in the inventory: today's *"the human/agent should"* becomes tomorrow's *"the schema enforces."*

### 3.5 Provenance composition

Pydantic models compose naturally with the fork's future provenance aspirations (Sigstore-style signed dispatches from the gap analysis). A signed artifact is a Pydantic model with a `signature: bytes` field and a `@model_validator` that verifies the signature. The model *is* the provenance record; no separate tooling layer. When you're ready to add provenance, having Pydantic already in place makes it a field addition, not a parallel system.

---

## 4. Testing Strategy — How We Prove It Works

The fork already has a strong three-layer test strategy (static / install / unit / behavioral). Pydantic adoption adds three additional testing modes, all of which compose with the existing layers.

### 4.1 Model-level tests (unit, pytest) — per-model, per-field

For each new Pydantic model, create `tests/unit/test_models/test_<model_name>.py` with:

**a. Golden-input tests** — a canonical valid instance parses without error, round-trips through JSON, and `model_dump() == expected_fixture`.

**b. Per-field failure tests** — parameterized over each field:
- Missing required field → `ValidationError` with path `field_name`
- Wrong type → `ValidationError` with `type_error`
- Out-of-range enum → `ValidationError` with `literal_error`

**c. Cross-field validator tests** — for each `@model_validator`, a fixture that violates the rule and asserts the specific error message surfaces.

```python
# Example pattern
def test_implementer_report_missing_status_fails():
    with pytest.raises(ValidationError) as exc:
        ImplementerReport.model_validate({"files_changed": []})
    assert exc.value.errors()[0]["loc"] == ("status",)
    assert exc.value.errors()[0]["type"] == "missing"
```

**d. Parse-and-render invariance** — for models with markdown rendering:
```python
def test_implementer_report_roundtrip_preserves_content():
    original = ImplementerReport.model_validate(GOLDEN_REPORT)
    rendered_md = original.to_markdown()
    reparsed = ImplementerReport.from_markdown(rendered_md)
    assert original == reparsed
```

### 4.2 Contract tests (integration) — across models

Separate test file per relationship. Example: `test_plan_report_contract.py`:

```python
def test_report_contracts_must_cover_plan_dependencies():
    plan = Plan.model_validate(fixture_plan("feature_x"))
    next_task_deps = plan.tasks[3].depends_on
    report = ImplementerReport.model_validate(fixture_report("task-002"))

    # This validator lives in a PlanExecutionContract model
    with pytest.raises(ValidationError, match="missing required contracts"):
        PlanExecutionContract.model_validate({
            "plan": plan,
            "completed_reports": [report_missing_deps],
        })
```

### 4.3 Shadow-mode migration tests — safety net for Phase 1

This is the **critical migration-safety pattern**. For each model that replaces an existing grep/regex check, run both validators in parallel during a burn-in period and log disagreements:

```python
def test_shadow_validate_report_matches_grep_validator():
    """During migration, new Pydantic validator must agree with old grep validator.
    Any disagreement is a potential bug in either — log and investigate."""
    for fixture in historical_reports():  # real reports from past SDD sessions
        old_result = old_validate_report_grep(fixture)
        new_result = ImplementerReport.model_validate(fixture).validation_status()
        assert old_result.overall == new_result.overall, \
            f"Disagreement on {fixture.name}: grep={old_result} pydantic={new_result}"
```

Run this test **against every historical report in the repo's git history** — they're a free, realistic regression corpus. If Pydantic and grep disagree on any of them, something about the migration is wrong.

### 4.4 Hook integration tests — the feedback-loop property

The entire argument for Pydantic rests on *explanatory errors reaching the subagent*. Test this end-to-end:

```python
def test_hook_FAIL_emits_structured_diagnostic():
    malformed_report = fixture("implementer-report-missing-status.md")
    hook_output = run_hook(malformed_report)

    # The subagent-facing error must contain enough detail to fix the problem
    assert "status" in hook_output  # field path
    assert "Status" in hook_output  # human-readable section name
    assert "DONE" in hook_output  # hint at valid values
    assert "DONE_WITH_CONCERNS" in hook_output
```

Add to the existing `tests/unit/test_sdd_hard_gates.py` pattern (which already tests hook block messages).

### 4.5 Property-based tests (stretch, using Hypothesis)

For high-volume models (especially `ImplementerReport` and `Plan`), add Hypothesis-driven tests that generate random valid instances and assert invariants:

```python
from hypothesis import given, strategies as st

@given(st.builds(ImplementerReport))
def test_implementer_report_status_always_valid(report):
    assert report.status in {"DONE", "DONE_WITH_CONCERNS", "BLOCKED", "NEEDS_CONTEXT"}

@given(st.builds(ImplementerReport))
def test_implementer_report_markdown_roundtrip(report):
    assert ImplementerReport.from_markdown(report.to_markdown()) == report
```

This catches edge cases humans don't think to write fixtures for.

### 4.6 Behavioral tests — does the subagent actually use the error?

The existing `tests/ARaymond-skill-behavior/run-all.sh` framework invokes real Claude Code sessions. Add one scenario per migrated model:

- Deliberately corrupt a test fixture so it fails Pydantic validation
- Run a subagent dispatch that receives the validation error
- Assert the subagent's corrective dispatch targets the specific field(s) flagged

This is the only way to empirically verify that the "explanatory errors teach the subagent" claim holds in practice vs. just in theory.

### 4.7 Test counts after adoption (estimate)

| Layer | Today | After Pydantic (Phase 3 complete) |
|-------|-------|-----------------------------------|
| Unit tests | 70 | ~120 (model tests, contract tests, shadow-mode tests) |
| Regression checks | 122 | ~122 (unchanged — static skill file checks) |
| Install checks | 103 | 105 (+2 for Pydantic version pinning, model import smoke test) |
| Behavioral scenarios | ~10 | ~13 (+3 for subagent error-consumption tests) |

### 4.8 Setup prerequisites

**Pydantic is not currently installed in `.venv/`.** First step of Phase 1:

```bash
# Pin to v2 minor (v2 has breaking changes vs v1)
echo "pydantic>=2.7,<3" >> requirements.txt
.venv/bin/pip install -r requirements.txt
```

Add to `verify-symlink-install.sh`:
```bash
check "Pydantic installed" ".venv/bin/python3 -c 'import pydantic; assert pydantic.VERSION.startswith(\"2.\")'"
```

---

## 5. Staged Rollout Principles

**Shadow before replace.** Phase 1 deploys `ImplementerReport` validation *alongside* the existing grep validator. Both run in every hook invocation. Disagreements are logged but the grep result is authoritative. After ~2 weeks of zero disagreements on a representative corpus, the grep validator is removed.

**One prompt-template rewrite per model.** When A1 migrates, `implementer-prompt.md` adds *"emit your report as JSON matching the attached `ImplementerReport` schema; markdown rendering will be generated automatically."* No other prompt changes in Phase 1.

**Keep markdown as the human-facing artifact.** The controller and reviewers continue reading markdown. Pydantic's `.to_markdown()` renderer produces files indistinguishable from today's output. Humans don't see the JSON.

**Hook errors are the first feature to ship, not the last.** The explanatory-error property is the single largest behavioral improvement Pydantic brings. Wire it into hook output *before* worrying about cross-model validators. Shipping the property early lets you measure "does the subagent actually recover better?" against real sessions.

**Write a rollback path for each phase.** Pydantic is a new dependency in a Python-script system. Each phase must include a rollback commit that restores the grep/regex validator — so if a phase ships a regression, cutover is reversible without pinning users to a broken version.

---

## 6. Open Questions For Brainstorming

1. **Scope of Phase 1:** ship A1 alone, or A1+A2 together (since A2 is nearly free)?
2. **Markdown renderer location:** is `.to_markdown()` a method on the model, or a separate `renderers/` module? (Model method is more ergonomic; separate module is more testable in isolation.)
3. **Subagent output format:** force JSON via tool-use (Instructor-style) or allow markdown-with-fenced-JSON and parse? The first is stricter but changes prompt template semantics substantially.
4. **Shadow-mode duration:** how many real SDD sessions constitute "enough" before retiring grep?
5. **Error-message prompt injection:** once subagents start receiving ValidationError text, that text enters their context. Should we sanitize/wrap it to prevent adversarial failure-mode loops where a subagent deliberately produces errors it can exploit?
6. **Hypothesis dependency:** worth adding, or keep property-based tests out of scope for v1?

---

`★ Insight ─────────────────────────────────────`
- **The fork is *almost* schema-driven already — it just doesn't know it.** Every candidate in Tier A has its schema declared somewhere (section constants, enum sets, JSON key patterns) but in a form the type system can't use. Pydantic adoption isn't "adding structure" — it's "making the existing structure honest."
- **The highest-value validator in the entire inventory is the one nobody writes today: "honesty-check concerns must appear in DEVIATIONS."** That's a semantic invariant of the SDD process that lives only as prose in `honesty-check-block.md`. Pydantic makes it mechanical. That one validator alone justifies a Phase 3.
- **Shadow mode turns historical artifacts into a free regression corpus.** Every report the fork has ever produced is sitting in past git histories. Running the new validator over all of them before cutover is the cheapest insurance available — and it's only possible because Pydantic's input is typed, whereas today's grep validators each parse slightly differently and can't be compared across time.
`─────────────────────────────────────────────────`
