# Complementary cross-arm v1 STATUS

Scope: bounded prospective local cross-arm complement over 7 contracts × 3 public tracks. This is not an official campaign and does not promote T1/T2/T3/T4 evidence.

Run: `run-20260916T112642Z`

Verified outcomes:

- Frozen input pins written before execution: contracts, campaign config, T3 binding-closure candidates, MBT registry, runner/checker sources.
- Materialized one source-guided positive case per contract × track: 21 cases total.
- Executed exactly 21 local API attempts, one attempt per case, no retries, no external calls.
- HTTP/contract structural comparison: 21/21 schema-valid documented 200 responses.
- Local byte-effect comparison: 21/21 observed concrete COBOL output bytes for the expected track artifact:
  - posting: non-empty `TRANFILE.after`
  - interest: non-empty `TRANSACT`
  - reporting: non-empty `TRANREPT`
- Measurement: runner reported 21/21 admissible preparatory measurements; no stop-policy failure and no structural violations.

Limits:

- The byte-effect checker is intentionally bounded and does not claim full semantic equivalence or full obligation coverage.
- Existing T1/T2 status remains historical/unchanged; no new external T1 send was performed.
- Original campaign packages and historical outputs were preserved; this run used a new output directory only.
- Future official design still requires explicit input/generation authorization and official suite freeze.

Primary artifacts:

- `freeze/input-freeze.json`
- `freeze/suite.freeze.json`
- `freeze/materialization-manifest.json`
- `run/campaign-report.json`
- `comparison.json`
- `RUN-SUMMARY.json`
