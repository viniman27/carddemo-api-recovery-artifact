# Desenho de validação complementar v2 — AWS CardDemo

Status: rascunho local concretizado, não congelado, sem campanha, sem chamada externa e sem autorização humana retropreenchida.

## Por que v2 substitui v1

A v1 permanece preservada em `P3/complementary-validation-v1/`, mas está rejeitada como desenho substantivo por três erros:

1. tratou `525` células obrigação×operação como se pudessem virar denominador semântico;
2. misturou `not_executed`, `unobservable` e `not_applicable` antes de qualquer execução;
3. usou três exemplos amplos, não um rol concreto de cenários para as 25 obrigações, e deixou T3 parecer uma bateria independente genérica em vez de MBT explícito.

Este v2 corrige sem editar a v1.

## Escopo e limites

- Escopo: desenho local de complemento semântico prospectivo para as 25 obrigações fonte-ancoradas de POSTTRAN, INTCALC e TRANREPT.
- Fora do escopo: campanha T1–T4, chamadas externas, alteração de contratos/APIs/COBOL/pesquisa principal, leitura de quarentena como autoridade, ou aprovação humana fictícia.
- A autorização registrada (`entao havera complemento ne? pode seguir?`) cobre este desenho local; não é tratada como autorização de campanha nem como concessão de expected outputs.

## Denominadores e estados corrigidos

- Obrigações: `25`.
- Contratos: `7`.
- Operações: `21`.
- Células obrigação×operação: `525` apenas para rastreabilidade/aplicabilidade.
- Células aplicáveis obrigação×contrato/operação: `175` (`25 × 7`, uma operação aplicável por contrato conforme trilha da obrigação).
- Células `not_applicable`: `350` (operações de outras trilhas).

Antes de execução complementar, as 175 células aplicáveis estão `not_executed`, `unchecked`, `no_observation` e `inconclusive`. As 350 restantes são `not_applicable`. O v2 proíbe usar `525` como denominador semântico.

Vocabulário separado: `not_executed`, `unchecked`, `inconclusive`, `nonexpressible`, `no_observation`, `failed`, `pass`, `not_applicable`.

## Papéis T1–T4

| Condição | Papel | Separação |
| --- | --- | --- |
| T1 | Geração LLM de cenários, quando autorizada. | Catálogo de geração separado do catálogo de avaliação; não expõe corpus de oráculo, quarentena, fixtures esperadas ou checkers. |
| T2 | Fuzzing/robustez OpenAPI puro. | Prova schema/status/content-type; qualquer checador de domínio adicional pertence à bateria de oráculo compartilhada, não ao mérito de OpenAPI puro. |
| T3 | Bateria MBT separada. | Mantém `reference-executable-v4/evidence/obligation-witnesses.json`, `transitionRefs` e witnesses; T3 não é colapsado no oráculo compartilhado. |
| T4 | União exata dos casos qualificados T1/T2/T3. | Sem casos novos; dedupe por operação + bytes exatos + pacote inicial + sequência + versão/target da expectativa; não é réplica independente. |

## Bateria compartilhada de oráculo

A bateria de checadores independentes é reutilizável sobre observações de T1–T4, mas sua independência está `pending_review_not_granted_by_this_design`. Ela deve ser congelada antes de execução futura e não pode ler quarentena de expected outputs nem outputs LLM melhorados pós-resultado.

## Rol fonte-ancorado de cenários — 25 obrigações

