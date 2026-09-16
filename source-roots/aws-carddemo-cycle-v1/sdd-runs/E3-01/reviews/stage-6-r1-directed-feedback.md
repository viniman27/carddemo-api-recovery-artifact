# Feedback dirigido Stage 6 r1 — API Contract CardDemo

## Veredito

Revisar o Stage 6 como especificação documental versionada, não como contrato executável aprovado. O problema principal não é contradição nova contra Stage 5/4; é que o texto atual deixa G-21..G-24 abertos de modo amplo demais para guiar uma revisão de contrato. A próxima versão deve separar escolhas legítimas de representação HTTP das evidências ausentes que continuam bloqueando promessas de runtime.

## Base e escopo

- Original Stage 6 revisado: `specs/api-contract-carddemo/requirements.md`
- SHA original conferido: `753a60a5ee7b1fb6d94f6ab982afe415bc01adca040bb3d89e24ffc60342bba7`
- Mesmo SHA em `prepared/api-contract-carddemo/execution/scope-original.md`
- Instrução humana Stage 6 original: `se nao existem mais ressalvas, pode prosseguir` (`stage6-generation-authorization.json:7-10`)
- Autorização Stage 5: aprova boundary documental e autoriza Stage 6 para posting, interest e reporting, sem Stage 7/implementação (`reviews/stage-5-authorization.json:7-11`)
- Materialização corrigida: o placeholder foi arquivado e `requirements.md` recebeu exatamente o Stage 6 gerado (`STAGE6-RESULT.md:78-80`)

## Constraints que a revisão deve preservar

- Três trilhas obrigatórias, separadas: Stage 6 declara isso em `requirements.md:3-22`; Stage 5 em `requirements.md:5-23`; Stage 4 em `requirements.md:5-24`.
- Stage 5 D-2..D-8 são vinculantes: sem lifecycle comum, sem recursos internos consumer-controlled, sem atomicidade/rollback/retry, sem políticas numéricas/datas inventadas, sem reparo de EOF/finalização, sem paginação de API derivada, sem filler/fee inventado (`Stage5:100-147`).
- Ausente não é zero: missing disclosure, finalização ausente, output desconhecido e zero computado são distintos (`Stage5:185-193`; `Stage4:R-8/R-9/R-10/R-15 em 199-221 e 255-261`).
- Efeitos e repetição são incertos por trilha, não universalmente seguros nem universalmente danosos (`Stage5:114-119`, `286-300`, `343-353`; `Stage4:295-301`).
- Source anchors existentes devem continuar via E/R aprovados; não criar novos fatos COBOL no Stage 6 (`Stage6:96-99`, `421-443`).

## Feedback por lacuna

### G-21 — Request participation

**Texto atual:** `requirements.md:502-505` diz que não se decide se sequência/data vira array, seletor externo, singleton, input vazio ou EOF signal. Operações usam `POST /posting`, `POST /interest`, `POST /reporting` mas dizem que participação permanece bloqueada (`requirements.md:118-136`, `282-285`, `307-310`, `328-331`).

**Escolhas legítimas de interface:**

- Manter as três rotas `POST` é defensável como decisão de representação, não como fato de job/lifecycle (`Stage6:128-136`).
- Escolher um modelo HTTP proposto para participação é permitido se rotulado como `design proposal requiring gate acceptance`, não como COBOL estabelecido.
- Um request pode representar “solicitar processamento contra entrada externa” ou “fornecer conteúdo de sequência” como alternativa de interface; a revisão precisa declarar qual alternativa escolhe e quais promessas nega.

**Evidência ausente / não inventar:**

- Posting: Stage 4 fala em “daily transaction records”, “non-EOF daily record” e processamento por registro, mas não estabelece request HTTP nem cardinalidade de array (`Stage4:101-111`, `143-149`). Stage 5 trata `Daily candidate sequence` como sequência encontrada, com conteúdo/ordem reais não resolvidos (`Stage5:302-312`).
- Interest: Stage 4 identifica category balances, account/xref/disclosure e `PARM-DATE`, mas não decide se o consumidor fornece sequência, parâmetro, ou apenas aciona processamento externo (`Stage4:113-123`, `191-229`). Stage 5 classifica account/xref/disclosure/suffix como internos e o parâmetro como texto externo com validade/lifetime não resolvidos (`Stage5:314-326`).
- Reporting: Stage 4 distingue transações sequenciais, date parameters, SORT upstream e EOF/date failure (`Stage4:125-135`, `231-237`, `271-277`). Stage 5 mantém `ReportingDateBasis` e `UpstreamReportSelectionBasis` separados (`Stage5:173-183`, `327-341`).

