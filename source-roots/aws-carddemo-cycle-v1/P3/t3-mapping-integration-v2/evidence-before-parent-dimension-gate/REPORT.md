# T3 Mapping Integration v2

Status: candidate. Official AWS campaign export: false.

## Corrections

- Reproduced v1 defects without modifying v1: isolated v1 import resolves `campaign-harness-v1`, and v1 reopens 56 upstream `generativeUse=blocked` / diagnostics-only / `selectorUsableForGeneration=false` cells as selector-bearing candidates. Examples include `POSTTRAN-OBL-004::E1-1::postDailyTransactions` through `POSTTRAN-OBL-004::E2-2::postDailyTransactions`.
- v2 imports `campaign-harness-v3` in isolated subprocess and verifies `module.__file__`, avoiding stale `sys.modules` contamination.
- v2 separates recipe existence from executable eligibility: v3/status surface alone is not enough. A cell is executable-eligible only when applicability, upstream plan flags, linked recipe, and concrete fixture selection are all present.
- Blocked/diagnostics/non-generative cells keep no selector objects and cannot produce usable requests even when a recipe join exists.
- SDD `{}` no longer receives an artificial placeholder fixture. Empty-object recipes without a fixture remain blocked until a fixture agenda exists.

## Corrected inventory

- Integrated cells: 175
- Recipes: 21
- v3/status-allowed cells with recipe join: 119 (kept only as recipe-existence fact, not executable eligibility)
- Executable-eligible cells with linked recipe: 54
- Recipe exists but not executable-eligible: 65
- Inventory totals: `{"contractually_impossible": 7, "implementation_missing": 72, "missing_fixture_variant": 28, "observation_without_authority": 14, "recipe_available_unexercised": 54}`

The previous 119 usable/allowed assertion was replaced because it counted recipe joins on status surface only and ignored documented upstream non-generative/blocked flags plus missing SDD fixture selection; the local v1 repro shows that as the defect.

## Verified commands

- RED: `../P2a/.venv/bin/python -m unittest discover -s t3-mapping-integration-v2/tests -v` failed against the copied v1 implementation: wrong harness v1, SDD placeholder fixture, missing executable summary, and blocked guard admitted as a case.
- GREEN: `../P2a/.venv/bin/python -m unittest discover -s t3-mapping-integration-v2/tests -v` → 5 tests OK.
- Compatible regression tests:
  - `../P2a/.venv/bin/python -m unittest discover -s t3-mapping-integration-v1/tests -v` → 4 tests OK; originals preserved.
  - `../P2a/.venv/bin/python -m unittest discover -s t3-mapper-preparation-v1/tests -v` → 7 tests OK.
  - `../P2a/.venv/bin/python -m unittest discover -s campaign-harness-v3/tests -v` → 14 tests OK.

## Artifacts

- `src/mapping_integration.py`
- `tests/test_integration_mapping_v2.py`
- `integrated-mapping.json`
- `compatibility-inventory.json`
- `validation-report.json`
- `REPORT.json`
- `red-v1-repro.json`
- `write_outputs.stdout.json`
