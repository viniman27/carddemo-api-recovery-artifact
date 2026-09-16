# Legacy Evidence Specification

## Purpose
<!-- What observable knowledge this artifact consolidates about the selected capability. -->
{{PURPOSE}}

## Evidence Quality Discipline
- Every claim is one of: **observed evidence** (with anchor), **inference** (labeled), or **ambiguity** (registered as `A-n`).
- Evidence anchors use `file:line-range` (e.g., `main.cob:112-131`). Reference-layer anchors are marked as such and carry less weight.
- No semantic normalization yet: this artifact records what the legacy does, not what it means for modernization.

## Section 1: Upstream Authority and Entry Condition

### 1.1 Upstream Authorities and Scope Inheritance
<!-- Pipeline Scope + Capability Selection gates as entry conditions. -->
### 1.2 Inherited Constraints
<!-- Restate binding constraints from upstream. -->

## Section 2: Source Program Evidence

### 2.1 Program Inventory and Capability-Relative Roles
<!-- Each source artifact and its role relative to the capability, with anchors. -->

| ID | Anchor | Observation |
|----|--------|-------------|
| E-1 | `{{file}}:{{lines}}` | |

### 2.2 Structural Characteristics
<!-- Dispatch structure, paragraph/PERFORM organization, data division layout relevant to the capability. -->
### 2.3 Primary Evidence Ownership
<!-- Which artifact is the primary owner of each behavior; avoids double-attribution later. -->

## Section 3: Operation Branch Evidence
<!-- One subsection per constituent operation. For each: trigger, inputs, control flow, outputs, effects — all anchored. -->

### 3.1 {{OPERATION_1}}
### 3.2 {{OPERATION_2}}

### 3.3 Relevant Behavior Inventory Matrix
<!--
Stage 3 creates the inventory only. Record candidate operations, rules and observable effects
with evidence or ambiguity labels. Do not assign endpoints, canonical types or final contract
conclusions here. The purpose is to give downstream reviewers a finite set of behaviors to
follow forward, while keeping interpretation and destination decisions in their proper stages.
-->

| Operation / rule / effect candidate | Evidence or ambiguity | Observed behavior summary | Why relevant | Downstream status |
|-------------------------------------|-----------------------|---------------------------|--------------|-------------------|
| | E-{{n}} / A-{{n}} | | operation / rule / state / ordering / failure / obligation | Inventory only; enrich in Stage 4 |

## Section 4: Data Access and State Evidence
<!-- Protocols for reading/writing state, field definitions (PIC clauses, copybooks), initialization, persistence characteristics. -->

### 4.1 Persistent Resources and Processing Sequence
<!-- When relevant: readers/writers per resource, ordering constraints, end-of-input, intermediate outputs and effects before errors, each anchored. Unknowns are A-n entries; absence of a transaction declaration is not evidence of atomicity. Source anchors use full corpus-relative paths. -->

| Resource / sequence edge | Read/write/order observation | Anchor | Unknowns |
|--------------------------|------------------------------|--------|----------|
| | | | |

## Section 5: Complexity Factor Documentation
<!-- The factors flagged at selection time, now documented with anchors: I/O coupling, state model, structural constraints, notable rules observed (not yet interpreted). -->

## Section 6: Completeness Gate and Stage 4 Entry Condition

### 6.1 Ambiguity Register
<!-- Full register state: new A-n entries plus status of inherited ones. -->

| ID | Description | Anchors | Candidate interpretations | Blocking? | Status |
|----|-------------|---------|---------------------------|-----------|--------|
| A-1 | | | | | Open |

### 6.2 Completeness Conditions
- [ ] All constituent operations evidenced with anchors
- [ ] Data access and state model evidenced
- [ ] Every claim classified as evidence / inference / ambiguity
- [ ] Complexity factors documented
- [ ] Relevant behavior inventory created without downstream endpoint/type/contract conclusions
- [ ] Ambiguity register current, blocking status assessed
- [ ] Human review outcome: Approve

### 6.3 Stage 4 Entry Condition
**Stage 4 may begin** only when the conditions above hold and no blocking ambiguity prevents semantic reconstruction of the core rule set.
