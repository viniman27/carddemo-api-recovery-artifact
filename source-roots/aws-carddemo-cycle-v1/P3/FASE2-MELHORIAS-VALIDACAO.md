# Melhorias de validação para eventual Fase 2

Status: backlog proposto a pedido de Researcher; não é execução nem aprovação de gate da Fase 2. O estudo público AWS é separado da futura Fase 2. Este registro não modifica a pesquisa principal.

## Princípio

Objetivo principal: continuidade funcional da capacidade entre legado, contrato/API e backend moderno, segundo objetivo de negócio e obrigações observáveis. Não exigir equivalência interna/formal. Separar reprodução do legado de correção de negócio; comportamento suspeito não se torna regra desejada por existir no fonte. Registrar autoridade e incerteza de cada expectativa.

## Melhorias propostas e critérios de evidência

1. Decompor obrigações em partições de entrada, estado, fronteira, rejeição e falha operacional. Registrar aplicabilidade, criticidade e denominadores antes da execução. Fechamento exige contabilização de todas as partições obrigatórias, não todos os testes passando.
2. Definir referência independente do gerador e do backend em avaliação. Regras desejadas precisam de autoridade documental ou validação de domínio; quando ausente, registrar hipótese, não inventar aprovação humana.
3. Assegurar observabilidade: estado antes/depois, bytes, ordem, multiplicidade, missing versus empty e auditoria vinculada à invocação. Ordem interna só deve ser requisito quando sustentada pela obrigação; comparar backends por efeitos observáveis.
4. Qualificar reset físico e seleção externa de fixtures, incluindo componentes de arquivos indexados; provar diferença efetiva entre situações e isolamento entre execuções.
5. Investigar falhas controladas de OPEN/READ/WRITE em sandbox. Avaliar viabilidade sem alterar semântica do programa; preservar baseline, registrar instrumentação e verificar interferência. Não executar injeções em ambiente real/institucional.
6. Expandir qualificação de oráculos com contraexemplos de mesmo tamanho, omissão, duplicação, reordenação, saldos incorretos e limites deslocados. Se adotada mutação de programa, usar somente cópias isoladas; separar inválidos, equivalentes, mortos, sobreviventes e não observáveis; não confundir mutação de saídas com mutation score do programa.
7. Aplicar propriedades metamórficas justificadas (não pressupor linearidade quando houver truncamento, arredondamento, ordem ou EOF). Preservar relações esperadas antes da execução.
8. Na comparação COBOL/backend moderno, aplicar entradas e estados semanticamente correspondentes; distinguir limitações da interface, falhas do binding, defeitos do legado, defeitos do backend e incerteza do oráculo.
9. Manter GnuCOBOL+gcov como cadeia principal. Usar cobertura de código como explicação auxiliar; comparar/ unir apenas fontes e denominadores compatíveis. Não reabrir gcobol/emulação por padrão.
10. Preservar papéis T1/LLM, T2/OpenAPI, T3/MBT e T4/união dependente; bateria source-guided compartilhada permanece separada. Congelar mudanças prospectivas sem reescrever resultados históricos.

## Lições AWS a transferir como hipóteses, não pressupostos universais

Investigar última conta/EOF e atualização de saldos; totais de relatório versus detalhes; limites de datas/paginação; rejeição sem efeito indevido; sinais, magnitudes e limites monetários; falhas de I/O e efeitos parciais. Os nomes/IDs CardDemo não devem entrar como respostas no framework genérico.

## Saída esperada quando a Fase 2 for autorizada

Matriz obrigação-partição-backend, expectativas com autoridade, snapshots/reset, checkers qualificados, resultados por efeito, divergências reproduzíveis, cobertura auxiliar e ameaças à validade. Nenhum percentual isolado é aprovação funcional.
