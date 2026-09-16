# Stage 7 r1 — feedback dirigido para aceite sólido

Veredito: **revisão estreita versionada necessária**. O r1 (`specs/adapter-behavior-carddemo/requirements.md`, SHA-256 `0125e68e65e38c703e89b0c1b843358da91a5281e20860fb7f59316d3286ecf4`) é conservador e não fabrica prova de execução, mas ainda deixa decisões documentais demais dentro de G-25..G-31.

## Objetivo da r2

Produzir uma revisão Stage 7 que defina responsabilidades e registros de evidência internos suficientes para guiar Stage 8/implementação futura, sem comandos, sem código, sem execução COBOL, sem novo endpoint/campo público e sem alterar o contrato Stage 6 r3.

## Fechamentos mínimos exigidos

1. **Atribuição por invocação.** Definir que cada chamada observável precisa de um registro interno com track, invocation id interno, recurso(s) vinculados, owner/preparação, janela de validade, canal de saída e relação com envelope. Isso não deve virar schema público.
2. **Captura e vazio positivo.** Distinguir explicitamente: saída observada vazia, captura zero-length inconclusiva, captura truncada, captura falha, saída stale e saída indisponível. Só observação positiva pode gerar `availability: "available", items: []`.
3. **Setup/resource identity.** Registrar responsabilidade por identidade de instância e preparação de recursos sem inventar API de upload, selector, reset, readiness ou job scheduling.
4. **Protocolo de observação como proposta, não fato.** Especificar precondições/evidence records esperados; não afirmar que algum mecanismo já existe ou funcionou.
5. **Conversões fiéis.** Exigir matriz origem física -> campo representado com largura, sinal, padding, display/truncamento e perda conhecida. Proibir trim/coerção silenciosa ou descarte de registro por valor desconhecido.
6. **Falha técnica conhecida.** Definir critério evidencial mínimo na fronteira de resposta. Não assumir comportamento universal de `CEE3ABD`, exit status, console ou file status; manter precedência de 500 quando a falha for conhecida.
7. **Estado e repetição.** Separar estado local da invocação, estado persistente e reset/isolamento. Reinício não é reset; repetição/idempotência continuam não prometidas.
8. **EOF, ordem e multiplicidade.** Para posting/interest/reporting, exigir preservação de ordem e duplicatas por canal/records observados; EOF não vira sinal HTTP; relatório vazio observado não é relatório completo vazio.
9. **Checklist final útil.** Substituir itens finais “unchecked” por matriz com três estados: fechado documentalmente, bloqueado por execução posterior, ou exige revisão upstream.

## Não fazer na r2

- Não mudar `{}` requests, rotas, statuses, schemas públicos ou `available[]` semantics de Stage 6 r3.
- Não adicionar idempotency key, resource id, readiness, reset, retry, status resource, dataset selector ou provisioning público.
- Não transformar 109 em rejeição; não inserir final flush de interest; não reparar reporting; não reconstruir totais/descrições; não impor `minItems: 1`.
- Não exigir evidência runtime para escolhas documentais; não declarar prova runtime inexistente.
- Não empurrar esses critérios para Stage 8 como se fossem detalhe de implementação. Stage 8 deve receber o protocolo, não criá-lo.

## Critérios de aceite da r2

| Critério | Responsável no texto r2 | Evidência aceita agora |
|---|---|---|
| Stage 6 r3 preservado | Seção de autoridade/contrato | Tabela que aponta mudanças nulas de contrato público |
| G-25 fechado documentalmente | Setup/invocation record | Campos internos de evidência e precondições, sem API nova |
| G-26 fechado documentalmente | Observation/capture record | Categorias de captura e regra para `available`/`unavailable` |
| G-27 fechado documentalmente | Conversion record | Matriz campo-a-campo e política de perda explícita |
| G-28 parcialmente fechado | Failure boundary record | Critério de “known”, deixando comportamento real para execução |
| G-29 parcialmente fechado | State lifecycle record | Estado por invocação/recurso, reset desconhecido quando não provado |
| G-30 parcialmente fechado | Reporting observation record | EOF/order/multiplicity e limitações sem total inventado |
| G-31 fechado externamente | Human review | Autorização externa com hash exato da r2 |

## Quando a r2 deve parar e pedir upstream

Se a correção exigir expor campos públicos novos, mudar status HTTP, mudar `available[]`, alterar request `{}`, prometer reset/idempotência, converter 109 em erro/rejeição, ou reparar finalização/totalização legacy, isso não é Stage 7: é alteração de Stage 6/5 e precisa de gate upstream.

## Recomendação final

Gerar r2 estreita do Stage 7 com os registros/protocolos acima. Aceite sólido deve ser para **documentary adapter behavior**, com obrigações empíricas residuais explícitas para execução posterior, não para funcionamento runtime já provado.
