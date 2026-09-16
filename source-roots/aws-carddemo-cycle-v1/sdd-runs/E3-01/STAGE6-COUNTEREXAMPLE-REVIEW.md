# Stage 6 Counterexample Review — API Contract CardDemo

Conclusão: **não pronto para implementação/Stage7; revisão recomenda manter como rascunho documental não aprovado.**

Esta revisão comparou o contrato Stage6 atual com Stage5, Stage4 e trechos do corpus pinado. Não regenerei, não corrigi o contrato, não executei COBOL, não chamei modelo/rede, e não validei OpenAPI standalone.

## Evidência de escopo

- Stage6 requirements: `specs/api-contract-carddemo/requirements.md` SHA `144750e350057971ee854856b8aa48ed7039904b7ab0a5bbc0bf8af96d8ded74`.
- Stage5 canonical boundary: `specs/canonical-data-boundary-carddemo/requirements.md` SHA `208d04fe6f9cae665dfa4cb514de5d4ad9eaf0ebc169dfae0fd8a6ba209e66f3`.
- Stage4 capability semantics: `specs/capability-semantics-carddemo/requirements.md` SHA `2f9d3ee52dd7788e206810e38c9173b19d21dfc44270cdd06d05e62dec95eb93`.
- Corpus source pins em `specs/api-contract-carddemo/input-pins.json`; exemplos conferidos em `CBTRN02C.cbl`, `CBACT04C.cbl`, `CBTRN03C.cbl`, `TRANREPT.jcl`.

## 1. Schema/rota/status: representação versus promessa inventada

Stage6 escolhe `POST /posting`, `POST /interest`, `POST /reporting` como **decisões de representação** (`D-9`), mas a própria linha de contrato mantém request participation e response availability bloqueadas por `G-21`..`G-23`. Isso é coerente com Stage5 `D-2/D-3/D-4`: trilhas separadas, recursos internos não expostos como APIs de estado, sem atomicidade/rollback/retry-safe.

Contraexemplo testado: tratar `POST /posting` como endpoint pronto com payload array, status `200`, ou recibo durável. O texto Stage6 não sustenta isso: status HTTP está “Unassigned pending G-23”, e `200/202/204/500/503` são explicitamente recusados quando implicariam completude, lifecycle ou diagnóstico universal. Logo, o artefato é documental; não é contrato HTTP executável completo.

## 2. Ausente versus zero

Stage5 linhas 185-193 distingue referências, quantidades, temporalidade, ausência e zero. Stage6 preserva essa distinção ao representar quantidades como texto decimal e recusar unidade, escala, rounding, coercion e date format em `D-11/G-22`.

Contraexemplos fonte:

- Disclosure ausente em interest não vira taxa zero; Stage4/Stage5 já registram reread DEFAULT e não substituição por zero.
- Finalização ausente em interest/reporting não vira total zero nem relatório vazio completo.
- Filler/declaration-only não vira campo descartável nem significado de negócio.

Resultado: não encontrei invenção de política zero-default na Stage6, mas `G-22/G-24` bloqueiam validação concreta de entrada e relatório.

## 3. Falhas condicionais e efeitos não atômicos

Stage5 `D-4` (linhas 114-119) recusa sucesso atômico, rollback, estado parcial durável e repetição segura. O corpus de posting mostra operações ordenadas em `CBTRN02C.cbl` antes de falhas posteriores: lookup/contas/transações e paths de erro em torno de `424-579`. Reporting escreve detalhe/totais antes de falhas possíveis em lookups/output (`CBTRN03C.cbl:274-322`, `486-510`).

Contraexemplo testado: transformar falha técnica em resposta HTTP única que promete “nenhum efeito”. Stage6 evita isso: “Partial durable effects” não é status reportável, não há snapshot de estado, e falhas externas via `CEE3ABD` não têm schema diagnóstico público licenciado. Isso é correto, mas deixa o contrato incompleto.

## 4. EOF e relatório parcial

Reporting tem fluxo sensível a data/EOF: `TRANREPT.jcl:37-74` filtra por SORT e `CBTRN03C.cbl:170-213` aplica lógica COBOL adicional; totais são escritos em calls distintas (`274-322`). Stage5 `D-6/D-7` impede reparar com “skip-and-continue”, “final total” ou paginação convencional.

Stage6 mantém `G-24`: não define relatório completo, empty success, EOF de date-input, post-read storage, nem final account total. Portanto, qualquer adapter que retorne uma coleção completa ou total final obrigatório estaria além desta Stage6.

## 5. Políticas numéricas e datas

