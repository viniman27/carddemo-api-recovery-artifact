# Evidence — suite-generation-preflight-v1

## Commands executed

```bash
P3/.venv-fuzz-preflight/bin/python -m unittest discover -s P3/suite-generation-preflight-v1/tests -v
```

Result:

```text
test_cli_only_synthetic_preparation_and_blocks_official ... ok
test_freeze_load_union_uses_harness_v3_and_asserts_module_path ... ok
test_t1_exports_pending_package_and_strictly_imports_only_concrete_requests ... ok
test_t2_generates_persists_and_imports_schemathesis_offline_with_budgets ... ok
test_t3_bfs_uses_only_allowed_mapping_and_blocks_guard_sensitive_or_abstract ... ok
Ran 5 tests in 0.775s
OK
```

```bash
P3/.venv-fuzz-preflight/bin/python P3/suite-generation-preflight-v1/suite_generation_cli.py synthetic-preparation --output P3/suite-generation-preflight-v1/evidence-synthetic-20260915T-prep
```

Result summary:

```json
{
  "counts": {"T1": 1, "T2": 5, "T3": 1, "T4": 6},
  "officialCampaign": false,
  "harnessV3Sha256": "0e5a9606b7d1ec10c2c07929a2fd18b72748e90ebdc4987a937bdc8fed5dd36e"
}
```

```bash
P3/.venv-fuzz-preflight/bin/python P3/suite-generation-preflight-v1/suite_generation_cli.py official --output P3/suite-generation-preflight-v1/official-should-not-exist
```

Result: exit `2`, message `official generation is gate-closed; use only synthetic-preparation in this preflight`.

## Key generated evidence

- `evidence-synthetic-20260915T-prep/preflight-report.json`
- `evidence-synthetic-20260915T-prep/t1-outbound/t1-outbound-package.json`
- `evidence-synthetic-20260915T-prep/t2/frozen-synthetic3.1-requests.json`
- `evidence-synthetic-20260915T-prep/freeze-load-union/T1.json`
- `evidence-synthetic-20260915T-prep/freeze-load-union/T2.json`
- `evidence-synthetic-20260915T-prep/freeze-load-union/T3.json`
- `evidence-synthetic-20260915T-prep/freeze-load-union/T4-union.json`

All evidence is synthetic/preparation only. No provider, AWS, or official campaign execution occurred.
