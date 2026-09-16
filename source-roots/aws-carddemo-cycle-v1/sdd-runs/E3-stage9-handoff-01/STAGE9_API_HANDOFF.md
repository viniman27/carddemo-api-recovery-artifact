# Stage 9 API handoff — API ready for external testing

Status técnico: `api_ready_for_testing: true`  
Status de campanha: `campaign_ready: false`  
Gate humano Stage 9: `pending` / `human_approval_granted: false`

Este handoff fecha apenas a operacionalização da API SDD Stage 9 para receber testes externos, no mesmo sentido operacional de E1/E2. Não congela suites, não executa T1–T4, não define oráculo independente e não concede aprovação humana.

## Artefatos fonte

- Run qualificado: `../E3-stage9-02/`
- Pacote executável: `../E3-stage9-02/E3-stage9-02-stage9-executable-package.tar.gz`
- SHA-256 do pacote: `1e92fa17f8bd51353271b914495a636be903012617a18fa1490f81d734408d10`
- Relatório Stage 9 original: `../E3-stage9-02/stage9-implementation-executable-qualification.json`
- Evidência independente deste handoff: `independent-http-consumer-report.json`
- Consumidor HTTP independente: `independent_http_consumer.py`
- Cópia nova extraída exercitada: `fresh-package-copy/E3-stage9-02/`

## Ambiente declarado

- Host verificado: macOS local.
- Python usado: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P2a/.venv/bin/python`
- Validador de schema: `jsonschema` importado no ambiente P2a.
- Parser de contrato: `PyYAML` importado no ambiente P2a.
- Compilação COBOL: via `cobc` chamado pelo pacote durante `p2b_binding.py build/serve`.
- Sem chamadas a modelos e sem endpoints públicos de setup/reset.

## Como iniciar a API em uma cópia extraída

A API publica a porta real em arquivo; o valor é efêmero por execução.

```bash
cd "fresh-package-copy/E3-stage9-02/execution/isolated-cycle/aws-carddemo-cycle-v1/P2b"
export P2B_FIXTURE_REGISTRY="../P3/technical-packages-v3-argument/registry.json"
"<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P2a/.venv/bin/python" p2b_binding.py serve --port-file /tmp/stage9-api.port
PORT=$(cat /tmp/stage9-api.port)
```

Endpoint base depois do start:

```text
http://127.0.0.1:${PORT}
```

Na execução independente deste handoff, a porta observada foi `53214`; o processo foi encerrado no fim do teste de lifecycle.

## Contrato HTTP

Contrato original pinado no pacote:

```text
fresh-package-copy/E3-stage9-02/execution/isolated-cycle/aws-carddemo-cycle-v1/P2a/openapi-carddemo-stage6r3.yaml
sha256=9ffb545df736591c56db381eb37bd0612136b6788714f5de758cc056d655c444
```

Rotas aceitas, todas com `POST {}` e `content-type: application/json`:

| Rota | Schema de resposta 200 | Evidência |
|---|---|---|
| `/posting` | `PostingEnvelope` | HTTP 200, schema válido, `reached_cobol=true` |
| `/interest` | `InterestEnvelope` | HTTP 200, schema válido, `reached_cobol=true` |
| `/reporting` | `ReportingEnvelope` | HTTP 200, schema válido, `reached_cobol=true` |

Requisições diferentes de objeto JSON vazio `{}` falham fechadas com HTTP 400 e schema `InterfaceError`; verificado com `POST []` em `/posting`.

## Recursos, reset e lifecycle

Recursos são selecionados por configuração local via variável `P2B_FIXTURE_REGISTRY`. A seleção não é parte do request público; os requests seguem fechados como `{}`.

Registry usado:

```text
fresh-package-copy/E3-stage9-02/execution/isolated-cycle/aws-carddemo-cycle-v1/P3/technical-packages-v3-argument/registry.json
```

Reset efetivo verificado neste handoff, sem reiniciar o servidor:

- mesmo processo do servidor: PID `77467` no relatório;
- primeira invocação `/posting`: workdir `posting-dss6aver`;
- recursos da primeira invocação foram mutados manualmente após a resposta;
- segunda invocação `/posting`: workdir `posting-4qbdjpxn` no mesmo processo;
- `ACCTFILE`, `DALYTRAN`, `TCATBALF`, `TRANFILE` e `XREFFILE` foram rematerializados na segunda invocação com hashes iguais aos bytes originais;
- resultado: `reset_effective_same_process: true`.

Recurso inadequado verificado em modo fail-closed:

- registry alterado localmente para destino `UNSUPPORTED_DD` em `posting`;
- resposta: HTTP 500 com `InterfaceError`/`technical_failure`;
- `new_audit_count: 0`, isto é, a falha ocorreu antes de chamar COBOL.

Lifecycle:

- `serve` constrói antes de publicar a porta;
- a porta é publicada em `--port-file`;
- encerramento por `SIGTERM` retorna `0` no servidor verificado;
- não há endpoint público de reset/setup; isolamento/reset ocorre por novo diretório local por invocação e materialização de recursos pinados.

## Evidência executada

Comando executado a partir deste diretório:

```bash
"<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P2a/.venv/bin/python" independent_http_consumer.py
```

Resultado bounded:

```json
{
  "api_ready_for_testing": true,
  "checks": {
    "fresh_copy_extracted": true,
    "build_exit_zero": true,
    "three_routes_http_200": true,
    "schemas_original_valid": true,
    "cobol_reached_three_routes": true,
    "invalid_request_failclosed_400": true,
    "bad_resource_failclosed_500_no_audit": true,
    "reset_effective_same_process": true
  }
}
```

## Limites explícitos

- Não é campanha pronta: `campaign_ready=false`.
- Não autoriza T1/T2/T3/T4, não congela suites e não define provider/modelos.
- Não cria oráculo independente nem mede fidelidade semântica plena.
- Gate humano é metadado separado do estado técnico: `human_approval_granted=false`, `stage9_review_status=pending`.
- A implementação foi adotada de fontes existentes pinadas e reconstruída; não foi gerada do zero no Stage 9.
