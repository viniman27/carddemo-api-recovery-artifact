# Entrada restrita para referência de avaliação

Este pacote contém apenas fontes originais autorizadas, layouts, JCL/procedimento e licença. Todos os arquivos em corpus foram conferidos contra os pins do manifesto de origem e após a cópia. Não contém um modelo ou resultados esperados prontos.

## Trabalho do autor em contexto separado

Ler somente este README, input-manifest.json e arquivos enumerados em corpus. Não explorar o diretório pai, memórias de resultados, contratos avaliados, documentos SDD, adaptadores, suporte, fixtures técnicas, runs ou quarentena. A localização em um diretório separado não é sandbox; a exposição efetiva precisa ser registrada pelo executor.

Produzir uma referência da capacidade para CBTRN02C/POSTTRAN, CBACT04C/INTCALC e CBTRN03C/TRANREPT, mantendo rastreabilidade individual. Para cada obrigação: identificador, fonte/intervalo de linhas/hash, pré-condição, transição/guarda, observação necessária, expectativa sustentada e limites. Distinguir evidência estática, dedução e hipótese dependente de ambiente.

Produzir modelo explícito com estados, transições, guardas e critérios de seleção de caminhos. Explicitar laços e fronteiras do modelo. Não inventar escala monetária, arredondamento, calendário, atomicidade, durabilidade, efeitos persistidos após falha ou comportamento de EOF. Quando a autoridade não permite uma expectativa decidível, registrar a lacuna em vez de preencher com conveniência.

Não executar código para descobrir a resposta e depois apresentá-la como expectativa prévia. Não adaptar o inventário às operações dos contratos avaliados; o mapeamento para cada superfície ocorre depois e não pode apagar obrigações ausentes. JCL é evidência documental, não alegação de execução local.

## Revisão posterior

Um revisor separado deve buscar contraexemplos diretamente nas fontes, conferir as âncoras e rejeitar expectativas não sustentadas. Novo contexto controla exposição, mas não garante independência do modelo nem elimina ameaças de conhecimento prévio. Registrar autor, revisor, entradas realmente entregues e intervenções.

Status: pacote de entrada preparado; autoria, revisão e congelamento da referência ainda não executados. Não autoriza campanha ou exportação de dados privados.
