# Verificação da invocação dos comandos SDD

Autorização atual: iniciar estágio 1, com comandos e gates; sem estágio 2 automático.

Comandos encontrados em .assistant/commands/sdd/ no workspace raiz: spec-init, spec-requirements, spec-design, spec-tasks, spec-impl, spec-status e validadores. São definições de slash commands do assistant, não executáveis de shell nem comandos nativos do transporte Codex usado em E1/E2.

Divergências verificadas antes de execução:
- spec-init lê .sdd/steering e escreve .sdd/specs; v3 exige FRAMEWORK_ROOT e RUN_ROOT separados.
- spec-init ativa integrações de todo steering; v3 mantém integrações opcionais desativadas.
- spec-requirements usa requirements genérico EARS; estágio 1 v3 exige pipeline-scope-spec e proíbe antecipar seleção/semântica.
- pipeline-sdd-v3/pipeline não contém comandos portados: apenas steering, rules/templates e verificadores.

Consequência: não invocar comandos legados diretamente no workspace, não redirecionar .sdd global e não chamar um prompt livre de execução nativa dos comandos.

Trabalho necessário: adaptar as definições para os roots e artefatos v3, registrar diff/proveniência, escolher ligação explícita ao executor gpt-6-astra por assinatura e verificar invocação + leitura/escrita reais. Preservar lógica stage-by-stage e gate humano. Qualquer expansão de prompt pelo executor deve ser registrada como adaptação, não slash command nativo se o cliente não o suporta.

Estado: descoberta concluída; nenhum spec-init/spec-requirements foi invocado e nenhuma Scope Spec AWS foi gerada. As seis respostas E1/E2 permanecem intactas.
