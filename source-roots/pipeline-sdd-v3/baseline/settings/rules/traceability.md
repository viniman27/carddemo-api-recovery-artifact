# Traceability

Traceability is the property that allows every claim in a downstream artifact to be followed back to legacy evidence or to a reviewed upstream specification.

In this project, traceability is not documentation hygiene.
It is the mechanism that makes the modernization pipeline analyzable, reviewable, and defensible in a research study context.

## Primary purpose

Every artifact in the pipeline must make it possible to answer, for each of its substantive claims:

- Where did this come from?
- What evidence or upstream decision supports it?
- What downstream artifacts depend on it?

The minimum traceability chain is:

legacy evidence -> capability semantics -> canonical data boundary -> API contract -> adapter behavior -> semantic validation

## Identifier conventions

Traceable elements must carry stable identifiers so that references survive rewording.

| Prefix | Element | Defined in | Referenced by |
|--------|---------|------------|---------------|
| `E-n`  | Evidence item | Legacy Evidence Spec | all downstream artifacts |
| `A-n`  | Ambiguity | any spec (usually Legacy Evidence / Capability Semantics) | ambiguity dispositions downstream |
| `R-n`  | Business rule / semantic rule | Capability Semantics Spec | boundary, contract, adapter, validation |
| `D-n`  | Design decision | the spec where the decision is made | downstream artifacts affected |
| `G-n`  | Gap | gap analysis outputs | tasks, reviews |
| `V-n`  | Validation scenario | Semantic Validation Spec | validation report |
| `DIV-n` | Observed divergence | Validation Report | conformance assessment, research study discussion |

Identifiers are scoped per capability pipeline run.
Once assigned, an identifier must not be silently renumbered.

## Evidence anchoring

Claims grounded in legacy source must cite their anchor explicitly, preferably as:

`<file>:<line-range>` — e.g., `main.cob:112-131`

Rules for anchors:

- one claim may cite multiple anchors
- an anchor must point to the artifact that actually exhibits the behavior, not merely a related file
- if a claim cannot be anchored, it must be labeled as inference or ambiguity, never presented as anchored evidence
- anchors to the Node.js reference layer must be marked as reference-layer anchors, distinct from COBOL evidence anchors

### Mechanical anchor verification

Anchor resolution is the one completeness condition in this framework that does not require human judgement, and it should therefore be checked by script rather than by reading. A verifier walks every `E-n` in a stage-3 artifact and confirms that the file exists in the frozen source, that the line range is within bounds, and that the anchor is present and well-formed. A failure fails the gate.

Two boundaries keep the check honest:

- **Literal quotation is a warning, not a failure.** Artifacts legitimately condense — recording `LINKAGE PASSED-OPERATION PIC X(6)` for two source lines is correct practice, and demanding character-for-character identity would manufacture false positives.
- **Anchoring is not coverage.** The verifier establishes that each claim points at code that exists. It says nothing about whether the evidence set covers the capability's relevant operations, which remains a matter for human review. Report the two separately and never let the mechanical number stand in for the judged one.

Phase 1 ran this over three stage-3 artifacts and resolved 54 of 54 anchors. The value of the result is that it is *measured* rather than asserted; the remaining completeness conditions are still inspection-based and worth mechanizing where they admit it.

## Upstream authority sections

Every pipeline artifact after Pipeline Scope must open with an explicit upstream authority statement that:

- names the upstream spec(s) it derives from
- states the entry condition inherited from the upstream completeness gate
- lists inherited constraints that remain binding

A downstream artifact that cannot state its upstream authority is not ready to exist.

## Traceability matrix discipline

Artifacts at the contract stage and later should include a traceability table mapping their elements to upstream identifiers, for example:

| Contract element | Canonical element | Semantic rule | Evidence |
|------------------|-------------------|---------------|----------|
| `POST /balance/debit` rejected variant | `DebitOutcome.rejected` | `R-3` (overdraft protection) | `E-7` (`operations.cob:88-104`) |

The table does not need to be exhaustive for trivial mappings, but every non-obvious or decision-bearing mapping must appear.

## Broken traceability is a blocking gap

The following situations are blocking, not cosmetic:

- a contract element with no corresponding canonical element
- a semantic rule with no evidence anchor and no explicit inference label
- an adapter behavior that cannot be mapped to a contract clause
- a validation claim with no scenario identifier
- a downstream artifact citing an upstream section that no longer exists

When upstream artifacts change, downstream references must be re-verified before the downstream artifact is treated as authoritative again.

## Research-specific interpretation

In the research study, the traceability chain is itself a result: it demonstrates that the pipeline preserves meaning across transformations.

Therefore:
- traceability records are first-class research artifacts
- identifier stability matters more than prose elegance
- a reviewer must be able to sample any downstream claim and walk it back to COBOL evidence without guessing

## Desired outcome

A successful traceability discipline should make the following test pass at any point in the pipeline:

> Pick any substantive claim in any artifact. Within a few minutes, a reviewer can identify the upstream element or legacy anchor that justifies it — or find an explicit ambiguity/inference label explaining why no anchor exists.

If that test fails, traceability is broken regardless of how complete the documents look.
