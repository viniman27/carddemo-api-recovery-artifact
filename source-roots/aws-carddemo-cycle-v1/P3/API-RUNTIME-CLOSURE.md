# Fechamento das pendências técnicas da API SDD

Status: as três pendências delimitadas no checkpoint anterior foram corrigidas e exercitadas localmente. Isto não aprova o desenho experimental, fixtures oficiais, oráculos ou campanhas. Não é uma nova etapa documental SDD nem a futura Fase 2.

## Postagem: observação em vez de reconstrução

Problema reproduzido: com entradas ZZZZ… e AAAA…, a API devolvia AAAA… antes de ZZZZ… porque usava a ordenação do dump indexado. Os contadores vinham do tamanho desse dump e as rejeições eram uma lista vazia fixa.

Correção:

- `P2b/write_observer.c` observa chamadas retornadas de `cob_write` no executável local CBTRN02C. O build usa `-A -Dcob_write=p2b_observed_write` sobre a tradução C; o shim chama o libcob original exatamente uma vez. Nenhum byte da fonte COBOL/copybook foi editado.
- Captura bytes do receiver antes da chamada e status local retornado depois, com sequência, SELECT, identidade da invocação e enquadramento BEGIN/END em arquivo exclusivo da invocação.
- A API usa as ocorrências de TRANSACT-FILE e DALYREJS-FILE, não a ordenação do dump. O dump continua evidência de estado separado.
- Contadores são extraídos das linhas efetivamente emitidas por CBTRN02C: TRANSACTIONS PROCESSED e TRANSACTIONS REJECTED. Não são calculados a partir de arrays.
- Rejeições usam receiver de 430 bytes: candidato original de 350 e trailer de 80, com layout ancorado em CBTRN02C:81–84/176–182 e CVTRA06Y. Motivos públicos continuam somente strings 100–103; 109 e conflitos permanecem internos.
- Campos de texto da nova conversão de postagem preservam largura/padding observado. Ordem e duplicatas não são normalizadas.

Evidência RED: `posting-observation-qa-dyvu8w37/result.json`.
Evidência GREEN final: `posting-observation-qa-oze1o30l/result.json`.

No exercício final, o COBOL recebeu quatro candidatos: duas escritas aceitas na ordem ZZZZ… → AAAA… e duas rejeições idênticas. A API preservou essa ordem e ambas as rejeições; stdout informou quatro processados e dois rejeitados. O envelope não nominal também passou jsonschema real.

Limite do observador: status 00 de WRITE retornado é observação do runtime local, não commit/durabilidade. END é enquadramento do observador, não EOF, conclusão de negócio ou job executado. O shim não captura REWRITE como efeito durável, não altera a regra de negócio e não constitui medição de cobertura. Sua proveniência/flags devem acompanhar qualquer uso experimental futuro, com política técnica equivalente nos braços.

## Falhas: precedência e retenção de evidência

Problemas reproduzidos: falha local de abertura em juros terminava como 503 por falta de captura; erro no dump de postagem interrompia a construção do audit; relatório podia retornar erro sem preencher eventos de falha.

Correção em `P2b/runtime_observations.py` e binding:

- Diagnóstico exato do suporte local CEE3ABD2, erro do observador e erro de transporte do novo wrapper são eventos técnicos atribuídos, com precedência 500.
- Código de saída isolado não define causa COBOL nem é convertido automaticamente em 500. A semântica de CEE3ABD/mainframe não foi inventada.
- Falha de aquisição de snapshot é registrada sem apagar observações anteriores; conteúdo público sustentado é preservado sob availableContent.
- Falhas de conversão/enquadramento mantêm conteúdo independente quando sustentado. Ausência de log não vira lista vazia; um log completo sem ocorrências delimita apenas esse escopo observado.

RED: `failure-boundary-qa-c_3n7e_l/results.json` e logs do ensaio.
GREEN final: `failure-boundary-qa-zgmc2_x6/results.json`.

Foram exercitados índices nativos deliberadamente inválidos nas três trilhas, como QA técnica. As três retornaram 500 com eventos de falha e audit preservado. Os três envelopes de erro passaram nos schemas específicos. Nenhum desses casos é fixture oficial ou oráculo de negócio.

## Juros: argumento externo real

