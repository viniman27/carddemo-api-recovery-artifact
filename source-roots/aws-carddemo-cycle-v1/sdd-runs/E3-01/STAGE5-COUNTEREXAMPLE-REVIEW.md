# Revisão Stage 5 — contraexemplos de fronteira canônica

**Conclusão técnica:** recomendo **aceitação humana condicionada ao escopo documental já autorizado**, sem aprovação automática. Não encontrei contradição source-grounded que exija regenerar a Stage 5 antes da decisão humana. A recomendação é limitada: não fecha os gaps de runtime, não aprova Stage 6 e não transforma validação mecânica em completude semântica.

## Escopo efetivamente inspecionado

- RUN_ROOT: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/sdd-runs/E3-01`
- Corpus: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-preparation/research-corpus`
- Entradas existentes revisadas: **32** arquivos, incluindo **19** arquivos do corpus permitido.
- Código obrigatório lido integralmente: `CBTRN02C.cbl`, `CBACT04C.cbl`, `CBTRN03C.cbl`.
- Também revisados: copybooks/JCL/proc allowlisted, Stage 5 completo, escopo original preparado, Stage 4 aprovado, Stage 3-r2, review Stage 4, authorizations e verificações mecânicas relevantes.
- Restrições obedecidas: revisão documental local; sem execução COBOL/JCL; sem rede/model generation; sem alteração de specs originais, aprovações, framework ou quarentena.

## Contagens independentes

| Item | Contagem |
|---|---:|
| Regras Stage 4 definidas (`R-1`..`R-20`) | 20 |
| Linhas de disposição Stage 5 para regras | 20 |
| Decisões Stage 5 (`D-2`..`D-8`) | 7 |
| Tipos canônicos Stage 5 | 17 |
| Linhas de recursos/estado Stage 5 | 31 |
| Variantes de outcome Stage 5 | 20 |
| Casos de contraexemplo R-n revisados | 20 |
| Achados D-n revisados | 7 |
| Âncoras explícitas full-path Stage 5 | 46 |
| Âncoras shorthand Stage 5 | 18 |
| Ocorrências totais de âncoras Stage 5 | 64 |
| Ranges únicos de âncora | 59 |

A verificação mecânica existente contava **46** âncoras explícitas full-path. Esta revisão confirmou essas 46 e também resolveu/validou **18** shorthand anchors no contexto da última path explícita da mesma citação. Todas as âncoras ficaram dentro dos limites dos arquivos.

## Resultado dos hashes e âncoras

- Hashes de autoridades declarados na Stage 5: **0 divergências**.
- Hashes dos 19 arquivos do corpus contra Stage 3-r2: **0 divergências**.
- Bounds de âncoras explícitas/shorthand da Stage 5: **0 falhas**.
- Hashes das entradas revisadas foram capturados antes e depois da escrita deste relatório; o JSON anexo registra os digests.

## Revisão dos D decisions

| Decisão | Resultado | Base |
|---|---|---|
| D-2 | not_falsified | Stage5 lines 100-105; R-3/R-7/R-11/R-13/R-19; source roles remain track-qualified. |
| D-3 | not_falsified | Stage5 lines 107-112 and Section 6; internal resources not promoted to consumer state APIs. |
| D-4 | not_falsified | Stage5 lines 114-119; R-6/R-18/R-20 preserve non-atomic and unknown failure/repetition. |
| D-5 | not_falsified | Stage5 lines 121-126; numeric/identifier/temporal policies remain unresolved. |
| D-6 | not_falsified | Stage5 lines 128-133; R-8/R-12/R-14/R-15 omissions not repaired. |
| D-7 | not_falsified | Stage5 lines 135-140; presentation and operational details bounded. |
| D-8 | not_falsified | Stage5 lines 142-147; filler/declaration-only/fee placeholder not promoted while evidence retained. |

## Contraexemplos por regra R-1..R-20

