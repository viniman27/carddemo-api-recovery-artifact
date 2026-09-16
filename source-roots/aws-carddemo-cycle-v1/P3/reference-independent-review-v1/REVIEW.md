# Revisão independente do rascunho de referência/MBT AWS CardDemo P3

**Classificação:** FAIL

O rascunho não deve ser aprovado para fixture/campanha. As âncoras e hashes declarados foram conferidos e o conjunto de obrigações cobre vários comportamentos reais, mas há inconsistências e omissões materiais que impedem tratá-lo como modelo de capacidade verificável para MBT.

## Escopo e limites da revisão

Entradas efetivamente usadas:

- `reference-authoring-input-v1/README.md` — sha256 `c0d2bb0e890a988ce643c0aa960933ab454e02e5db1fdd4af932e512c54b7ced`
- `reference-authoring-input-v1/input-manifest.json` — sha256 `93d178bcf5a2e50e43c6af51985f68ae0edfe6162a196883d146cb27c56a5510`
- arquivos enumerados em `reference-authoring-input-v1/corpus/`, com hashes conferidos contra o manifesto
- `reference-authoring-draft-v1/README.md` — sha256 `8681e53fd09e0003e5f4691b1723535511187a2aa03691a95e83e6f023f8a2e8`
- `reference-authoring-draft-v1/obligations.json` — sha256 `eb1fdce18f639ef87097f871434c42925e42167c6fce18acfed35757acdf3637`
- `reference-authoring-draft-v1/model.json` — sha256 `0ca0277175d0a9746df84c7b77d9090a870315d95b951334d29dcb2c7b35920c`
- `reference-authoring-draft-v1/exposure-manifest.json` — sha256 `05eeb4b98c501115ff87a3bbcba2458c71672799dce00df357b1290b150233fd`

Não foram lidos contratos E1/E2, SDD, APIs, fixtures, suporte, expected, preflight, quarentena, runs, resultados oficiais ou diretórios fora dos dois pacotes permitidos. Não executei COBOL nem usei memória de resultados como autoridade de referência. A revisão não certifica independência cognitiva absoluta; registra apenas o contexto efetivamente usado.

## Verificações mecânicas

- `input-manifest.json`: 19 arquivos enumerados; todos os hashes e tamanhos conferem com os bytes em `corpus/`.
- `obligations.json`: 23 obrigações revisadas — 8 POSTTRAN, 8 INTCALC, 7 TRANREPT.
- Todas as âncoras de `source_anchors` apontam para arquivo existente, hash correto e intervalo de linhas válido.
- `model.json`: 3 capacidades revisadas.

Essas verificações não bastam para aprovação; os achados abaixo são semânticos e de modelagem.

## Achados bloqueadores

### FAIL-01 — `TRANREPT` trata EOF como se sempre escrevesse totais, mas a fonte testa data antes de verificar EOF

**Rascunho afetado:**

- `model.json`: transição `tran_10->write totals with current TRAN-AMT branch`.
- `TRANREPT-OBL-003`: “READ status 00 processa; status 10 marca EOF”.
- `TRANREPT-OBL-007`: “no EOF normal há risco sustentado de duplicar o último TRAN-AMT em memória”.

**Evidência fonte:**

- `app/cbl/CBTRN03C.cbl` linhas 170-178: depois de `PERFORM 1000-TRANFILE-GET-NEXT`, o programa avalia `TRAN-PROC-TS (1:10) >= WS-START-DATE AND <= WS-END-DATE`; se falhar, executa `NEXT SENTENCE`.
- `app/cbl/CBTRN03C.cbl` linhas 248-265: status `10` move `Y` para `END-OF-FILE`.
- `app/cbl/CBTRN03C.cbl` linhas 179-203: o ramo que escreve totais no EOF só é alcançado depois do teste de data anterior.

**Contraexemplo sustentado:** se a leitura encontra EOF e o `TRAN-PROC-TS` retido do último registro está fora do intervalo textual, ou se não há registro anterior com valor decidível, o `NEXT SENTENCE` pode pular o ramo de totais. Portanto, o modelo não pode afirmar de forma incondicional que `tran_10` escreve totais; a duplicação do último `TRAN-AMT` é uma possibilidade condicionada, não uma transição EOF universal.

**Impacto:** expectativa de relatório final e totalização pode ser falsa para entradas fora do intervalo/arquivo vazio. Isso bloqueia campanha porque afeta oráculo de saída e seleção de caminhos.

### FAIL-02 — `TRANREPT` omite a ausência de total final por cartão/conta no EOF

**Rascunho afetado:**

- `TRANREPT-OBL-004` cobre total anterior em mudança de cartão.
- `TRANREPT-OBL-007` cobre page/grand total e risco de duplicação, mas não registra a falta de `Account Total` final.
- `model.json` não possui estado/transição específica para total de último cartão/conta.

**Evidência fonte:**

