# T3 mapper preparation v1

Status: `preparation_synthetic_only`  
Official AWS suite/case generation: `false`

This directory contains a reusable T3 mapper API for later authorized generation. It does not call AWS APIs, COBOL, runtime harnesses, LLMs, oracle material, quarantine, coverage, or official case sources.

## What is implemented

- `src/t3_mapper.py`
  - `FixtureIndex` and `FixturePackage` for explicit external fixture selection.
  - `build_request_from_explicit_mapping(...)` to convert operation + explicit selector mapping + fixture into `HttpRequestSpec`.
  - Concrete selector functions for:
    - `literal` scalar values only;
    - `fromResource` resource metadata (`ddName`, `sha256`, `size`);
    - `fromBinding` fixture binding/path evidence;
    - `fromBytes` pinned resource bytes (`base64` or `utf8`) with size/hash checks;
    - `fromScalar` explicit scalar extracted from fixture key metadata.
  - OpenAPI request schema validation using the original schema document supplied by the caller.
  - Fail-closed `MappingBlocked(blocked_reason, details)` instead of inventing request values.
  - `bfs_map_model_to_suite(...)` for BFS over explicit mapping cells only.
  - `compatibility_inventory(...)` for static supported/blocked inventory against current mapping plans.
  - `freeze_load_synthetic(...)` and `freeze_load_union_synthetic(...)` against the existing campaign harness freeze/load API.
- `t3_mapper_cli.py`
  - `synthetic`: synthetic-only end-to-end BFS -> mapper -> schema -> Suite freeze/load -> synthetic union freeze/load.
  - `inventory`: static mapping compatibility inventory.
  - `map`: preparation-only explicit mapping run for supplied files.
  - `official`: intentionally exits non-zero; official T3 generation remains gate-closed.

## Local verification

```bash
../../P2a/.venv/bin/python -m unittest discover -s tests -v
../../P2a/.venv/bin/python t3_mapper_cli.py synthetic --output synthetic-evidence
../../P2a/.venv/bin/python t3_mapper_cli.py inventory --matrix ../applicability-mapping-v3/applicability_matrix.json --output compatibility-inventory.json
```

Observed results in this run:

- Unit tests: `Ran 6 tests ... OK`.
- Synthetic CLI: accepted 1 synthetic T3 mapped case, blocked 2 synthetic cells, froze/loaded `T3.json`, and froze/loaded synthetic T4 union; `officialCampaign=false`.
- Current matrix static inventory: 175 cells inspected; 9 supported by the current code path, 166 blocked with per-cell `minimumMissing`.
- Original SDD schema dry validation: `/posting`, `/interest`, `/reporting` all validated with constant JSON body `{}` and exported no official cases.

## Boundaries

- The mapper refuses a prebuilt `request` dictionary. It requires operation + selector mapping + fixture evidence.
- It does not invent timestamps, values, events, variants, expected results, or fixture selections.
- Non-SDD current mappings that only say `deterministic_from_allowed_schema_fields_when_case_is_later_frozen` are blocked until replaced by explicit selector objects and an external `fixtureSelection.fixtureId`.
- The 44 matrix-admissible cells remain an applicability/methodology claim, not operational proof for this mapper. This mapper currently treats only the SDD `{}` cells as statically supported from the current AWS mapping file.
