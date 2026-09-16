# Rubrica candidata — anterior à coleta

Status: proposta, não aplicada a contratos AWS. Não contém respostas sobre o alvo.

Unidade de julgamento: obrigação observável da referência, com ID, evidência fonte, precondição, entrada, resultado/efeito e limites. A lista concreta da referência deve ser construída em contexto separado e revisada antes de observar os contratos; este documento ainda não é essa lista.

Para cada obrigação: representada integralmente / parcialmente / ausente / contradita / indeterminada. Registrar cláusula do contrato, justificativa e evidência. N/A exige exclusão de escopo aprovada antes da coleta; ausência no contrato não autoriza retirar obrigação da referência. Parcial significa que parte identificável foi preservada, com restante explicitado; indeterminada significa evidência insuficiente, não acerto.

Inspecionar operações e encadeamento; dados e limites representáveis; validações/rejeições; estado e persistência; falha parcial/término; distinção transporte/domínio; dependências e ambiguidade. Julgar também afirmações adicionadas sem suporte, separadamente da completude. Não usar soma ponderada arbitrária como resultado principal.

Validade sintática/OpenAPI é uma dimensão separada, com ferramenta/versão ainda a selecionar. Contrato inválido permanece no inventário e na taxa de falha; sem conserto semântico ou descarte seletivo. Julgamento semântico de saída inválida, quando possível, será explicitamente separado da operacionalização.

Apresentar contagens por categoria e denominadores explícitos; cobertura não substitui esta rubrica. Revisão sem nome do braço quando viável, registrando pistas que impeçam cegamento; preservar avaliações e adjudicar discordâncias por evidência, não por votação de modelos.

Exercício sintético de aplicação: obrigação fictícia exige rejeitar item vencido sem escrita. Um contrato que declara apenas rejeição é parcial quanto à obrigação composta; um contrato que promete escrita é contraditório; omitir a operação é ausência, não N/A. Este exercício testa interpretação da rubrica, não avalia CardDemo nem prova confiabilidade entre revisores.
