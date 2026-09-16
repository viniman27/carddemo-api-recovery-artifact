# Design Review

Design review is the quality-control stage responsible for verifying whether a produced artifact is coherent, stage-appropriate, evidentially grounded, and correctly aligned with upstream artifacts in the project's specification-driven modernization pipeline.

In this project, review is not a cosmetic check. It is a methodological checkpoint.
Its purpose is to prevent premature design decisions, weakly supported semantics, broken traceability, and implementation drift.

## Primary purpose

Design review must determine whether the current artifact is fit to serve as an authoritative output for its stage in the pipeline.

The review must check, at minimum:

- internal coherence
- alignment with upstream artifacts
- stage appropriateness
- evidential grounding
- traceability
- usefulness for downstream derivation
- suitability for research study-level explanation and defense

## Pipeline context

Artifacts in this project are expected to evolve through the following progression:

legacy evidence -> capability semantics -> canonical data boundary -> API contract -> adapter behavior -> semantic validation

A review must always judge the current artifact in light of its place in that progression.

An artifact should not be approved merely because it is plausible or implementable.
It must be appropriate for the stage it belongs to.

## Core review questions

The following questions must guide design review.

### Capability and scope
- Is the capability boundary explicit and understandable?
- Is the selected capability justified rather than assumed?
- Does the artifact respect capability-first decomposition rather than file-first decomposition?
- Are scope assumptions clearly stated?

### Evidence grounding
- Are the artifact's claims grounded in legacy evidence?
- Is there a visible distinction between observed evidence, inferred interpretation, and unresolved ambiguity?
- Are major claims traceable to source artifacts or stable patterns in the legacy material?
- Does the artifact avoid unsupported certainty?

### Semantic quality
- Are business rules clearly stated where relevant?
- Are business rules separated from implementation assumptions?
- Does the semantics layer include preconditions, postconditions, and invariants where appropriate?
- Are observable side effects explicitly represented if relevant?
- Are uncertainties and missing evidence recorded explicitly?

### Cross-artifact consistency
- Is the canonical data boundary consistent with the capability semantics?
- Is the API contract traceable to the semantics and data boundary?
- Does the adapter behavior preserve the intended contract semantics?
- Is semantic validation defined in terms of observed or reference behavior rather than vague correctness claims?

### Stage discipline
- Does this artifact belong to the current stage of the pipeline?
- Has the process skipped any required upstream artifact?
- Has the artifact introduced downstream decisions prematurely?
- Is implementation appearing before semantics or contract stabilization?

### Research suitability
- Is the artifact analyzable?
- Is it reviewable and comparable?
- Is it sufficiently explicit to be discussed and defended in the research study?
- Does it improve the methodological clarity of the project rather than obscure it?

## Review discipline

Design review must reject or return for refinement any artifact that does one or more of the following:

- skips the structured semantics layer
- collapses multiple conceptual layers without justification
- mixes business semantics with implementation tasks
- presents inference as evidence
- infers unsupported behavior from weak evidence
- introduces API decisions without a canonical data boundary
- introduces adapter behavior without a stable contract
- treats prematurely generated code as authoritative design
- hides ambiguity instead of documenting it
- breaks traceability to upstream artifacts
- is operationally plausible but analytically opaque

## Review outcomes

A design review should produce exactly one of the following outcomes:

### 1. Approve
Use this outcome only when the artifact is sufficiently coherent, grounded, traceable, and stage-appropriate to support downstream work.

Approval means:
- the artifact may be used as an authoritative input for the next stage
- its main claims are acceptable within the current evidence limits
- any remaining ambiguity is non-blocking and explicitly documented

### 2. Request refinement
Use this outcome when the artifact has value but still requires revision before it can serve as an authoritative stage output.

Typical causes:
- unclear capability boundary
- incomplete traceability
- weak distinction between evidence and inference
- missing rules or side effects
- unstable data boundary
- insufficient explanation of uncertainty

Refinement should identify what must be improved, not merely that the artifact is weak.

### 3. Return to evidence gathering
Use this outcome when the artifact is fundamentally under-supported by available legacy evidence.

Typical causes:
- major semantic claims cannot be grounded
- the capability candidate is unstable or ambiguous
- critical dependencies are still unknown
- the artifact relies on speculative interpretation
- downstream derivation would be unsafe or misleading

This outcome means the process should move back to discovery or evidence consolidation before continuing.

## Review severity rule

The stricter the artifact's role in downstream derivation, the stricter the review should be.

In particular:
- capability semantics must be reviewed rigorously before any contract derivation
- canonical data boundary must be reviewed rigorously before any API design
- API contract must be reviewed rigorously before adapter behavior
- semantic validation must be reviewed rigorously before any strong claim of adherence

Do not relax review merely because the artifact is convenient for implementation.

## Treatment of premature code artifacts

If the framework generates implementation-oriented files earlier than expected, review must explicitly determine:

- whether the file is merely auxiliary
- whether it has introduced semantic or contract assumptions too early
- whether it should be ignored, refined, or demoted to exploratory status

Implementation-oriented files generated before their proper stage must not be treated as authoritative simply because they exist.

## Reviewer mindset for this project

Review must behave as if the artifact will later be used both:
- as an input to the next pipeline stage
- and as evidence in a research argument

Therefore, the reviewer must ask:
- Would I trust this artifact to guide the next transformation?
- Would I trust this artifact to be explained and defended in the research study?
- Would I be able to trace its claims back to legacy evidence?

If the answer is no, the artifact is not ready.

## Desired outcome

A successful design review should ensure that the approved artifact is:

- internally coherent
- externally aligned with upstream artifacts
- grounded in evidence
- explicit about ambiguity
- appropriate for its stage
- safe to use downstream
- defensible in the context of the master's research

The purpose of review is not to reward polished artifacts.
It is to protect the integrity of the pipeline.