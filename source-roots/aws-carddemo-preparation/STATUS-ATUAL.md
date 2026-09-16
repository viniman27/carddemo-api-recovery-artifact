# Estado atual — prioridade: aplicabilidade da pesquisa

## Decisão operacional
O recorte tecnicamente demonstrado é POSTTRAN + INTCALC + TRANREPT: postagem de transações, cálculo/geração de transações de juros e relatório de transações. Programas originais CBTRN02C, CBACT04C e CBTRN03C; 2.226 linhas físicas de COBOL/copybooks, contra 1.934 nos três legados anteriores somados.

A meta aproximada de 10k NÃO foi atingida com um conjunto executável preservando as restrições atuais. Não usar o volume dos candidatos anteriores como volume validado. A instrução mais recente de Researcher tornou aplicabilidade da pesquisa primordial; por isso a proposta CICS e os extratos dependentes de z/OS não entram no corpus executável. Se 10k voltar a ser requisito obrigatório, será necessária outra seleção de corpus ou um ambiente mainframe demonstrado — não uma alegação de compatibilidade.

A pesquisa principal e os experimentos V4 não foram alterados. Preparação técnica não executou nenhum dos oito gates de especificação, nenhum contrato/API ou backend moderno.

## Como verificar
No diretório aws-carddemo-preparation:

    python3 verify_research.py

Esse comando recompila o original, executa a suíte POSTTRAN/segurança, executa o encadeamento batch instrumentado, verifica reset/erros/cobertura e materializa o pacote de entrada separado. Requisitos locais demonstrados: Python 3, GnuCOBOL 3.2 com BDB, GCC/gcov 11.5. Logs completos: evidence/research-acceptance.json. Não há servidor, Docker ou serviço remoto envolvido.

## O que foi exercitado
1. Suíte POSTTRAN e suporte: 13 testes, incluindo rejeições, duplicata, ausência de entrada, roundtrip e guardas de integridade/escopo.
2. Encadeamento real em diretório novo:
   - Fixture sintética: conta com 500,00; saldo por categoria de 10.000,00; taxa de 12%; cartão e grupo correspondentes.
   - CBTRN02C posta uma transação de 25,00: conta passa a 525,00 e categoria a 10.025,00.
   - CBACT04C original calcula e grava uma transação de juros de 100,25, com 350 bytes.
   - CBTRN03C original recebe ESSA transação efetivamente gerada e produz relatório de 1.064 bytes com o valor. Não é um relatório sintético escrito pelo Python.
3. O encadeamento roda novamente em outro diretório. Comparam-se os bytes da transação de juros, exceto as duas regiões de timestamp (278:330), e o registro completo de conta. Os bytes originais são preservados. Isso não prova determinismo de todo relatório nem identidade dos bancos BDB.
4. DISCGRP ausente em INTCALC e DATEPARM ausente em TRANREPT: terminação explícita com código local 12. POSTTRAN preserva o código 4 para rejeições.
5. Os três programas rodam instrumentados com GnuCOBOL/GCC; gcov-11 lê .gcda reais e gera relatórios .cbl.gcov com contadores positivos. Não são denominadores ou resultados oficiais de pesquisa.

O cenário de relatório usa a transação de juros como entrada unitária já ordenada. Não foi demonstrado todo o ciclo de backup, merge, GDG e recarga do mestre descrito em COMBTRAN; não reivindicar esse fluxo completo como executado.

## Entradas e isolamento
- `research-corpus/`: somente os três fontes originais, COPYs transitivos e evidências JCL/procedimento/licença. Cada arquivo confere com o archive fixado. Usar evidence/research-package.json como allowlist.
- `expanded-batch/corpus/`: árvore ampla criada durante exploração; NÃO é a entrada de extração.
- `support/`, `expanded-batch/support/`, testes, runs, relatórios e resultados esperados: suporte/caracterização, fora dos prompts de extração.
- Fixtures são sintéticas, não uma importação ou correção disfarçada dos datasets upstream. Política de dados de domínio visíveis às estratégias deve ser explicitada no gate de escopo antes da coleta oficial.
- O pacote ainda depende do snapshot local e das ferramentas instaladas; não reivindicar reprodução em outro sistema sem testá-la.

## Bloqueios verificados das alternativas maiores
### Atualização online COACTUPC (~10k com dependências e batch)
Prova direta em GnuCOBOL falhou: COPYs de sistema DFHAID/DFHBMSCA ausentes, EIBCALEN indefinido e EXEC CICS não suportado. Evidência: evidence/cics-gnucobol-probe.json. Não foi instalado/emulado CICS e nenhuma regra foi substituída.

### Extratos CBSTM03A/CBSTM03B
Compilação alcançada com configuração explícita de tabulação de quatro colunas para CBSTM03A; fontes permanecem byte-idênticos. Entretanto CBSTM03A acessa PSA/TCB/TIOT do z/OS no início, em torno das linhas 235–285, e o processo local morreu com sinal 11 antes de processamento de negócio. Evidência preservada: expanded-batch/runs/verified-deehe0as/commands.json. CBSTM03B compilou, mas não é contado como capacidade executada isoladamente. Não houve remoção do prólogo ou simulação dessas estruturas.

## Achados de comportamento preservados
- POSTTRAN: duplicata pode deixar saldos atualizados e apenas uma transação persistida antes do abend; já caracterizado nos testes anteriores.
- INTCALC: no lote unitário observado, gera os juros, mas a conta permanece em 525,00 após o cálculo. O fluxo do original posiciona a atualização em mudança de conta e em um ramo cuja relação com o encerramento precisa ser analisada formalmente. Não corrigir nem aplicar os juros pelo harness para esconder o comportamento. Fonte para investigação: CBACT04C:185–222 e 350–356.
- A rotina 1400-COMPUTE-FEES é um placeholder do legado; não descrever taxas/tarifas como funcionalidade implementada.

## Robustez do suporte
As guardas de integridade críticas agora usam exceções explícitas, inclusive com Python -O. O harness verifica que LOAD permanece no diretório novo da execução e que não sobrescreve destino existente. O binário RAWIO é uma ferramenta de baixo nível: LOAD usa OPEN OUTPUT e é destrutivo se invocado diretamente fora do harness. Isso não é um sandbox contra outro processo concorrente.

Os execution.json de POSTTRAN incluem tamanhos e observações por offset em hexadecimal, além de hashes e arquivos brutos. A primeira tentativa de expansão foi interrompida por HTTP429 e tinha defeitos no suporte; o script foi arquivado como evidence/abandoned-runner.py.txt em expanded-batch e não é mais o ponto de entrada. O loader antigo de 500 bytes não é usado. A rotina atual usa loaders de larguras/chaves reais; nenhum banco BDB é interpretado como se seus bytes iniciais fossem um registro de conta.

## Critério de prontidão e limite da garantia
Há evidência de que o recorte pode ser invocado, observado, reinicializado e instrumentado sem editar o COBOL. Isso sustenta começar a aplicação da pipeline nesse ambiente local. Não garante qualidade das especificações geradas, correção do legado, fidelidade z/OS/VSAM/LE, aprovação da banca ou continuidade funcional de um futuro backend — essas são questões a avaliar pela pesquisa.

Próximo passo metodológico: Pipeline Scope Spec sobre o corpus limpo, com aprovação do pesquisador, preservando os limites e dados visíveis. Não retomar a redação da qualificação.
