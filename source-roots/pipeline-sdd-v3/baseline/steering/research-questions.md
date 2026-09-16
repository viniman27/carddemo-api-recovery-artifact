# Research Questions

This file is the single source of truth for the project's research questions (RQs). It is steering memory, not the research study text: it captures the stable framing agreed with the advisor and evolves as the questions are refined for the qualification document.

## Status and provenance

- **Origin**: advisor meeting of 2026-06-12 ("Apresentação Api"). The advisor asked to (a) tie the RQs to the pipeline components, (b) treat the study as mostly qualitative, and (c) list five or more RQs and prioritize them, with final prioritization informed by feedback from institutional domain specialists.
- **Maturity**: draft. Wording will be lapidated in the qualification document; priorities marked below are provisional until specialist feedback is collected.
- **Vocabulary discipline**: RQs stay at the level of *test-based behavioral confidence* and *usefulness*. They must not claim or presuppose formal verification, semantic preservation, or equivalence (see `settings/rules/validation-principles.md`).

## Overarching question

**RQ0.** To what extent can LLMs, embedded in a human-supervised, specification-driven process, support the extraction and operationalization of knowledge from legacy COBOL systems — through structured strategies of summarization, decomposition, and validation — so as to derive and implement API contracts backed by test-based behavioral confidence, as a controlled step supporting incremental migration?

RQ0 is the umbrella; the questions below decompose it along the pipeline. The study is primarily qualitative: evidence comes from executing the pipeline, from researcher observation of each stage, and (in the institutional phase) from domain-specialist feedback and inter-rater agreement.

## Pipeline-aligned questions

Each RQ names the pipeline stage(s) it interrogates (see `steering/pipeline.md`).

### RQ1 — Evidence extraction fidelity *(stages 3)*
When assisting legacy-evidence extraction under human supervision, how reliably do LLMs recover observable COBOL behavior as anchored evidence, and how well do they keep the distinction between observed evidence, inference, and ambiguity rather than inventing plausible behavior?
- **Method**: compare extracted evidence against source anchors; count human corrections by type (`rules/ai-assistance.md` provenance).
- **Priority**: high — grounds every downstream claim.

### RQ2 — Semantic drift control via a structured intermediate spec *(stages 4–5)*
Does forcing an explicit, reviewable intermediate specification layer (capability semantics + canonical data boundary) between code and interface reduce semantic drift compared with a direct code→contract jump?
- **Method**: qualitative analysis of drift instances caught at the gate; ambiguity register outcomes.
- **Priority**: high — this is the methodological core of the pipeline.
- **Phase 1 status (July 2026): answered, hypothesis NOT confirmed.** A pre-registered baseline (frozen prompt, 15-item rubric decidable directly against the legacy, blind scoring, isolated executor) scored 14/15 against the pipeline's 15/15 — 14–14 discounting the one item biased toward a pipeline decision. For capabilities of 100–1100 lines the intermediate layer produced no measurable fidelity gain. With the comparison arm scoring at ceiling this is *no difference detected*, not evidence of no difference; the hypothesis is unconfirmed, which is distinct from false.

### RQ2′ — Drift control beyond single-reading scale *(stages 4–5)*
Does the intermediate specification layer reduce semantic drift compared with a direct code→contract jump **for capabilities that exceed the context recoverable in a single reading**?
- **Rationale**: RQ2 was answered only in the regime where the whole source fits in one reading, so structural decomposition resolves a problem that does not arise. The regime where it would have to pay for itself was never tested.
- **Method**: repeat the pre-registered protocol on the institutional slice, with enough repetitions to estimate variance and a rubric extended with a behavior-fabrication item declared before execution.
- **Priority**: high — successor to RQ2, not a reformulation of it.

### RQ3 — Usefulness of the "derive the API contract first" strategy *(stage 6)*
Is deriving an API contract (in OpenAPI) from stabilized semantics a useful and adequate way to expose selected legacy capabilities for migration support — capability-to-capability rather than function-to-function?
- **Method**: qualitative assessment of contract adequacy; specialist review in the institutional phase.
- **Priority**: high — one of the strategies flagged as most critical to institutional stakeholders.

### RQ4 — Behavioral confidence from derived tests and fuzzing *(stages 7–8)*
To what extent do LLM-derived test suites, complemented by property-based testing and stateful API fuzzing (e.g., RESTler over the derived OpenAPI), provide useful behavioral confidence that a modernized surface matches observed legacy behavior — and what are the limits of test-based validation here?
- **Method**: scenario conformance results; divergences registry; exploratory fuzzing findings (including any latent legacy defects surfaced).
- **Priority**: high — central to the validation argument; the "limits of tests" framing is itself a contribution.

### RQ5 — Value and cost of human-in-the-loop supervision *(all gates)*
How valuable is the human-in-the-loop / feedback strategy at each stage gate, and how much human supervision is actually required for the LLM drafts to become trustworthy stage outputs?
- **Method**: per-stage record of human intervention depth (none / minor / substantive / rejection); qualitative specialist feedback.
- **Priority**: medium-high — the advisor stressed the feedback loop as important and qualitative.

### RQ6 — Legacy-defect handling policy *(stages 3, 8)*
In a migration process, should the pipeline propose corrections for defects found in the legacy code, or keep the legacy unchanged and only report them? Under which contexts (open-source proof of concept vs critical institutional system) does each policy apply?
- **Method**: analysis of defects surfaced (e.g., the overdraft rule); specialist stance in the institutional phase; see `rules/legacy-code-policy.md`.
- **Priority**: medium — explicitly raised by the advisor as a distinct RQ.

### RQ7 — Economic viability *(all stages)*
What is the execution cost of the pipeline (at minimum, token consumption per stage) and is it viable relative to the human effort it would replace or assist?
- **Method**: instrument future runs to collect per-stage cost (`rules/ai-assistance.md`); compare against developer-time estimates.
- **Priority**: medium — recognized limitation of the first PoC run (cost was unmeasured); the advisor noted cost matters but is likely modest.

### RQ8 — Transferability from proof of concept to institutional scale *(whole pipeline)*
Do the results obtained on the controlled public repository transfer to a real institutional COBOL system with multiple programs, copybooks, and multiple capabilities — and what additional evidence (specialist evaluation, inter-rater agreement) is needed to support that transfer?
- **Method**: comparative execution across the two phases; qualitative specialist evaluation; agreement measures.
- **Priority**: medium — the institutional phase is the true empirical target, but depends on the PoC being sound first.

## Prioritization note

The advisor's expectation is that, by the end of the research, a subset of these RQs will emerge as the ones institutional stakeholders care about most, while others will matter less. Provisional high-priority set: **RQ1, RQ2, RQ3, RQ4**. RQ5–RQ8 are important but secondary until specialist feedback re-ranks them. This ranking must be revisited, not treated as fixed.

## Maintenance

- Keep RQs tied to pipeline stages; if a proposed RQ cannot be attached to a stage or to the overarching RQ0, question whether it belongs here.
- When wording is finalized in the qualification document, update this file to match and note the date.
- Do not let RQs drift into verification/semantic-preservation vocabulary.
