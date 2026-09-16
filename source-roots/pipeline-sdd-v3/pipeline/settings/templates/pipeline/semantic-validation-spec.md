# Semantic Validation Specification

<!-- This is the validation PLAN. Results go in validation-report.md. Do not merge them. -->

## Purpose
<!-- What adherence question this validation answers, for which surface, against which oracles. -->
{{PURPOSE}}

## Validation Integrity Discipline
- Every scenario (`V-n`) derives from an identifiable upstream element (contract clause, canonical constraint, `R-n`, or `E-n`). Intuition-only scenarios are gaps, not scenarios.
- Each scenario names its oracle and the question it answers: contract conformance, legacy characterization or agreed observable obligations. There is no universal strength ordering. Record conflicts and limitations; reference-layer-only expectations are explicitly labeled.
- Scenarios touching open ambiguities are excluded or exploratory — never conformance-bearing.
- Claim vocabulary stays at test level: behavioral consistency / test-based confidence, never "verified", "semantic preservation", or "equivalence" (`rules/validation-principles.md`).
- Scenarios are phrased against the contract surface, not adapter internals, so the suite remains transferable to a future reimplementation behind the same API.
- Every scenario is typed as **conformance** (asserts what the contract promises; transfers as an acceptance criterion) or **legacy characterization** (records observed legacy behavior, including anomalies; does **not** transfer as an acceptance criterion — against a new backend it acts as a change detector). Leaving the two unmarked makes a legitimate correction read as a regression.
- Any capability the suite requires but the contract does not expose — state reset, seeding, clock control, fixture loading — is declared in the execution protocol. An undeclared dependency passes silently while the backend shares provenance with the legacy and fails as soon as it does not.

## Section 1: Upstream Authority and Entry Condition

### 1.1 Upstream Authorities
<!-- Adapter Behavior gate as entry condition; contract and semantics as scenario sources. -->
### 1.2 Validation Scope Statement
<!-- What is being validated (surface, environment) and what is explicitly out of validation scope. -->

## Section 2: Oracle Inventory
<!-- Available oracles for this run, their strength, and limitations. -->

| Oracle | Claim / question | Expected-outcome origin | Tool origin / data exposure | Limitations |
|--------|------------------|-------------------------|-----------------------------|-------------|
| | | | | |

## Section 3: Scenario Groups
<!-- Group scenarios by operation or rule. For each scenario: derivation anchor, setup, stimulus, expected outcome, oracle. -->

### Group A — {{OPERATION_OR_RULE}} [{{upstream §}}]

| ID | Type | Derived from | Setup | Stimulus | Expected outcome | Oracle |
|----|------|--------------|-------|----------|------------------|--------|
| V-1 | conformance / characterization | §{{ref}} / R-{{n}} | | | | |

## Section 4: Coverage Statement
<!-- Which contract operations and semantic rules the scenario set exercises; which it does not, and why. Unvalidated behavior is scope, not omission. -->

| Element | Covered by | Not covered — reason |
|---------|-----------|----------------------|
| R-{{n}} | V-{{...}} | |

## Section 5: Execution Protocol
<!-- Environment, ordering/isolation requirements, how observations will be recorded, what constitutes a divergence. Include any test data setup needed so rules are actually exercised (environment work, per rules/legacy-code-policy.md). -->

### 5.1 Harness Dependencies Not Declared in the Contract
<!--
List every capability the suite needs that the contract does not expose, and how it is
obtained against this backend. Typical entries: state reset, data seeding, clock control,
session establishment, process lifecycle.

For each: what is needed, how the current backend supplies it, and what a backend of
different provenance would have to supply instead. If the list is empty, say so — an
asserted empty list is a check; an absent section is not.

Anything appearing here is, by definition, something stage 5 either declared as an
out-of-boundary consequence or failed to declare. If it is the latter, escalate upstream.
-->

| Capability needed | How this backend supplies it | Declared in contract? | Upstream owner |
|-------------------|------------------------------|-----------------------|----------------|
| | | yes / no | stage {{n}} §{{ref}} |

### 5.2 Oracle Convention Pre-Modeling
<!--
Arithmetic and representation conventions carried by the semantic rules (`R-n`) must be
modeled in the oracles BEFORE execution: truncation vs rounding, signedness, field width
ceilings, decimal scale, string padding. An oracle built on the wrong convention produces
a constant low-amplitude divergence that masks the real anomalies underneath it.
State here which conventions were modeled and from which `R-n` each comes.
-->

### 5.3 State, Failure and Observation Matrix
<!-- Trace stage-5 state through stage-6 mapping and stage-7 mechanism. Per scenario: pre-state/reset evidence, in-sequence persistence, final-state observations, allowed normalizations, partial-failure/repetition obligations. Missing observation means inconclusive. Separate HTTP acceptance, COBOL reachability, effects and oracle verdict. Do not introduce a known preparation answer as an independent oracle. -->

| Scenario | State/setup source | Contract or external provision | Observations required | Verdict basis |
|----------|--------------------|-------------------------------|-----------------------|---------------|
| | | | | |

## Section 6: Exploratory Expansion (optional)
<!-- Mechanisms beyond designed scenarios: property-based testing for input masses, stateful API fuzzing over the OpenAPI contract (tool selected and justified per run; declare actual dependency support, budgets and checkers), selectively designed manual tests. Results are exploratory until formalized as anchored V-n scenarios; fuzzing findings on the legacy itself become defect reports per legacy-code-policy. -->

<!--
Declare the campaign BUDGET (operation count, seed) and the COUNTING UNIT (requests that
triggered an anomaly? findings within a fixed output set?) before running. Raw counts
without both are not interpretable and are never comparable across capabilities — different
budgets and different units produce ratios that mean nothing. See
`rules/validation-principles.md`, "Exploratory findings are budgeted observations".

Record the provenance of the harness itself. A harness written by the same pipeline that
produced the contract and the adapter verifies self-consistency, not fidelity.
-->

## Completeness Gate (plan) and Execution Entry Condition
- [ ] All scenarios upstream-anchored with named oracles
- [ ] Every scenario typed as conformance or legacy characterization
- [ ] No conformance-bearing scenario depends on an open ambiguity
- [ ] Coverage statement complete and honest
- [ ] Harness dependencies not exposed by the contract listed in §5.1 (or the list asserted empty), with undeclared ones escalated upstream
- [ ] Oracle conventions from `R-n` modeled before execution (§5.2)
- [ ] Exploratory budget, seed and counting unit declared before running
- [ ] State/setup requirements mapped end-to-end (§5.3), partial failure and repetition addressed or explicitly N/A
- [ ] Tool independence is not confused with independent expected outcomes
- [ ] Execution protocol reproducible
- [ ] Human review outcome: Approve

**Execution may begin** only when this gate is passed. Results are recorded in `validation-report.md`.
