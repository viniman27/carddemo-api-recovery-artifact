# Revisão da referência candidata AWS CardDemo
Status: `partial_reviewed_draft_not_frozen`. Esta revisão não aprova gates, não executa COBOL, não executa extrações e não alega completude.
## Escopo e limites
- Rascunho inicial não é cego: foi produzido em contexto de coordenação já exposto a preflight.
- Revisão documental apenas nos 19 arquivos allowlisted; não leu outputs de braços experimentais.
- Sem execução de COBOL, sem extração LLM, sem aprovação de gates e sem alegação de completude.
- Âncoras são por path relativo ao corpus completo e hashes; não são prova de semântica dinâmica.

## Resultado documental
- Arquivos permitidos lidos pelo manifesto: 19 de 19.
- Registros no rascunho original: 16; registros revisados/adicionados: 34.
- Original preservado: `evaluation-quarantine/obligations-draft.json`.
- Saída JSON revisada: `evaluation-quarantine/obligations-reviewed-draft.json`.

## Correções relevantes
- `P-07`: explicitado que transação negativa é somada como valor negativo a `ACCT-CURR-CYC-DEBIT`, não convertida para absoluto.
- `I-01`/`T-02`: não congelar atualização final de conta em `CBACT04C`; fluxo textual de EOF torna a chamada final a `1050-UPDATE-ACCOUNT` bloqueante.
- `R-01`: relatório tem filtro inclusivo em JCL SORT e também filtro interno via `DATEPARM`; precedência precisa de decisão.
- `R-02`/`T-03`: totalização no EOF de `CBTRN03C` é bloqueante textual: adiciona `TRAN-AMT` no ramo EOF e não escreve total de conta final nesse ramo.
- `R-03`: detalhes de relatório devem respeitar truncamento/formatação do copybook `CVTRA07Y`.

## Obrigações acrescentadas
- `L-01`: Preservar layout físico de ACCOUNT-RECORD: 300 bytes, ACCT-ID 9(11), saldos/limites S9(10)V99, datas X(10), campos de ciclo e nome literal ACCT-EXPIRAION-DATE.
- `L-02`: Preservar layout CARD-XREF-RECORD: cartão X(16), cliente 9(09), conta 9(11), filler X(14), RECLN 50.
- `L-03`: Preservar layouts de transação mestre e diária com RECLN 350 e campos ID, tipo, categoria, fonte, descrição, valor, comerciante, cartão, timestamp de origem e processamento.
- `L-04`: Preservar layouts de agregação e domínio: chave de saldo por conta+tipo+categoria, saldo S9(09)V99; disclosure group por grupo+tipo+categoria com taxa S9(04)V99; descrições de tipo/categoria em arquivos separados.
- `L-05`: Relatório de transações deve respeitar layout de 133 bytes: cabeçalho com DALYREPT/Daily Transaction Report/date range, detalhe com descrições truncadas e totais Page/Account/Grand com máscaras sinalizadas.
- `J-01`: POSTTRAN executa CBTRN02C contra DALYTRAN.PS, TRANSACT.VSAM.KSDS, CARDXREF, DALYREJS novo, ACCTDATA e TCATBALF; o programa abre TRANSACT como OUTPUT e ACCT/TCATBALF como I-O.
- `J-02`: TRANBKP primeiro descarrega TRANSACT.VSAM.KSDS para TRANSACT.BKUP(+1) via REPROC, depois apaga e redefine o cluster TRANSACT.VSAM.KSDS com chave offset 0 tamanho 16 e RECORDSIZE 350.
- `J-03`: INTCALC executa CBACT04C com PARM=2022071800, lê TCATBALF, CARDXREF/alternate path, ACCTDATA e DISCGRP, e grava SYSTRAN(+1) LRECL 350.
- `J-04`: COMBTRAN ordena a concatenação de TRANSACT.BKUP(0) e SYSTRAN(0) por TRAN-ID crescente e carrega o resultado em TRANSACT.VSAM.KSDS via REPRO.
- `J-05`: TRANREPT descarrega TRANSACT.VSAM.KSDS, filtra/sorta por TRAN-CARD-NUM com TRAN-PROC-DT entre datas hard-coded e depois executa CBTRN03C com DATEPARM e arquivos de descrição.
- `O-01`: Ordem candidata de ciclo em lote, se adotada, deve ser explicitamente humana: POSTTRAN/TRANBKP/INTCALC/COMBTRAN/TRANREPT são jobs separados e o corpus permitido não contém um scheduler que imponha sequência total.
- `E-01`: Falhas de abertura/leitura/gravação/fechamento tratadas nos programas seguem padrão fatal: exibir mensagem, mover FILE STATUS para IO-STATUS, exibir status normalizado e chamar CEE3ABD com ABCODE 999.
- `E-02`: Em CBTRN02C, erro ao fechar DALYREJS exibe mensagem de DAILY REJECTS FILE, mas move XREFFILE-STATUS para IO-STATUS, não DALYREJS-STATUS.
- `E-03`: Lookups inválidos no relatório (cartão, tipo, categoria) são fatais por INVALID KEY com IO-STATUS 23 e CEE3ABD; não produzem linha omitida nem marcador de desconhecido.
- `E-04`: CBACT04C trata falta de conta/XREF como erro fatal após READ, mas falta de disclosure group status 23 tenta DEFAULT; falha no DEFAULT é fatal.
- `T-01`: CBTRN02C em término normal fecha DALYTRAN, TRANSACT, XREF, DALYREJS, ACCTFILE e TCATBALF, exibe contadores e define RETURN-CODE 4 apenas se WS-REJECT-COUNT > 0.
- `T-02`: CBACT04C abre TCATBALF, XREF, DISCGRP, ACCTFILE e TRANSACT nessa ordem e fecha na mesma família de recursos antes de GOBACK; porém a atualização da última conta no EOF é lacuna/bloqueante textual.
- `T-03`: CBTRN03C abre arquivos, lê DATEPARM antes do loop e, no EOF do TRANFILE, escreve page/grand totals; há risco textual de adicionar TRAN-AMT do registro anterior no EOF e de não escrever account total final.

