# Complementary reporting essential v1

Status: local P3 package only. It does not edit original COBOL, P2b API binding, contracts, campaign packages, main study files, or prior P3 packages.

Purpose: execute essential TRANREPT/CBTRN03C complementary reporting cases with source-grounded date, grouping, pagination and totals partitions. Final report totals are deliberately qualified as `inconclusive-eof-branch` because the source EOF path adds the last `TRAN-AMT` before writing page/grand totals; raw bytes are preserved for review instead of converting that behavior into an oracle.

## Run

```bash
python3 -m unittest discover -s tests -v
python3 reporting_essential.py --run
```

## Outputs

- `evidence/frozen-inputs/*/freeze-manifest.json` — physical fixture bytes, hashes, expected input partitions, source facts.
- `evidence/p2b-runs/*/audit.json` — real local API/COBOL invocation audits using `{}` request bodies and external local fixture selection.
- `evidence/raw-report-outputs/*.TRANREPT.bin` — raw 133-byte report output files copied from each run.
- `evidence/raw-report-outputs/*.parsed.json` — parser output preserving raw record order/multiplicity and unknown records.
- `evidence/reporting-essential-results.json` — case results and qualifications.
- `evidence/obligation-partition-matrix.json` — eight explicitly scoped obligation partitions; not a counts proxy.
