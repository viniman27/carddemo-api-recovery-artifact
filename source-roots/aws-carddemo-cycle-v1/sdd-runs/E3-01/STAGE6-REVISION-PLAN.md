# Plano de Revisão Stage 6 — API Contract CardDemo

## Metadados de controle

- RUN: `casos/aws-carddemo-cycle-v1/sdd-runs/E3-01`
- Artefato Stage 6 original/materializado: `specs/api-contract-carddemo/requirements.md`
- SHA-256 original/materializado conferido: `753a60a5ee7b1fb6d94f6ab982afe415bc01adca040bb3d89e24ffc60342bba7`
- Original preparado: `prepared/api-contract-carddemo/execution/scope-original.md`, mesmo SHA `753a60a5ee7b1fb6d94f6ab982afe415bc01adca040bb3d89e24ffc60342bba7`
- Stage 5 aprovado como entrada: `specs/canonical-data-boundary-carddemo/requirements.md`, SHA `208d04fe6f9cae665dfa4cb514de5d4ad9eaf0ebc169dfae0fd8a6ba209e66f3`
- Stage 4 aprovado como entrada: `specs/capability-semantics-carddemo/requirements.md`, SHA `2f9d3ee52dd7788e206810e38c9173b19d21dfc44270cdd06d05e62dec95eb93`
- Instrução humana original Stage 6 registrada: `se nao existem mais ressalvas, pode prosseguir` (`stage6-generation-authorization.json:7-10`)
- Instrução humana desta revisão: “Analyze full generated Stage6 G21..24 against Stage5/4 and source grounded constraints to produce actionable revision feedback (not replacement contract)... Recommend whether current authorization is sufficient for one versioned Stage6 revision with this feedback or a consequential human choice is necessary.”

## Objetivo da revisão

Produzir uma revisão versionada do Stage 6 que transforme o rascunho atual em um contrato documental mais acionável, sem convertê-lo em contrato executável aprovado e sem reparar lacunas por invenção. A revisão deve manter as três trilhas obrigatórias (`posting`, `interest`, `reporting`) e preservar as decisões congeladas do Stage 5.

Este plano não substitui o contrato. O feedback dirigido está em `reviews/stage-6-r1-directed-feedback.md`.

## Fontes inspecionadas

- `WORKSPACE-NOTES.md:12-18`, `32-43`, `122-170`: disciplina de pipeline, taxonomia e limites de estágio.
- `stage6-generation-authorization.json:7-10`: autorização original para Stage 6, sem Stage 7/implementação.
- `reviews/stage-5-authorization.json:7-11`: escopo aprovado do Stage 5, autorização para Stage 6 e limites residuais.
- `STAGE6-RESULT.md:78-80`: correção de materialização/proveniência.
- `STAGE6-COUNTEREXAMPLE-REVIEW.md:14-92`: revisão anterior e sua classificação excessivamente bloqueante para contrato concreto.
- `specs/api-contract-carddemo/requirements.md:100-170`, `263-379`, `498-511`, `513-542`: decisões D-9..D-13, G-21..G-24 e gate.
- `specs/canonical-data-boundary-carddemo/requirements.md:96-147`, `185-193`, `195-243`, `245-353`, `453-495`: decisões D-2..D-8, limites de valores, operação/campo/estado e gaps herdados.
- `specs/capability-semantics-carddemo/requirements.md:99-139`, `143-301`, `338-360`: R-1..R-20 e ambiguidades A-1..A-17.
- Pins do corpus em `specs/api-contract-carddemo/input-pins.json:89-207`; as citações de fonte devem continuar resolvendo via Stage 3/4, não por novos anchors inventados.

## Diagnóstico resumido

O Stage 6 atual tem boas escolhas de representação, mas trata G-21..G-24 como lacunas que bloqueiam quase todo contrato concreto. Isso é parcialmente correto para promessas de implementação, durabilidade, completude e validação de negócio; porém é amplo demais para a camada documental de API. Uma revisão pode separar:

1. **Escolhas legítimas de interface**: rotas `POST /posting`, `POST /interest`, `POST /reporting`; OpenAPI 3.1; strings para datas/referências; decimal textual para quantidades; exclusão de telemetry/debug interno; categorias de erro separadas.
2. **Evidência realmente ausente**: participação exata de entradas, domínio lexical aceito, required/null/coercion, gatilhos/status/envelopes observáveis, completude de reporting, durabilidade, EOF e efeitos parciais.
3. **Propostas autorizáveis**: um HTTP documental pode representar “resultado observado/disponível”, “efeitos de durabilidade desconhecidos” e “completude não atestada” sem prometer atomicidade, retry, idempotência, telemetry interna ou relatório completo.

## Direção de revisão por lacuna

### G-21 — Participação de request

- **Não fechar como fato COBOL**: o corpus não estabelece se a API recebe array de registros, seleciona sequência externa, aceita singleton, ou sinaliza EOF.
- **Revisar como decisão de interface proposta**: declarar explicitamente quais campos seriam `consumer-supplied` e quais permanecem `externally supplied/internal dependency`.
- **Preservar granularidade**: não transformar processamento batch/sequencial em semântica per-record obrigatória. Se houver endpoint com coleção, chamar isso de representação da participação de sequência, não de garantia de transação por registro.
- **Critério mínimo de fechamento documental**: cada operação deve ter um modelo de request marcado como `proposed-interface`, com matriz campo a campo: consumidor fornece / ambiente fornece / não exposto / desconhecido. A ausência/EOF deve ser representada como desconhecida ou fora do contrato, não como array vazio com significado de sucesso.