- `app/cbl/CBTRN03C.cbl` linhas 181-184: `1120-WRITE-ACCOUNT-TOTALS` é chamado apenas quando `WS-CURR-CARD-NUM NOT= TRAN-CARD-NUM` e não é a primeira ocorrência.
- `app/cbl/CBTRN03C.cbl` linhas 197-203: no ramo EOF são executados `1110-WRITE-PAGE-TOTALS` e `1110-WRITE-GRAND-TOTALS`, sem chamada a `1120-WRITE-ACCOUNT-TOTALS`.
- `app/cbl/CBTRN03C.cbl` linhas 306-316: `1120-WRITE-ACCOUNT-TOTALS` é a rotina que materializa `Account Total` e zera `WS-ACCOUNT-TOTAL`.

**Contraexemplo sustentado:** um arquivo com transações em intervalo para um único cartão nunca sofre mudança de cartão; pela fonte, não há chamada final a `1120-WRITE-ACCOUNT-TOTALS`. O rascunho não torna esse comportamento obrigatório nem lacunar.

**Impacto:** o oráculo de relatório fica incompleto: uma implementação que escreve total final de conta ou não escreve poderia passar dependendo de como a campanha interpreta a ausência. Isso impede avaliação justa de `CBTRN03C/TRANREPT`.

### FAIL-03 — `TRANREPT` deixa o caminho fora de intervalo como “sem expectativa rígida”, mas ele é decisivo para controle de fluxo e totais

**Rascunho afetado:**

- `TRANREPT-OBL-002`: “NEXT SENTENCE precisa revisão”.
- `model.json`: `tran_00_out_of_range->no rigid expectation pending NEXT SENTENCE review`.

**Evidência fonte:**

- `app/cbl/CBTRN03C.cbl` linhas 170-178: registros fora do intervalo textual executam `NEXT SENTENCE` antes de lookup/detalhe.
- `app/cbl/CBTRN03C.cbl` linhas 179-196: lookup e detalhe ficam depois desse ponto.
- `app/cbl/CBTRN03C.cbl` linhas 287-289: somas de page/account ocorrem apenas na rotina de detalhe chamada depois dos lookups.

**Contraexemplo sustentado:** uma entrada com um registro `TRAN-PROC-TS` fora do intervalo deve não produzir detalhe nem acumular valor, mas o modelo não congela esse comportamento decidível. O mesmo ponto interfere no EOF do achado FAIL-01.

**Impacto:** o modelo não é MBT-pronto para partição básica “dentro vs fora do intervalo”; isso é uma guarda central de `TRANREPT`, não detalhe opcional.

### FAIL-04 — `POSTTRAN` omite falha de escrita/duplicidade em `TRANFILE` após efeitos anteriores

**Rascunho afetado:**

- `POSTTRAN-OBL-008`: registra a ordem `TCATBAL`, `ACCOUNT`, `TRANFILE` e diz que estado após falha intermediária é indecidível.
- `model.json`: caminho aceito termina em `valid->post_tcatbal->post_account->write_tran->read_daily`, sem caminho de falha de escrita depois de efeitos anteriores.

**Evidência fonte:**

- `app/cbl/CBTRN02C.cbl` linhas 424-442: a transação aceita move campos e executa `2700-UPDATE-TCATBAL`, depois `2800-UPDATE-ACCOUNT-REC`, depois `2900-WRITE-TRANSACTION-FILE`.
- `app/cbl/CBTRN02C.cbl` linhas 562-578: `WRITE FD-TRANFILE-REC`; status diferente de `00` exibe erro e chama `9999-ABEND-PROGRAM`.
- `app/cbl/CBTRN02C.cbl` linhas 370-421: validações cobrem XREF, conta, limite e expiração; não há validação de duplicidade de `DALYTRAN-ID`/`TRAN-ID` antes da escrita.

**Contraexemplo sustentado:** duas transações aceitas com o mesmo `DALYTRAN-ID` podem levar a falha de chave na segunda escrita de `TRANFILE` depois de `TCATBAL` e `ACCOUNT` já terem sido atualizados na segunda transação. A fonte autoriza esse caminho como possibilidade de status não-`00`; o rascunho não o modela como obrigação/caminho observável.

**Impacto:** uma campanha MBT derivada do rascunho tenderia a testar apenas aceitação limpa ou rejeição validatória, omitindo caminho crítico de efeito parcial/abend em `CBTRN02C/POSTTRAN`.

### FAIL-05 — `POSTTRAN` não captura que falha no `REWRITE` de `ACCOUNT` não é tratada como abend nessa rotina

**Rascunho afetado:**

- `POSTTRAN-OBL-008`: expectativa “ACCOUNT e TRANFILE” com nota genérica de estado após falha intermediária.
- `model.json`: não há transição específica de falha no update de conta.

**Evidência fonte:**

- `app/cbl/CBTRN02C.cbl` linhas 545-559: `REWRITE FD-ACCTFILE-REC`; em `INVALID KEY` apenas move razão `109` e descrição, sem checar `ACCTFILE-STATUS`, sem `PERFORM 9910-DISPLAY-IO-STATUS` e sem `PERFORM 9999-ABEND-PROGRAM`.
- `app/cbl/CBTRN02C.cbl` linhas 440-442: após `2800-UPDATE-ACCOUNT-REC`, o fluxo segue para `2900-WRITE-TRANSACTION-FILE`.

