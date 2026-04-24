# Claude Code in Production — Guardrails Reference

**Captured:** 2026-04-21
**Source:** LinkedIn, "Artificial Intelligen..." group
**Author:** Brian Reiff
**Purpose:** External reference for Superpowers fork improvement planning. Use as input for brainstorming guardrail/determinism enhancements.

---

## Part 1 — Infographic: "Claude Code in Production — What Actually Works vs What Breaks"

### ✅ DOs

#### 1. Deterministic Prompt Design
```python
# Good
response = client.responses.create(
    model="claude",
    prompt=template.format(input=data),
    max_tokens=300,
    timeout=5
)
```
*Enforce reproducibility and bounded output.*

#### 2. Structured Output Enforcement
```python
from pydantic import BaseModel:
    status: str
    data: dict
```
*Always validate outputs using schemas.*

#### 3. Retrieval Optimized
```python
# Good
docs = retriever.search(query, top_k=5)
context = "\n".join(d.content for d in ...)
```
*Minimize tokens & latency with retrieval.*

---

### ❌ DON'Ts

#### 1. Unbounded Generation 💲💲💲
```python
# Bad:
temperature=1.0
max_tokens=None
```
*Non-deterministic + runaway costs.*

#### 2. Prompt Injection Exposure 🐛
```python
# Bad:
prompt = user_input
```
*User controls system behavior.*

#### 3. No Output Validation ⚠️
```python
# Bad:
return llm_output
```
*Propagates invalid or unsafe results.*

---

### Pipeline Diagram
```
Input → Model → Validation → Output
```

### What Actually Breaks In Production?
| Stage | Failure Mode |
|-------|-------------|
| Input | Cost spikes 💲 |
| Model | Silent failures 🔄 |
| Output | Blind debugging 🔍 |
| — | Downstream failures ❗ |
| — | Fragile systems 🔄 |
| — | Blind debugging 🔍 |

---

## Part 2 — Supporting LinkedIn Post

> 🚨 Most teams don't fail at AI; they fail at everything **around it**
>
> 🧠 **Deterministic prompts**, structured outputs, and retrieval aren't "nice to have"; they're the difference between a demo and **production**
>
> 💸 Unbounded tokens and bad context design quietly turn into **massive cost** problems
>
> 🔓 Prompt injection and no validation create **risks** most teams don't even see coming
>
> ⚙️ The model isn't the hard part; building a **reliable system** around it is
>
> 📉 What actually breaks in production isn't intelligence; it's the lack of **guardrails**
>
> \#AI #Claude #LLM #AIDevelopment #MachineLearning #TechLeadership #ArtificialIntelligence

---

## Relevance to Superpowers Custom Fork

This content aligns with the fork's Swiss Cheese defense model (see `docs/plans/2026-03-24-deterministic-ai-agent-discipline-hooks-analysis.md`). The core thesis — that systems around the model matter more than the model itself — is the same philosophy driving hook-based enforcement, pre-dispatch gates, and multi-layer review. See companion gap analysis: `2026-04-21-production-guardrails-gap-analysis.md`.
