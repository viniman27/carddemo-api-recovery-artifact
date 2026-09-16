# fewshot-parent-closure-v1

## Resultado

Correção mínima aplicada em `P2c-few-shot/p2c_facade.py` após RED no original e arquivamento do arquivo original. O patch proposto no diagnóstico foi revisado, mas não aplicado literalmente: a versão aplicada evita a heurística genérica `END OF EXECUTION` e só reconhece alcance COBOL por saída materializada ou por marcador do programa esperado.

## Pins de entrada e autoridade

- `P2c-few-shot/p2c_facade.py` original validado antes da alteração: `ebe50eebc8c4157ad240b491054187b5499c8b9d761d8c71d6371a1b98da72a8`.
- Arquivo original arquivado em `P3/fewshot-parent-closure-v1/evidence-archive/p2c_facade-original-ebe50eeb.py`.
- Patch diagnóstico lido em `P3/fewshot-integration-diagnosis-v1/proposed-p2c-few-shot.patch`; SHA-256 observado: `45f81b7dbcbf103688134246bcb324a8ca1e3531e7b662c3958f2d11bb56ecde`.
- Contratos conferidos sem alteração:
  - E2-1 `01a904a7c416b0788622dc20ced84fcf3cc8d52065088be97333314037494586`
  - E2-2 `c79c27b56fee0ee985e8c3642c494869c2701054dce7a06cff90fa2519259820`
  - E2-3 `7e91d7c81738a95d97b7a2ece08fd13fb316348e03109885f4ac835ae68ea0a3`
- `contractsIntact`: `true`.

## Mudança aplicada

- `rejections[].candidate.suppliedProcessingTimestamp` é projetado como `rejections[].transaction.processingTimestamp` somente para E2-2, sem inventar timestamp e sem expor o nome interno.
- `run_reporting` registra `cobol_precondition_failure` a partir de DISPLAY COBOL autorizado (`INVALID CARD NUMBER`, `INVALID TRAN TYPE KEY`, `INVALID TRAN CATG KEY`) preservando `rawStatusText`.
- `reached_cobol` em reporting agora usa `reached_cobol_program(cmd, "CBTRN03C", report)`, que não aceita `END OF EXECUTION` genérico de outro programa.
- O 500 de reporting por CARDXREF ausente permanece 500 schema-válido/precondição; não foi mascarado como sucesso nem reparado por fixture.

## RED/GREEN

- RED no original com `tests.test_e2_2_integration_defects`: 3 regressões falharam/erraram pelos sintomas esperados antes da correção (`processingTimestamp` ausente, `reached_cobol=false`, helper ausente para a regra mais rigorosa). Evidência original dos testes arquivada em `evidence-archive/test_e2_2_integration_defects-red.py`.
- GREEN específico salvo em `regression-tests-green.txt`: `3` testes, OK.
- Suíte completa existente + regressões salva em `full-suite-green.txt`: `17` testes, OK.

## HTTP/schema 3 contratos × 3 tracks

Relatório novo: `http-schema-matrix/http-schema-matrix-report.json`.

Contagens derivadas:

```json
{
  "total": 9,
  "schemaValid": 9,
  "schemaInvalid": 0,
  "transportFailed": 0,
  "fixturePrecondition": 3,
  "blocked": 0,
  "http500": 3,
  "http200": 6
}
```

Interpretação preservada:

- `total=9`, `schemaValid=9`, `schemaInvalid=0`, `blocked=0`, `transportFailed=0`.
- `http500=3` são os três reportings com precondição de fixture/dados (`CARDXREF` chave `0000000000000001`, `fileStatus=23`), não falha de transporte.
- `http200=6` cobre postings e interest de E2-1/E2-2/E2-3.

## Revisão de segurança/diff

- Diff aplicado arquivado em `facade-minimal-fix.diff`.
- Varredura estática de linhas adicionadas salva em `security-scan.json`: `securityScanPassed=true`.
- SHA atual de `P2c-few-shot/p2c_facade.py`: `3865e68048e9aee864fcd5085758972912b54826d7449b277ca2e00b18b3c39d`.

## Manifesto

`evidence-manifest.json` lista bytes e SHA-256 dos artefatos de fechamento. Nenhum contrato, SDD, P2b, corpus ou run antigo foi editado por este fechamento.
