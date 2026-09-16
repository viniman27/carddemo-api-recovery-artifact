# Extensão empírica local retrospectiva — resultado verificado

## Estado e escopo

Concluída a extensão retrospectiva delimitada, com limitações abaixo. Saída de referência: `run-04/`. Não foram reexecutadas APIs ou programas de negócio. Nenhuma alteração de pesquisa principal, COBOL, contratos, APIs, pipeline ou Fase 2; nenhuma chamada externa ou publicação. Expectativas novas são retrospectivas, não oráculos originalmente congelados.

`verify_results.py` executou com exit code 0. Conferiu 12.700 aplicações oficiais, 84 complementares, 8.910 pins de entrada, 2.350 pins externos também presentes em run-03 e 16 fontes/copybooks ancorados no catálogo. Zero divergências nessa preservação. O hash do relatório oficial permanece `bdef12959aebfcf38f06e9e0720d7e211cdd66d9d7084043d1cfe496188e68aa`.

O gerenciador de processos retornou exit code null para run-04; não foi usado como prova de sucesso. O fechamento se baseia na leitura dos arquivos completos, recontagem independente e execução bem-sucedida de verify_results.py.

## 1. O que mudou na verificação

Posting: comparação dos campos postados, quantidade de registros, bytes dos rejeitos, motivo e return-code; comparação integral de ACCOUNT antes/depois; valores e chaves de TCATBAL; XREF inalterado. Nas rejeições disponíveis, não se observou alteração indevida de ACCOUNT/TCATBAL. Não se infere ordem interna nem rollback. TRANFILE usa OPEN OUTPUT: preservar conteúdo anterior não é uma obrigação assumida.

Juros: fórmula truncada em centavos, ordem/multiplicidade e campos estáveis das transações; estado integral das contas, incluindo saldo e créditos/débitos do ciclo. Duas perguntas separadas: o resultado reproduz o legado? Todas as contas percorridas receberam a atualização financeira? A segunda não é reclassificada como pass por reproduzir um defeito.

Reporting: leitor indexado em cópias para XREF/tipos/categorias; todos os detalhes e toda a sequência de subtotais/totais, incluindo grand total, preservados em lista. O verificador anterior retinha somente o último total de cada tipo e não confrontava o grand total. A verificação nova acompanha o contador de linhas/paginação e as quebras de cartão; não compara cada subtotal com o total global.

Exclusões justificadas pelo fonte: timestamps gerados; filler TCATBAL 28:50; cauda da descrição de juros 56:132 não atribuída pelo STRING. Bytes brutos permanecem preservados. As diferenças desses bytes encontradas em run-03 eram expectativas indevidas do novo verificador, não defeitos financeiros. As correções não apagaram run-03.

## 2. Resultados complementares por efeito

| Operação | Aplicações | Resultado delimitado |
|---|---:|---|
| Posting | 42 | Seis verificações por aplicação: 252 passes parciais. Inclui aceitação e quatro motivos de rejeição; estado de contas/categorias conferido. |
| Juros | 14 | 14 passes em transações; 14 passes na reprodução do estado legado; 14 falhas na expectativa financeira de atualização de todos os grupos, incluindo a última conta. |
| Reporting com auditoria | 22 | 22 passes em sequência de eventos do legado e 22 em detalhes. Totais financeiros: 8 falhas; 14 não exercitados. |
| Reporting rejeitado antes do COBOL | 6 | Sem verificação de negócio. Rejeição numérica da validação de schema identificada abaixo. |

Total: 360 verificações, com 324 passes, 22 falhas e 14 não exercitadas, distribuídas por 78 aplicações observáveis; outras seis aplicações não chegaram a uma auditoria de negócio. Verificações não são casos, nem obrigações completas. Não comparar 324 com os 63 passes de casos da análise anterior.

