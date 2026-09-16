# Revisão outside-in — campaign-harness-v1

**Veredito delimitado: FAIL para o núcleo serial sintético antes de integração.**

Escopo: `campaign-harness-v1/` em P3. Não executei campanha AWS, COBOL, contratos, dados/oráculos/quarentena. Saída nova: `evidence-20260915T125017Z/`, não `evidence/latest`.

## Execução real

- Testes existentes: **6/6 OK** (`python3 -m unittest tests/test_campaign_harness.py -v`).
- Demo HTTP loopback real: **12 chamadas observadas**, T4 com **6 casos**, duas reexecuções com totais `planned=6`, `attempted=6`, `completed=5`, `deadline_failures=1`, `transport_failures=0`, `http_failures=0` em cada execução.
- CLI oficial: exit **2** para `--mode official-aws`, fail-closed.
- Probes outside-in adicionais: **5 probes**, **5 defeitos reproduzidos**.

## Causas-raiz consolidadas

1. **O estímulo congelado não é necessariamente o estímulo enviado.**
   - Reprodução: `duplicate_headers_wire_collapse` pediu `X-Dup: one` e `X-Dup: two`; o servidor recebeu só `['two']`.
   - Causa: `_send_once` converte `req.headers` para `dict`, perdendo duplicatas e ordem antes do fio.
   - Consequência experimental: identidade/dedupe podem distinguir casos que a aplicação recebe como iguais, ou o inverso para endpoints sensíveis a headers repetidos.

2. **Reset de arquivo não está acoplado à aplicação HTTP.**
   - Reprodução: `reset_copy_not_bound_to_service_state` mostrou pins frescos em todas as aplicações, mas o serviço leu estado fixo mutado: segunda chamada começou com `original+mutated`.
   - Causa: `replay_suite` cria `workdir` por caso, mas não passa esse diretório ao serviço nem reinicia/configura alvo por aplicação.
   - Consequência experimental: a evidência de cópia fresca pode ser sem efeito sobre o backend real; vazamento de estado entre aplicações pode ser contabilizado como comportamento do caso atual.

3. **Deadline não isola a próxima aplicação em alvo serial.**
   - Reprodução: `deadline_cascade_on_serial_target` executou `/slow` com timeout curto seguido de `/fast`; totais reais: `attempted=2`, `completed=0`, `deadline_failures=2`; o handler registrou apenas `/slow`.
   - Causa: após timeout, o harness fecha a conexão e segue imediatamente; se o serviço ainda está ocupado/processando, o próximo request pode expirar sem ser aplicado.
   - Consequência experimental: falhas deixam de ser independentes por aplicação e denominadores/taxas podem imputar ao segundo caso uma falha causada pelo primeiro.

4. **Expectativas não são aplicadas na classificação; 500 inesperado vira sucesso operacional.**
   - Reprodução: `unexpected_500_not_classified_against_expectation` usou expectation `status: [200]`; servidor respondeu 500; totais: `completed=1`, `http_failures=0`.
   - Causa: `replay_suite` registra status/bytes, mas nunca avalia `case.expectation.checks`; `http_failures` não é incrementado para status fora do esperado.
   - Consequência experimental: aderência contratual e totais de sucesso podem ser inflados; a regra correta “500 documentado não é falha automática” virou “qualquer 500 é completed”.

5. **IDs entram em paths de evidência sem sanitização suficiente.**
   - Reprodução: `case_id_path_traversal_workdir_escape` com `case_id='x/../../escaped-case'` gravou workdir resolvido fora de `applications/`: `.../path_traversal_run/escaped-case`.
   - Causa: `workdir = output_dir / "applications" / f"{index:04d}-{case.case_id}"` aceita separadores e `..`.
   - Consequência experimental: evidências podem sair da árvore esperada, colidir com outros artefatos ou mascarar contagens por aplicação.

## Controles que passaram, mas não anulam o FAIL

- Freeze/load detecta adulteração de JSON congelado.
- Ausência de body, body vazio e JSON `{}` são distintos no teste existente e no demo.
- União T4 manteve ordem e proveniência no cenário positivo.
- A demo não observou retry/redirect automático; isso ainda precisa permanecer explícito na integração.

## Evidências

- `review.json` — relatório estruturado com contagens e hashes.
- `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-harness-review-v1/evidence-20260915T125017Z/unittest.stderr` — saída dos 6 testes OK.
- `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-harness-review-v1/evidence-20260915T125017Z/demo-output/report.json` — demo HTTP real.
- `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-harness-review-v1/evidence-20260915T125017Z/probes-output-v2/outside_in_probes.json` — reproduções outside-in.

## Conclusão

O núcleo é útil como protótipo sintético, mas **não deve ser integrado como runner comum ainda**. Os bloqueadores não são cosméticos: afetam identidade do estímulo, isolamento/reset, independência serial após deadline, classificação de expectativas e integridade da árvore de evidências.
