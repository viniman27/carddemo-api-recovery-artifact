# Continuidade — testes ampliados e referência inicial

## Exercício das demonstrações

Executados 12 casos adicionais em demo-verification/expanded: 11 com expectativa explícita passaram e um de overflow foi apenas observado, sem classificá-lo como acerto. Frete cobriu zero, zona B, zona desconhecida e valor máximo representável; desconto cobriu zero, tier S, desconhecido e compra máxima; temperatura incluiu negativos e overflow. Compilação -free, fontes candidatas preservadas.

Overflow: entrada -999.99 produziu -767.98 no GnuCOBOL local e término 0. Não converter esse resultado numa regra HTTP universal ou numa aprovação do contrato. O exemplo ainda tem uma limitação deliberadamente explícita; resultado local não elimina a lacuna de portabilidade. Evidência: demo-verification/expanded/cases.json e results.json. Os 12 casos não são células AWS nem provam cobertura exaustiva.

## Referência de avaliação

Criado ../evaluation-quarantine/obligations-draft.json com 16 registros únicos, cada qual com arquivo/hash/intervalo/hash do trecho. A leitura focou os fluxos centrais dos três fontes. Checagem mecânica dos intervalos passou. Rascunho parcial, sem congelamento ou aprovação; falta complementar layouts COPY, JCL, I/O, término e revisão independente/humana. Foi elaborado pelo coordenador já exposto ao preflight: não é referência cega independente. Fora das entradas E1/E2/E3.

## Isolamento

Inspeção do CLI confirmou que `none` é um toolset desconhecido; a chamada anterior continua sendo apenas prova de acesso. Não qualificar esse comando como isolamento pronto. Nada foi alterado no local runtime. Lançador e parâmetros de experimento permanecem pendentes.

## Retomada

P1 permanece aberto: concluir referência e revisão das demos, qualificar captura integral de requisição e isolamento, definir parâmetros suportados, aprovar repetições e pacote final antes de extrações. Estado histórico em ESTADO.md é complementado por este checkpoint; nenhuma autorização posterior dos gates SDD foi criada.
