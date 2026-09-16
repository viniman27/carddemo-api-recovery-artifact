# Campaign Harness v2 — núcleo pré-campanha sintético

Status: qualificação sintética somente. Este diretório não implementa runners oficiais AWS, não carrega contratos AWS, não executa COBOL/API AWS e não faz chamadas de modelo.

## O que este núcleo entrega

- Replay HTTP serial de casos congelados, uma tentativa por caso, sem redirect e sem retry.
- Cliente HTTP real de baixo nível (`http.client`) preservando headers duplicados e ordem; body ausente, bytes vazios e JSON `{}` continuam distintos.
- Lifecycle explícito por aplicação via `PerApplicationHttpTarget`: servidor local iniciado contra o `workdir` fresco da aplicação, parado, fechado e `join`ado antes da próxima.
- Reset por aplicação comprovado no servidor demo: o handler lê/muta `state.txt` no `workdir`; a próxima aplicação vê novamente `original`.
- Timeout em alvo controlado exige parada/join/quietude antes de continuar; timeout em alvo estático não controlado aborta o restante como `not_executed` quando quietude não pode ser provada.
- Expectativas estruturais avaliadas separadamente do transporte: `completed` não significa `pass`; status inesperado vira `violation`; 500 documentado pode ser `pass`; checker não suportado é `inconclusive`, nunca sucesso.
- IDs de caso preservados nos registros, mas paths de aplicação são opacos/contidos; pacotes com symlink são recusados.
- Congelamento/load, união T4, ordem, proveniência e distinção de expectativas preservados.
- CLI fail-closed: nenhum label JSON libera campanha oficial; somente `--mode synthetic-qualification` é aceito.

## Limites explícitos

Não alegar a partir deste pacote:

- runner T1 completo: geração LLM, captura de pacote visível e adaptador de cenários ainda pendentes;
- runner T2 completo: adaptação do fuzzer a contratos AWS e fixtures oficiais ainda pendente;
- runner T3 completo: modelo MBT/referência independente e adaptador ainda pendentes;
- campanha T4 oficial: a união é qualificada em loopback local e precisa integração com agenda oficial, fixtures, APIs, cobertura e coleta;
- autorização AWS: labels como `approved_frozen` ou `approved_campaign_execution` continuam sem autoridade executável nesta CLI.

## Arquivos

- `src/campaign_harness.py`: núcleo de dados, freeze/load, união T4, reset de recursos, lifecycle por aplicação e replay HTTP.
- `campaign_harness_cli.py`: CLI intencionalmente sintética/fail-closed.
- `qualification_demo.py`: demonstração real com servidor HTTP loopback local controlado por aplicação.
- `outside_in_probes.py`: probes outside-in v2 que verificam os cinco defeitos encontrados na revisão v1.
- `tests/test_campaign_harness.py`: regressões sintéticas com HTTP real.
- `INTEGRATION_API.md`: contrato delimitado para futura integração.
- `evidence-20260915T130333Z/`: evidência nova RED/GREEN desta correção.

## Comandos verificados

A partir deste diretório:

```bash
python3 ../campaign-harness-review-v1/outside_in_probes.py --output evidence-20260915T130333Z/v1-red-probes
python3 -m unittest tests/test_campaign_harness.py -v
python3 outside_in_probes.py --output evidence-20260915T130333Z/v2-green-probes
python3 qualification_demo.py --output evidence-20260915T130333Z/demo-output
python3 campaign_harness_cli.py --mode official-aws --config ../current-pretest-state-v4.json
```

Resultados observados:

- v1 RED: `defects_reproduced=5`, `probes_total=5`.
- v2 testes: 9 testes `OK`.
- v2 probes: `fixes_verified=5`, `probes_total=5`.
- demo: 8 casos T4 por execução; em cada execução `attempted=8`, `completed=7`, `deadline_failures=1`, `expectation_inconclusive=1`, `http_failures=0`, `not_executed=0`.
- CLI oficial: retorno 2, mensagem `official AWS campaign execution is not implemented; this CLI accepts only synthetic-qualification`.

## Mapa de integração pendente

1. **Geração T1**: congelar prompt/pacote visível/modelo real autorizado, coletar cenários sem retry/fallback e adaptar cenários para requests públicos por contrato.
2. **Adaptador T2**: conectar a ferramenta OpenAPI qualificada aos contratos AWS congelados, preservar geração offline antes do HTTP e bloquear shrink/replay com efeitos.
3. **Adaptador T3**: receber referência/MBT independente aprovada, mapear transições para superfícies de cada braço e separar expectativas inconclusivas/não expressáveis.
4. **Agenda oficial de fixtures/reset**: substituir pacote local sintético por pacotes oficiais revisados, com bytes e pins físicos/lógicos aceitos.
5. **Runners por braço/API**: integrar zero-shot, few-shot e SDD sem fortalecer contratos nem usar saídas de um braço para reparar outro.
6. **Cobertura/coleta**: integrar denominadores GnuCOBOL/gcov, flush normal e coleta de stdout/stderr/artefatos por aplicação.
7. **Manifesto de liberação**: criar gate autenticado externo ao label JSON antes de qualquer célula AWS oficial.

## Interpretação dos totais

Os totais são calculados do replay sintético real. Eles contam ocorrências/aplicações, não diversidade de negócio AWS. T4 é dependente das suítes T1/T2/T3 e é reexecutado neste pacote para demonstrar reset e coleta, não para somar coberturas anteriores.
