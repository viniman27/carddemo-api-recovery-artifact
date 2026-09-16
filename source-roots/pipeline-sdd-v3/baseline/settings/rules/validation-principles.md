# Validation Principles

Semantic validation is the stage that determines whether modernized behavior remains aligned with the behavior observed or inferred from the legacy system.

In this project, validation is not "running the test suite."
It is the evidential basis for any claim of semantic adherence made in the research study.

## Claim vocabulary discipline

Validation in this project stays at the test level. Terminology must not promise more than tests can deliver (advisor alignment, June 2026: research communities with formal-methods rigor read "verification" and "semantic preservation" as mathematical guarantees, and tests do not provide them).

**Avoid in claims and artifact titles:**
- "verified" / "verifiable" (as a property of the migration)
- "semantic preservation" / "preserves semantics"
- "equivalence" / "semantically equivalent"
- "proves" / "guarantees"

**Prefer:**
- "behavioral consistency with observed legacy behavior, for the validated scenarios"
- "test-based behavioral confidence"
- "conformance to the derived contract, for the executed scenario set"
- "no divergence observed within the validated scope"

The stage name "semantic validation" remains as taxonomy vocabulary, but every claim it produces must be scoped and test-level.

## Primary purpose

Semantic validation must answer, explicitly and with observable support:

1. What behavior was the modernized surface expected to preserve?
2. Where did that expectation come from (contract, semantics, evidence)?
3. What was actually observed?
4. Where does observed behavior diverge from expected behavior?
5. What conformance claim do the results actually support?

## Validation plan before validation execution

Validation work is split into two artifacts that must not be merged:

- **Semantic Validation Spec** — the plan: scenarios, expected outcomes, oracles, and their upstream derivation
- **Validation Report** — the results: observed outcomes, divergences, and the conformance assessment

A report without a prior plan invites post-hoc rationalization.
A plan without a report supports no adherence claim.

## Scenario derivation discipline

Every validation scenario (`V-n`) must be derived from an identifiable upstream element:

- an API contract clause,
- a canonical boundary constraint,
- a semantic rule (`R-n`),
- or directly observed legacy behavior (`E-n`).

Scenarios invented from general intuition about "what an accounting system should do" are not valid scenarios in this project.
If a behavior seems worth testing but has no upstream anchor, that is a gap in the upstream artifacts — record it as a gap, do not silently test it.

## Oracle discipline

Each scenario must state what plays the role of oracle, chosen from:

- observed legacy execution (strongest)
- documented legacy evidence with anchors
- the reviewed API contract (for surface-level conformance)
- the reviewed capability semantics (for rule-level conformance)

The Node.js reference layer may support execution and comparison, but it is never the semantic authority.
When the only available oracle is the reference layer, the scenario must be labeled accordingly and its evidential weight downgraded.

## Divergence discipline

Divergences are results, not failures to hide.

Every observed divergence must be recorded in a divergence registry with:

- identifier (`DIV-n`)
- scenario(s) affected
- expected vs observed behavior
- most plausible origin (evidence gap, semantic drift, contract decision, adapter defect, legacy idiosyncrasy)
- disposition: fix (in the modernization layer), report as legacy defect, accept with justification, or escalate to upstream revision

A divergence whose origin is an upstream artifact must trigger upstream review — it must not be patched only at the adapter level.

A divergence whose origin is a defect in the legacy code follows `legacy-code-policy.md`: it is registered and reported, never fixed in the legacy source by the pipeline (proof-of-concept PR proposals are an explicit, documented exception).

## Conformance claim limits

Claims must be scoped to what the scenarios actually exercised.

- "The adapter conforms to the contract for the validated scenarios" is acceptable when supported.
- "The modernized capability is semantically equivalent to the legacy system" is almost never supportable and must not be claimed.
- Partial conformance with explicit exclusions is a legitimate and honest research result.

Every conformance statement must reference the scenario set, the oracle types used, and the known divergences.

## Test suite as transferable artifact

The derived test suite is not only a validation instrument for the current adapter; it is a research output designed for reuse.

- The suite must be executable against any implementation exposed through the same API contract, so a future reimplementation (e.g., in Java) can be checked against the same behavioral expectations.
- Scenarios should therefore be phrased against the contract surface, not against adapter internals.
- **Transferability is a claim to be tested, not a property obtained by intent.** Phase 1 pointed a derived suite at a second implementation and found it discriminated the injected divergence with no false positives — and also that three of eight scenarios failed for a reason unrelated to behavior: the suite required a state reset that the contract did not expose and that the legacy adapter had supplied implicitly by restarting a process. Phrasing scenarios against the contract is necessary and not sufficient; the suite must also not depend on capabilities the contract omits (see "Same-provenance instruments").
- Expansion mechanisms may strengthen the suite beyond designed scenarios: property-based testing for large input masses, stateful API fuzzing to explore the surface (and potentially expose long-standing legacy defects), and selectively designed manual tests. The preferred fuzzer is **RESTler**, which consumes the stage-6 OpenAPI contract directly and explores stateful request sequences (see `steering/tech.md`). Results from exploratory mechanisms are labeled exploratory until scenarios are formalized with upstream anchors; fuzzing findings on the legacy behavior itself are routed to the defect-reporting policy (`legacy-code-policy.md`).
- Exploring the limits of what test suites can and cannot establish is part of the research contribution of stages 7–8.

## Same-provenance instruments

An instrument produced by the same pipeline run as the thing it checks can establish self-consistency, never independent fidelity.

