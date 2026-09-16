# Proposta de ampliação para aproximadamente 10 mil linhas

Status: alternativa medida para discussão; não substitui silenciosamente RECORTE-ESCOLHIDO.md nem declara prontidão executável. Nenhuma alteração na pesquisa principal ou no legado.

## Fronteira proposta
Manutenção dos dados de conta de cartão e processamento financeiro batch associado: atualização de conta, postagem de transações, juros, extratos e relatório. Acrescentar COACTUPC ao conjunto batch anterior, além da dependência literal de chamada CSUTLDTC. O conjunto compartilha dados de conta; não é uma operação atômica única nem o sistema completo.

## Medição
Reprodução: `python3 measure_10k_options.py`.
Manifesto: `evidence/10k-scope-options.json`, chave `account-maintenance-batch`.
Snapshot: 59cc6c2fd7ebd7ef7925cad552a01a4b8b6e4d5e.

- Programas COBOL, incluindo utilitário encontrado por CALL: 7.579 linhas físicas.
- Copybooks locais únicos: 2.444 linhas físicas.
- Copybooks de mapas BMS: 668 linhas físicas.
- Total local inventariado: 10.691 linhas físicas.

Inclui comentários/vazios; não são 10 mil linhas de regras de negócio ou instruções executáveis. COPY compartilhado contado uma vez, sem multiplicar COPY REPLACING. Não inclui JCL, harness, APIs ou datasets. A closure de runtime está incompleta: o total mede arquivos locais selecionados, não toda a infraestrutura requerida.

## Custo técnico novo
COACTUPC utiliza EXEC CICS, incluindo RECEIVE/SEND, READ/REWRITE, SYNCPOINT, XCTL e ABEND. A ampliação exige ambiente/runtime compatível para executar o legado original; GnuCOBOL sozinho não demonstra essa capacidade. Não há autorização para substituir CICS ou reimplementar comportamento em um wrapper.

A análise identificou COPY DFHAID e DFHBMSCA não resolvidos nos diretórios locais de fontes/copybooks pesquisados; chamadas externas CEE3ABD e CEEDAYS; transferência CICS por variável CDEMO-TO-PROGRAM, cujo destino não foi fechado. A dependência CSUTLDTC entrou na contagem local por chamada literal resolvida.

Não replicar a alegação de execução de POSTTRAN para este conjunto. Não tratar um adaptador que desvia do programa CICS como execução de todo o recorte. Antes de adotar a ampliação como caso executável, provar viabilidade do módulo online sem editar seu fonte e avaliar o efeito sobre a reprodutibilidade.

## Alternativas medidas
- Manutenção + consulta de conta + batch: 12.110 linhas físicas locais.
- Acrescentando pagamento: 12.822.
- Acrescentando também inclusão/listagem/consulta online de transações: 15.906 (10.904 nos programas COBOL, restante copybooks/mapas).

A primeira proposta fica mais próxima de 10k considerando programas e copybooks. Se o critério passar a ser 10k exclusivamente em programas .cbl, a última alternativa atende, mas aumenta também a superfície CICS e as dependências. Nenhuma alternativa foi compilada/executada neste estudo de tamanho.
