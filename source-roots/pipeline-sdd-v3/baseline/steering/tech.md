# Technology Stack

## Technology Philosophy

This project has three distinct technical layers that must remain conceptually separate:

1. **legacy technology** — the source of evidence and behavior under study
2. **proof-of-concept modernization technology** — the controlled environment used to instantiate and test parts of the pipeline
3. **specification infrastructure** — the tools and artifacts used to drive the research workflow

The purpose of this separation is methodological clarity.

The legacy system is not the modernization target architecture.
The proof-of-concept implementation is not automatically the semantic authority.
The specification pipeline is the primary mechanism that connects evidence, semantics, interface derivation, adaptation, and validation.

## Core Technical Position

This project is specification-driven and parser-agnostic by default.

That means:
- the research pipeline must work even when a dedicated parser is not yet part of the execution flow
- if parsing or static-analysis support is introduced later, it should strengthen evidence extraction, not replace the specification chain
- LLMs are used as assistants for extraction and structuring, not as authoritative semantic or validation oracles

No API layer is assumed at the outset.
The API contract is a downstream artifact to be derived from stabilized semantics and canonical data boundaries.

## Legacy Immutability Position

The legacy COBOL code is not modified by the modernization process.

- Modernization adds a wrapper layer on top of the unmodified legacy core; in the proof of concept this is realized through a Node.js-to-COBOL binding that executes the legacy code directly.
- Business rules implemented inside the legacy core are exercised through the wrapper, not reimplemented in the modern layer.
- Defects found in the legacy code are research findings to be documented and reported, not silently fixed (see `settings/rules/legacy-code-policy.md` for the full policy, including the proof-of-concept vs institutional distinction).
- Whether a given legacy system can be wrapped without modification is itself a research question; obstacles to wrapping must be recorded as findings.

## Legacy Artifact Layer

### Source Language
- **Language**: COBOL
- **Target context**: legacy-system understanding and capability extraction
- **Current proof-of-concept artifact**: a public COBOL accounting repository used as a controlled legacy input

### Structural Characteristics
The proof-of-concept COBOL system is treated as a small but useful legacy artifact that exposes:
- multiple cooperating source files
- procedural logic
- data-oriented program structure
- observable operations over a shared domain concept

### Execution Characteristics
- interactive console-oriented execution
- single-process behavior in the public proof of concept
- simplified persistence/state model relative to enterprise COBOL environments

This proof-of-concept legacy artifact is useful because it allows the methodology to be exercised in a controlled environment before being applied to institutional material with more complex dependencies.

### Evidence Role
The legacy layer serves as:
- the source of code evidence
- the basis for capability identification
- the basis for semantic reconstruction
- the source against which downstream artifacts must remain traceable

It must not be treated as a direct blueprint for modern interface design.

## Proof-of-Concept Modernization Layer

### Current Language and Runtime
- **Language**: JavaScript
- **Runtime**: Node.js

### Current Role
The Node.js layer is currently part of the proof-of-concept environment.
Its role is not to define the modernization architecture in advance, but to provide:
- an execution-friendly environment for controlled experimentation
- a candidate adaptation or comparison surface
- a practical environment for testing and validation-related work

### Important Constraint
The Node.js implementation or reference behavior must not become the primary semantic authority of the project.

The authoritative chain remains:

legacy evidence -> capability semantics -> canonical data boundary -> API contract -> adapter behavior -> semantic validation

If Node.js artifacts are used in validation or prototyping, they remain subordinate to that chain.

### Current Technical Characteristics
- no required web framework at the start
- possible use of simple runtime interfaces for proof-of-concept behavior
- implementation choices should remain lightweight until the contract layer is mature
- adapter-facing or API-facing code should only emerge after the corresponding specification artifacts exist

## Specification Infrastructure Layer

### Workflow Framework
- **Framework**: Spec-Driven Development (SDD)
- **Workspace structure**: `.sdd/`
- **Main directories**:
  - `.sdd/steering/`
  - `.sdd/specs/`
  - `.sdd/settings/`

### AI Tooling
- **Primary tooling**: assistant Code / assistant Sonnet in slash-command workflow
- **Role of AI**:
  - assist evidence extraction
  - support semantic organization
  - support derivation of downstream artifacts
  - assist review, gap identification, and staged tasking

AI tooling must not be treated as a substitute for evidence, semantic review, or explicit stage control.

### Specification Artifacts
The project uses an ordered family of specification artifacts, including:
- Pipeline Scope
- Capability Selection
- Legacy Evidence
- Capability Semantics
- Canonical Data Boundary
- API Contract
- Adapter Behavior
- Semantic Validation

These artifacts are the main carriers of project knowledge across the pipeline.

### Language Policy
Artifact content is written in the language configured by `spec.json.language`, but conceptual reasoning and internal workflow guidance may remain English-first if that improves consistency.

