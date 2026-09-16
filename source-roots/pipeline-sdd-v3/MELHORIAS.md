# Matriz de melhorias — candidata v3

A lista abaixo reconcilia evidência recuperada com inspeção da base. Não é apresentada como transcrição integral de um backlog histórico: ele não foi localizado integralmente. `baseline/` contém os arquivos anteriores, com hashes em provenance.json. Nenhum documento histórico é alterado.

| ID | Evidência recuperada | Diagnóstico e ação da candidata | Aceite |
|---|---|---|---|
| M1 | Qualificação, `../casos/monografia-v4/tex/Apendice_CamadaIntermediaria.tex:79`; baseline `steering/pipeline.md:72,82`; template canônico §6 | Omissão histórica do ciclo de estado JÁ corrigida parcialmente na v2. Completar propagação no contrato, adaptador e validação; não anunciar §6 como novidade | Reset externo não vira endpoint inventado; estado é mapeado por recurso até o cenário |
| M2 | Baseline `steering/tech.md:52-55` pressupõe console/processo único; templates de semântica e adaptador não exigem ordem de persistência/repetição | Extensão nova para capacidades batch e multi-recurso, motivada pelas limitações da base e preparação AWS; não alegar backlog histórico recuperado | Falha parcial e retry incerto permanecem explícitos; nenhuma atomicidade/compensação inventada |
| M3 | Baseline template de escopo §1.2 admite referência sem política de visibilidade; preparação AWS STATUS-ATUAL §Entradas e isolamento | Manifesto de entradas visíveis por estágio; separar corpus, suporte e referência de avaliação; registrar exposição prévia | Material de teste conhecido não aparece como extração independente; exceções aprovadas são declaradas |
| M4 | Baseline `validation-principles.md:116` aceita fuzzer externo como exemplo de atestação; template usa hierarquia universal de oráculos | Corrigir distinção entre origem da ferramenta e independência da expectativa; autoridade depende da pergunta | Fuzzer externo guiado só pelo OpenAPI não atesta fidelidade ao COBOL; legado observado não define sozinho a obrigação desejada |
| M5 | Baseline tech/structure/RQs fixam caminhos, runtime e resultados antigos como contexto ativo | Separar framework, execução e estudo; parametrizar caminhos e ferramentas; manter histórico na base | Uso não escreve em `.sdd/` por acidente nem herda perguntas/resultados de outro caso |
| M6 | Baseline traceability §Mechanical anchor verification; `../casos/analise/ancoragem/verificar-ancoras.py:40,71-79` indexa fontes por basename e não restringe por manifesto | Empacotar verificador de âncoras estruturadas com caminhos completos relativos e SHA-256, sem alterar o script histórico | Homônimos não colidem, travessia/symlink/fora da allowlist falham; aprovação semântica nunca automática |

## Lote adicional autorizado — M7 a M9

Propostas apresentadas nesta sessão e autorizadas por Researcher; não atribuídas ao backlog histórico.

| ID | Lacuna | Implementação | Aceite |
|---|---|---|---|
| M7 | Rastrear afirmações não revela tudo que foi omitido | Inventário de comportamentos no estágio 3, enriquecido nos estágios 4–6 até cláusula/exclusão justificada/lacuna | Não exigir endpoint por parágrafo nem preencher decisões futuras; omissão sem destino é questionável no gate |
| M8 | Revisão podia concluir genericamente por coerência | Amostras de regra, ausência, efeitos persistidos e obrigação omitida com trecho/objeção/conclusão; N/A exige escopo e justificativa | Não inventar casos para completar tabela; amostra não prova completude |
| M9 | Aprovação podia permanecer aparente após mudança upstream | run_id/artifact_path/gate.review, hashes de artefato/autorização/specs upstream e verificador read-only recursivo | Mudança transitiva produz stale; metadados incompletos ou cadeia inválida não produzem current; ferramenta nunca aprova |

Evidências e limitações adicionais: `evidence/lote2/`. O parecer independente do lote anterior não cobre automaticamente estas alterações.

Já presentes e preservados: oito estágios, regras de ambiguidades, cenários de conformidade versus caracterização, reset canônico, custos/intervenções, gates humanos e revisão de dependências da suíte.

Fora deste lote: generalização do teste diferencial histórico (baseline steering/pipeline.md:108), medição gcov, novos geradores T1–T4, coleta AWS, definição da futura Fase 2 e edição retrospective. São fluxo/instrumentos, não motivos para alterar respostas da pipeline agora.

## Lote pós-Stage 9 — M10 qualidade/cobertura de testes

| ID | Lacuna | Implementação | Aceite |
|---|---|---|---|
| M10 | Depois de `api_ready_for_testing`, HTTP/schema e cobertura bruta podiam ser confundidos com qualidade semântica ou prontidão de campanha | Gate complementar em `pipeline/settings/templates/testing/` mais `pipeline/tools/check_test_quality_gate.py`; documentação integrada como pós-Stage 9, não Stage 10 | Denominador conhecido; all-not-executed não vira N/A; schema-only não qualifica negócio; oráculo independente exigido; reset por caso; T1/T2/T3/T4 separados; mutações não alteram fonte; saída da ferramenta não concede aprovação humana |

Este lote é genérico e não incorpora respostas CardDemo/AWS. Ele prepara a disciplina de teste para um run autorizado futuro, preservando specs/fonte/experimentos históricos.
