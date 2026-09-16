# Revisão independente v4 — referência MBT

**Veredito: PASS** para **seleção de caminhos abstratos** da referência MBT v4.

Não é PASS de campanha, não é execução COBOL, não autoriza fixtures/casos oficiais e não prova equivalência semântica completa com COBOL. O escopo foi deliberadamente limitado à correção v3→v4 dos bloqueios V3-BLOCK-001/002/003, CLI relativo, testemunhos das 25 obrigações e busca de regressões materiais novas.

## Escopo e isolamento

Entradas usadas: `reference-authoring-input-v1/`, `reference-authoring-draft-v2/obligations.json`, `reference-executable-v3/`, `reference-independent-review-v3/`, `reference-executable-v4/`.

Excluído: COBOL/campanha/casos oficiais, APIs/contratos/SDD/fixtures/runs/quarentena e varredura ampla de P3.

Nota de exposição: durante `search_files`, local runtime expôs automaticamente `Documents/Códigos/workspace/WORKSPACE-NOTES.md` como contexto de diretório. Registrei a ocorrência; não usei esse arquivo como fonte semântica da revisão.

## Testes/probes executados

| Probe | Resultado |
|---|---|
| Unit tests v4 | exit 0; 16 testes OK |
| CLI absoluto v4 | exit 0; `errors=[]`; 3 capabilities, 25 obligations, 25 states, 40 transitions; 98 anchors/8 files |
| CLI relativo v4 | exit 0; `errors=[]`; 98 anchors/8 files |
| Probes semânticos direcionados | todos compatíveis com os bloqueios revisados |
| Mutantes de evento whitelisted em capacidade errada | rejeitados por escopo de capacidade |

## Bloqueios v3

### V3-BLOCK-001 — INTCALC taxa zero

**Resolvido.** `disc_rate_path` agora inclui `zero`; `step(CBACT04C_INTCALC, I_GROUP, {disc_rate_path: zero})` seleciona `INTCALC-T009Z`, emite apenas `interest_rate_zero_no_interest_write` e retorna a `I_OPENED`. Não emite `interest_compute_attempt` nem `interest_write_attempt`.

A fonte revisada apoia a distinção: `CBACT04C.cbl:213-217` executa cálculo/escrita apenas sob `IF DIS-INT-RATE NOT = 0`. A v4 separa adequadamente origem da taxa (`specific/default/missing`) de valor zero (`zero`), que era o ponto de risco.

### V3-BLOCK-002 — INTCALC-OBL-008 EOF

**Resolvido.** `INTCALC-OBL-008` referencia `INTCALC-T006`. Probe EOF (`tcatbal_read_status=10`) segue `INTCALC-T006`, emite `tcatbal_read_attempt`, `intcalc_eof_no_final_account_update`, `close_attempt`, e não emite `account_update_attempt`.

A fonte revisada (`CBACT04C.cbl:188-222`, `325-370`) sustenta a interpretação estática usada: status 10 move EOF=Y e o loop normal termina antes do `ELSE` externo que chamaria `1050-UPDATE-ACCOUNT`.

### V3-BLOCK-003 — eventos whitelisted em caminho errado

**Resolvido com controle limitado.** A v4 adiciona escopo de evento por capacidade. Mutantes testados foram rejeitados:

- `interest_write_attempt` em `POSTTRAN-T003` → erro de escopo;
- `report_detail_attempt` em `INTCALC-T003` → erro de escopo;
- `tcatbal_update_attempt` em `TRANREPT-T003` → erro de escopo.

Limite: isto é controle de tipagem/escopo + revisão humana/modelo. Não é verificador universal de semântica COBOL nem garante completude de todos os eventos.

### CLI relativo

**Resolvido.** `cd reference-executable-v4 && python3 executable_reference.py . ...` retorna exit 0, `errors=[]`, e valida 98 anchors/8 files, igualando o comportamento relevante do root absoluto.

## Testemunhos das 25 obrigações

Não encontrei contraexemplo mecânico nos testemunhos: para as 25 obrigações, cada witness declarado existe na travessia limitada e contém ao menos uma transitionRef da obrigação correspondente. Portanto, não parecem ser apenas refs coladas sem caminho executável.

Limite importante: o arquivo de testemunhos comprova alcance/ref-inclusão sob orçamento, não semântica completa por si só. A confiança comportamental vem da combinação de testemunhos, probes dirigidos e conferência das fontes ancoradas. Há reutilização/duplicação de alguns caminhos entre obrigações próximas; isso é fraco como evidência independente granular, mas não materialmente bloqueante para seleção de caminhos abstratos.

Resumo de travessia v4: `POSTTRAN` completed=11/frontier=8/unknown=3/omitted=8; `INTCALC` completed=12/frontier=1/unknown=0/omitted=4; `TRANREPT` completed=16/frontier=0/unknown=3/omitted=4. As omissões/frontier permanecem explícitas pelo orçamento.

## Busca de contraexemplos em modelo bruto e fontes

- INTCALC taxa zero: nenhum contraexemplo encontrado; fonte e modelo bruto v4 concordam na ausência de transação quando taxa é zero.
- INTCALC EOF: nenhum contraexemplo material encontrado; modelo reflete o achado estático de não atualizar última conta no EOF normal.
- POSTTRAN invalid-key em rewrite ACCOUNT: nenhum contraexemplo; fonte move razão 109 sem abend local e prossegue para tentativa de TRANFILE.
- TRANREPT fora de intervalo/EOF desconhecido: nenhum bloqueio novo; v4 preserva skip sem detalhe/acréscimo e caminho `unknown` para EOF receiver.

## Veredito final

**PASS** no escopo delimitado: a v4 corrige os três bloqueios materiais v3 e o bug de CLI relativo, sem regressão material nova encontrada para seleção de caminhos abstratos.

Permanece **não aprovado** para prontidão de campanha/oficialização de oráculo: não houve execução COBOL, fixtures oficiais, casos oficiais, contratos/APIs ou validação de equivalência completa.
