# Procedimento executável de promoção/freeze T1-T4 — preparação local v1

Status: procedimento, não execução. Não rode comandos marcados como PROMOÇÃO sem autorização humana explícita. Este pacote não contém suítes oficiais congeladas.

## 0. Base

```bash
cd "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1"
```

## 1. Verificação local obrigatória antes de qualquer promoção

```bash
cd "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-configuration-v2"
python3 verify_campaign_config.py campaign-config-v2.json
```

Saída verificada neste pacote: `ok=true`, 7 contratos, 21 operações, `official_campaigns_started=false`, `provider_calls_allowed_by_config=false`, 7 payloads T1 `not_sent`, 3 fixtures candidatas não oficiais.

```bash
cd "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-harness-v3"
python3 -m unittest tests/test_campaign_harness.py tests/test_lifecycle_bounded.py -v
```

Saída verificada neste pacote: 14 testes OK.

```bash
cd "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1"
P2a/.venv/bin/python -c 'import jsonschema,sys; print("python",sys.executable); print("jsonschema",jsonschema.__version__)'
```

Saída verificada: Python P2a e jsonschema 4.26.0.

```bash
cd "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3"
.venv-fuzz-preflight/bin/python -c 'from importlib.metadata import version; import sys; print("python",sys.executable); [print(p, version(p)) for p in ["schemathesis","hypothesis"]]'
```

Saída verificada: Schemathesis 4.27.1, Hypothesis 6.168.0.

## 2. T1 — bloqueado antes de envio externo

Pré-condições materiais:
- autorização humana explícita para enviar os 7 payloads existentes;
- aceitar provedor/modelo/transporte de `campaign-config-v2.json`;
- preservar recibos SSE e returned model;
- sem retry, fallback ou model switch.

Payloads locais já existem em:

```text
<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/pre-campaign-acceptance-package-v1/t1-outbound-payloads
```

Não há comando oficial existente para envio T1: `t1_send_runner.py` está ausente por desenho. Logo T1 não pode ser promovido por este pacote.

## 3. T2 — preparação local independente

Config candidata: Schemathesis 4.27.1, Hypothesis 6.168.0, seeds `104729`, `130363`, `155921`, 100 exemplos/operação/seed separados em 50 positivos + 50 negativos, sem replay durante geração e sem transferência de orçamento ocioso.

Comandos existentes relevantes já inspecionados:

```text
<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/suite-generation-preflight-v1/src/suite_generation.py :: generate_t2_schemathesis_suite, import_t2_frozen_suite
<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/unified-preflight-v3/src/suite_adapters.py :: import_t2_frozen_requests
<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-harness-v3/src/campaign_harness.py :: freeze_suite, load_frozen_suite, replay_suite, UnionBuilder
```

Limite material: só há qualificação sintética/preflight; não há ainda importador/gerador T2 AWS oficial executado para os 7 contratos × 21 operações. Não promover T2 sem gerar offline os requests oficiais em pacote novo autorizado, congelar os bytes e reimportar sem replay extra.

## 4. T3 — bloqueado por revisão/adaptação paralela

Não promover T3 neste pacote. A configuração aponta `t3-mapping-integration-v2` como candidata; falta adaptar/revisar contra a configuração final e autoridade independente.

## 5. T4 — união e reexecução, não réplica

Depois — e somente depois — de T1, T2 e T3 oficiais existirem como suítes congeladas verificadas:
1. carregar T1/T2/T3 congeladas com `load_frozen_suite`;
2. construir união com `UnionBuilder().build([t1, t2, t3])` preservando ordem T1→T2→T3 e ledger;
3. congelar T4 com `freeze_suite`;
4. reexecutar T4 fresca com reset por aplicação/workdir;
5. registrar T4 como dependente das constituintes, não como réplica estatística independente.

Não usar a união sintética ou smoke (`UNION-QUALIFICATION-NOT-T4`) como T4 oficial.
