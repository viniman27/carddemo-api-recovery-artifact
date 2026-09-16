# Design Discovery Light

Use this mode for early-stage exploration when the objective is to form a cautious, preliminary, and evidence-aware understanding of a possible COBOL business capability.

In this project, light discovery is not intended to design solutions, define contracts, or propose implementation structure. Its sole purpose is to decide whether there is enough evidence to justify deeper analysis.

## Primary purpose

Light discovery should answer a limited set of early questions:

- Is there a plausible candidate capability here?
- Which COBOL artifacts appear relevant to it?
- What probable inputs and outputs can be observed at a preliminary level?
- What visible effects or state changes seem associated with it?
- What are the main ambiguities or uncertainties?
- Is the material mature enough to move into full discovery?

This mode is intentionally exploratory and low-commitment.

## Expected outputs

In this project, light discovery should produce only lightweight, document-first artifacts such as:

- capability selection notes
- initial legacy evidence summary
- preliminary scope hypothesis
- rough capability boundary hypothesis
- ambiguity notes
- evidence collection to-do items

These outputs should remain small, provisional, and easy to revise.

## Acceptable artifact style

Outputs from light discovery may take the form of:

- short markdown notes
- structured bullet summaries
- preliminary evidence tables
- compact yaml/json summaries
- annotated lists of relevant source artifacts

At this stage, outputs are exploratory aids, not authoritative specifications.

## Discovery discipline

Light discovery must stay close to observable material.
It should favor:
- artifact identification
- boundary hypothesis
- visible input/output clues
- dependency hints
- uncertainty logging

It should avoid:
- semantically strong conclusions
- architectural interpretation beyond available evidence
- interface decisions
- implementation planning

## Analytical dimensions allowed in light mode

The following dimensions may be explored, but only at a preliminary level:

- candidate business purpose
- relevant COBOL files or routines
- apparent dependencies
- probable inputs
- probable outputs
- likely validations
- likely observable effects
- major ambiguity sources
- initial confidence level

These dimensions should be framed as hypotheses unless directly evidenced.

## Evidence and confidence rules

Light discovery must explicitly distinguish:

- observed evidence
- plausible hypothesis
- unresolved ambiguity

Do not elevate early hypotheses into stable semantics.
Do not state business rules as facts unless supported by visible evidence.
Do not claim capability boundaries as final during this stage.

When confidence is low, say so directly.

## Capability-first guidance

In this project, light discovery should begin capability-oriented thinking, but only at a tentative level.

A source file, paragraph, or routine may suggest a capability, but must not be assumed to define one completely.
If multiple interpretations are possible, record them instead of collapsing them prematurely.

## Strict non-goals of light discovery

Do not produce, in light mode:

- final API contracts
- implementation design
- adapter behavior
- orchestration design
- route/controller/service structure
- task breakdown
- final semantic specification
- strong semantic claims without evidence
- code artifacts that imply stabilized architecture or interface decisions

In particular, avoid generating implementation-facing files such as:
- pipeline.js
- service.js
- controller.js
- route.js
- adapter.js

If such files are generated automatically by the framework, they must be treated as premature auxiliary artifacts and not as valid outputs of light discovery.

## Relationship to later stages

Light discovery is successful only if it helps determine what should happen next.

The preferred outcomes are:

- refine capability boundary
- gather more evidence
- isolate relevant artifacts
- identify blocking ambiguities
- decide whether full discovery is justified
- defer the candidate if evidence is too weak

Light discovery should not attempt to complete the work of full discovery.

## Research-specific interpretation

In this project, light discovery is a pre-analysis stage for a master's research pipeline on COBOL modernization.
It serves to reduce uncertainty before committing to a structured semantic reconstruction effort.

Its value lies in:
- preventing premature design decisions
- avoiding implementation drift
- exposing ambiguity early
- selecting the right candidate capability for deeper reverse-engineering

## Desired outcome

A successful light discovery pass should leave the project with:

- a plausible candidate capability
- a bounded set of relevant source artifacts
- a preliminary evidence summary
- a clear list of uncertainties
- a justified decision on whether to proceed to full discovery

It should not leave the project with implementation-oriented artifacts, finalized semantics, or integration design decisions.