# T2 offline preparation v2 — ponte candidata local

Status: candidata local, não congelada e não oficial. Nenhuma rede, suíte oficial ou campanha AWS foi executada.

## Entrega

- `src/t2_offline_bridge.py`: ponte T2 offline que valida a configuração corrente, constrói plano dry-run, gera requests Schemathesis a partir de fixtures OpenAPI sintéticas, importa via `unified-preflight-v3.import_t2_frozen_requests` e congela/carrega via `campaign-harness-v3`.
- `t2_offline_bridge_cli.py`: CLI utilizável.
- `candidate-config.json`: configuração candidata atualizada para T2 offline, com 7 contratos totais/21 operações, seeds/budgets/reset/erros/união e blockers explícitos.
- `tests/test_t2_offline_bridge.py`: testes TDD da ponte, incluindo negativos.

## Comandos

Dry-run seguro, sem geração:

```bash
cd "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1"
P3/.venv-fuzz-preflight/bin/python P3/t2-offline-preparation-v2/t2_offline_bridge_cli.py \
  --output-dir P3/t2-offline-preparation-v2/evidence-dry-run \
  --dry-run
```

Exercício sintético offline, não oficial:

```bash
cd "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1"
P3/.venv-fuzz-preflight/bin/python P3/t2-offline-preparation-v2/t2_offline_bridge_cli.py \
  --output-dir P3/t2-offline-preparation-v2/evidence-synthetic-aws-fixture-small \
  --generate-synthetic \
  --max-examples-per-direction 1 \
  --seeds 104729
```

Para planejar o orçamento candidato completo sem executar campanha, manter `--dry-run`; o default candidato registrado é 50 positivos + 50 negativos por operação por seed, seeds `104729,130363,155921`, sem transferência, replay, retries ou shrink/reprodução com efeito.

## Evidência real desta entrega

- RED inicial: `P3/.venv-fuzz-preflight/bin/python -m unittest P3/t2-offline-preparation-v2/tests/test_t2_offline_bridge.py -v` falhou por `ModuleNotFoundError: No module named 't2_offline_bridge'` antes da implementação.
- RED incremental: teste de CLI `--generate-synthetic` falhou porque a geração recusava o diretório já contendo `plan.json`; corrigido para permitir somente esse artefato prévio.
- GREEN final: `P3/.venv-fuzz-preflight/bin/python P3/t2-offline-preparation-v2/tests/test_t2_offline_bridge.py -v` → 6 testes OK.
- Dry-run CLI: `ok=true`, `officialCampaign=false`, 7 contratos, 21 operações.
- Exercício sintético CLI: `ok=true`, `officialCampaign=false`, 42 ocorrências (`21 ops × 1 seed × 2 direções`), `networkCallsDuringGeneration=0`.
- Config corrente: `python3 verify_campaign_config.py campaign-config-v2.json` → `ok=true`, 7 contratos, 21 operações, `official_campaigns_started=false`, `provider_calls_allowed_by_config=false`, 7 payloads T1 não enviados, 29 fontes checadas, 3 fixtures candidatas não oficiais.
- Ferramentas: Schemathesis 4.27.1, Hypothesis 6.168.0; P2a jsonschema 4.26.0 confirmado.

## Limites preservados

- Não gerou suíte oficial AWS T2/freeze nem campanha.
- Não chamou provedor, rede, T1 probe ou APIs COBOL.
- `candidate-config.json` não promove fixtures/oráculos, não altera `main study/contracts/COBOL/APIs` e não edita a configuração v2 histórica.
- Ocorrências geradas são contagem operacional, não diversidade de negócio; repetição de `{}`/IDs técnicos não vira diversidade.
- T1 continua bloqueado por consentimento específico externo.
- T3 v2 permanece explicitamente unbound; os pins atuais preservados são `t3-campaign-adapter-v3 + sdd-external-selection-v1 + substantive-review-v1`.
- T4 permanece bloqueado até existirem T1/T2/T3 oficiais congeladas, e será união dependente, não réplica estatística independente.
