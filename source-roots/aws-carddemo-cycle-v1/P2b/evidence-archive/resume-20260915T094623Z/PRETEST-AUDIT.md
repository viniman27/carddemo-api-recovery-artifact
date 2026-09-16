# P2b pre-test readiness audit

Scope: independent source/evidence-grounded audit of `casos/aws-carddemo-cycle-v1/P2b` before any official T1/T2/T3/T4 campaign or comparison. No frozen upstream/corpus/spec edits were made.

Verdict: **NOT READY for official tests yet**.

The P2b smoke evidence does show actual COBOL reachability for all three tracks and source-pin hashes match the pinned corpus files checked in the manifest. However, reporting response construction and malformed/partial capture handling still leave material prerequisites unresolved before readiness claims can be stronger than a bounded technical smoke.

## Verification performed

Commands/run evidence:

- `python3 -m unittest discover -s tests -v` in `P2b`: **PASS**, 3 tests.
- `python3 validate_p2b.py` in `P2b`: **FAIL** under the mandated local `python3` because `yaml` is not installed (`ModuleNotFoundError: No module named 'yaml'`).
- `uv run --with pyyaml --with jsonschema python3 validate_p2b.py` in `P2b`: **PASS**, 4 schema cases valid. This re-wrote `schema-validation-report.json` with the same validation result shape.
- Existing `latest-schema.stdout.json`: records the same 4 schema cases valid and `overall_passed: true`.
- `readiness-manifest.json`: records three smoke HTTP 200 responses and four current run dirs.

Current run attribution verified from `readiness-manifest.json`:

- `runs/posting-9fqne1xr`: `audit.json` exists, `INV.track=posting`, `RESP.status=200`, `program_exit=0`, `reached_cobol=true`; captures include `DALYTRAN` 350 bytes and `TRANFILE.after` 350 bytes.
- `runs/interest-00sakxae`: `audit.json` exists, `INV.track=interest`, `RESP.status=200`, `program_exit=0`, `reached_cobol=true`; captures include `TRANSACT` 350 bytes.
- `runs/reporting-7_v3mkz0`: `audit.json` exists, `INV.track=reporting`, `RESP.status=200`, `program_exit=0`, `reached_cobol=true`; captures include `TRANREPT` 1064 bytes.
- `runs/reporting-source-iadzh2o9`: source run dir exists and contains `TRANSACT`, but no `audit.json`; this is expected from current code because it is an internal reporting source invocation, not a top-level track audit.

COBOL/source hash verification:

- `readiness-manifest.json` pins source root `casos/aws-carddemo-preparation/research-corpus` and commit `59cc6c2fd7ebd7ef7925cad552a01a4b8b6e4d5e`.
- Recomputed hashes match for the three COBOL programs:
  - `app/cbl/CBTRN02C.cbl`: `708f3cadc555acab63f11e2f3238f5372ac7180e6b01197bf960d96bf0d2e83f`
  - `app/cbl/CBACT04C.cbl`: `5084bb8b0c9a0f0199f737487ae1863f12e43cabbdc459a62b6b67bedc683cc4`
  - `app/cbl/CBTRN03C.cbl`: `8691e625502b7efcfd7ba4ae61797132e7b68f3fd5fedcdcc7dd6488f6871eef`

## Findings

### P1 — Reporting response reconstructs detail fields instead of parsing the report artifact

Path/lines:

- `casos/aws-carddemo-cycle-v1/P2b/p2b_binding.py:263-275`
- Evidence artifact: `runs/reporting-7_v3mkz0/TRANREPT`

The reporting path reads the generated `TRANREPT` at lines 269-272 and stores a preview in audit, but the public `records.items[0].value` body at line 275 is built from the source transaction bytes plus literals:

- `accountReference`: hardcoded as `00000000001`
- `typeCode`: hardcoded as `01`
- `typeDescription`: hardcoded as `System transaction`
- `categoryCode`: hardcoded as `0005`
- `categoryDescription`: hardcoded as `Interest charge`
- `amountText`: copied from transaction cents text `00000010000`, not from report text `100.00`

Raw `TRANREPT` record 4 actually contains:

```text
2022071800000001 00000000001 01-System transact 0005-Interest charge               System                 100.00
```

This is not an unsafe unconditional 200, but it is a fabricated/reconstructed response risk: schema validity does not prove that the reported fields came from the report receiver output. Before official tests, reporting output should either be parsed from `TRANREPT` or marked unavailable/diagnostic rather than synthesized from support fixture knowledge.

### P1 — Partial/malformed fixed-width captures can be treated as empty or successful data

Path/lines:

- `casos/aws-carddemo-cycle-v1/P2b/p2b_binding.py:228-232`
- `casos/aws-carddemo-cycle-v1/P2b/p2b_binding.py:244-249`
- `casos/aws-carddemo-cycle-v1/P2b/p2b_binding.py:270-278`

The posting/interest/reporting converters slice fixed offsets without checking that capture length is an exact expected record size (`350` for transaction records, `133` for report records). Empty missing captures become `[]` while `availability` remains `available` in interest (`lines 244, 248`) and reporting (`lines 270, 275`). Reporting returns one reconstructed item regardless of whether `TRANREPT` can be parsed, as long as `reached` is true.

This can hide truncated or malformed partial captures as valid empty or reconstructed responses. Before official testing, malformed capture should be a technical failure or an explicit unavailable state with retained diagnostics, not a 200 body with `available` data.

