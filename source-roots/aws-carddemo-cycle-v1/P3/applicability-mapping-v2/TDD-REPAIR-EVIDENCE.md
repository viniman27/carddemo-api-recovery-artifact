# Applicability mapping v2 — TDD repair evidence

Status: `candidate_needs_review`. This file records mechanical TDD evidence for CE-001–CE-006 repair. It is not campaign authorization and does not define expected results.

## RED

After copying v1 to `applicability-mapping-v2/`, regression tests were added before implementation and run against the unmodified v1-derived matrix:

```text
../../P2a/.venv/bin/python -m unittest discover -s tests -v
FAILED (failures=4, errors=1)
```

Expected RED failures reproduced the review mismatches:

- 318 explicit-source selector mismatches from token-expanded `allowedSource`.
- missing `applicabilityDimensions` / `exercised_by_package` dimension.
- 16 guard-sensitive conditioned cells without a named variant or block.
- diagnostics-only/blocked reporting and posting partial-effect cells still had executable selectors/generative plan gaps.

## GREEN

After implementation:

```text
../../P2a/.venv/bin/python tools/build_matrix.py
../../P2a/.venv/bin/python tools/validate_matrix.py
../../P2a/.venv/bin/python -m unittest discover -s tests -v
../../P2a/.venv/bin/python tools/review_probes_v2.py
```

Observed GREEN results:

- `validate_matrix.py`: `PASS applicability matrix integrity`.
- `unittest`: `Ran 10 tests in 0.065s; OK`.
- `review_probes_v2.py`: `selector_mismatches.count=0`; `conditioned_guard_cells_without_block.count=0`; `diagnostics_with_executable_selectors.count=0`; `sdd_empty_request_guard.violations=[]`.

## Calculated counts

From generated v2 matrix/probes:

- obligations: 25
- contracts: 7
- operations: 21
- obligation_contract_cells / mapped_contract_cells: 175
- dimensions:
  - inventory_cells: 175
  - surface_expressible_cells: 76
  - fixture_variant_required_cells: 43
  - generative_admissible_cells: 76
  - exercised_by_package_cells: 0
- plans:
  - supported_unexercised: 95
  - pending_or_blocked: 80
  - diagnostics_only_non_generative: 35

## Boundary

No runtime/API results, coverage, oracles, quarantine, official generated cases, API/COBOL/model calls were used to set expected behavior. These checks verify the candidate mapping structure only; they do not declare full pretest completion.
