# Stage6 r2 Counterexample Review — API Contract CardDemo

## Veredito

**Recomendação: enviar para gate humano como Stage 6 r2 documental candidato; manter `approved=false` e `ready_for_implementation=false`.**

Não encontrei contraprova documental que obrigue descartar o r2 como revisão Stage 6, mas a revisão ainda depende de aceitação humana porque faz propostas de design novas/mais concretas. Ela fecha G-21..G-24 como lacunas amplas de contrato somente no sentido documental: escolhe representação HTTP/schema/status/envelope para revisão, mantendo sem garantia runtime, persistência, completude, retry, EOF reparado ou validação de política de negócio.

## Base lida

- R2 gerado/materializado: `specs/api-contract-carddemo-r2/requirements.md` (`scope-original.md` SHA `163d1d0455f2524e8100e1722b78f255fbca7a4bda1a5caccb45e05fbe362567`)
- Feedback r1: `reviews/stage-6-r1-directed-feedback.md` SHA `87a74e6570babd2e5e811ba1c0a6f0ee2d5cd0bdfbe4bdbb5504e3e9bfe4659c`
- Plano de revisão: `STAGE6-REVISION-PLAN.md` SHA `51ce5a1a13ab107b5c6f0df536c371e3337ad79275da0377021c273598a59c35`
- Stage 6 r1 original: `specs/api-contract-carddemo/requirements.md` SHA `753a60a5ee7b1fb6d94f6ab982afe415bc01adca040bb3d89e24ffc60342bba7`
- Stage 5: `specs/canonical-data-boundary-carddemo/requirements.md` SHA `208d04fe6f9cae665dfa4cb514de5d4ad9eaf0ebc169dfae0fd8a6ba209e66f3`
- Stage 4: `specs/capability-semantics-carddemo/requirements.md` SHA `2f9d3ee52dd7788e206810e38c9173b19d21dfc44270cdd06d05e62dec95eb93`
- Stage 3-r2: `specs/legacy-evidence-carddemo-r2/requirements.md` SHA `4566786600b60e9377c1e369e67765098d06b0153ba973361d2065614a6c9b7b`

## G21..G24 — fechamento real versus relabeling

- **G-21 participation:** r1 pedia escolher participação por trilha sem inventar cardinalidade HTTP. R2 introduz D-14: requests `PostingRequest`, `InterestRequest`, `ReportingRequest` são objetos JSON vazios, fechados e obrigatórios; inputs batch/datas/bases continuam externos ou internos, não propriedades do consumidor (`requirements.md:167`, `302`). Isso é fechamento documental de shape, não runtime guarantee.
- **G-22 schema/validation:** D-10/D-11 e §3.1/§3.5 escolhem objetos fechados, requiredness, strings para valores decimais/data/referência e erro estrutural, mas preservam D-5 Stage5: sem unidades, rounding, domínio numérico, calendário ou lifetime inventados (`requirements.md:177`, `302`).
- **G-23 response boundary:** D-13/D-15..D-17 e §5 propõem categorias/envelopes, disponibilidade `available/not_attested` e conteúdo não-vacuuo (`requirements.md:185`, `197`, `338`, `487`). Não prometem entrega universal, durabilidade, rollback, retry ou observabilidade completa.
- **G-24 reporting finalization:** §3.3, §3.4 e §7.3 mantêm relatório como array ordenado/misto de header/detail/total quando disponível; não convertem total ausente em zero nem EOF/finalização em garantia reparada (`requirements.md:322`, `631`).

Conclusão: o r2 não apenas relabela blockers; ele escolhe D-14..D-17 e restringe o que permanece sem autoridade. O fechamento é documental e condicional ao gate humano, não pronto-para-implementar.

## Três tracks — request/schema/status/envelope

