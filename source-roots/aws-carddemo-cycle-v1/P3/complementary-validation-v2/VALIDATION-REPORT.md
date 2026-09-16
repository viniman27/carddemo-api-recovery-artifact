# Mechanical validation report — complementary-validation-v2

## TDD RED observed

Initial test run after writing `tests/test_validator.py` and before implementing `validate_catalog.py` failed with missing production artifacts:

```text
FileNotFoundError: ... complementary-validation-v2/validate_catalog.py
FileNotFoundError: ... complementary-validation-v2/scenario-catalog.json
FAILED (errors=5)
```

A second RED after creating the validator exposed a Python-version incompatibility in type annotations under the workspace interpreter; that was fixed before GREEN.

## GREEN — unittest with P2a Python

Command:

```bash
../../P2a/.venv/bin/python -m unittest discover -s tests -v
```

Output:

```text
test_catalog_has_one_source_backed_scenario_per_obligation_not_count_proxy (test_validator.ComplementaryValidationV2Tests) ... ok
test_contract_mapping_is_7_contracts_21_operations_175_applicable_350_na (test_validator.ComplementaryValidationV2Tests) ... ok
test_source_pins_and_schema_reference_are_verified (test_validator.ComplementaryValidationV2Tests) ... ok
test_status_denominators_separate_not_executed_unchecked_inconclusive_nonexpressible_noobservation_failed_pass_and_na (test_validator.ComplementaryValidationV2Tests) ... ok
test_t3_mbt_is_separate_battery_with_shared_independent_checker_assessment (test_validator.ComplementaryValidationV2Tests) ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.049s

OK
```

## Catalog validator with P2a Python

Command:

```bash
../../P2a/.venv/bin/python validate_catalog.py
```

Output:

```json
{
  "checked": {
    "applicableCells": 175,
    "contracts": 7,
    "coverageIsByObligationIds": true,
    "coveredObligations": 25,
    "mappingCells": 525,
    "notApplicableCells": 350,
    "obligations": 25,
    "operations": 21,
    "scenarioRecords": 25,
    "schemaRef": "schema/complementary-validation-v2.schema.json",
    "sourceHashesVerified": true
  },
  "errors": [],
  "status": "PASS"
}
```

The validator checks source hashes/line ranges, source pins, 25-obligation coverage by IDs, the 7/21/525/175/350 denominator split, strict status separation, schema reference, and T3 MBT preservation. It does not execute campaign, COBOL, APIs, or external calls.
