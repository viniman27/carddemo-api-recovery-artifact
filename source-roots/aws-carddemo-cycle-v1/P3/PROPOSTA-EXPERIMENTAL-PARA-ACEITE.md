# Configuração experimental AWS — proposta para aceite

Status histórico da proposta: originalmente não aprovada. Direção D1–D8 agora selecionada sob autorização explícita do pesquisador, com refinamentos em `experimental-direction-delegated-v1.json`. Ver `READINESS-DECISION.md`: não há prontidão material para executar campanhas. O texto abaixo preserva o desenho original; pedidos históricos de aceite não devem ser repetidos como bloqueio rotineiro.

## Onde estamos

A geração documental SDD está concluída. Estamos implementando a API do braço SDD e preparando os testes. A coleta zero-shot/few-shot não significa que suas APIs estejam implementadas. A análise semântica entre braços continua adiada. Este ciclo AWS não é a futura Fase 2.

Este documento complementa, sem apagar, PRETEST-FREEZE-DRAFT.md e seu manifesto histórico. Os hashes antigos daquele manifesto são pins do rascunho, não certificado de frescor do código atual. O estado técnico da nova integração deve ser consultado em FIXTURE-INTEGRATION-TECHNICAL.md e suas evidências, não presumido por esta proposta.

## 1. O que já é regra e o que ainda é proposta

Regras reutilizadas de PROTOCOLO.md:

- Seções 1 e 4: postagem, juros e relatório; zero-shot, few-shot e SDD; fachada por contrato sobre COBOL original, sem acrescentar operações omitidas. Não operacionalizável é resultado registrado.
- Seção 2: isolamento de entradas; suporte e respostas de avaliação não enriquecem silenciosamente extração ou geração. Envio externo depende de autorização do pacote/provedor.
- Seção 3: preservar originais e não retroalimentar contratos da coleta principal com resultados de testes.
- Seção 5: T1 por LLM, T2 por fuzzing de OpenAPI, T3 por modelo explícito com autoridade das expectativas, T4 união dependente. Registrar estado inicial/reset e não inventar rollback/retry.
- Seção 6: separar validade do contrato, alcance, conteúdo/efeitos, aderência ao contrato, fidelidade ao legado, cobertura e custo/intervenções. GnuCOBOL+GCC/gcov é a cadeia de referência a validar; cobertura é explicativa.
- Seção 7: critérios, fixtures, modelo, orçamento e análise precisam de congelamento e decisão humana antes das células oficiais.

Números, ferramenta candidata, ordem e critérios operacionais abaixo são propostas novas. Não são decisões já aprovadas pelo protocolo. Os trechos de estado antigos de PROTOCOLO.md não desfazem coletas e aprovações posteriores.

## 2. Decisões reunidas, com recomendação concreta

### D1 — Fixtures oficiais e visibilidade

Recomendação: pacotes locais imutáveis por trilha, sem dados pessoais, separados de expectativas. Cada pacote deve declarar todos os recursos de entrada/estado necessários, parâmetro externo de juros, recurso de datas e proveniência da seleção anterior do relatório. Identificar recursos vazios explicitamente; não fazer fallback para fixture de smoke em caso de omissão.

Congelar por recurso: caminho relativo, papel, formato físico/encoding, SHA-256, tamanho, origem, gerador e versão se houver; por pacote: ID, trilha, versão, lista de recursos, pré-condições, reset e classificação de exposição. Entradas esperadas/oráculos ficam em pacote separado, não acessível ao adaptador/geradores. Hash de arquivo indexado comprova os bytes daquele objeto; não substitui dump lógico nem portabilidade de Berkeley DB.

Propor famílias para revisão de conteúdo, não casos já gerados:

- Postagem: caminho nominal; ausência de lookup; fronteiras das comparações documentais; repetição/ordem e efeitos parciais com observabilidade explicitamente limitada.
- Juros: caminhos de taxa/fallback; zero e sinal sob autoridade física ainda a confirmar; transição de grupos; término sem inserir finalização não existente.
- Relatório: seleção anterior e datas separadas; mudança de cartão e paginação; ordem/multiplicidade dos registros emitidos; término/falha parcial com campos condicionais não convertidos em expectativas universais.

