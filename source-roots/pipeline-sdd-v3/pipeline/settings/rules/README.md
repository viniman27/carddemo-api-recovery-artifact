# Rules Index

Rules are framework-level discipline documents. They shape how artifacts are produced; the methodological truth of the project lives in `steering/` and in the specs themselves.

## Rules by concern

| Rule | Concern | Most relevant stages |
|------|---------|----------------------|
| `steering-principles.md` | What belongs in project memory | all |
| `design-principles.md` | Cross-cutting design discipline for every artifact | all |
| `design-discovery-light.md` | Low-commitment exploration of a candidate capability | 1–3 |
| `design-discovery-full.md` | Rigorous evidence-based reverse engineering | 3–5 |
| `ears-format.md` | When and how EARS phrasing is allowed | 6–8 |
| `gap-analysis.md` | Diagnosing what blocks safe stage progression | all transitions |
| `design-review.md` | Artifact fitness and recorded counterexample review at stages 4 and 6 | all transitions |
| `tasks-generation.md` | Stage-controlled derivation of work units | all |
| `tasks-parallel-analysis.md` | When parallel work is safe | all |
| `traceability.md` | Evidence anchors, downstream traceability and reverse-completeness matrices | all |
| `ambiguity-management.md` | Lifecycle of ambiguities (`A-n`): open, disposed, resolved, accepted | all |
| `validation-principles.md` | Scenario derivation, oracles, divergences, claim vocabulary, conformance limits | 8 |
| `legacy-code-policy.md` | Legacy source is read-only; wrapper-first; defect reporting policy | 3, 7, 8 |
| `ai-assistance.md` | Role boundaries, hallucination guards, provenance for reproducibility | all |
| `run-integrity.md` | Authorized inputs, state propagation, batch failures, oracle purpose and revision control | all |

## Stage numbering

Stage numbers refer to the pipeline taxonomy (see `steering/pipeline.md`):

1. Pipeline Scope
2. Capability Selection
3. Legacy Evidence
4. Capability Semantics
5. Canonical Data Boundary
6. API Contract
7. Adapter Behavior
8. Semantic Validation

## Precedence

When rules appear to conflict, resolve in this order:

1. research logic recorded in `steering/`, with cross-stage input/state discipline in `run-integrity.md`
2. stage discipline (`design-principles.md`, `gap-analysis.md`, `design-review.md`)
3. artifact-local guidance in templates
4. framework defaults

Framework behavior is always subordinate to research logic.
