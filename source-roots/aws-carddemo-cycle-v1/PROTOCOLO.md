# Ciclo público AWS CardDemo — protocolo candidato

Status: preparação documental autorizada; protocolo ainda não congelado. Nenhuma extração, contrato, API ou célula experimental executada neste ciclo. Não é Fase 2, não reabre V4 nem a qualificação. A autorização para preparar este documento não aprova gates experimentais.

## 1. Objeto e recorte

Comparar zero-shot, few-shot e SDD na recuperação e exposição de uma capacidade batch COBOL, e exercitar cada contrato sobre o legado com testes LLM, fuzzing OpenAPI, MBT e união. Avaliar obrigações observáveis e limites, não equivalência interna ou formal.

Recorte operacional de referência: POSTTRAN → INTCALC → TRANREPT (CBTRN02C, CBACT04C, CBTRN03C). A delimitação final da capacidade/operacionalização pertence ao gate de escopo. Fonte autorizável: ../aws-carddemo-preparation/research-corpus, exclusivamente conforme evidence/research-package.json da preparação, commit 59cc6c2fd7ebd7ef7925cad552a01a4b8b6e4d5e. Não substituir pelo antigo recorte de cinco programas ou árvore exploratória. O ciclo integral de backup/merge/GDG/recarga não foi demonstrado pela preparação.

## 2. Entradas e isolamento

- Corpus de referência comum: fontes originais, COPYs transitivos, JCL/procedimento e licença da allowlist. Manifesto local registra hashes efetivamente verificados. JCL é evidência, não alegação de execução local.
- E1/E2 recebem o mesmo alvo e instrução de extração. E2 acrescenta somente demonstrações externas previamente fixadas. SDD recebe corpus equivalente e framework genérico; a visibilidade pode ser escalonada por estágio, nunca enriquecida silenciosamente com respostas da preparação.
- Dados de domínio: proposta inicial sem fixtures sintéticas nos prompts de extração; layouts originais permanecem visíveis. Qualquer inclusão precisa de decisão anterior à coleta, aplicada por política comum e registrada.
- Quarentena: suporte, fixtures, testes, runs, resultados esperados, relatórios de preflight e contratos/reimplementações preexistentes. Não transmitir este protocolo administrativo inteiro como prompt: ele referencia a preparação.
- O coordenador desta sessão já leu os achados do preflight. Extrações devem usar contextos novos e pacotes explicitamente montados, sem histórico/memória de respostas. Registrar contexto realmente entregue e exposições humanas; contexto novo não apaga conhecimento do pesquisador nem prova ausência de memorização pelo modelo.
- Não exportar material pessoal/privado. Chamadas de modelo dependem de aprovação do pacote visível e do provedor antes do envio.

## 3. Estratégias de extração

E1: instrução fixa + corpus-alvo, sem demonstrações.
E2: mesma instrução + demonstrações COBOL→OpenAPI externas, fixas e com proveniência + mesmo corpus. Quantidade e conteúdo ainda pendentes; não herdar automaticamente exemplos históricos.
E3: candidata pipeline-sdd-v3/pipeline, com oito artefatos: escopo, seleção de capacidade, evidência, semântica, fronteira canônica, contrato, comportamento do adaptador e validação semântica. Preservar ordem e gates. Matriz de completude cresce nos estágios 3–6; contraexemplos nos gates 4/6; revisões vinculadas a versões e autorização real.

Congelar modelo/versão, parâmetros suportados, contexto, saída, orçamento, repetições, seed quando disponível, retry, idioma e política de contrato inválido antes de extrair. Preferir configuração comum onde comparável; registrar diferenças do processo SDD, revisão humana e custo acumulado. Comparação entre estratégias completas, não efeito causal isolado de prompting.

Nenhum feedback de testes ou resultados da avaliação retroalimenta contratos da coleta principal. Correções futuras exigem emenda e novo ciclo identificado; preservar original inclusive falhas.

## 4. Operacionalização de todos os contratos

Contrato do braço → fachada específica → driver técnico comum quando aplicável → COBOL original. Não implementar regra de negócio no suporte, acrescentar operação omitida ou fortalecer silenciosamente schema. Registrar toda adaptação técnica e exigir política equivalente nos braços. Evidenciar alcance do COBOL por chamada/efeito/log; sucesso HTTP sozinho não basta.

Um contrato não operacionalizável vira resultado documentado, não exclusão silenciosa. O estágio 8 SDD não libera execução de testes antes de congelar os contratos e o protocolo comum; artefatos específicos SDD não concedem informação privilegiada ao T1 dos demais braços.

