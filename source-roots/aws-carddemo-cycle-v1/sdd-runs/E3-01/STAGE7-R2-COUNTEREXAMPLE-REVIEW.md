# Stage 7 r2 Counterexample Review — E3-01

## Veredito

**Aceitar de forma estreita como artefato documental Stage 7 r2; não autoaprovar.** A revisão r2 fecha os bloqueios de desenho documental identificados em r1 sem introduzir nova superfície pública aparente. O gate humano G-31 permanece pendente.

## Evidência mecânica

- `requirements.md` r2 foi materializado exatamente de `prepared/adapter-behavior-carddemo-r2/execution/scope-original.md`.
- SHA da resposta/texto original: `b53c471116dfa0c3831fc810964bddca3eb1fa0d3b8e7d459181ba71e54b3d8f`.
- SHA do request separado: `6968b20fb88aab6e082fcced34f018893c7ccd755018ff443cb6eba39d998c19`.
- Modelo/status: `gpt-6-astra` / `completed`.
- `tools: []`, `previous_response_id: null`, `store: false` no parsed.
- Arquivo de verificação: `specs/adapter-behavior-carddemo-r2/stage7-r2-verification.json`.

## Critérios de feedback r1/r2

Resultado programático/semântico dos critérios: `10/10` atendidos.

1. **Campos/owners/precondições de registros internos** — atendido. A r2 define `INV`, `RES`, `CAP`, `CONV`, `FAIL`, `STATE`, `RESP`; `RES` inclui owner fornecedor e prerequisites declarados. Isso é escolha documental, não prova de execução.
2. **Atribuição de invocação e captura stale** — atendido. `CAP` exige invocation/resource links e freshness; stale é conteúdo não corrente retido internamente.
3. **Zero-length vs observed empty** — atendido. Zero byte não vira output vazio; vazio positivo exige observação atribuível.
4. **Incompletude/truncation sem perda silenciosa** — atendido. Conteúdo conhecido truncado/danificado não pode ser apagado para produzir array vazio.
5. **Conversões físico→representado** — atendido. `CONV` exige declaração física, span bruto, encoding/sign/framing, largura/padding observados, valor, perda conhecida e representabilidade.
6. **Known failure sem semântica fabricada de CEE3ABD** — atendido. `CEE3ABD` aparece como call site/contexto; falha técnica conhecida exige evento atribuível dentro da fronteira de resposta.
7. **Estado local vs persistente/reset** — atendido. `STATE` separa estado local/persistente, preparação, lifetime, reset/isolation e efeitos tentados/observados/duráveis.
8. **EOF/ordem/multiplicidade/reason 109** — atendido. EOF não é inventado como entrada pública; ordem/duplicatas são retidas; reason 109 não é tratado como rejeição preliminar.
9. **Sem nova telemetry/fields/statuses e sem regressão minItems:1** — atendido. A r2 declara não criar schemas públicos; preserva 200/400/500/503 e afirma `No minItems: 1 is introduced`.
10. **G-31 humano pendente** — atendido. A r2 afirma que G-31 permanece aprovação humana externa e que não há autorização de implementação.

## Auditorias programáticas

- Referências `R-1..R-20`: `True`; contagens por regra em JSON.
- C-clauses em r2: `C-1, C-2, C-3, C-4, C-5, C-6, C-7, C-8, C-9, C-10, C-11, C-12, C-13, C-14` (`14` IDs distintos; contrato tem `14`).
- D-definitions em r2: `D-3, D-5, D-7, D-8, D-10, D-11, D-12, D-14, D-15, D-16, D-17` (`11` IDs distintos; contrato tem `16`; não referenciadas nominalmente em r2: `D-2, D-4, D-6, D-9, D-13`).
- Gaps em r2: `G-21, G-24, G-25, G-26, G-27, G-28, G-29, G-30, G-31`.
- Anchor audit: `13` anchors detectados; fora de bounds: `0`. Escopo exato e amostras estão no JSON.

## Comparação r1→r2

Mudanças relevantes são direcionadas aos bloqueios r1: registros internos, captura/observabilidade, conversão, failure predicate e estado. Não foi detectada troca de operações públicas (`POST /posting`, `/interest`, `/reporting`), nem criação de novo status público; a revisão explicita que não há novos schemas públicos. Contagens de termos públicos r1/r2 estão em `r1_r2_public_term_counts`.

## Fechamentos vs resíduos

### Escolhas documentais fechadas

- Responsabilidades internas e registros de evidência especificados.
- Distinções de captura vazia/zero/truncada/stale especificadas.
- Conversão campo-a-campo e perdas conhecidas especificadas.
- Failure predicate bounded sem atribuir semântica fabricada a `CEE3ABD`.
- Estado/reset/persistência mantidos como obrigação evidencial, não garantia.

### Resíduos empíricos

- Nenhum binding runtime, captura real, disponibilidade de recurso, reset/isolation ou efeito durável foi demonstrado.
- Nenhum registro INV/RES/CAP/CONV/FAIL/STATE/RESP populado foi observado.
- Nenhuma observação real de saída vazia foi certificada.

### Design essencial ainda ausente

Nenhum bloqueio essencial novo encontrado para o nível documental Stage 7 r2. O que resta é empírico/humano: G-31 e futura evidência autorizada, não autoaprovação.

## Recomendação

**Aceitar r2 como correção documental estreita e preservar `ready_for_implementation: false`.** Se o avaliador quiser exigir runtime/provas populadas agora, isso deve ser formulado como novo escopo empírico, não como falha documental da r2.
