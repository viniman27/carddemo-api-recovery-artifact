# Tasks Generation

Generate tasks only after the relevant specification artifacts are mature enough to support execution without forcing premature design decisions.

In this project, task generation is not a generic productivity step.
It is a stage-controlled transformation from structured specification artifacts into executable work units that preserve methodological order, semantic discipline, and traceability.

## Primary purpose

Task generation must translate stabilized specification artifacts into concrete, reviewable, and traceable units of work.

Tasks must serve the specification-driven pipeline.
They must not replace it, compress it, or bypass it.

The purpose of task generation is to operationalize what has already been sufficiently clarified, not to invent structure where the specifications are still incomplete.

## Minimum maturity requirement

In this project, tasks should only be generated after at least the following artifacts exist and are sufficiently mature:

- capability selection
- legacy evidence
- capability semantics

For downstream implementation-oriented work, additional artifacts must also be available:

### Before data-boundary tasks
- capability semantics must be stable enough to support canonical modeling

### Before API-contract tasks
- canonical data boundary must exist and be stable enough

### Before adapter-implementation tasks
- API contract must exist and have passed review

### Before semantic-validation tasks
- adapter behavior and validation basis must be explicit enough to support meaningful comparison

## Stage-aware task generation

Tasks must be generated according to the current stage of the pipeline.

### Early-stage tasks
These are still specification-oriented and document-first:
- evidence refinement tasks
- ambiguity reduction tasks
- capability boundary clarification tasks
- semantics consolidation tasks
- canonical data boundary definition tasks

### Later-stage tasks
These are interface- or implementation-oriented:
- API contract derivation tasks
- adapter behavior definition tasks
- implementation tasks
- semantic validation tasks
- integration testing tasks

The framework must not generate late-stage tasks merely because they appear implementable.
Stage discipline takes precedence over implementation momentum.

## Preferred task groups

Preferred task groups in this project are:

1. evidence refinement tasks
2. semantics consolidation tasks
3. canonical data boundary definition tasks
4. API contract derivation tasks
5. adapter behavior and implementation tasks
6. semantic validation tasks

These groups reflect the intended order of the research pipeline and should remain visible in task planning.

## Tasks must come from specs, not from vague intent

Do not generate tasks directly from broad feature goals, vague modernization intent, or implementation enthusiasm.

Tasks must be derived from existing specs, reviewed artifacts, or explicit gap analysis outcomes.

A task is justified when it can be traced to one of the following:
- a stabilized specification artifact
- a blocking or important gap
- a design review decision
- an explicit validation requirement

A task is not justified merely because it "seems useful."

## Task quality rules

Each task should:

- reference the artifact(s) it depends on
- state the stage it belongs to
- have a clear expected output
- avoid mixing analysis and implementation in the same step
- remain small enough to preserve context and traceability
- be specific enough to review after completion
- avoid silently introducing new semantics
- preserve the order of the specification-driven process

Each task should produce one identifiable result.
If a task appears to require multiple conceptual layers at once, split it.

## Forbidden task compression

Do not generate tasks that collapse multiple stages into one unit of work.

In particular, avoid tasks that combine:
- evidence extraction + semantic consolidation
- semantic consolidation + API design
- API design + adapter implementation
- implementation + validation judgment
- discovery + orchestration code generation

These compressions make the pipeline harder to review, harder to explain, and harder to defend in the research study.

## Early-stage restrictions

When the current stage is still discovery- or semantics-oriented, do not generate tasks that directly produce:

- pipeline orchestration modules
- service layers
- route/controller files
- adapter implementation files
- public execution surfaces
- API-facing code
- end-to-end integration logic

If such tasks are generated automatically by the framework, they should be treated as invalid or premature unless the relevant upstream specs already exist.

## Gap-driven task generation

Tasks should be especially informed by gap analysis.

Good tasks often arise from gaps such as:
- unclear capability boundary
- missing source evidence
- incomplete rule extraction
- unresolved side effect
- unstable field mapping
- incomplete validation basis

In this project, task generation should prefer closing real analytical or derivational gaps over simply expanding implementation.

## Output-oriented task design

A task should always make clear what artifact it is expected to change or produce.

Examples of acceptable expected outputs include:
- refined capability-selection spec
- updated legacy-evidence summary
- completed capability-semantics section
- stabilized canonical data boundary
- draft API contract
- reviewed adapter behavior artifact
- validation scenario table
- semantic comparison result

Avoid tasks whose outputs are vague, such as:
- "improve the pipeline"
- "modernize the feature"
- "make the API better"
- "finish implementation"

## Traceability discipline

Every task should preserve traceability.

A task should be answerable in terms of:
- what artifact it reads
- what artifact it modifies or generates
- what gap or review issue it addresses
- what downstream stage it enables

If a task cannot be linked to upstream artifacts and downstream purpose, it is probably too vague or premature.

## Reviewability of tasks

Tasks must be written so that a reviewer can later determine:
- whether the task was completed
- whether it produced the intended artifact
- whether it respected stage boundaries
- whether it introduced unsupported assumptions

A task that cannot be reviewed is not a good task for this project.

## Research-specific interpretation

In this master's project, tasks are not only implementation drivers.
They are also methodological execution units.

This means task generation must support:
- reproducibility of the proof of concept
- transparency of how the pipeline advanced
- explanation of how artifacts were produced
- later discussion in the research study

Tasks should therefore be intelligible not only to a developer, but also to a reviewer of the research process.

## Desired outcome

A successful task generation pass should produce a task set that is:

- stage-appropriate
- artifact-driven
- traceable
- non-compressed
- reviewable
- aligned with the specification-driven pipeline
- suitable for a research-oriented modernization workflow

If tasks accelerate implementation by skipping semantic maturity, they are failing.
If tasks operationalize the next justified step in the pipeline, they are working.