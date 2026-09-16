# Campaign Harness v1 — núcleo pré-campanha sintético

Status: qualificação sintética somente. Este diretório não implementa runners oficiais AWS, não carrega contratos AWS, não executa COBOL/API AWS e não faz chamadas de modelo.

## O que este núcleo entrega

- Replay HTTP serial de casos congelados, uma tentativa por caso, sem redirect e sem retry.
- Congelamento de suíte por `suite_freeze_sha256`, com falha em adulteração posterior.
- Identidade conservadora de request: body ausente, body vazio (`Content-Length: 0`) e JSON `{}` são distintos.
- União T4 estável na ordem T1 → T2 → T3, preservando proveniência; estímulos iguais com expectativas distintas permanecem casos distintos.
- Reset por aplicação: cópia nova de pacote local, pins antes/depois e detecção de mutação sem contaminar próxima aplicação.
- Separação de deadlines/falhas de transporte de respostas HTTP documentadas como 500.
- CLI fail-closed: nenhum label JSON libera campanha oficial; somente `--mode synthetic-qualification` é aceito.

## Limites explícitos

Não alegar a partir deste pacote:

- runner T1 completo: geração LLM, captura de pacote visível e adaptador de cenários ainda pendentes;
- runner T2 completo: adaptação do fuzzer a contratos AWS e fixtures oficiais ainda pendente;
- runner T3 completo: modelo MBT/referência independente e adaptador ainda pendentes;
- campanha T4 oficial: a união é qualificada em loopback local e precisa integração com agenda oficial, fixtures, APIs, cobertura e coleta;
- autorização AWS: labels como `approved_frozen` ou `approved_campaign_execution` continuam sem autoridade executável nesta CLI.

## Arquivos

- `src/campaign_harness.py`: núcleo de dados, freeze/load, união T4, reset de recursos e replay HTTP.
- `campaign_harness_cli.py`: CLI intencionalmente sintética/fail-closed.
- `qualification_demo.py`: demonstração real com servidor HTTP loopback local.
- `tests/test_campaign_harness.py`: testes unitários/integrados sintéticos com HTTP real.
- `evidence/latest/`: evidência gerada pela última execução local da demonstração.

## Comandos verificados

A partir deste diretório:

```bash
python3 -m unittest tests/test_campaign_harness.py -v
python3 qualification_demo.py --output evidence/latest
python3 campaign_harness_cli.py --mode official-aws --config evidence/latest/report.json
```

Resultados esperados:

- testes: 6 testes `OK`;
- demo: cria `evidence/latest/report.json` e recibos de duas execuções T4 reexecutadas sobre HTTP local;
- CLI oficial: retorna código 2 e informa que campanha AWS oficial não está implementada.

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