### G-22 — Schema e validação

- **Não inventar validação de negócio**: nada de `format: date`, moeda, positivo obrigatório, range financeiro, rounding, calendário, trimming/padding/coercion, ou rejeição de domínio sem autorização.
- **Revisar como schema estrutural mínimo**: documentar shape JSON e tipos de transporte, com `required` somente quando a proposta de request decidir que o consumidor deve fornecer o campo. Usar descrições para limites e não para prometer validação COBOL.
- **Numericidade**: manter quantidades em decimal textual e report presentation em texto; se algum padrão lexical for proposto, rotular como restrição de transporte proposta, não evidência COBOL.
- **Critério mínimo de fechamento documental**: separar `schema-shape` de `validation-policy`; todo `required`, enum, regex, range ou formato deve ter uma de três etiquetas: `source-grounded`, `interface-proposal-needs-gate`, ou `not-specified`.

### G-23 — Envelopes, status e gatilhos HTTP

- **Não bloquear status globalmente**: escolher HTTP status para uma representação concreta é permitido se a descrição não prometer durabilidade/completude. O próprio Stage 6 reconhece isso em `requirements.md:379`.
- **Não prometer atomicidade/retry/internal telemetry**: respostas não devem incluir file status, branch trace, rollback, idempotency receipt, retry token, diagnostic universal, ou “no effects”.
- **Revisar como envelope observacional**: permitir envelope que diga quais conteúdos estão disponíveis/representados, quais efeitos são desconhecidos e se completude é não atestada. Status deve mapear a condição da interface, não o resultado interno completo do COBOL.
- **Critério mínimo de fechamento documental**: para cada resposta/status proposto, registrar: gatilho observável autorizado, corpo permitido, promessa explicitamente negada, e lacuna residual. Se o gatilho exige runtime/adapter, marcar como proposta para gate, não fato.

### G-24 — Reporting completeness/finalização

- **Não substituir incerteza por relatório vazio/completo**: EOF de date-input, storage pós-read, early exit e job flow continuam incertos.
- **Não bloquear todo schema de reporting**: `ReportDetail`, `ReportHeaderContext` e `ReportTotal` podem existir como representações de conteúdo disponível, sem promessa de coleção completa ou total final.
- **Preservar parcialidade**: o contrato pode representar `completeness: not_attested` ou equivalente; não pode dizer que a lista é completa, que não há mais registros, que o total reconcilia, ou que ausência de itens significa zero/empty success.
- **Critério mínimo de fechamento documental**: todo retorno de reporting precisa distinguir “conteúdo emitido/observável” de “relatório completo”. Qualquer campo de completude deve ser negativo/unknown, não uma garantia positiva sem nova evidência.

## Mudanças permitidas na revisão Stage 6 r1

- Criar uma versão revisada do Stage 6, preservando o original e sua SHA.
- Reclassificar G-21..G-24 em: `interface-choice`, `evidence-gap`, `gate-required-design-proposal`, e `blocks-runtime-guarantee`.
- Acrescentar matriz de origem dos campos: `consumer-supplied`, `externally supplied`, `internal dependency`, `output content`, `not exposed`, `unknown`.
- Especificar uma representação HTTP concreta proposta com ressalvas, desde que ela não prometa durabilidade, completude, atomicidade, retry, idempotência, reset, telemetry interna, ou validação de negócio não autorizada.
- Marcar toda decisão nova como proposta de interface para aceitação no gate, não como fato COBOL estabelecido.

## Mudanças proibidas

- Não editar specs originais, aprovações, quarentena, fonte COBOL, corpus ou autorizações existentes.
- Não executar COBOL, gerar código, chamar modelo/rede, iniciar Stage 7, ou implementar adapter.
- Não reduzir o escopo para uma trilha; posting, interest e reporting permanecem obrigatórios.
- Não adicionar CRUD, reset, rollback, retry, idempotency-key, status-resource, pagination, job scheduling, fee computation ou business validation convencional.
- Não usar lacuna de EOF/durabilidade para remover schemas/status que possam ser documentados como proposta sem garantia forte.

## Ambiguidades que exigiriam alterar Stage 5 antes de prosseguir

A revisão Stage 6 não deve tentar “corrigir” upstream se for necessário:

- transformar recursos internos de account/category/disclosure/xref em APIs consumer-controlled;
- declarar atomicidade, rollback, durable partial-state ou retry-safe;
- redefinir reporting como relatório completo/reconciliado com total final obrigatório;
- adicionar validações de negócio como moeda, calendário, positividade, ou política de arredondamento;
- unificar posting/interest/reporting em um ciclo obrigatório ou endpoint único.

Esses pontos contradizem Stage 5 D-2..D-8 e exigiriam aprovação explícita de mudança de Stage 5, não apenas revisão do Stage 6.

## Recomendação de autorização

A autorização atual é suficiente para **uma revisão versionada do Stage 6** limitada a incorporar este feedback como contrato documental/proposta de interface, preservando o original e sem avançar para implementação.

Uma escolha humana consequencial é necessária **antes de aprovar o gate, iniciar Stage 7 ou tornar vinculantes** as propostas que selecionem request granularity, required fields, status triggers, envelope semantics ou qualquer noção de completude. Se a revisão quiser resolver essas escolhas como obrigação aceita, e não apenas registrá-las como proposta para revisão humana, deve parar para decisão humana.