# Complementary validation v2 — AWS CardDemo

Status: draft local design, not frozen, no campaign.

This v2 preserves `../complementary-validation-v1/` unchanged as a rejected historical draft and replaces it with a concrete, source-backed design:

- 25 scenario records, one per obligation, each with initial condition, stimulus semantics, source anchors, MBT transition refs, observable effects, oracle method and qualification-pending status.
- 7 contracts / 21 operations mapped into 525 traceability cells: 175 candidate-applicable obligation×contract-operation cells and 350 `not_applicable` cells.
- Pre-execution states separated: `not_executed`, `unchecked`, `inconclusive`, `nonexpressible`, `no_observation`, `failed`, `pass`, `not_applicable`.
- T3 retained as a separate MBT battery; the reusable oracle checker battery is shared across T1–T4 but still pending independent review.
- T1 generation catalog and evaluation catalog are separated; T2 pure OpenAPI checks are separated from any domain extension; T4 is exact union only.

No COBOL/API/campaign execution, external LLM call, main study edit, contract edit, or quarantine oracle read was performed.

## Files

- `DESENHO.md` — human-readable design in PT-BR.
- `scenario-catalog.json` — machine-readable catalog.
- `obligation-operation-mapping.csv` — tabular cell mapping.
- `schema/complementary-validation-v2.schema.json` — schema reference used by the catalog.
- `validate_catalog.py` — strict validator.
- `tests/test_validator.py` — TDD tests.
- `VALIDATION-REPORT.md` — actual verification output.

## Verify

From this directory:

```bash
../../P2a/.venv/bin/python -m unittest discover -s tests -v
../../P2a/.venv/bin/python validate_catalog.py
```
