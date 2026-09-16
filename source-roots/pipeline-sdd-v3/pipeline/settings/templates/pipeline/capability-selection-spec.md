# Capability Selection Specification

## Purpose
<!-- Which capability was selected for this run and what this artifact establishes. -->
{{PURPOSE}}

## Selection Integrity Discipline
- The selected capability must be justified, not assumed; file boundaries do not define capability boundaries.
- Selection precedes evidence work: claims here remain preliminary and low-commitment.

## Section 1: Upstream Authority and Scope Reference

### 1.1 Upstream Authority
<!-- Name the Pipeline Scope Spec and its passed gate as entry condition. -->
### 1.2 Inherited Constraints
<!-- Restate scope-level constraints that bind this selection. -->

## Section 2: Capability Identification

### 2.1 Selected Capability
<!-- Name and one-paragraph characterization. -->
### 2.2 Constituent Operations
<!-- The operations that compose the capability, at hypothesis level. -->
### 2.3 Operational Boundary
<!-- What is inside/outside the capability, with preliminary anchors where visible. -->
### 2.4 Single-Focus Status
<!-- Confirm one capability per run, or justify explicitly if not. -->

## Section 3: Selection Rationale

### 3.1 Selection Criteria
<!-- Why this capability: evidential accessibility, business significance, pipeline-exercising value, feasibility. -->
### 3.2 Constraints That Shaped the Selection
### 3.3 Proof-of-Concept vs. Institutional Context
<!-- Institutional applicability note for the selection logic itself. -->

## Section 4: Downstream Evidence Scope

### 4.1 Primary Evidence Sources
<!-- Which source artifacts stage 3 should examine first. -->
### 4.2 Evidence Collection Target
<!-- What stage 3 must establish for the semantics stage to be possible. -->
### 4.3 Complexity Factors and Stage 3 Entry Condition
<!-- Known complexity (I/O coupling, state model, dispatch structure) that evidence work must document. -->

## Ambiguity Register (initial)
<!-- Register early ambiguities as A-n entries: description, exposing observation, potential impact, blocking status. -->

| ID | Description | Exposed by | Impact | Blocking? |
|----|-------------|-----------|--------|-----------|
| A-1 | | | | |

## Completeness Gate and Stage 3 Entry Condition
- [ ] Capability named, characterized, and single-focused (or deviation justified)
- [ ] Operational boundary stated with preliminary anchors
- [ ] Selection rationale explicit against stated criteria
- [ ] Evidence scope and collection target defined for stage 3
- [ ] Initial ambiguities registered
- [ ] Human review outcome: Approve

**Stage 3 entry condition**: this gate passed and recorded in `spec.json`.
