# suite-adapters-preflight-v1

Preflight-only adapters for preparing P3 suite surfaces against the existing `campaign-harness-v2` `Case`/`Suite` model.

## Scope

Implemented:

- T1 preserved-response importer: reads a frozen text response, extracts explicit JSON only, preserves the raw response and source hash, does not call a model, and does not repair omissions.
- T2 frozen-request importer: reads already-frozen offline request JSON, performs no HTTP and preserves body distinctions (`absent`, present empty bytes, JSON `{}`).
- T3 external-path importer: accepts externally materialized HTTP paths; abstract transition IDs without business-request mapping are blocked explicitly.
- Real operation inventory from pinned contracts: reads the six E1/E2 original response contracts plus the SDD Stage6r3 OpenAPI contract and counts operations programmatically.
- Synthetic freeze/load/union qualification through `campaign-harness-v2`.

Not implemented / not claimed:

- no AWS generation or official campaign execution;
- no T1 generator and no LLM call;
- no T2 fuzzer/generator for AWS contracts;
- no T3 oracle access or business-request conversion from abstract IDs;
- no official gate enabled.

## Files

- `src/suite_adapters.py` — adapter library.
- `suite_adapters_cli.py` — preflight-only CLI; `--mode` accepts only `preflight`.
- `tests/test_suite_adapters.py` — synthetic adapter tests.
- `evidence-real-preflight-20260915T-synthetic/` — real generated evidence for this delivery.

## Real evidence produced

Command run from this directory:

```bash
python3 -m unittest discover -s tests -v
python3 suite_adapters_cli.py --mode preflight --output evidence-real-preflight-20260915T-synthetic
```

Observed results:

- Unit tests: 5 tests ran and passed with the existing P3 fuzz preflight venv (`unittest-p3venv.exit` = `0`). A system `python3` run also passed (`unittest.exit` = `0`).
- CLI preflight generated evidence without AWS/model/API-business calls.
- Programmatic inventory verification passed (`programmatic-verification.json` has `allPass: true`).
- Real contracts read: 7.
- Real operations inventoried by parser: 21.
- Synthetic union cases after duplicate handling: 3.
- Official CLI mode remains unavailable (`cli-official-blocked.exit` = `2`).

## Contract pins read

The generated `contract-pins.json` pins bytes and SHA-256 for:

- `E1-1` — `collection-01/E1-1/response-original.txt`
- `E1-2` — `collection-01/E1-2/response-original.txt`
- `E1-3` — `collection-01/E1-3/response-original.txt`
- `E2-1` — `collection-01/E2-1/response-original.txt`
- `E2-2` — `collection-01/E2-2/response-original.txt`
- `E2-3` — `collection-01/E2-3/response-original.txt`
- `E3-01-SDD-stage6r3` — `P2a/openapi-carddemo-stage6r3.yaml`

`programmatic-verification.json` re-read those files and confirmed that each recorded byte count and SHA-256 matches the current file.

## Pending blockers before official use

- Approve the concrete T1 outbound package before any model call.
- Define schema/mapping for the actual T1 preserved-response format if it is not explicit JSON objects/lists.
- Produce/freeze official T2 requests externally; this importer only loads them offline.
- Provide T3 business-request mappings from independent MBT paths to each contract surface; abstract IDs remain blocked.
- Define operation-specific fixture package applicability and non-expressable/non-mapped classifications.
- Add official structural/schema checkers and result interpretation policy.
- Create a concrete freeze manifest and human decision before enabling any official runner/gate.
