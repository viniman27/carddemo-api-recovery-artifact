# Registro de mudanças — candidata v3

## Escopo corrigido

Renomeado `pipeline-draft/` para `pipeline-sdd-v3/`. O ciclo atual é revisão da pipeline seguida de aplicação AWS quando autorizada. Não é a Fase 2; ela usará outros códigos e poderá usar outra versão. Nenhuma mudança à qualificação, V4 congelada ou COBOL.

## Implementado na candidata

- M1: propagação de estado/reset do canônico ao contrato, adaptador e plano de validação. O campo canônico de estado já existia na v2; a novidade é o fechamento dos elos posteriores.
- M2: requisitos explícitos para recursos persistentes, encadeamento batch, falha parcial, término e segurança de repetição; sem rollback/retry/compensação inventados.
- M3: manifesto com visibilidade por estágio e registro de exposição prévia; suporte e respostas esperadas fora da extração por padrão.
- M4: autoridade do oráculo por pergunta; origem da ferramenta separada da origem das expectativas; cobertura/reachability/efeitos/veredito distintos.
- M5: steering independente de caso, roots explícitos e ferramentas por execução. Integrações genéricas opcionais permanecem inativas; não redirecionam `.sdd/` nem outros repositórios.
- M6: `pipeline/tools/check_anchors.py`, sem dependências externas, para registro JSON de âncoras-fonte contra manifesto de caminhos relativos e hashes. Não substitui revisão semântica, reconciliação com Markdown ou autorização humana.

A taxonomia dos oito artefatos foi mantida. Nenhum gate experimental foi fechado. A base `.sdd-v2` e seu snapshot permanecem íntegros conforme verificação local.

## Verificação realizada

- Teste nominal escrito e observado falhar antes de existir o verificador; passou após implementação.
- Registro vazio/malformado e aliases/travessia/symlink expuseram falhas; implementação foi corrigida e as regressões passaram.
- `python3 -m unittest discover -s tests -v`: passou.
- `PYTHONOPTIMIZE=1 python3 -m unittest discover -s tests -v`: passou, inclusive subprocessos com otimização herdada.
- `python3 verify_snapshot.py`: base e origem sem divergências; diferenças da candidata inventariadas.
- Sintaxe Python e scan estático de padrões de execução perigosa: sem ocorrências nos arquivos examinados. Isso não equivale a auditoria de segurança completa.
- Exercício documental próprio sobre reset externo, falha parcial, oráculos e exposição: `evidence/revisao-documental.md`.
- Saídas reais, executável Python observado e diff: `evidence/verification.json`, `tests.txt`, `tests-optimized.txt`, `snapshot.txt` e `candidate.diff`.

## Lote adicional — completude, revisão e versões

Implementados M7–M9 após autorização de Researcher:

- Matriz de comportamentos relevantes evolui de inventário de evidências para semântica, fronteira e destino contratual, sem pular etapas.
- Gates de semântica e contrato exigem contraexemplos registrados; quando uma categoria não se aplica, exigir N/A com escopo e justificativa.
- Metadados vinculam revisão a identidade de run/capacidade, artefato, dependências e referência de autorização por hash.
- `pipeline/tools/check_gate.py` detecta alterações diretas/transitivas, metadados insuficientes e cadeia inválida; não escreve nos registros nem concede aprovação.
- Templates permanecem unreviewed por padrão. Guia: `pipeline/tools/gates.md`.
- Regressões: 15 testes passaram em modo normal e com PYTHONOPTIMIZE=1. O teste de mudança/restauração percorreu current → stale → current; a retirada de aprovação ancestral permaneceu unreviewed mesmo com hashes downstream atualizados. Dados exclusivamente sintéticos.
- Evidências novas preservadas separadamente em `evidence/lote2/`, sem substituir os recibos do lote anterior. Base e origem continuam íntegras.
- A execução auxiliar documental encerrou com HTTP 429 após gravar arquivos. O implementador leu os seis arquivos afetados e o relato deixado, conferiu a integração e acrescentou N/A justificado. Não foi tratada como sucesso automático nem revisão independente.
- Revisão independente específica do lote 2 concluída: passed=true, sem bloqueantes no escopo examinado; parecer em `evidence/lote2/revisao-independente.md`. O verification.json preserva o checkpoint anterior à chegada do parecer. Não há execução AWS nem aprovação humana de gates.

