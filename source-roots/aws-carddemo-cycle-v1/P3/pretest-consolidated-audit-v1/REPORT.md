# Auditoria consolidada outside-in — prontidão pré-teste P3

Status técnico: **NÃO PRONTO PARA CAMPANHA**. Há preparo qualificado suficiente para parar retrabalho em smokes nominais, mas o caminho executável T1–T4/freeze/fixtures/mappings/medição ainda não está integrado nem congelado.

Escopo: leitura de estado/documentos P3, inventário de artefatos recentes e inspeção de código efetivo. Não li oráculos/expected outputs/quarentena e não executei campanhas. Testes executados foram unitários/sintéticos/read-only ou em diretório desta auditoria.

## Decisão curta

- **Frozen atual:** cadeia documental SDD aprovada; direção D1–D8 selecionada sob autorização do pesquisador; API SDD/P2b e algumas fachadas têm evidência técnica; referência MBT v4 tem PASS limitado para seleção de caminhos abstratos; fixture materialization v2 tem PASS técnico de bytes/reset; Schemathesis está qualificado só em loopback sintético; cobertura reconciliada é correção de relatório existente, não cobertura oficial.
- **Candidate/preparatório:** campaign-harness-v3, suite-adapters-preflight-v1, api-harness-integration-v1, fixture candidates/materialization, coverage candidate/reconciliation. São úteis, mas não formam um runner oficial completo.
- **Stale/histórico:** `PRETEST-FREEZE-DRAFT` e seu manifesto são rascunho antigo; coverage candidate original tem summaries inválidos; campaign-harness-v1/v2 e reviews v1/v2 são superseded; reference v1/v2/v3 são histórico/antecedente; integration-v1 inclui cópia few-shot antecedente ao patch pai.
- **Bloqueio principal:** não falta “perfeição semântica” da API. Faltam freeze concreto, mapeamento/aplicabilidade, runner oficial integrado e medição admissível.

## Checklist material PASS/PARTIAL/FAIL

| Item | Status | Evidência | Interpretação |
|---|---:|---|---|
| Estado corrente reconhece bloqueio material, não permissão rotineira | PASS | `STATUS-FLUXO.md:3-15`; `P3/READINESS-DECISION.md:1-13,46-54`; `current-pretest-state-v4.json:43-52` | Não pedir nova rotina; continuar fechamento material. |
| Pins atuais do estado v4 | PASS | `pin-checks.json`: 5/5 artefatos `current-pretest-state-v4.artifacts` batem | Estado v4 é pin corrente para decisão; não usar draft antigo como frescor. |
| `pretest-freeze-draft-manifest` fresco | PARTIAL/STALE | `pin-checks.json`: `P2b/p2b_binding.py` e `P2b/tests/test_p2b_contract.py` divergem dos hashes declarados | Manifesto é histórico/draft, não pacote final de freeze. |
| Referência MBT v4 | PARTIAL | `REFERENCE-V4-ACCEPTANCE-SCOPE.md:1-18`; `reference-independent-review-v4/REVIEW.md:3-12,50-72` | PASS limitado a seleção de caminhos abstratos; não oráculo completo/campanha. |
| Fixtures/materialização técnica | PARTIAL | `fixture-materialization-review-v2/REVIEW.md:17-27`; `FIXTURE-INTEGRATION-V2.md:99-101` | Bytes/reset/famílias técnicas avançaram; não oficializa fixtures nem corrige lacunas de mapeamento/reporting/argumento de juros. |
| API/harness integration smoke real | PARTIAL | `api-harness-integration-v1/integration-report.json`: 9 planejados, 9 HTTP, 8 schema/doc500 válidos, 8 reached COBOL; E2 reporting reached_cobol=false | Integração técnica existe, mas não é runner T1–T4 e tem falha material em um braço/caso. |
| campaign-harness-v3 como núcleo sintético | PARTIAL | `campaign-harness-v3/README.md:1-28`; testes desta auditoria 14 OK em `test-run.log:1-20` | Classe/núcleo qualificado sinteticamente, mas CLI ainda fail-closed sem runner oficial. |
| harness-v3 realmente usado pela integration-v1 | FAIL | `api-harness-integration-v1/src/api_harness_integration.py` não importa `campaign_harness`; `api_harness_integration.py:95-147,161-283` define checker/server próprios; `inventory.json` sem fato de import v3 | Integration-v1 não usa harness-v3; é integração separada com classes próprias. |
| adapters PYTHONPATH para harness-v3 | FAIL | `suite-adapters-preflight-v1/suite_adapters_cli.py:9-13`; `tests/test_suite_adapters.py:8-12`; `inventory.json` registra `campaign-harness-v2` linhas 11/10 | Adapters estão hardcoded para v2, não v3. Risco de validar contra núcleo antigo. |
| parser gcov corrigido no runner futuro | FAIL/PARTIAL | `coverage-report-reconciliation-v1/reconcile_coverage.py:1-7,61-67,215-230,288-326`; `inventory.json` mostra parser só em reconciliation; `coverage-candidate-check-v2/run_candidate_coverage_check.py` é fonte stale pinada | Parser corrigido é pós-processamento/reconciliação de artefatos existentes; não está integrado ao runner de medição futuro. |
| Coverage original summaries | FAIL/STALE | `coverage-reconciliation-report.json:15-27,157-170,287-326`; testes 5 OK em `test-run.log:55-65` | Summary antigo mistura escopos e é inválido para decisão; reconciliação limita escopo ao main generated C. |
| suite adapters preflight | PARTIAL | `adapter-preflight-report.json:48-66,100-147`; testes 5 OK em `test-run.log:21-31` | Importa/freeze/union sintético; não gera T1/T2/T3 e bloqueia T3 abstrato sem mapping. Além disso usa harness-v2. |
| api-harness unit env | PARTIAL | Python do sistema falhou sem jsonschema (`test-run.log:32-54`); P2a venv passou 3 testes (`api-harness-p2a-venv-test.log:1-9`) | Dependência não é autossuficiente no ambiente padrão; pinar venv/requirements do runner. |
| Few-shot parent closure independente | PARTIAL/QUALIFIED | `fewshot-parent-closure-v1/REPORT.md:1-24,42-54`; contexto do usuário: review-v3 do harness feito pelo autor não independente; integration-v1 antecede patch pai | Fechamento técnico útil; não tratar como revisão independente global nem como prova de integration-v1 atualizada. |
| Official execution gate | FAIL | `campaign-harness-v3/campaign_harness_cli.py:23-35`; `campaign-harness-v3/README.md:18-28`; `READINESS-DECISION.md:46-53` | Não existe CLI/runner oficial AWS; labels JSON não autorizam execução. |

