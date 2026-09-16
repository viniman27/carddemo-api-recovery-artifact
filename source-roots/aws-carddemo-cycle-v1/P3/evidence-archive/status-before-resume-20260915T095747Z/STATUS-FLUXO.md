# Estado do fluxo AWS

## Concluído

- Melhorias do framework candidato SDD.
- Coleta E1/zero-shot: três respostas originais.
- Coleta E2/few-shot: três respostas originais.
- Validação OpenAPI 3.1.0 das seis respostas: seis válidas, sem alteração de texto, remoção de fences, reparo semântico ou retry. Hashes de requisições e respostas conferidos. Evidência collection-01/validation.json; recibos individuais e streams preservados em collection-01/E1-* e E2-*.

Validade OpenAPI não atesta fidelidade ao COBOL, completude das obrigações ou operacionalização. Não houve análise semântica dos contratos nesta validação.

## SDD documental concluído; operacionalização em descoberta

- Estágios documentais 1, 2-r2, 3-r2, 4, 5, 6-r3, 7-r2 e 8 aprovados por registros estruturados em `sdd-runs/E3-01/reviews/`.
- Stage 8 aprovado em `reviews/stage-8-authorization.json` com escopo: fecha a cadeia documental SDD e permite descoberta pós-pipeline; não certifica testes executados nem validade runtime.
- Descoberta de prontidão operacional iniciada em `POST-PIPELINE-READINESS.md` sem executar COBOL, modelos, APIs, builds ou testes oficiais.
- Histórico anterior preservado abaixo; declarações antigas de pendência dos estágios 3–8 são superadas pelos registros estruturados atuais, não apagadas.

## Histórico SDD anterior preservado

- Estágio 1 aprovado.
- Estágio 2: primeira proposta restrita à postagem não aprovada, preservada.
- Revisão 2 gerada por gpt-6-astra por correção humana explícita; cobertura obrigatória de postagem, geração de juros e relatório em três trilhas provisórias.
- Artefato: sdd-runs/E3-01/specs/capability-selection-carddemo-r2/requirements.md.
- Evidência: sdd-runs/E3-01/STAGE2-R2-REVIEW-NOTE.md.
- Revisão 2 aprovada pelo usuário ('podemos seguir'); gate mecânico current, sem razões de bloqueio. Registro em reviews/stage-2-r2-authorization.json dentro de E3-01.
- Estágio 3 gerado nas três trilhas por gpt-6-astra; resposta original preservada. Verificação mecânica passou: 35 itens, 57 âncoras, 19 arquivos. Não prova completude/fidelidade semântica.
- Artefato: sdd-runs/E3-01/specs/legacy-evidence-carddemo/requirements.md; revisão pendente e ambiguidades explícitas em STAGE3-REVIEW-NOTE.md dentro de E3-01. Estágios 4–8 ainda não estavam autorizados neste ponto histórico.

## P2b técnico iniciado — fatia localhost full3track

- Criado apenas novo workspace `P2b/`, preservando P2a congelado, specs aprovadas, fontes e preparação.
- Implementada fachada localhost técnica para `POST /posting`, `POST /interest` e `POST /reporting`, alinhada ao contrato P2a, com diretórios isolados por invocação e auditoria INV/RES/CAP/CONV/FAIL/STATE/RESP.
- Smoke técnico local executado via GnuCOBOL sobre os três programas originais: `CBTRN02C`, `CBACT04C`, `CBTRN03C`; todos retornaram HTTP 200 no manifesto atual.
- QA local executada: `python3 -m unittest discover -s tests -v` OK; `python3 p2b_binding.py smoke` OK; `../P2a/.venv/bin/python validate_p2b.py` OK, com respostas validadas contra schemas P2a.
- Evidência principal: `P2b/readiness-manifest.json`, `P2b/schema-validation-report.json`, `P2b/command-log.jsonl`, `P2b/server-lifecycle.json`, `P2b/REPORT.md`.
- Limite preservado: isto é smoke técnico pré-teste, não T1/T2/T3/T4 oficial, não comparação, não oráculo semântico, não cobertura e não aprovação P2/P3.

## P2b auditoria final pré-teste

