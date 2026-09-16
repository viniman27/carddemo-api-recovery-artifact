# Revisão independente v3 — referência MBT executável AWS CardDemo P3

**Veredito delimitado: PARTIAL.**  
A v3 é executável e determinística para os caminhos abstratos que ela representa, mas **não recebe PASS como referência completa das 25 obrigações v2 para seleção pré-campanha**. Há perda silenciosa de pelo menos um caminho obrigatório (`INTCALC` taxa zero) e uma obrigação presente no catálogo (`INTCALC-OBL-008`) não está ligada a nenhuma transição. Portanto, a v3 só pode ser tratada como avanço parcial/insumo de revisão, não como autorização de campanha, fixtures oficiais ou equivalência COBOL.

## Escopo e exposição efetiva

Entradas efetivamente usadas:

- `reference-authoring-input-v1/README.md`, `input-manifest.json` e trechos do corpus allowlisted necessários para conferir anchors de fonte.
- `reference-authoring-draft-v2/obligations.json`.
- `reference-independent-review-v2/REVIEW.md`.
- `reference-executable-v3/README.md`, `model.json`, `executable_reference.py`, `tests/test_engine_contract.py`.

Não usei: COBOL executado, caso oficial, campanha, contratos E1/E2/SDD, APIs, fixtures, runs, oráculos/quarentena ou outros diretórios P3 fora das entradas permitidas. A busca de arquivos foi direcionada aos quatro diretórios permitidos. O runtime local runtime expôs automaticamente o `WORKSPACE-NOTES.md` do repositório como contexto de subdiretório; isso fica registrado e não é alegado isolamento absoluto.

## Comandos executados e resultados

### 1. Testes stdlib da v3

```sh
python3 -m unittest discover -s '<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/reference-executable-v3/tests' -v
```

Resultado observado: exit `0`; `Ran 11 tests in 0.035s`; `OK`.

### 2. CLI com root absoluto

```sh
python3 '<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/reference-executable-v3/executable_reference.py' '<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/reference-executable-v3' --traverse CBTRN02C_POSTTRAN --traverse CBACT04C_INTCALC --traverse CBTRN03C_TRANREPT --max-depth 8 --max-paths 80
```

Resultado observado: exit `0`; `errors=[]`; contagens `capabilities=3`, `obligations=25`, `states=25`, `transitions=39`; `sourcePins.checkedAnchors=94`, `checkedFiles=8`, `sourcePins.errors=[]`.

### 3. CLI com `root='.'` — problema conhecido, não semântico

```sh
cd '<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/reference-executable-v3' && python3 executable_reference.py . --traverse CBTRN02C_POSTTRAN --max-depth 2 --max-paths 5
```

Resultado observado: exit `1`; `model.json` foi carregado, mas `validate_source_pins` resolveu o corpus a partir de `root.parent` e retornou múltiplos `missing source app/...`. Com root absoluto, a validação passa. Isto confirma o problema CLI relativo já reproduzido pelo coordenador e **não deve ser confundido com falha semântica do modelo**.

### 4. Probes/counterexamples no interpretador

Com `python3 -c` stdlib importando `executable_reference.py` e `model.json`:

- IDs das 25 obrigações v3 coincidem com v2: `true`.
- Obrigações sem transição referenciada: `['INTCALC-OBL-008']`.
- Enumeração exaustiva dos domínios finitos não encontrou múltiplas transições habilitadas para a mesma valuação (`nondeterminism_examples=[]`).
- Travessias repetidas são determinísticas; resumos com `max-depth=8`, `max-paths=80`:
  - `CBTRN02C_POSTTRAN`: `completed=11`, `frontier=8`, `unknown=3`, `omitted=8`.
  - `CBACT04C_INTCALC`: `completed=8`, `frontier=1`, `unknown=0`, `omitted=1`.
  - `CBTRN03C_TRANREPT`: `completed=16`, `frontier=0`, `unknown=3`, `omitted=4`.
