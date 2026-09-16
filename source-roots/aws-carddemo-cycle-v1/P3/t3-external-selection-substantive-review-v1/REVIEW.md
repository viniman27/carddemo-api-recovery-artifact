# Parecer substantivo — T3 SDD external selection v1

Status do parecer: **não promove automaticamente** fixtures, matriz, recipes, suíte ou campanha. A revisão é local e versionada; nenhuma implementação, contrato, fonte, API, oráculo em quarentena ou artefato anterior foi modificado.

## Conclusão

A mudança resolve corretamente a distinção mecânica central: o request público SDD permanece `{}` e a seleção de dados é externa por `fixtureId`. Porém, a revisão substantiva encontrou **2 classificações superabrangentes** entre as 18 novas seleções: elas são válidas como preparação parcial/seleção de um subcaso, mas não sustentam toda a guarda declarada.

Recomendação: **não promover para campanha oficial** nesta versão. Antes de qualquer promoção humana, ajustar ou qualificar as duas declarações superabrangentes e manter explícito que várias seleções preparam requests/guardas sem criar oráculo de resultado.

## Contagens computadas

- Obrigações SDD totais no plano: **25** = **18 selecionadas** + **7 bloqueadas**.
- Selecionadas por trilha: **{'posting': 6, 'interest': 6, 'reporting': 6}**.
- Vereditos das 18 selecionadas: **{'ok_static_selection': 3, 'ok_guard_selection': 9, 'ok_branch_selection_no_output_oracle': 1, 'partial_overbroad': 2, 'ok_request_preparation_no_write_oracle': 1, 'ok_branch_selection_no_report_oracle': 1, 'ok_request_preparation_no_format_oracle': 1}**.
- Arquivos físicos de fixture conferidos: **18**, pins bytes+sha256 OK: **18**.
- Âncoras de fonte conferidas: **70 ocorrências / 62 únicas**, mismatches sha256: **0**.
- Recipes SDD na cópia versionada: **3**, todos com `requestBody == {}` e `sddConstantEmptyObject == true`: **3**.
- Testes existentes, após leitura estática: **5 tests OK** com `P2a/.venv/bin/python`; não executam HTTP/API/COBOL/campanha.

## Evidência por classificação nova

| Obrigação | Trilha | Fixture | Request SDD | Veredito | Evidência/limite |
|---|---:|---|---|---|---|
| POSTTRAN-OBL-001 | posting | posting.candidate-v1-physical-v2 | `{}` | ok_static_selection | preparação e seleção estrutural: presença dos DDs físicos permite montar ambiente; não prova OPEN runtime 00. |
| POSTTRAN-OBL-002 | posting | posting.candidate-v1-physical-v2 | `{}` | ok_guard_selection | DALYTRAN 700 bytes/2 registros seleciona pelo menos um READ 00; EOF/outros não selecionados. |
| POSTTRAN-OBL-004 | posting | posting.candidate-v1-physical-v2 | `{}` | ok_guard_selection | DALYTRAN contém card presente 4111111111111111 e ausente 4999999999999999 contra XREFFILE keys 4111111111111111/4222222222222222. |
| POSTTRAN-OBL-005 | posting | posting.candidate-v1-physical-v2 | `{}` | ok_guard_selection | card presente mapeia para conta 10000000001 existente e conta tem limite/expiração compatíveis; variantes negativas não selecionadas. |
| POSTTRAN-OBL-006 | posting | posting.candidate-v1-physical-v2 | `{}` | ok_branch_selection_no_output_oracle | card ausente 4999999999999999 seleciona ramo de rejeição; conteúdo DALYREJS permanece sem oráculo. |
| POSTTRAN-OBL-007 | posting | posting.candidate-v1-physical-v2 | `{}` | partial_overbroad | seleciona TCATBALF status 00 para chave 10000000001010005; não há registro presente com TCATBAL ausente para status 23, logo a frase “00/23” está superabrangente. |
| INTCALC-OBL-001 | interest | interest.candidate-v1-physical-v2 | `{}` | ok_static_selection | presença de TCATBALF, XREFFILE(+sidecar), ACCTFILE, DISCGRP e PARMFILE 10 bytes prepara abertura; não prova OPEN runtime 00. |
| INTCALC-OBL-002 | interest | interest.candidate-v1-physical-v2 | `{}` | ok_guard_selection | TCATBALF indexado possui 2 registros e CBACT04C acessa sequencialmente; seleciona READ 00 inicial, não EOF/outros. |
| INTCALC-OBL-003 | interest | interest.candidate-v1-physical-v2 | `{}` | ok_guard_selection | TCATBALF contas 10000000001/2 casam com ACCTFILE e XREFFILE alternateKeys 10000000001/2. |
| INTCALC-OBL-004 | interest | interest.candidate-v1-physical-v2 | `{}` | partial_overbroad | seleciona caminhos específicos STANDARD e ZERORATE; DEFAULT existe como recurso, mas nenhum TCATBALF/ACCTFILE usa grupo ausente para provocar status 23 e fallback DEFAULT. |
| INTCALC-OBL-005 | interest | interest.candidate-v1-physical-v2 | `{}` | ok_guard_selection | DISCGRP tem taxa não-zero STANDARD 000150 e zero ZERORATE 000000, com TCATBALF para ambas as contas. |
| INTCALC-OBL-006 | interest | interest.candidate-v1-physical-v2 | `{}` | ok_request_preparation_no_write_oracle | PARMFILE 2022071800 e XREF fornecem campos para transação; WRITE/resultado permanecem sem oráculo. |
| TRANREPT-OBL-001 | reporting | reporting.candidate-v1-physical-v2 | `{}` | ok_static_selection | /reporting + pacote físico fornece TRANFILE, DATEPARM, CARDXREF, TRANTYPE, TRANCATG; SORT/REPROC não é alegado. |
| TRANREPT-OBL-002 | reporting | reporting.candidate-v1-physical-v2 | `{}` | ok_guard_selection | DATEPARM 2022-07-01..2022-07-31 e TRANFILE com proc_ts 2022-07-05 selecionam in_range. |
| TRANREPT-OBL-003 | reporting | reporting.candidate-v1-physical-v2 | `{}` | ok_guard_selection | TRANFILE tem registro 2022-08-01 fora da janela de julho, selecionando guarda false/skip; EOF não selecionado. |
| TRANREPT-OBL-004 | reporting | reporting.candidate-v1-physical-v2 | `{}` | ok_guard_selection | registro in-range 4111111111111111, type 01, cat 0005 casa com CARDXREF, TRANTYPE e TRANCATG 010005. |
| TRANREPT-OBL-005 | reporting | reporting.candidate-v1-physical-v2 | `{}` | ok_branch_selection_no_report_oracle | um registro in-range seleciona primeiro detalhe/cabeçalho; limite de página não selecionado. |
| TRANREPT-OBL-006 | reporting | reporting.candidate-v1-physical-v2 | `{}` | ok_request_preparation_no_format_oracle | há bytes de transação e lookup para detalhe/acréscimo; formatação edited-money não é expectativa autorizada. |

