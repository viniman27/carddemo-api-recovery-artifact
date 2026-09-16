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

## Section 6: Traceability Matrix
<!-- Non-obvious mappings only (see rules/traceability.md). -->

| Contract element | Canonical element | Rule | Decision |
|------------------|-------------------|------|----------|
| | | R-{{n}} | D-{{n}} |

## Completeness Gate and Stage 7 Entry Condition
- [ ] All canonical operations have contracts; no extra surface without `D-n`
- [ ] All canonical types represented with constraints preserved or compromises recorded
- [ ] Outcome-variant mapping constraints satisfied
- [ ] Error strategy complete with rationale for non-obvious decisions
- [ ] Traceability matrix covers all decision-bearing mappings
- [ ] Human review outcome: Approve

**Stage 7 entry condition**: this gate passed and recorded in `spec.json`.
