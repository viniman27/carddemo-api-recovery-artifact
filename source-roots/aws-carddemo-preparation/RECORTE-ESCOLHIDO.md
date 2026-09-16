# Recorte escolhido — ciclo batch financeiro de cartões

## Decisão
Selecionar, no AWS CardDemo, o processamento batch de transações, cálculo de juros e emissão de demonstrativos. POSTTRAN isolado permanece apenas o ensaio técnico inicial. Esta decisão substitui a hipótese de usar suas 817 linhas como caso maior.

Objetivo de negócio do recorte: processar movimentações e juros de contas de cartão e produzir as saídas financeiras correspondentes, com rastreabilidade entre entradas, saldos, transações, rejeições, extratos e relatórios. É um subsistema coeso com operações relacionadas, não uma única função artificialmente inflada. A fronteira de capacidade/serviço deverá ser estabilizada na pipeline, sem impor previamente uma API única.

A pesquisa principal, os casos anteriores e as evidências congeladas não foram editados. Este arquivo registra somente seleção de escopo, não início de novos gates.

## Medição reproduzível
Comando: `python3 measure_selection.py` neste diretório.
Manifesto com arquivos individuais, hashes e closure COPY: `evidence/large-scope-selection.json`.
Commit CardDemo: `59cc6c2fd7ebd7ef7925cad552a01a4b8b6e4d5e`.

Mesma métrica para os dois lados: linhas físicas de COBOL/copybooks, incluindo comentários e vazios. Cada arquivo aparece uma vez; COPY compartilhado não é somado por ocorrência. JCL, testes novos, harness, API, dados e relatórios não aumentam a contagem AWS.

Baseline conservador: todos os fontes/copybooks dos diretórios legacy-cobol dos três casos atuais, incluindo auxiliares e o teste COBOL de BAMS; não apenas as linhas instrumentáveis das capacidades. Não somar cópias do mesmo legado repetidas por contrato, wrappers gerados ou texto da pesquisa principal.

| Corpus anterior | Linhas físicas |
|---|---:|
| account-balance | 100 |
| payroll | 728 |
| bams | 1.106 |
| Total dos três | 1.934 |

| Programa escolhido | Papel | Linhas físicas |
|---|---|---:|
| CBTRN02C | Postagem, validações, rejeições e atualização de saldos | 731 |
| CBACT04C | Cálculo de juros e geração de transações do sistema | 652 |
| CBTRN03C | Relatório detalhado de transações | 649 |
| CBSTM03A | Emissão de extratos em texto/HTML | 924 |
| CBSTM03B | Acesso aos arquivos usado pela emissão dos extratos | 230 |
| Programas, sem copybooks | | 3.186 |
| 11 copybooks únicos | Layouts e áreas compartilhadas | 258 |
| Total do recorte | | 3.444 |

O novo recorte tem aproximadamente 1,78 vez o total anterior. Mesmo seus programas sozinhos ultrapassam todos os fontes/copybooks dos casos anteriores somados. A comparação não depende de agregar menus, telas CICS, CRUDs não relacionados ou artefatos gerados.

## Coesão observada e orquestração a validar
Os jobs compartilham conta, referência de cartão e transações:

- POSTTRAN.jcl executa CBTRN02C sobre lote, conta, cartão e saldos por categoria.
- INTCALC.jcl executa CBACT04C sobre os saldos e grupos de taxas e grava SYSTRAN.
- TRANBKP/COMBTRAN fazem parte da investigação da ligação entre transações persistidas e transações do sistema; COMBTRAN combina backup e SYSTRAN e recarrega o mestre.
- TRANREPT.jcl descarrega/filtra/ordena transações e chama CBTRN03C.
- CREASTMT.JCL reorganiza transações com chave cartão+ID e chama CBSTM03A, que usa CBSTM03B.

O encadeamento acima é uma fronteira candidata sustentada pelos datasets/JCLs, não uma execução end-to-end já comprovada. Ordem operacional completa, parâmetros, políticas de período, duplicatas e reset ainda precisam ser fechados. Não presumir um fechamento contábil completo, atomicidade ou reprocessamento idempotente.

## Por que é um caso mais interessante
- Estado atravessa vários programas, não somente uma função.
- Há validações, rejeições, cálculos, efeitos persistentes e saídas distintas.
- Copybooks e arquivos compartilhados exigem reconstrução semântica transversal.
- JCL possui filtros, ordenação e reorganização de registros relevantes; não pode ser descartado como configuração irrelevante.
- Há chamada real entre programas na emissão de extratos.
- O conjunto evita a dependência inicial de telas e transações CICS, sem reduzir a pesquisa a um programa de poucas centenas de linhas.

## Limites técnicos conhecidos
Só CBTRN02C tem execução local demonstrada no preparo anterior. Os outros programas não estão declarados compilados, executados ou validados por esta seleção. Não ampliar automaticamente o significado dos 10 testes anteriores.

Investigar antes de preparar o fluxo inteiro:
- parâmetros de CBACT04C, tabelas de taxas, arquivos e possíveis chaves alternativas;
- semântica dos passos SORT/IDCAMS/PROC/GDG e rearranjo de registros de CREASTMT;
- layout de clientes usado pelo extrato e compatibilidade dos datasets;
- assinatura de CBSTM03B e convenções de retorno;
- CBSTM03A contém chamada CEE3ABD sem argumentos: o shim de POSTTRAN, que exige ABCODE/TIMING, não pode ser reutilizado cegamente;
- importação dos dados upstream, incluindo CARDXREF com 36 bytes versus FD de 50;
- reset do conjunto, timestamps, erros e efeitos parciais;
- instrumentação/flush de cobertura, separadamente do build funcional.

Se a execução exigir alterar o COBOL ou implementar regras fora dele, parar para decisão explícita. Não portar o corpus silenciosamente e não acrescentar programas sem relação apenas para aumentar linhas.

## Próxima preparação, sem autorização implícita de gates
O alvo técnico passa a ser este conjunto de cinco programas e seus dados/orquestração. Preservar o ensaio POSTTRAN existente. A seleção não modifica a qualificação, não inicia specs ou contratos e não equivale à aprovação científica do caso.