- Novo wrapper local `P2b/interest_driver.cbl`, sem alteração de CBACT04C ou do driver histórico do suporte.
- Pacotes externos de juros devem declarar PARMFILE, com hash e tamanho, além dos recursos existentes e XREFFILE.1.
- O wrapper passa os dez bytes pela estrutura de linkage `S9(04) COMP` + `X(10)`, conforme CBACT04C:175–180. Não interpreta calendário nem aplica default de negócio.
- Pacote externo sem esse recurso é rejeitado; pacote antigo não recebe o literal histórico por fallback.
- A trilha interna de smoke histórico permanece explicitamente identificada como desenvolvimento, separada do caminho configurado.

RED: `interest-argument-qa-d921oatr/`.
GREEN final: `interest-argument-qa-rv2amw5n/result.json`.

O argumento técnico `EXTARG0001` apareceu no identificador emitido pela rotina original. Isso comprova transporte do argumento, não validação calendárica ou correção de juros.

Pacote técnico corrente: `technical-packages-v3-argument/registry.json`. A migração mantém o valor do antigo smoke como arquivo explícito; não o promove a padrão da API. Pacotes anteriores permanecem preservados.

## Verificação final

Saídas completas e comandos: `runtime-closure-evidence-20260915T104230Z/`.

A partir de P2b:

    ../P2a/.venv/bin/python -m unittest discover -s tests -v

Resultado: 25 testes OK.

A partir de P3:

    ../P2a/.venv/bin/python -m unittest discover -s tests -v
    ../P2a/.venv/bin/python pretest_config.py
    ../P2a/.venv/bin/python qa_posting_runtime.py
    ../P2a/.venv/bin/python qa_failure_runtime.py
    ../P2a/.venv/bin/python qa_interest_argument.py
    ../P2a/.venv/bin/python qa_external_runtime.py
    ../P2a/.venv/bin/python qa_reset_packages.py

Resultado: cinco testes de configuração OK; os quatro testes explícitos de integração runtime passaram; reset por bytes e rejeição de adulteração passaram nas três trilhas, com PARMFILE incluído. `execution_decision.allowed=false` permanece.

HTTP/schema final, a partir de P2b:

    P2B_FIXTURE_REGISTRY="<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/technical-packages-v3-argument/registry.json" ../P2a/.venv/bin/python p2b_binding.py smoke > latest-smoke.stdout.json
    ../P2a/.venv/bin/python validate_p2b.py > latest-schema.stdout.json

Resultados: postagem, juros e relatório retornaram HTTP 200; jsonschema real overall_passed=true. O warning de depreciação RefResolver permanece, sem fallback. Servidor encerrou com returncode 0.

Audits finais:

- `../P2b/runs/posting-p72m7r6h/audit.json`
- `../P2b/runs/interest-4cbgz2lo/audit.json`
- `../P2b/runs/reporting-k7j8xplj/audit.json`

Capturas e hashes dos componentes foram lidos e conferidos após execução. Os pins do corpus foram verificados no build. Readback estrutural adicional dos resultados nominais, não nominais e erros: `runtime-closure-evidence-20260915T104230Z/parent-verification.json`.

## Preservação e autorização

Arquivos anteriores arquivados antes de mudanças/rerun:

- `../P2b/evidence-archive/observations-20260915T103433Z/archive-manifest.json`
- `../P2b/evidence-archive/observations-final-20260915T104344Z/archive-manifest.json`

Specs aprovadas, P2a, corpus, fontes COBOL originais, qualificação e V4 não foram editados. Não houve leitura de outputs E1/E2, geração oficial, campanha ou comparação nesta continuação. Não foi disparada nova execução auxiliar para contornar a quota anteriormente registrada; a conferência foi direta, não apresentada como nova revisão independente.

## Onde isso nos deixa

As três pendências específicas deste lote estão encerradas no escopo local exercitado. Não equivale a fidelidade abrangente da API: conversões/capturas em todos os estados, falhas abruptas, completude de relatório, durabilidade e cobertura continuam sem certificação integral.

Próximo marco: aceitar/ajustar o desenho D1–D8 e materializar o pacote experimental que ainda falta — fixtures oficiais, referência/MBT independente, ferramentas/versões, orçamentos, agenda e plano de análise. APIs zero-shot/few-shot não foram declaradas prontas. Aprovar a direção não congela conteúdo ainda ausente nem inicia campanhas.
