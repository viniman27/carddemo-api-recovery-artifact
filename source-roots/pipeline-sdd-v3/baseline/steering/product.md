# Product Overview

This project is a master's research proof of concept on COBOL legacy modernization using a specification-driven pipeline.

It is not a conventional product development workflow.
The central artifact of interest is not a software product in the usual sense, but a research methodology: a structured, AI-assisted process for recovering actionable knowledge from legacy COBOL systems and progressively transforming that knowledge into integration-oriented artifacts.

More specifically, the project investigates how legacy behavior can be reconstructed, structured, and reused to support incremental API-oriented modernization without collapsing evidence gathering, semantic interpretation, interface design, and implementation into a single step.

## Research Objective

The main objective of the project is to evaluate the usefulness of an incremental, specification-supported approach for COBOL migration, in which selected legacy capabilities are exposed through derived API contracts and exercised by derived test suites — providing test-based behavioral confidence for a later reimplementation, without claiming formal semantic preservation.

The project is centered on the following progression:

COBOL legacy -> AI-assisted extraction -> structured specification -> API contract -> adapter behavior -> semantic validation

This progression defines the logic of the research and should be preserved across specs, reviews, task generation, and implementation.

The intermediate result the research targets is deliberate: exposing the functionalities of a COBOL system through an API and deriving automated tests for that API, as a controlled step that supports a migration process — not the migration itself.

The research questions that operationalize this objective — tied to the pipeline stages and treated as a primarily qualitative study — are maintained in `steering/research-questions.md`.

### Migration framing

The strategic value of the pipeline is that it prepares a safer migration path: once capabilities are exposed via contracts and covered by derived test suites, a future reimplementation (e.g., in Java or another modern platform) exposed through the same API can be checked against the same tests. Code regeneration is outside the current scope, but the artifacts are designed to make that step cheaper and safer later.

## Core Capabilities of the Methodology

- **Legacy understanding**  
  Identify candidate business capabilities from COBOL source artifacts, associated data structures, and relevant dependencies.

- **Evidence-based extraction**  
  Recover observable evidence from the legacy system while preserving the distinction between direct evidence, inferred interpretation, and unresolved ambiguity.

- **Structured semantic reconstruction**  
  Consolidate extracted knowledge into stable intermediate artifacts, especially capability semantics and canonical data boundaries, before deriving interfaces.

- **Specification-driven derivation**  
  Produce a sequence of ordered specification artifacts that progressively move from legacy understanding toward modern integration artifacts.

- **API-oriented modernization**  
  Derive interface contracts from stabilized semantic and data artifacts rather than directly from raw legacy source code.

- **Adapter-oriented operationalization**  
  Define how derived contracts can be connected back to legacy behavior through an adaptation layer.

- **Semantic validation**  
  Assess whether the resulting artifacts and behaviors remain aligned with the behavior observed or inferred from the original legacy system.

## Explicit Non-Goals

The following are deliberately outside the objective of this research (advisor alignment, June 2026):

- **Optimal microservice decomposition.** Producing a high-quality decomposition of the monolith is a separate research line. This project only exposes selected functionalities through services; the quality of the decomposition is not a claim and not a target.
- **Formal verification or formal semantic-preservation guarantees.** Claims stay at the level of test-based behavioral confidence. Terms such as "verified" and "semantic preservation" imply guarantees this project does not provide and must be avoided in claims (see `settings/rules/validation-principles.md`).
- **Rewriting or restructuring the COBOL core.** The legacy code is not modified; modernization adds a wrapper layer on top of it (see `settings/rules/legacy-code-policy.md`).
- **Inter-service orchestration.** The exposed services do not need to communicate with each other; each endpoint exposes a legacy functionality directly.
- **Big-bang API generation.** Capabilities are selected incrementally; the pipeline never targets the whole system at once.

## Target Use Cases

This project currently supports two complementary use cases.

### 1. Public proof-of-concept application
Apply the pipeline to the public COBOL accounting repository (`cobol-accounting-system/`) in order to:
- exercise the specification workflow end to end
- reveal methodological weaknesses early
- refine artifact boundaries and stage transitions
- reduce uncertainty before moving to institutional legacy material

### 2. Preparation for institutional application
Use the proof of concept to prepare for a later application of the same methodology to a real institutional COBOL legacy context, where the stakes, ambiguity, and validation requirements are expected to be higher.

Expected characteristics of the institutional phase (to be planned, not improvised):
- real scale: multiple programs, copybooks, and multiple capabilities
- qualitative evaluation with domain specialists as a primary evidence source
- inter-rater agreement when multiple evaluators assess artifacts
- explicit cost measurement (e.g., token consumption per stage)
- selective automation of repetitive stages, possibly including multi-agent execution, without weakening human gates

The public repository is therefore not the final empirical target of the research study, but an important controlled stage in the research process.

## Value Proposition

The value of the methodology lies in enforcing a disciplined transformation path.

Instead of jumping directly from legacy source code to modern API implementation, the process imposes ordered intermediate artifacts and explicit stage boundaries:

- scope before capability selection
- evidence before interpretation
- semantics before interface
- interface before adapter behavior
- validation before strong claims of adherence

This reduces the risk of premature implementation, unsupported semantic assumptions, and weakly justified interface design.

The methodology is therefore intended to improve:
- traceability
- analytical clarity
- reviewability
- reproducibility of the proof of concept
- defensibility of the resulting artifacts in a research study context

## Intended Outcome

A successful outcome for this project is not merely "generated code."

A successful outcome is a coherent, traceable, and reviewable chain of artifacts showing that:
- a candidate legacy capability was identified
- its evidence was consolidated
- its semantics were structured
- its data boundary was stabilized
- an API contract was derived
- adapter behavior was specified or implemented without modifying the legacy core
- semantic validation was defined and supported by observable behavior
- the derived test suite exists as a transferable artifact, reusable against a future reimplementation exposed through the same API

## Scope Reminder

This steering file captures the stable identity, purpose, and value logic of the research project.

It is not intended to enumerate feature lists, implementation details, or individual generated artifacts.