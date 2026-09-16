# Gap Analysis

Gap analysis is the control mechanism used to determine what is still missing, unstable, unsupported, or insufficiently specified before the pipeline can safely advance to the next stage.

In this project, gap analysis is not a generic backlog exercise.
It is a specification-driven diagnostic activity whose purpose is to protect the integrity of the modernization pipeline by making incompleteness explicit.

## Primary purpose

Gap analysis must identify the distance between:

1. what is evidenced in the legacy artifacts
2. what is currently represented in the structured specs
3. what is still required to support a justified downstream artifact

Depending on the stage, the downstream artifact may be:
- a capability semantics spec
- a canonical data boundary spec
- an API contract spec
- an adapter behavior spec
- a semantic validation artifact

The role of gap analysis is to prevent the process from moving forward based on plausible but under-supported assumptions.

## Core principle

A gap is not merely "something missing."
A gap is any discrepancy between:
- available evidence
- current structured representation
- required maturity for the next stage

This includes missing information, unstable interpretation, unresolved ambiguity, broken traceability, and premature downstream decisions.

## Typical gap categories

Typical gaps in this project include:

- missing source evidence
- unclear capability boundary
- ambiguous business rule
- incomplete input/output model
- unknown dependency
- unstable canonical field mapping
- unspecified side effect
- missing precondition or postcondition
- unsupported invariant
- missing contract rationale
- insufficient validation basis
- broken traceability between stages
- premature implementation assumption
- premature API or adapter decision

These categories should be treated as analytical diagnostics, not cosmetic notes.

## Stage-specific use

Gap analysis should be used especially between the following transitions:

- legacy evidence -> capability semantics
- capability semantics -> canonical data boundary
- canonical data boundary -> API contract
- API contract -> adapter behavior
- adapter behavior -> semantic validation

It may also be used within a stage when an artifact appears internally inconsistent or insufficiently grounded.

## What gap analysis must check

For each stage transition, gap analysis must ask:

### Evidence adequacy
- Is there enough source evidence to support the current semantic claims?
- Are important claims still weakly grounded?
- Are some claims based mostly on inference rather than evidence?

### Semantic maturity
- Is the capability boundary stable enough?
- Are the core business rules explicit enough?
- Are preconditions, postconditions, and side effects sufficiently represented?

### Data maturity
- Are inputs and outputs explicit enough to support canonical modeling?
- Are field meanings stable?
- Are there missing validations or unresolved data assumptions?

### Contract readiness
- Is the semantic layer mature enough to justify interface design?
- Are error conditions sufficiently understood?
- Is the canonical data boundary stable enough to define request/response structures?

### Adapter readiness
- Is the contract precise enough to guide adapter behavior?
- Are the legacy interactions sufficiently understood?
- Are downstream transformations traceable to upstream semantics?

### Validation readiness
- Are there enough observable behaviors, reference scenarios, or testable expectations?
- Is there a credible basis for judging adherence?
- Are key ambiguities still unresolved in ways that block meaningful validation?

## Gap severity classification

Always classify gaps as one of the following:

### Blocking
A gap is blocking when it prevents the current artifact from serving as a trustworthy input for the next stage.

Examples:
- no stable capability boundary
- unknown core dependency
- incomplete or contradictory semantic rule
- missing input/output meaning required for canonical boundary
- API contract being derived without mature semantics
- validation attempted without observable behavior criteria

Blocking gaps must be addressed before the pipeline advances.

### Important but non-blocking
A gap is important but non-blocking when the artifact can still advance provisionally, provided that the limitation is explicit and the downstream use remains cautious.

Examples:
- secondary side effect still unclear
- non-critical ambiguity in edge-case behavior
- optional field mapping still provisional
- validation scenario incomplete but not central

These gaps must remain visible and should be tracked for later refinement.

### Cosmetic
A gap is cosmetic only when it does not materially affect semantics, traceability, derivation quality, or validation credibility.

Examples:
- wording improvements
- naming consistency adjustments
- formatting issues
- non-substantive redundancy cleanup

Do not downgrade substantive gaps to cosmetic merely because they are inconvenient.

## Output discipline

Gap analysis outputs must be explicit, actionable, and stage-aware.

Each identified gap should ideally include:
- gap identifier or short label
- affected artifact(s)
- description of the missing or unstable element
- severity classification
- reason why the gap matters
- what evidence or clarification would reduce or resolve it
- whether the next stage is blocked or allowed with caution

Gap analysis should produce clarity, not just a list of complaints.

## Relationship to review

Gap analysis and design review are related but not identical.

- Design review judges whether an artifact is acceptable as a stage output.
- Gap analysis identifies what is still missing or unstable relative to the next stage.

In practice:
- design review asks "Is this artifact acceptable now?"
- gap analysis asks "What still prevents safe progression?"

An artifact may pass review with non-blocking gaps.
An artifact with blocking gaps should not progress, even if it is well written.

## Important discipline

Do not invent missing information in order to close gaps.

Missing evidence must remain explicit.
Weakly supported semantics must remain qualified.
Ambiguity must not be hidden behind polished wording.
Implementation convenience must not be used to justify unresolved semantic assumptions.

The correct response to an unresolved gap is one of the following:
- gather more evidence
- refine the current spec
- narrow the scope
- postpone the downstream decision
- escalate to human review

It is not acceptable to silently guess.

## Research-specific interpretation

In this project, gap analysis supports research rigor by making partial knowledge visible.
Its role is especially important because the pipeline moves from legacy code to increasingly abstract and modernized artifacts.

Without explicit gap analysis, the project risks:
- overclaiming semantic understanding
- deriving contracts from unstable assumptions
- implementing adapters against incomplete semantics
- presenting weakly grounded artifacts as reliable results

Gap analysis therefore contributes directly to the defensibility of the research study.

## Desired outcome

A successful gap analysis should make it clear:

- what is already strong enough to preserve
- what remains unstable or incomplete
- what is required before the next stage
- whether the process may proceed, proceed with caution, or must stop and return to earlier work

Its purpose is not to accelerate the pipeline artificially.
Its purpose is to ensure that the pipeline only advances when the current level of knowledge justifies it.