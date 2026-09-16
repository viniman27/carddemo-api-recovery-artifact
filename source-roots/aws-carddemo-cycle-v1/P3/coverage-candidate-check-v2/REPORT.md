# coverage-candidate-check-v2 — qualificação preparatória com registry candidato real

Status: evidência técnica preparatória, não cobertura oficial e não campanha T1/T2/T3/T4.

## Comandos executados

```bash
cd "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/coverage-candidate-check-v2"
python3 run_candidate_coverage_check.py  # falhou por ModuleNotFoundError(jsonschema); preservado em failure.json
<WORKSPACE>/aws-carddemo-cycle-v1/P2a/.venv/bin/python run_candidate_coverage_check.py
```

## Resultado resumido

- Invocações planejadas/completadas HTTP: `6` / `6`.
- Processo COBOL com saída normal (código >= 0): `6/6`; por sinal: `0/6`.
- `program_exit=0`: `4/6`; `program_exit` não-zero normal: `2/6`.
- COBOL alcançado: `6/6`; `.gcda` de negócio presente: `6/6`; `gcov-11` lido: `6/6`.
- `GCOV_PREFIX` observado no comando de negócio: `6/6`; pares reset/isolamento verificados: `3/3`.
- Execuções admissíveis para medição preparatória: `6/6`.

## Registry candidato pinado

- Registry usado: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/coverage-candidate-check-v2/isolated-cycle/aws-carddemo-cycle-v1/P3/technical-packages-v3-argument/registry.json`
- SHA-256 do registry gerado/copiado: `f942e3c1e7d9d0fa65422a97ff9252c233947e70c30af9d0fd713d4f5ad57109`
- Tree SHA-256 do pacote candidato copiado: `694494464b6db6b79bcc60b5cc5efb6a92c90610dc0f5ed18e1c4e0914aefd8b`
- Tree SHA-256 do pacote fonte `fixture-materialization-v2/package`: `694494464b6db6b79bcc60b5cc5efb6a92c90610dc0f5ed18e1c4e0914aefd8b`
- Não houve fallback para smoke interno; `P2B_FIXTURE_REGISTRY` apontou para esse registry candidato nas 6 invocações.

## Admissibilidade por execução

| # | Track | Programa | HTTP | program_exit | Processo | COBOL | .gcda negócio | gcov-11 | Linhas C preparatórias | Suporte .gcda | Admissibilidade |
|---:|---|---|---:|---:|---|---:|---:|---:|---:|---:|---|
| 1 | `posting` | `CBTRN02C` | 200 | 4 | `normal_exit_code` | true | true | 0 | 58.64% / 1134 | 0 | `admissible_preparatory` |
| 2 | `interest` | `CBACT04C` | 200 | 0 | `normal_exit_code` | true | true | 0 | 57.43% / 1043 | 0 | `admissible_preparatory` |
| 3 | `reporting` | `CBTRN03C` | 200 | 0 | `normal_exit_code` | true | true | 0 | 56.03% / 1244 | 0 | `admissible_preparatory` |
| 4 | `posting` | `CBTRN02C` | 200 | 4 | `normal_exit_code` | true | true | 0 | 58.64% / 1134 | 0 | `admissible_preparatory` |
| 5 | `interest` | `CBACT04C` | 200 | 0 | `normal_exit_code` | true | true | 0 | 57.43% / 1043 | 0 | `admissible_preparatory` |
| 6 | `reporting` | `CBTRN03C` | 200 | 0 | `normal_exit_code` | true | true | 0 | 56.03% / 1244 | 0 | `admissible_preparatory` |

Observação empírica: as duas execuções de `posting` retornaram `program_exit=4`, mas o processo terminou normalmente (`exitKind=normal_exit_code`), alcançou COBOL, gerou `.gcda` e foi lido por `gcov-11`. Portanto, neste pacote candidato, `exit 4` não é interrupção por sinal nem, por si só, invalida flush de cobertura.

## Denominadores e exclusão de suporte

Números abaixo são preparatórios/não oficiais e pertencem ao C gerado por GnuCOBOL, não a decisões de negócio COBOL.

| Programa | Linhas C gcov | Branches C gcov | Calls C gcov | Denominador comum nas duas invocações |
|---|---:|---:|---:|---:|
| `CBACT04C` | 1043 | 36 | 148 | true |
| `CBTRN02C` | 1134 | 38 | 154 | true |
| `CBTRN03C` | 1244 | 48 | 2 | true |

- Regra aplicada: apenas `CBTRN02C`, `CBACT04C` e `CBTRN03C` contam como negócio; drivers, fixtures, IO helpers e shims são suporte.
- Nesta execução, `supportGcdaCount=0` nas 6 invocações. Se suporte aparecer em execução futura, o relatório o classifica como excluído/inadmissível para cobertura de negócio.

## Integridade de isolamento e GCOV_PREFIX

- `posting`: dois run dirs distintos, dois `GCOV_PREFIX` distintos, 1 + 1 `.gcda`; `resetVerified=true`.
- `interest`: dois run dirs distintos, dois `GCOV_PREFIX` distintos, 1 + 1 `.gcda`; `resetVerified=true`.
- `reporting`: dois run dirs distintos, dois `GCOV_PREFIX` distintos, 1 + 1 `.gcda`; `resetVerified=true`.

## Falhas preservadas

- Primeira tentativa com `python3` falhou por infra/dependência: `ModuleNotFoundError("No module named 'jsonschema'")`. O arquivo `failure.json` foi preservado. A execução válida usou o Python do venv P2a que já contém as dependências do harness.

## Artefatos principais

- `run_candidate_coverage_check.py` — SHA-256 `56a96a730b1363989ba45c6e7a9a20b61aca3586267ce5dcfb21c804bbda830b`
- `candidate-coverage-report.json` — SHA-256 `548ea8d5f2fe139d5041bd15819956c77e3f7d8b9d592bdcfca6d607f8e3f63e`
- `failure.json` — SHA-256 `617f6f09de134be272678d0fbf7097af1efa60994b2f94d4c931a29e0afd4b77`
- `driver-command-log.jsonl` — SHA-256 `747d9514ebaf0746b1e76227fa5591c0a6f335fe264c91c609fc7840289f8a09`
