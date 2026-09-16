# Ledger final de cobertura defensável

Gerado por script sobre evidências salvas em 2026-09-16T12:00:41.139891+00:00. Não executa API, COBOL, modelo externo ou quarentena.

## Tabela executiva

| Métrica | Valor |
|---|---:|
| Obrigações de negócio | 25 |
| Contratos | 7 |
| Denominador semântico (obrigação×contrato aplicável) | 175 |
| Denominador bruto ilustrativo (não usar como semântico) | 525 |
| Células N/A fora do denominador | 350 |

## Estados no denominador semântico

| Estado | Células |
|---|---:|
| coberto e checado | 14 |
| falhou | 0 |
| inconclusivo | 28 |
| não exercitado | 133 |
| não observável | 0 |

## Por trilha

| Trilha | coberto | falhou | inconclusivo | não exercitado | não observável |
|---|---:|---:|---:|---:|---:|
| interest | 7 | 0 | 7 | 42 | 0 |
| posting | 7 | 0 | 7 | 49 | 0 |
| reporting | 0 | 0 | 14 | 42 | 0 |

## Gcov alinhado por fingerprint do C gerado

| Programa | Comparabilidade | Linhas | Branches executados | Observação |
|---|---|---:|---:|---|
| CBACT04C | mesmo fingerprint | 585/1029 | 214/266 | somável apenas dentro desta série |
| CBTRN02C | mesmo fingerprint | 651/1120 | 246/288 | somável apenas dentro desta série |
| CBTRN03C | mesmo fingerprint | 655/1192 | 216/272 | somável apenas dentro desta série |

## Lacunas decisivas

| Rank | Obrigação | Células afetadas | Motivo |
|---|---|---:|---|
| alta | POSTTRAN-OBL-008 | 7 | partição de valor negativo/débito de posting ainda precisa evidência primária por contrato para alegação financeira |
| média | POSTTRAN-OBL-001 | 7 | falhas de OPEN/READ/WRITE são fault-injection; documentar como indisponíveis se não executáveis sem adulterar ambiente |
| alta | INTCALC-OBL-002 | 7 | última conta/EOF de juros bloqueia afirmação de atualização final de todas as contas |
| alta | TRANREPT-OBL-002 | 7 | totais/paginação/final account do relatório não sustentam alegação financeira global |
| média | TRANREPT-OBL-001 | 7 | fronteiras de datas e paginação precisam permanecer por campo/partição, não por obrigação inteira |
| baixa | INTCALC-OBL-001 | 7 | Data do JCL é exemplo de fonte, não calendário universal. |
| baixa | INTCALC-OBL-003 | 7 | Índice alternativo é evidenciado no JCL, mas ambiente VSAM não é executado. |
| baixa | INTCALC-OBL-004 | 7 | Sem fallback adicional. |
| baixa | INTCALC-OBL-005 | 7 | Arredondamento/truncamento/overflow dependem de PIC/compilador; não fixado. |
| baixa | INTCALC-OBL-007 | 7 | Não é update por cada categoria. |
| baixa | INTCALC-OBL-008 | 7 | Achado estático; não confirmado por execução. Para arquivo vazio, não assumir conta carregada. |
| baixa | POSTTRAN-OBL-002 | 7 | Não assumir retenção de último registro no EOF nem conteúdo observável do buffer após status 10. |
| baixa | POSTTRAN-OBL-004 | 7 | Não há validação de formato além da busca. |
| baixa | POSTTRAN-OBL-005 | 7 | Comparação de datas é textual X(10); calendário real não é decidido. |
| baixa | POSTTRAN-OBL-006 | 7 | Não afirma rollback de sucessos anteriores. |
| baixa | POSTTRAN-OBL-007 | 7 | Status aceitos 00/23 no read; sem atomicidade/durabilidade. |
| baixa | POSTTRAN-OBL-009 | 7 | Não confundir ordem de chamadas com commit/durabilidade; estado externo pós-abend é fora de autoridade. |
| baixa | TRANREPT-OBL-003 | 7 | Não assumir retenção de último registro no EOF nem conteúdo estável do receiver. |
| baixa | TRANREPT-OBL-004 | 7 | Não há linha de erro/rejeição para lookup ausente. |
| baixa | TRANREPT-OBL-005 | 7 | Page-size conta linhas de header/totais; não é 20 detalhes. |

## Critério de parada bounded

Parar a contabilização desta versão aqui: a saída congela o denominador aplicável atual, separa evidência original/suplementar e registra lacunas. Novas matrizes devem ser agregadas por novo comando/artefato, não por reinterpretação manual deste relatório.
