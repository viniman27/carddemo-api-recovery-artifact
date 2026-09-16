# Stage6 r2 Result — API Contract CardDemo

## Resultado operacional

- RUN_ROOT: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/sdd-runs/E3-01`
- Saída gerada inspecionada: `prepared/api-contract-carddemo-r2/execution/scope-original.md`
- Modelo registrado no recibo: `gpt-6-astra`
- HTTP/status registrado: `200` / `generated_pending_human_review`
- Completion SSE verificado: `response.completed=2`, `output_text.done=2`, `status=completed tokens=2`
- SHA-256 real da resposta gerada: `163d1d0455f2524e8100e1722b78f255fbca7a4bda1a5caccb45e05fbe362567`
- `parsed.json.text` byte-idêntico ao original UTF-8: `True` (`49791` bytes)

## Materialização

- Placeholder inicial detectado em `specs/api-contract-carddemo-r2/requirements.md`: `True`
- Placeholder arquivado em: `specs/api-contract-carddemo-r2/requirements-initial-placeholder.md`
- `requirements.md` substituído pelos bytes exatos de `scope-original.md`: `True`
- SHA-256 final de `requirements.md`: `163d1d0455f2524e8100e1722b78f255fbca7a4bda1a5caccb45e05fbe362567`

## Metadados r2 atualizados

Arquivo: `specs/api-contract-carddemo-r2/spec.json`

- `approvals.requirements.generated`: `true`
- `approvals.requirements.approved`: `false`
- `gate.review`: `null`
- `ready_for_implementation`: `false`
- `updated_at`: `2026-09-13T07:56:12-03:00`
- SHA-256 final de `spec.json`: `3dd7c64774f75c3155b2e9941f139ca593401887555fd7d7917874c6bc591b54`

Nenhuma aprovação humana, Stage7, geração adicional, chamada de rede, execução COBOL ou implementação foi realizada.

## Escopo inspecionado e proteção

Entradas protegidas verificadas antes/depois: `12`. Todas permaneceram inalteradas: `True`. Detalhes e hashes completos estão em `specs/api-contract-carddemo-r2/stage6-r2-verification.json`.

## Validações programáticas

- Operações HTTP únicas encontradas: `POST /interest, POST /posting, POST /reporting` (`3`)
- Tracks mencionadas: posting `37`, interest `32`, reporting `26`
- `R-1..R-20` no documento: `20` únicos; reverse-completeness cobre `20/20`; faltantes: `[]`
- Decisões `D-n` únicas: `16` (`D-2..D-17` com lacunas conforme histórico Stage5/6)
- Gaps `G-n` únicos: `6`; inclui G-21..G-24
- Âncoras fonte em r2: full `3`, shorthand `0`; hashes SHA-256 literais em r2 `16`
- Corpus permitido citado no request: `19` menções únicas; hashes SHA-256 únicos no request `85`
- Rejeições posting: 100 `3`, 101 `2`, 102 `3`, 103 `5`, 109 `8`

## OpenAPI

Nenhum documento standalone OpenAPI (`openapi: 3.x`) foi incluído no `requirements.md`. Portanto não houve validação OpenAPI com validador real. A conclusão é apenas de completude documental/representabilidade proposta, não de contrato pronto para implementação.

## Recomendação

Encaminhar `specs/api-contract-carddemo-r2/requirements.md` para gate humano como revisão documental candidata. Não marcar aprovado e não iniciar Stage7/implementação até decisão humana explícita.