**Revisão requerida:**

Adicionar uma matriz por operação:

| Categoria | Posting | Interest | Reporting |
|---|---|---|---|
| `consumer-supplied` | somente campos escolhidos pela proposta de request; não presumir todos | somente campos escolhidos; `PARM-DATE` se escolhido deve ser proposta | start/end apenas se escolhidos; não confundir com SORT |
| `externally supplied` | sequência diária se não vier no request | category sequence, account/xref/disclosure | transaction sequence, upstream SORT/date resources |
| `internal dependency` | account/category/xref | account/xref/disclosure/suffix | xref/type/category lookups, counters/totals |
| `unknown/EOF` | ausência/EOF sem semântica HTTP completa | normal EOF sem final flush | date-input EOF e post-read storage desconhecidos |

**Critério mínimo de fechamento:**

G-21 pode ser fechado documentalmente quando cada operação tiver um request model proposto com granularidade explícita e etiquetas `consumer-supplied`/`externally supplied`/`internal`. Não pode ser fechado por declarar array vazio, singleton por registro, dataset ID, ou EOF signal sem aceitar que isso é uma decisão de interface submetida ao gate.

### G-22 — Schemas e validação

**Texto atual:** D-11 escolhe strings e decimal text, mas não escala, rounding, units, overflow, date format, padding/trimming/coercion (`Stage6:146-152`). C-9 lista required, null, lexical forms, ranges, unknown properties, collection size e EOF como não resolvidos (`Stage6:263-279`).

**Escolhas legítimas de interface:**

- Decimal textual para quantidades evita binary float sem inventar política financeira (`Stage6:146-152`; `Stage5:121-126`).
- Strings para datas/referências/descritivos são representação conservadora, não validação de calendário (`Stage5:185-193`; `Stage4:215-221`, `231-237`).
- Enum textual dos motivos preliminares `100..103` é aceitável como rótulo de razão selecionada, desde que `109` continue fora da rejeição preliminar (`Stage6:195-205`; `Stage4:151-181`).

**Evidência ausente / não inventar:**

- Não há base para `format: date`, moeda, positividade, start-before-end, escala global, overflow, coerção, null policy, padding/trimming ou domain validation (`Stage5:121-126`, `185-193`, `481-495`).
- Interest não autoriza positive-balance guard, positive-result guard, default rate ou zero substitution (`Stage6:313-314`; `Stage4:207-221`).
- Reporting não autoriza calendar validity, default range ou conventional filter policy (`Stage6:334`; `Stage4:231-237`, `271-277`).

**Revisão requerida:**

Separar em cada componente:

1. `transport-shape`: tipo JSON, propriedades e descrições.
2. `source-grounded distinctions`: razão 100/101/102/103, `processingTimestamp` construído vs supplied timestamp, zero rate bypass, totals labels.
3. `not validation policy`: datas, moeda, ranges, rounding, trimming, padding, null, unknown properties.
4. `proposal-needs-gate`: qualquer required, regex, enum novo, HTTP request rejection, ou coercion behavior.

**Critério mínimo de fechamento:**

G-22 só fecha na camada documental se todo campo e restrição tiver etiqueta de autoridade. O closure não exige resolver unidade/overflow/calendário para todo domínio; exige impedir que a representação OpenAPI seja lida como validação de negócio COBOL.

### G-23 — Envelopes, status e gatilhos HTTP

**Texto atual:** categorias têm status “Unassigned pending G-23” e body shapes ausentes em vários casos (`Stage6:347-367`). O texto bloqueia `200/202/201/500/503` quando implicariam completude, lifecycle ou diagnóstico universal, mas reconhece que status podem ser escolhidos depois como decisões de representação sem inventar durabilidade (`Stage6:368-379`).