| Regra | Trilha | Resultado | Conclusão | Citações |
|---|---|---|---|---|
| R-1 | posting | not_falsified | Contador/reason reset antes de 1500; razão zero seleciona 2000, não-zero seleciona rejeição; EOF apenas seta flag. | Stage4 R-1 lines 143-149; Stage5 matrix line 363; CBTRN02C.cbl:202-215,345-369. |
| R-2 | posting | not_falsified | Guard por razão zero e comparações >= preservados; 103 posterior sobrescreve 102. | Stage4 R-2 lines 151-157; Stage5 lines 189,253-257,364; CBTRN02C.cbl:370-422. |
| R-3 | posting | not_falsified | Campos transferidos e timestamp novo distinguem transação; rejeição move registro diário + trailer; filler não recebeu significado. | Stage4 R-3 lines 159-165; Stage5 lines 157-159,203-208,365; CBTRN02C.cbl:424-465,692-705; CVTRA05Y.cpy:5-17; CVTRA06Y.cpy:5-17. |
| R-4 | posting | not_falsified | Ordem 2700 antes de 2800/2900; flag de criação e status 00/23 retidos; erro segue abend local. | Stage4 R-4 lines 167-173; Stage5 lines 161,309,366; CBTRN02C.cbl:440-442,467-542. |
| R-5 | posting | not_falsified | ADD usa sinal; 109 é atribuído no REWRITE e o caller prossegue a 2900 em retorno normal. | Stage4 R-5 lines 175-181; Stage5 lines 190,258,308,367; CBTRN02C.cbl:545-560 and caller 440-442. |
| R-6 | posting | not_falsified | Stage5 mantém tentativas ordenadas e efeitos duráveis desconhecidos; não cria contagem de postados. | Stage4 R-6 lines 183-189; Stage5 lines 116-119,259-260,310,368; CBTRN02C.cbl:221-234,254-270,424-579. |
| R-7 | interest | not_falsified | Mudança de conta encontrada dirige update do grupo anterior; xref/disclosure são dependências internas. | Stage4 R-7 lines 191-197; Stage5 lines 167,269,318-320,369; CBACT04C.cbl:188-218,350-413. |
| R-8 | interest | not_falsified | Sem chamada pós-loop; EOF normal não reentra no ELSE; distinção transação/conta preservada. | Stage4 R-8 lines 199-205; Stage5 lines 130-132,270,319,370; CBACT04C.cbl:188-228,325-370,462-515. |
| R-9 | interest | not_falsified | Somente status 23 dispara DEFAULT; segundo read exige 00; missing não é zero. | Stage4 R-9 lines 207-213; Stage5 lines 168,266,321,371; CBACT04C.cbl:415-460. |
| R-10 | interest | not_falsified_with_deferred_note | Selector é taxa != 0; fórmula e receivers retidos. Nota: a linha de mapeamento 222 ancora cálculo/acúmulo, mas o guard direto está via R-10/E-12/E-14 e outcome, não no mesmo anchor local. | Stage4 R-10 lines 215-221; Stage5 lines 170,222,267-268,372; CBACT04C.cbl:166-173,214-217,462-470. |
| R-11 | interest | not_falsified | Sufixo local + parâmetro; literais e timestamp local preservados; fee limitado ao placeholder inspecionado. | Stage4 R-11 lines 223-229; Stage5 lines 169-171,221,223-227,373; CBACT04C.cbl:175-180,473-520,613-626; INTCALC.jcl:20-41. |
| R-12 | reporting | not_falsified | NEXT SENTENCE sai da sentença do loop; DATEPARM EOF seta flag compartilhada; comparação precede teste EOF. | Stage4 R-12 lines 231-237; Stage5 lines 178,277-279,331-332,374; CBTRN03C.cbl:159-243,248-272. |
| R-13 | reporting | not_falsified | Trigger é mudança de cartão; xref fornece conta exibida; cardinalidade e persistência seguem abertas. | Stage4 R-13 lines 239-245; Stage5 lines 180,281,334,375; CBTRN03C.cbl:179-196,484-512. |
| R-14 | reporting | not_falsified | Sites de page/account/grand e resets distintos preservados. | Stage4 R-14 lines 247-253; Stage5 lines 182,240,337-339,376; CBTRN03C.cbl:274-322,343-359. |
| R-15 | reporting | not_falsified | EOF finaliza só se comparação anterior permitir; adiciona e chama page/grand, sem account-total; duplicação permanece hipótese. | Stage4 R-15 lines 255-261; Stage5 lines 130-132,280,284,338,377; CBTRN03C.cbl:170-206,287-322. |
| R-16 | reporting | not_falsified | Line counter avança em headers/totais/detalhes; receivers de descrição/valores são limitados e tratados como apresentação/proveniência. | Stage4 R-16 lines 263-269; Stage5 lines 137-139,180-183,237-240,340,378; CBTRN03C.cbl:274-374; CVTRA07Y.cpy:4-66. |
| R-17 | reporting | not_falsified | Stage5 mantém seleção upstream documental separada, sem override comum e com executabilidade aberta. | Stage4 R-17 lines 271-277; Stage5 lines 179,235,333,379; TRANREPT.jcl:19-80; CBTRN03C.cbl:170-177,220-243; REPROC.prc:19-29. |
| R-18 | all | not_falsified | Stage5 limita-se a chamada externa e falha local; não inventa política de API/erro. | Stage4 R-18 lines 279-285; Stage5 lines 116-119,193,259,271,282,351,380; CBTRN02C.cbl:707-711; CBACT04C.cbl:628-632; CBTRN03C.cbl:626-630. |
| R-19 | all | not_falsified | Recursos compartilhados são contexto operacional; REPROCT ausente e labels duplicados seguem gap. | Stage4 R-19 lines 287-293; Stage5 lines 347-350,381; POSTTRAN/INTCALC/TRANREPT/COMBTRAN/TRANBKP/REPROC anchors. |
| R-20 | all | not_falsified | Repetition safety é unknown por trilha; nenhum reset/retry/compensação inventado. | Stage4 R-20 lines 295-301; Stage5 lines 297,324-325,341,347-349,382; E-5,E-9–E-12,E-14–E-19,E-32–E-34. |

