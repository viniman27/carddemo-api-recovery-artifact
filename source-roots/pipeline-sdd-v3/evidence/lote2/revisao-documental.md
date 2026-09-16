# Revisão documental — lote 2

Escopo: leitura documental da pipeline candidata para verificar se as novas instruções de completude reversa e revisão por contraexemplos tornam duas omissões sintéticas visíveis antes da aplicação AWS. Não houve execução de corpus, AWS, COBOL, modelos externos, aprovação humana ou fechamento de gate experimental.

## Contraexemplo 1 — falha com efeito persistido omitido

- **Leitura sintética**: Stage 3 registra uma operação batch que grava um registro de saída antes de rejeitar o item seguinte; Stage 4 descreve apenas “item inválido é rejeitado”; Stage 6 promete resposta de erro sem dizer se efeitos anteriores persistem.
- **Trecho exercitado**: `capability-semantics-spec.md` agora exige revisão registrada para “failure with persisted effects”; `api-contract-spec.md` exige que efeitos de falha e restrições de repetição sejam derivados, não inventados, e que a matriz dê destino a cada comportamento relevante.
- **Objeção**: uma leitura focada só no endpoint poderia tratar erro como rollback implícito ou retry seguro, embora a evidência só mostre persistência parcial.
- **Conclusão documental**: a omissão deixa de passar silenciosamente: deve virar regra/ambiguidade/gap na Stage 4, tratamento de fronteira na Stage 5 e cláusula/exclusão/gap na Stage 6. A amostra não prova que todos os casos similares serão encontrados.

## Contraexemplo 2 — ausência alegada nas dependências e obrigação omitida

- **Leitura sintética**: Stage 4 afirma “não há identificador externo” porque o programa principal não mostra parâmetro de conta; uma copybook/dependência ou arquivo de controle poderia carregar a identidade, e o contrato resultante omite uma obrigação de inicialização/seleção de contexto.
- **Trecho exercitado**: `design-review.md` agora exige registro de “claimed dependency absence” e “omitted obligation” com trecho, objeção e conclusão; `traceability.md` orienta seguir operação/regra/efeito de evidência até destino contratual ou exclusão justificada.
- **Objeção**: “não encontrado no arquivo lido” não equivale a “não existe”; a ausência precisa declarar quais dependências foram examinadas e qual lacuna permanece.
- **Conclusão documental**: a revisão deve aceitar, refinar ou abrir lacuna explicitamente, distinguindo ausência examinada de inexistência. A amostra é orientada ao risco e não substitui revisão integral nem aprovação humana.

## Limites

- Evidência produzida por leitura dos templates e regras, sem execução AWS e sem validação sobre CardDemo.
- Dois contraexemplos sintéticos exercitam a nova disciplina, mas não estabelecem completude global.
- A revisão própria documenta plausibilidade metodológica; não é revisão independente nem aceite de Researcher.
