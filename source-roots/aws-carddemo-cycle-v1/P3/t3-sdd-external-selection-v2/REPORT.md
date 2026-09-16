# T3 SDD external selection v2

Status: candidate/static-only local correction. Official campaign: false. Official suite/fixture promotion: false. Runtime/API/COBOL executed: false.

## Scope

This version preserves `t3-sdd-external-selection-v1` and writes a new local versioned correction under `P3/t3-sdd-external-selection-v2`.

Policy maintained:

- SDD public request body remains `{}` for `/posting`, `/interest`, and `/reporting`.
- Selection is local and external by `fixtureId`, using already pinned fixture resources.
- No expected status, report bytes, output file bytes, COBOL runtime result, or campaign oracle is introduced.
- No suites or fixtures are promoted and no campaign/freeze command is run.

## Conservative classifications

Computed SDD obligation denominator remains 25: 18 selected locally and 7 blocked.

Selected by track: `{"interest": 6, "posting": 6, "reporting": 6}`.

Selection categories:

```json
{"branch_selected_no_output_oracle": 3, "guard_eligible": 9, "guard_eligible_partial_branch": 2, "request_preparation_no_output_oracle": 1, "request_preparation_static_only": 3}
```

Corrections from v1 review:

- `POSTTRAN-OBL-007`: downgraded to partial branch selection. The fixture supports `tcatbal_status=00` only; `tcatbal_status=23` and `other` are not selected. Effective transitions are restricted to `POSTTRAN-T012` and `POSTTRAN-T013`; `POSTTRAN-T014` is excluded from static request preparation.
- `INTCALC-OBL-004`: downgraded to partial branch selection. The fixture supports `disc_rate_path=specific` and `disc_rate_path=zero`; `default` and `missing` are not selected. Effective transitions are restricted to `INTCALC-T007` and `INTCALC-T009Z`; `INTCALC-T008` is excluded from static request preparation.

Adapter static check now reports 65 candidate static requests after effective-transition filtering. Excluded by effective selection:

```json
[
  {"cellRef": "INTCALC-OBL-004::E3-01-SDD-stage6r3::interest", "transitionId": "INTCALC-T008"},
  {"cellRef": "INTCALC-OBL-004::E3-01-SDD-stage6r3::interest", "transitionId": "INTCALC-T008"},
  {"cellRef": "POSTTRAN-OBL-007::E3-01-SDD-stage6r3::posting", "transitionId": "POSTTRAN-T014"}
]
```

## Pins

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/t3-sdd-external-selection-v2/sdd_external_selection.py` | 32877 | `7e7313a8bb6304d56ee9a247f28d16aa197595b9f73ba974c4419ec8de87af1f` |
| `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/t3-sdd-external-selection-v2/tests/test_sdd_external_selection.py` | 7387 | `d934b13be82e104ff615b8f1d52106e41fedab77d1f163f93e4ed7b54e846ce1` |
| `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/t3-sdd-external-selection-v2/external-selection-plan.json` | 105989 | `137f65a2612c28f34763c22623681f27f736bc4d325e497ff2d10f177e36f815` |
| `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/t3-sdd-external-selection-v2/applicability_matrix.sdd-external-selection-v2.json` | 1064992 | `ed97ed5ece2ca592fb2fab2d52e8a26f0847534c9a78e49056a9b718036da09e` |
| `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/t3-sdd-external-selection-v2/recipes.sdd-external-selection-v2.json` | 41732 | `663f3ce0ed91c8ee1835bfa8affea68388848b434d396fecf8c4ad1c7936710c` |
| `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/t3-sdd-external-selection-v2/integrated-mapping.sdd-external-selection-v2.json` | 568693 | `4fdfca6d93053e84c755589be3794760f6912783b66d4168131cb27be15c2f1e` |
| `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/t3-sdd-external-selection-v2/fixture-byte-structural-check.json` | 3143 | `3ed1cd1e675b6f1920403ca9ab83b807a53dae81a8e4789b3109e8424cef9ca8` |
| `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/t3-sdd-external-selection-v2/adapter-static-check.json` | 26565 | `fd8d58d5720e62ae776912295a983cd5eaf32e663ef6af8789f8d99ffa89d898` |
| `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/t3-sdd-external-selection-v2/static-fairness-check.json` | 420 | `18e1b4612409ddab1cfcdc35838d4648a9cc64459404d19a8bf56d7f6ee714a2` |
| `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/t3-sdd-external-selection-v2/REPORT.json` | 10800 | `2097366be583bfdcb109bf3984f6393d270feff1560e371a82732af89e264e37` |
| `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/t3-sdd-external-selection-v2/sdd-id-migration.external-selection-v2.json` | 1076 | `a4658a786014da3e2036dbcca34cdd919fd46b95fa7e15e002a757db1de2a69c` |

## Verification

RED was observed before implementation with `P2a/.venv/bin/python -m unittest discover -s P3/t3-sdd-external-selection-v2/tests -v`: 8 tests run, 2 failures, 2 errors.

GREEN/static verification after implementation:

```text
PYTHONDONTWRITEBYTECODE=1 P2a/.venv/bin/python -m unittest discover -s P3/t3-sdd-external-selection-v2/tests -v
Ran 8 tests in 2.835s
OK
```

Artifact generation:

```text
PYTHONDONTWRITEBYTECODE=1 P2a/.venv/bin/python P3/t3-sdd-external-selection-v2/sdd_external_selection.py --p3 P3 --out P3/t3-sdd-external-selection-v2
status: candidate_static_only
selectedCells: 18
blockedCells: 7
adapterCases: 65
changedMatrixCells: 18
```