Stage6 `D-11` é defensável como representação conservadora: strings para datas/referências e decimal text para quantidades evitam binary float e formatos inventados. Mas isso não resolve escala, sinal, moeda, overflow, calendário válido, normalização, padding/trimming ou coerção. Stage5 `D-5/G-17` permanecem bloqueadores para schemas validadores completos.

Contraexemplo: aplicar `format: date`, currency BRL/USD, positive-only amount ou regex por largura COBOL. Isso seria invenção; Stage6 não o faz, e por isso também não entrega validação OpenAPI pronta.

## 6. Observabilidade interna

Stage6 `D-12` exclui branch telemetry e estados internos (`PostingAttemptState`, `InterestAttemptState`, `ReportingAttemptState`) de respostas públicas. Isso se alinha a Stage5 `D-3`: conta, categoria, disclosure, lookup, suffix e estado de arquivo são dependências internas, não APIs consumer-controlled.

Contraexemplo: expor `reason`, file status, lookup status, account rewrite status, ou retry/idempotency receipt como debug schema. Stage6 não licencia isso. Lacuna restante: sem outra decisão humana, o adapter não sabe qual envelope observável devolver.

## 7. Todas as três trilhas

A revisão confirmou cobertura documental das três trilhas obrigatórias:

- Posting: `R-1..R-6`, `POST /posting`, `PostingCandidate/Transaction/Rejection/Progress`, com `G-21/G-22/G-23`.
- Interest: `R-7..R-11`, `POST /interest`, category/identifier/generated transaction, com numeric/request/response gaps.
- Reporting: `R-12..R-17` mais falhas cross-track, `POST /reporting`, date basis/detail/header/total, com `G-21/G-23/G-24`.

`R-18..R-20` aparecem como limites de falha externa, operational flow e repetição, não como endpoints. Essa exclusão é justificada por Stage5 `D-4/D-7` e não por esquecimento.

## 8. Omissões justificadas versus gaps bloqueadores

Omissões justificadas:

- CRUD de account/category/disclosure/xref, state snapshot, reset, rollback, compensation, retry, idempotency-key, scheduling e pagination: excluídos por `D-3/D-4/D-7/D-8`.
- Fee computation: placeholder não autoriza semântica de negócio.
- Status/file codes como HTTP status: recusado corretamente.

Gaps bloqueadores autodeclarados e confirmados:

- `G-21`: participação de request para sequências/data ainda indefinida.
- `G-22`: schemas e validação completos não definidos.
- `G-23`: envelope de resposta, cardinalidade, disponibilidade e gatilhos HTTP ausentes.
- `G-24`: completude/finalização de reporting ausente.
- Herdados `G-17/G-19`: numérico/data/runtime/durabilidade/EOF/job flow continuam limitando claims fortes.

## 9. Classificação honesta

- **Blocker para contrato concreto executável:** sim. Falta boundary de request/response/status.
- **Blocker para OpenAPI validado:** sim. Não existe artifact OpenAPI standalone validado; há apenas texto representável em tese.
- **Blocker para implementação/Stage7:** sim. O próprio artifact declara gate não passado e não pronto.
- **Contradição source-grounded nova contra Stage5/Stage4:** não encontrei nos contraexemplos revisados; o problema principal é incompletude assumida, não invenção flagrante.
- **Aprovação humana:** nenhuma; não deve ser inferida da materialização nem desta revisão.

## Recomendação

Manter Stage6 como **draft documental materializado, unapproved**. Antes de Stage7 ou adapter, uma decisão humana/metodológica precisa resolver ou explicitamente estreitar `G-21`..`G-24`; caso contrário, qualquer implementação teria que inventar payloads, status HTTP, envelopes e completude de reporting.


## Correção de materialização e proveniência

Conferência direta posterior: requirements.md era apenas o placeholder de init, não uma versão experimental concorrente. Foi arquivado sem alterações em specs/api-contract-carddemo/requirements-initial-placeholder.md; requirements.md recebeu exatamente os bytes de scope-original.md, também coincidentes com parsed.text. SHA-256 da resposta/materialização: 753a60a5ee7b1fb6d94f6ab982afe415bc01adca040bb3d89e24ffc60342bba7. O hash 0e5d2063f232c500e94ff3513cb5a9a0640a82d16cc3bc2aa9cdbea33183f79d é do request serializado canonicamente, não da resposta. As referências anteriores ao hash 144750... identificam o placeholder, não o texto substantivo revisado. A revisão substantiva refere-se ao original gerado. G-21..G-24 permanecem abertos, sem aprovação. gate.review restaurado a null (não houve decisão humana). Nenhuma resposta do modelo foi corrigida ou regenerada.
