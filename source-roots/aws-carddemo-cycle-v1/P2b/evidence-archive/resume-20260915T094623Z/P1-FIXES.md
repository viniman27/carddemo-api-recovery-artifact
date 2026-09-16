# P2b P1 fixes — technical validation report

Scope: P2b-only fix for the two P1 pretest audit defects. No official T1/T2/T3/T4 tests or oracle/comparison runs were executed.

## Outcomes

- Fixed reporting conversion so public `records.items` are parsed from actual `TRANREPT` 133-byte receiver records, not reconstructed from `TRANSACT` or fixture literals.
- Fixed fixed-width capture framing for all three tracks:
  - posting/interest transaction captures require 350-byte record framing;
  - reporting captures require 133-byte record framing;
  - missing capture => 503 `content_unavailable`;
  - positively observed empty capture => 200 available `items: []`;
  - truncated/malformed/unreadable/stale known capture failure => 500 `technical_failure`, with supported partial content only when actually available.
- Added conversion provenance into audit `CONV.field_mappings`, including fixed-width source spans and raw report record classifications.
- Preserved mixed reporting record order/multiplicity for mapped header/detail/total records; retained raw evidence/classification for blank, rule/header-row, and unknown unmapped report lines in audit evidence.
- Preserved public guard against internal `109`, fee, and suffix fields.

## Files modified/created

- Modified: `P2b/p2b_binding.py`
- Modified: `P2b/tests/test_p2b_contract.py`
- Created: `P2b/P1-FIXES.md`
- Created: `P2b/p2b-p1-fixes-manifest.json`
- Created archive snapshot before new smoke: `P2b/evidence-archive/20260914T154000Z/archive-manifest.json`

## TDD evidence

RED was observed with the new tests before implementation:

```text
python3 -m unittest discover -s tests -v
FAILED (errors=5)
missing attributes: fixed_capture_status, parse_transaction_records, empty_available_body, parse_report_records
```

GREEN/unit QA after implementation:

```text
python3 -m unittest discover -s tests -v
Ran 8 tests in 0.045s
OK
```

New tests cover:

- report bytes mutation proving response follows raw `TRANREPT` bytes, not fixture/source literals;
- report mixed header/detail/detail/total order and duplicate preservation;
- unknown/unmapped report line raw evidence classification;
- missing/truncated/malformed/empty capture status mapping for posting, interest, reporting;
- 350-byte posting/interest record framing and multiple ordered transaction records;
- public guard for internal reason `109`, fee, suffix.

## Real smoke/schema evidence

Commands run from `casos/aws-carddemo-cycle-v1/P2b`:

```bash
python3 -m unittest discover -s tests -v
python3 p2b_binding.py smoke > latest-smoke.stdout.json
../P2a/.venv/bin/python validate_p2b.py > latest-schema.stdout.json
```

Schema validator reproducible command:

```bash
cd "casos/aws-carddemo-cycle-v1/P2b" && ../P2a/.venv/bin/python validate_p2b.py
```

Results:

- `latest-schema.stdout.json`: `overall_passed: true`, all 4 schema cases valid.
- `readiness-manifest.json`: posting, interest, reporting all HTTP 200 in isolated smoke.
- New audit dirs:
  - `runs/posting-g5ezlm2o/audit.json`: status 200, `program_exit=0`, `reached_cobol=true`, `TRANFILE.after` 350-byte framing available.
  - `runs/interest-nbc10dm1/audit.json`: status 200, `program_exit=0`, `reached_cobol=true`, `TRANSACT` 350-byte framing available.
  - `runs/reporting-9h4tknw3/audit.json`: status 200, `program_exit=0`, `reached_cobol=true`, `TRANREPT` 1064 bytes = 8 x 133-byte records.

Observed reporting public response is now report-derived:

- header from `TRANREPT`: `DALYREPT`, `Daily Transaction Report`, date range `2026-09-14` to `2026-09-14`;
- detail from `TRANREPT`: `typeDescription` is emitted/truncated as `System transact`, and `amountText` is formatted as `100.00`;
- totals from `TRANREPT`: page and grand totals are emitted as `+        200.00`.

Audit retained unmapped raw report lines with classifications: `known_blank`, `known_unmapped_header_row`, `known_unmapped_rule`.

## Source/hash preservation

`readiness-manifest.json` continues to pin source commit `59cc6c2fd7ebd7ef7925cad552a01a4b8b6e4d5e` and verified source hashes, including:

- `app/cbl/CBTRN02C.cbl`: `708f3cadc555acab63f11e2f3238f5372ac7180e6b01197bf960d96bf0d2e83f`
- `app/cbl/CBACT04C.cbl`: `5084bb8b0c9a0f0199f737487ae1863f12e43cabbdc459a62b6b67bedc683cc4`
- `app/cbl/CBTRN03C.cbl`: `8691e625502b7efcfd7ba4ae61797132e7b68f3fd5fedcdcc7dd6488f6871eef`
- `app/cpy/CVTRA07Y.cpy`: `72ba597b1a40e1e6cf908e15da9e6a818a0ab899ef1d27d15edeb074963102fa`

## Residuals / readiness boundary

- Still not an official T1/T2/T3/T4 run.
- No oracle/comparative analysis, coverage claim, production lifecycle/concurrency claim, or P2/P3 human gate approval claimed.
- Reporting exposes only fields physically representable in the frozen contract; unmapped physical lines remain in audit evidence because the frozen public union has no unknown-line variant.
