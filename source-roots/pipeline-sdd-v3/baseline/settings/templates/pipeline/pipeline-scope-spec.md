# Pipeline Scope Specification

## Purpose
<!-- What this run of the pipeline covers, for which legacy material, and under which research framing. 1–2 paragraphs. -->
{{PURPOSE}}

## Scope Integrity Discipline
<!-- The commitments this artifact makes: no capability decisions yet, no semantic claims, boundaries stated before analysis begins. -->
- This artifact bounds the run; it does not select the capability (stage 2) nor interpret behavior (stages 3–4).
- Every boundary statement must distinguish proof-of-concept conditions from expected institutional conditions.

## Section 1: Source Layer Identification

### 1.1 Legacy Source Programs
<!-- Inventory the legacy artifacts in scope: files, roles, approximate size. Inventory only — no behavioral claims. -->

### 1.2 Reference Layer (if any)
<!-- Identify any non-authoritative comparison/execution layer and state its subordinate role explicitly. -->

## Section 2: Capability Boundary

### 2.1 In-Scope Operations
### 2.2 Out-of-Scope Capabilities
<!-- What is deliberately excluded and why. -->
### 2.3 Proof-of-Concept vs. Institutional Scope
<!-- Institutional applicability notes: where PoC conditions will not transfer directly. -->
### 2.4 Architectural Constraints Known at Scope Time
<!-- Constraints already visible before evidence work (e.g., absence of account identifier). Each gets stated here and inherits downstream. -->

## Section 3: Pipeline Stage Map

### 3.1 Specification Artifact Stages
<!-- The intended stage sequence for this run, referencing steering/pipeline.md. Note any run-specific adjustments. -->
### 3.2 Structural Separation Commitments
<!-- Which separations this run commits to preserve (evidence/semantics, semantics/contract, contract/adapter, research/framework). -->

## Section 4: Research Context

### 4.1 Research Objective
<!-- How this run serves the research study objective. -->
### 4.2 Legacy Artifact Constraints
<!-- Known limits of the material: execution model, persistence, environment. -->
### 4.3 LLM Role Statement
<!-- What AI assistance is allowed to do in this run (see rules/ai-assistance.md) and provenance expectations. -->

## Section 5: Artifact Chain and Scope Completion

### 5.1 Intended Artifact Chain
<!-- The concrete spec directories this run intends to produce. -->
### 5.2 Scope Completion Gate

## Completeness Gate and Stage 2 Entry Condition
<!-- Explicit, checkable conditions. Example set: -->
- [ ] Source layer inventoried with roles assigned
- [ ] In-scope and out-of-scope boundaries stated and justified
- [ ] Known constraints registered for downstream inheritance
- [ ] PoC vs institutional divergences noted
- [ ] Human review outcome: Approve

**Stage 2 entry condition**: this gate passed and recorded in `spec.json`.