- Mutante com evento whitelisted mas semanticamente indevido (`interest_write_attempt` inserido em `POSTTRAN-T003`) retornou `validate_model(...).errors=[]`.

## O que passa

1. **Execução mecânica:** os 11 testes rodam e o CLI absoluto valida pins e travessias.
2. **Determinismo local:** para os domínios finitos declarados, não encontrei sobreposição de guardas no mesmo estado. A ordem de travessia por `transitionId` é estável.
3. **Unknown EOF:** `UnknownEOF` não satisfaz igualdade comum e gera caminho `unknown` explícito em `POSTTRAN`/`TRANREPT`.
4. **Orçamento visível:** `frontier`, `unknown`, `omittedCount` e `budget` aparecem nos resultados; a v3 não finge cobertura completa quando o orçamento corta caminhos.
5. **Três correções críticas v2→v3 são representadas como caminhos executáveis:**
   - `POSTTRAN-T020`: `ACCOUNT REWRITE INVALID KEY` continua para `P_TRANFILE_WRITE` com `account_rewrite_invalid_key_continues` e `tranfile_write_attempt_pending`.
   - `TRANREPT-T009`: fora do intervalo emite `tranrept_skip_detail_out_of_range` sem `report_detail_attempt`/`account_accrual_attempt`.
   - `INTCALC-T006`: EOF em `I_OPENED` emite `intcalc_eof_no_final_account_update` e fecha sem `account_update_attempt`.

## Bloqueios reais

### V3-BLOCK-001 — `INTCALC` taxa zero foi apagada do modelo

**Severidade: P0.**  
`INTCALC-OBL-005` diz que taxa zero não gera transação: “Taxa zero não gera transação; taxa diferente de zero gera valor pela fórmula fonte.” A fonte sustenta isso em `CBACT04C.cbl:213-217`:

```text
PERFORM 1200-GET-INTEREST-RATE
IF DIS-INT-RATE NOT = 0
  PERFORM 1300-COMPUTE-INTEREST
  PERFORM 1400-COMPUTE-FEES
END-IF
```

Na v3, `disc_rate_path` tem domínio `specific/default/missing`, sem valor para taxa zero. A transição `INTCALC-T009` tem guarda `true` e emite `interest_write_attempt` depois de `I_RATE`. Resultado do probe: `intcalc_rate_zero_representable=false`.

Impacto: um seletor MBT não consegue escolher o caminho “taxa encontrada, mas valor zero, sem transação”. Isso é perda silenciosa de obrigação, não falta de equivalência completa COBOL.

### V3-BLOCK-002 — `INTCALC-OBL-008` existe, mas não é rastreável por transição

**Severidade: P0.**  
A checagem programática encontrou:

```json
"obligations_without_transition_refs": ["INTCALC-OBL-008"]
```

O evento correto de EOF sem update final aparece em `INTCALC-T006`, mas essa transição referencia `INTCALC-OBL-007`. Assim, a v3 declara 25 obrigações, mas uma delas não é selecionável/rastreável como caminho abstrato.

Impacto: bloqueia PASS para seleção determinística das 25 obrigações. Mesmo que o efeito esteja modelado, a obrigação v2→v3 não está fechada por rastreabilidade.

### V3-BLOCK-003 — o validador ainda permite eventos inventados se o nome estiver na whitelist

**Severidade: P1.**  
A v3 rejeita eventos desconhecidos, mas não prova que um evento whitelisted pertence ao caminho fonte. Mutante executado no interpretador:

- alteração: adicionar `{"op":"emit","event":"interest_write_attempt"}` em `POSTTRAN-T003`;
- resultado: `validate_model(...).errors=[]`.

Impacto: os 11 testes e o validador não bastam para detectar invenção de eventos fora dos três mutantes hardcoded. O modelo bruto precisa de inspeção independente; não pode ser aprovado apenas pelo pacote de testes.

## Conferência contra fonte dos caminhos de risco

### POSTTRAN — falha parcial e ordem de efeitos

Fonte conferida:

