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
<!--
The state the capability operates on, described in technology-neutral terms. This section
exists because the boundary is not only about the shape of values crossing it: a consumer
cannot reason about two consecutive calls without knowing how long the state lives.

Stage 7's template requires that its adapter state model "realizes the canonical state
scope" — this section is what it realizes. Leaving it blank leaves that reference dangling
and, because the legacy usually supplies state lifecycle implicitly (process restart, region
recycle, job boundary), the omission is invisible until an implementation with different
provenance is put behind the same contract. See `rules/validation-principles.md`,
"Same-provenance instruments".

Note: `rules/ambiguity-management.md` already treats environmental behavior (persistence,
concurrency, initialization) as registrable ambiguity when unclear. This section is the
complementary obligation: when it IS clear, it must be decided and recorded, not left
implicit because it happens to work.
-->

- **State identity**: what distinguishes one instance of the state from another (or an explicit `D-n` that there is a single global instance).
- **Initialization**: the initial value and which legacy artifact is its authority (anchor).
- **Lifetime and scope**: how long the state persists and what bounds it (per call, per session, per process, global). State the legacy mechanism that produces this lifetime, even when implicit.
- **Reset semantics**: whether the state can be returned to its initial condition, by what means, and whether that means is part of the capability or external to it.
- **Isolation**: whether concurrent or successive consumers observe independent state.
- **Downstream consequences**: what stage 6 must expose (or explicitly not expose), and what stage 8 will therefore have to obtain from outside the contract.

For multiple resources, record the state fields above per resource, including persistent files, intermediate results and batch/job boundaries. A process restart does not reset persistent state. Map failure outcomes to the effects that may already exist and state repetition safety (safe / unsafe / unknown) with R-n/E-n or a blocking ambiguity.

If the capability is genuinely stateless, say so explicitly — an asserted absence is a decision; a blank section is not.

## Section 7: Reverse-Completeness Matrix — Boundary Enrichment
<!--
Start from the Stage 4 matrix. Enrich only the boundary treatment: canonical element,
state/resource treatment, D-n exclusion, A-n ambiguity or G-n gap. Do not invent API routes,
status codes or endpoint-per-behavior mappings.
-->

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
