# API Contract Specification

## Purpose
<!-- The modern interface surface derived from the canonical boundary. -->
{{PURPOSE}}

## Contract Integrity Discipline
- Every contract element derives from a canonical element or a recorded design decision (`D-n`); nothing enters the surface from implementation convenience.
- Outcome-variant mappings must follow the stage 5 mapping notes.
- Error strategy decisions are design decisions: recorded, justified, and traceable.
- EARS phrasing is permitted here (see `rules/ears-format.md`) when it sharpens behavioral statements.
- The contract should be represented (or representable) in OpenAPI, the project's preferred contract format for review and test/fuzzing tooling.

## Section 1: Upstream Authority and Entry Condition

### 1.1 Upstream Authority and Scope Inheritance
<!-- Canonical Data Boundary gate as entry condition. -->
### 1.2 Inherited Model Constraints
<!-- E.g., singleton/identity model inherited from D-n decisions. -->

## Section 2: API Operation Surface

### 2.1 Operation Inventory
<!-- The full surface, one line per operation, each mapped to a canonical operation. -->
### 2.2 Method and Route Structure
<!-- Route/method decisions with rationale; record non-obvious choices as D-n. -->
### 2.3 Scope Constraint
<!-- What the surface deliberately does not expose. -->

## Section 3: Shared Type Schemas
<!-- API representation of each canonical type, with constraints preserved. Flag any representation compromise as D-n. -->

### 3.1 {{TYPE_NAME}}

## Section 4: Operation API Contracts
<!-- One subsection per operation: request schema, response schema per outcome variant, validation behavior, error behavior. EARS statements welcome. -->

### 4.1 {{METHOD}} {{ROUTE}} — {{OPERATION}}
- **Request**:
- **Responses**:
- **Validation**:
- **Traceability**: canonical element(s), R-{{n}}, D-{{n}}

## Section 5: Error Handling Strategy

### 5.1 Response Categories
### 5.2 Category Table
<!-- Category | condition | status | body shape | upstream source -->
### 5.3 Rationale for Non-Obvious Status Decisions
<!-- E.g., domain rejection vs transport error status choices, recorded as D-n. -->

### 5.4 State and Recovery Contract
<!-- Carry every stage-5 state requirement, including external/unsupported ones. Do not invent a reset endpoint. Document consumer-visible lifetime, ordering, effects on rejection/failure and retry restrictions; preserve ambiguity rather than promising rollback/idempotency. -->

| State requirement / resource | Stage-5 source | Contract clause or external/unsupported | Consumer consequence |
|------------------------------|----------------|-----------------------------------------|----------------------|
| | | | |

## Section 6: Traceability Matrix
<!-- Non-obvious mappings only (see rules/traceability.md). -->

| Contract element | Canonical element | Rule | Decision |
|------------------|-------------------|------|----------|
| | | R-{{n}} | D-{{n}} |

## Section 7: Reverse-Completeness Matrix — Contract Destination
<!--
Start from the Stage 5 matrix. Enrich only the destination column: contract clause,
explicit exclusion with rationale, external/unsupported requirement, or gap. Do not conclude
that every behavior needs its own endpoint; state why the chosen surface does or does not expose it.
-->

| Operation / rule / effect | Evidence | Semantic representation | Boundary treatment | Contract destination / justified exclusion / gap |
|---------------------------|----------|--------------------------|--------------------|--------------------------------------------------|
| | E-{{n}} / A-{{n}} | R-{{n}} / inference / ambiguity | canonical element / state / D-{{n}} / G-{{n}} | clause / external or unsupported / excluded with rationale / G-{{n}} |

## Completeness Gate and Stage 7 Entry Condition
- [ ] All canonical operations have contracts; no extra surface without `D-n`
- [ ] All canonical types represented with constraints preserved or compromises recorded
- [ ] Outcome-variant mapping constraints satisfied
- [ ] Error strategy complete with rationale for non-obvious decisions
- [ ] Each canonical state/reset requirement mapped to a clause or declared external/unsupported
- [ ] Failure effects and repetition constraints derived, not invented
- [ ] Reverse-completeness matrix gives each relevant upstream behavior a contract clause, justified exclusion, external/unsupported status, or gap
- [ ] Traceability matrix covers all decision-bearing mappings
- [ ] Recorded review includes risk-oriented samples for rule reading, claimed absence in dependencies, failure with persisted effects, and omitted obligation — or justified N/A with inspected scope
- [ ] Each sampled item has passage/objection/conclusion and resulting contract/exclusion/`G-n` disposition where applicable
- [ ] Review record states that the sample does not prove completeness
- [ ] No blocking gap or unjustified omission remains in the behavior-to-contract matrix
- [ ] Human review outcome: Approve

**Stage 7 entry condition**: this gate passed and recorded in `spec.json`.