## Código efetivo do caminho de execução

### Harness-v3 vs integration-v1

- `campaign-harness-v3/src/campaign_harness.py` contém o núcleo `Suite`, `UnionBuilder`, `PerApplicationHttpTarget`, `replay_suite` e freeze/load.
- `api-harness-integration-v1/src/api_harness_integration.py` **não importa** `campaign_harness`; define `ContractChecker`, `HarnessCase`, `PosixSpawnServer`, `send_json` e utilitários próprios.
- Consequência: o smoke real de integration-v1 não exercita o lifecycle/freeze/union do harness-v3. Ele prova outra coisa: spawn HTTP + contratos + fixtures técnicas + reach COBOL em um script separado.

### Suite adapters

- `suite_adapters_cli.py` injeta `ROOT.parent / "campaign-harness-v2" / "src"` no `sys.path` e importa `UnionBuilder`, `freeze_suite`, `load_frozen_suite` dali.
- `tests/test_suite_adapters.py` repete o mesmo path v2.
- Consequência: qualquer PASS dos adapters hoje qualifica import/freeze/union contra **v2**, não contra v3. Deve ser rebatido antes de acoplar adapters ao runner.

### Parser de cobertura

- `coverage-report-reconciliation-v1/reconcile_coverage.py` corrige o parser por `File` unit e ignora aggregate misto; os testes confirmam isso.
- Mas a função corrigida é usada na reconciliação que lê `coverage-candidate-check-v2` e `.gcov` existentes. Ela não substitui automaticamente o parser do runner de medição/campanha.
- Consequência: coverage original summaries são stale; um runner futuro precisa incorporar essa seleção/parsing ou chamar esse reconciliador como etapa oficial versionada.

## Frozen vs candidate

### Frozen/aceito com escopo limitado

- `sdd-runs/E3-01/reviews/stage-7-r2-authorization.json` e `stage-8-authorization.json`: documental, não runtime.
- `P3/experimental-direction-delegated-v1.json` + `READINESS-DECISION.md`: direção operacional selecionada, sem iniciar campanhas.
- `P3/reference-executable-v4/` + `reference-independent-review-v4/`: referência executável limitada para caminhos abstratos; não equivalência COBOL completa.
- `P3/readiness-revision-20260915T105955Z/`: fuzzer sintético qualificado; não T2 AWS.
- `P3/fixture-materialization-v2/` + review-v2: pacote técnico/materialização candidata, não fixture oficial.

### Candidate/preparatório

