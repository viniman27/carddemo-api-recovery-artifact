# API de integração delimitada — campaign-harness-v2

Este arquivo delimita a API local sintética existente. Ele não autoriza campanha AWS e não define contratos/oráculos/dados oficiais.

## Import principal

```python
from campaign_harness import (
    Case,
    Expectation,
    HttpRequestSpec,
    LocalResourcePackage,
    PerApplicationHttpTarget,
    Suite,
    UnionBuilder,
    VerificationError,
    freeze_suite,
    load_frozen_suite,
    replay_suite,
)
```

## Modelo de caso

- `HttpRequestSpec(method, path, headers, body_kind, body_b64)`
  - `headers` é uma tupla ordenada de pares e pode conter nomes duplicados.
  - `body_kind`: `absent`, `bytes` ou `json`.
  - `absent` não envia `Content-Length`.
  - `bytes` com `body_b64=""` envia corpo presente vazio e `Content-Length: 0`.
  - `json` com `body_b64="e30="` envia `{}` e `Content-Length: 2`.
- `Expectation(expectation_id, checks)`
  - v2 suporta somente `checks["status"]` como lista de status aceitáveis.
  - Qualquer checker não suportado resulta em `expectation_result="inconclusive"`, nunca `pass`.
- `Case.case_id`
  - Preservado literalmente em recibos e registros.
  - Nunca usado como path; o diretório de aplicação é opaco `NNNN-<hash>`.

## Recursos locais

```python
package = LocalResourcePackage.from_directory("pkg-a", source_dir)
suite = Suite("T4", cases, resources={"pkg-a": package})
```

- O pacote recusa symlinks.
- Cada aplicação recebe cópia fresca verificada em `workdir` próprio.
- `pins_before` e `pins_after` são hashes/tamanhos físicos dos arquivos do `workdir`.

## Alvos HTTP

### Alvo controlado por aplicação

```python
target = PerApplicationHttpTarget(MyHandler)
result = replay_suite(suite, target=target, output_dir=Path("run"))
```

- O harness cria um `HTTPServer` loopback novo por aplicação.
- Antes de iniciar, define `MyHandler.workdir = str(workdir)`.
- Após a chamada, executa shutdown, join e close; `applications[i]["target_quiet"]` registra a quietude provada.
- Após timeout, o alvo controlado precisa ficar quieto antes da próxima aplicação; se não ficar, o restante deve ser abortado como `not_executed`.

### Alvo estático legado/sintético

```python
result = replay_suite(suite, base_url="http://127.0.0.1:PORT", output_dir=Path("run"))
```

- Permitido apenas para loopback sintético.
- Se ocorrer timeout, o harness não consegue provar quietude do alvo externo e aborta os casos restantes como `not_executed`.
- Use esta forma apenas para testes onde o alvo não precisa de `workdir` e não há dependência após timeout.

## Resultado

`ReplayResult` contém:

- `totals`
  - `planned`, `attempted`, `completed`, `deadline_failures`, `transport_failures`, `http_failures`, `not_executed`.
  - `expectation_passes`, `expectation_violations`, `expectation_inconclusive`.
- `receipts`
  - `case_id`, `provenance`, método/path/body, `request_headers`, `request_identity`.
  - status/content-type/bytes/hash/failure de transporte.
  - `expectation_result`: `pass`, `violation`, `inconclusive`, `not_evaluated` ou `not_executed`.
- `applications`
  - `case_id`, `workdir`, `pins_before`, `pins_after`, `failure_class`, `target_quiet`.

## Freeze e união

- `freeze_suite(suite, path)` grava JSON com `suite_freeze_sha256`.
- `load_frozen_suite(path)` falha se o JSON congelado foi alterado.
- `UnionBuilder().build([t1, t2, t3])` preserva ordem T1 → T2 → T3.
- Duplicatas de estímulo+expectativa são mescladas com proveniência; mesmo estímulo com expectativa distinta permanece caso distinto.

## Fora de escopo nesta API

- Autorização de execução oficial.
- Geração T1 por LLM.
- Fuzzing T2 real contra contratos AWS.
- Modelo/reference runner T3 independente.
- Fixture oficial AWS/CardDemo.
- Runner COBOL/API por braço.
- Cobertura GnuCOBOL/gcov.
- Oráculos de negócio além de check estrutural de status HTTP.
