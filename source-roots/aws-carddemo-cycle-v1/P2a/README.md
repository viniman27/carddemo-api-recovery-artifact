# P2a — OpenAPI materialization and binding plan

Status: working artifact created under Cycle/P2a only. It is a mechanical OpenAPI 3.1 materialization of approved Stage 6 r3 plus a documentary binding plan derived from Stage 7 r2. It is not an API server, adapter implementation, COBOL execution, official experiment, or runtime fidelity claim.

## Files

- `openapi-carddemo-stage6r3.yaml` / `.json` — OpenAPI 3.1 contract for `POST /posting`, `POST /interest`, `POST /reporting`.
- `traceability.json` — machine-readable source mapping and input hashes.
- `mapping-matrix.md` — separate traceability matrix.
- `plan-binding.md` — INV/RES/CAP/CONV/FAIL/STATE/RESP duties and pending choices.
- `validate_p2a.py` — structural/schema QA script.
- `validation-report.json` — validator commands, outputs, synthetic case results, before/after hashes.

## Limitations

- Required requests are closed empty JSON objects; body absence remains invalid by OpenAPI `requestBody.required`, not a business input policy.
- Ordered arrays are used throughout; no set/keymap representation or deduplication is introduced.
- `not_attested`, `unknown`, and `unavailable` are preserved as contract constants/variants only; they are not runtime facts.
- Authentication/authorization is unspecified, not declared absent.
- No selectors, upload/provisioning, reset, polling, retry, idempotency, telemetry, reason 109, file status, units, calendar, numeric coercion, durability, or complete reporting guarantee is added.
- No COBOL/support outputs were read or executed.
