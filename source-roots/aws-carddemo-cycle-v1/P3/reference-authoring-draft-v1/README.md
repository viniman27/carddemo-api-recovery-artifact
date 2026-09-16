# Rascunho independente de referência de capacidade/MBT — AWS CardDemo P3

**Status:** `draft_needs_independent_review`

Este diretório contém um rascunho source-anchored para `CBTRN02C/POSTTRAN`, `CBACT04C/INTCALC` e `CBTRN03C/TRANREPT`, produzido somente a partir do pacote restrito `reference-authoring-input-v1`.

## Arquivos

- `obligations.json` — obrigações revisáveis com fonte, hash, linhas, pré-condição, guarda/transição, observável, expectativa decidível e limites.
- `model.json` — modelo finito por trilha, com estados, transições, guardas de seleção de caminho, limites de loop e critérios de determinação.
- `exposure-manifest.json` — exposição efetiva registrada, incluindo arquivos lidos, hashes e uso declarado.

## Achados principais para revisão

- POSTTRAN: valida cartão, conta, limite e expiração; expiração pode sobrescrever overlimit; rejeitos geram trailer e RC 4; postagem aceita atualiza TCATBAL, ACCOUNT e depois TRANFILE, sem alegação de atomicidade.
- INTCALC: depende de TCATBAL contíguo por conta; usa taxa específica ou DEFAULT; taxa zero não gera juros; a atualização da última conta no EOF parece inalcançável pela estrutura fonte.
- TRANREPT: JCL descarrega/ordena/filtra antes do programa; o programa também filtra por DATEPARM; lookups ausentes abendem; no EOF, a fonte soma o TRAN-AMT corrente antes dos totais finais, podendo duplicar o último valor em memória.

## Limites deliberados

Não foram consultados casos oficiais, fixtures, contratos avaliados, outputs, runs, API, suporte, documentos SDD, preflight ou quarentena. Não foram inventados escala/arredondamento/calendário/atomicidade/durabilidade/estado após falha. Lacunas permanecem marcadas para revisão independente.
