# Complemento de qualidade dos testes — estado consolidado

## Objetivo e autorização

Researcher autorizou implementar testes essenciais para uma validação defensável e registrar regras reutilizáveis no fluxo. O complemento é distinto da campanha congelada original e não é a futura Fase 2. Nenhuma conclusão pode retroativamente transformar a campanha original em validação semântica independente.

## Implementado e exercitado

- Catálogo complementar: `complementary-validation-v2/`, 25 obrigações, cenários-base e aplicabilidade. Cenário-base não equivale a todas as partições cobertas.
- Casos essenciais reais: `complementary-posting-essential-v1/` (6 casos), `complementary-interest-essential-v1/` (2 casos), `complementary-reporting-essential-v1/` (4 casos). Verificar o escopo das assertivas, não usar rótulos gerais de covered como prova da obrigação inteira.
- Verificadores com proveniência: `complementary-validation-implementation-v3/`; resultados ligados aos artefatos em `complementary-runner-binding-v1/`. Passes são ocorrências de verificações, não quantidade de obrigações únicas integralmente cobertas.
- Ligação ao modelo: `complementary-mbt-binding-v1/latest/candidate-registry.json`. Nove candidatos prospectivos T3; três casos auxiliares sem ligação MBT suficiente. Esta é qualificação posterior aos primeiros exemplos e não torna os resultados desses exemplos prospectivamente congelados.
- Integração dos sete contratos e três trilhas: `complementary-crossarm-v1/run-20260916T112642Z/`, 21 chamadas reais, sem alteração dos contratos. O campo businessCheck inicial era apenas observação de arquivos; NÃO usar como veredicto semântico.
- Semântica retrospectiva parcial: `complementary-crossarm-semantic-v1/`. Preserva distinção entre bytes internos e o que a API expõe.
- Juros: `complementary-interest-source-extractor-v1/` extrai TCATBALF/DISCGRP/ACCTFILE/XREFFILE de cópias dos recursos preservados e compara valores com cálculo derivado do fonte. Sete casos aprovados para a verificação aritmética exercitada; não cobre todas as taxas/sinais/limites possíveis. Testes parentais executados: 3 OK.
- Relatórios: `complementary-reporting-source-extractor-v1/` confere detalhes/representação com entradas reais e fontes. Sete casos aprovados no recorte de detalhes; totais não observáveis e caminho EOF de totais não exercitado nesses casos. Testes parentais executados: 4 OK.

## Limites que continuam abertos

- Não há nova campanha completa T1–T4 concluída com esses verificadores.
- T1/T2 permanecem os da campanha histórica. Casos manuais não foram rebatizados como LLM ou fuzzing. Novas chamadas externas T1 exigem pacote de entrada especificamente autorizado.
- Os casos essenciais variados ainda não foram todos aplicados aos sete contratos. A rodada cruzada exercitou um caso por operação, não todos os limites/exceções.
- Ordem interna de efeitos não é demonstrada por snapshots finais. Sem traço apropriado: inconclusivo.
- Limitações EOF observadas em juros e totais de relatório não são correção financeira; distinguir reprodução do legado de cumprimento de requisito de negócio.
- Comparações retrospectivas não substituem congelamento prospectivo de fixtures, extratores, autoridades e verificadores antes de uma nova campanha.
- Reexecuções de scripts de posting/reporting ocorreram na integração. Não contar como novas réplicas; preservar o fato e não afirmar que todo histórico desses diretórios é imutável.

## Regras incorporadas ao fluxo

No workspace, `pipeline-sdd-v3/pipeline/settings/templates/testing/test-quality-gate.md`, manifesto irmão e `pipeline/tools/check_test_quality_gate.py` definem o gate complementar após prontidão técnica da API, sem criar Stage 10 nem reabrir stages 1–9. Exigem autoridade do oráculo, contraexemplos, evidência de reset, denominadores e separação T1–T4. A aprovação mecânica do manifesto não é avaliação humana nem demonstração de suficiência semântica.

## Próxima fatia de execução

Aplicar as partições essenciais qualificadas à matriz dos sete contratos, com os verificadores agora disponíveis congelados antes da execução; registrar casos não expressíveis em vez de adaptar APIs. Manter partições não representadas no modelo como bateria auxiliar. T4 complementar deve derivar de conjuntos explicitamente identificados, sem misturar nova evidência com o freeze original. Antes de qualquer nova T1, fechar exatamente a informação entregue ao gerador e obter autorização de envio. Não apresentar cobertura percentual global de negócio enquanto os denominadores e a observabilidade das partições restantes não estiverem fechados.