## Parsing and Static-Analysis Position

At the current stage, the project does not require a parser as a mandatory prerequisite for the methodology to function.

However, the project is compatible with parser-assisted or static-analysis-assisted evolution later.

If introduced, parser or static-analysis support should primarily strengthen:

- structural evidence extraction
- dependency mapping
- artifact segmentation
- identification of likely inputs and outputs
- traceability back to source artifacts

Parser support should not collapse the distinction between:
- structural evidence
- semantic interpretation
- specification artifacts

## API and Contract Position

No API implementation technology should be treated as fixed before the contract stage.

This project explicitly avoids premature commitment to:
- web framework choice
- route/controller structure
- transport-layer conventions
- public execution surface

The correct order is:
1. reconstruct semantics
2. stabilize canonical data boundary
3. derive API contract
4. define adapter behavior
5. only then allow implementation-oriented decisions

This rule is more important than framework convenience.

Once the contract stage is reached, **OpenAPI is the preferred representation format** for the derived contract, because it is reviewable, standard, and directly consumable by test-generation and fuzzing tooling.

## Validation Technology Position

Validation in this project may draw on multiple technical mechanisms depending on stage maturity and available artifacts, including:

- existing tests from the proof-of-concept environment
- controlled reference executions
- comparison of observed input/output behavior
- review of generated semantic artifacts
- integration tests for derived contracts or adapters

Validation is not treated as merely "the test suite."
It is a broader technical activity aimed at assessing adherence to observed or reference behavior.

### Test-suite-centered mechanisms

The derived test suite is the central validation artifact and a transferable output: it is designed to be re-run against a future reimplementation exposed through the same API.

Candidate expansion mechanisms discussed for strengthening test-based confidence:
- LLM-derived automated tests against the contract (baseline mechanism)
- property-based testing to generate large input masses
- stateful API fuzzing to explore the surface beyond designed scenarios — potentially exposing long-standing defects in the legacy code itself
- selectively designed manual tests, as a deliberate complement

**Preferred fuzzing tool: RESTler** (`github.com/microsoft/restler-fuzzer`), Microsoft Research's stateful REST API fuzzer — the "Microsoft fuzzing" work the advisor referenced. It is a strong fit because it consumes an OpenAPI specification directly (reinforcing the choice of OpenAPI at stage 6), infers request dependencies to reach deeper stateful behavior, and flags HTTP 500s plus checker-based issues (resource leaks, hierarchy violations) with replayable logs. In this project RESTler is an exploratory validation mechanism at stage 8: findings on the exposed surface strengthen behavioral confidence, and any latent legacy defect it surfaces becomes a defect report under `settings/rules/legacy-code-policy.md`, never a silent fix. RESTler complements, and does not replace, the upstream-anchored scenario suite; its results are exploratory until formalized as anchored scenarios.

These mechanisms explore the limits of test-based validation; none of them upgrades the claim level from behavioral confidence to formal guarantee.

### Cost observability

Future pipeline runs should collect execution cost metrics — at minimum, token consumption per stage — so the research study can discuss the economic viability of the approach. Cost measurement was a recognized limitation of the first proof-of-concept run.

## Key Technical Decisions

### 1. Specification-first, implementation-later
Technology choices must not overtake artifact maturity.

### 2. Document-first early stages
Early stages should primarily produce structured documents, not implementation architecture.

### 3. Parser-agnostic, parser-compatible
The methodology should function without requiring a parser, while remaining open to parser-assisted strengthening later.

### 4. Contract derivation before API implementation
The API must be derived from stabilized semantic artifacts, not inferred casually from the proof-of-concept runtime.

### 5. Controlled proof-of-concept implementation
Implementation artifacts generated in the public proof-of-concept stage are acceptable, but they are exploratory unless grounded in the corresponding specification stages.

### 6. Validation grounded in behavior
Technical validation should remain tied to observed or reference behavior, not merely to generated code structure.

## Development Environment

### Required Tools
- Node.js and npm
- assistant Code / SDD workflow tooling
- optional COBOL toolchain support when direct execution of the legacy artifact is needed
- optional test tooling for proof-of-concept execution and validation

### Common Working Context
The most common working environments in this project are:
- the public proof-of-concept repository
- the `.sdd/` specification workspace
- steering-guided generation and review sessions

### Practical Command Context
Command usage may evolve during the project and should not be over-specified in steering unless the commands reflect a stable methodological pattern.

Only stable, recurring commands with clear methodological value should be preserved as project memory.

## Scope Reminder

This file documents stable technical context and stage-aware technology decisions.

It should not become:
- an exhaustive dependency inventory
- a full implementation manual
- a substitute for spec artifacts
- a prematurely fixed architecture document