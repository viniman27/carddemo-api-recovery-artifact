# T3 mapper preparation v1 — report

## Outcome

Implemented a preparation-only T3 mapper that converts BFS path + explicit mapping + external fixture evidence into harness `HttpRequestSpec` / `Suite` cases, with OpenAPI schema validation and fail-closed blocking.

No official AWS suite, official case, expected result, oracle, runtime output, COBOL/API call, or model call was created.

## Implemented API

- `FixtureIndex.from_manifest(...)`: loads candidate fixture metadata and bindings.
- `build_request_from_explicit_mapping(mapping, fixture_index, openapi)`: builds a request only from concrete selectors.
- `bfs_map_model_to_suite(...)`: maps model transitions through explicit mapping cells; insufficient cells produce per-cell `blocked_reason`.
- `validate_request_against_openapi(...)`: validates the generated request body against the supplied original OpenAPI request schema.
- `compatibility_inventory(...)`: produces static supported/blocked inventory for current mapping files.
- `freeze_load_synthetic(...)` / `freeze_load_union_synthetic(...)`: qualifies Suite freeze/load through the existing harness API.

## Selector support

Supported:

- `literal`: scalar only (`str`, `int`, `float`, `bool`, `null`).
- `fromResource`: explicit resource metadata (`ddName`, `sha256`, `size`).
- `fromBinding`: explicit fixture binding/path.
- `fromBytes`: pinned physical resource bytes, hash/size checked, encoded as `base64` or `utf8`.
- `fromScalar`: explicit scalar from fixture key metadata by DD/attribute/index.
- SDD `{}`: only when the operation schema is a closed empty JSON object.

Blocked:

- Prebuilt `request` dictionaries.
- Unsupported selectors such as invented timestamps/events/values.
- Missing fixture evidence or missing selected resources/bindings.
- Non-object requestBody plans such as `deterministic_from_allowed_schema_fields_when_case_is_later_frozen` until replaced by explicit selector objects.

## Evidence produced

- `synthetic-evidence/`: synthetic-only BFS -> mapper -> schema -> Suite freeze/load -> synthetic T4 union freeze/load.
- `compatibility-inventory.json`: static inventory over `../applicability-mapping-v3/applicability_matrix.json`.
- `original-schema-dry-validation.json`: dry validation of SDD `{}` against original `P2a/openapi-carddemo-stage6r3.yaml` for `/posting`, `/interest`, `/reporting`.

## Static compatibility result

Current mapping matrix inspected: 175 cells.

- Supported by current mapper code: 9 cells.
- Blocked by current mapper code: 166 cells.

Reason: the matrix has 44 generative-admissible cells as an applicability claim, but most non-SDD cells still lack an explicit requestBody selector object and external `fixtureSelection.fixtureId`. This mapper therefore does not treat those cells as operationally generatable.

## Verification commands

```bash
../../P2a/.venv/bin/python -m unittest discover -s tests -v
../../P2a/.venv/bin/python t3_mapper_cli.py synthetic --output synthetic-evidence
../../P2a/.venv/bin/python t3_mapper_cli.py inventory --matrix ../applicability-mapping-v3/applicability_matrix.json --output compatibility-inventory.json
```

Observed:

- `Ran 6 tests ... OK`.
- Synthetic CLI summary: `acceptedCount=1`, `blockedCount=2`, `officialCampaign=false`, freeze/load `T3`, synthetic union `T4` loaded.
- Inventory CLI summary: `supported=9`, `blocked=166`, `officialCampaign=false`.
