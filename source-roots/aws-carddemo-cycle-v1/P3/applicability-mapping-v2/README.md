# Applicability mapping v2 — pré-campanha

Status: `candidate_needs_review`.  
Autorização de campanha: `false`.

Este diretório preserva a forma de inventário da v1 e corrige os counterexamples CE-001–CE-006 apontados pela revisão. A matriz continua sendo somente um artefato de aplicabilidade pré-campanha: não cria casos oficiais, suítes oficiais, expectativas, oráculos, resultados de runtime, cobertura ou autorização de execução.

## Artefatos

- `applicability_matrix.json` — matriz substantiva e legível por máquina.
- `tools/build_matrix.py` — reconstrói a matriz com mapa explícito por campo/schema/trilha.
- `tools/validate_matrix.py` — verifica cobertura, denominadores e regressões CE-001–CE-006.
- `tools/review_probes_v2.py` — probes estáticos adaptados da revisão v1.
- `probe-results-v2.json` — resultado dos probes adaptados.
- `tests/test_matrix_integrity.py` — testes de regressão da matriz v2.

## Entradas usadas

Entradas permitidas para mapping pré-campanha:

- `P3/reference-executable-v4/model.json`
- `P3/reference-executable-v4/evidence/obligation-witnesses.json`
- `P3/reference-independent-review-v4/review.json`
- `P3/suite-adapters-preflight-v1/evidence-real-preflight-20260915T-synthetic/operation-inventory.json`
- `P3/suite-adapters-preflight-v1/evidence-real-preflight-20260915T-synthetic/contract-pins.json`
- contratos originais E1/E2 pinados, apenas para extrair schema/request surface;
- `P2a/openapi-carddemo-stage6r3.yaml`, apenas como contrato SDD aprovado;
- `P3/fixture-materialization-v2/package/manifest.json`.

Não foram usados resultados runtime/API, cobertura, oráculos, quarentena, casos oficiais gerados ou model calls para definir expectativas.

## Correções CE-001–CE-006

- **CE-001:** removida a heurística por tokens de nomes de campos; `FIELD_SOURCE_BY_TRACK` mapeia explicitamente campo/schema/trilha para o recurso correto (`accountFile→ACCTFILE`, `categoryBalanceFile→TCATBALF`, `rejectFile→DALYREJS`, `transactionTypeFile→TRANTYPE`, `reportOutput→TRANREPT`, etc.).
- **CE-002:** cada célula agora tem `applicabilityDimensions`: `inventory_cell`, `surface_expressible`, `fixture_variant_required`, `generative_admissible`, `exercised_by_package`. Todas as células permanecem `exercised_by_package=false`.
- **CE-003/CE-004:** células guard-sensitive `conditioned_on_external_fixture` têm bloqueio explícito quando não há variante nomeada efetivamente disponível. A matriz não transforma E2-1/E2-3 nem SDD `{}` em seleção exercitável de branch.
- **CE-005:** células de reporting EOF/raw/ordem bloqueadas ficam `diagnostics_only_non_generative` e sem `fieldSelectors` executáveis.
- **CE-006:** células de posting partial effects/lookup não autorizadas ficam não generativas no plano, sem seletores executáveis para criar T3.
- **SDD `{}`:** mantém `requestBody={}`, `fieldSelectors=[]`, `selectionMode=external_fixture_schedule_only`; nenhuma seleção substantiva é adicionada ao contrato.

## Denominadores programáticos

Extraído de `applicability_matrix.json` e confirmado por `tools/validate_matrix.py`/`tools/review_probes_v2.py`:

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
    "generative_admissible_cells": 76,
    "exercised_by_package_cells": 0
  },
  "plan_counts": {
    "supported_unexercised": 95,
    "pending_or_blocked": 80,
    "diagnostics_only_non_generative": 35
  }
}
```

`generative_admissible` é uma propriedade de plano candidato, não evidência de caso oficial exercitado nem expectativa de resultado. `supported_unexercised` inclui planos candidatos sustentados por superfície/fixture sem status oficial de exercício; `pending_or_blocked` requer variante/revisão/emenda antes de uso gerativo.

## Verificação local

Com o venv permitido de P2a:

```bash
../../P2a/.venv/bin/python tools/build_matrix.py
../../P2a/.venv/bin/python tools/validate_matrix.py
../../P2a/.venv/bin/python -m unittest discover -s tests -v
../../P2a/.venv/bin/python tools/review_probes_v2.py
```

Última verificação local:

- `validate_matrix.py`: `PASS applicability matrix integrity`.
- `unittest`: `Ran 10 tests ... OK`.
- `review_probes_v2.py`: `selector_mismatches.count=0`, `conditioned_guard_cells_without_block.count=0`, `diagnostics_with_executable_selectors.count=0`, `sdd_empty_request_guard.violations=[]`.

Esses checks são integridade mecânica pré-campanha; não declaram pré-teste completo e não autorizam campanha.
