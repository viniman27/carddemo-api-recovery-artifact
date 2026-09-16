# Adapter Behavior Specification

## Purpose
<!-- How the contract surface connects to legacy-faithful behavior, without redefining contract semantics. -->
{{PURPOSE}}

## Adapter Integrity Discipline
- The adapter realizes the contract; it never reinterprets it. Any needed deviation is an upstream revision, not an adapter workaround.
- Legacy-facing behavior must stay faithful to stage 3–4 artifacts; convenience simplifications are design decisions (`D-n`) at minimum.
- The legacy source is read-only: the adapter must not require modifying legacy code (`rules/legacy-code-policy.md`). Environment preparation (data population, bindings, harness) is allowed.
- Business rules inside the legacy core are exercised through the wrapper, not reimplemented; the adapter does not silently compensate for legacy defects.
- Implementation technology choices become legitimate at this stage, but remain subordinate to the contract.

## Section 1: Upstream Authority and Entry Condition

### 1.1 Upstream Authority and Scope Inheritance
<!-- API Contract gate as entry condition; semantics/boundary chain restated briefly. -->
### 1.2 Inherited Constraints and Decisions
<!-- D-n decisions that bind adapter design. -->

## Section 2: Adaptation Model

### 2.1 Adaptation Strategy
<!-- Default strategy: wrap the unmodified legacy core (e.g., via runtime binding) so legacy rules keep executing where they live. Reimplementing behavior in the modern layer is exceptional and requires an explicit D-n justification. State the strategy and, if not pure wrapping, justify the deviation. -->
### 2.2 Semantic Authority Statement
<!-- Explicit statement of which artifacts govern behavior when implementation questions arise. -->

## Section 3: Operation Behavior Mappings
<!-- One subsection per contract operation: triggering contract clause, internal behavior steps, state interactions, outcome production per variant, rule enforcement points (R-n). -->

### 3.1 {{METHOD}} {{ROUTE}} — {{OPERATION}}
- **Contract clause(s)**:
- **Behavior**:
- **State interaction**:
- **Rule enforcement**: R-{{n}} at {{point}}
- **Outcome mapping**:

## Section 4: State and Session Model
<!-- How adapter state realizes the canonical state scope: initialization, lifetime, isolation, persistence position. -->

### 4.1 State Realization and Setup Boundary

| Resource / requirement | Contract clause or external setup | Concrete mechanism | Observable reset/isolation check |
|------------------------|-----------------------------------|--------------------|---------------------------------|
| | | | |

<!-- Distinguish in-sequence persistence from isolation between tests. Restarting a server is not a reset of a persistent datastore. Support remains outside corpus. -->

## Section 5: Error and Edge Behavior
<!-- Adapter-level failures vs domain rejections vs validation errors; mapping to the contract's error strategy; behavior when legacy/reference dependencies are unavailable. -->

### 5.1 Partial Execution and Process Lifecycle
<!-- Specify output acceptance versus process completion, timeout/crash behavior, state already written, and retry policy inherited from stages 4–6. No silent compensation or business-rule replacement. If coverage is requested, require separate evidence that counters flush on normal exit; a response alone is insufficient. -->

## Section 6: Implementation Notes (non-authoritative)
<!-- Technology and structure notes for implementation tasks. These do not carry semantic authority. -->

## Completeness Gate and Stage 8 Entry Condition
- [ ] Every contract operation has a behavior mapping with rule enforcement points
- [ ] State model realizes the canonical state scope
- [ ] Error/edge behavior fully mapped to the contract's error strategy
- [ ] No contract reinterpretation; deviations escalated upstream or recorded as `D-n`
- [ ] Behavior mappings support scenario derivation for stage 8
- [ ] Human review outcome: Approve

**Stage 8 entry condition**: this gate passed and recorded in `spec.json`.
