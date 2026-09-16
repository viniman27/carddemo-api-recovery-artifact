# Complementary validation runtime v1

Status: bounded local integration qualification, not an official campaign and not T1/T2/T3/T4.

This package connects the existing `P3/complementary-validation-implementation-v1` semantic checkers to actual isolated localhost API calls that invoke the current qualified P2b COBOL binding for three essential tracks: posting, interest and reporting.

## What is frozen and executed

- Frozen local physical fixture inputs: `evidence/frozen-inputs/freeze-manifest.json`
- Raw HTTP request/response bytes: `evidence/raw-http/`
- Per-track API/COBOL run workdirs and audits: `evidence/api-cobol-runs/`
- Typed observations extracted from raw files/audits only: `evidence/typed-observations.json`
- Semantic checker output: `evidence/semantic-check-results.json`
- Runtime summary: `evidence/runtime-summary.json`

## Re-run

```bash
../../P2a/.venv/bin/python -m unittest discover -s tests -v
../../P2a/.venv/bin/python run_runtime_cases.py
```

## Current result

Latest run completed with `semanticCheckerReturncode: 0`.

Semantic result counts:

- pass: 6
- failed: 2
- pending: 17

Observed passes:

- `POSTTRAN-OBL-003` accepted posting copies daily fields and regenerates processing timestamp.
- `POSTTRAN-OBL-004` missing-card rejection reason 100 and no posted transaction for that candidate.
- `POSTTRAN-OBL-006` reject record plus reject-count return code.
- `INTCALC-OBL-005` nonzero-rate monthly interest and zero-rate no-write partition.
- `INTCALC-OBL-006` written interest transaction fields.
- `TRANREPT-OBL-002` inclusive date partition for the observed detail.

Observed failures / boundaries:

- `POSTTRAN-OBL-009` failed because the available write trace proves `TRANFILE` and reject writes, but not `TCATBAL`/`ACCOUNT` ordering. This is intentionally not promoted to pass without trace evidence.
- `TRANREPT-OBL-006` failed because the observed report contains the detail line but no page/account total lines; no totals were synthesized from expected arithmetic.

No expected output fields are inserted as observed data. Expected values in checker details come only from source-grounded checker logic, while `details.observed` comes from raw API/COBOL artifacts.
