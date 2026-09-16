# api-harness-integration-v1 — relatório técnico

Escopo: smoke técnico delimitado, não T1/T2/T3/T4 oficial, sem oráculos de negócio e sem leitura de quarentena/oráculos.

## Artefatos produzidos

- `src/api_harness_integration.py`: ligação técnica com spawn controlado (`os.posix_spawn` + `exec`) e checker OpenAPI/jsonschema.
- `src/run_real_smoke.py`: preparação de ciclo isolado e execução serial dos requests HTTP.
- `tests/test_integration_contract.py`: testes TDD para registry copiado, jsonschema/status/content-type e quietude de process group.
- `integration-report.json`: readback completo dos 9 requests reais.
- `isolated-cycle/`: cópia operacional temporária dos braços, contratos, corpus público necessário e fixtures atuais copiadas.
- `run-output/`: stdout/stderr e diretórios por aplicação.

## O que foi exercitado

Um contrato por servidor, um processo por aplicação/request, serial:

| Braço | Contrato pinado | Rotas/tracks exercitados |
|---|---|---|
| SDD/P2b | `E3-01-stage6r3` / `P2a/openapi-carddemo-stage6r3.yaml` SHA-256 `9ffb545df736591c56db381eb37bd0612136b6788714f5de758cc056d655c444` | `/posting`, `/interest`, `/reporting` |
| Zero-shot/P2c | `E1-3` SHA-256 `415f9cceb3bc96dff489552c19a916e63ccf14f22741a4b320c970104032faa4` | `/transaction-postings`, `/interest-transaction-generations`, `/transaction-reports` |
| Few-shot/P2c | `E2-2` SHA-256 `c79c27b56fee0ee985e8c3642c494869c2701054dce7a06cff90fa2519259820` | `/transaction-posting-runs`, `/interest-generation-runs`, `/transaction-report-runs` |

## Resultado real

Resumo de `integration-report.json`:

```json
{
  "planned": 9,
  "http_completed": 9,
  "schema_or_documented_500_valid": 8,
  "reached_cobol": 8,
  "quiet": 9
}
```

Evidências registradas por caso:

- request HTTP completou nos 9 casos;
- servidor iniciado por `posix_spawn_setsidshell_exec` nos 9 casos;
- quietude comprovada nos 9 casos após parar API e grupo/process tree, não apenas matar a API;
- SDD/P2b: 3/3 chegaram ao COBOL e usaram registry isolado copiado;
- Zero-shot/P2c: 3/3 chegaram ao COBOL; cada request materializou registry local derivado no `run-output/.../request-packages/.../registry.json`;
- Few-shot/P2c: 2/3 chegaram ao COBOL; reporting retornou 500 documentado com schema válido, mas o audit registrou `local_compatibility_abort` e `reached_cobol=false`.

## Checkers

`ContractChecker` usa `jsonschema.Draft202012Validator` com resolver do contrato OpenAPI. Classificações separadas:

- `schema_valid` para status documentado + content-type JSON + schema válido;
- `documented_500_schema_valid` para 500 documentado válido;
- `status_violation`, `content_type_violation`, `json_violation`, `schema_violation` para violações;
- `infra_transport` para falha sem resposta HTTP.

## Pendências / achados

- Few-shot/E2-2 posting: HTTP 200 chegou ao COBOL, mas falhou schema (`processingTimestamp` ausente). Classificado como violação de contrato, não infra.
- Few-shot/E2-2 reporting: HTTP 500 documentado e schema válido, mas audit mostra `local_compatibility_abort` com `program_exit=12` e `reached_cobol=false`; tratado como falha técnica documentada, não sucesso funcional.
- Zero-shot/P2c cria registries por request package; não usa diretamente o registry global isolado no audit P2b. O registry-fonte e bytes de entrada são copiados/isolados, mas o audit P2b aponta para registry derivado por request.
- Não há alegação de cobertura total: foram 9 requests representativos, três tracks em três braços, um contrato pinado por braço.

## Verificações executadas

- `P2a/.venv/bin/python -m unittest discover -s tests -v` em `P3/api-harness-integration-v1`: 3 testes OK.
- `PYTHONPATH=P3/campaign-harness-v3/src P2a/.venv/bin/python -m unittest discover -s tests -v` em `P3/suite-adapters-preflight-v1`: 5 testes OK; compatibilidade adapter v1 → harness v3 preservada sem mudar originais.
- `P2a/.venv/bin/python src/run_real_smoke.py`: gerou `integration-report.json` com 9/9 HTTP, 8/9 schema/documented-500 válido, 8/9 reached COBOL, 9/9 quiet.
