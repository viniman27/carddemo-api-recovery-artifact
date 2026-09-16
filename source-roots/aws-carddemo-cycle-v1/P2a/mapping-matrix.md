# P2a Traceability Mapping Matrix

- Stage 6 r3: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md` SHA-256 `6cba102f8335843b46e75a77b1a71d4e56373a95d5ac63cf645491556c443b27`
- Stage 7 r2: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/sdd-runs/E3-01/specs/adapter-behavior-carddemo-r2/requirements.md` SHA-256 `b53c471116dfa0c3831fc810964bddca3eb1fa0d3b8e7d459181ba71e54b3d8f`

| Artifact element | Source/clause | Mapping note |
|---|---|---|
| `PostingRequest` | `sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md §3.4 Requests/D-14/C-9` | Required empty closed JSON object; missing body/null/array/properties invalid |
| `InterestRequest` | `sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md §3.4 Requests/D-14/C-9` | Required empty closed JSON object; missing body/null/array/properties invalid |
| `ReportingRequest` | `sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md §3.4 Requests/D-14/C-9` | Required empty closed JSON object; missing body/null/array/properties invalid |
| `PostingCandidate` | `sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md §3.2/C-5` | Posting candidate/source daily fields |
| `PostingTransaction` | `sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md §3.2/C-5` | Prepared posted transaction fields |
| `PostingRejection` | `sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md §3.2/C-5` | Posting rejection content |
| `PostingProgress` | `sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md §3.2/C-5/D-16` | Progress counts; not committed/durable output counts |
| `InterestCategoryBasis` | `sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md §3.2/C-6` | External description only; not request |
| `InterestIdentifierBasis` | `sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md §3.2/C-6` | External identifier basis only; not request |
| `GeneratedInterestTransaction` | `sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md §3.2/C-6` | Generated interest transaction fields; no fee/suffix public |
| `ReportingTransactionBasis` | `sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md §3.3` | External description only; not request |
| `ReportingDateBasis` | `sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md §3.3` | External date basis only; not request |
| `ReportDetail` | `sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md §3.3/C-7` | Report receiver detail fields |
| `ReportHeaderContext` | `sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md §3.3/C-7` | Report header context |
| `ReportTotal` | `sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md §3.3/C-7/C-8` | Report total occurrence |
| `ReportRecord` | `sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md §3.4/C-7/C-8/D-15` | Mixed ordered reporting records union |
| `PostingTransactionAvailability` | `sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md §3.4/D-15/D-16` | PostingTransactionAvailability availability oneOf; unavailable items forbidden |
| `PostingRejectionAvailability` | `sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md §3.4/C-5/D-16` | PostingRejectionAvailability availability oneOf; unavailable items forbidden |
| `InterestOutputAvailability` | `sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md §3.4/C-6/D-16` | InterestOutputAvailability availability oneOf; unavailable items forbidden |
| `ReportRecordAvailability` | `sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md §3.4/C-8/D-16` | ReportRecordAvailability availability oneOf; unavailable items forbidden |
| `ProgressAvailability` | `sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md §3.4/C-5/D-16` | Posting progress availability |
| `PostingEnvelope` | `sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md §3.4/D-16/C-10/C-12` | Posting envelope; any available outputs/rejections/progress required for 200 |
| `InterestEnvelope` | `sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md §3.4/D-16/C-11/C-12` | Interest envelope; outputs available required for 200 |
| `ReportingEnvelope` | `sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md §3.4/D-16/C-8/C-12` | Reporting envelope; records available required for 200 |
| `PostingInterfaceError` | `sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md §3.4/§5/C-12/D-13/D-16` | posting error envelope; known failure 500 precedence; no internal diagnostics |
| `InterestInterfaceError` | `sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md §3.4/§5/C-12/D-13/D-16` | interest error envelope; known failure 500 precedence; no internal diagnostics |
| `ReportingInterfaceError` | `sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md §3.4/§5/C-12/D-13/D-16` | reporting error envelope; known failure 500 precedence; no internal diagnostics |
| `InterfaceError` | `sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md §3.4/§5/C-12` | Track-specific interface errors |
| `posting /posting` | `sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md C-1/C-5/C-9/C-10/C-12-C-14` | posting operation; no selector/reset/polling/telemetry/default business fields |
| `interest /interest` | `sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md C-2/C-6/C-9/C-11-C-14` | interest operation; no selector/reset/polling/telemetry/default business fields |
| `reporting /reporting` | `sdd-runs/E3-01/specs/api-contract-carddemo-r3/requirements.md C-3/C-7-C-9/C-12-C-14` | reporting operation; no selector/reset/polling/telemetry/default business fields |
