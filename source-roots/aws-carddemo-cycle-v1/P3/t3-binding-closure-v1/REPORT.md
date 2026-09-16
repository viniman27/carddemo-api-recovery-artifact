# T3 Binding Closure v1

Status: candidate preparatory amendment only; officialCampaign=false.

## Root cause

The frozen T3 E1/E2-2 request bodies carried generic COBOL DD names (`TRANFILE`, `TCATBALF`, `CARDXREF`, etc.) where the real local P2c facades require their existing technical fixture-token protocols:

- E1 zero-shot facade: `p3:{track}:{DD}` exact local token.
- E2-2 few-shot facade: `p3-local-technical-fixture-selection:{bindingField}` exact local token.

Two additional technical mapper mismatches were source-backed by the facade/contract:

- E1 reporting output fields must use the facade DD `TRANREPT`, not the generic public name `REPORT`.
- E1-3 reporting `dateParameterRecords` has `contentEncoding: base64` / 80 decoded bytes; the candidate preserves the same 80 bytes and only encodes them.

No contract, API facade, COBOL source, T1/T2 original suite, or business transaction data was changed.

## Outputs

- Candidate suite: `amended-candidates/T3-BINDING-CLOSURE-V1.json`
  - sha256: `ccf49bbe86d9342e3e66fafdfc6db6cf572255e20aba829af8ef449409643c6c`
  - cases: 12 (E1-1/E1-2/E1-3 first T3 case per track = 9; E2-2 first T3 case per track = 3)
- Amendment manifest: `amended-candidates/AMENDMENT-MANIFEST.json`
  - sha256: `8265944c8af911373bf4dee435c2f5037c0d49539ccce0f6094ca5e7cc46aba3`
- Real readiness report: `real-readiness-T3-BINDING-CLOSURE-V1/campaign-report.json`
  - sha256: `79be3ad0b614dc668c9f35a2dabad69cfecc49297bdedc1726cd5b69bdd49479`

## Verification

- TDD regression command: `python3 -m unittest discover -s tests -v`
  - result: 5 tests passed.
- Plan command used P2a venv and loaded the amended frozen suite:
  - planned: 12 cases, 1 suite.
- Real narrow integration:
  - attempted: 12
  - completed: 12
  - structural_ok: 12
  - statuses: 12/12 HTTP 200
  - stopPolicy: `stopped=false`, `reason=null`
  - experimentalViolations: `[]`
  - measurement_admissible: 3 (E2-2); E1 remained structurally successful but measurement-limited by existing readiness measurement classification.

## Contract-defect preservation

The amendment function leaves SDD closed `{}` bodies unchanged. It does not merge/strengthen allOf schemas, does not add business fields, and does not relax contract defects. The observed E2-2 pre-COBOL 400 was not an allOf-closed-positive impossibility; it was the same technical fixture-token protocol mismatch, now corrected only in the candidate T3 request bytes.
