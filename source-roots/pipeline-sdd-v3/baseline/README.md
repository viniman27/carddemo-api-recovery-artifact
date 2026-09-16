# .sdd-v2 — Improved SDD Workspace

Evolution of `.sdd/` for the master's research pipeline on COBOL legacy modernization. Everything from v1 is preserved; v2 only adds, completes, and codifies.

## What changed from `.sdd/`

### Fixed
- `settings/rules/steering-principles.md` — was truncated mid-example in v1; completed (good/bad example pair, steering-vs-specs table, maintenance discipline, security notes, desired outcome).

### Codified (existing practice turned into reusable assets)
- `settings/templates/pipeline/` — **new**: templates for the eight taxonomy artifacts plus the validation report. They codify the anatomy that stabilized in the account-balance run (Purpose → Integrity Discipline → Upstream Authority & Entry Condition → numbered body → Ambiguity handling → Completeness Gate → next-stage entry condition). In v1 this pattern existed only implicitly inside the finished specs.
- `steering/pipeline.md` — **new**: consolidated stage map, canonical artifact anatomy, gate discipline, identifier scheme, and stage-boundary lessons from the proof of concept.
- `steering/glossary.md` — **new**: canonical project vocabulary (capability, evidence anchor, canonical type, oracle, divergence, …) for artifact and research study consistency.

### Added (gaps in the v1 rule set)
- `settings/rules/traceability.md` — identifier conventions (`E/A/R/D/G/V/DIV-n`), evidence-anchor format (`file:line-range`), upstream-authority sections, traceability matrices, and what counts as broken traceability.
- `settings/rules/ambiguity-management.md` — full ambiguity lifecycle (open → disposed/resolved/accepted), registration requirements, propagation rules, blocking assessment.
- `settings/rules/validation-principles.md` — plan-before-report separation, scenario derivation discipline, oracle hierarchy, divergence registry, conformance-claim limits, coverage honesty.
- `settings/rules/ai-assistance.md` — stage-by-stage AI role boundaries, hallucination guards, mandatory human checkpoints, provenance for research study reproducibility.
- `settings/rules/README.md` — index mapping every rule to pipeline stages, with precedence order.
- `settings/templates/steering-custom/cobol-analysis.md` — COBOL-specific evidence-extraction heuristics (reading order, PIC/88-level/REDEFINES guidance, interpretation traps, institutional-scale extensions).

### Extended
- `settings/templates/specs/init.json` — adds `artifact_type`, `pipeline_stage`, `capability`, `upstream_specs`, and a `gate` block (`completeness_gate_passed`, `gate_review_date`, `blocking_gaps`) to the v1 fields. Applies to new specs; existing spec.json files were not modified.

### Preserved unchanged
- `steering/product.md`, `steering/tech.md`, `steering/structure.md`
- the nine v1 rules (only `steering-principles.md` was completed)
- all v1 templates (`specs/`, `steering/`, `steering-custom/`)
- the eight account-balance spec directories (research outputs — see `specs/README.md`)

## Revision after advisor meeting (2026-06-12)

Based on the recorded advisor discussion ("Apresentação Api"), the following research positions were incorporated:

1. **Claim vocabulary softened** — no "verified"/"verifiable", "semantic preservation", or "equivalence" in claims; the project operates at test-based behavioral confidence. → `rules/validation-principles.md` (new "Claim vocabulary discipline"), `steering/glossary.md` ("Behavioral confidence"), validation templates.
2. **Optimal decomposition is an explicit non-goal** — the pipeline exposes functionalities to support migration; decomposition quality is another research line. → `steering/product.md` (new "Explicit Non-Goals").
3. **Legacy source is read-only** — wrapper-first adaptation (Node-to-COBOL binding in the PoC); defects are registered and reported, never silently fixed (PoC PR is an explicit exception; institutional: signal only). → new `rules/legacy-code-policy.md`, `steering/tech.md` ("Legacy Immutability Position"), adapter/validation templates.
4. **Rule reconstruction = documentation, optional in force** — documented rules serve boundary/contract/test derivation; the legacy core remains the runtime enforcer. → `steering/pipeline.md` (stage-boundary lessons), `capability-semantics-spec` template.
5. **Test suite as central, transferable artifact** — reusable against a future reimplementation behind the same API; candidate expansions: property-based testing, API fuzzing, manual tests. → `rules/validation-principles.md`, `steering/tech.md`, `semantic-validation-spec` template (new optional "Exploratory Expansion").
6. **OpenAPI as preferred contract format.** → `steering/tech.md`, `api-contract-spec` template.
7. **Cost observability (tokens per stage)** for future runs. → `steering/tech.md`, `rules/ai-assistance.md`.
8. **Institutional phase expectations** — multiple capabilities, domain-specialist evaluation, inter-rater agreement, cost measurement, selective automation. → `steering/product.md` (use case 2).

## Research questions and RESTler (2026-07-08)

Follow-up on the advisor feedback:

- **Research questions authored** — new `steering/research-questions.md` holds the overarching RQ0 plus eight pipeline-aligned RQs (evidence fidelity, semantic-drift control, contract-first strategy, test/fuzzing confidence, human-in-the-loop value, legacy-defect policy, cost, transferability), each tied to a stage, marked as a qualitative study, with a provisional priority ranking to be re-ranked by institutional-specialist feedback. `steering/product.md` points to it.
- **RESTler adopted as preferred fuzzer** — `github.com/microsoft/restler-fuzzer` is the Microsoft stateful REST API fuzzer the advisor referenced. It consumes the stage-6 OpenAPI contract directly, which reinforces the OpenAPI decision. Wired into `steering/tech.md` (test mechanisms), `rules/validation-principles.md` (exploratory expansion), and the `semantic-validation-spec` template (Section 6). It is a stage-8 exploratory mechanism; latent legacy defects it surfaces route to `legacy-code-policy.md`.

## Adoption

To adopt v2 as the active workspace, either point the SDD tooling at `.sdd-v2/` or, after review, replace `.sdd/` with this directory (keeping the old one as backup). `WORKSPACE-NOTES.md` references to `.sdd/` paths would need the corresponding update.
