# Pipeline SDD v3 — candidata para revisão

## Escopo correto

O foco atual é melhorar a pipeline e, depois de aprovada, aplicá-la ao recorte AWS CardDemo. Esse ciclo público NÃO é a Fase 2 da pesquisa. A Fase 2 usará outros códigos; tanto a pipeline quanto o fluxo poderão evoluir novamente até lá.

Esta pasta foi inicialmente criada como `pipeline-draft/` e renomeada para `pipeline-sdd-v3/` para não perpetuar a confusão de escopo. Nenhuma configuração global foi redirecionada.

## Estrutura

- `baseline/`: README, steering e settings originais da `.sdd-v2`, preservados.
- `pipeline/`: framework candidato v3; não contém specs históricas como respostas para novos casos.
- `provenance.json`: origem e hashes da base.
- `MELHORIAS.md`: evidência, mudança e aceite por item.
- `CHANGELOG.md`: estado efetivamente implementado.
- `QUALITY.md`: integridade versus qualidade de uso.
- `evidence/` e `tests/`: revisão e regressões do framework, fora das entradas de extração.

O framework continua document-first para os estágios 1–8 e agora inclui o estágio 9, `Implementation and Executable Qualification`, para adoção/qualificação executável de uma implementação após aprovação upstream. O estágio 9 exige proveniência explícita, execução nova e preservação de hashes 1–8; não é um runner automático de LLM nem o fluxo experimental completo.

## Verificações locais

    python3 verify_snapshot.py
    python3 -m unittest discover -s tests -v

Stage 9 AWS stage-only, quando os estágios 1–8 aprovados estão atuais, exige manifesto explícito de entrada e run novo:

    python3 pipeline/tools/stage9_qualify.py --cycle-root "../casos/aws-carddemo-cycle-v1" --manifest "../casos/E3-stage9-02-stage9-input.json" --run-id E3-stage9-02 --execute

A primeira verifica a base contra a origem e lista diferenças da candidata. A segunda testa ancoragem e atualização das revisões dos gates, sem invocar modelos, APIs ou COBOL. O Stage 9 copia apenas fontes/recursos pinados, constrói binários novos no run, executa HTTP local e gera pacote com `launch_stage9.py`; não copia um preflight isolado antigo. O guia do novo verificador está em `pipeline/tools/gates.md`; sua saída nunca concede aprovação humana.

Handoff operacional API ready for testing, sem campanha pronta:

    "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P2a/.venv/bin/python" ../casos/aws-carddemo-cycle-v1/sdd-runs/E3-stage9-handoff-01/independent_http_consumer.py

Critério aplicado do template Stage 9 seção 7: build/start a partir do pacote, contrato Stage6r3 original, três rotas HTTP, schemas, COBOL alcançado, reset de recursos no mesmo processo e falha fechada para request/recurso inadequado. Evidência: `../casos/aws-carddemo-cycle-v1/sdd-runs/E3-stage9-handoff-01/STAGE9_API_HANDOFF.md` e `independent-http-consumer-report.json`. Resultado técnico: `api_ready_for_testing=true`, `campaign_ready=false`, gate humano ainda pendente.

Gate complementar pós-Stage 9 para qualidade/cobertura de testes, sem virar Stage 10 nem aprovar T1–T4:

    python3 pipeline/tools/check_test_quality_gate.py path/to/test-quality-gate.json

Template e checklist: `pipeline/settings/templates/testing/test-quality-gate.md` e `test-quality-gate-manifest.json`. O verificador exige freeze prospectivo, denominador de cobertura conhecido, separação schema versus oráculo de negócio independente, reset por caso, regras T1–T4, mutações apenas como evidência de checker e lacunas de rastreabilidade separadas. Saída pronta significa pronta para revisão humana, não aprovação.

## Limites e retomada

A qualificação, os artefatos congelados e o COBOL não são editados. O próximo uso do framework exige um run separado com corpus e entradas autorizadas; nenhuma spec CardDemo foi produzida nesta revisão.

A referência de preparação AWS é `../casos/aws-carddemo-preparation/STATUS-ATUAL.md`; ela não substitui a extração. O corpus permitido deverá vir de `research-package.json`, não da árvore exploratória nem do suporte. Os dados e achados da preparação não entram silenciosamente nos prompts. A qualificação stage9 executada em `../casos/aws-carddemo-cycle-v1/sdd-runs/E3-stage9-01/` é técnica e estreita; não absorve T1–T4 nem concede aprovação independente.