**Contraexemplo sustentado:** se `REWRITE` falha por chave inválida ou outro status materializado como `INVALID KEY`, a fonte não aborta nesse ponto e ainda tenta escrever `TRANFILE`. O rascunho transforma isso em limite genérico, sem expectativa decidível ou guarda de revisão.

**Impacto:** comportamento de falha intermediária fica subespecificado em uma capacidade com efeitos persistentes. Isso não exige assumir durabilidade, mas exige modelar a ordem e a ausência de tratamento local.

### FAIL-06 — `model.json` não é um modelo MBT verificável suficiente; é uma lista de transições em prose

**Rascunho afetado:** `model.json` inteiro.

**Evidência do próprio rascunho:**

- `model.json` linhas 32-48, 76-98, 127-145: transições são strings livres, sem identificador, fonte, guarda formal, pré/pós-condição, efeito observável nem obrigação de origem por transição.
- `model.json` linhas 49, 99 e 147: `path_selection` é texto genérico repetido — “status codes, key existence, group/card change, date/rate/limit guards” — mesmo quando a capacidade não possui todos esses guardas.
- `model.json` linhas 50, 100 e 148: `loop_bound` é genérico e não distingue loops condicionados por `NEXT SENTENCE`, quebras de cartão/conta, primeira ocorrência ou EOF com campos retidos.

**Contraexemplo de modelagem:** `CBTRN03C_TRANREPT` precisa separar pelo menos `tran_00_in_range`, `tran_00_out_of_range`, `tran_10_after_in_range`, `tran_10_after_out_of_range/empty`, mudança de cartão e último cartão sem total final. O rascunho mistura esses caminhos ou os deixa como nota pendente.

**Impacto:** mesmo com obrigações parcialmente corretas, `model.json` não permite geração MBT justa e auditável sem interpretação externa. Isso viola a exigência do pacote de entrada de produzir modelo explícito com estados, transições, guardas, laços e fronteiras.

## Achados não bloqueadores / pontos sustentados

- As âncoras de hash/linha do rascunho são mecanicamente válidas.
- `POSTTRAN-OBL-004` e `POSTTRAN-OBL-005` estão sustentadas quanto a XREF, conta, limite e expiração textual: `CBTRN02C.cbl` linhas 380-421.
- A precedência “expiração pode sobrescrever overlimit” está sustentada: `CBTRN02C.cbl` linhas 407-419.
- A ordem geral dos efeitos aceitos em `POSTTRAN` está sustentada: `CBTRN02C.cbl` linhas 440-442.
- `INTCALC-OBL-008` está sustentada como achado estático: em `CBACT04C.cbl` linhas 188-222, o `ELSE` externo que chamaria `1050-UPDATE-ACCOUNT` não é alcançado no EOF normal porque a condição do `PERFORM UNTIL END-OF-FILE = 'Y'` encerra antes da próxima iteração.
- A ausência de fallback além de `DEFAULT` em `INTCALC` está sustentada: `CBACT04C.cbl` linhas 415-459.

Esses pontos não compensam os bloqueios; aprovação por contagem seria indevida.

## Inventário faltante para aprovação

Antes de qualquer fixture/campanha, o rascunho precisa ser revisado para incluir ou marcar explicitamente como fora de escopo, com justificativa source-anchored:

1. Partições `TRANREPT` para registro dentro/fora do intervalo antes de EOF.
2. EOF de `TRANREPT` condicionado ao valor retido de `TRAN-PROC-TS`, incluindo arquivo vazio ou último registro fora do intervalo.
3. Ausência de `Account Total` final em `TRANREPT`.
4. Caminho de falha de `WRITE TRANFILE` em `POSTTRAN` após `TCATBAL` e `ACCOUNT`.
5. Caminho de falha/ausência de abend local em `POSTTRAN` `REWRITE ACCOUNT`.
6. Modelo MBT com transições identificadas, guardas decidíveis, efeitos observáveis e âncoras por transição, sem `path_selection` genérico copiado.

## Condição exata de aprovação

A classificação só pode passar para PASS depois que uma versão nova do rascunho:

- resolver todos os achados FAIL-01 a FAIL-06 com alterações source-anchored;
- preservar os hashes/âncoras ou justificar qualquer mudança de corpus/autoria;
- declarar para cada capacidade quais caminhos são obrigatórios, opcionais ou indecidíveis;
- tornar `model.json` suficiente para geração MBT sem interpretação externa de prose;
- registrar novamente exposição efetiva e revisão, sem consultar fixtures, contratos, outputs oficiais, runs, SDD, APIs, suporte, preflight ou quarentena.

Até lá, a decisão é **FAIL** e não autoriza fixture, suíte oficial, campanha ou congelamento de referência.
