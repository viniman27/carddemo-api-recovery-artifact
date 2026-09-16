# Contrainterpretação e limitações — campanha AWS CardDemo official large12k

## Escopo auditado

Auditei diretamente os artefatos executados, não resumos derivados:

- relatório oficial: `P3/official-campaign-large12k-run-v2/campaign-report.json`;
- suites congeladas: `P3/campaign-freeze-package-v3/{E1,E2,E3}/T{1..4}.json`;
- contrato SDD materializado: `P2a/openapi-carddemo-stage6r3.json`;
- prontidão/freeze: `P3/campaign-freeze-package-v3/MANIFEST.json` e `FINAL-READINESS.json`.

Não alterei APIs, runners, suites, contratos, fixtures ou execuções originais. Os dados derivados desta revisão ficam em `P3/official-analysis-review-v1/`.

## Resultado principal

A campanha prova uma coisa forte, mas estreita: **o harness oficial conseguiu executar 12.700 casos, preservar recibos, aplicar a checagem estrutural do contrato e classificar todos como estruturalmente aceitáveis segundo os status documentados**.

Ela **não** prova que 12.700 casos foram sucessos funcionais de negócio, nem que a cobertura estrutural HTTP/contratual equivale a completude semântica COBOL. O próprio conjunto de recibos mostra o contrário: dos 12.700 casos, só 1.068 retornaram HTTP 200; 7.254 retornaram HTTP 500 e 4.378 retornaram HTTP 400. A admissibilidade de medição de cobertura ficou em 1.070 casos, porque 11.630 casos foram marcados como `inadmissible_or_limited`, sempre por `audit_missing_for_current_case_track`.

Em outras palavras: **100% estrutural** significa “resposta encaixou nos status/esquemas aceitos pelo contrato/harness”, não “100% comportamento de negócio”.

## Números globais

| Medida | Contagem | Percentual |
|---|---:|---:|
| Casos planejados/tentados/concluídos | 12.700 | 100,00% |
| `structural_ok=true` | 12.700 | 100,00% |
| HTTP 200 | 1.068 | 8,41% |
| HTTP 400 | 4.378 | 34,47% |
| HTTP 500 | 7.254 | 57,12% |
| Medição `admissible_preparatory` | 1.070 | 8,43% |
| Medição `inadmissible_or_limited` | 11.630 | 91,57% |

Classificação estrutural no relatório:

| Classe estrutural | Contagem |
|---|---:|
| `documented_500_schema_valid` | 7.254 |
| `schema_valid` | 5.446 |

Essa é a chave da aparente contradição: os 7.254 HTTP 500 entram como sucesso estrutural porque 500 estava documentado e o corpo respondeu ao esquema esperado. Isso é correto para checagem contratual, mas fraco como evidência de negócio.

## Por experimento

| Experimento | Casos | HTTP 200 | HTTP 400 | HTTP 500 | Admissíveis | Inadmissíveis/limitados |
|---|---:|---:|---:|---:|---:|---:|
| E1 zero-shot | 5.774 | 256 | 0 | 5.518 | 256 | 5.518 |
| E2 few-shot | 5.722 | 526 | 3.460 | 1.736 | 528 | 5.194 |
| E3 SDD | 1.204 | 286 | 918 | 0 | 286 | 918 |

Leitura:

- **E1** quase sempre chegou ao adaptador com entradas estruturalmente aceitas pelo contrato, mas operacionalmente ruins para a amarração real: 95,57% dos casos E1 retornaram 500. As respostas decodificadas recorrentes incluem `unresolved local binding token`, validações de schema e erros de codificação ASCII.
- **E2** melhorou a ligação com a forma real de execução em parte dos casos, mas também concentrou 400 e 500. Muitos 400 são `{}` e representam rejeição de representação; muitos 500 são falhas técnicas de codificação/dados. Só 526/5.722 foram 200.
- **E3/SDD** não retornou 500 na campanha, mas isso não significa maior sucesso semântico. O contrato SDD aceitou explicitamente `{}` como corpo válido das três operações e modelou 400 como `request_representation`; assim, 918/1.204 casos foram 400 e 286 foram 200 com envelopes do tipo `completeness: not_attested` e `durability: unknown`.

