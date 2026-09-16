# Ambiguity Management

Ambiguity is not a failure of the process; hidden ambiguity is.

This rule defines the lifecycle of ambiguities so that uncertainty remains explicit, tracked, and correctly propagated across the pipeline instead of being silently absorbed by downstream artifacts.

## What counts as an ambiguity

An ambiguity (`A-n`) is any point where the available legacy evidence admits more than one reasonable interpretation, or where required information is absent, including:

- behavior that depends on unobserved runtime conditions
- fields or values whose business meaning is not evidenced
- control flow whose intent is unclear from source alone
- discrepancies between legacy source and reference-layer behavior
- environmental behavior (persistence, concurrency, initialization) not visible in the proof-of-concept setup

## Ambiguity lifecycle

Every ambiguity moves through explicit states:

1. **Open** — recorded with an identifier, description, and the evidence that exposes it
2. **Disposed** — a downstream artifact explicitly decides how to proceed despite it
3. **Resolved** — new evidence or human clarification eliminates it
4. **Accepted** — it is acknowledged as permanently unresolvable within project scope, with consequences documented

State changes must be recorded where they happen, and the register entry must point to the artifact that changed the state.

## Registration requirements

Each ambiguity entry must include:

- identifier (`A-n`), stable across the pipeline run
- description of what is unclear and why
- evidence anchors that expose the ambiguity
- candidate interpretations, when enumerable
- impact: which downstream stages it can affect
- blocking status: does it block the next stage, or allow cautious progression?

## Disposition discipline

When a downstream artifact proceeds despite an open ambiguity, it must record a disposition stating:

- which interpretation was adopted (or which design decision `D-n` neutralizes the ambiguity)
- why that choice is safe enough at this stage
- what would need to be revisited if the interpretation proves wrong

A disposition is a scoped decision, not a resolution.
The ambiguity remains visible in the register with its disposition attached.

## Propagation rules

- An ambiguity affecting a semantic rule propagates to every artifact that uses that rule.
- Contract and adapter artifacts must not silently normalize ambiguous behavior into clean specifications; the normalization is a design decision and must be labeled as one.
- Validation must not claim conformance on behavior whose expected outcome depends on an open ambiguity; such scenarios are either excluded (with note) or run as exploratory observations.

## Blocking assessment

An ambiguity is blocking for the next stage when the next stage would have to guess to proceed.

Guidance:
- if the ambiguity concerns the core rule set or the meaning of a primary input/output, it blocks semantics/boundary work
- if it concerns edge behavior with contained impact, cautious progression with disposition is acceptable
- if it concerns environmental behavior that the target scope excludes, it may be Accepted with documented consequences

The assessment must be made explicitly, not implied by simply continuing the work.

## Research-specific interpretation

The ambiguity register is a research instrument.
It documents the limits of what AI-assisted extraction could establish from the available legacy material — which is itself a finding of the research study.

Institutional legacy material is expected to produce a larger and harder register; the proof of concept should exercise the mechanics of registration, disposition, and propagation so they are ready for that case.

## Desired outcome

Ambiguity management is working when:

- no downstream artifact contains a silent guess
- every open ambiguity can be listed with its current state and dispositions
- validation scope explicitly reflects unresolved ambiguity
- the research study can quantify and characterize the uncertainty the pipeline had to manage
