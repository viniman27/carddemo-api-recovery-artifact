# Applicability mapping v1 — pré-campanha

Status: `candidate_needs_review`.  
Autorização de campanha: `false`.

Este diretório contém uma matriz substantiva de aplicabilidade entre:

- inventário completo de 25 obrigações da referência MBT v4;
- 7 contratos pinados (`E1-1`, `E1-2`, `E1-3`, `E2-1`, `E2-2`, `E2-3`, `E3-01-SDD-stage6r3`);
- 21 operações reais inventariadas, 3 por contrato/trilha;
- 3 fixtures físicas candidatas de `fixture-materialization-v2`, ainda com `candidate_needs_review`.

A matriz não cria casos, suítes oficiais, resultados esperados, oráculos ou autorização de execução. Ela classifica se uma obrigação é aplicável à superfície/fixture antes da campanha.

## Artefatos

- `applicability_matrix.json` — matriz substantiva e legível por máquina.
- `tools/build_matrix.py` — reconstrói a matriz a partir das entradas permitidas e regras explícitas de mapeamento.
- `tools/validate_matrix.py` — verifica integridade referencial, cobertura do inventário e denominadores.
- `tests/test_matrix_integrity.py` — testes de regressão da matriz.

## Entradas usadas

Todas as entradas são lidas somente para mapping pré-campanha:

- `P3/reference-executable-v4/model.json`
- `P3/reference-executable-v4/evidence/obligation-witnesses.json`
- `P3/reference-independent-review-v4/review.json`
- `P3/suite-adapters-preflight-v1/evidence-real-preflight-20260915T-synthetic/operation-inventory.json`
- `P3/suite-adapters-preflight-v1/evidence-real-preflight-20260915T-synthetic/contract-pins.json`
- contratos originais E1/E2 pinados, apenas para extrair schema/request surface;
- `P2a/openapi-carddemo-stage6r3.yaml`, apenas como contrato SDD aprovado;
- `P3/fixture-materialization-v2/package/manifest.json`.

Não foram lidos resultados runtime/API, cobertura, oráculos, quarentena ou saídas de campanha para escolher expectativas.

## Denominadores programáticos

Extraído de `applicability_matrix.json`:

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
  "by_track": {
    "posting": {
      "obligations": 9,
      "contract_cells": 63
    },
    "interest": {
      "obligations": 8,
      "contract_cells": 56
    },
    "reporting": {
      "obligations": 8,
      "contract_cells": 56
    }
  }
}
```

Esses números vêm do validador/script, não de contagem manual.

## Taxonomia de aplicabilidade

- `expressible_by_surface`: a operação pública tem campos de request suficientes para selecionar os dados/precondições sem fortalecer o contrato.
- `conditioned_on_external_fixture`: a operação existe, mas a seleção substantiva depende de recursos externos/fixtures físicos candidatos.
- `not_expressible`: a obrigação exige controle de falha/estado interno/efeito que nem request nem fixture candidato sustentam sem alterar a superfície.
- `not_mapped`: há operação pública da trilha, mas o passo da obrigação não foi mapeado para invocação HTTP concreta preservando a abstração.
- `precondition_indeterminate`: a obrigação depende de precondição não determinada antes da campanha pelos contratos/fixtures permitidos.
- `observation_inadmissible`: a observação requerida não pode ser usada como veredito pré-campanha sem runtime/oráculo/cobertura ou estado interno não autorizado.

## T3 — plano determinístico de mapping

Cada célula `contractMappings[]` contém `t3DeterministicMapping` com:

- `requestBody`: `deterministic_from_allowed_schema_fields_when_case_is_later_frozen`, `{}` para SDD, ou bloqueio;
- `fieldSelectors`: seletores permitidos exclusivamente a partir dos campos já declarados pelo schema do contrato;
- `constraints`: restrições explícitas de schema e preservação de bytes/roles;
- `fixtureSelection`: fixture por trilha, sem endpoint ou selector novo;
- `blocks`: bloqueios quando abstração/request não sustentam aplicação.

Para o contrato SDD (`E3-01-SDD-stage6r3`), os requests permanecem exatamente `{}`:

- `PostingRequest`, `InterestRequest`, `ReportingRequest`: `type=object`, `properties=[]`, `additionalProperties=false`;
- `fieldSelectors=[]`;
- `newSelectorsIntroduced=false`;
- variação substantiva só pode vir de agenda externa de fixtures, quando sustentada; caso contrário a célula permanece bloqueada/condicionada.

## Revisão de limitações

- `candidate_needs_review` não promove fixtures nem autoriza campanha.
- A classificação é de aplicabilidade, não de satisfação/violação das obrigações.
- `expressible_by_surface` não cria expected result; apenas indica que a superfície pública tem campos suficientes para uma futura seleção determinística revisada.
- `conditioned_on_external_fixture` preserva a ideia de que a variação COBOL pode estar no estado externo, não no body HTTP.
- Células `not_expressible`, `not_mapped`, `precondition_indeterminate` e `observation_inadmissible` não devem virar casos T3 sem emenda revisada.
- A referência v4 tem PASS apenas para seleção abstrata de caminhos; não é oráculo completo nem prova de equivalência COBOL.
- O JCL/SORT de `TRANREPT-OBL-001` permanece não mapeado como operação HTTP; só o relatório efetivo com `TRANFILE`/`DATEPARM` preparado é endereçável.
- Não há nova operação, selector, request field ou normalização SDD introduzida por este artefato.

## Verificação

Com o venv permitido de P2a:

```bash
../../P2a/.venv/bin/python tools/build_matrix.py
../../P2a/.venv/bin/python tools/validate_matrix.py
../../P2a/.venv/bin/python -m unittest discover -s tests -v
```

Última verificação local: `5` testes, `OK`; `validate_matrix.py` retorna `PASS applicability matrix integrity`.
