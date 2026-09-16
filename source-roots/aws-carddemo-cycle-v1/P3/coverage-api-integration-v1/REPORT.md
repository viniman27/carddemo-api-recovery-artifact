# coverage-api-integration-v1 — smoke técnico instrumentado

Status: evidência técnica P3; não é cobertura oficial, não congela campanha e não usa suites oficiais/oráculos/quarentena/model calls.

## Comando verificado

```bash
cd "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/coverage-api-integration-v1"
python3 run_coverage_api_smoke.py
python3 -m unittest discover -s tests -v
```

## Resultado

- HTTP completou: `6/6`.
- COBOL alcançado: `6/6`.
- Saída de processo COBOL normal (`program_exit=0`): `6/6`.
- `.gcda` de rotina de negócio presente: `6/6`.
- Reset/isolamento serial verificado: `3/3` pares.

## Trilhas SDD/P2b exercitadas

| Track | Programa | HTTP | exit COBOL | `.gcda` relativo | SHA-256 `.gcda` | gcov-11 |
|---|---|---:|---:|---|---|---|
| `posting` | `CBTRN02C` | 200 | 0 | `gcov/CBTRN02C-CBTRN02C.gcda` | `a1b2b022c28bc21625f36119bc8f34b57b3544f246c3fa823fc1b09f48057b7c` | `Lines executed:56.96% of 1120` |
| `interest` | `CBACT04C` | 200 | 0 | `gcov/CBACT04C.dylib-CBACT04C.gcda` | `1d18a1857bee7ef7772d2e1b3f9f3b160bb6f09d4c217ddf40afafe6df2e467d` | `Lines executed:55.00% of 1029` |
| `reporting` | `CBTRN03C` | 200 | 0 | `gcov/CBTRN03C.gcda` | `8a776150d15851b8f0d7268bb527300cda704ab3117facb16d19fd46aac490d8` | `Lines executed:60.57% of 1192` |

Cada track foi invocada duas vezes em série; os pares têm diretórios de run e `GCOV_PREFIX` distintos. Os nomes relativos dos contadores podem coincidir, mas os arquivos ficam sob árvores diferentes por invocação.

## Isolamento e fontes

- Cópia isolada: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/coverage-api-integration-v1/isolated-cycle`.
- Patch mecânico só na cópia de API: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/coverage-api-integration-v1/isolated-cycle/aws-carddemo-cycle-v1/P2b/p2b_binding.py`.
- Hash original da API copiada: `dfbdf7e6575c34731d08ecb3220c981e9f0b9cc55e835f7d0dcf46ec917b4853`.
- Hash API instrumentada copiada: `f66ce1536889e488f0f2fe32d9238124dcef0756ea572c21023050f491de5ed2`.
- Contratos/fontes COBOL de negócio originais não foram editados; hashes das três fontes estão em `coverage-api-integration-report.json > sourceHashes`.
- Registry técnico copiado/pinado mas não usado nesta prova de lifecycle: `49f0cb521328e6cf26ffdacabfd04d7cae74cc0e2ab6cb4e73facd385aa41160`. Motivo: o pacote local de posting retorna código COBOL 4; para demonstrar saída normal foi usado o smoke técnico interno da API copiada.

## Exclusão de suporte

Regra registrada: apenas `CBTRN02C`, `CBACT04C` e `CBTRN03C` são admissíveis como contadores de negócio. Drivers, fixtures, IO helpers e shims são suporte. Nesta execução, contadores de suporte ficaram ausentes (`supportGcdaCount=0` em 6/6); se aparecerem em execução futura, o script classifica como `inadmissible_nonzero_support_counter`, não como cobertura de negócio.

## Limites de comparabilidade

- Smoke HTTP sintético; sem suites oficiais, sem oráculo de negócio e sem claim de cobertura oficial.
- Contadores gcov são de C gerado por GnuCOBOL; branch C não é decisão de negócio COBOL.
- Runtime exercitado aqui é SDD/P2b nas três trilhas. Zero-shot/few-shot podem compartilhar denominadores preparados, mas não há claim de runtime/cobertura deles neste artefato.
- O patch é mecânico e isolado na cópia de API para trocar build/lifecycle por `cobc -C + gcc-11/gcov-11` e `GCOV_PREFIX` por invocação; fontes de negócio e contratos permanecem inalterados.

## Artefatos principais

- Script: `run_coverage_api_smoke.py` SHA-256 `a2978bc5de6fc379dd65ab86a417e478a1f12ee08773207438164293cbbceabe`.
- Relatório JSON: `coverage-api-integration-report.json` SHA-256 `7cd257df006948341d6f98e9423719b13d059912e8813c468bbbdd3a8e041386`.
- Testes: `tests/test_coverage_api_report.py` SHA-256 `383ff5a2f4f4d4ae12fdc4709fed33d0d1ac7be88f7a080604f6eda308105e07`.
- Build report isolado: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/coverage-api-integration-v1/isolated-cycle/aws-carddemo-cycle-v1/P2b/build-report.json` SHA-256 `c2318d822aa451b0a1fe0c16008dc1f3ff554798641aa47db11b4b464db3237f`.
