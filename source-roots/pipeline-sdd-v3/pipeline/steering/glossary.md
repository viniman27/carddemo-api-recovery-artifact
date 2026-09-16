# Project Glossary

Canonical vocabulary for the research pipeline. Artifacts, reviews, and the research study should use these terms consistently and avoid untracked synonyms.

## Pipeline concepts

- **Capability** — a unit of business significance recovered from legacy behavior, potentially spanning multiple source artifacts (in plain terms: a functionality of the legacy system). The primary unit of analysis; never assumed equal to a file, program, or paragraph. A large capability may contain smaller functions; selection is always incremental, never big-bang.
- **Pipeline run** — the full progression of one capability through stages 1–8.
- **Stage** — one of the eight ordered steps of the pipeline (see `pipeline.md`). Stages are cumulative and gate-protected.
- **Completeness gate** — the explicit, checkable exit conditions of a stage artifact; passing it is the entry condition of the next stage.
- **Upstream authority** — the reviewed artifact(s) a given artifact derives from and remains subordinate to.

## Evidence concepts

- **Evidence (`E-n`)** — an observable fact about the legacy system, anchored to source (`file:line-range`) or to controlled execution. Distinct from interpretation.
- **Evidence anchor** — the explicit source reference that grounds a claim.
- **Inference** — an interpretation built on evidence but not directly observable; must be labeled as such.
- **Ambiguity (`A-n`)** — a point where evidence admits multiple readings or is absent; tracked through the lifecycle open → disposed/resolved/accepted.
- **Disposition** — a scoped downstream decision to proceed despite an open ambiguity, with the adopted interpretation recorded.

## Semantic concepts

- **Capability semantics** — the structured meaning of a capability: purpose, rules, preconditions, postconditions, invariants, side effects.
- **Semantic rule (`R-n`)** — a named, evidence-grounded behavioral rule (e.g., overdraft protection).
- **Canonical data boundary** — the technology-neutral definition of the capability's data meanings: canonical types, fields, constraints, and legacy mappings. Not yet an API.
- **Canonical type** — a named, constraint-carrying type at the boundary (e.g., `MonetaryValue`, `DebitOutcome`).

## Modernization concepts

- **API contract** — the modern interface surface derived from the canonical boundary: operations, schemas, error strategy. Derived, never invented from source inspection.
- **Adapter** — the layer that connects the contract surface to legacy-faithful behavior without redefining contract semantics.
- **Wrapper** — the default adaptation strategy: a layer added on top of the unmodified legacy core (in the PoC, via a Node.js-to-COBOL binding) so that legacy rules keep executing where they live. The legacy source is read-only for the pipeline.
- **Reference layer** — an explicitly identified comparison or execution aid; its technology is per-run and it is not automatically the semantic authority.
- **Design decision (`D-n`)** — a recorded choice made where evidence underdetermines the artifact, with rationale and downstream consequences.

## Validation concepts

- **Semantic validation** — the assessment of whether modernized behavior adheres to legacy-observed or legacy-inferred behavior.
- **Validation scenario (`V-n`)** — a planned, upstream-anchored behavioral check with a stated oracle.
- **Oracle** — the stated reference for a particular question: reviewed contract for surface conformance, observed legacy for characterization, or agreed observable obligations for functional continuity. No universal hierarchy; conflicts and expected-outcome provenance remain explicit.
- **Divergence (`DIV-n`)** — an observed difference between expected and observed behavior, registered with origin and disposition.
- **Conformance assessment** — the scoped adherence claim the validated scenarios actually support. Never a blanket equivalence claim.
- **Behavioral confidence** — the claim level this project operates at: test-based consistency with observed legacy behavior for validated scenarios. Deliberately weaker than "verification" or "semantic preservation", which imply formal guarantees and are avoided in claims (see `rules/validation-principles.md`).
- **Transferable test suite** — the derived test suite phrased against the contract surface, reusable to check a future reimplementation exposed through the same API.

## Research-context terms

- **Public application / PoC** — a scoped public run used to exercise and evaluate the method. It is not automatically the later Phase 2 corpus; each application records its own inputs and framework version.
- **Institutional case** — the intended later application of the pipeline to real institutional COBOL legacy material.
- **Institutional applicability note** — an in-place remark documenting where PoC conditions diverge from expected institutional conditions.
- **Gap (`G-n`)** — a diagnosed discrepancy between available evidence, current representation, and required maturity for the next stage; classified blocking / important / cosmetic.

---
Add terms only when they carry methodological weight across artifacts. This is vocabulary memory, not an index of everything.
