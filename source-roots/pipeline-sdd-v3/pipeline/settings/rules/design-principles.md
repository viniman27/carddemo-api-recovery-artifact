# Design Principles

These principles govern the design of all artifacts produced in this project.

This project is not a generic software feature workflow. It is a specification-driven master's research pipeline for COBOL legacy modernization, in which actionable knowledge is progressively recovered from legacy artifacts and transformed into structured semantics, API contracts, adapter behavior, and validation artifacts.

The principles below must be applied across all stages of the pipeline.

## 1. Single Responsibility per Spec

Each spec must answer one main question only.

A spec must not collapse multiple conceptual layers into a single artifact. In particular, do not combine the following in the same document unless the artifact type explicitly requires it:

- legacy evidence
- business semantics
- canonical data modeling
- API contract design
- adapter behavior
- implementation detail
- task planning
- validation logic

The purpose of this principle is to preserve clarity, traceability, and manageable context size.

When a spec begins to accumulate multiple layers of meaning, split it instead of enlarging it.

## 2. Capability-First Decomposition

Design work must be centered on business capabilities recovered from legacy behavior, not merely on source files, modules, or technical components.

A COBOL program, paragraph, routine, or copybook is not automatically the unit of modernization.
The primary unit of analysis in this project is the capability of business significance that may later be exposed through an API-oriented integration boundary.

Therefore:
- do not assume file boundaries are capability boundaries
- do not assume one program equals one capability
- do not assume a capability exists without evidential support
- explicitly justify the chosen capability scope

## 3. Evidence Before Interpretation

When extracting meaning from COBOL, prioritize observable evidence from source code and related legacy artifacts.

Interpretation must be explicitly separated from raw evidence.

All design stages must preserve the distinction between:
- directly observed evidence
- inferred semantics
- unresolved ambiguity

Do not present plausible inference as confirmed fact.
Do not hide missing evidence by replacing it with polished assumptions.
When the evidence is incomplete, the artifact must remain incomplete in an explicit and reviewable way.

## 4. Specification Before Interface

Before proposing an API contract, the process must produce and stabilize the following:

- evidence from the legacy system
- a structured capability semantics artifact
- a canonical data boundary

This project rejects direct jumps from code inspection to interface design.
API contracts must be derived from a prior semantic layer, not directly from source syntax or implementation convenience.

Likewise, adapter behavior must be derived from the contract and semantics, not invented independently.

## 5. Semantics Before Implementation

Implementation-oriented artifacts must not overtake semantic reconstruction.

In this project, the correct progression is:

legacy evidence -> capability semantics -> canonical data boundary -> API contract -> adapter behavior -> semantic validation

This means:
- discovery stages are document-first
- interface stages are contract-first
- implementation stages come only after the relevant semantic and interface artifacts exist

If code is generated earlier by the framework, it must be treated as auxiliary and non-authoritative until the corresponding semantic artifacts are stabilized.

## 6. Traceability by Design

Every downstream artifact must remain traceable to upstream artifacts.

The minimum traceability chain is:

legacy evidence -> capability semantics -> canonical data boundary -> API contract -> adapter behavior -> validation

This traceability must be strong enough to support:
- analytical review
- error localization
- methodological transparency
- research study-level argumentation

No downstream design decision should exist without a recoverable link to upstream evidence or structured semantics.

## 7. Controlled Modernization

Prefer incremental, integration-oriented modernization over wholesale rewrite assumptions.

The objective is not to replace the entire legacy system at once, nor to assume that reimplementation is the natural first move.
The objective is to expose selected capabilities in a controlled, reviewable, and semantically grounded manner.

Therefore:
- prefer stable integration boundaries over broad redesign
- prefer capability extraction over full-system rewriting
- prefer explicit intermediate artifacts over direct code generation
- prefer measured transformation over speculative modernization

## 8. Canonicalization Before Technology Choices

Data meaning must be stabilized before transport and framework decisions are made.

The project must first identify:
- what inputs and outputs mean
- what fields are semantically relevant
- what validations and invariants matter
- how legacy structures map to a canonical boundary

Only after that should the process define:
- endpoint shape
- method selection
- error exposure style
- adapter structure
- framework-specific implementation choices

This protects the project from leaking accidental implementation decisions into the semantic layer.

## 9. Research-Oriented Outputs

Outputs must be suitable for a master's research workflow.

Every relevant artifact should be:
- analyzable
- reviewable
- comparable
- traceable
- discussable in writing
- defensible in a research study context

This means artifacts should not only be useful for implementation, but also for explanation, critique, and evaluation.

If an artifact is operationally useful but analytically opaque, it is insufficient for this project.

## 10. Explicit Treatment of Ambiguity

Ambiguity is not a failure of the process; hidden ambiguity is.

Whenever the legacy system does not provide enough evidence to support a strong conclusion, the artifact must record:
- what is unclear
- why it is unclear
- what evidence is missing
- whether human review is needed
- whether downstream derivation should be blocked or allowed with caution

The process should prefer explicit uncertainty over premature certainty.

## 11. Stage-Appropriate Artifact Generation

Not every stage is allowed to generate every artifact type.

The stages of discovery must prioritize:
- notes
- evidence summaries
- semantic structures
- canonical data models

The stages of contract and adaptation may later generate:
- API contracts
- adapter behavior artifacts
- implementation-oriented files
- validation assets

This project does not reject implementation.
It rejects premature implementation.

## 12. Framework Subordination to Research Logic

If the SDD framework attempts to generate artifacts that violate the project logic, the research logic takes precedence.

This includes cases where the framework prematurely generates:
- orchestration modules
- service layers
- public execution surfaces
- API-facing code
- adapter code

In such cases, those artifacts must be treated as exploratory by-products, not as authoritative outputs of the current stage.

The framework is a support mechanism.
It is not the methodological authority of the project.

## Desired Design Outcome

A well-designed artifact in this project should do three things simultaneously:

1. remain faithful to the legacy evidence available
2. support the next stage of the specification-driven pipeline
3. remain intelligible and defensible as part of a research argument

If an artifact is implementable but not explainable, it is insufficient.
If it is explainable but not traceable, it is insufficient.
If it is traceable but collapses multiple conceptual layers at once, it is insufficient.