### P2 — Schema validation is not reproducible with bare project `python3`

Path/lines:

- `casos/aws-carddemo-cycle-v1/P2b/validate_p2b.py:5-6`

`python3 validate_p2b.py` fails because `yaml` is not installed in the active local Python environment. `uv run --with pyyaml --with jsonschema python3 validate_p2b.py` passes, so the saved schema evidence is credible only when the dependency invocation is recorded. Add a pinned/recorded dependency command or script wrapper before using schema validation as a routine gate.

### P2 — Smoke process lifecycle is acceptable for this bounded slice but not yet a production-service claim

Path/lines:

- `casos/aws-carddemo-cycle-v1/P2b/p2b_binding.py:324-354`
- Evidence artifact: `server-lifecycle.json`

The smoke subprocess is terminated in `finally`; `server-lifecycle.json` shows `returncode: 0`, empty stdout/stderr for the current smoke. This is adequate for technical smoke cleanup. It does not establish production service lifecycle, concurrent serving, or long-running state safety.

### P2 — Server is single-threaded and shared build/log files are mutable global state

Path/lines:

- `casos/aws-carddemo-cycle-v1/P2b/p2b_binding.py:36`
- `casos/aws-carddemo-cycle-v1/P2b/p2b_binding.py:115-125`
- `casos/aws-carddemo-cycle-v1/P2b/p2b_binding.py:183-203`
- `casos/aws-carddemo-cycle-v1/P2b/p2b_binding.py:316-321`

Per-invocation dirs isolate COBOL file state (`tempfile.mkdtemp` at lines 211-213), but `build()`, `COMMAND_LOG`, `build-report.json`, `server.port`, `server-access.log`, `readiness-manifest.json`, and `schema-validation-report.json` are mutable root-level artifacts. `HTTPServer` is single-threaded. This is acceptable for one smoke run, but readiness claims must not imply concurrent/state-isolated service behavior.

### P2 — Support fixtures include expected descriptive values; public responses must not use them as oracle output

Paths/lines:

- `casos/aws-carddemo-preparation/expanded-batch/support/report_fixture.cbl:25-27`
- `casos/aws-carddemo-preparation/expanded-batch/support/intcalc_fixture.cbl:34`
- `casos/aws-carddemo-cycle-v1/P2b/p2b_binding.py:275`

Support setup necessarily seeds card/type/category descriptors. That is acceptable for technical reachability, but line 275 currently promotes those known descriptor values into the public reporting response without parsing `TRANREPT`. This crosses from fixture setup into response reconstruction. Keep support fixture values out of expected-output assertions and public response synthesis unless the response field is directly captured from COBOL output.

### P3 — Internal/public boundary for 109 and fee/suffix fields preserved in inspected P2b code

Evidence:

- `P2a/openapi-carddemo-stage6r3.yaml:455-465` keeps posting preliminary rejections to `100`-`103` and notes `109` remains internal.
- `P2a/openapi-carddemo-stage6r3.yaml:646` notes no fee/suffix public fields for interest.
- Searches in P2b code did not find public `109`, fee, suffix, or new public semantics.

### P3 — Source-pin verification is non-empty and path-based, but not an authenticated git checkout proof

Path/lines:

- `casos/aws-carddemo-cycle-v1/P2b/p2b_binding.py:131-146`

`verify_source_pins()` recomputes hashes for existing manifest paths and confirmed checked files match. It does not independently prove the source root is a clean git checkout at the pinned commit. For P2b technical smoke this is acceptable; for publication/official replay, add explicit git/object provenance or package manifest verification as a separate gate.

## Readiness checklist before official tests

- [x] P2a frozen OpenAPI file present and schema references resolve under dependency-managed validation.
- [x] Three smoke responses recorded with HTTP 200 in `readiness-manifest.json`.
- [x] Current run dirs attributed to this smoke via set-difference guard and verified on disk.
- [x] COBOL reachability stronger than HTTP 200 verified through `audit.json` `program_exit=0`, `reached_cobol=true`, and non-empty captures for all three top-level tracks.
- [x] Recomputed hashes match the pinned COBOL program source files used by the manifest.
- [x] No public `109`, fee, suffix, or new public semantic fields found in inspected P2b response code.
- [ ] Reporting public response must be derived from `TRANREPT` bytes or explicitly unavailable; current response is reconstructed from transaction/support literals.
- [ ] Fixed-width converters must reject or diagnose malformed/truncated captures instead of exposing `available` empty/reconstructed items.
- [ ] Schema validation command/dependencies must be recorded so `python3 validate_p2b.py` is not a hidden environment failure.
- [ ] Readiness language must stay bounded to technical smoke; no official test, semantic oracle, comparison, coverage, durability, or production-service claim.

## Recommendation

Do **not** proceed to official P2b/P3 readiness claims or official T1/T2/T3/T4 tests until the two P1 defects are fixed with failing-then-passing P2b tests:

1. a reporting test proving response detail fields are parsed from `TRANREPT` rather than reconstructed from `TRANSACT`/fixture constants;
2. a malformed/truncated capture test proving the facade returns technical failure or unavailable diagnostics instead of a 200 available empty/reconstructed body.

No broad rewrite is recommended. The existing per-invocation COBOL harness and smoke artifacts are useful; the next prerequisite work should be narrow converter hardening plus dependency-recording for schema validation.
