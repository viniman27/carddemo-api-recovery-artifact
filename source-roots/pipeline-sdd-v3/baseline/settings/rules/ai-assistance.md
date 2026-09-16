# AI Assistance Discipline

This project studies AI-assisted extraction; therefore the use of AI is itself part of the research method and must be disciplined, bounded, and reportable.

LLMs in this project are assistants for extraction, structuring, derivation, and review support.
They are never authoritative semantic or validation oracles.

## Primary purpose

This rule defines:

1. what AI assistance is allowed to do at each stage
2. what must always remain under human review
3. what provenance information must be preserved for reproducibility

## Role boundaries per stage

| Stage | AI may assist with | AI must not do |
|-------|--------------------|----------------|
| Scope / Selection | surveying artifacts, drafting candidate boundaries | deciding the capability without human ratification |
| Legacy Evidence | locating anchors, summarizing structures, drafting evidence tables | asserting unanchored behavior as evidence |
| Capability Semantics | drafting rules from anchored evidence, structuring pre/postconditions | inventing rules to fill evidence gaps |
| Canonical Data Boundary | proposing canonical names/types, drafting mappings | fixing meanings that semantics has not stabilized |
| API Contract | deriving contract drafts from the boundary, drafting schemas | introducing surface behavior with no upstream basis |
| Adapter Behavior | drafting behavior mappings and error strategies | redefining contract semantics for implementation convenience |
| Semantic Validation | drafting scenarios from upstream anchors, comparing outputs | judging its own output as the conformance verdict |

## Hallucination guards

The known failure modes of LLM-based extraction must be actively guarded against:

- **Plausible invention**: fluent claims about legacy behavior with no anchor. Guard: every extracted claim requires an evidence anchor or an explicit inference label. Phase 1 gives this guard its only empirical support so far: an unscaffolded baseline asserted that a fill loop leaves a byte unwritten — false, falsified by recompiling the unmodified subprogram — and built three contract elements on the invented defect, while the pipeline produced no fabrication across three cases. Three runs per arm makes this an indication rather than a measurement, but it is the failure mode most worth instrumenting, and the anchoring requirement is the plausible mechanism.
- **Premature closure**: resolving ambiguity by picking the most common interpretation. Guard: ambiguities are recorded (`A-n`), not resolved by fluency.
- **Domain-pattern bleed-through**: importing "how accounting systems usually work" into a system that works differently. Guard: review must ask "is this in the COBOL, or in the training data?"
- **Compression drift**: meaning subtly changing across restatements. Guard: downstream restatements must be checked against upstream identifiers, not against memory of them.

## Human review checkpoints

AI-generated content becomes authoritative only after human review at stage boundaries.

Mandatory human checkpoints:

- ratification of the selected capability
- approval of the legacy evidence spec before semantics
- approval of capability semantics before canonical boundary work
- approval of the canonical boundary before contract derivation
- approval of the API contract before adapter behavior
- approval of the validation plan before executing validation
- acceptance of the conformance assessment

Fast-tracking (`-y`) any of these checkpoints is an explicit methodological decision and should be noted in the affected artifact.

## Provenance for reproducibility

For each pipeline stage, preserve enough information to describe in the research study how AI assistance was used:

- which model/tool family was used (e.g., GPT via the SDD command workflow)
- at approximately what date the stage was executed
- which artifacts were provided as input context
- what kind of human correction was needed (none / minor edits / substantive rework / rejection)
- execution cost when available — at minimum, approximate token consumption per stage (an advisor-requested metric)

Cost is recoverable retrospectively from the execution transcript by attributing turns to the last observed (capability, stage) pair, but the attribution is a heuristic: stage boundaries are approximate, rework counts against the current stage, and one-off framework configuration lands on whichever stage absorbed it. Prefer live measurement where the tooling allows; where it does not, state that the figure is retrospective and name the attribution rule.

**Token cost is not effort cost.** Consumption figures measure the model, not the human review at the gates, which phase 1 left entirely uninstrumented. Any economic-viability claim requires both, and a claim resting only on tokens should say so.

**Record the run count.** A generative model produces different artifacts across runs from identical input. A pipeline executed once per capability yields a sample of size one from the distribution of possible outputs, and no statement about variance is available. Where repetitions are affordable, run them; where they are not, say plainly that variance was not measured rather than letting single-run artifacts read as stable output.

This does not require archiving raw transcripts, but the degree of human intervention per stage is a research observation and must not be lost.

Record provenance in the spec's `research.md` or in a dedicated section of the artifact, whichever the stage's template indicates.

## Failure reporting

When AI assistance produces wrong or unsupported content that is caught by review, that event is data, not noise.

Notable failure events should be logged briefly (stage, type of error, how it was detected), because they inform:

- the research study's discussion of AI reliability in legacy extraction
- the design of guardrails for the institutional case

## Desired outcome

AI assistance is working in this project when:

- extraction speed improves without unanchored claims entering authoritative artifacts
- every stage output can be defended without appealing to "the model said so"
- the research study can describe precisely where AI helped, where it failed, and how the pipeline contained those failures
