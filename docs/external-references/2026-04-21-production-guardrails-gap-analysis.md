# Gap Analysis — Production Guardrails vs Superpowers Fork

**Date:** 2026-04-21
**Source input:** `2026-04-21-claude-code-production-guardrails.md`
**Status:** DRAFT — discussion input for brainstorming session
**Owner:** Aaron Raymond

---

## Executive Summary

The Superpowers fork already implements structural equivalents of all three DO's and mitigations for all three DON'Ts — but at **coarse granularity** (markdown regex, grep patterns, file-existence checks). The biggest unrealized leverage is replacing **pattern-based validation** with **schema-based validation**, which the LinkedIn infographic's Pydantic example points at directly. This document scores each item, identifies the gap, and surveys novel technologies beyond Pydantic that could raise the determinism ceiling.

Scoring: 🟢 strong / 🟡 partial / 🔴 weak.

---

## Section 1 — DO's: How We Measure Up

### DO-1: Deterministic Prompt Design 🟡 Partial

**Infographic advice:** Templated prompts, bounded `max_tokens`, bounded `timeout`, low temperature.

**What the fork does:**
- Inline prompt templates (`implementer-prompt.md`, `spec-reviewer-prompt.md`, `code-quality-reviewer-prompt.md`, `trace-auditor-prompt.md`, `controller-partner-prompt.md`) with variable injection points.
- Token estimation pre-dispatch (`estimate-task-tokens.py`) — advisory bound on context size, not output.
- Context compression (`context-summary.py`) past midpoint to prevent context bloat.

**Gap:**
- **No output token budget** per subagent. Claude Code's harness doesn't expose `max_tokens` at the skill layer, so reports can balloon silently. Today's only brake is validate-report.py's minimum-section check — not a cap.
- **No timeout wall** on subagent work. A runaway implementer can consume arbitrary time.
- **Prompt drift is invisible.** Templates are free-form markdown; there's no snapshot/diff check that the dispatched prompt matches the template. A controller editing the template mid-session wouldn't be caught.

**Candidate improvements:**
- Emit a **prompt hash** alongside each dispatch; fail hook if template hash changes mid-plan without an explicit version bump.
- **Output length budgets** per report section in `validate-report.py` (e.g., uncertainties ≤ 2000 chars, summary ≤ 500).

---

### DO-2: Structured Output Enforcement 🟡 Partial — **highest-leverage gap**

**Infographic advice:** Pydantic BaseModel on every LLM output. Parse or fail.

**What the fork does:**
- `validate-report.py` grep-checks for 9 required sections in markdown.
- `validate-plan.py` regex-checks task headers, module headers, source contract field.
- Hook gates check for file existence, minimum byte size, dispatch-log entries.

