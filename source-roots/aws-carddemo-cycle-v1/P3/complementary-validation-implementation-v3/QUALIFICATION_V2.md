# Qualification — complementary validation implementation v2

Status: versioned corrective package. v1 is preserved. This package qualifies checker behavior only; it does not claim campaign execution, API result correctness, real COBOL observation, or human approval.

## Changes from v1

- Retained public imports/functions: `Fixture`, `load_fixture`, `run_fixture_checks`, `CheckResult`, `CheckStatus`, `source_catalog`.
- Added optional `Fixture.evidence_class` / fixture JSON `evidenceClass`.
- Synthetic semantically-correct observations now return `INCONCLUSIVE`, not `PASS`, with `details.semanticOutcome='pass'` and `details.evidenceSufficiency.businessConclusionAllowed=false`.
- `PASS` is reserved for `evidenceClass == 'real_cobol_observation'` plus checker success.
- Added provenance requirements for observed records: `kind`, `artifact`, `recordOffset` or `lineNumber`, and `observedFields`.
- `POSTTRAN-OBL-009` no longer accepts `effectOrder` flags as evidence; it requires observed effect records with provenance.

## Qualification result

Executed with `../../P2a/.venv/bin/python`:

```text
Ran 8 tests in 0.059s
OK
synthetic_success_results_v2.json {'pending': 17, 'inconclusive': 8}
synthetic_known_wrong_results_v2.json {'pending': 17, 'failed': 8}
schema ok evidence/synthetic_success_results_v2.json
schema ok evidence/synthetic_known_wrong_results_v2.json
```

Independent review tests in `../complementary-checker-review-v1`:

```text
Ran 5 tests in 0.024s
OK
```

v1 preservation check:

```text
../complementary-validation-implementation-v1: Ran 8 tests in 0.055s OK
```

## Obligation state

- Implemented checker slices: 8/25, source-anchored and adversarially checked locally.
- Pending checker slices: 17/25.
- Business obligations concluded from real observations: 0/25 in this package, because inputs are synthetic review observations only.

Detailed review: `../complementary-checker-review-v1/QUALIFICATION_REVIEW.md`.
