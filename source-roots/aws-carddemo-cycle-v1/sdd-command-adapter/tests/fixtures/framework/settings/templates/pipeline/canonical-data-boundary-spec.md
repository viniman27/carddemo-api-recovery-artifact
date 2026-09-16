# Canonical Data Boundary Specification

## Purpose
<!-- The technology-neutral, stable data meanings of the capability, derived from stage 4 semantics. -->
{{PURPOSE}}

## Boundary Integrity Discipline
- Canonical elements derive from semantic rules (`R-n`) and data semantics, never from transport convenience.
- No endpoint names, HTTP methods, status codes, or serialization decisions in this artifact.
- Where semantics underdetermines the boundary, record a design decision (`D-n`) with rationale and consequences.
- The boundary covers **values and state**. Declaring what data crosses is not sufficient: the lifetime, scope and resettability of the state behind the boundary are boundary properties, and stage 6 cannot expose what this stage did not license (see Section 6).

## Section 1: Upstream Authority and Entry Condition

### 1.1 Upstream Authorities and Scope Inheritance
<!-- Capability Semantics gate as entry condition. -->
### 1.2 Inherited Constraints
<!-- Binding constraints restated. -->

## Section 2: Design Decisions at the Boundary
<!-- One subsection per D-n decision the boundary must make (e.g., identifier model). -->

### 2.1 D-{{n}}: {{DECISION_TITLE}}
- **Decision**:
- **Rationale**:
- **Downstream consequences for this run**:
- **Institutional applicability note**:

## Section 3: Canonical Types
<!-- One subsection per canonical type: definition, constraints, validity rules, semantic source. -->

### 3.1 {{TYPE_NAME}}
- **Definition**:
- **Constraints / validity**:
- **Derived from**: R-{{n}} / Section 4 of stage 4

## Section 4: Canonical Operation Boundaries
<!-- One subsection per operation: canonical inputs (name, type, required/optional, meaning), canonical outputs, outcome variants, guard conditions — mapped to legacy structures. -->

### 4.1 {{OPERATION_1}}

| Canonical element | Type | Req? | Meaning | Legacy mapping | Source |
|-------------------|------|------|---------|----------------|--------|
| | | | | `{{file}}:{{lines}}` | R-{{n}} |

## Section 5: Outcome Models
<!-- Canonical modeling of multi-variant outcomes (e.g., accepted/rejected), with guard conditions and the semantic rule each variant expresses. Include a note for how stage 6 must map variants. -->

## Section 6: Canonical State Scope
<!-- State identity, initialization, lifetime and scope, reset semantics, isolation, downstream consequences. -->

## Section 7: Reverse-Completeness Matrix — Boundary Enrichment

| Operation / rule / effect | Evidence | Semantic representation | Boundary treatment | Contract destination / exclusion / gap |
|---------------------------|----------|--------------------------|--------------------|----------------------------------------|
| | E-{{n}} / A-{{n}} | R-{{n}} / inference / ambiguity | canonical element / internal state / D-{{n}} exclusion / A-{{n}} / G-{{n}} | pending Stage 6 |

## Section 8: Completeness Gate and Stage 6 Entry Condition

### 8.1 Completeness Conditions
- [ ] All canonical types defined with constraints and semantic sources
- [ ] All operations bounded with canonical inputs/outputs and legacy mappings
- [ ] Outcome variants modeled with guard conditions
- [ ] All boundary design decisions recorded as `D-n` with institutional notes
- [ ] No transport-layer vocabulary present
- [ ] Canonical state scope declared (identity, initialization, lifetime, reset, isolation) — or statelessness asserted explicitly
- [ ] Reverse-completeness matrix enriched with boundary treatment, exclusions, ambiguities or gaps
- [ ] Any state capability that stage 8 will need but the contract will not expose is named here as a consequence, not discovered later

### 8.2 Semantic Integrity Condition
- [ ] Every canonical element traces to a semantic rule or a labeled design decision

### 8.3 Stage 6 Entry Condition
**Stage 6 may begin** only when the conditions above hold and human review outcome is Approve.
