# Pipeline Artifact Templates

Templates for the eight authoritative artifacts of the modernization pipeline. They codify the anatomy that stabilized during the account-balance proof-of-concept run (see `steering/pipeline.md`).

## Usage

- Instantiate the template matching the spec's `artifact_type` as the authoritative artifact of the spec directory (e.g., `legacy-evidence-spec.md` inside `legacy-evidence-[capability]/`).
- `requirements.md` / `design.md` / `tasks.md` remain SDD phase files that plan and support the production of this artifact; the artifact itself is the stage output.
- Replace `{{...}}` placeholders; delete guidance comments (`<!-- ... -->`) once addressed.
- Section numbering may grow per capability, but the anatomy (Purpose → Integrity Discipline → Upstream Authority → body → Ambiguity handling → Completeness Gate) must be preserved.
- Identifier conventions (`E-n`, `A-n`, `R-n`, `D-n`, `V-n`, `DIV-n`) follow `settings/rules/traceability.md`.

## Files

| Stage | Template |
|-------|----------|
| 1 | `pipeline-scope-spec.md` |
| 2 | `capability-selection-spec.md` |
| 3 | `legacy-evidence-spec.md` |
| 4 | `capability-semantics-spec.md` |
| 5 | `canonical-data-boundary-spec.md` |
| 6 | `api-contract-spec.md` |
| 7 | `adapter-behavior-spec.md` |
| 8 | `semantic-validation-spec.md` + `validation-report.md` |
