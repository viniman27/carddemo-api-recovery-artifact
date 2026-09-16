# P2b final pretest readiness audit
Scope: final P2b acceptance audit after P1 fixes, bounded to technical pretest readiness. No official T1/T2/T3/T4 cells, E1/E2 comparisons, evaluation quarantine outputs, source/spec/contract/corpus edits, or semantic oracle results were produced.
## Verdict

**Technical P2b smoke is acceptable as pretest evidence, but official testing remains blocked on P3 protocol approval.** The narrow P1 runtime defects are fixed and verified; the remaining blockers are methodological/protocol gates, not a new runtime failure found here.
## What changed in this final audit

- Added a narrow TDD regression for unknown meaningful `TRANREPT` records that previously could become `200` with `records.items: []`.
- Updated `p2b_binding.py` so report captures containing only unknown meaningful non-empty records classify as `unmapped_meaningful` and return `500 technical_failure` rather than silently reporting an available empty sequence.
- Preserved prior evidence before rerunning smoke: `P2b/evidence-archive/20260914T200843Z/archive-manifest.json`.
## Real verification results

- `python3 -m unittest tests.test_p2b_contract.P2bContractTests.test_unknown_meaningful_report_only_is_not_silent_available_empty_200 -v` — RED before fix, then PASS after fix
- `python3 -m unittest discover -s tests -v` — PASS 9 tests
- `python3 p2b_binding.py smoke > latest-smoke.stdout.json && ../P2a/.venv/bin/python validate_p2b.py > latest-schema.stdout.json` — PASS exit 0; schema warning only (jsonschema RefResolver deprecation)

Schema validation used the dependency-managed command mandated by the current P2b evidence: `../P2a/.venv/bin/python validate_p2b.py`; all four cases are valid.

## Current smoke attribution