- `P3/campaign-harness-v3/`: núcleo sintético qualificado, sem official runner.
- `P3/suite-adapters-preflight-v1/`: adapters sintéticos, mas presos a harness-v2.
- `P3/api-harness-integration-v1/`: smoke real técnico de APIs/fixtures, separado do harness-v3.
- `P3/coverage-report-reconciliation-v1/`: reconciliação correta de artefatos existentes, não medição oficial.
- `P3/fixture-candidates-v1/`: candidatos/famílias; ainda precisa oficialização/aplicabilidade.

### Histórico/stale/superseded

- `P3/PRETEST-FREEZE-DRAFT.md` e `pretest-freeze-draft-manifest.json`: rascunho útil, pins parcialmente stale.
- `P3/coverage-candidate-check-v2/candidate-coverage-report.json`: fonte stale para summaries; útil só com reconciliação.
- `P3/campaign-harness-v1/`, `campaign-harness-v2/`, `campaign-harness-review-v1/v2`: antecedentes.
- `P3/reference-independent-review-v1/v2/v3` e `reference-executable-v3`: antecedentes para v4; v3 era PARTIAL.

## Bloqueios restantes para runner completo

1. **Unificar núcleo:** apontar suite adapters e qualquer integração futura para `campaign-harness-v3` ou versionar explicitamente que v2 ainda é alvo. Hoje há desalinhamento real.
2. **Freeze manifesto final:** gerar um manifesto concreto com artefatos atuais, hashes, venv/requirements, fixtures, contratos, runner, budgets/seeds/order e política de falha. Não reciclar `pretest-freeze-draft-manifest` como freeze.
3. **Fixtures oficiais/aplicabilidade:** oficializar bytes, reset, pré-condições e mapping por operação/contrato/trilha. Não ler o novo `applicability-mapping-v1` nesta auditoria; tratá-lo como entrada pendente a ser incorporada quando liberado.
4. **T1:** definir pacote outbound/modelo/parâmetros, congelar respostas preservadas e adapter de cenários. Sem retry/reparo manual.
5. **T2:** ligar Schemathesis qualificado a contratos reais e agenda de fixtures, com suite congelada offline antes de replay e sem chamadas extras por shrinking/replay.
6. **T3:** transformar referência v4 em paths/request mappings por superfície ou registrar não aplicabilidade. O `blocked_without_external_mapping` atual confirma a lacuna.
7. **T4:** integrar união no runner oficial após T1/T2/T3 congelados; reexecutar com reset, não somar resultados anteriores.
8. **Medição:** incorporar parser corrigido e seleção main-generated-C no runner oficial; provar build/gcov/flush/denominadores na versão efetiva do binding.
9. **Integration-v1/few-shot drift:** revalidar integração contra a versão pós-`fewshot-parent-closure-v1`, pois o próprio contexto registra que a cópia integration-v1 antecede o patch pai.
10. **Ambiente:** declarar o Python/venv oficial. `api-harness-integration-v1` falha no Python do sistema por `jsonschema`, mas passa no venv P2a.

## Plano mínimo sem expansão

1. **Patch de acoplamento mínimo:** trocar `suite-adapters-preflight-v1` para `campaign-harness-v3/src`; rerodar seus 5 testes e um preflight sintético novo.
2. **Smoke integrado mínimo:** criar um único script dry-run que importe adapters + harness-v3 + integration target, mas execute apenas um caso sintético loopback e um caso técnico já existente; sem campanhas.
3. **Freeze final candidato:** emitir manifesto novo com hashes atuais, ambiente, e status `not_approved/not_executable` até conter fixtures/mappings/medição.
4. **Coverage runner correction:** portar `parse_gcov_stdout_units`/`select_units_by_program` para o futuro medidor ou chamar reconciliation como etapa oficial; invalidar explicitamente summaries antigas.
5. **Mapping/applicability gate:** incorporar o mapping novo quando autorizado/lido; classificar cada operação/fixture/obrigação como aplicável, não expressável, bloqueada ou pendente antes de T1–T4.
6. **Revalidar few-shot:** rerodar apenas smoke técnico equivalente ao integration-v1 contra a árvore pós-patch pai, registrando drift/compatibilidade.

## Verificação feita por esta auditoria

- `campaign-harness-v3`: 14 testes sintéticos OK.
- `suite-adapters-preflight-v1`: 5 testes OK, mas contra harness-v2.
- `api-harness-integration-v1`: falhou no Python do sistema por falta de `jsonschema`; passou 3 testes com `../../P2a/.venv/bin/python`.
- `coverage-report-reconciliation-v1`: 5 testes OK.
- Inventário/hashes criados em `inventory.json`; pins comparados em `pin-checks.json`.
