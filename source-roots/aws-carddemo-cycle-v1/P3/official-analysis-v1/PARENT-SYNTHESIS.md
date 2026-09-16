# Síntese parental e ressalvas de interpretação

Relatório oficial relido: SHA256 bdef12959aebfcf38f06e9e0720d7e211cdd66d9d7084043d1cfe496188e68aa. CSV case_rows.csv relido: 12.700 registros. Esta nota é adicional; não modifica relatório, manifestos ou resultados congelados.

## Conclusão

A campanha concluiu a aplicação dos estímulos e a verificação de respostas contratuais. Não concluiu validação independente das obrigações de negócio. Os 394 casos T3 têm expectativa inconclusiva. As 1.070 medições admissíveis são evidência de instrumentação/cobertura, NÃO 1.070 sucessos de validação semântica. A frase final da revisão independente que associa esse número à validação semântica deve ser lida com esta correção.

## Comparação sem duplicar T4

Recontagem parental de T1+T2+T3:

- zero-shot: N=2.887; HTTP 200=128; HTTP 400=0; HTTP 500=2.759.
- few-shot: N=2.861; HTTP 200=263; HTTP 400=1.730; HTTP 500=868.
- SDD: N=602; HTTP 200=143; HTTP 400=459; HTTP 500=0.

T4 é a reexecução dependente da união. Não somar suas ocorrências às anteriores para obter tamanho amostral independente. Nem identidades de requests que diferem em metadados/headers representam necessariamente diversidade de negócio. E1/E2 têm três contratos cada; SDD tem um. Volumes e superfícies diferentes impedem ranking causal por taxa HTTP.

Falhas de tokens locais em E1 mostram limitação da cadeia contrato–geração–mapeamento–infraestrutura, não isolam defeito de extração nem defeito COBOL. SDD mantém request público fechado {}, por isso sua ausência de 500 não prova superioridade funcional. A seleção externa e fixtures precisam ser consideradas na interpretação.

## Configuração efetivamente passada e metadado incorreto

O argv preservado em P3/campaign-execution-handoff-v2/REPORT.json, commands.executeParentTrackedOnlyAfterReadinessTrue, passa --config com campaign-configuration-v3/campaign-config-v3.json. O comando parental executou esse argv via os.execv; a inspeção posterior do processo 4477 também mostrou --config v3.

No runner aws-campaign-runner-v3/src/aws_campaign_runner.py, main carrega load_contract_registry(args.config) na linha 605. Porém prerequisite_report registra file_pin(CAMPAIGN_CONFIG), constante padrão v2, na linha 313. A discrepância é um defeito de proveniência no metadado do relatório: o campo não acompanha o argumento. Não corrigir retroativamente o relatório congelado. Interpretar v3 com a cadeia argv/processo/fonte e preservar a ressalva de que o relatório isolado mostra v2.

## Cobertura

As tabelas da análise unem linhas observadas em gcov, não fazem média de percentuais. Referem-se à instrumentação GnuCOBOL/GCC; não equivalem a cobertura de obrigações COBOL. Antes de usar diferenças pequenas como conclusão, conferir alinhamento dos fontes gerados/denominadores entre unidades compiladas e não apenas coincidência de números de linha. Ausência de auditoria do track corrente não é cobertura zero nem prova universal de ausência de execução.

## Fechamento

Execução e análise descritiva concluídas. A pergunta de continuidade funcional independente permanece aberta por falta de verificação de obrigação vinculada aos resultados. Um eventual complemento semântico deve ser explicitamente versionado, com autoridade e critérios definidos antes de avaliar novos resultados, sem reclassificar os casos atuais como se esse oráculo estivesse congelado desde o início. A pesquisa principal permanece fora do escopo desta intervenção.
