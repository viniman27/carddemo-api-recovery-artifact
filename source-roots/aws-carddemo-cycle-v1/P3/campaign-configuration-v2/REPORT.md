# P3 campaign configuration v2 — executable preparation only

Status: config atual consolidada; campanhas e suítes oficiais não iniciadas.

## Decidido e reaproveitado

- Escopo: 7 contratos, 21 operações, três braços (E1 zero-shot, E2 few-shot, E3 SDD AWS incluído).
- Ordem: contract replica → arm → T1/T2/T3/T4 → track → fixture → case.
- Reset: execução serial, novo workdir por aplicação e comparação de recursos efetivos.
- T1: 1 chamada/contrato, até 12 cenários/operação, sem retry/fallback/model switch.
- T2: Schemathesis 4.27.1, Hypothesis 6.168.0, seeds 104729/130363/155921, 100 exemplos/op/seed em 50 positivos + 50 negativos, sem transferir orçamento ocioso.
- T3: referência executável v4 existe com PASS delimitado para seleção de caminhos abstratos; mapeamento v2 é candidato e ainda depende da adaptação T3.
- T4: união T1→T2→T3, reexecução fresca, dependente, não réplica independente.

## T1

Modelo/provedor/transporte previamente usado em P1: `gpt-6-astra`, `openai-codex`, `https://chatgpt.com/backend-api/codex/responses`, SSE direto. Pin disponível: `P1/direct-transport/baseline-request.json`, `baseline-response.txt`, `results.json`, `baseline-parsed.json`. `temperature=0` e `max_output_tokens=64` foram rejeitados; seed não foi qualificada.

Pacote local já existe em `P3/pre-campaign-acceptance-package-v1/t1-outbound-payloads/` com 7 payloads `not_sent`. Antes de enviar será necessário confirmar com o usuário: autorização externa explícita para enviar os 7 payloads; uso do provedor/modelo/transporte acima sem temperature/max_output_tokens/seed; sem retry/fallback/switch; se quer ou não probe sintético fresco; aceite de custo/assinatura e leitura do returned model dos recibos.

## Fixtures

Fixtures referenciadas apenas como candidatas: `posting.candidate-v1-physical-v2`, `interest.candidate-v1-physical-v2`, `reporting.candidate-v1-physical-v2`, vindas de `P3/fixture-materialization-v2/package/manifest.json`. Não foram promovidas a oficiais e não carregam expected outputs.

## Pendências mínimas recomendadas

1. T3: adaptar/revisar `P3/t3-mapping-integration-v2/src/mapping_integration.py::map_enriched_model_to_suite` contra a configuração final.
2. T1: obter confirmação do usuário para envio externo; recomendar usar os 7 payloads existentes sem probe extra, salvo necessidade de revalidar disponibilidade do provedor.
3. Fixtures: revisão humana para promoção dos bytes candidatos, sem inferir oráculos.
4. Release de geração: só depois de checker verde + decisão T1 + adaptação T3.

## Arquivos

- `campaign-config-v2.json`: configuração executável/pinada.
- `verify_campaign_config.py`: verificador local de stale/tamper/autorização por label.
- `test_verify_campaign_config.py`: testes do verificador.
- `VERIFY-RESULT.json`: saída real do verificador.
