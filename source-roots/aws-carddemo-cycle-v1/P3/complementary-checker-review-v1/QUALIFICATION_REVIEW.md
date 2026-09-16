# Complementary checker substantive review v1

Status: local checker qualification only. No campaign execution, no API result, no COBOL run result, no human approval, and no business-pass claim.

## Reviewed artifacts

- Preserved implementation: `P3/complementary-validation-implementation-v1/`
- Fixed versioned implementation: `P3/complementary-validation-implementation-v2/`
- Regression tests: `P3/complementary-checker-review-v1/tests/test_v2_substantive_qualification.py`
- 25-scenario catalogue: `P3/complementary-validation-v2/scenario-catalog.json`
- Real source anchor base from catalogue: `sdd-runs/E3-stage9-02/execution/isolated-cycle/aws-carddemo-preparation/research-corpus/`

## Source validity findings for the 8 implemented obligations

| Obligation | Source support observed | v1 checker sufficiency | v2 conclusion from current observations |
| --- | --- | --- | --- |
| `POSTTRAN-OBL-003` | Supported by `CVTRA06Y.cpy`/`CVTRA05Y.cpy` matching layouts and `CBTRN02C.cbl` moving DALYTRAN fields plus `CURRENT-DATE`-derived proc timestamp. | Too weak: accepted synthetic field objects without observation provenance. | `INCONCLUSIVE` on synthetic success; may pass only with real COBOL observations and provenance. |
| `POSTTRAN-OBL-004` | Supported by `CBTRN02C.cbl` missing-card branch moving reason `100` and `INVALID CARD NUMBER FOUND`. | Too weak: accepted hand-authored reject object without raw provenance. | `INCONCLUSIVE` on synthetic success; wrong reason/posted transaction still fails. |
| `POSTTRAN-OBL-006` | Supported by reject-write paragraph and final `RETURN-CODE` set to `4` when reject count > 0. | Too weak: relied on fixture flags for reject write and return code. | `INCONCLUSIVE` on synthetic success; wrong return code/reject absence still fails. |
| `POSTTRAN-OBL-009` | Source order supports TCATBAL/account attempts before TRANFILE write, with duplicate/write-status behavior not a prevalidation reject. | Defective: accepted `effectOrder` assertion flags rather than observed effect records. | Fixed: v2 rejects effect-order-only observations. Requires observed effect records with provenance. |
| `INTCALC-OBL-005` | Source supports zero-rate guard and formula `(TRAN-CAT-BAL * DIS-INT-RATE) / 1200`; catalogue itself says numeric amount/PIC qualification remains pending. | Too weak: accepted matching formula numbers without raw observation provenance and could be overread as business pass. | `INCONCLUSIVE` on synthetic success; rejects formula-matching observations lacking provenance. Exact rounding/sign precision remains limited. |
| `INTCALC-OBL-006` | Source supports MOVEs for system interest transaction fields and runtime timestamp. | Too weak: accepted object fields without raw transaction provenance. | `INCONCLUSIVE` on synthetic success; wrong fields still fail. |
| `TRANREPT-OBL-002` | Source supports textual `TRAN-PROC-TS(1:10)` range filter before detail processing; EOF conditional path is a documented limitation. | Too weak: accepted made-up report transaction list. | `INCONCLUSIVE` on synthetic success; wrong in/out range behavior still fails. EOF behavior remains unsupported. |
| `TRANREPT-OBL-006` | Source supports detail line write and accumulation into page/account totals for qualified records. | Too weak: accepted report-line bytes without line provenance. | `INCONCLUSIVE` on synthetic success; wrong totals/empty bytes still fail. |

## TDD evidence

RED (new review tests against missing/faulty v2):

```text
../../P2a/.venv/bin/python -m unittest discover -s tests -v
FAILED (errors=4)
FileNotFoundError: ... complementary-validation-implementation-v2/semantic_checkers/__init__.py
```

GREEN after v2 fixes:

```text
cd P3/complementary-checker-review-v1
../../P2a/.venv/bin/python -m unittest discover -s tests -v
Ran 5 tests in 0.024s
OK
```

v2 implementation suite:

```text
cd P3/complementary-validation-implementation-v2
../../P2a/.venv/bin/python -m unittest discover -s tests -v
Ran 8 tests in 0.059s
OK
```

v1 preservation check:

```text
cd P3/complementary-validation-implementation-v1
../../P2a/.venv/bin/python -m unittest discover -s tests -v
Ran 8 tests in 0.055s
OK
```

v2 evidence generation and schema validation:

```text
synthetic_success_results_v2.json {'pending': 17, 'inconclusive': 8}
synthetic_known_wrong_results_v2.json {'pending': 17, 'failed': 8}
schema ok evidence/synthetic_success_results_v2.json
schema ok evidence/synthetic_known_wrong_results_v2.json
```

## v2 interface/migration notes

- Public import names are retained: `Fixture`, `load_fixture`, `run_fixture_checks`, `CheckResult`, `CheckStatus`, `source_catalog`.
- `Fixture` has one compatible optional field: `evidence_class='synthetic_review'`.
- Fixture JSON may include top-level `evidenceClass`. Only `real_cobol_observation` can produce `PASS`; synthetic fixtures with semantically correct observations produce `INCONCLUSIVE` plus `details.semanticOutcome='pass'`.
- Implemented checkers now require per-record provenance (`kind`, `artifact`, `recordOffset` or `lineNumber`, and `observedFields`) for real-observation pass eligibility. `POSTTRAN-OBL-009` requires observed `effects` records; v1-style `effectOrder` flags are rejected.

## Generic quality gate note

`pipeline-sdd-v3/pipeline/tools/check_test_quality_gate.py` is stronger than label-only for many manifest fields, but it cannot substantively validate business checker evidence: it checks presence of oracle inventory, counterexample lists, and authority labels, not whether checker observations are real COBOL records or whether counterexamples catch semantic blind spots. I did not modify the generic gate; the substantive fix is isolated in v2 checker qualification.

## Bottom line

No obligation can currently be concluded as a real business/API/COBOL pass from the available synthetic review observations. The defensible current result is: 8 checker slices are source-anchored and adversarially qualified as local checkers; 17 obligations remain pending; all 25 business obligation outcomes remain unsupported until real COBOL/API observations with provenance are supplied.
