# Análise quantitativa — AWS CardDemo P3 official campaign large12k run v2

## Escopo e reprodutibilidade

Esta análise agrega o relatório oficial concluído sem reexecutar testes, sem gerar novos casos, sem chamar APIs/LLMs e sem editar artefatos congelados. A saída foi criada em `P3/official-analysis-v1/` a partir de `P3/official-campaign-large12k-run-v2/campaign-report.json` e dos manifestos/configurações congelados.

Evidência principal: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/official-campaign-large12k-run-v2/campaign-report.json`  
SHA-256: `bdef12959aebfcf38f06e9e0720d7e211cdd66d9d7084043d1cfe496188e68aa`  
Tamanho: `99908182` bytes

## Verificações independentes

| Item | Resultado |
| --- | --- |
| Linhas/casos agregados a partir de `suiteReports[].checks` | 12700 |
| Suítes no relatório oficial | 28 |
| Totais declarados no relatório | `{"attempted": 12700, "completed": 12700, "measurement_admissible": 1070, "planned": 12700, "structural_ok": 12700}` |
| Suítes congeladas recontadas em `campaign-freeze-package-v3/*/T*.json` | 28 |
| Contagem congelada por condição recontada | `{'T1': 88, 'T2': 5868, 'T3': 394, 'T4': 6350}` |
| T1/T2/T3/T4 esperado | `88 / 5868 / 394 / 6350` |
| Status HTTP totais | `{'200': 1068, '400': 4378, '500': 7254}` |
| Violações experimentais declaradas | 0 |

## Leitura dos braços e condições

- Braços de extração: `E1-* = zero-shot`, `E2-* = few-shot`, `E3-SDD-stage6r3 = SDD`.
- Condições de teste: `T1 = cenários LLM importados`, `T2 = fuzzing OpenAPI`, `T3 = MBT`, `T4 = união/reexecução dependente de T1/T2/T3`.
- `T4` não é réplica independente: é uma união congelada e reexecutada, portanto não deve ser usada como amostra estatística independente dos seus componentes.

## Tabela principal por condição

| Condição | N | Status HTTP | Classificação estrutural | Expectativa harness | Admissibilidade de medição |
| --- | --- | --- | --- | --- | --- |
| T1 | 88 | {'200': 19, '400': 37, '500': 32} | {'documented_500_schema_valid': 32, 'schema_valid': 56} | {'pass': 88} | {'admissible_preparatory': 20, 'inadmissible_or_limited': 68} |
| T2 | 5868 | {'200': 177, '400': 2124, '500': 3567} | {'documented_500_schema_valid': 3567, 'schema_valid': 2301} | {'pass': 5868} | {'admissible_preparatory': 177, 'inadmissible_or_limited': 5691} |
| T3 | 394 | {'200': 338, '400': 28, '500': 28} | {'documented_500_schema_valid': 28, 'schema_valid': 366} | {'inconclusive': 394} | {'admissible_preparatory': 338, 'inadmissible_or_limited': 56} |
| T4 | 6350 | {'200': 534, '400': 2189, '500': 3627} | {'documented_500_schema_valid': 3627, 'schema_valid': 2723} | {'inconclusive': 394, 'pass': 5956} | {'admissible_preparatory': 535, 'inadmissible_or_limited': 5815} |


Interpretação: todos os 12700 casos completaram e passaram a checagem estrutural. Isso significa conformidade de rota/operação/status/content-type/JSON/schema conforme contrato congelado. Não significa sucesso de negócio. Em particular, `7254` respostas HTTP 500 foram classificadas como `documented_500_schema_valid`: são falhas documentadas e estruturalmente admissíveis, não sucessos funcionais.

## Status por braço e condição

| Braço | Condição | N | Status HTTP |
| --- | --- | --- | --- |
| zero-shot | T1 | 31 | {'500': 31} |
| zero-shot | T2 | 2700 | {'500': 2700} |
| zero-shot | T3 | 156 | {'200': 128, '500': 28} |
| zero-shot | T4 | 2887 | {'200': 128, '500': 2759} |
| few-shot | T1 | 45 | {'200': 16, '400': 28, '500': 1} |
| few-shot | T2 | 2700 | {'200': 159, '400': 1674, '500': 867} |
| few-shot | T3 | 116 | {'200': 88, '400': 28} |
| few-shot | T4 | 2861 | {'200': 263, '400': 1730, '500': 868} |
| SDD | T1 | 12 | {'200': 3, '400': 9} |
| SDD | T2 | 468 | {'200': 18, '400': 450} |
| SDD | T3 | 122 | {'200': 122} |
| SDD | T4 | 602 | {'200': 143, '400': 459} |


## Medição/coverage admissível

A campanha tem `1070` casos com medição admissível/preparatória e `11630` casos inadmissíveis ou limitados. Ausência de medição admissível não foi convertida em cobertura zero.

| Razão de inadmissibilidade/limite | Ocorrências |
| --- | --- |
| audit_missing_for_current_case_track | 11630 |


## Gcov: união de linhas, não média de percentuais

A tabela abaixo une números de linha executáveis observados nos arquivos `.gcov` disponíveis dos casos admissíveis. Não há média de percentuais por caso. Onde não há medição admissível, o resultado permanece ausente/inadmissível, não zero.

| Braço | Condição | Trilha | Programa | Casos admissíveis | Linhas executadas (união) | Linhas totais (união) | Cobertura de linhas (união) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SDD | T1 | interest | CBACT04C | 1 | 585 | 1029 | 0.568513 |
| SDD | T1 | posting | CBTRN02C | 1 | 651 | 1120 | 0.58125 |
| SDD | T1 | reporting | CBTRN03C | 1 | 655 | 1192 | 0.549497 |
| SDD | T2 | interest | CBACT04C | 6 | 585 | 1029 | 0.568513 |
| SDD | T2 | posting | CBTRN02C | 6 | 651 | 1120 | 0.58125 |
| SDD | T2 | reporting | CBTRN03C | 6 | 655 | 1192 | 0.549497 |
| SDD | T3 | interest | CBACT04C | 28 | 585 | 1029 | 0.568513 |
| SDD | T3 | posting | CBTRN02C | 17 | 651 | 1120 | 0.58125 |
| SDD | T3 | reporting | CBTRN03C | 77 | 655 | 1192 | 0.549497 |
| SDD | T4 | interest | CBACT04C | 35 | 585 | 1029 | 0.568513 |
| SDD | T4 | posting | CBTRN02C | 24 | 651 | 1120 | 0.58125 |
| SDD | T4 | reporting | CBTRN03C | 84 | 655 | 1192 | 0.549497 |
| few-shot | T1 | interest | CBACT04C | 5 | 585 | 1029 | 0.568513 |
| few-shot | T1 | posting | CBTRN02C | 5 | 508 | 1120 | 0.453571 |
| few-shot | T1 | reporting | CBTRN03C | 7 | 576 | 1192 | 0.483221 |
| few-shot | T2 | interest | CBACT04C | 37 | 585 | 1029 | 0.568513 |
| few-shot | T2 | posting | CBTRN02C | 81 | 508 | 1120 | 0.453571 |
| few-shot | T2 | reporting | CBTRN03C | 41 | 528 | 1192 | 0.442953 |
| few-shot | T3 | interest | CBACT04C | 18 | 585 | 1029 | 0.568513 |
| few-shot | T3 | posting | CBTRN02C | 14 | 651 | 1120 | 0.58125 |
| few-shot | T3 | reporting | CBTRN03C | 56 | 655 | 1192 | 0.549497 |
| few-shot | T4 | interest | CBACT04C | 60 | 585 | 1029 | 0.568513 |
| few-shot | T4 | posting | CBTRN02C | 100 | 651 | 1120 | 0.58125 |
| few-shot | T4 | reporting | CBTRN03C | 104 | 714 | 1192 | 0.598993 |
| zero-shot | T3 | interest | CBACT04C | 54 | 585 | 1029 | 0.568513 |
| zero-shot | T3 | posting | CBTRN02C | 18 | 651 | 1120 | 0.58125 |
| zero-shot | T3 | reporting | CBTRN03C | 56 | 655 | 1192 | 0.549497 |
| zero-shot | T4 | interest | CBACT04C | 54 | 585 | 1029 | 0.568513 |
| zero-shot | T4 | posting | CBTRN02C | 18 | 651 | 1120 | 0.58125 |
| zero-shot | T4 | reporting | CBTRN03C | 56 | 655 | 1192 | 0.549497 |


## Observações específicas dos conjuntos

- T1 original importado: `88` cenários; `43` schema-valid e `45` schema-invalid. Dos inválidos, `42` eram negativos intencionais executáveis e `3` eram má geração executável. Esses casos foram preservados como estímulos; não são provas de sucesso de negócio.
- T2 domina o volume (`5868` casos congelados), mas contém muitos `400` e `500` documentados; isso é útil para robustez contratual, não para inferir continuidade funcional positiva.
- T3 registra `expectation_inconclusive` em todos os `394` casos: o checker de negócio permaneceu inconclusivo/limitado. O freeze v3 removeu `7` casos com `guardResult != true`.
- SDD (`E3-SDD-stage6r3`) tem menos casos em T2/T4 porque o contrato expõe superfície mais estreita/selecionada; não comparar percentuais de volume como qualidade causal.
- O conjunto SDD tem corpos de requisição selecionados externamente/limitados em partes do fechamento T3; a evidência não autoriza equivalência funcional ampla nem superioridade causal.

## Limitações dos checkers brutos

- `campaign_harness._evaluate_expectation` aceita apenas expectativa de `status`; checks não suportados ou ausentes viram `inconclusive`.
- O checker estrutural do runner valida contrato OpenAPI: contrato conhecido, rota/método/operação, status documentado, `application/json`, JSON parseável e schema de resposta. Ele classifica 500 documentado como estruturalmente OK.
- Nenhum desses checkers é oráculo independente de negócio. Portanto, a leitura correta separa: execução técnica concluída, conformidade estrutural, falhas documentadas (`500`), requisições inválidas/documentadas (`400`) e expectativas de negócio inconclusivas.

## Arquivos produzidos

- `aggregate.json` — agregado reproduzível e evidências/hashes.
- `case_rows.csv` — 12.700 linhas normalizadas por caso.
- `suite_summary.csv` — 28 suítes e totais do runner.
- `freeze_suite_counts.csv` — recontagem independente das suítes congeladas.
- `counts_by_arm_contract_track_condition_status.csv` — tabela granular solicitada.
- `coverage_union_by_contract_condition_track.csv` — união gcov por contrato/condição/trilha/programa.
- `coverage_union_by_arm_condition_track.csv` — união gcov por braço/condição/trilha/programa.
