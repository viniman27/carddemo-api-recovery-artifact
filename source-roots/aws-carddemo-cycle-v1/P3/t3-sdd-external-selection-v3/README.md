# T3 SDD external selection v3

Status: `candidate_static_only`; official campaign/suite promotion: false; runtime/API/COBOL execution: false.

This version preserves `t3-sdd-external-selection-v1` and `t3-sdd-external-selection-v2` and fixes the v2 report-only effective-transition filter. The new entrypoint `build_selected_t3_suite(...)` returns a real `Suite` whose `suite.cases` are filtered before callers consume it.

## Policy maintained

- SDD public request body remains `{}` for `/posting`, `/interest`, and `/reporting`.
- Selection remains local/external by `fixtureId`; no request-field selector is introduced.
- No expected status, report bytes, output bytes, COBOL runtime result, campaign oracle, official freeze, or business execution is introduced.
- Denominator remains 25 SDD obligations: 18 locally selected/prepared, 7 blocked.

## v3 correction

`POSTTRAN-OBL-007` and `INTCALC-OBL-004` declare partial effective transitions. v2 removed disallowed transitions only from `adapter-static-check.json`; the underlying suite returned by `build_t3_suite(...)` still contained 68 cases including `POSTTRAN-T014` and two `INTCALC-T008` cases.

v3 adds:

- `effective_transition_restriction(cell)`: distinguishes no declared restriction (`None`) from explicit empty deny (`set()`).
- `build_selected_t3_suite(enriched, p3, out)`: builds through the real adapter, filters the returned `Suite.cases`, and returns the restricted real suite plus exclusion ledger.
- `selected-suite-real.json`: candidate/static-only serialization of the returned real selected suite for inspection, not an official campaign freeze.

## Outputs

- `external-selection-plan.json` — fixtureId-level selection plan.
- `applicability_matrix.sdd-external-selection-v3.json` — versioned matrix copy with SDD-only external-selection annotations.
- `recipes.sdd-external-selection-v3.json` — versioned recipes copy with SDD empty-request recipes bound to external fixture selection.
- `integrated-mapping.sdd-external-selection-v3.json` — adapter-local enriched plan.
- `sdd-id-migration.external-selection-v3.json` — versioned matrix-ID to registry-ID proof for copied inputs only.
- `selected-suite-real.json` — real restricted `Suite` serialization: 65 cases, all request bodies `{}`.
- `adapter-static-check.json` — static link report over the already-restricted suite.
- `fixture-byte-structural-check.json` — structural byte/hash fixture check only.
- `static-fairness-check.json` — SDD/non-SDD fairness check.
- `REPORT.json` — aggregate report and pins.

## Verification commands

```bash
cd "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/t3-sdd-external-selection-v3"
"<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P2a/.venv/bin/python" -m unittest discover -s tests -v
"<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P2a/.venv/bin/python" sdd_external_selection.py
```

Observed v3 unit result: 10 tests, OK. Generated report status: `candidate_static_only`.