## Pendências e limites

- Revisão independente do utilitário e da amostra documental concluída: passed=true, sem bloqueantes no escopo examinado. Parecer e limites em `evidence/revisao-independente.md`; não equivale à revisão integral do método ou ao aceite de Researcher.
- Aceite de Researcher da direção revisada; verificação mecânica não é aceite metodológico.
- Lista histórica de melhorias não localizada integralmente. MELHORIAS.md distingue evidência recuperada, itens já presentes e extensões novas; não há alegação de fechamento de todo o backlog original.
- Depois do aceite, criar run separado para AWS com corpus/entradas/gates explícitos. Nenhuma extração, contrato, API, coleta AWS ou backend moderno foi produzido nesta revisão.
- Generalização dos instrumentos de fluxo, medição gcov, execução experimental e retrospective ficam fora deste lote.

## Estágio 9 — Implementation and Executable Qualification

Adicionado Stage 9 após autorização explícita de Researcher nesta sessão: `implementation-executable-qualification`.

- Documentação/template/gate: `pipeline/steering/pipeline.md`, `pipeline/settings/templates/pipeline/implementation-executable-qualification-spec.md`, `pipeline/settings/templates/pipeline/README.md`, `pipeline/tools/gates.md` e `pipeline/settings/templates/specs/init.json` reconhecem 1–9.
- Routing mecânico: `pipeline/tools/check_gate.py` aceita stage 9 em cadeias sintéticas; testes atualizados para 9 estágios.
- Caminho executável: `pipeline/tools/stage9_qualify.py` verifica Stage 8 corrente, registra hashes dos estágios 1–8 antes/depois, copia a implementação SDD preexistente para isolamento, executa HTTP localhost para `posting`, `interest` e `reporting`, valida resposta contra o contrato P2a e escreve artefato stage9.
- Run AWS stage-only: `../casos/aws-carddemo-cycle-v1/sdd-runs/E3-stage9-01/`. Resultado técnico: `overall_passed=true`, três trilhas HTTP 200, `reached_cobol=true` nas três trilhas, `program_exit=4` preservado em posting e hashes 1–8 preservados.
- Adoção registrada como requalificação de implementação preexistente (`generated_from_scratch=false`), não geração nova. Não executa nem incorpora avaliação independente T1–T4.

## Gate complementar pós-Stage 9 — qualidade e cobertura de testes

Adicionado após `api_ready_for_testing=true`, sem criar Stage 10 e sem reabrir os estágios 1–9:

- Checklist/template genérico: `pipeline/settings/templates/testing/test-quality-gate.md` e `test-quality-gate-manifest.json`.
- Validador mecânico: `pipeline/tools/check_test_quality_gate.py`. Ele exige freeze prospectivo, denominador de cobertura conhecido, contagens executado/não executado/inconclusivo/N/A, gaps separados, reset por caso, oráculo de negócio independente de saídas LLM, contraexemplos de saída errada, regras T1–T4, mutações somente como evidência de checker e não aprovação humana por ferramenta.
- Integração documental estreita: `README.md`, `pipeline/tools/gates.md`, `pipeline/tools/README.md`, `pipeline/steering/pipeline.md`, `implementation-executable-qualification-spec.md` e README de templates apontam o gate como complementar ao Stage 9, não como nova etapa histórica.
- Testes TDD sintéticos: o novo teste foi observado falhar antes da ferramenta existir; depois passou detectando schema-only sem oráculo de negócio, oráculo derivado de LLM, denominador desconhecido/all-not-executed e violações T3/T4.
- Verificação executada: `python3 -m unittest discover -s tests -v` passou com 27 testes; `PYTHONOPTIMIZE=1 python3 -m unittest discover -s tests -v` passou com 27 testes; `python3 -m py_compile pipeline/tools/check_test_quality_gate.py tests/test_test_quality_gate.py` passou; `python3 verify_snapshot.py` passou e preservou base/origem.
