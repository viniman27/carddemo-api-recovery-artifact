# Desenho de validação complementar v1 — AWS CardDemo

## Escopo

Este complemento existe porque a campanha oficial demonstrou execução estrutural, mas não fechou validação independente das obrigações de negócio. O pacote é prospectivo: congela critérios antes de novos resultados e não reclassifica os 12.700 casos históricos como se já tivessem oráculo semântico.

Fora do escopo: pesquisa principal, edição de artefatos congelados, nova campanha, chamadas externas, melhoria silenciosa de outputs T1/modelo, leitura de quarentena de expected outputs como autoridade.

## Papéis T1–T4

| Condição | Papel no complemento | Limite |
| --- | --- | --- |
| T1 | Gerar estímulos de cenário por LLM quando houver autorização explícita de input/provedor. | Estímulo, não oráculo. Não reaproveitar outputs melhorados após resultado. |
| T2 | Explorar robustez/schema pela superfície OpenAPI congelada. | Não prova fidelidade COBOL; domínio gerado pelo contrato é dependente do contrato. |
| T3 | Bateria de validação independente por obrigações: cada caso precisa declarar obrigação, fonte, guarda, observação e autoridade de expected result. | Obrigações não expressíveis continuam no denominador como `unobservable`. |
| T4 | União dependente dos casos T1/T2/T3 qualificados, com deduplicação e ordem congeladas. | Não cria casos novos e não é réplica independente. |

## Denominadores congelados para o catálogo

- Obrigações: 25.
- Contratos: 7.
- Operações: 21.
- Células obrigação×operação: 525.
- Células aplicáveis por trilha: 175.
- Células não aplicáveis por trilha: 350.
- Resultado antes de nova execução: achieved=0, failed=0, unobservable=525.

Na análise futura, cada denominador deve aparecer separado por: obrigação, operação, contrato, braço, condição, trilha e autoridade do oráculo. Ausência de observabilidade não pode virar zero funcional.

## Gates de qualificação de oráculo

1. `OQ-1`: expected value só é admissível com autoridade anterior ao resultado e fonte/revisão independente.
2. `OQ-2`: guarda/ramo e valor de saída são denominadores diferentes.
3. `OQ-3`: T1/LLM e contrato OpenAPI não são autoridade independente do comportamento COBOL.
4. `OQ-4`: obrigação bloqueada ou não expressível permanece no catálogo e no relatório.

## Gates de integração

1. `IG-1`: revalidar 7 contratos e 21 operações em `campaign-config-v3`.
2. `IG-2`: revalidar 25 obrigações e anchors contra `../aws-carddemo-preparation/research-corpus`.
3. `IG-3`: congelar fixtures/checkers/suites antes de observar novos resultados.
4. `IG-4`: T4 deve ser derivado apenas de T1/T2/T3 já qualificados; sem geração independente.
5. `IG-5`: relatório final deve declarar achieved/failed/unobservable e razões de inadmissibilidade, não só HTTP/gcov.

## Exemplos fonte-ancorados por trilha

### Posting

Exemplo `EX-POSTING-001`: obrigações `POSTTRAN-OBL-004`, `POSTTRAN-OBL-006`, `POSTTRAN-OBL-007`. A fonte permite propor casos que selecionem cartão ausente/presente, rejeição e atualização/criação de TCATBAL. O catálogo não inventa bytes finais de `TRANFILE`/`DALYREJS`; isso exige oráculo revisado.

### Interest

Exemplo `EX-INTEREST-001`: obrigações `INTCALC-OBL-003`, `INTCALC-OBL-004`, `INTCALC-OBL-005`. A fonte permite separar lookup ACCOUNT/XREF, taxa específica/DEFAULT e guarda de taxa zero. Fórmula e bytes de transação de juros só entram como expected result depois de qualificação independente.

### Reporting

Exemplo `EX-REPORTING-001`: obrigações `TRANREPT-OBL-002`, `TRANREPT-OBL-004`, `TRANREPT-OBL-006`. A fonte permite selecionar janela DATEPARM e lookups de relatório. Formatação editada, paginação e totais permanecem com denominador próprio; não são inferidos de HTTP 200.

## Ameaças registradas antes de novos resultados

- Confundir resposta estrutural/schema-valid com sucesso funcional.
- Usar gcov admissível como proxy de obrigação satisfeita.
- Tratar T4 como amostra independente.
- Comparar volume de casos entre braços como qualidade causal.
- Corrigir T1 ou modelo depois dos resultados e chamar de mesmo experimento.
- Omitir obrigações bloqueadas por não expressibilidade.

## Próximo passo autorizado por este pacote

Somente decisão/gate: revisar `scenario-catalog.json` e aprovar ou alterar a autoridade de oráculo por obrigação. Implementação de bateria executável é uma versão posterior.
