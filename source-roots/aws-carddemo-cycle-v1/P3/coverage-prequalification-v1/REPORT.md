# Pré-qualificação isolada GnuCOBOL + GCC/gcov — P3

Status: evidência preparatória, não cobertura oficial.

## Escopo executado

- Árvore nova: `P3/coverage-prequalification-v1/evidence-20260915Tprequal-v1/`.
- Script reproduzível: `P3/coverage-prequalification-v1/prequalify_gnucobol_gcov.py`.
- Manifesto completo: `evidence-20260915Tprequal-v1/manifest.json`.
- Comando verificado:

```bash
cd "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/coverage-prequalification-v1"
python3 prequalify_gnucobol_gcov.py --run-id evidence-20260915Tprequal-v1
```

O script recusa sobrescrever um diretório de execução existente.

## Cadeia e versões reais

Registradas em `manifest.json > toolVersions`:

- `cobc`: `/opt/homebrew/bin/cobc`, GnuCOBOL 3.2.0.
- `gcc-11`: `/opt/homebrew/bin/gcc-11`, Homebrew GCC 11.5.0.
- `gcov-11`: `/opt/homebrew/bin/gcov-11`, Homebrew GCC 11.5.0.
- Plataforma observada: macOS 26.5.2 arm64.

Observação técnica: `cobc -info` mostra que o GnuCOBOL instalado foi construído com `clang` e inclui `-Qunused-arguments` em `COB_CFLAGS`; `COB_CC=gcc-11 cobc ...` falhou por essa flag específica de clang durante probe manual. A cadeia qualificada usa `cobc -C` para gerar C intermediário e depois compila esse C com `gcc-11 -fprofile-arcs -ftest-coverage`, lido por `gcov-11`.

## Fontes pinadas e build isolado

O script copiou e verificou os 19 arquivos de `manifest-preparation.json`, commit `59cc6c2fd7ebd7ef7925cad552a01a4b8b6e4d5e`, para `evidence-20260915Tprequal-v1/source-tree/`. Todos os hashes e tamanhos bateram (`hashOk=true`, `bytesOk=true`).

As três rotinas COBOL originais foram compiladas em `evidence-20260915Tprequal-v1/instrumented-build/`:

| Rotina | Fonte original | Artefato | C intermediário | Observação |
|---|---|---:|---|---|
| `CBTRN02C` | `app/cbl/CBTRN02C.cbl` | executável | `CBTRN02C.c` | compilado sem contar o shim `write_observer.c` como negócio |
| `CBACT04C` | `app/cbl/CBACT04C.cbl` | módulo `.dylib` | `CBACT04C.c` | denominador obtido via `.gcno`, sem executar campanha |
| `CBTRN03C` | `app/cbl/CBTRN03C.cbl` | executável | `CBTRN03C.c` | denominador obtido via `.gcno`, sem executar campanha |

Não foi invocado `P2b/p2b_binding.py build()`, nem servidor, nem campanha oficial.

## Denominadores preparatórios

Extraídos de `gcov-11 -b -c` sobre C intermediário e do mapeamento `/* Line: ... : fonte.cbl */` emitido pelo GnuCOBOL. Estes números são preparatórios, não oficiais:

| Rotina | Linhas COBOL atribuíveis por anotação GnuCOBOL | Linhas C gcov | Branches C gcov | Chamadas C gcov |
|---|---:|---:|---:|---:|
| `CBTRN02C` | 366 | 1120 | 288 | 154 |
| `CBACT04C` | 317 | 1029 | 266 | 148 |
| `CBTRN03C` | 346 | 1192 | 272 | 157 |

Limites do denominador:

- O denominador de linhas COBOL é apenas o conjunto de linhas da fonte original anotadas no C gerado; não inclui COPY/support como COBOL de negócio.
- Os denominadores de linhas/branches/chamadas C pertencem ao C gerado por GnuCOBOL e incluem scaffolding técnico/runtime.
- Branch C não está mapeado a decisão de negócio COBOL. Não usar `branch C = decisão negócio`.
- Suportes P2b (`write_observer.c`, drivers, fixtures, IO helpers) foram hashados quando relevantes, mas não contam como COBOL negócio.

## Probe real de flush `.gcda`

Programa sintético isolado: `evidence-20260915Tprequal-v1/synthetic-flush-probe/flush_probe.cbl`.

Resultados reais:

| Modo | Saída do processo | `.gcda` | `gcov-11` |
|---|---:|---|---|
| término normal (`STOP RUN`) | exit `0` | `flush_probe-flush_probe.gcda`, `flush_probe-technical_sleep.gcda` | linhas C 88.24% de 102; branches C 63.64% de 22; chamadas C 92.31% de 13 |
| interrupção (`SIGKILL` antes do fim) | exit `-9` | nenhum `.gcda` | 0.00% de 102 linhas C com `.gcno` presente e `.gcda` ausente |

Conclusão do probe: nesta cadeia, `.gcda` é materializado no término normal do processo COBOL sintético; interrupção por sinal antes do encerramento não flushou cobertura.

## Resultado qualificado vs. ainda pendente

Qualificado agora:

- fontes originais pinadas das três rotinas podem ser copiadas e verificadas em árvore nova P3-local;
- `cobc -C` + `gcc-11` + `gcov-11` gera `.gcno`, `.gcda` e `.gcov` reais;
- denominadores preparatórios por fonte original são extraíveis sem contar suporte como negócio;
- flush normal vs interrupção foi demonstrado com artefatos reais.

Ainda não integrado/qualificado:

- binding AWS/P2b não foi alterado nem executado com cobertura;
- lifecycle do subprocesso P2b ainda precisa garantir saída normal para medição oficial;
- nenhuma campanha/caso oficial foi rodada;
- estes denominadores ainda precisam de congelamento/admissibilidade antes de P3 oficial.
