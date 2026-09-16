# Revisão delimitada — campaign-harness-v2

**Veredito delimitado: PARTIAL para o núcleo serial sintético.** As cinco correções v1 foram reproduzidas como verdes nos probes outside-in, mas há um bloqueio material novo: `PerApplicationHttpTarget.stop()` chama `HTTPServer.shutdown()` sem limite antes do `join(timeout=2)`. Em handler travado, o deadline do caso não limita a parada; o processo filho precisou ser morto por timeout externo de 3s.

Escopo: somente `campaign-harness-v2/` e HTTP sintético local. Não executei campanhas AWS, COBOL, contratos, oráculos ou quarentena. Não alterei `campaign-harness-v2/`. Saída nova exclusiva: `campaign-harness-review-v2/`.

## Execução real

- Testes existentes: **9/9 OK**  
  Comando: `python3 -m unittest tests/test_campaign_harness.py -v` em `campaign-harness-v2/`.
- Probes outside-in v2: **5/5 correções verificadas**  
  Comando: `python3 outside_in_probes.py --output .../campaign-harness-review-v2/evidence-20260915T130807Z/outside-in-probes`.
- Probe negativo bounded de shutdown travado: **FAIL material reproduzido**  
  Comando: subprocess sintético `shutdown_hang_child.py`, timeout externo 3s; resultado `timed_out_externally=true`, duração 3.005s.
- Probes semânticos adicionais: **OK mecânico** para cópias/freeze/union e classificação de checker sem suporte como `inconclusive`, não `pass`.
- Checagem de processos pendurados: nenhum processo correspondente a `campaign-harness`, `shutdown_hang_child` ou `HTTPServer` permaneceu após os probes.

## Matriz PASS/PARTIAL/FAIL

| Item revisado | Resultado | Evidência |
|---|---:|---|
| Headers duplicados/ordem no fio | PASS | Servidor recebeu `X-Dup: ["one", "two"]`; receipts preservaram headers. |
| Reset via workdir efetivo | PASS | Target controlado recebeu workdirs distintos e estado inicial `original\n` nas duas aplicações. |
| Quietude pós-timeout | PARTIAL/FAIL | Caso lento normal foi reaped antes do próximo request; porém handler travado bloqueou em `shutdown()` sem limite e só foi contido pelo timeout externo. |
| Classificação de expectativas/status | PASS | 500 inesperado => `expectation_result="violation"`; 500 documentado => `pass`; transporte continua separado de expectativa. |
| Paths de evidência/workdir | PASS | `case_id` malicioso preservado como dado, mas workdir opaco ficou contido em `applications/`. |
| Checker sem suporte fail-closed | PARTIAL | `jsonSchema` sem suporte vira `expectation_result="inconclusive"` e não `pass`; não aborta a execução nem marca violação. É fail-closed contra PASS, mas consumidores precisam tratar inconclusivo como não-aprovação. |
| Cópias/freeze/union | PASS | Cópia fresca bate pins e mutação da cópia não altera fonte; freeze rejeita tamper; union mantém ordem T1/T2 e proveniência/dedup esperadas. |

## Bloqueio material consolidado

`PerApplicationHttpTarget.stop()` contém:

```python
self._server.shutdown()
self._thread.join(timeout=2)
```

O limite de 2s só se aplica depois que `shutdown()` retorna. Em `HTTPServer` serial, se o handler continua preso depois do timeout do cliente, `shutdown()` aguarda o loop de `serve_forever` encerrar e pode bloquear indefinidamente. O probe filho com handler `time.sleep(60)` e `case.timeout_seconds=0.05` não terminou em 3s; isso invalida a alegação de deadline bounded para handler travado.

Não é cosmético: um único caso travado pode parar o runner local apesar de receipts/deadlines planejados. Para o escopo serial sintético, isso bloqueia tratar v2 como runner bounded até a parada do target também ter limite efetivo ou isolamento por processo com kill externo controlado.

## Observações de não-bloqueio

- A classificação `inconclusive` para checker sem suporte é aceitável como não-PASS, desde que relatórios/campanhas não a promovam a aprovação. Se a regra desejada for abortar ao encontrar checker sem suporte, v2 ainda não faz isso.
- Não encontrei regressão material em headers, paths, reset workdir efetivo, freeze/load, cópias ou union nos probes executados.

## Evidências principais

- `review.json` — relatório estruturado desta revisão.
- `evidence-20260915T130807Z/review_probes_result.json` — comandos, resultados e hashes dos artefatos.
- `evidence-20260915T130807Z/shutdown_hang_probe.json` — probe negativo bounded do shutdown travado.
- `evidence-20260915T130807Z/outside-in-probes/outside_in_probes.json` — 5 probes outside-in verdes.
- `evidence-20260915T130807Z/semantic_probes.stdout` — copy/freeze/union/checker sem suporte.
- `evidence-20260915T130807Z/unittest.stderr` — 9 unittests OK.
- `evidence-20260915T130807Z/process-check.txt` — checagem final sem processos pendurados.
