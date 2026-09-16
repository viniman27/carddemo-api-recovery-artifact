# complementary-reporting-source-extractor-v1

Status: source-qualified read-only reporting checks over the preserved seven cross-arm reporting cases.

- Cases checked: 7
- Case verdicts: {'pass': 7}
- Obligation verdicts: {'pass': 14, 'not_exercised': 7, 'not_observable': 7}
- Pin verification failures: 0
- Separation: legacy EOF behavior is reported separately from financial correctness; missing totals with a non-selected stale EOF guard are `not_exercised`, not correct totals.
- Oracle boundary: expected detail values come from actual DATEPARM/TRANFILE/support input bytes and COBOL/JCL source anchors, not from API reruns or report-output-derived expectations.