## Categorias de risco solicitadas

- **Tipos/campos:** tipos canônicos mantêm proveniência conceitual e não viram layouts físicos. Campo filler, customer declaration e fee placeholder não são promovidos a obrigação (`D-8`; Stage5 lines 142-147, 397-408).
- **Ausência vs zero:** missing disclosure, zero-rate bypass, zero computed value, finalização ausente e output unknown permanecem distintos (`R-8`–`R-10`, `R-15`, `R-18`; Stage5 lines 192, 266-270, 284).
- **Truncation/presentation:** descrições e amounts de relatório preservam limites de receiver/display e line counter; Stage5 não promete lossless description nem 20 detalhes por página (`R-16`; CBTRN03C.cbl:274-374; CVTRA07Y.cpy:4-66).
- **Incerteza numérica:** unidades/rate policy/overflow/rounding não foram fechados; o cálculo literal e receivers `S9(09)V99` foram preservados (`R-10`, `R-11`; CBACT04C.cbl:166-173, 462-470).
- **Original/reject vs posted:** candidato diário, transação preparada e rejeição são separados; reason 109 pós-rewrite não vira `PostingRejection` automaticamente (`R-3`, `R-5`).
- **Observabilidade interna:** Stage5 expõe estado/tentativas como `AttemptState` e recursos internos, sem transformá-los em controles de consumidor ou API.
- **Outcomes:** variantes preservam guardas e não prometem durabilidade, completude de range ou rollback.
- **Identidade cross-track:** nenhuma identidade global de transação/card/account ou ciclo executado foi inferida (`D-2`, `R-19`).
- **EOF:** interest EOF normal sem final flush e reporting EOF condicional permanecem sem reparo; buffer pós-EOF não foi inventado (`R-8`, `R-12`, `R-15`).
- **Falha não atômica:** posting/interest/reporting mantêm tentativas ordenadas e efeitos duráveis desconhecidos; erro não implica output vazio/inalterado (`D-4`, `R-6`, `R-18`).
- **No invented API policy:** N/A para superfície de API; nenhum endpoint/status/retry/idempotência foi introduzido. A falha externa fica como chamada `CEE3ABD` sem semântica de rollback/retorno.

## Blockers, gaps deferidos e N/A

### Blockers encontrados nesta revisão

Nenhum blocker source-grounded novo foi encontrado contra a Stage 5 atual.

### Gaps que permanecem deferidos

- `G-15/G-20`: este relatório fornece revisão substantiva e verificação mecânica independente, mas não fecha aprovação humana nem edita o artefato Stage 5.
- `G-16`: report/JSON foram criados; retenção/digest final de gate continua externa.
- `G-17`: unidades, política numérica/temporal, overflow, validade de parâmetro e truncation permanecem bloqueadores de claims fortes.
- `G-18`: durabilidade, identidade de recurso, isolamento, reset e repetição permanecem unknown.
- `G-19`: EOF storage, datas concretas, job flow executado e totais numéricos permanecem unknown.

### N/A justificado

- API contract/adapter behavior: fora do Stage 5; só verifiquei ausência de política/API inventada.
- Runtime outcome validation: proibido pela tarefa; não executei COBOL/JCL.
- Aplicabilidade institucional: fora do corpus público; Stage5 mantém nota de evidência separada.

## Recomendação

Recomendo que o humano aceite a Stage 5 **apenas como fronteira canônica documental condicionada**, com os gaps acima preservados e sem tratar esta revisão como aprovação automática. A Stage 5 está semanticamente coerente com `R-1`–`R-20` nos cenários de tentativa de refutação examinados aqui, mas continua não pronta para implementação e não deve autorizar Stage 6 sem decisão humana explícita.