## Por condição de teste

| Condição | Casos | HTTP 200 | HTTP 400 | HTTP 500 | Admissíveis |
|---|---:|---:|---:|---:|---:|
| T1 — cenários preservados | 88 | 19 | 37 | 32 | 20 |
| T2 — fuzz OpenAPI | 5.868 | 177 | 2.124 | 3.567 | 177 |
| T3 — obrigações/fixtures | 394 | 338 | 28 | 28 | 338 |
| T4 — união | 6.350 | 534 | 2.189 | 3.627 | 535 |

A condição T4 não é uma nova família independente de diversidade: ela é a união/reexecução dos casos T1+T2+T3. Há 6.350 `request_identity` únicos na campanha inteira, cada um aparecendo duas vezes no conjunto global de 12.700: uma vez em T1/T2/T3 e outra em T4. Portanto, T4 mede recorrência/reexecução da união, não duplica a evidência semântica independente.

## Por que 100% estrutural coexistiu com muitos 500

### 1. O contrato documentou status de falha como aceitáveis

Nos contratos E1, os status permitidos eram, em geral, `[200, 500]`. Nos contratos E2, `[200, 400, 500]`. No contrato SDD, `[200, 400, 500, 503]` nas operações, embora a campanha E3 observada tenha produzido 200/400.

Exemplos reais decodificados:

- `T1-REAL-E1-1-E1-1-posting-positive-01` retornou 500 com corpo:
  `{"message":"technical_failure","program":"CBTRN02C","diagnostics":["ValueError(\"unresolved local binding token: 'TRANFILE'\")"]}`.
  A expectativa permitia `[200,500]`, logo passou estruturalmente.
- `T2-E1-1-E1-1-POST-postDailyTransactions-seed104729-positive-9` retornou 500 por `recordBase64 must decode to 350 bytes`; também era um 500 documentado.
- `T2-E2-1-E2-1-POST-postDailyTransactions-seed104729-positive-3` retornou 500 por `UnicodeEncodeError(... 'ordinal not in range(128)')`; E2 permitia `[200,400,500]`.

Esses casos são evidência de robustez do harness/contrato para registrar falhas previstas, não evidência de sucesso de negócio.

### 2. T2 gerou diversidade estrutural/fuzz, não diversidade de negócio validada

T2 veio de Schemathesis/OpenAPI e preservou bytes/headers, mas os corpos decodificados mostram entradas que exercitam fronteiras técnicas: strings não ASCII, `recordBase64` inválido, campos vazios, corpos `{}` e valores fora da representação COBOL. Isso é útil para pressão estrutural, mas não equivale a cenários de negócio válidos.

Exemplos:

- E1 T2: `transactionFile: "0"`, `accountFile: "0"`, `dailyTransactions: []` gerou `unresolved local binding token: '0'`.
- E2 T2: strings com Unicode aleatório geraram `UnicodeEncodeError`.
- Muitos 400 E2 têm corpo de resposta `{}`, isto é, rejeição estrutural/representacional, não comportamento de negócio.

### 3. T1 preservou requisições, mas não promoveu oráculos esperados

As suites T1 carregam marcadores como `expectedAssertionsQuarantined=true` e `expectedAssertionsPolicy=contract_assertion_quarantined_not_oracle`. Isso é metodologicamente correto: preserva o cenário sem usar o esperado gerado como oráculo independente. Mas o efeito interpretativo é que T1 não pode ser lido como validação semântica ampla; ele é estímulo executável + status estrutural.

### 4. T3 tem a melhor proporção de 200, mas o checker de obrigação ainda ficou inconclusivo

