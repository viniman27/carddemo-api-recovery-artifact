# Início autorizado do SDD — estágio 1

Usuário aprovou iniciar estágio 1 com invocação dos comandos e confirmou continuidade após esclarecimento da adaptação necessária. Mensagens: “pode sim, com a invocacao dos comandos e tudo mais, certo?” e “entendi, podemos seguir entao”.

Escopo: ligação explícita dos comandos spec-init/spec-requirements à candidata v3, seguida de geração da Pipeline Scope Spec via gpt-6-astra/openai-codex assinatura. Parar antes do estágio 2 para revisão humana. Não autoriza gates em lote, APIs ou testes AWS.

Adaptação em desenvolvimento: sdd-command-adapter/, execução auxiliar aux-d9262151. Executor será bridge local documentada, não slash command nativo. A execução auxiliar só desenvolve/testa offline; ele não executa braço SDD nem gera a Scope Spec. A inferência do estágio será feita pelo modelo escolhido após verificação local do adaptador.

Aprovado iniciar uma instância E3-01, sem inferir aprovação de três réplicas SDD. Entradas do estágio 1: framework/rules/templates e inventário de fonte permitida, com visibilidade escalonada; sem respostas E1/E2, preflight ou referência de avaliação. A política de entrada deve constar do recibo antes da chamada.

Estado deste checkpoint: adaptação em andamento; nenhum comando SDD ainda invocado. Coletas E1/E2 concluídas e intactas.