**Escolhas legítimas de interface:**

- Uma resposta HTTP pode representar conteúdo disponível, rejeição preliminar selecionada, ou falha de interface sem prometer durabilidade completa.
- É aceitável escolher envelope com campos como `outputs`, `rejections`, `progress`, `completeness`, `durability`, desde que `durability` e `completeness` não sejam garantias positivas sem evidência.
- `200` ou outro status de sucesso de interface não está proibido em si; é proibido se descrito como “todos os efeitos COBOL completados/duráveis”.
- `4xx` para request fora do schema pode ser proposta de interface, não regra COBOL. Não deve virar “business rejection”.

**Evidência ausente / não inventar:**

- Stage 4 R-6 estabelece ordered attempts e não atomicidade/durabilidade (`Stage4:183-189`). Stage 5 D-4 recusa atomic success, rollback, durable partial state, failure diagnosis e safe repetition (`Stage5:114-119`).
- External failure via `CEE3ABD` não fornece retorno, rollback ou diagnóstico público (`Stage4:279-285`; `Stage5:343-353`).
- Internal attempt states não são telemetry pública (`Stage6:154-160`, `251-261`).
- Repetition safety é unknown per track, não idempotency/retry receipt (`Stage6:381-420`; `Stage4:295-301`).

**Revisão requerida:**

Para cada operação, definir uma tabela proposta:

| Response case | HTTP status proposto | Body | Gatilho observável | Promessa negada |
|---|---|---|---|---|
| interface accepted/processed to available boundary | design proposal | envelope com componentes permitidos | boundary do adapter/contrato, não COBOL completo | sem durabilidade, sem completude global |
| preliminary posting rejection | design proposal | `PostingRejection` | razão preliminar selecionada | não é erro técnico, não lista todos checks |
| request-representation rejection | design proposal | erro de interface mínimo | schema/interface policy | não é regra de negócio COBOL |
| technical/external failure known to boundary | design proposal/unknown | erro sem diagnóstico interno | apenas se observável | sem rollback, sem no-effects, sem file status |
| unknown/partial effects | não status separado ou corpo unknown | `durability: unknown` se representado | não observável como sucesso/falha completo | sem retry/idempotency |

**Critério mínimo de fechamento:**

G-23 fecha documentalmente quando cada status/corpo diz exatamente qual gatilho é observável e quais garantias não existem. Não precisa provar persistência; precisa não prometer persistência.

### G-24 — Reporting completeness e finalização

**Texto atual:** reporting response permite `ReportDetail`, `ReportHeaderContext`, `ReportTotal`, mas não mandatory header/final total/complete collection/empty-report success; response assembly fica G-23/G-24 (`Stage6:328-334`). G-24 exige delimitar completude sem reparar R-12..R-17 (`Stage6:502-507`).

**Escolhas legítimas de interface:**

- Manter schemas de detail/header/total é válido como representação de conteúdo disponível (`Stage6:227-249`).
- `ReportTotal.label` como `page/account/grand` é uma decisão de representação aceitável, desde que não adicione account identity/page number/group cardinality (`Stage6:235-240`).
- Um envelope pode declarar `completeness: not_attested` ou `complete: false/unknown` como limite explícito, sem bloquear todo schema de reporting.

**Evidência ausente / não inventar:**

- Date failure leaves loop sentence, não skip-and-continue (`Stage4:231-237`; `Stage5:273-284`).
- EOF finalization é condicional e assimétrica, sem final account-total call (`Stage4:255-261`; `Stage5:273-284`).
- Job SORT/date basis e COBOL date basis são separados; output completo não é simples interseção (`Stage4:271-277`; `Stage5:327-341`).
- Report output durability/interruption e actual final totals continuam não resolvidos (`Stage5:327-341`, `453-495`).

**Revisão requerida:**

Criar no contrato revisado uma semântica de retorno de reporting nestes termos:

- `items`/`records` representam conteúdo de relatório tornado disponível no boundary, não totalidade do relatório COBOL.
- Ausência de `ReportDetail` não significa relatório vazio completo.
- Ausência de `ReportTotal` não significa zero.
- Header dates não certificam que toda transação no range foi processada.
- Totais não são reconciliados nem finais salvo onde o próprio conteúdo diz `page`, `account` ou `grand`, e mesmo assim como emitido/observado, não como total global certificado.