- **Posting:** `POST /posting`; request vazio fechado; resposta com `PostingSuccessEnvelope`; conteúdo de candidate/transaction/rejection/progress e distinção 100..103; 109 não é preliminar consumer-facing. Citações: `requirements.md:381-410`, matriz `577-585`, tabela estado `522-527`.
- **Interest:** `POST /interest`; request vazio fechado; bases account/xref/disclosure internas ou externas, não controladas por request; generated transaction opcional/representado quando disponível; disclosure ausente não é zero-rate. Citações: `requirements.md:413-440`, matriz `587-591`, tabela estado `530-537`.
- **Reporting:** `POST /reporting`; request vazio fechado; selection/date basis externo/documental; envelope ordenado de records heterogêneos; total/report ausente não é sucesso vazio. Citações: `requirements.md:443-468`, matriz `592-597`, tabela estado `541-549`.

## Traceabilidade R1..R20 e reverse completeness

Validação programática: `R-1..R-20` aparecem no documento e a seção reverse-completeness cobre `20/20`; faltantes: `[]`. A matriz começa em `requirements.md:577` e liga regras a E-n, destino de contrato e limites. Isso cobre todos os R-n, mas não prova que cada cláusula futura de OpenAPI seria implementável sem decisões adicionais.

## Pontos de política conferidos

- **Numéricos/datas:** mantidos como strings/representação conservadora; sem rounding, unidade, calendário ou domínio inventado, alinhado com Stage5 D-5 (`Stage5 requirements.md:None`, r2 `requirements.md:143-151`).
- **Granularidade batch, ordem e multiplicidade:** D-14/D-15 escolhem processamento batch por entrada externa e envelopes ordenados; preserva multiplicidade representada sem criar EOF HTTP (`requirements.md:167-177`, `322`).
- **Sem contrato vacuoso all-empty:** §3.4 exige que `200` contenha ao menos uma seção disponível ou falhe como indisponível, evitando sucesso vazio (`requirements.md:338`).
- **unknown vs false:** `not_attested` é falta de atestação, não false/incompleto confirmado; missing disclosure/report/total não vira zero (`requirements.md:185`, `631`).
- **Optional outputs vs telemetry:** D-12/D-17 excluem branch telemetry, file status, retries, idempotency receipts, rollback/status resources; outputs opcionais são representações de disponibilidade, não telemetria (`requirements.md:153-157`, `197`).
- **Partial reporting/EOF:** G-24 permanece como limite estreito; não há reparo de EOF/finalização nem total certificado (`requirements.md:631`).
- **Rejects 100..103 vs 109:** contagens programáticas 100=3, 101=2, 102=3, 103=5, 109=8; o texto trata 109 como razão interna/local, não preliminary business rejection.

## Propostas novas que exigem gate humano

- D-14: modelo de participação por request vazio fechado e batch externo.
- D-15: envelopes ordenados e arrays de conteúdo por disponibilidade.
- D-16: constantes/semântica de não-atestação e bloqueio a sucesso vazio.
- D-17: disponibilidade opcional sem apagar obrigações observáveis.

Essas escolhas são plausíveis e rastreáveis, mas são decisões de interface propostas; não devem ser tratadas como aprovação, runtime guarantee ou autorização Stage7.

## OpenAPI

Não há documento OpenAPI standalone no r2. Nenhum validador OpenAPI real foi executado. A checagem é de representabilidade/documentação, não de validade de especificação OpenAPI pronta para implementação.

## Limitações

- Revisão documental por inspeção e regex; não houve rede, geração, execução COBOL, implementação, Stage7, nem aprovação automática.
- As citações de fonte COBOL continuam indiretas via Stage3/4 E/R; r2 contém `3` âncoras fonte full e `0` shorthand próprias, evitando criar novos fatos fonte.
- A classificação depende dos textos congelados de Stage3-r2/4/5 e do feedback r1; não valida comportamento runtime.

## Recomendação final

Aceitar apenas como **candidato documental Stage 6 r2 para gate humano**. Manter bloqueado para implementação até revisão humana aprovar explicitamente as propostas D-14..D-17 e os limites residuais de G-21..G-24.