**Gap (this is the big one):**
- **Reports are markdown-with-conventions, not typed data.** The 9 sections must exist, but:
  - A "Decisions Made" section can be empty prose.
  - An "Uncertainties" section can say "None" without proof that any were actually considered.
  - A "Deviations" reference can point to a DEVIATIONS.md row that doesn't exist.
  - Cross-references (task N cites task N-1's decisions) aren't enforced.
- **Subagents produce free-form text then the controller paraphrases it.** Each paraphrase is a decoding loss opportunity.
- **No schema contract between plan and report.** The plan says "implement X with signature Y" — the report has no mandatory `contracts_implemented: [{name, signature}]` field the hook could diff against.

**Why this is the highest-leverage gap:**
Every other enforcement layer (honesty checks, trace audits, partner reviews) is inspecting the *output of a structured-output layer that doesn't fully exist yet*. Upgrading from "markdown with required section headers" to "typed report with schema-validated fields" would make every downstream check sharper and more automatable.

---

### DO-3: Retrieval Optimized 🟢 Strong

**Infographic advice:** Fetch top-k relevant docs; join into context; minimize tokens/latency.

**What the fork does:**
- `context-summary.py` compresses prior task reports.
- Plan manifest scopes validation to only the current feature's files (via `plan-manifest.txt`).
- Progressive disclosure: `references/` dirs keep SKILL.md under 5000 words.
- QMD as a semantic layer for the user's vault (not subagent-facing but same philosophy).

**Gap:**
- No per-task **selective retrieval** of the plan. The implementer-prompt bundles the entire task block as context, not just dependencies. A task depending on contracts from Task 3 gets Task 1, 2, 4, 5 context it doesn't need.
- **No embedding-based selection** — the fork is keyword/structure-based throughout. QMD exists globally but isn't wired into subagent dispatch.

**Candidate improvement:** Pre-dispatch retrieval step that pulls only the referenced tasks/contracts/pattern-refs into the implementer's context, using BM25 or a small embedding model.

---

## Section 2 — DON'Ts: Mitigations Present?

### DON'T-1: Unbounded Generation 🟡 Partial

**Mitigations:**
- `estimate-task-tokens.py` → BLOCK on unestimable task (input bound).
- `context-summary.py` at midpoint (cumulative-context bound).

**Gap:**
- **No per-subagent output cap.** The harness controls `max_tokens`, not the fork.
- **No temperature floor assertion.** We trust the default; there's no record of what model/temperature the subagent actually ran under.

---

### DON'T-2: Prompt Injection Exposure 🔴 Weak — **second-highest-risk gap**

**Current posture:**
- `handoff-acceptance` skill gates incoming packages via `check-handoff.sh`, which grep-checks for a contract summary in the first 50 lines.
- Plan-validation gate checks `plan-review-report.md` exists before plan execution.

**Gap:**
- **Handoff content is treated as instructions, not untrusted data.** A malicious or malformed handoff file could inject directives into the brainstorming/planning pipeline with no sanitation layer.
- **User-supplied spec text** (brainstorming outputs) flows into planning prompts. A distilled spec could contain prompt-injection payloads that would be honored by downstream subagents.
- **No isolation boundary** between "data to reason about" and "instructions to follow." Subagents see both in the same context window.

**Why this is under-addressed:**
The fork's threat model has implicitly been "trusted user, trusted subagent, adversarial bugs." The LinkedIn graphic's concern is "adversarial input" — which becomes real the moment handoffs come from automated pipelines or untrusted agents.

---

### DON'T-3: No Output Validation 🟢 Strong

**Mitigations:**
- `validate-report.py`, `validate-plan.py`, `controller-checkpoint.py`, trace audit, honesty check, partner review, pre-completion gates.
- Swiss Cheese: multiple independent layers, any one catches drift.

**Gap:**
- As noted in DO-2, validation is *structural* (section exists, file >50 bytes) not *semantic* (field has expected type/range/cross-reference). Upgrading DO-2 closes this gap too.

---

## Section 3 — Scorecard

| Item | Fork Grade | Biggest Gap | Leverage to Fix |
|------|-----------|-------------|-----------------|
| Deterministic Prompts | 🟡 | No prompt hash / output cap | Medium |
| **Structured Output** | 🟡 | **Markdown-regex instead of schema** | **Highest** |
| Retrieval Optimization | 🟢 | No per-task selective retrieval | Medium |
| Unbounded Generation | 🟡 | No output token cap | Low (harness-limited) |
| **Prompt Injection** | 🔴 | **No untrusted-input boundary** | **High** |
| Output Validation | 🟢 | Depends on DO-2 upgrade | — |

---

## Section 4 — Novel Technology Survey

Pydantic is one option. Here's the wider landscape of 2025–2026 tooling that could enforce determinism more rigorously than markdown + regex.

### 4a. Schema & Structured-Output Layers

| Tech | What It Does | Fit For Fork |
|------|-------------|--------------|
| **Pydantic v2** | Runtime validation + JSON Schema generation for Python dataclass-style models. | ⭐ Drop-in for report/plan schemas. `validate-report.py` becomes `ReportModel.model_validate_json(...)`. |
| **Instructor** | Wraps LLM clients to force Pydantic-typed responses via tool-use. | ⭐ Best for the actual subagent call — forces JSON tool output instead of markdown. |
| **Outlines** | Regex/CFG/JSON-Schema-constrained token generation. Guarantees valid output at decode time. | Requires local model control — Claude Code doesn't expose decoder hooks. Not directly applicable but worth understanding. |
| **BAML** | DSL for declaring LLM functions with typed inputs/outputs; compiles to runtime. | Interesting for rewriting prompt templates as typed functions. Migration cost is high. |
| **Guardrails AI** | Python framework: schema → validators → re-ask on failure. | ⭐ Matches fork's "validate then fail/retry" pattern; could replace validate-report.py with richer validators (SQL injection, PII, semantic checks). |
| **Marvin (Prefect)** | Pydantic-first LLM orchestration. Functions return Pydantic types. | Overlaps with Instructor. Smaller community. |
| **DSPy** | Programmatic prompts as modules; optimizer finds best prompts for a metric. | ⭐⭐ **Novel angle** — treat implementer-prompt.md as a DSPy program; let it *learn* which phrasings reduce uncertainty flags. |
| **LMQL** | Query language for LLMs with typed constraints. | Research-grade. High switching cost. |
| **TypeChat (Microsoft)** | TypeScript-first structured output with schema auto-repair. | Not Python-native; fork is Python. |

### 4b. Contract & Interface Validation

| Tech | What It Does | Fit For Fork |
|------|-------------|--------------|
| **JSON Schema Draft 2020-12** | Universal declarative schemas. | ⭐ Portable — plans and reports could declare JSON Schema blocks that subagents both emit AND validate against. |
| **OpenAPI / AsyncAPI** | Contract-first API definitions. | Overkill for report format but useful if subagent dispatch becomes a real RPC. |
| **Protobuf / Cap'n Proto** | Binary schemas with strong types. | Too heavy for human-readable reports. |
| **Pact** | Consumer-driven contract testing. | ⭐⭐ **Novel angle** — plan = consumer contract, subagent report = provider response. Pact-style testing would catch "subagent claims to implement X but report says Y." |

### 4c. Execution Determinism & Provenance

| Tech | What It Does | Fit For Fork |
|------|-------------|--------------|
| **Deterministic Replay (Hermit, rr)** | Record-and-replay for deterministic debug. | Not AI-specific but inspires: record every dispatch's (prompt, model, seed, output) for audit replay. |
| **OpenTelemetry + Trace Spans** | Distributed tracing with structured metadata. | ⭐ Already extracting traces from JSONL; formalizing as OTel spans would let any OTel-aware tool consume them. |
| **Sigstore / in-toto** | Supply chain provenance for builds. | ⭐⭐ **Novel angle** — attest every report with a signed manifest: "produced by subagent X from template hash Y against plan hash Z." Makes forgery detection mechanical. |
| **Merkle DAGs** | Content-addressed history. | Overkill but would make "did anything get silently rewritten?" trivial to check. |

### 4d. Prompt Injection Defense

| Tech | What It Does | Fit For Fork |
|------|-------------|--------------|
| **Lakera Guard / PromptGuard (Meta)** | Classifier models that detect injection attempts. | ⭐ Run over incoming handoff packages before they enter the pipeline. |
| **NVIDIA NeMo Guardrails** | DSL for input/output rails with LLM-based policies. | Powerful but adds a dependency and a second model. |
| **Rebuff** | Multi-layer injection detection (heuristics + canary + LLM + vectordb). | ⭐ Pre-built layered defense; aligns with Swiss Cheese model. |
| **Spotlighting / Delimiter Tagging** | Wrap untrusted content in dedicated delimiters; system prompt tells model to treat delimited content as data only. | ⭐ Zero-dependency — can be added to implementer-prompt.md template today. Cheapest first step. |
| **Dual-LLM Pattern (Simon Willison)** | Privileged LLM orchestrates; quarantined LLM processes untrusted content. | ⭐⭐ **Novel angle** — maps onto subagent architecture already. Formalize the trust boundary: handoff content only reaches "quarantined" analysis subagents, never orchestration ones. |

### 4e. Retrieval & Context Management

| Tech | What It Does | Fit For Fork |
|------|-------------|--------------|
| **LanceDB / Qdrant / ChromaDB** | Embedded vector stores. | Could index plan files for per-task retrieval. QMD already partially fills this role. |
| **BM25S / rank_bm25** | Pure-Python BM25. | ⭐ Lightweight; already used by QMD. Trivial to wire into dispatch. |
| **ColBERT / late-interaction retrieval** | Higher-precision retrieval than dense embeddings. | Overkill for plan sizes; worth noting for large-codebase tasks. |
| **LlamaIndex SubQuestion / RAPTOR** | Hierarchical retrieval for large corpora. | Relevant if plans grow beyond what fits in a single context. |

---

## Section 5 — Three Ideas Worth Brainstorming

Ranked by (impact × novelty × fit):

### Idea A — Reports-as-Pydantic-Models (not markdown)
**Essence:** Define `ImplementerReport(BaseModel)` with typed fields: `summary: str`, `files_modified: list[FileChange]`, `contracts_implemented: list[Contract]`, `uncertainties: list[Uncertainty]`, `deviations: list[DeviationRef]`. Subagent emits JSON via tool-use (Instructor-style). Controller and hooks validate by `.model_validate_json()`. Current markdown is a *rendering* of this model.

**Why novel here:** Collapses `validate-report.py` regex grep into a type check. Makes cross-task validation trivial (task N's `contracts_implemented` must be a superset of task N+1's `depends_on`).

**Risk:** Subagents must be constrained to tool-use output, which changes the implementer-prompt template substantially. Markdown reviewability is preserved via a renderer.

---

### Idea B — Signed Report Provenance (in-toto / Sigstore style)
**Essence:** Every dispatch produces `(prompt_hash, template_version, plan_hash, model, timestamp, output_hash)` signed into `reports/.provenance/`. Hook verifies chain: "report X claims to be produced from plan version Y via template version Z" must match the current state. Forged reports (controller self-writing) fail signature check.

**Why novel here:** Turns dispatch-log auditing from grep-based ("does the string appear?") into cryptographic ("does the chain verify?"). Catches entire classes of bypass attempts — including ones you haven't imagined yet.

**Risk:** Key management in a CLI context. Probably need ed25519 keys in `~/.claude/` or an ephemeral session key. Signing at dispatch time is the question.

---

### Idea C — Dual-LLM / Quarantine Pattern for Handoffs & Specs
**Essence:** Formalize the trust boundary Simon Willison describes. Untrusted input (handoff packages, user-supplied specs) is processed by a **quarantined subagent** whose only output is a validated Pydantic model. The orchestrator never sees the raw untrusted text — only the validated structured summary. Applies spotlighting delimiters as the cheap first layer; upgrades to full quarantine for sensitive stages.

**Why novel here:** Closes DON'T-2 (prompt injection) at an architectural level, not a pattern-matching level. Fits the existing subagent-per-task model — it's a role refinement, not a new component.

**Risk:** Adds a dispatch per handoff. Cost/latency non-trivial but aligned with SDD's "one subagent per discrete task" philosophy.

---

## Section 6 — Open Questions for Brainstorming

1. **Report schema scope:** Do we boil the ocean (full Pydantic models for every report type) or start with one high-value report (implementer report) as a proof point?
2. **Harness limits:** What does/doesn't Claude Code let us control at the tool-invocation layer? Can we force a subagent into tool-use-only mode from a skill?
3. **Provenance practicality:** Is signed provenance overkill given that the threat model is *agent drift*, not *malicious adversary*? Or does drift count as adversarial when it's the controller gaming its own gates?
4. **DSPy / optimizable prompts:** Could the fork *learn* better implementer prompts from its own trace history? The JSONL sessions are a training set.
5. **Pact-style contract tests:** Plan declares contracts → subagent report claims contracts-satisfied → test suite exercises the claim. Who writes the test?

---

`★ Insight ─────────────────────────────────────`
- **The fork's Swiss Cheese model is strong on structural layers but weak on typed payload.** Every hole in every slice is checking "does this text contain X?" — none are checking "does this *data* match a *schema*?". Moving one layer from text-grep to schema-validate collapses multiple follow-on checks.
- **DSPy + fork's JSONL traces is the most unexplored synergy.** You already record every dispatch outcome; DSPy's optimizer wants exactly that kind of (input, output, score) tuple to refine prompts. The fork could literally improve its own implementer prompt over time.
- **Dual-LLM pattern is the architectural peer of hooks.** Hooks are runtime gates; dual-LLM is a structural gate. The two compose: hooks catch drift inside the pipeline, dual-LLM prevents untrusted input from reaching the pipeline at all.
`─────────────────────────────────────────────────`
