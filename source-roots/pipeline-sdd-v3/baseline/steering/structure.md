# Project Structure

## Organization Philosophy

This project is structured around three distinct concerns that must remain conceptually separate:

1. **legacy artifacts** — what is being studied
2. **specification artifacts** — what is being produced by the research pipeline
3. **framework infrastructure** — what supports the execution of the pipeline

These three layers must never be conflated.

In particular:
- the COBOL source is evidence, not a design template
- generated implementation artifacts are not automatically authoritative research outputs
- framework metadata is not the same as project knowledge

The project is organized primarily by **pipeline stage and artifact role**, not by generic software-feature expansion.

## Structural Principle

Artifact progression in this project is stage-driven and specification-driven.

New artifacts should appear because the pipeline has advanced through a justified stage transition, not because the framework happened to generate more files.

The expected progression is:

legacy evidence -> capability semantics -> canonical data boundary -> API contract -> adapter behavior -> semantic validation

This progression should be visible both conceptually and structurally.

## Top-Level Structural Layers

### 1. Legacy Source Layer

**Location**: `cobol-accounting-system/`  
**Purpose**: Contains the public COBOL accounting system used as a controlled proof-of-concept legacy artifact.

This directory is the empirical source of evidence for the proof-of-concept stage.
Its contents should be treated primarily as observational material for reverse engineering, semantic reconstruction, and traceability.

The default stance toward this directory is:
- read-only for legacy evidence purposes
- modifiable only when explicitly working on a derived proof-of-concept implementation layer
- never treated as if its file structure were the target modernization architecture

**Typical contents**
- `*.cob` — COBOL source programs
- `README.md` — project description and contextual notes
- `TESTPLAN.md` — available behavior/testing guidance
- `node-accounting-app/` — auxiliary behavioral reference layer for proof-of-concept comparison or implementation support

### 2. Specification Layer

**Location**: `.sdd/specs/`  
**Purpose**: Contains the project’s specification artifacts, one spec directory per pipeline artifact or pipeline run.

This is the most important research workspace of the project.
It is where the structured outputs of the methodology are formalized and advanced through the SDD phases.

Specs in this project must follow the official artifact taxonomy rather than arbitrary feature naming.

### 3. Steering Layer

**Location**: `.sdd/steering/`  
**Purpose**: Contains project memory — stable methodological identity, project-level rules, structural logic, and stage-aware guidance.

Steering files are read as global memory and should preserve:
- project identity
- artifact taxonomy
- stage boundaries
- evidence discipline
- semantic sequencing
- research constraints

Steering is not a substitute for specs and should not become a duplicate of them.

### 4. Framework Infrastructure Layer

**Location**: `.sdd/settings/`  
**Purpose**: Contains templates, rules, and internal SDD framework support files.

This directory is framework support, not authoritative project knowledge.
It may shape behavior, but the methodological truth of the project resides in the steering files and the generated specification artifacts.

## Specification Directory Pattern

### Spec Root

**Location**: `.sdd/specs/[feature-name]/`

Each spec directory represents a **single specification artifact or a single stage-oriented pipeline unit** for one candidate capability.

In this project, spec directories should ideally reflect the artifact taxonomy explicitly.

### Preferred naming convention

Use:

`[artifact-type]-[capability-name]`

Examples:
- `pipeline-scope-account-balance`
- `capability-selection-account-balance`
- `legacy-evidence-account-balance`
- `capability-semantics-account-balance`
- `canonical-data-boundary-account-balance`
- `api-contract-account-balance`
- `adapter-behavior-account-balance`
- `semantic-validation-account-balance`

This naming convention helps preserve:
- stage awareness
- single responsibility per spec
- capability-centered organization
- traceable progression across artifacts

### Structural rule

A spec directory should not silently accumulate multiple conceptual roles.
If a spec begins to mix:
- semantics
- contract
- implementation
- validation
- task orchestration

then the structure is probably wrong and the artifact should be split.

## Standard Spec Files

Each spec directory may contain standard SDD files such as:

- `spec.json` — metadata and phase tracking
- `requirements.md`
- `design.md`
- `tasks.md`

These files must be interpreted according to the project’s research logic.

For example:
- `requirements.md` in an early-stage spec may still be document-first and analytical
- `design.md` must not automatically imply implementation design
- `tasks.md` must remain stage-aware and must not collapse semantic and implementation work

The presence of a standard filename does not override the intended methodological role of the spec.

## Artifact Taxonomy Memory

This project uses the following artifact taxonomy:

1. Pipeline Scope Spec
2. Capability Selection Spec
3. Legacy Evidence Spec
4. Capability Semantics Spec
5. Canonical Data Boundary Spec
6. API Contract Spec
7. Adapter Behavior Spec
8. Semantic Validation Spec

This taxonomy is the preferred backbone of `.sdd/specs/`.

The structure should reinforce this sequence rather than hide it.

## Artifact Lifecycle Pattern

Each spec directory represents a controlled unit of methodological progress.

A spec is expected to evolve through SDD phases, but that phase progression must remain aligned with the research stage the spec belongs to.

The `spec.json` `phase` field may track framework progression, such as:

`initialized` -> `requirements-generated` -> `requirements-approved` -> `design-generated` -> `design-approved` -> `tasks-generated` -> `tasks-approved` -> `ready-for-implementation`

However, in this project, readiness for implementation must be interpreted in a stage-aware way.

For example:
- a capability semantics spec may be "ready-for-implementation" only in the sense that it is ready to support the next specification stage, not necessarily code generation
- an API contract spec may be genuinely closer to implementation readiness
- an adapter behavior spec may more naturally support downstream implementation tasks

The framework phase model must therefore be interpreted through the project’s research pipeline.

## Structural Separation Rules

The following separations must remain explicit in the structure:

### Legacy vs Derived Artifacts
Legacy materials must remain distinguishable from:
- derived specifications
- generated code
- validation assets
- modernization outputs

### Evidence vs Semantics
Evidence summaries and semantic reconstructions should not be silently merged without justification.

### Semantics vs Contract
The canonical meaning of a capability must be stabilized before interface-level artifacts become authoritative.

### Contract vs Adapter
The interface contract and the operational adaptation layer should remain distinguishable.

### Research Artifacts vs Framework Metadata
Project reasoning must not be buried inside framework internals.

## Naming Conventions

- **Spec directories**: `[artifact-type]-[capability]` in kebab-case
- **COBOL programs**: preserve original repository naming and conventions
- **Derived Node.js or auxiliary implementation modules**: use project-appropriate naming, but do not let these become authoritative over spec artifacts
- **Spec artifact files**: use the framework’s standard filenames consistently, while preserving the intended role of each artifact

Naming must support readability, stage clarity, and traceability.

## Code and Artifact Organization Principles

- Claims made in any downstream artifact must be traceable to specific legacy evidence or reviewed upstream specifications.
- Steering files must remain concise enough to be read as project memory in full.
- `.sdd/specs/` should grow in a controlled way, one justified artifact at a time.
- Early-stage specs should remain primarily document-first.
- Implementation-facing code must not become the main carrier of semantic truth before the corresponding specification artifacts are stabilized.
- Proof-of-concept implementation artifacts are acceptable, but they must remain clearly subordinate to the specification chain.

## Proof-of-Concept Structure Reminder

The public COBOL accounting repository is a proof-of-concept artifact, not the final institutional case.

Its structural role is to:
- provide a controlled legacy input
- support early evidence extraction
- allow experimentation with the specification pipeline
- expose methodological issues before transfer to the institutional context

This distinction should remain visible in how the project is structured and discussed.

## Desired Structural Outcome

A good project structure in this workspace should make it easy to see:

- what is legacy evidence
- what is steering memory
- what is specification output
- what is framework support
- what stage each artifact belongs to
- how artifacts connect across the modernization pipeline

If the structure makes the project look like a generic feature implementation tree, it is too weak.
If it makes the methodological pipeline visible and preserves artifact boundaries, it is working.

---
Document structural patterns and naming rules, not file inventories.