As 22 falhas financeiras agrupam-se em duas classes sustentadas pelo fonte: ausência de atualização final em juros e soma residual no EOF de reporting. Não são 22 defeitos independentes. O comportamento do programa permanece inalterado.

Reporting por situação: agrupamento produz Page/Grand Total 15,54 contra 11,10 de detalhes; paginação produz último Page Total 5,89 contra 4,70 e Grand Total 23,09 contra 21,90. Esses resultados são reproduzidos nos três contratos zero-shot e no SDD. O primeiro subtotal de página e o subtotal de grupo são preservados e verificados separadamente.

Comparação entre braços: posting possui seis situações comuns aos sete contratos; juros possui duas. Em reporting, os seis bloqueios few-shot impedem comparação de totais entre todos os sete contratos nas situações de agrupamento e paginação. Nas duas situações de reporting exercitadas por todos os contratos, os totais não foram exercitados. Não há base para ranking de fidelidade financeira entre braços por taxa HTTP.

## 3. Os seis bloqueios few-shot

Os requests e respostas reais foram confrontados com `http-rejections.jsonl`, com vinculação de PID, contrato e rota. Os seis retornaram HTTP 400 e `{}`. O validador em ponto flutuante rejeitou números como 1.11 como não múltiplos de 0.01. O contracheque local dos mesmos schemas/requests com Decimal não produziu erros nos seis casos.

Conclusão: limitação da implementação da validação numérica antes do COBOL, não ausência inexplicada de coleta nem proteção superior da interface. O contracheque não reexecutou as APIs, não reparou a fachada e não transforma os seis em passes de negócio. Evidência: `fewshot-diagnosis.json` e `diagnose.py`.

## 4. Informação adicional da campanha oficial

12.700 aplicações incluem T4. Há 1.070 aplicações com negócio observado pela auditoria vinculada. O verificador retrospectivo produziu assertivas em 1.002 delas: 3.406 passes parciais e 428 verificações não exercitadas. Isso NÃO valida integralmente 1.002 casos.

Limitações restantes nas 68 aplicações observadas sem assertivas: 58 DATEPARM curtos/vazios sem modelo qualificado para esse caminho; oito valores DISPLAY assinados fora da qualificação atual; duas saídas anormais fora do oráculo de caminho de sucesso. Não são falhas do COBOL estabelecidas pela análise. As demais 11.630 aplicações não possuem auditoria de negócio vinculada; essa ausência não autoriza inferir universalmente que nada foi executado.

| Condição | Aplicações | Negócio observado | Com assertivas novas | Entradas/estados distintos, dentro de contrato/operação |
|---|---:|---:|---:|---:|
| T1 | 88 | 20 | 16 | 19 |
| T2 | 5.868 | 177 | 147 | 103 |
| T3 | 394 | 338 | 338 | 17 |
| T4 | 6.350 | 535 | 501 | 126 |

T4 é replay dependente da união. T1/T2/T3 somam 6.350 aplicações, não 12.700 réplicas independentes.

A união contém 126 pares contrato/operação/entrada-estado. As contribuições exclusivas são T1=9, T2=93, T3=14. Na ordem explicitada T1→T2→T3, os incrementos são 19, 93 e 14. T1 e T2 compartilham 10 situações; três situações aparecem nas três condições. O conjunto observado em T4 coincide com a união, sem situações adicionais. Deduplicando também entre contratos, há 107 entradas/estados lógicos distintos, não 107 comportamentos demonstrados.

As identidades vêm da suíte congelada envolvente, não do nome/aparência de cada caso. O fingerprint usa inputs efetivamente materializados, dumps lógicos e estado prévio com hash verificado; exclui UUID/request_identity e fillers conhecidos. É uma medida conservadora de diversidade de entrada/estado, não uma prova de equivalência comportamental: campos distintos podem conduzir ao mesmo caminho. Entradas sem estado recuperável não entram como situações conhecidas.

## 5. Qualificação dos verificadores