| Obrigação | Trilha | Condição inicial | Estímulo/semântica | Transições MBT | Observáveis | Partições práticas |
| --- | --- | --- | --- | --- | --- | --- |
| `POSTTRAN-OBL-001` | posting | DDs documentais do POSTTRAN disponíveis. | OPEN DALYTRAN input, TRANFILE output, XREF input, DALYREJS output, ACCOUNT I-O, TCATBAL I-O; status diferente de 00 em qualquer OPEN chama erro/abend. | `POSTTRAN-T001, POSTTRAN-T002` | status de abertura, mensagens, terminação | all DD/open statuses are 00 before first read; one required open returns non-00 and must stop before processing |
| `POSTTRAN-OBL-002` | posting | Arquivos abertos. | READ DALYTRAN status 00 mantém END-OF-FILE=N e processa; status 10 move END-OF-FILE=Y; outro status abende. | `POSTTRAN-T003, POSTTRAN-T004, POSTTRAN-T005, POSTTRAN-T006` | contador TRANSACTIONS PROCESSED, fechamento/abend | first read status 00 increments processed count; read status 10 ends loop without processing a new record; non-00/non-10 read status abends |
| `POSTTRAN-OBL-003` | posting | Transação validada sem razão de falha. | Move campos DALYTRAN para TRAN e substitui TRAN-PROC-TS por timestamp DB2-formatado. | `POSTTRAN-T012` | registro TRANFILE se escrita for alcançada e bem-sucedida | accepted transaction copies business fields from DALYTRAN; processing timestamp is current-date derived and not pre-fixed |
| `POSTTRAN-OBL-004` | posting | Registro diário lido; razão zerada. | READ XREF por DALYTRAN-CARD-NUM; INVALID KEY define razão 100 e descrição INVALID CARD NUMBER FOUND. | `POSTTRAN-T007, POSTTRAN-T008` | DALYREJS e ausência de postagem | card absent in XREF rejects with reason 100; card present continues to account checks without format-only validation |
| `POSTTRAN-OBL-005` | posting | XREF encontrado. | Conta ausente razão 101; conta presente calcula credit-debit+amount, razão 102 se excede limite; depois compara ACCT-EXPIRAION-DATE >= DALYTRAN-ORIG-TS(1:10) e pode mover razão 103. | `POSTTRAN-T008, POSTTRAN-T009, POSTTRAN-T010, POSTTRAN-T011` | trailer de rejeição ou caminho aceito | account absent rejects 101; account over limit rejects 102 unless later expiry check overwrites with 103; textual expiration comparison fails and final reason is 103 |
| `POSTTRAN-OBL-006` | posting | Razão de validação diferente de zero. | Incrementa contador, escreve 350 bytes originais + trailer 80; ao final RC=4 se reject count>0. | `POSTTRAN-T007, POSTTRAN-T009, POSTTRAN-T010, POSTTRAN-T011` | DALYREJS, contador e RETURN-CODE | one validation reason writes one reject trailer; normal close with reject count greater than zero returns RC 4 |
| `POSTTRAN-OBL-007` | posting | Transação aceita. | Chave = XREF-ACCT-ID + type + category; status 23 cria registro inicializado, status 00 atualiza; ambos somam DALYTRAN-AMT; status diferente de 00/23 em READ ou diferente de 00 em WRITE/REWRITE abende. | `POSTTRAN-T012, POSTTRAN-T013, POSTTRAN-T014` | registro TCATBAL ou abend | TCATBAL missing key creates initial category balance; TCATBAL existing key rewrites balance plus amount; TCATBAL I/O status outside documented set abends before account/TRANFILE effects |
| `POSTTRAN-OBL-008` | posting | Transação aceita, TCATBAL concluído e conta carregada. | Soma amount ao saldo; se amount>=0 soma ao credit, senão ao debit; REWRITE INVALID KEY move razão 109/descrição mas não chama abend local e o fluxo retorna para escrever TRANFILE. | `POSTTRAN-T013, POSTTRAN-T019, POSTTRAN-T020` | ACCOUNT lógico, WS-VALIDATION-FAIL-REASON 109 possível, próxima tentativa de TRANFILE | positive amount updates balance and credit; negative amount updates balance and debit; ACCOUNT rewrite invalid key records reason 109 but continues toward TRANFILE write |
| `POSTTRAN-OBL-009` | posting | Transação aceita e rotinas TCATBAL/ACCOUNT retornaram ao chamador. | WRITE FD-TRANFILE-REC; status 00 conclui postagem, status diferente de 00 exibe erro e chama abend. Não há validação prévia de duplicidade de DALYTRAN-ID/TRAN-ID na validação. | `POSTTRAN-T019, POSTTRAN-T020, POSTTRAN-T021, POSTTRAN-T022` | TRANFILE ou mensagem/abend após efeitos anteriores | TRANFILE write status 00 completes after prior effects; TRANFILE write non-00 abends after prior effects were attempted; duplicate DALYTRAN/TRAN id is not prevalidated before write |
| `INTCALC-OBL-001` | interest | Job INTCALC com PARM e DDs documentais. | Abre TCATBAL input sequencial, XREF/DISCGRP input, ACCOUNT I-O, TRANSACT output; falha abende. | `INTCALC-T001, INTCALC-T002` | status e registros de saída | required input/output files open before scan; PARM-DATE is available to transaction id construction; open failure abends before interest scan |
| `INTCALC-OBL-002` | interest | TCATBAL disponível. | A cada registro status 00, se TRANCAT-ACCT-ID muda, atualiza conta anterior exceto primeiro registro, zera total e carrega nova conta/xref. | `INTCALC-T003, INTCALC-T004` | updates ACCOUNT por grupo | first TCATBAL record initializes first account group; account id change updates previous group and resets total; same account contiguous records stay in one group; same account reappearing later is a new group |
| `INTCALC-OBL-003` | interest | Novo grupo. | Lê ACCOUNT por TRANCAT-ACCT-ID e XREF por alternate key FD-XREF-ACCT-ID; status não 00 abende. | `INTCALC-T003` | abend ou campos usados | ACCOUNT lookup by TCATBAL account succeeds; ACCOUNT lookup failure abends; XREF alternate-key lookup succeeds and supplies card; XREF lookup failure abends |
| `INTCALC-OBL-004` | interest | Conta e TCATBAL carregados. | Lê DISCGRP por group/type/category; status 23 tenta group DEFAULT preservando type/category; DEFAULT ausente abende. | `INTCALC-T007, INTCALC-T008, INTCALC-T009Z` | DIS-INT-RATE ou abend | specific group/type/category discount exists; specific missing and DEFAULT exists; both specific and DEFAULT missing abends |
| `INTCALC-OBL-005` | interest | Taxa lida. | Só se DIS-INT-RATE != 0 calcula (TRAN-CAT-BAL*DIS-INT-RATE)/1200, acumula WS-TOTAL-INT e escreve TX. | `INTCALC-T007, INTCALC-T009, INTCALC-T009Z` | TRAN-AMT e total acumulado | non-zero rate attempts monthly interest formula and write; zero rate returns to scan with no interest transaction; numeric amount value remains pending COBOL/PIC qualification |
| `INTCALC-OBL-006` | interest | Juros calculados. | TRAN-ID=PARM-DATE+sufixo; type 01; cat 05; source System; desc Int. for a/c + ACCT-ID; amount mensal; merchant zero/spaces; card XREF; timestamps current. | `INTCALC-T009, INTCALC-T010, INTCALC-T011` | TRANSACT output | interest transaction fields are moved from PARM/account/xref/source constants; current timestamps are generated at runtime; literal/type/category physical representation stays pending review |
| `INTCALC-OBL-007` | interest | Mudança de conta depois da primeira. | 1050 soma WS-TOTAL-INT ao saldo, zera credit/debit e reescreve. | `INTCALC-T010` | ACCOUNT | group break after first group invokes account update; update adds accumulated interest and clears credit/debit; rewrite failure abends |
| `INTCALC-OBL-008` | interest | EOF normal após zero ou mais registros. | READ status 10 move END-OF-FILE=Y dentro de iteração iniciada com END=N; PERFORM UNTIL termina antes do ELSE externo. | `INTCALC-T006` | ACCOUNT do último grupo | EOF normal after empty input closes without loaded-account assumptions; EOF after last group reaches close path without final 1050 update |
| `TRANREPT-OBL-001` | reporting | JCL TRANREPT documental. | REPROC descarrega, SORT ordena por card e filtra por proc date, STEP10 roda CBTRN03C com arquivos de lookup e report. | `TRANREPT-T001, TRANREPT-T002` | TRANFILE efetivo e TRANREPT | effective TRANFILE input is sorted by card for report semantics; JCL/proc filter and COBOL DATEPARM are treated as separate documentary inputs; lookup/report files open before details |
| `TRANREPT-OBL-002` | reporting | DATEPARM disponível. | Lê start/end X(10); após cada READ TRANFILE, inclusive quando EOF foi marcado, testa TRAN-PROC-TS(1:10) >= start e <= end antes do ramo END-OF-FILE. Fora do intervalo executa NEXT SENTENCE. | `TRANREPT-T003, TRANREPT-T012` | mensagem e presença/ausência de detalhe/totais | record proc date text inside range reaches lookups/detail; record proc date text before/after range produces no detail/no accumulation; EOF receiver/date path is unknown unless observed by runtime |
| `TRANREPT-OBL-003` | reporting | Arquivos abertos e DATEPARM ok. | READ status 00 deixa END=N; status 10 move END=Y; outros abendem. O teste de data acontece após o READ e antes do IF END=N/ELSE de totais. | `TRANREPT-T009` | relatório, ausência de relatório ou abend | read status 00 keeps END=N and can process record; read status 10 sets END=Y then date test still gates total branch; read status other abends |
| `TRANREPT-OBL-004` | reporting | Transação no intervalo e END=N. | Em card novo escreve total anterior se não primeira ocorrência; lê XREF. Para todo registro lê tipo e categoria; chave ausente abende. | `TRANREPT-T003` | detalhe ou abend | new card writes previous account total except first occurrence; XREF lookup missing abends; type/category lookup missing abends; successful lookups feed detail text |
| `TRANREPT-OBL-005` | reporting | Primeiro detalhe ou boundary. | Primeiro detalhe escreve headers com date range; quando MOD(line-counter,20)=0 escreve page total e headers. | `TRANREPT-T003, TRANREPT-T014, TRANREPT-T015` | linhas de relatório | first detail writes report headers; line-counter modulus boundary writes page total and headers; page size is line-counter based, not 20 detail rows |
| `TRANREPT-OBL-006` | reporting | Lookups concluídos para registro no intervalo. | Soma TRAN-AMT a WS-PAGE-TOTAL e WS-ACCOUNT-TOTAL; move id, account, type code/desc, category code/desc, source e amount para detail. | `TRANREPT-T016` | TRANREPT detail e acumuladores | each qualified transaction writes one detail line; amount accumulates into page and account totals; type/category/account descriptions come from lookups |
| `TRANREPT-OBL-007` | reporting | END=Y após READ e teste textual anterior não desviou por NEXT SENTENCE. | Ramo ELSE de END soma TRAN-AMT corrente a page/account, escreve page totals, soma page ao grand, zera page e escreve grand totals. | `TRANREPT-T010, TRANREPT-T011, TRANREPT-T013, TRANREPT-T016` | Page Total/Grand Total | EOF branch reachable only after preceding date guard permits it; page total and grand total are written from current accumulated values; possible retained TRAN-AMT addition is conditional, not universal |
| `TRANREPT-OBL-008` | reporting | Um ou mais detalhes para último cartão sem mudança subsequente de cartão. | 1120-WRITE-ACCOUNT-TOTALS é chamado apenas em mudança de cartão quando não é primeira ocorrência; ramo EOF chama page/grand totals e não chama 1120. | `TRANREPT-T010` | Account Total final ausente/presente só por mudança anterior | single-card interval has no final account total call at EOF; last card total appears only if a later card break occurred; absence of final account total does not imply page/grand totals always occur |

## Arquivos normativos deste v2

- `scenario-catalog.json`: catálogo legível por máquina com os 25 cenários, 525 células de mapeamento e pins de fonte.
- `obligation-operation-mapping.csv`: visão tabular das células, com estados pré-execução separados.
- `schema/complementary-validation-v2.schema.json`: schema mínimo referenciado pelo catálogo.
- `validate_catalog.py`: validador estrito de contagens, cobertura por obrigação, hashes, source pins, status e T3 MBT.
- `tests/test_validator.py`: testes TDD do validador.
- `VALIDATION-REPORT.md`: execução real observada.