This applies to the property-based harness, the fuzzing driver and any reference implementation written alongside the contract. When harness, contract and adapter share provenance, a result of "zero contract violations" means: no response left the envelope the contract declares. It does not mean the contract describes the legacy correctly — the same process wrote both.

Rules:

- state the provenance of every instrument in the validation report
- report same-provenance results as **conformance regression**, useful and worth having, and never as attestation
- an independent attestation requires an instrument of distinct provenance — an external validator, a third-party fuzzer consuming the contract, or an implementation written by someone without access to the pipeline artifacts

The corollary matters more than the caveat: **a defect that only manifests under a change of provenance is undetectable by any amount of artifact review.** Every artifact can be internally coherent and mutually consistent while the suite silently depends on something the contract never declared, because the dependency is satisfied by accident as long as the backend is the one the pipeline was built against. This is why §5.1 of the validation plan exists, and why listing undeclared harness dependencies is a gate condition rather than good practice.

## Scenario types: conformance versus characterization

A derived suite contains two kinds of scenario, and conflating them corrupts its reuse value.

- **Conformance scenarios** assert what the contract promises. They transfer literally and serve as acceptance criteria for any correct implementation behind the same contract.
- **Characterization scenarios** record observed legacy behavior, including anomalies the modernization has deliberately chosen not to correct. They do **not** transfer as acceptance criteria: a corrected reimplementation will fail them by design. Against a new backend they function as change detectors.

Both must be marked as such in the plan and in the report. An unmarked characterization scenario makes a legitimate correction read as a regression, which is the most expensive kind of false signal a migration suite can produce.

## Exploratory findings are budgeted observations

A finding count without its budget and its counting unit is not a result.

- **Budget**: operation count and seed, declared before the campaign runs
- **Counting unit**: what exactly is being counted — requests that triggered an anomaly, or findings within a fixed set of outputs? These are different units and produce incomparable numbers
- **Class**: anomalies of different root-cause classes are not interchangeable, even within one capability

Consequences:

- raw counts are never comparable across capabilities; normalize by budget and compare class to class
- when heterogeneous counts are aggregated, say explicitly that the total measures root-cause coverage and not severity or relative incidence
- a large count under a large budget and a small count under a small budget may describe the same incidence rate

## Oracle conventions are modeled before execution

Arithmetic and representation conventions carried by the semantic rules must be built into the oracles before the first run: truncation versus rounding, signedness, field-width ceilings, decimal scale, padding.

An oracle built on the wrong convention produces a constant low-amplitude divergence across every scenario — and that noise floor is exactly high enough to hide the real anomaly underneath it. Record which conventions were modeled and which `R-n` each derives from, so a reviewer can tell a modeled convention from an unexamined assumption.

## Root-cause isolation outside the legacy program

An anomaly observed through the adapter has at least three candidate origins: the legacy logic, the runtime or compiler underneath it, and the adapter itself. Reasoning about which one from inside the full stack is unreliable, because all three are present in every observation.

The technique is to reproduce the anomaly in the smallest possible program that contains only the suspected mechanism, outside the legacy source, and vary one dimension at a time.

Phase 1 used this on a cent-loss anomaly: a six-line COBOL program declaring one field and reading it, run against two field widths, showed that `ACCEPT` reads at most as many characters as the field has digit positions — so a field whose declared ceiling needs nine characters, read through a channel that takes eight, cannot reach roughly four fifths of its own declared domain. That converted 83 observations from "anomaly of unclear origin" to "conflict between declared domain and input channel, internal to the legacy."

Discipline:

- isolate before attributing; an attribution argued only from full-stack observation is a hypothesis
- vary one dimension and report the comparison, not the conclusion alone
- separate what is **legacy** (the conflict between declared domain and available channel) from what is **implementation-defined** (the specific shape of the loss, which may differ under another compiler); the first transfers, the second requires re-testing
- an isolation experiment is cheap, reproducible and belongs with the artifacts

## Coverage honesty

The validation report must state explicitly:

- which contract operations were exercised and which were not
- which semantic rules were exercised and which were not
- which behaviors could not be validated and why (missing oracle, ambiguity, environment limits)

Unvalidated behavior is a scope statement, not a silent omission.

## Research-specific interpretation

In the research study, validation results carry the burden of the project's central argument.

That argument was revised by phase 1 and the revision must not be quietly undone. It was *not* established that the specification-driven pipeline achieves higher semantic fidelity than a direct code→contract jump: a pre-registered baseline scored 14 of 15 rubric items against the pipeline's 15, or 14–14 once the one biased item is discounted, for capabilities small enough to fit in a single reading of the model. What phase 1 does support is **auditability of the derivation** — that each contract element can be walked back to the evidence that founds it and the decision that shaped it, and that when a defect appears it can be attributed to a named artifact.

Note also that the earlier phrasing of this section used "preserves semantics", which the claim vocabulary discipline above forbids. Framework text is subject to the same discipline as artifacts.

Therefore:
- negative and partial results are reportable results
- the divergence registry is analytical material, not an embarrassment
- overclaiming adherence would damage the credibility of the entire pipeline argument
- claims of superiority over unstructured alternatives require a comparison arm that was actually run; absent one, claim auditability and traceability, which do not depend on comparison

## Desired outcome

A successful validation stage should produce:

- a scenario set fully traceable to upstream artifacts
- explicit oracles per scenario
- a complete divergence registry with dispositions
- a conformance assessment whose strength matches the evidence
- an honest statement of what remains unvalidated

If validation produces only green checkmarks and strong claims, it is probably failing.
If it produces a scoped, traceable, divergence-aware adherence argument, it is working.