- Smoke manifest: `P2b/readiness-manifest.json`, started `2026-09-14T20:08:51Z`.
- `interest`: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P2b/runs/interest-r9ug5z7z`; audit `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P2b/runs/interest-r9ug5z7z/audit.json`; HTTP/status `200`, `program_exit=0`, `reached_cobol=true`; captures TRANSACT 350 bytes sha256 69c77ff39f36aed5....
- `posting`: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P2b/runs/posting-_2obkukj`; audit `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P2b/runs/posting-_2obkukj/audit.json`; HTTP/status `200`, `program_exit=0`, `reached_cobol=true`; captures TRANFILE.seed 0 bytes sha256 e3b0c44298fc1c14..., TCATBALF.seed 0 bytes sha256 e3b0c44298fc1c14..., ACCTFILE.seed 300 bytes sha256 a4c2b21f75787ebd..., XREFFILE.seed 50 bytes sha256 ad894f02c91d427a..., DALYTRAN 350 bytes sha256 8e58b42b598dd048..., TRANFILE.after 350 bytes sha256 9746aa4303a905a9..., XREFFILE.after 50 bytes sha256 ad894f02c91d427a..., ACCTFILE.after 300 bytes sha256 401a58e5971c5bba..., TCATBALF.after 50 bytes sha256 4c867452904c67bf..., DALYREJS 0 bytes sha256 e3b0c44298fc1c14....
- `reporting`: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P2b/runs/reporting-ipoj4c8j`; audit `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P2b/runs/reporting-ipoj4c8j/audit.json`; HTTP/status `200`, `program_exit=0`, `reached_cobol=true`; captures TRANREPT 1064 bytes sha256 4d78f75c0d14aaff....

`reporting-source-qy1m3p1u` is an internal source invocation directory for the reporting setup and intentionally has no top-level audit.

## Audit findings

- Report parsing: current reporting response is derived from actual `TRANREPT` bytes. The audit records 1064 bytes = 8 × 133-byte records, classifications `header`, `known_blank`, `known_unmapped_header_row`, `known_unmapped_rule`, `detail`, `total`, `known_unmapped_rule`, `total`, and source spans for each record.
- Missing/truncated/error precedence: unit QA verifies missing capture → `503 content_unavailable`; positively observed empty capture → `200` with empty items; truncated/malformed capture → `500 technical_failure`; unknown meaningful report-only capture → `500 technical_failure`.
- Unmapped presentation lines: known blank/header/rule lines are retained in audit evidence and excluded from the public union because the frozen public schema has no presentation-line variant.
- Unmapped meaningful records: no longer silently become `200` empty when they are the only observed report content; they are a technical failure with retained classification evidence. Mixed reports with known public records and known presentation separators remain `200` in current smoke.
- Source pins: `readiness-manifest.json` records commit `59cc6c2fd7ebd7ef7925cad552a01a4b8b6e4d5e`; checked source hashes include `CBTRN02C`, `CBACT04C`, `CBTRN03C`, COPYs/JCL/proc. This is hash evidence for the local pinned corpus, not an independent clean-checkout attestation.
- Lifecycle: `server-lifecycle.json` has `returncode: 0`, empty stdout/stderr after the bounded smoke. This supports cleanup for the local smoke only, not production service/concurrency.

## Protocol prerequisite gaps

The approved protocol still requires P3 freeze/authorization before official cells: official fixtures and data exposure, reset/isolation per case or sequence, capture channels/freshness/framing, conversion/oracle authority, T1/T2/T3/T4 budgets/seeds/order/union, and analysis rules. These were inspected in `PROTOCOLO.md` and `P2a/plan-binding.md`; they are not satisfied by smoke success.

## Checklist status

See machine-readable checklist: `P2b/final-pretest-checklist.json`. Summary:

- **done** `previous_failed_transcript_inspected` — Read <REDACTED_LOCAL_PATH>/.run-cache/aux-ff83df32/task-0.log: stopped at HTTP 429 after reading current P2b files; no completed final report/checklist left behind.
- **done** `old_evidence_preserved_before_rerun` — Archived previous smoke/schema/lifecycle/run evidence at P2b/evidence-archive/20260914T200843Z/archive-manifest.json before rerunning because runtime code changed.
- **done** `unit_tdd_unknown_report_guard` — RED observed for test_unknown_meaningful_report_only_is_not_silent_available_empty_200: expected unmapped_meaningful but current classification was available; GREEN all 9 tests pass.
- **done** `report_parsing_actual_capture` — New reporting smoke audit parses TRANREPT 1064 bytes as 8 x 133-byte records; public detail amountText=100.00 and typeDescription=System transact come from report bytes; audit retains sourceSpanEvidence.
- **done** `missing_truncated_error_precedence` — Unit tests cover missing=>503, known empty=>200 empty, truncated/malformed=>500 technical_failure for posting/interest/reporting; unknown meaningful report-only=>500, not 200 empty.
- **done** `unmapped_presentation_records` — Actual reporting audit classifies known_blank, known_unmapped_header_row, known_unmapped_rule as retained audit evidence and excludes them from public schema by known presentation classification.
- **done** `unmapped_meaningful_records` — Narrow runtime fix: report captures containing only unknown meaningful non-empty records classify framing as unmapped_meaningful and map to 500 technical_failure with evidence, preventing silent available empty 200.
- **done** `smoke_attribution_actual_source_hashes` — readiness-manifest current_run_dirs identify posting-_2obkukj, interest-r9ug5z7z, reporting-ipoj4c8j plus internal reporting-source-qy1m3p1u; top-level audits show program_exit=0 and reached_cobol=true; source commit 59cc6c2f... and checked hashes recorded.
- **done** `schema_qa` — ../P2a/.venv/bin/python validate_p2b.py > latest-schema.stdout.json: overall_passed true, posting/interest/reporting envelopes plus InterfaceError valid.
- **blocked** `official_T1T2T3T4` — No official T1/T2/T3/T4 was run or generated in this task.
- **blocked** `approved_protocol_prerequisites` — Protocol lines 36-43 and 53-61 require P3 freeze of T1/T2/T3/T4 inputs, reset, capture, conversion/oracle rules and human gate; technical smoke does not approve those.
- **unverified** `semantic_oracle_comparison_coverage` — No oracle/comparative analysis, E1/E2 comparison, evaluation quarantine output, coverage, durability, or production concurrency was executed or claimed.

## Concrete next gate

Proceed only to **P3 human freeze/authorization** of official fixtures, reset policy, capture/conversion/oracle rules, T1/T2/T3/T4 budgets/seeds/order/union and analysis plan. Do not start official cells from this smoke alone.