- `CBTRN02C.cbl:424-442`: `2000-POST-TRANSACTION` move campos e chama `2700-UPDATE-TCATBAL`, `2800-UPDATE-ACCOUNT-REC`, depois `2900-WRITE-TRANSACTION-FILE`.
- `CBTRN02C.cbl:545-559`: `REWRITE ACCOUNT INVALID KEY` move razão 109, sem abend local.
- `CBTRN02C.cbl:562-578`: falha no `WRITE TRANFILE` exibe erro e chama abend.

Avaliação: v3 preserva a ordem abstrata e não promete durabilidade/rollback. `POSTTRAN-T020` e `POSTTRAN-T022` são aceitáveis como eventos de tentativa/controle.

### INTCALC — EOF, grupos e taxa zero

Fonte conferida:

- `CBACT04C.cbl:188-222`: o loop lê `TCATBAL`; update de conta em quebra ocorre quando há novo grupo e não é a primeira vez.
- `CBACT04C.cbl:325-370`: status `10` marca `END-OF-FILE=Y`; o update final no `ELSE` externo não é alcançado no EOF normal da iteração que entrou com `END=N`.
- `CBACT04C.cbl:213-217`: `DIS-INT-RATE NOT = 0` é a guarda para computar/escrever juros.

Avaliação: v3 preserva o evento de EOF sem update final, mas associa a transição à obrigação errada e apaga o caso taxa zero.

### TRANREPT — EOF condicional, fora do intervalo e lookups

Fonte conferida:

- `CBTRN03C.cbl:170-206`: após `READ`, a data textual é testada antes do ramo `IF END-OF-FILE`; fora do intervalo executa `NEXT SENTENCE` e pula detalhe/acúmulo.
- `CBTRN03C.cbl:248-272`: status `10` marca EOF; receiver em EOF não foi assumido como estável.
- `CBTRN03C.cbl:484-512`: lookups por XREF/tipo/categoria podem abendar em invalid key.

Avaliação: v3 está alinhada no caminho fora do intervalo e explicita `unknown_eof_receiver_path`; não inventa retenção do receiver em EOF.

## Rastreabilidade das 25 obrigações v2→v3

- Catálogo: 25 IDs v3 coincidem com `reference-authoring-draft-v2/obligations.json`.
- Bloqueio: `INTCALC-OBL-008` não aparece em `obligationRefs` de nenhuma transição.
- Consequência: a contagem `obligations=25` do validador é insuficiente; ela não garante que todas as obrigações são selecionáveis.

## Redução do modelo e omissões

A v3 é uma abstração finita com orçamento explícito, e isso é aceitável como direção. O problema não é reduzir COBOL para um grafo finito; o problema é reduzir sem preservar obrigações decidíveis. A ausência do ramo taxa zero e a falta de referência para `INTCALC-OBL-008` são perdas materiais. Já `omittedCount`/`frontier` são omissões orçamentárias visíveis e não são, por si só, falha semântica.

## Decisão

**PARTIAL, não PASS.**

Permitido como evidência parcial:

- validar mecanicamente pins e execução com root absoluto;
- explorar caminhos já representados de forma determinística;
- usar os probes acima como regressões manuais de revisão.

Não permitido como PASS pré-campanha:

- selecionar caminhos para as 25 obrigações completas;
- tratar os 11 testes como prova semântica;
- usar a v3 como referência independente final sem corrigir `INTCALC` taxa zero e rastreabilidade de `INTCALC-OBL-008`;
- confundir o bug `root='.'` com falha semântica.

## Condições mínimas para PASS posterior

1. Representar explicitamente o ramo `INTCALC` de taxa zero/não geração de transação.
2. Ligar `INTCALC-OBL-008` a uma transição selecionável adequada, ou justificar formalmente outra estrutura de rastreio.
3. Fortalecer validação/revisão para impedir eventos whitelisted mas sem fonte no caminho.
4. Manter invocação com root absoluto ou corrigir a resolução de source pins para `root='.'`, sem reclassificar esse bug como semântico.
