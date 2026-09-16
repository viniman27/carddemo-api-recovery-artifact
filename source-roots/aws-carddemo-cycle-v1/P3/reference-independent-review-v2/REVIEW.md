# Revisão independente v2 — referência AWS CardDemo P3

**Veredito: FAIL para prontidão MBT.**  
As correções semânticas principais de `FAIL-01..05` estão sustentadas contra as fontes, com as condicionais indicadas abaixo. `FAIL-06` não está fechado: a v2 deixou de ser prosa solta e virou JSON estruturado, mas ainda não é um modelo executável/decidível o suficiente para seleção determinística de caminhos MBT.

## Escopo e exposição efetiva

- Entradas usadas: `reference-authoring-input-v1/`, `reference-authoring-draft-v1/`, `reference-independent-review-v1/`, `reference-authoring-draft-v2/`.
- Não executei COBOL, não criei casos oficiais, não alterei o rascunho.
- Verificação mecânica executada:
  - `python3 -m unittest discover -s reference-authoring-draft-v2/tests -v` → 3 testes OK.
  - `python3 reference-authoring-draft-v2/validate_reference_model.py reference-authoring-draft-v2` → `PASS` mecânico com 3 capacidades, 32 estados, 62 transições, 25 obrigações, 6 achados marcados resolvidos.
- Exceção de exposição registrada: uma descoberta inicial ampla de arquivos em `P3` expôs nomes de artefatos irmãos e o contexto automático `WORKSPACE-NOTES.md`; não usei conteúdo desses artefatos nos achados.

## Fechamento dos seis achados v1

| ID | Veredito independente | Base |
|---|---|---|
| FAIL-01 | Fechado como obrigação fonte, não como caminho MBT determinístico | `CBTRN03C.cbl:170-178`, `197-203`, `248-265`: EOF só alcança totais depois do teste textual de data; receiver em EOF continua autoridade desconhecida. |
| FAIL-02 | Fechado contra fonte | `CBTRN03C.cbl:181-184`, `306-316`: `1120-WRITE-ACCOUNT-TOTALS` ocorre em mudança de cartão; EOF não chama account total final. |
| FAIL-03 | Fechado contra fonte | `CBTRN03C.cbl:170-178` com `NEXT SENTENCE` salta a sentença do loop; detalhe/acúmulo em `179-203`/`287-289` não ocorre para fora do intervalo. |
| FAIL-04 | Fechado contra fonte, sem alegar durabilidade | `CBTRN02C.cbl:424-442`, `562-578`: `WRITE TRANFILE` falho abende depois das tentativas TCATBAL/ACCOUNT. |
| FAIL-05 | Fechado contra fonte | `CBTRN02C.cbl:545-559`, `440-442`: `REWRITE ACCOUNT INVALID KEY` move razão 109, não abende localmente, e o fluxo continua para `WRITE TRANFILE`. |
| FAIL-06 | **Não fechado** | O modelo é finito e referenciado, mas efeitos/observáveis continuam strings; guardas são só parcialmente tipadas; loops e valuações não são executáveis. |

## Traços estáticos sustentados

1. **TRANREPT fora de intervalo:** após `READ`, se `TRAN-PROC-TS(1:10)` fica fora de `WS-START-DATE..WS-END-DATE`, `NEXT SENTENCE` salta a sentença até depois do ponto em `END-PERFORM`; não há lookup, detalhe nem acúmulo.
2. **TRANREPT EOF:** EOF é marcado em `1000-TRANFILE-GET-NEXT`, mas a data textual ainda é testada antes do ramo `IF END-OF-FILE`; se passa, escreve page/grand totals, não account total; se falha, pula totais.
3. **POSTTRAN falha de write:** o caminho aceito executa TCATBAL, ACCOUNT e depois `WRITE TRANFILE`; falha do write chama abend depois das tentativas anteriores.
4. **INTCALC EOF:** `READ` com status 10 marca `END-OF-FILE=Y` dentro de iteração que entrou pelo ramo `END=N`; o `ELSE` externo com `1050-UPDATE-ACCOUNT` não é alcançado no EOF normal.

## Causas-raiz consolidadas

### 1. Semântica do modelo ainda não é executável

`effects` e `observables` são strings livres. Não há linguagem de atualização para contadores, acumuladores, cartão/conta corrente, `first` flags, receiver em EOF, writes ou razões de rejeição. Um seletor MBT não consegue calcular, a partir do artefato, o próximo estado concreto, os dados necessários ou o oráculo esperado.

### 2. Guardas AST são checadas parcialmente

O validador confere operadores e nomes de variáveis, mas não prova satisfatibilidade, exclusão entre transições do mesmo estado, tipagem/domínio dos literais em `eq/ne/gte/lte`, nem semântica operacional de `unknown`. A lista de operadores também contém operadores não usados ou sem interpretação completa (`exists`, `changed`, `first_record`, `gte`, `lte`).

### 3. Finitude do grafo não prova MBT finito

O grafo tem 32 estados e 62 transições, mas os laços não têm política executável de travessia. Parâmetros como `maxDailyRecords`, `maxTcatbalRecords`, `maxTranRecords` e `maxCards` aparecem como rótulos; não há atualização/decremento nem critério formal de parada/cobertura.

### 4. O PASS mecânico não rejeita mutantes semanticamente inválidos

Mutantes que contradizem a fonte ainda passam o validador:

- `POSTTRAN-T020`: inverter “razão 109 e continua para WRITE” para “abend antes do WRITE”.
- `TRANREPT-T009`: inverter “fora de intervalo pula detalhe/acúmulo” para “gera detalhe e soma”.
- `INTCALC-T006`: inverter “sem update final no EOF” para “update final no EOF”.

Resultado: o validador ainda retorna `PASS` com zero erros. Isso demonstra que os 3 testes positivos atuais validam forma, existência de refs e reachability, não correção semântica.

## Condição de fechamento

Uma próxima versão só deve receber PASS se resolver `FAIL-06` materialmente: domínios e valuações tipadas, interpretação operacional de guardas, checagem de satisfatibilidade/disjunção, efeitos/observáveis estruturados e verificáveis, política de loops/traversal finito, testes negativos/mutantes que rejeitem contradições de fonte, e tratamento condicional do EOF desconhecido sem inventar retenção do receiver.

Não autoriza campanha, fixtures oficiais ou aprovação humana.
