# EARS Format

Use EARS-style statements only when they improve the clarity, precision, and testability of behavioral requirements or expected observable behavior.

In this project, EARS is a controlled writing aid.
It is not the primary semantic model of the pipeline, and it must not replace evidence gathering, capability semantics reconstruction, or canonical data boundary definition.

## Primary role of EARS in this project

The purpose of EARS in this project is to help express specific behavioral expectations in a clear and reviewable form, especially when downstream artifacts need concise requirement-like statements.

EARS is useful when the project needs to express:
- externally visible behavior
- conditional behavior
- exceptional behavior
- validation expectations
- adapter response expectations
- semantic validation scenarios

EARS should make downstream artifacts more explicit, not more superficial.

## Where EARS is appropriate

In this project, EARS is most useful for:

- API behavior statements
- adapter behavior expectations
- semantic validation scenarios
- specific error-handling behavior
- externally observable contract rules
- conditional operational expectations derived from prior semantics

These are contexts in which concise, structured behavioral phrasing can improve clarity and comparability.

## Where EARS is not the right tool

Do not force EARS for:

- raw legacy evidence
- source artifact description
- dependency inventory
- ambiguity logging
- capability boundary notes
- broad capability semantics documents
- traceability tables
- code evidence summaries
- preliminary discovery notes

In particular, do not use EARS as a substitute for:
- evidential grounding
- semantic reconstruction
- canonical data modeling
- interface derivation logic

## Relationship to the semantic model

The primary semantic model of this project is the structured capability semantics artifact.

That artifact remains the authoritative representation of:
- business purpose
- rules
- preconditions
- postconditions
- invariants
- side effects
- ambiguities
- evidence-backed interpretation

EARS may be used later to restate selected parts of that semantic model in a more operational, requirement-like style.
It must not be used to invent semantics that have not already been grounded in evidence or stabilized in the semantics layer.

## Stage-appropriate use

EARS is generally inappropriate during early discovery stages.

### During light discovery
EARS should almost never be used.
At this point, the process is still identifying evidence, scope, and ambiguity.
Requirement-like phrasing may create false confidence too early.

### During full discovery
EARS may occasionally be used for very localized behavioral clarification, but it must remain secondary to structured semantics.
It must not define the capability.

### During contract, adapter, and validation stages
EARS becomes more useful, because the project is now expressing:
- precise external behavior
- boundary conditions
- integration expectations
- validation criteria

Therefore, the preferred use of EARS is later in the pipeline, not earlier.

## Acceptable usage pattern

EARS should be used only after the project can already answer:
- what capability is being described
- what evidence supports that behavior
- what the canonical inputs and outputs are
- what stage of the pipeline the artifact belongs to

If those conditions are not met, EARS is premature.

## Examples of acceptable usage

Examples of acceptable EARS-style statements include:

- When a valid account identifier is provided, the system shall return the current balance.
- If the debit amount exceeds the available balance, the system shall reject the operation.
- While the legacy dependency is unavailable, the adapter shall return a controlled integration error.
- When a credit amount is valid, the adapter shall update the exposed balance consistently with the observed legacy behavior.
- If the input amount is missing for a debit request, the API shall return a validation error.

These are acceptable because they describe concrete behavior at the contract, adapter, or validation level.

## Unacceptable usage patterns

Do not use EARS to:

- describe raw code structure
- summarize COBOL paragraphs
- replace evidence with polished requirements
- hide ambiguity behind normative phrasing
- define capability scope prematurely
- derive API semantics directly from guessed behavior
- imply correctness that has not yet been validated

For example, an EARS sentence is unacceptable if it makes a claim that the current evidence does not yet support.

## Review guidance for EARS-based content

Whenever EARS is used, review must check:

- Is the statement grounded in prior semantics?
- Is it traceable to evidence or stable upstream artifacts?
- Is it expressing externally visible behavior rather than implementation detail?
- Is it appropriate for the current stage?
- Does it improve clarity, or merely make the artifact sound more formal?

If the statement sounds precise but is weakly grounded, it should be rejected or downgraded.

## Desired outcome

EARS should help the project express selected behavioral requirements more clearly, especially in contract, adapter, and validation artifacts.

It should never become the main language of the project.
Its role is supportive, local, and stage-dependent.

In summary:
- use EARS where behavioral precision helps
- avoid EARS where semantic reconstruction is still incomplete
- treat EARS as an aid to articulation, not as a replacement for the specification-driven core of the research