# Capability Semantics Specification

## Purpose
<!-- The structured meaning of the capability: rules, conditions, invariants — grounded in stage 3 evidence. -->
{{PURPOSE}}

## Semantic Integrity Discipline
- Every semantic claim cites its evidence (`E-n`) or is labeled as inference with rationale.
- Rules are named and numbered (`R-n`); downstream artifacts reference rules, not prose.
- Ambiguities are disposed explicitly, never absorbed silently into clean rules.
- No interface, transport, or implementation vocabulary in this artifact.
- Rule documentation is not a reimplementation mandate: rules documented here support boundary derivation, contract derivation, and test design (including test data setup); at runtime they remain enforced by the legacy core through the wrapper (`rules/legacy-code-policy.md`).

## Section 1: Upstream Authority and Entry Condition

### 1.1 Upstream Authorities and Scope Inheritance
<!-- Legacy Evidence gate as entry condition; scope/selection chain restated briefly. -->
### 1.2 Inherited Constraints
<!-- Binding constraints restated (e.g., absence-of-identifier). -->

## Section 2: Operation Semantic Model
<!-- One subsection per operation. For each: purpose, inputs (meaning, not format), preconditions, behavior rules, postconditions, outputs, side effects — each element citing E-n or labeled inference. -->

### 2.1 {{OPERATION_1}}
### 2.2 {{OPERATION_2}}
### 2.x Operation Dispatch Model
<!-- How operations are selected/sequenced, if semantically relevant. -->

## Section 3: Named Semantic Rules
<!-- One subsection per rule R-n: statement, accepted outcome, rejected outcome, scope, evidence. -->

### 3.1 R-1: {{RULE_NAME}}
- **Statement**:
- **Accepted outcome (rule satisfied)**:
- **Rejected outcome (rule not satisfied)**:
- **Scope and expression**:
- **Evidence**: E-{{n}}

## Section 4: Data Semantics
<!-- The meaning of the capability's data: concept definitions, identity model, state scope, persistence semantics, initialization semantics. Meaning only — canonical types come in stage 5. -->

## Section 5: Ambiguity Disposition
<!-- For each open A-n that touches semantics: adopted interpretation, why safe at this stage, what to revisit if wrong. Update register status. -->

### 5.1 A-{{n}} — {{TITLE}}
- **Disposition**:
- **Adopted interpretation**:
- **Revisit trigger**:

## Section 6: Completeness Gate and Stage 5 Entry Condition

### 6.1 Completeness Conditions
- [ ] All operations semantically modeled with pre/postconditions and side effects
- [ ] All core rules named (`R-n`), with accepted/rejected outcomes and evidence
- [ ] Data semantics defined (concept, identity, state scope, persistence)
- [ ] All semantics-touching ambiguities disposed or explicitly blocking
- [ ] No interface/implementation vocabulary present

### 6.2 Semantic Integrity Condition
- [ ] Sampled claims trace back to `E-n` anchors or carry inference labels (traceability spot-check)

### 6.3 Stage 5 Entry Condition
**Stage 5 may begin** only when the conditions above hold and human review outcome is Approve.