## Contraexemplos substantivos encontrados

1. **POSTTRAN-OBL-007** — a declaração fala em ramo `tcatbal_status 00/23`, mas os bytes selecionados sustentam apenas `00`: `DALYTRAN` tem o registro aceito `4111111111111111`/tipo `01`/cat `0005`, `XREFFILE` mapeia para conta `10000000001`, e `TCATBALF` tem a chave `10000000001010005`. Não há transação presente com XREF/ACCOUNT válidos e TCATBALF ausente para provocar `23`.
2. **INTCALC-OBL-004** — `DISCGRP` contém `STANDARD`, `ZERORATE` e `DEFAULT`, mas o fluxo DEFAULT em `CBACT04C` só ocorre após READ específico com status `23`. Os dois registros `TCATBALF` apontam para contas existentes com grupos `STANDARD` e `ZERORATE`; não há grupo ausente para exercitar fallback DEFAULT. Portanto a classificação seleciona os caminhos específico e zero, não o caminho DEFAULT.

## Preparação de request vs elegibilidade

- **Preparação de request confirmada**: as três recipes SDD usam corpo `{}`; `fixtureSelection.fixtureId` carrega a escolha externa. Isso prepara materialização estática, não campanha.
- **Elegibilidade de guarda confirmada para 16/18 seleções** em nível local/candidato, com as limitações de não executar COBOL e não criar expectativa de resultado.
- **Elegibilidade apenas parcial para 2/18**: POSTTRAN-OBL-007 e INTCALC-OBL-004 devem ser rebaixadas/qualificadas ou receber fixtures adicionais antes de promoção.
- **Sem oráculo novo**: as seleções marcadas `noExpected` continuam sem status esperado, bytes esperados de saída, cobertura oficial ou equivalência COBOL.

## Leitura dos testes antes de execução

Arquivo lido: `P3/t3-sdd-external-selection-v1/tests/test_sdd_external_selection.py`. Os testes chamam `build_external_selection_plan`, `write_versioned_copies`, `enrich_with_external_selection`, `run_all` em diretório temporário e `verify_current_fixture_bytes`; o adaptador chamado por `run_all` constrói casos estáticos via `build_t3_suite`, com `officialCampaign: false`, sem `freeze_suite`, HTTP, subprocess, API, COBOL ou campanha.

Execução realizada:

```text
PYTHONDONTWRITEBYTECODE=1 P2a/.venv/bin/python -m unittest discover -s P3/t3-sdd-external-selection-v1/tests -v
Ran 5 tests in 1.808s
OK
```

## Evidência exata preservada

Ver `evidence.json` neste diretório para pins, hashes, registros decodificados, avaliação por obrigação e varredura estática dos testes.

## Recomendação

1. Não promover `t3-sdd-external-selection-v1` para campanha oficial sem revisão humana explícita.
2. Corrigir por nova versão, não nesta tarefa: qualificar POSTTRAN-OBL-007 como status `00` apenas ou adicionar fixture que selecione `23`; qualificar INTCALC-OBL-004 como específico/zero apenas ou adicionar conta/grupo ausente que force DEFAULT.
3. Manter nos artefatos a diferença entre “request preparado com fixtureId” e “guarda/obrigação elegível”; não usar os 68 casos estáticos como evidência semântica de campanha.
