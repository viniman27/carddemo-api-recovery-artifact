# Candidatas few-shot — revisão antes de reutilizar

Foram lidos COBOL, OpenAPI e mapping das três demonstrações históricas de experimentos-v4/protocolo/few-shot/demos: temperatura, frete e desconto de associação. São declaradas sintéticas na proveniência histórica. Nenhum arquivo histórico foi alterado ou incorporado ao pacote AWS.

Não reutilizar automaticamente como aprovadas. A leitura encontrou limites relevantes:
- membership: purchaseAmount não declara o teto representável de PIC 9(5)V99; request admite números fora da representação COBOL.
- shipping: mapping diz amount/status na resposta, mas OpenAPI expõe amount no sucesso e traduz a falha em HTTP 422 sem payload. É necessário distinguir tradução deliberada da perda de informação.
- temperature: a descrição admite limitação do resultado representável, mas a entrada pode gerar overflow. É preciso manter a incerteza explícita, sem inventar comportamento de erro do COBOL.

Proposta: produzir cópias candidatas revisadas, fora da V4, preservando originais e registrando as alterações, com compilação/invocação sintética e validação OpenAPI antes de incluí-las. Seleção não usa resultados AWS. As três são microcasos sem persistência: declarar essa limitação de representatividade, não alegar equivalência com uma demonstração batch stateful.

Ainda pendente: aprovação/validação das demonstrações revisadas. E2 não está montado nem liberado para execução.