## Decisões humanas necessárias antes de congelar
- Congelar ou não sequência operacional POSTTRAN -> TRANBKP -> INTCALC -> COMBTRAN -> TRANREPT; o allowlist não traz scheduler único.
- CBACT04C: preservar literalmente a aparente não atualização da última conta no EOF ou tratar como defeito a ser documentado/testado.
- CBTRN03C: preservar literalmente comportamento de EOF/totais ou corrigir/adjudicar antes de oráculo de relatório.
- CBTRN02C: erro no close de DALYREJS move XREFFILE-STATUS; decidir se isso é obrigação de compatibilidade.
- Definir se datas hard-coded no SORT de TRANREPT ou DATEPARM do programa têm precedência na referência de avaliação.

## Bloqueantes reais para congelamento
- independent/human review before freeze
- decidir ordem oficial do ciclo entre jobs JCL ou manter obrigações separadas
- adjudicar CBACT04C EOF/última conta sem inventar intenção
- adjudicar CBTRN03C NEXT SENTENCE/EOF/totais antes de usar como oráculo
- decidir tratamento de bugs textuais observados como compatibilidade obrigatória, documentação de limitação ou defeito excluído
- testes dinâmicos e exemplos numéricos permanecem fora desta revisão

## Recibo de checagem programática de âncoras
- Manifesto: `aws-carddemo-preparation/evidence/research-package.json`; commit `59cc6c2fd7ebd7ef7925cad552a01a4b8b6e4d5e`.
- Hashes e contagem de linhas dos 19 arquivos allowlisted: `True`.
- Âncoras de registros conferidas por recomputação de `sha256` de arquivo e de excerto: `True`.
- Registros conferidos: 34; âncoras conferidas: 54.
- Detalhes completos do recibo estão em `anchor_check.details` no JSON revisado.
- Os `excerpt_sha256` dos 16 registros do rascunho foram recalculados; valores anteriores ficam preservados como `original_draft_excerpt_sha256` nas âncoras afetadas.

## Nota metodológica
A referência permanece candidata e contaminada pelo contexto do rascunho inicial; deve ficar em quarentena de avaliação e nunca ser enviada como prompt de extração.