São eixos de inventário, não promessa de que todos sejam expressáveis pela API ou pelo materializador atual. Cada família só se torna fixture oficial após bytes, pré-condições, rastros e revisão. Não promover automaticamente os pacotes técnicos existentes.

Recomendação de visibilidade: T1 vê somente o contrato do braço e instrução comum; T2 vê somente seu OpenAPI e configuração comum. O controlador externo aplica a mesma agenda congelada de pacotes por trilha em todas as condições/braços compatíveis. Não entregar resultados esperados aos geradores. Qualquer dado adicional exige emenda prévia de exposição.

### D2 — Estado, reset e ordem

Recomendação: execução local serial. Cada aplicação de caso recebe diretório novo, cópia verificada dos recursos iniciais e registro antes/depois; não reaproveitar resultados da aplicação anterior. Os pacotes de origem permanecem imutáveis. Reiniciar o servidor não comprova reset.

Essa ordem vale somente para a campanha oficial após congelamento. A preparação técnica da API SDD pode anteceder os demais braços e não integra as células oficiais.

Ordem proposta: réplica do contrato, estratégia zero-shot → few-shot → SDD, condição T1 → T2 → T3 → T4, trilha postagem → juros → relatório, fixture por ID, caso por ID. Ausências de réplicas não serão preenchidas por reexecução; ainda falta congelar o rol real das unidades, sem ler suas saídas nesta implementação. Essa ordem fixa simplifica replay, mas deixa confusão temporal de latência; registrar essa limitação, sem alegação causal de desempenho.

Não executar POSTTRAN → INTCALC → TRANREPT como cadeia compartilhada automaticamente. A ordem das trilhas não prova encadeamento. Proposta inicial: nenhuma sequência de chamadas com estado reutilizado; T3 modela uma invocação batch e seus estados documentados. Se uma obrigação exigir sequência entre chamadas ou job completo, marcar não demonstrada/não exercitável sob este desenho. Incluir sequências stateful somente por decisão explícita, com recursos, passos e reset próprio definidos.

### D3 — T1, cenários por LLM

Proposta de orçamento inicial: uma chamada de geração por contrato, solicitando até 12 cenários por operação pública expressável, com categorias positiva, negativa e fronteira. A associação à trilha vem da agenda externa de fixtures, não de um selector implícito no request. Mesmo prompt-base, idioma e limite entre braços. Conservar a resposta integral; menos casos, duplicatas, inválidos e omissões são resultados de geração, não motivo para completar manualmente ou tentar outra vez.

Modelo candidato: manter gpt-6-astra se disponível no transporte autorizado. Identificador efetivamente retornado, versão quando disponibilizada e parâmetros suportados precisam de pin no congelamento; o nome nesta proposta não atesta disponibilidade. Sem fallback pago, troca automática, reparo por outra chamada ou retry oportunista. Se seed não for suportada, registrar não suportada, não simular determinismo. Sem replicar geração SDD documental ou importar Stage 8 como suíte T1 privilegiada.

Cada cenário aplicável será executado uma vez por fixture compatível definida na agenda externa. Orçamento solicitado, cenários efetivamente produzidos e aplicações runtime são contadores distintos. O teto monetário permanece zero para fallback pago; chamada no acesso autorizado ainda depende de aprovação explícita do pacote e dos limites do transporte.

### D4 — T2, fuzzing de OpenAPI

Ferramenta candidata: Schemathesis, versão a selecionar mediante ensaio sintético de compatibilidade OpenAPI 3.1, sem campanha AWS. Não declarar versão/compatibilidade antes de medi-las. Proposta: seeds 104729, 130363 e 155921; limite de 100 exemplos por operação e seed, e 10 minutos por operação/seed/fixture, encerrando no primeiro limite. Registrar casos únicos e repetições reais; não preencher orçamento quando o espaço se esgotar. Congelar configuração nativa equivalente somente após verificar a ferramenta.

Checkers propostos: conformidade de status, content type e schema de resposta; registro separado de timeout/falha de transporte. Um 500 admitido pelo contrato não deve ser automaticamente contado como violação contratual só por ser 500. Nenhum checker estrutural é oráculo de negócio. Desabilitar reprodução/shrinking que faça novas chamadas com efeitos até haver política congelada e reset comprovado; se não for possível, a ferramenta/configuração ainda não está apta.

