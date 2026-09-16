# Applicability Mapping v3 — fail-closed guard-sensitive repair

Status: `candidate_needs_review`  
Campaign authorization: false

## Scope completed

Minimal v3 correction over v2. Guard-sensitive obligation/contract cells now require a documented named selection variant before any generative use, whether their applicability status is `expressible_by_surface` or `conditioned_on_external_fixture`.

## What changed

- `generative_admissible` is now computed from both surface status and plan admissibility.
- Guard-sensitive cells without a named `fixtureVariant` are blocked fail-closed.
- Blocked cells expose no usable executable selectors: `fieldSelectors=[]`, `selectorUsableForGeneration=false`.
- Rich `bindings` fields are not treated as business branch selection.
- SDD cells remain immutable: request body `{}`, no selectors, no new selector fields.
- Diagnostics are preserved as non-generative/blocking causes, not converted into executable cases.

## What did not change

- Inventory remains 25 obligations × 7 contracts = 175 cells.
- No variants, expected results, official cases, runtime calls, coverage reads, oracle reads, quarantine reads, or campaign authorization were created.
- Status remains `candidate_needs_review`.

## RED/GREEN evidence

RED against v2:

- `test_v2_recovery_count_is_reproduced_when_pointed_at_v2` passed and confirmed the coordinator's `confirmed_guard_sensitive_admissibility_without_variant_or_block = 32`.
- The v3 fail-closed assertion pointed at v2 failed with `First list contains 32 additional elements` and exit status 1.

GREEN against v3:

- `../../P2a/.venv/bin/python -m unittest discover -s tests -v` → `Ran 16 tests ... OK`.
- `../../P2a/.venv/bin/python tools/validate_matrix.py` → `PASS applicability matrix integrity`.
- `../../P2a/.venv/bin/python tools/review_probes_v2.py` → `sdd_empty_request_guard.violations=[]`, `selector_mismatches.count=0`, `conditioned_guard_cells_without_block.count=0`, `diagnostics_with_executable_selectors.count=0`.

## Programmatic counts

```json
{
  "denominators": {
    "obligations": 25,
    "contracts": 7,
    "operations": 21,
    "obligation_contract_cells": 175,
    "mapped_contract_cells": 175,
    "status_counts": {
      "expressible_by_surface": 76,
      "conditioned_on_external_fixture": 43,
      "not_expressible": 7,
      "precondition_indeterminate": 28,
      "observation_inadmissible": 14,
      "not_mapped": 7
    },
    "dimensions": {
      "inventory_cells": 175,
      "surface_expressible_cells": 76,
      "fixture_variant_required_cells": 43,
      "documented_selection_variant_required_cells": 84,
      "generative_admissible_cells": 44,
      "exercised_by_package_cells": 0
    },
    "plan_counts": {
      "supported_unexercised": 63,
      "pending_or_blocked": 112,
      "diagnostics_only_non_generative": 14
    }
  },
  "repair_checks": {
    "guard_cells_total": 84,
    "guard_surface_or_conditioned_cells": 56,
    "guard_surface_or_conditioned_without_variant_blocked": 56,
    "blocked_with_selectors": 0,
    "sdd_cells": 25,
    "sdd_mutated": 0,
    "rich_binding_guard_blocked": 12,
    "diagnostics_only_or_blocked": 35,
    "diagnostics_with_selectors": 0
  }
}
```

## Review boundary

This is a bounded preparation artifact, not a campaign/readiness approval. It preserves the v2 diagnostic posture and closes the guard-sensitive generative leak without re-reviewing the whole mapping.
