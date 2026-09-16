# Applicability mapping v3 — pré-campanha fail-closed

Status: `candidate_needs_review`.  
Autorização de campanha: `false`.

Este diretório é uma correção mínima de `applicability-mapping-v2/`: células guard-sensitive não podem ser usadas para geração sem uma seleção documentada nomeada (`fixtureVariant`) ou prova/variante equivalente. Na ausência dessa seleção, o plano fica `generativeUse=blocked`, `generative_admissible=false`, e `fieldSelectors=[]`, mesmo quando `applicabilityStatus=expressible_by_surface`. A dimensão `surface_expressible` continua separada.

## Artefatos

- `applicability_matrix.json` — matriz v3 legível por máquina.
- `tools/build_matrix.py` — reconstrói a matriz v3 sem ler runtime/cobertura/oráculos/quarentena/cases oficiais.
- `tools/validate_matrix.py` — valida denominadores, SDD `{}`, bloqueios e contagens programáticas.
- `tools/review_probes_v2.py` — probes estáticos preservados/adaptados para a política v3.
- `tests/test_guard_sensitive_fail_closed.py` — RED/GREEN específico da correção de 32 células v2.
- `tests/test_matrix_integrity.py` — regressões de integridade herdadas e ajustadas para v3.
- `REPORT.md` — relatório bounded da correção.

## Regras v3

- O inventário permanece 25 obrigações × 7 contratos = 175 células.
- Guard-sensitive requer variante/seleção nomeada documentada, independentemente de status `expressible_by_surface` ou `conditioned_on_external_fixture`.
- `bindings` rico não é seletor automático de branch de negócio.
- Células `blocked` não expõem seletores utilizáveis (`fieldSelectors=[]`, `selectorUsableForGeneration=false`).
- SDD permanece `{}`: `requestBody={}`, `fieldSelectors=[]`, `newSelectorsIntroduced=false`.
- Nenhum expected result, variante, caso oficial, runtime call, oráculo, cobertura ou autorização de campanha foi criado.

## Denominadores programáticos v3

```json
{
  "calculation": "programmatic",
  "obligations": 25,
  "contracts": 7,
  "operations": 21,
  "tracks": 3,
  "candidateFixtures": 3,
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
}
```

Checks adicionais calculados em código:

```json
{
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
```

## Verificação local

Com o venv permitido de P2a:

```bash
../../P2a/.venv/bin/python tools/build_matrix.py
../../P2a/.venv/bin/python -m unittest discover -s tests -v
../../P2a/.venv/bin/python tools/validate_matrix.py
../../P2a/.venv/bin/python tools/review_probes_v2.py
```

Última verificação:

- RED v2: `test_v2_recovery_count_is_reproduced_when_pointed_at_v2` confirmou 32 células em `coordinator-recovery.json`; a regra GREEN apontada para v2 falhou com `First list contains 32 additional elements`.
- GREEN v3: `Ran 16 tests ... OK`.
- Validator v3: `PASS applicability matrix integrity`.
- Probes v3: `sdd_empty_request_guard.violations=[]`, `selector_mismatches.count=0`, `conditioned_guard_cells_without_block.count=0`, `diagnostics_with_executable_selectors.count=0`.

Esses checks são integridade mecânica pré-campanha; não autorizam campanha e não revisam semanticamente todo o inventário.