**Critério mínimo de fechamento:**

G-24 fecha documentalmente quando o response shape de reporting explicita parcialidade e não-atestação de completude. Fica bloqueado para qualquer promessa de relatório completo, total final, empty success ou EOF resolution sem nova autoridade.

## Lacunas reais versus decisões de interface

| Item | Classificação correta | Por quê | Fecha como |
|---|---|---|---|
| Rotas `POST /posting`, `/interest`, `/reporting` | escolha legítima de interface | Stage 5 preserva trilhas separadas; POST não promete idempotência | manter D-9 como proposta |
| OpenAPI 3.1 components | escolha legítima | schema representável não é validação | manter D-10, adicionar authority tags |
| Decimal textual | escolha legítima conservadora | evita float; não escolhe escala/moeda | manter D-11 |
| Required fields | design proposal | depende do modelo de request escolhido | precisa gate |
| Arrays/coleções | design proposal com risco | pode preservar batch, mas não per-record guarantee | precisa matriz de granularidade |
| Status HTTP | design proposal | permitido se não promete runtime guarantee | precisa tabela de gatilho/promessa negada |
| Durability/atomicity/retry | evidence gap / proibido como garantia | Stage 5 D-4 e Stage 4 R-6/R-18/R-20 | não fechar no Stage 6 |
| Reporting complete result | evidence gap | R-12/R-15/R-17 deixam EOF/date/job incertos | só `not_attested`, sem promessa positiva |
| Business validation | evidence gap / proibido | Stage 5 D-5/G-17 | não inventar |
| Internal telemetry | proibido sem autoridade | Stage 5 D-3/D-4; Stage 6 D-12 | não expor |

## Pontos que não devem ser prescritos

- Não dizer que `POST /posting` processa exatamente um registro por chamada se o modelo batch/sequencial não foi escolhido.
- Não dizer que `POST /posting` recebe necessariamente array se a sequência pode ser externa; se escolher array, marcar como proposta de interface.
- Não expor account/category/disclosure/xref como campos consumer-controlled.
- Não adicionar `postedCount`, `successCount`, `committed`, `rolledBack`, `retryable`, `idempotencyKey`, `jobId`, `statusUrl`, branch `reason`, file status, telemetry ou diagnostics internos.
- Não tratar preliminary posting rejection como validação HTTP comum.
- Não transformar reason 109 em preliminary rejection.
- Não transformar missing disclosure em zero rate.
- Não tratar ausência de report records/totals como relatório vazio ou total zero.
- Não transformar page total em paginação API.
- Não prometer que failure response implica nenhum efeito anterior.

## Ambiguidade upstream que exigiria aprovação de Stage 5 alterado

A revisão Stage 6 deve parar e pedir decisão humana se quiser fazer qualquer uma destas mudanças:

- unificar as três trilhas em uma operação/ciclo obrigatório;
- transformar recursos internos em APIs de estado ou campos do consumidor;
- declarar reset, retry, idempotência, rollback, compensation ou atomicidade;
- converter relatório em contrato de completude/finalização positiva;
- impor regras financeiras/calendário/validação de negócio não derivadas de Stage 5;
- remover reporting ou interest por dificuldade de schema.

Essas mudanças contradizem `Stage5:100-147`, `Stage5:286-353` e não são corrigíveis só no Stage 6.

## Recomendação operacional

A autorização atual é suficiente para uma revisão versionada do Stage 6 que aplique este feedback, desde que a revisão seja marcada como `draft/proposed-interface`, preserve o original SHA `753a60a5ee7b1fb6d94f6ab982afe415bc01adca040bb3d89e24ffc60342bba7`, e não aprove gate nem avance para Stage 7.

Uma decisão humana consequencial é necessária antes de aceitar como contrato vinculante qualquer escolha de request granularity, required/null policy, HTTP status trigger, response envelope ou reporting completeness. A revisão pode propor essas escolhas; não pode apresentá-las como fato COBOL estabelecido nem como aprovação automática.