Limitação central: o contrato SDD tem requests fechados {}. Fuzzing dessa superfície pode ter diversidade válida mínima. A variação de dados COBOL vem de fixtures externas, não de propriedades inventadas no body. Recomenda-se publicar separadamente diversidade de requests, diversidade de estados externos e obrigações exercitáveis. Não apresentar 100 repetições de {} como 100 entradas de negócio distintas.

### D5 — T3, modelo e expectativas independentes

Recomendação: modelo de referência da capacidade revisado separadamente antes de resultados. Autoridade primária: corpus original e layouts com âncoras e limites explícitos. O autor/revisor não deve usar os contratos avaliados, seus testes nem outputs runtime para escolher expectativas. Stage 3–8 SDD pode apoiar auditoria de rastreabilidade do braço SDD, mas não transforma um modelo derivado desses artefatos em referência independente entre braços.

Separar dois modelos:

1. Modelo técnico de observação: preparado → invocado → observação disponível/indisponível/com falha → resposta. Verifica evidência do adaptador, não regra de negócio.
2. Modelo de capacidade: transições/guardas próprias de postagem, juros e relatório, com cada expectativa vinculada à fonte e às pré-condições. Ainda não existe pacote independente aprovado nesta entrega.

Proposta de seleção após revisão do modelo: busca em largura, desempate lexicográfico por ID de transição, até 50 caminhos por trilha e fixture; sem geração aleatória inicial. O grafo finito e os limites dos laços devem ser aprovados antes de contar caminhos; não truncar silenciosamente obrigações por esse teto. Registrar alcançáveis, não exercitáveis, omitidas pelo orçamento e expectativas inconclusivas separadamente. Uma aplicação por caminho aplicável, sem retry.

Não calcular valores esperados de juros, arredondamento, datas, durabilidade, efeitos após falha ou armazenamento em EOF por conveniência. Guardas com semântica não estabelecida ficam condicionais/caracterização. Critério de passagem exige referência prévia decidível e observação admissível; não basta repetir a saída da implementação como esperado.

### D6 — T4, união e duplicatas

Recomendação: unir casos preservados de T1/T2/T3 somente após congelar as suítes constituintes. Identidade inclui operação e request HTTP exato (ausência de body não é {}), hash do pacote inicial, parâmetros externos, eventual sequência e ordem de passos, e versão/alvo das expectativas. Não normalizar textos, números ou arrays do domínio para deduplicar.

Casos com mesmo estímulo/estado mas expectativas distintas podem compartilhar uma execução somente se todas as verificações e proveniências forem mantidas. Por padrão conservador, manter ambos quando a equivalência não for demonstrada. Ordem da união: primeira ocorrência em T1, depois inéditos T2, depois inéditos T3; proveniência aponta todos os constituintes.

Executar T4 novamente com reset, não somar coberturas anteriores nem copiar resultados como execução da união. Relatar orçamento efetivo e dependência estatística; T4 não é réplica independente. Duplicata descartada permanece no registro com motivo e referência de destino.

### D7 — Análise e denominadores

Recomendação: análise descritiva por trilha/contrato/condição, sem teste de superioridade causal ou total de células presumido. Manter todas as unidades planejadas, inclusive inválidas/não operacionalizáveis/não executadas.

Denominadores separados, sem substituição retroativa:

1. Desenho: trilhas, estratégias, réplicas de contratos e condições previstas, incluindo unidades sem API operacionalizável.
2. Suítes congeladas: casos efetivamente produzidos e preservados por gerador, com inválidos/duplicatas/omissões e regras de aplicação às fixtures. Congelar cada suíte antes de executar; tamanho efetivo não é o teto solicitado.
3. Execução: aplicações previstas na agenda congelada, tentadas, concluídas e não executadas, com motivo. Não dividir apenas pelos sucessos.
4. Obrigações: inventário de referência independente congelado antes dos resultados; classificação de expressabilidade e evidência não altera o inventário original.

Rubrica proposta:

- Validade contratual: validação estrutural, separada de completude e expressabilidade.
- Operacionalização: implementável sem fortalecer contrato; COBOL efetivamente alcançado por invocação; falhas locais em classe própria.
- Aderência ao contrato: status/envelope/campos/ordem perante observações atribuídas. Não usar 200 como veredito.
- Obrigações do legado: satisfeita, contrariada, inconclusiva, não expressável, não exercitada; autoridade e evidência por obrigação. Razões distintas não são descartadas para melhorar taxa.
- Métricas condicionais: satisfeitas sobre obrigações com veredito decidível, sempre acompanhadas do inventário integral e proporções de inconclusivas/não expressáveis/não exercitadas. Não confundir falta de evidência com falha de negócio ou com satisfação.
- Infraestrutura: falha de setup/hash/build/transporte/captura, timeout, execução interrompida. Guardar bytes/logs; sem apagar/reclassificar retrospectivamente para melhorar desempenho.
- Cobertura: numeradores/denominadores comuns do COBOL, auxiliares fora; cadeia instrumentada e flush ainda precisam de demonstração. Ausência de cobertura medida não vira zero fabricado.
- Custo/latência/intervenções: geração, materialização, invocação e análise separados; publicação de contagens realmente observadas, sem imputação de tentativas faltantes.

Bytes brutos sempre preservados. Proposta inicial: nenhuma normalização de timestamps em comparação; se atrapalharem a pergunta, aprovar previamente máscara por campo e motivo, nunca aplicar exclusão pós-observação para obter PASS.

### D8 — Falhas e conteúdo parcial

O contrato aprovado já distingue indisponível, vazio positivamente observado e falha técnica. Não há nova votação para recriar essa semântica. O que precisa de aceite experimental é a taxonomia operacional e a aplicação uniforme das regras aos braços sem alterar seus contratos.

Para a API SDD, manter falha técnica para TRANREPT significativo não representável, inclusive misturado com registros reconhecidos; preservar conteúdo sustentado em availableContent e bytes desconhecidos em auditoria. Registros físicos de 133 bytes e transações de 350 bytes são limites do binding observado, não requisitos públicos novos. Ausência de captura não é vazio; progresso não comprova saída; motivo 109 permanece interno.

## 3. O que esta proposta não entrega

Implementação ainda necessária antes das campanhas:

- APIs dos braços zero-shot/few-shot, ainda não verificadas como prontas, e mapeamentos justos dos testes para cada superfície.
- Pacotes oficiais com conteúdo e hashes aprovados, e ferramentas de materialização suficientes para suas famílias; a seleção de pacotes técnicos não prova adequação de todos os layouts oficiais.
- Modelo de capacidade/expectativas independentes e revisão de autoridade; o texto acima é desenho, não modelo executável validado.
- Ensaio sintético e pin da ferramenta de fuzzing, runners T1/T2/T3/T4, união/deduplicação e medição; config de exemplo não é runner.
- Instrumentação/denominadores gcov e prova de término/flush nas condições oficiais.
- Manifesto final de congelamento com todas as versões e registro real de aceite. Alterar rótulos JSON não equivale a autorização humana.

Evidência ainda não demonstrada por QA técnico:

- Fidelidade semântica abrangente, completude do relatório, persistência durável, segurança de repetição ou equivalência a mainframe.
- Independência efetiva da referência/MBT e aplicabilidade de cada fixture/obrigação em cada contrato.
- Comparação entre abordagens, cobertura oficial, taxas de sucesso e resultados T1/T2/T3/T4.

## 4. Forma de aceite recomendada

Aceitar ou ajustar D1–D8 como direção, sem autorizar execução oficial ainda. Depois materializar os itens dependentes dessa decisão (fixtures oficiais, modelo independente, versões, limites e rol de unidades) e apresentar um único manifesto concreto para congelamento. O aceite da direção não preenche hashes inexistentes, não aprova expectativas ausentes e não inicia campanha.

Questão metodológica central para o aceite: manter T1/T2 limitados à superfície pública e controlar estados COBOL por agenda externa comum, aceitando a baixa diversidade de {} no SDD? Recomendação: sim; isso preserva o contrato e deixa sua expressabilidade como propriedade observável, em vez de disfarçá-la com endpoints inventados.
