# Stage 6 Result — API Contract CardDemo

Status: **geração verificada, requirements.md existente difere da resposta gerada e não foi sobrescrito; gate não aprovado; não pronto para Stage 7/implementação**.

## Escopo revisado

- RUN: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/sdd-runs/E3-01`
- Spec dir: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/sdd-runs/E3-01/specs/api-contract-carddemo`
- Resposta gerada: `prepared/api-contract-carddemo/execution/parsed.json`
- Recibo metadata: `prepared/api-contract-carddemo/execution/metadata.json`
- Original preparado: `prepared/api-contract-carddemo/execution/scope-original.md`
- Upstream imediato: `specs/canonical-data-boundary-carddemo/requirements.md`
- Stage 4 semântica: `specs/capability-semantics-carddemo/requirements.md`
- Corpus: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-preparation/research-corpus`

## Verificações mecânicas

| Item | Resultado | Evidência |
|---|---:|---|
| parsed status | `completed` | `prepared/api-contract-carddemo/execution/parsed.json` |
| parsed model | `gpt-6-astra` | `prepared/api-contract-carddemo/execution/parsed.json` |
| metadata model | `gpt-6-astra` | `prepared/api-contract-carddemo/execution/metadata.json` |
| HTTP status receipt | `200` | metadata |
| tools | `[]` | parsed |
| previous_response_id | `None` | parsed |
| store | `False` | parsed |
| requirements.md | `blocked_existing_requirements_differs_no_overwrite` | SHA `144750e350057971ee854856b8aa48ed7039904b7ab0a5bbc0bf8af96d8ded74` |
| materialization blocker | `Existing requirements.md is not byte-identical to parsed Stage6 response; no overwrite performed per task constraint.` | no overwrite if existing differs |
| byte-identical to parsed text | `False` | parsed text SHA `753a60a5ee7b1fb6d94f6ab982afe415bc01adca040bb3d89e24ffc60342bba7` |

## Hashes principais

| Artefato | SHA-256 | Bytes |
|---|---|---:|
| `prepared/api-contract-carddemo/execution/parsed.json` | `72597c2ad3d0034ddf3307692b1c468314f3159f3756d061ed232dfee97309de` | `46538` |
| `prepared/api-contract-carddemo/execution/metadata.json` | `c50fafe749e6dda1973e890ed014a050b3e718b238b76677a124aa5998f3aeb7` | `1378` |
| `prepared/api-contract-carddemo/execution/scope-original.md` | `753a60a5ee7b1fb6d94f6ab982afe415bc01adca040bb3d89e24ffc60342bba7` | `44132` |
| `specs/api-contract-carddemo/requirements.md` | `144750e350057971ee854856b8aa48ed7039904b7ab0a5bbc0bf8af96d8ded74` | `239` |
| `specs/api-contract-carddemo/spec.json` | `d1da55b75c48eb0e02dcddfa0785bbe1962268fc257b5e4a2e0d9d77e1410dcf` | `1622` |
| `specs/api-contract-carddemo/input-pins.json` | `c56d1b9e68db3f0e724702672c702c476564669a9dd706f9caccb3882ba4de12` | `10809` |
| `stage6-generation-authorization.json` | `a6f9017a08ab8c4a0ea133908525944f3b2724c7286d0244a296289779b88298` | `509` |

## Atualização permitida de metadata

Alterei apenas `specs/api-contract-carddemo/spec.json` para registrar:

- `approvals.requirements.generated = true`
- `approvals.requirements.approved = false`
- `gate.completeness_gate_passed = false`
- `gate.review = unapproved_pending_human_review`
- `gate.blocking_gaps = [G-21, G-22, G-23, G-24]`
- `ready_for_implementation = false`

Não alterei autorizações, upstreams, corpus, aprovações humanas, Stage7, código, quarentena ou artifacts originais.

## Contagens reais e cobertura reversa

- Stage6 text: 542 linhas, 44132 bytes, SHA `753a60a5ee7b1fb6d94f6ab982afe415bc01adca040bb3d89e24ffc60342bba7`.
- IDs `R`: 20 (`R-1`..`R-20`) — todos aparecem e foram auditados como destino/gap/exclusão.
- IDs `D`: 12 (`D-2`..`D-13`) — `D-2`..`D-8` herdados, `D-9`..`D-13` decisões documentais Stage6.
- Tipos extraídos das tabelas Stage6: 17.
- Categorias de resposta: 8, todas com status HTTP não atribuído ou explicitamente não reportável.
- Source bodies pinados: 19; derived representations pinadas: 19.

O JSON estruturado em `specs/api-contract-carddemo/stage6-verification.json` contém a matriz `R-1..R-20`, decisões `D`, tipos, categorias, hashes antes/depois, anchors e limitações de rastreabilidade.

## Limites de anchors e rastreabilidade

- Anchors examinados: 74; bounds válidos resolvidos por fonte pinada: 74.
- Referências completas e shorthand coexistem. Shorthand como `CBTRN02C.cbl:370-422` só é verificável quando resolvido contra o mapa pinado de corpus; não é prova standalone.
- A Stage6 herda `E-n/R-n` de Stage4/Stage5; não substitui o pacote de pesquisa nem valida efeitos runtime.

## Recomendação

**Não aprovar automaticamente.** A resposta Stage6 completa foi verificada nos recibos, mas `requirements.md` já existia como placeholder divergente e não foi sobrescrito pela regra solicitada. A Stage6 gerada é uma especificação documental com decisões de representação úteis, mas declara e mantém gaps bloqueadores (`G-21`..`G-24`). Não há contrato OpenAPI executável validado, não há status HTTP/body envelope completo, e não há autorização para Stage7/implementação.


## Correção de materialização e proveniência

Conferência direta posterior: requirements.md era apenas o placeholder de init, não uma versão experimental concorrente. Foi arquivado sem alterações em specs/api-contract-carddemo/requirements-initial-placeholder.md; requirements.md recebeu exatamente os bytes de scope-original.md, também coincidentes com parsed.text. SHA-256 da resposta/materialização: 753a60a5ee7b1fb6d94f6ab982afe415bc01adca040bb3d89e24ffc60342bba7. O hash 0e5d2063f232c500e94ff3513cb5a9a0640a82d16cc3bc2aa9cdbea33183f79d é do request serializado canonicamente, não da resposta. As referências anteriores ao hash 144750... identificam o placeholder, não o texto substantivo revisado. A revisão substantiva refere-se ao original gerado. G-21..G-24 permanecem abertos, sem aprovação. gate.review restaurado a null (não houve decisão humana). Nenhuma resposta do modelo foi corrigida ou regenerada.
