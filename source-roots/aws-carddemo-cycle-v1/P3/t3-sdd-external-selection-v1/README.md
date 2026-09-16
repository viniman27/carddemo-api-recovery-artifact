# T3 SDD external selection v1

Status: `candidate_static_only`; official campaign/suite generated: false; business runtime/HTTP: not executed.

This package closes the local modeling distinction between the SDD public `request {}` and T3 data selection. Selection is represented outside the request by `fixtureId`; the SDD body remains the closed empty object required by P2a.

## Outputs

- `external-selection-plan.json` — fixtureId-level selection plan with source → resource → guard reasons for SDD obligations.
- `applicability_matrix.sdd-external-selection-v1.json` — versioned copy of the matrix with SDD-only external-selection annotations/classification corrections; upstream v3 is untouched.
- `recipes.sdd-external-selection-v1.json` — versioned copy with SDD empty-request recipes bound to external fixture selection.
- `integrated-mapping.sdd-external-selection-v1.json` — adapter-local enriched plan consumed by the real T3 adapter functions.
- `sdd-id-migration.external-selection-v1.json` — explicit versioned matrix-ID to registry-ID proof for this copied package; not an upstream alias.
- `fixture-byte-structural-check.json` — structural byte/hash check for fixture package resources; no business execution.
- `adapter-static-check.json` — synthetic/static adapter integration proof: 68 candidate cases, every SDD request body `{}`.
- `static-fairness-check.json` — SDD/non-SDD control check: non-SDD cells are not marked with external selection authority, and SDD blocked cells without authority remain ineligible.
- `REPORT.json` — aggregate report and remaining blockers.

## Verification

```bash
cd "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1"
PYTHONDONTWRITEBYTECODE=1 P2a/.venv/bin/python -m unittest discover -s P3/t3-sdd-external-selection-v1/tests -v
PYTHONDONTWRITEBYTECODE=1 P2a/.venv/bin/python P3/t3-sdd-external-selection-v1/sdd_external_selection.py
```

Observed unit test result: 5 tests, OK. Structural fixture check: PASS for 18 files, no mismatches.
