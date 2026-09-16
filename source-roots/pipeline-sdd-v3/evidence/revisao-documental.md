# Exercício documental da candidata — revisão própria

Não é revisão independente, extração CardDemo, execução de COBOL ou aprovação humana. Os contraexemplos abaixo são sintéticos e foram lidos contra as regras/templates alterados. Objetivo: verificar se a orientação agora exige a informação que a base podia omitir.

## 1. Reset externo e dois recursos

Amostra: um lote mantém um arquivo persistente e um cache por processo. A API não expõe reset; o teste usa servidor novo e supõe dados limpos.

Leitura: estágio 5 §6 agora exige estado por recurso e distingue reinício de processo de reset persistente. Estágio 6 §5.4 deve marcar reset externo, sem inventar endpoint. Estágio 7 §4.1 pede mecanismo e observação. Estágio 8 §5.3 exige fonte do estado/setup. A amostra incompleta deve retornar ao dono da decisão, não receber aprovação pela sessão nova.

Resultado da revisão própria: cadeia documental cobre a omissão; a implementação real de reset permanece por testar na aplicação futura.

## 2. Falha após a primeira escrita

Amostra: operação escreve um saldo e falha antes de inserir seu registro; cliente recebe erro e repete automaticamente.

Leitura: estágio 3 §4.1 deve registrar ordem/evidência ou ambiguidade; estágio 4 exige efeitos parciais e segurança de repetição; 5 transporta essa restrição; 6 não pode prometer rollback/idempotência sem fundamento; 7 §5.1 não compensa silenciosamente; 8 §5.3 exige observação do estado, não só do status.

Resultado da revisão própria: retry deve ficar unsafe/unknown até haver evidência. Isso é exercício genérico do template, não constatação nova sobre AWS.

## 3. Fuzzer externo com contrato incorreto

Amostra: contrato omite uma obrigação; ferramenta externa gera requests válidos desse mesmo OpenAPI e não encontra violações.

Leitura: inventário de oráculos distingue origem da ferramenta de origem da expectativa. run-integrity §4 e validation-principles proíbem inferir fidelidade COBOL desse resultado. Relatório só pode afirmar conformidade no escopo exercitado.

Resultado da revisão própria: o contraexemplo invalida a alegação de fidelidade, mesmo com ferramenta de outro fornecedor.

## 4. Contaminação pela preparação

Amostra: executor leu um relatório com respostas esperadas e depois recebe apenas os fontes em uma mensagem nova na mesma sessão.

Leitura: escopo §1.3 exige exposição prévia; run-integrity §1 distingue sessão exposta de contexto limpo. Um manifesto sem o relatório não apaga o conhecimento anterior.

Resultado da revisão própria: declarar exposição ou criar execução isolada conforme protocolo, sem chamar o resultado de descoberta independente.

## Limites

A revisão mostra que as perguntas necessárias agora estão nos pontos de derivação e gates. Não mostra que um modelo as responderá corretamente nem que o framework evitará toda omissão. A qualidade da cadeia real depende da aplicação revisada por Researcher. A tentativa de busca independente por execução auxiliar falhou por HTTP 429; não há parecer independente dessa tentativa.