15 testes automatizados passaram. A qualificação sintética contém 35 sondas: 30 contraexemplos dentro das assertivas-alvo, todos detectados; quatro ausências corretamente inconclusivas; uma modificação de timestamp excluído não detectada, explicitamente mantida como ponto cego.

Classes: valores incorretos do mesmo tamanho, omissão, duplicação, reordenação, registro parcial, vazio inesperado, saldo não atualizado, ciclo não zerado, primeiro/último subtotal incorreto, grand total incorreto e deslocamento de fronteira monetária/data. Fronteiras qualificam o verificador; não demonstram que novas aplicações COBOL foram executadas nessas fronteiras.

É uma amostra pequena e deliberada de erros de saídas/estados, não mutation score do programa nem sensibilidade universal. Não foi medida sensibilidade experimental equivalente dos verificadores antigos; suas limitações foram inspecionadas no código. Não houve mutação de programa, fault injection nem novo experimento metamórfico.

## 6. Denominadores e limites

Catálogo: 25 obrigações × sete contratos = 175 células aplicáveis por condição. O ledger novo tem 875 células: quatro condições oficiais mais a faixa complementar separada. Células sem aplicações permanecem `not_executed`; nenhuma obrigação é declarada integralmente validada. O CSV de obrigação-partição traz contexto de partição e efeito específico, não afirma que cada assertiva fecha todas as partições listadas.

Há 10.308 linhas de ligação assertiva–obrigação no ledger de partições; a mesma assertiva pode contribuir a mais de uma obrigação. Esse número não é cobertura nem quantidade de observações independentes.

Auditorias zero-shot têm pins na árvore de aplicação. Few-shot/SDD mantêm auditorias fora dela: o vínculo foi conferido pelo caminho registrado, identificador de invocação, track e cwd do comando; outputs são confrontados com snapshots/capturas históricos do audit. O hash do próprio audit externo não estava congelado naquela árvore. Esta diferença de força de proveniência permanece explícita.

A análise é posterior aos resultados; fonte compartilhada com o objeto; implementador e qualificador não independentes; caso único, sete contratos sem independência estatística presumida; nenhuma significância inferida. Assinatura negativa/overflow e falhas de I/O continuam lacunas. Não existe autorização implícita para ampliar o escopo na Fase 2.

## 7. Reprodução e arquivos

A partir deste diretório:

    PYTHONDONTWRITEBYTECODE=1 ../../P2a/.venv/bin/python -m unittest -v
    PYTHONDONTWRITEBYTECODE=1 ../../P2a/.venv/bin/python diagnose.py
    PYTHONDONTWRITEBYTECODE=1 ../../P2a/.venv/bin/python qualify.py
    PYTHONDONTWRITEBYTECODE=1 ../../P2a/.venv/bin/python verify_results.py

Para uma nova reprodução SOMENTE da análise, use um diretório de saída inexistente; não sobrescreva run-04:

    PYTHONDONTWRITEBYTECODE=1 ../../P2a/.venv/bin/python analysis.py --out reproduction-new-id

Artefatos: `run-04/{summary.json,applications.csv,observability.csv,obligation-coverage.csv,obligation-partition-checks.csv,strategy-contribution.csv,source-pins.json}`, `oracle-qualification.json`, `oracle-sensitivity.csv`, `fewshot-diagnosis.json`, `FINAL-VERIFICATION.json`. JSONL por aplicação preserva os detalhes de falhas/limites.

Tentativas preservadas: run-01 (body ausente), run-02 (metadado de condição), run-03 (análise completa porém inadequada para few-shot/SDD e bytes não atribuídos), run-04 (referência verificada). Nenhuma dessas tentativas repetiu o experimento de negócio.

## 8. Uso na redação

O achado defensável é a distância entre conformidade HTTP, diversidade de entradas e evidência financeira observável, com contribuição complementar das estratégias e uma camada de verificação source-derived. Não é superioridade causal do SDD.