T3 é a condição mais forte em execução observável: 338/394 casos retornaram 200 e foram `admissible_preparatory`. Porém todos os T3 carregam `expectation_result=inconclusive`, com `unsupported_checks` para `contract_checker` e `expected_status_source`. Assim, T3 demonstra ligação técnica com fixtures e execução melhor que T1/T2, mas ainda não fecha comparação de obrigação independente.

### 5. SDD aceitou `{}` como contrato de requisição

No contrato SDD materializado, as três requisições são objetos fechados vazios:

- `PostingRequest`: `type: object`, `additionalProperties: false`, `required: []`, `properties: {}`;
- `InterestRequest`: mesma forma;
- `ReportingRequest`: mesma forma.

O próprio contrato anota: “Required empty closed JSON object; missing body/null/array/properties invalid”. Isso explica por que E3/SDD teve muitos 200 com request `{}` e muitos 400 para qualquer representação diferente. O resultado mede um boundary SDD deliberadamente estreito, não uma interface rica de negócio.

Contagens de `{}` em E3:

| Condição E3 | Posting `{}` | Interest `{}` | Reporting `{}` |
|---|---:|---:|---:|
| T1 | 1 | 1 | 1 |
| T2 | 6 | 6 | 6 |
| T3 | 17 | 28 | 77 |
| T4 | 24 | 35 | 84 |

### 6. `allOf` e envelopes SDD favorecem aceitação estrutural de disponibilidade, não completude

O OpenAPI SDD usa `allOf` em campos como `InterestEnvelope.outputs` e `ReportingEnvelope.records`, combinando uma referência de disponibilidade com `availability: available`. As notas dizem “items may be []” e os retornos 200 trazem `completeness: not_attested` e `durability: unknown`. Portanto, ainda que o `allOf` seja estruturalmente validável, ele não deve ser interpretado como merge semântico de obrigações COBOL completas.

## Por que houve poucos admissíveis de cobertura/medição

A razão operacional dominante é única: `audit_missing_for_current_case_track`.

Todos os 11.630 casos inadmissíveis/limitados trazem essa razão. Isso significa que a resposta HTTP existe e foi checada estruturalmente, mas a evidência de auditoria/cobertura para o track daquele caso não foi vinculada/admissível no critério do runner.

Por isso, a “cobertura” reportada precisa ser separada em duas camadas:

1. **Cobertura estrutural do harness/contrato:** 12.700/12.700 `structural_ok`.
2. **Medição admissível associada à execução/auditoria:** 1.070/12.700.

Não há base para transformar a primeira em “cobertura COBOL completa” ou “cumprimento de obrigações de negócio”.

## Comparação E1/E2/SDD: o que é justificável

Comparação justificada:

- comparar quantidade de casos executados por braço/condição;
- comparar distribuição de status HTTP;
- comparar taxa de resposta estruturalmente válida;
- comparar taxa de admissibilidade preparatória;
- comparar classes de falhas técnicas observadas;
- comparar quão estreito/largo cada contrato tornou o espaço de requisições aceitas.

Comparação não justificada sem qualificação:

- dizer que E3/SDD é semanticamente superior porque teve zero 500;
- dizer que E1/E2 “falharam funcionalmente” só porque geraram muitos 500, pois muitos 500 estavam documentados como falha técnica prevista;
- dizer que HTTP 200 é sucesso de negócio, porque há 200 com `returnCode: 4`, `rejectedCount`, `completeness: not_attested`, `durability: unknown` ou listas vazias;
- dizer que `structural_ok=100%` é cobertura de obrigações COBOL;
- usar T4 como amostra independente adicional, já que T4 é reexecução da união.

Interpretação comparativa mais defensável:

