# Campaign Harness v3 — lifecycle bounded sintético

Status: qualificação sintética somente. Este diretório não implementa runners oficiais AWS, não carrega contratos AWS, não executa COBOL/API AWS e não faz chamadas de modelo.

## O que este núcleo entrega

- Replay HTTP serial de casos congelados, uma tentativa por caso, sem redirect e sem retry.
- Cliente HTTP real de baixo nível (`http.client`) preservando headers duplicados e ordem; body ausente, bytes vazios e JSON `{}` continuam distintos.
- Lifecycle explícito por aplicação via `PerApplicationHttpTarget` isolado em processo filho: `start`, `stop`, `terminate`, `kill` e `reap` com prazos explícitos.
- Timeout ou handler travado em alvo controlado só permite seguir para o próximo caso depois de processo reaped e `pid_alive_after_reap=false`; não há shutdown bloqueante em thread daemon.
- Se quietude não puder ser provada, o restante é abortado como `not_executed`; alvo estático após deadline permanece unprovable e não inicia o próximo caso.
- Reset por aplicação preservado: cada caso recebe `workdir` fresco; mutações ficam contidas na aplicação.
- Expectativas estruturais avaliadas separadamente do transporte: `completed` não significa `pass`; status inesperado vira `violation`; 500 documentado pode ser `pass`; checker não suportado é `inconclusive`, limite aceito.
- IDs de caso preservados nos registros, mas paths de aplicação são opacos/contidos; pacotes com symlink são recusados.
- Congelamento/load, união T4, ordem, proveniência e distinção de expectativas preservados.
- CLI fail-closed: nenhum label JSON libera campanha oficial; somente `--mode synthetic-qualification` é aceito.

## Limites explícitos

Não alegar a partir deste pacote:

- runner T1 completo: geração LLM, captura de pacote visível e adaptador de cenários ainda pendentes;
- runner T2 completo: adaptação do fuzzer a contratos AWS e fixtures oficiais ainda pendente;
- runner T3 completo: modelo MBT/referência independente e adaptador ainda pendentes;
- campanha T4 oficial: a união é qualificada em loopback local e precisa integração com agenda oficial, fixtures, APIs, cobertura e coleta;
- autorização AWS: labels como `approved_frozen` ou `approved_campaign_execution` continuam sem autoridade executável nesta CLI;
- interrupção cooperativa do handler: v3 prova quietude matando/reapando o processo alvo quando necessário, não finalização limpa do código de handler infinito;
- checker `unsupported` conclusivo: segue `inconclusive` por desenho.

## Arquivos

- `src/campaign_harness.py`: núcleo de dados, freeze/load, união T4, reset de recursos, lifecycle bounded por processo e replay HTTP.
- `campaign_harness_cli.py`: CLI intencionalmente sintética/fail-closed.
- `qualification_demo.py`: demonstração loopback sintética.
- `outside_in_probes.py`: cinco probes outside-in atualizados para isolamento por processo.
- `tests/test_campaign_harness.py`: 9 regressões sintéticas preservando HTTP bytes/headers/freeze/union/status/fresh-workdir/CLI.
- `tests/test_lifecycle_bounded.py`: novo negativo/verde de lifecycle bounded com handler infinito/lento, startup fail, stop fail, caso seguinte rápido, sem retry, sem vazamento de alvo.
- `../campaign-harness-review-v3/review_probes.py`: agregador de evidência v3.

## Evidência RED/GREEN

RED observado antes da correção em v3 copiado de v2:

```bash
python3 -m unittest tests/test_lifecycle_bounded.py -v
```

Resultado RED: handler infinito executado em subprocess do teste estourou timeout externo de 3s; lifecycle antigo não registrava `lifecycle`, continuava após quietude não provada em cenário estático e não aceitava prazos de stop/terminate/kill.

GREEN observado após a correção:

```bash
python3 -m unittest tests/test_campaign_harness.py tests/test_lifecycle_bounded.py -v
```

Resultado: 14 testes OK (9 regressões existentes + 5 lifecycle bounded), duração medida 5.330s nesta máquina.

Probes existentes:

```bash
python3 outside_in_probes.py --output /tmp/chv3-probes-fixed-1789478337
```

Resultado: `fixes_verified=5`, `probes_total=5`.

Agregador com novo negativo bounded:

```bash
python3 ../campaign-harness-review-v3/review_probes.py
```

A evidência é gravada em `../campaign-harness-review-v3/evidence-*` com stdout/stderr, JSON do handler travado, aplicações e hashes.

## Medição real de quietude bounded

Cada aplicação controlada registra em `applications.json`:

- `target_quiet`: booleano só verdadeiro quando o alvo foi parado e quietude foi provada;
- `lifecycle.pid`: PID do processo alvo;
- `lifecycle.stop_method`: `graceful`, `terminate` ou `kill`;
- `lifecycle.reaped`: processo filho coletado via `join`;
- `lifecycle.pid_alive_after_reap`: prova negativa por `os.kill(pid, 0)` após reap.

O próximo caso só inicia quando `target_quiet=True`. Se `target_quiet=False`, `abort_reason` marca os demais casos como `not_executed`.

## Interpretação dos totais

Os totais são calculados do replay sintético real. Eles contam ocorrências/aplicações, não diversidade de negócio AWS. T4 é dependente das suítes T1/T2/T3 e é reexecutado neste pacote para demonstrar reset e coleta, não para somar coberturas anteriores.
