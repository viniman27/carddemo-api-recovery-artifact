# Resultado consolidado do complemento essencial

## Execução e verificações parentais

Matriz: 12 cenários essenciais aplicados aos sete contratos, 84 aplicações. Relatório executado: complementary-matrix-v2/parent-full84-v1/campaign/campaign-report.json. Inputs: complementary-matrix-v2/parent-plan-absolute-v1/. A configuração v3 foi atribuída explicitamente ao módulo no lançamento parental; não usar a constante padrão v2 como prova do argv efetivo.

84 concluídas, 84 respostas estruturalmente válidas, 78 medições admissíveis, seis sem auditoria associada (few-shot/reporting, agrupamento e paginação). Erro documentado estruturalmente válido não é sucesso de negócio.

A tarefa delegada de análise expirou; a execução parental recuperou e exercitou a versão complementar de análise v2. Comando de testes: P2a/.venv/bin/python -m unittest discover -s tests -v, no diretório complementary-matrix-analysis-v2; seis testes passaram. O comando python -m matrix_analysis aplicado ao report/freeze acima produziu parent-final-v1/, sem repetir APIs. Zero falhas de verificação de pins nessa análise.

## Cobertura estrutural — C gerado pelo GnuCOBOL

União apenas entre medições com mesmo fingerprint do fonte C e denominador. Não é percentual de obrigações COBOL.

| Programa | Linhas | Desvios tomados ao menos uma vez |
|---|---|---|
| Posting CBTRN02C | 686/1120, 61,25% | 200/288, 69,44% |
| Interest CBACT04C | 606/1029, 58,89% | 172/266, 64,66% |
| Reporting CBTRN03C | 763/1192, 64,01% | 180/272, 66,18% |

Branches executed é outra métrica gcov: não substitui branches taken>0. Para reporting few-shot isoladamente: linhas 655/1192 (54,95%) e desvios tomados 158/272 (58,09%). Não atribuir a cobertura da união inteira individualmente a cada braço.

## Semântica — recorte efetivamente conferido

- 63 casos aprovados nas assertivas implementadas.
- 13 inconclusivos.
- 8 falhas detectadas em totais de reporting, nos cenários de agrupamento e paginação em zero-shot/SDD. Não são oito defeitos independentes: são ocorrências de verificação da divergência.
- Posting: 42 aprovações do recorte verificado; Interest: 14 aprovações do recorte verificado; Reporting: 7 aprovações, 13 inconclusivos, 8 falhas.
- O caso de última conta em interest documenta comportamento do legado; sua aprovação não prova que todas as contas tiveram atualização financeiramente desejável.
- Os passes não fecham todas as partições das 25 obrigações. Ordem interna, determinadas falhas de I/O, sinais/limites e observações públicas insuficientes continuam fora das conclusões.

## Julgamento de encerramento

Este complemento é útil para validação focada nas situações essenciais selecionadas e revelou divergências reais; não está demonstrada cobertura ideal, exaustiva ou validação integral do negócio. Repetir casos ou corrigir COBOL/APIs para obter mais passes seria incompatível com o objetivo experimental.

T1/T2 históricos não foram regenerados; a matriz é source-guided complementar, não uma nova campanha completa T1–T4. Nove cenários foram qualificados como candidatos prospectivos MBT; os demais continuam auxiliares. Checkers adicionais aplicados depois da execução são análise retrospectiva explicitamente identificada, não devem ser apresentados como oráculo congelado originalmente.

A documentação genérica de qualidade já está integrada em pipeline-sdd-v3/pipeline/settings/templates/testing/test-quality-gate.md e no verificador pipeline/tools/check_test_quality_gate.py. Não é Stage 10 e não altera a pesquisa principal.

## Evidência

- complementary-matrix-coverage-v1/evidence/current/PTBR-RELATORIO-COBERTURA.md e coverage-summary.csv.
- complementary-matrix-analysis-v2/parent-final-v1/PTBR-ANALISE.md, actual84-semantic-analysis.json e actual84-cases.csv.
- COMPLEMENTO-ESTADO-ATUAL.md preserva a cronologia anterior; este documento consolida os resultados posteriores sem reescrever os relatórios experimentais.