- **E1** expôs contratos zero-shot amplos/instáveis na amarração operacional: muitos campos de binding foram tratados como tokens locais inválidos ou formatos incompatíveis. A alta taxa de 500 é evidência de desalinhamento de boundary/fixture, não necessariamente de falha do COBOL.
- **E2** reduziu parte do desalinhamento e permitiu mais 200, mas também documentou 400/500 de forma ampla. A campanha mostra melhor encaixe de certas representações e grande sensibilidade a fuzz técnico.
- **E3/SDD** reduziu falhas 500 ao estreitar a requisição para `{}` e explicitamente separar `request_representation` (400), mas isso desloca a questão: o boundary é limpo e estável, porém de baixa diversidade de entrada de negócio e com completude não atestada.

## Evidências sobre fixtures e seleção de recursos

O freeze v3 registra 18 recursos físicos pinados por bytes/hash, incluindo `XREFFILE.1` em interest/posting, e `FINAL-READINESS.json` registra testes unitários da seleção externa/local de fixtures com resultado `OK, 3 tests, 0.038s`. Isso sustenta que havia mecanismo de fixture e reset físico.

Limite: nos casos T2/T4, muitos parâmetros continuam marcados como `fixtureBindingStatus=candidate_not_official` e `fixtureBindingAuthority=campaign-config-v2 fixturesCandidates bytes; no oracle promotion`. Isso é suficiente para seleção técnica de execução, mas não promove fixture a oráculo de negócio.

Também há uma inconsistência interpretativa a registrar: o contexto fala em `Configv3`, e o freeze é `campaign-freeze-package-v3`, mas o `campaign-report.json` executado declara `campaignConfig.path` como `P3/campaign-configuration-v2/campaign-config-v2.json`. Pode haver uma razão histórica/mecânica para isso, mas o relatório desta campanha, lido isoladamente, não autoriza chamar a execução de “config v3” sem explicar essa discrepância.

## Ameaças à validade / limitações

1. **Oráculo independente ausente ou incompleto.** T3 preserva obrigações, mas o próprio recibo marca checker/status-source como inconclusivos. T1/T2 não usam expected outputs em quarentena como oráculo.
2. **Status documentado amplo.** Contratos que aceitam 500/400 tornam a checagem estrutural robusta, mas menos discriminativa para negócio.
3. **Baixa diversidade de negócio no SDD.** O SDD aceita `{}` como request completo; a diversidade de inputs de negócio fica fora da requisição pública e depende de fixture interna.
4. **T4 não é amostra independente.** É a união/replay de T1+T2+T3; todos os 6.350 `request_identity` aparecem duas vezes no conjunto de 12.700.
5. **Medição de cobertura admissível é minoritária.** 91,57% dos casos têm auditoria/cobertura inadmissível/limitada por falta de auditoria do track corrente.
6. **HTTP 200 não é sucesso funcional.** Exemplos incluem `returnCode: 4`, rejeições, listas vazias e `completeness: not_attested`.
7. **Cobertura estrutural não é cobertura COBOL.** `structural_ok` verifica status/esquema documentado; não mede branch coverage nem obrigação de negócio COBOL.
8. **Fuzz técnico domina T2.** Entradas Unicode, base64 inválido e campos vazios exercitam robustez de representação, não necessariamente regras de negócio válidas.

## Conclusão curta

A campanha é válida como evidência de **execução oficial, rastreabilidade de recibos, preservação de bytes/hashes e conformidade estrutural com contratos congelados**. Ela também é útil para comparar como E1, E2 e SDD moldam o espaço de falhas.

A interpretação precisa ser limitada: **não há base para vender os 12.700/12.700 como sucesso funcional, nem para usar 100% estrutural como completude de obrigações COBOL**. A leitura mais defensável é que a campanha revelou, em escala, a diferença entre aceitação contratual de fronteira e validação semântica admissível: a primeira foi total; a segunda foi parcial e concentrada em 1.070 casos, especialmente T3 e subconjuntos tecnicamente bem amarrados.
