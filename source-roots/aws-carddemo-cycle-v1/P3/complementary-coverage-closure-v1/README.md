# complementary-coverage-closure-v1

Read-only final coverage/acceptance ledger for AWS CardDemo P3.

## Reusable command for the current preserved evidence

Run from this directory:

```bash
python3 final_coverage_ledger.py \
  --catalog ../complementary-validation-v2/scenario-catalog.json \
  --semantic-results ../complementary-crossarm-semantic-v1/latest/results.json \
  --semantic-results ../complementary-interest-source-extractor-v1/latest/results.json \
  --semantic-results ../complementary-reporting-source-extractor-v1/latest/results.json \
  --semantic-results ../complementary-posting-essential-v1/evidence/posting-essential-report.json \
  --semantic-results ../complementary-reporting-essential-v1/evidence/reporting-essential-results.json \
  --supplemental-results ../complementary-interest-essential-v1/evidence/rates-specific-default-zero/result.json \
  --supplemental-results ../complementary-interest-essential-v1/evidence/single-final-eof/result.json \
  --model-registry ../complementary-mbt-binding-v1/latest/candidate-registry.json \
  --coverage-report ../coverage-report-reconciliation-v1/coverage-reconciliation-report.json \
  --campaign-coverage-csv ../official-analysis-v1/coverage_union_by_contract_condition_track.csv \
  --out-dir evidence/current
```

Outputs:

- `evidence/current/acceptance-ledger.json` — machine-readable accounting ledger.
- `evidence/current/final-coverage-report.md` — concise PT-BR report generated from the ledger.

## Policy enforced by the script

- Semantic denominator is the 175 applicable obligation×contract cells from catalog v2, not the 525 gross obligation×operation cells.
- `not_exercised` stays inside the denominator; N/A is only for other-track cells outside it.
- Original cross-arm observations require `contractId` + `operationId`; supplemental essential evidence is reported separately and never silently fills future campaign cells.
- Gcov line/branch counts are comparable only for the same main generated-C fingerprint/denominator.
- Structural/API success is not promoted to semantic PASS without checker evidence.
