# Método, reprodução e autorização da continuidade

## Autorização efetivamente recebida

Mensagem do usuário nesta sessão: “sobre t1, autorizo, de resto pode prosseguit tambem. pergunta, a geracao desses testes e e devidas acoes e revisoes, sao no geral deterministicas ne? digo, meu fluxo preve as acoes que estamos tomando”.

A autorização responde à pergunta específica: novo probe omitindo somente previous_response_id e, se passar, sete envios T1 via openai-codex/gpt-6-astra, mesmos prompts/escopo, sem retry/fallback/model switch. Permite continuidade da preparação local. Não registra assinatura, revisão humana dos novos artefatos nem autorização de campanha: permanece o gate separado de apresentar fechamento e obter autorização explícita.

## Determinismo não é sinônimo de controle metodológico

T1 é geração LLM não determinística. Prompts/modelo fixados não garantem resposta idêntica; preservar saída real e congelar casos, não regenerá-los para replay.

T2 é geração pseudoaleatória: seeds e versões sustentam reprodução no ambiente fixado, não identidade universal. Requests preparados congelados são a entrada do replay. IDs e repetições não são diversidade de dados de negócio.

T3 pode selecionar deterministicamente caminhos sob modelo, ordem lexicográfica, limites, mapeamento e recursos fixados. A construção/revisão do modelo e da autoridade de guarda envolve julgamento. PASS de seleção abstrata não prova equivalência COBOL ou satisfação de obrigação.

T4 é união dependente com identidade, multiplicidade/duplicatas e ordem fixadas, seguida de execução nova com reset. Não é réplica independente. Mesmo com casos fixados, timestamps e comportamento do ambiente podem variar; bytes brutos devem permanecer preservados.

## Aderência ao fluxo

PROTOCOLO.md, seções 4–7, prevê operacionalização, adaptação documentada, modelo/referência revisados, congelamento de entradas/budgets/seeds/reset/união e autorização anterior à campanha. Seu texto de estado inicial é histórico e não descreve o estado atual do ciclo.

Bugs concretos de implementação não eram etapas experimentais previamente especificadas. Corrigir perda de query, substituição indevida de schema ou filtro restrito ao relatório restaura o comportamento pretendido; registrar versões rejeitadas e intervenções de preparação. Não contar esses testes de infraestrutura como resultados da campanha.

Mudanças que alterem estímulos, orçamento, elegibilidade, fixture, expectativa ou seleção não são automaticamente neutras: devem ser explicitadas e fixadas antes dos resultados. Nenhuma revisão automatizada constitui inspeção humana. O ciclo AWS não é a futura Fase 2.
