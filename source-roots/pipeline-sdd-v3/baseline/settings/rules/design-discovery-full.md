# Design Discovery Full

Use this mode only when sufficient legacy material is available and the goal is to construct a rigorous, structured, and evidence-based understanding of a candidate COBOL business capability.

In this project, full discovery is a reverse-engineering stage, not an implementation stage. Its purpose is to recover and structure actionable knowledge from legacy artifacts so that later stages may derive stable specifications, contracts, and adapters for API-oriented modernization.

## Primary purpose

Full discovery must transform scattered legacy evidence into structured analytical artifacts that support the following progression:

legacy COBOL -> legacy evidence -> capability semantics -> canonical data boundary -> API contract -> adapter behavior -> semantic validation

At this stage, the focus is exclusively on the left-hand side of that progression.

## Expected outputs

Full discovery should prioritize the creation or refinement of the following document-first artifacts:

- capability selection spec
- legacy evidence spec
- capability semantics spec
- canonical data boundary spec

These artifacts must be treated as the primary outputs of discovery.
If any code files are produced, they must remain strictly auxiliary and must not become the source of truth for semantics, interface definition, or execution flow.

## Discovery scope

Full discovery must answer, as explicitly as possible:

1. What business capability is being analyzed?
2. Which legacy artifacts participate in that capability?
3. What evidence supports the identification of that capability?
4. What are the inputs, outputs, rules, validations, and side effects associated with it?
5. What semantic structure can be stated with reasonable confidence?
6. What remains ambiguous, incomplete, or dependent on human review?

## Required analytical dimensions

For each candidate capability, examine and document:

- business purpose
- source artifacts involved
- structural dependencies
- data dependencies
- relevant inputs
- relevant outputs
- validations and constraints
- business rules
- preconditions
- postconditions
- invariants
- observable side effects
- external interactions
- ambiguities
- missing evidence
- confidence level of each major claim

## Evidence discipline

Discovery must distinguish clearly between:
- direct evidence from legacy artifacts
- inferred interpretation
- unresolved ambiguity

Every strong semantic claim should be traceable to at least one concrete source artifact or observable pattern in the codebase.

Do not present inference as fact.
Do not fill semantic gaps with plausible but unsupported assumptions.
If the evidence is insufficient, record the uncertainty explicitly.

## Capability-first discipline

In this project, discovery must be capability-oriented rather than file-oriented.

A COBOL file, module, paragraph, or routine is not automatically a business capability.
A capability may span multiple artifacts.
A single artifact may contain more than one candidate capability.

Therefore, full discovery must explicitly justify capability boundaries instead of assuming them from source-file boundaries alone.

## Specification-first discipline

The main outcome of discovery is structured understanding, not implementation.

Discovery must not jump directly from code inspection to:
- API endpoints
- route/controller/service structure
- orchestration modules
- adapter code
- public execution surfaces
- integration flow implementation

No implementation-facing artifact should be treated as the natural result of full discovery unless the structured semantics layer has already been produced and reviewed.

## Early-stage implementation restriction

During full discovery, avoid generating code artifacts such as:
- pipeline.js
- service.js
- controller.js
- route.js
- adapter.js
- API handlers
- orchestration modules

If the framework produces such files automatically, they must be treated as exploratory auxiliary artifacts only.
They must not define the official capability semantics, contract behavior, or modernization design of the project.

## Canonical data boundary discipline

When discovery reaches the point of identifying stable inputs and outputs, it may begin consolidating a canonical data boundary.

However, this boundary must still be expressed as a structured analytical artifact, not as an API contract yet.

At this stage, prioritize:
- canonical field names
- types and formats
- required vs optional fields
- semantic meaning of fields
- mapping between legacy structures and canonical representation

Do not yet decide:
- endpoint names
- HTTP methods
- status codes
- transport-layer conventions

## Review threshold before moving forward

Full discovery may be considered sufficiently mature only when:

- the candidate capability boundary is explicit
- the main source artifacts are identified
- the core rules and validations are documented
- the main inputs and outputs are understood
- uncertainties are explicitly logged
- the resulting semantics spec is coherent enough to support later derivation

If these conditions are not met, discovery must continue.
Do not advance prematurely to contract or adapter stages.

## Research-specific interpretation

In this project, discovery is not merely feature understanding.
It is a research-grade knowledge extraction activity that supports:
- reverse engineering of legacy behavior
- structured semantic reconstruction
- specification-driven modernization
- later derivation of API contracts and adaptation layers

Therefore, quality in discovery is measured by:
- evidential grounding
- semantic clarity
- traceability
- explicit handling of uncertainty
- usefulness for downstream specification artifacts

## Desired outcome

A successful full discovery stage should leave the project with:

- a clearly delimited candidate capability
- a documented body of legacy evidence
- a structured semantic description of that capability
- a stable enough canonical data boundary to support later contract derivation

It should not yet leave the project with implementation-led artifacts presented as authoritative design decisions.