## 5. Estratégias de teste

T1: cenários por LLM sob categorias, orçamento e entrada uniformes por contrato. Congelar exatamente se vê apenas contrato ou outro material comum. Não importar automaticamente a suíte produzida no SDD como T1 sem declarar a assimetria.
T2: fuzzing orientado pelo contrato OpenAPI; ferramenta e versão selecionadas por compatibilidade demonstrada, orçamento, seeds suportadas, checkers e sequenciamento documentados. Ferramenta externa não garante oráculo de negócio independente.
T3: MBT com modelo explícito de estados/transições/guardas, fonte das expectativas e revisão anteriores aos resultados. Proposta: referência da capacidade separada dos contratos avaliados, traduzida para cada superfície por mapeamento documentado. Obrigações não expressáveis ficam registradas, não desaparecem do denominador. Não gerar o modelo somente do contrato e chamá-lo independente.
T4: união T1/T2/T3 com proveniência, política de duplicatas, ordem e reset congelados. Não somar percentuais de cobertura nem tratar união como réplica estatística independente. Registrar orçamento efetivo da união e não presumir igualdade ao de uma suíte individual.

Para todas: diretório/estado inicial novo por unidade definida; preservar sementes, dumps lógicos, stdout/stderr, exit codes e arquivos resultantes. Definir reset entre casos versus sequência stateful. Não compensar falha parcial, inventar rollback ou repetir operações com efeitos sem política explícita. Comparar registros lógicos; exclusões de timestamps precisam de regra congelada, com bytes brutos preservados.

## 6. Medição e análise

Separar: validade/qualidade/completude do contrato; alcance e falhas de infraestrutura; resultado observável e efeitos persistidos; aderência ao contrato versus fidelidade ao legado; cobertura estrutural; custo, latência e intervenções humanas. Definir rubrica e autoridade do oráculo para cada pergunta antes de observar resultados.

GnuCOBOL+GCC/gcov permanece a cadeia de referência a validar no ambiente. Denominadores comuns do corpus original, auxiliares excluídos; verificar término normal e flush real de .gcda. Contadores do preflight não são medidas oficiais. Cobertura é explicativa, não prova principal de continuidade funcional.

Unidade candidata: capacidade × estratégia de extração × réplica de contrato × condição de teste × réplica/seed de execução. T4 é dependente das suítes constituintes. Não fixar total de células antes de aprovar capacidade, repetições e política de falhas. Preservar ausências, contratos inválidos e limites de ambiente na análise; evitar selecionar só sucessos.

## 7. Gates do ciclo (distintos dos oito gates SDD)

P0 — Aprovar escopo, corpus, visibilidade, isolamento e desenho geral.
P1 — Congelar prompts/demonstrações, modelo/parâmetros, custos, repetições, retries, rubrica e política de contratos inválidos. Autorizar extrações; E3 mantém autorizações por estágio.
P2 — Congelar contratos e aprovar operacionalização justa, prova de execução do COBOL e limites técnicos.
P3 — Congelar entradas/oráculos T1–T4, modelo MBT, orçamentos, seeds, resets, união, denominadores e plano de análise. Autorizar células oficiais.
P4 — Consolidar evidências, limitações e análise sem reescrever resultados históricos.

Dependências metodológicas: construir referência de avaliação sem resultados dos braços; fixar rubrica em P1. Finalizar instrumentação e mapeamentos de teste em P3 sem mudar obrigações de avaliação após ver desempenho. Todo gate requer registro de decisão humana; verificação mecânica nunca o aprova.

## 8. Decisões ainda necessárias

Antes de P1: modelo/provedor e acesso permitido; limites de custo/contexto; quantidade de repetições; demonstrações few-shot; prompts reais; unidade final da capacidade; rubrica e equipe/contexto da referência. Antes de P3: fuzzer compatível; modelo MBT e autoridade das expectativas; entrada T1; orçamento/seed/reset/união; métricas e análise. Não usar defaults ocultos nem parâmetros antigos como se aprovados para AWS.

## 9. Estado e retomada

Entregue agora: protocolo candidato e verificação local da allowlist/fontes do framework. Sem copiar resultados da preparação para corpus, sem executar COBOL/modelos/APIs, sem aprovar specs. Próximo gate: leitura e decisão de Researcher sobre P0; depois preparar os artefatos concretos de P1 em etapa autorizada.
