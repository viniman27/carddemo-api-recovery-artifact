# Qualidade — preparação técnica AWS CardDemo

## Resultado útil
Oferecer um primeiro recorte do AWS CardDemo que execute localmente o COBOL original, com entradas, estado, falhas e saídas rastreáveis, antes da entrada formal na pipeline.

## Antimetas
Não alterar a pesquisa principal, fontes COBOL/copybooks, artefatos congelados V4 ou regras de negócio. Não fabricar equivalência com mainframe; não criar contratos/API ou avançar gates. Não vender o tamanho do repositório como tamanho do recorte.

## Amostra representativa
POSTTRAN/CBTRN02C: postagem nominal com leitura dos saldos e transação persistidos; rejeição de cartão, conta, limite e expiração; lote vazio; falha de infraestrutura; duplicata com atualização parcial; repetição após reset. Os testes caracterizam o comportamento local, não são um oráculo independente de negócio.

## Verificação mecânica
Responsável: verify.py e leitura das evidências. Compilação real; hashes do corpus contra archive e snapshot; roundtrip de registro indexado; códigos de retorno e bytes persistidos; reset em diretórios novos. Logs em evidence/ e runs/. Instrumentação gcov demonstrada nos três programas do recorte executável; medição oficial permanece fora deste preparo.

## Adequação ao objetivo
Responsável: Researcher no checkpoint de escopo. O recorte contém 817 linhas físicas COBOL/copybooks; portanto prova infraestrutura de uma capacidade, não um experimento de dezenas de milhares de linhas. Apresentar a postagem e a duplicata com seus efeitos e limites antes de ampliar o caso.

## Paradas
Necessidade de editar o legado ou reproduzir regra fora dele; estado não reinicializável; pressupostos sobre IBM/VSAM tratados como demonstrados; necessidade de alterar corpus para compatibilidade; extrapolação de teste local para continuidade funcional validada.

## Checkpoint
A ampliação técnica foi autorizada, com aplicabilidade da pesquisa como prioridade. Estado vigente em STATUS-ATUAL.md: somente programas realmente executados integram o pacote de entrada. Não iniciar Pipeline Scope Spec, API ou cobertura oficial sem autorização de gate. Aprovação mecânica não substitui a decisão do pesquisador.
