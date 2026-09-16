# Conferência direta das correções E1/E2

Status: avanço técnico verificado; implementação integral e campanhas ainda NÃO liberadas. Este relatório sucede a primeira reprovação em FACADE-IMPLEMENTATION-REVIEW.md sem apagar o histórico.

## Fechado no escopo exercitado

- Arrays e argumentos do request passaram a determinar recursos usados pelo COBOL. A regressão independente de posting vazio e prefixo INPUTCHECK passou nas seis réplicas: 12/12. Evidência final: `facade-input-review-_00z5u85/results.json`.
- Os serviços agora fazem chamadas HTTP reais. A primeira conferência do corpo HTTP completo encontrou 15 falhas em 18: os agentes validavam apenas payload.body, enquanto o wire continha wrapper com metadados/audit paths. Evidência RED: `wire-envelope-review-bwbkf1ck/results.json`.
- Removido o wrapper da resposta pública nos dois braços; metadados ficam localmente. Conferência do corpo inteiro recebido pela rede: 18/18 schemas passaram, inclusive os 500 documentados: `wire-envelope-review-sg8besjl/results.json`. Não confundir schema válido com sucesso de negócio.
- Detectado e corrigido diretamente: E1 codificava -1.23 com sinal separado em largura incorreta para o runtime escolhido; E2 recusava todo negativo e preenchia categoryCode/merchantId numéricos com espaços à direita. O probe COBOL sintético compilado com `-std=ibm -fsign=ascii` produziu `0000000012s` para -1.23. Código e bytes originais do probe em `native-display-probe-v1/`; achados pré-correção em `codec-review.json`.
- Correções de transporte: negativos usam sign-overpunch ASCII, campos numéricos recebem zero-fill; E2 decodifica negativo na resposta; nenhuma nova regra de arredondamento foi criada. TDD RED/GREEN executado.
- Suítes finais: E1 oito testes OK; E2 nove testes OK. Logs em `facade-parent-verification-20260915T113118Z/`, incluindo a falha intermediária de auditoria após remoção do wrapper e sua correção por log local.
- Hashes dos seis contratos originais permanecem iguais ao intake anterior à implementação.

## O que os números NÃO encerram

O smoke auxiliar continua evidência de cenários particulares, não certificado de implementação integral. As seguintes lacunas de código/infraestrutura permanecem identificadas, sem nova declaração de 9/9 integral:

1. `parameterLength` exposto em E1-1 e E2-2 é aceito no schema, mas o driver técnico ainda fornece comprimento fixo. Não declarar transporte integral dessa propriedade, mesmo sendo campo não examinado pelo COBOL.
2. Resolução de bindings de saída e política do índice alternativo ainda precisam de fechamento: E1 guarda alguns tokens de output em auditoria sem resolução efetiva; a vinculação do sidecar usa o recurso técnico fixo. Isso não pode ser apresentado como suporte genérico a qualquer recurso válido.
3. Base URLs/roteamento: HTTP QA usa namespace /E1-n ou /E2-n antes dos paths. A publicação experimental deve fixar montagem por contrato ou servidor separado; aliases few-shot sem namespace podem colidir. Não entregar seleção ambígua de réplica ao runner.
4. Caminhos de erro de transporte/setup e preservação de conteúdo parcial em todos os envelopes ainda precisam de verificação fora do happy path. A aprovação dos 18 bodies deste smoke não cobre essas classes.
5. A cadeia original de snapshots/proveniência precisa ser conferida contra os recursos pós-materialização em todas as trilhas; o binding few-shot modifica recursos depois do preparo inicial. O reset/captura deve referir os bytes efetivamente invocados, não apenas a fixture antes do request.

Portanto: as fachadas existem, chamam COBOL e já consomem inputs no escopo verificado, mas a etapa de implementação segue parcial. A prioridade é fechar estes itens delimitados, não ampliar campanhas ou repetir somente smoke nominal.

## Preservação

Versões reprovadas mantidas nos arquivos auxiliares; patches do coordenador também foram arquivados em evidence-archive/parent-codec-fix-* de cada fachada e no diretório de verificação acima. Nenhuma fonte original COBOL, contrato, P2a ou API SDD foi alterada nesta conferência. P3 recebeu QA técnico e relatórios novos, sem substituir resultados experimentais.

A referência independente e as fixtures oficiais continuam separadas; nenhum resultado deste QA deve ser importado como oráculo de negócio. Nenhuma campanha T1/T2/T3/T4 foi iniciada.
