# T3 SDD external selection v3 report

Status: candidate/static-only local correction. Official campaign: false. Official suite/fixture promotion: false. Runtime/API/COBOL executed: false.

## Scope

This version preserves `t3-sdd-external-selection-v1` and `t3-sdd-external-selection-v2` and writes a new local correction under `P3/t3-sdd-external-selection-v3`.

The correction targets the v2 bug where effective-transition restrictions were applied only to the JSON report cases, not to the actual returned `Suite.cases` used by callers.

## Real-suite correction

Behavioral check against v2 confirmed the parent bug on the real suite:

```json
{"version":"v2","suite_cases":68,"forbidden_in_suite_cases":[["INTCALC-OBL-004::E3-01-SDD-stage6r3::interest","INTCALC-T008"],["INTCALC-OBL-004::E3-01-SDD-stage6r3::interest","INTCALC-T008"],["POSTTRAN-OBL-007::E3-01-SDD-stage6r3::posting","POSTTRAN-T014"]]}
```

v3 result from `build_selected_t3_suite(...)`:

```json
{"version":"v3","suite_cases":65,"forbidden_in_suite_cases":[],"excluded_count":3}
```

The new entrypoint returns the restricted real `Suite`, not only a filtered `adapter-static-check.json` projection. `selected-suite-real.json` serializes that candidate/static-only suite for inspection.

## Conservative classifications preserved

Computed SDD obligation denominator remains 25: 18 selected locally and 7 blocked.

Selection categories:

```json
{"branch_selected_no_output_oracle":3,"guard_eligible":9,"guard_eligible_partial_branch":2,"request_preparation_no_output_oracle":1,"request_preparation_static_only":3}
```

Request bodies remain `{}` for all selected-suite cases. Fixture selection remains by `fixtureId`, not request fields. No output/status/report-byte oracle is introduced.

## Effective-transition policy

- Missing `effectiveSelectableTransitions`: no declared restriction; not treated as an invented allowed list.
- Empty `effectiveSelectableTransitions`: explicit deny.
- Non-empty `effectiveSelectableTransitions`: keep only listed transition IDs in the returned `Suite.cases`.

Excluded by declared effective selection:

```json
[
  {"cellRef":"INTCALC-OBL-004::E3-01-SDD-stage6r3::interest","transitionId":"INTCALC-T008"},
  {"cellRef":"INTCALC-OBL-004::E3-01-SDD-stage6r3::interest","transitionId":"INTCALC-T008"},
  {"cellRef":"POSTTRAN-OBL-007::E3-01-SDD-stage6r3::posting","transitionId":"POSTTRAN-T014"}
]
```

## Pins

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/t3-sdd-external-selection-v3/sdd_external_selection.py` | 35586 | `a9744fac60ff4ccb6a43cac7e52cafb669f6d9297834ee48f9d920550593d71a` |
| `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/t3-sdd-external-selection-v3/tests/test_sdd_external_selection.py` | 10478 | `0f67b7cbf46ea5f8520f904f5b0816a0637926484d43ead631219c87503e43cd` |
| `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/t3-sdd-external-selection-v3/external-selection-plan.json` | 105740 | `845725cb334e6e59916e8862223f83255862d515e4735bc6b39154196085a0af` |
| `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/t3-sdd-external-selection-v3/applicability_matrix.sdd-external-selection-v3.json` | 1064192 | `7282d50f22a4b895eba3614ca47871c8e9fbb2910504fdca361eb84575c6bef1` |
| `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/t3-sdd-external-selection-v3/recipes.sdd-external-selection-v3.json` | 41732 | `911338477386472104a9c2bca34bd34529d8c49d56a8a63b07874530297db732` |
| `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/t3-sdd-external-selection-v3/integrated-mapping.sdd-external-selection-v3.json` | 569619 | `0d16e3946eda57e1924938d43a58d5cf3313c5ebff1bac3ecba03725fe8141ee` |
| `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/t3-sdd-external-selection-v3/fixture-byte-structural-check.json` | 3143 | `3ed1cd1e675b6f1920403ca9ab83b807a53dae81a8e4789b3109e8424cef9ca8` |
| `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/t3-sdd-external-selection-v3/adapter-static-check.json` | 26966 | `72021b294e08c56071ba61fc97d3eca8147ce9a3c605721d7f895830bfdd22aa` |
| `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/t3-sdd-external-selection-v3/selected-suite-real.json` | 144644 | `24f9ccc719ac7c6d60b1c931c263704dc1e4b7f95e0c7c729b8b3d4bdd568d1b` |
| `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/t3-sdd-external-selection-v3/static-fairness-check.json` | 420 | `7ca13edd937183377a1091870acd442075c62df9ef4f37d2ce1d15b5306ad7e7` |
| `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/t3-sdd-external-selection-v3/REPORT.json` | 11742 | `72b8acde4419f7f1241f68e0fec487516ae1b77dffa1d62bff33701ec2dbc67a` |
| `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/t3-sdd-external-selection-v3/sdd-id-migration.external-selection-v3.json` | 1076 | `807c521dbd1e2a695d32dc1a41b603d9048dd60e9c85a7690e38dba2b0aa8f23` |

## Verification

RED observed before implementation:

```text
P2a/.venv/bin/python -m unittest tests.test_sdd_external_selection.SddExternalSelectionV3Tests.test_build_selected_t3_suite_returns_real_suite_without_unselected_transitions -v
AttributeError: module 'sdd_external_selection' has no attribute 'build_selected_t3_suite'
FAILED (errors=1)
```

GREEN/static verification after implementation:

```text
P2a/.venv/bin/python -m unittest discover -s tests -v
Ran 10 tests in 3.526s
OK
```

Artifact generation:

```text
P2a/.venv/bin/python sdd_external_selection.py
status: candidate_static_only
selectedCells: 18
blockedCells: 7
adapterCases: 65
changedMatrixCells: 18
```

Control run preserving v2 tests:

```text
P2a/.venv/bin/python -m unittest discover -s P3/t3-sdd-external-selection-v2/tests -v
Ran 8 tests in 2.848s
OK
```