- Auditoria final P2b registrada em `P2b/FINAL-PRETEST-READINESS.md` e checklist JSON em `P2b/final-pretest-checklist.json`.
- Correção estreita adicional aplicada via TDD: registros significativos desconhecidos de `TRANREPT` não viram mais `200` vazio silencioso; agora são `500 technical_failure` com evidência de classificação.
- QA real após a correção: `python3 -m unittest discover -s tests -v` OK (9 testes); `python3 p2b_binding.py smoke` OK nos três tracks; `../P2a/.venv/bin/python validate_p2b.py` OK.
- Evidência anterior preservada antes do rerun em `P2b/evidence-archive/20260914T200843Z/archive-manifest.json`.
- Próximo gate concreto: P3 humano para congelar fixtures oficiais, reset/isolation, captura/conversão, oráculos, seeds/orçamentos/ordem/união T1-T4 e plano de análise. Smoke técnico não autoriza células oficiais.

## Não iniciado
- Testes AWS T1, T2, T3, T4.
- Comparação final.

## Revisão pontual do estágio 3

- Parecer aplicado a um novo request após autorização do usuário.
- Tentativa r2 interrompida pelo timeout local de 420 segundos, sem evento response.completed. Stream parcial preservado; não equivale a resposta concluída.
- Nenhum retry automático. Original preservado. Detalhes: sdd-runs/E3-01/STAGE3-R2-STATUS.md.

## Revisão do estágio 3 concluída na tentativa autorizada 3

- gpt-6-astra retornou completed; revisão r2 preservada em sdd-runs/E3-01/specs/legacy-evidence-carddemo-r2/requirements.md.
- R1–R6 tratados com distinção entre observação documental, dedução estática e hipótese de execução.
- Verificação mecânica: 35 itens, 57 âncoras, 19 arquivos; sem erros. Aceite humano pendente, estágio 4 bloqueado. Tentativas anteriores permanecem históricas.

## Estágio 4 gerado, revisão pendente

- Estágio 3-r2 aprovado pelo usuário; estágio 4 gerado com gpt-6-astra.
- Artefato: sdd-runs/E3-01/specs/capability-semantics-carddemo/requirements.md.
- 20 regras únicas e matriz reversa com os 35 itens E-n conferidos mecanicamente. Três trilhas mantidas. Revisão por contraexemplos e aceite humano pendentes; estágio 5 não autorizado.

## Próxima autorização

Revisar as evidências do estágio 3 nas três trilhas e dispor as ambiguidades bloqueantes antes de autorizar o estágio 4. Não iniciar downstream sem aceite explícito. Número de réplicas SDD ainda não congelado: não atribuir automaticamente três réplicas só porque E1/E2 tiveram três.

## Limites preservados

Referência de avaliação é candidata e deve ser adjudicada antes de servir como oráculo final. Preservar fontes, qualificação, V4 histórica e todos os resultados originais. Nenhuma API ou teste oficial está autorizado pelo mero sucesso de coleta/validação.

## P3 implementation preparation — non-executing

- Narrow P2b fix applied via TDD for `TRANREPT` mixed known+unknown meaningful captures: local binding now returns `500 technical_failure` with parsed public records retained in `availableContent`, and unknown raw report evidence retained in audit classifications.
- Pre-edit evidence preserved in `P2b/evidence-archive/20260914T204319Z/archive-manifest.json` before edits/rerun.
- Added P3 preparation-only configurable fixture/config interface: `P3/pretest_config.py`, `P3/fixture-registry.sample.json`, `P3/campaign-config.sample.json`, and `P3/tests/test_pretest_config.py`.
- QA actually run: P2b unit tests OK (10 tests); P3 config/schema tests OK (3 tests); `python3 p2b_binding.py smoke` OK on posting/interest/reporting technical tracks; `../P2a/.venv/bin/python validate_p2b.py` OK with `overall_passed=true`.
- Progress/evidence summary: `P3/IMPLEMENTATION-PROGRESS.md`.
- Limits preserved: this is API implementation and preparation-test infrastructure only; no official fixtures, oracle answers, model generations, E1/E2 comparisons, production services, or T1/T2/T3/T4 official executions. Budgets/seeds/model/oracle choices, real fixture registry contents, stateful sequences, and analysis denominators remain pending P3 human freeze.
