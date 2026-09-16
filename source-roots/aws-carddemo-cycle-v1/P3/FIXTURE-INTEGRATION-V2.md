# Integração real de fixtures — fechamento técnico delimitado

Status: integração local de bytes externos exercitada nas três trilhas; NÃO é prontidão experimental integral. Continuação direta após a execução auxiliar interrompida por HTTP 429. Nenhuma nova chamada de modelo, fallback pago, campanha ou comparação foi feita nesta continuação.

Este relatório supera as alegações de seleção/reset de FIXTURE-INTEGRATION-TECHNICAL.md, sem apagar esse relatório nem suas evidências. O rascunho histórico de congelamento permanece inalterado; seus pins de código não representam esta versão.

## O que foi fechado

- `P2B_FIXTURE_REGISTRY` aceita pacote `local_file_package` com arquivos efetivos, não apenas nome/descriptor de fixture interna.
- Conjunto completo de recursos por trilha, destinos permitidos e caminhos locais confinados ao diretório do registro. Um pacote incompleto não recebe recursos de smoke por fallback.
- SHA-256 e tamanho obrigatórios por arquivo em `materializer.filePins`, além do hash do descriptor. Todos os bytes são conferidos antes de escrever qualquer recurso; os mesmos bytes conferidos são copiados, sem segunda leitura entre validação e cópia.
- Materialização em diretório novo de invocação e snapshot depois do setup, antes do COBOL. Snapshot final separado. A antiga alegação baseada em árvore inicialmente vazia foi removida.
- Recursos/outputs COBOL vinculados explicitamente por DD ao diretório da invocação; a QA incluiu DD_TRANFILE/DD_TRANSACT herdados apontando para fora, que não devem sobrepor o binding.
- Juros inclui o arquivo físico `XREFFILE.1`, observado no backend indexado local. Sua ausência produziu erro de abertura no ensaio preservado; não foi corrigido COBOL nem dado de negócio.
- Relatório configurado usa TRANFILE, DATEPARM e lookups do pacote externo; não cria uma nova entrada implícita via INTCALC. Um identificador alterado no input técnico apareceu no TRANREPT real.
- Validação estrutural usa jsonschema real no ambiente já existente. O fallback subset foi removido e preservado como tentativa rejeitada. Warning de depreciação de RefResolver permanece, sem falha de validação.

## Artefatos e evidências atuais

Pacote técnico completo: `technical-packages-v2-complete/registry.json`.

Não é pacote oficial. Contém arquivos nativos do backend local, com origens e hashes registrados. Postagem usa construtores sintéticos já existentes; juros usa o gerador de recursos técnico; relatório usa recursos de entrada de smoke anterior, não respostas esperadas. Formato nativo com índice alternativo não é garantia de portabilidade para outro runtime/backend.

Evidência HTTP final:

- `../P2b/runs/posting-yg7swiws/audit.json`
- `../P2b/runs/interest-qjs2s9xt/audit.json`
- `../P2b/runs/reporting-apqncj25/audit.json`
- `../P2b/readiness-manifest.json`
- `../P2b/schema-validation-report.json`
- `../P2b/server-lifecycle.json`

Conferência direta dos três audits: HTTP 200, exit 0, reached_cobol=true, cinco arquivos físicos declarados/materializados por trilha; hashes das origens, cópias e capturas conferidos. Isso atesta este exercício técnico, não fidelidade abrangente.

QA de mudança de entrada e isolamento DD:

- GREEN: `external-runtime-qa-gxywku5z/results.json`; reporting contém no TRANREPT o identificador vindo da entrada externa modificada.
- RED inicial preservado: `external-runtime-qa-4r0dnlq9/results.json` — setup interno ainda usado em postagem, falta do índice alternativo de juros, relatório ignorando pacote externo.
- RED de DD herdado: `external-runtime-qa-cpheczxu/results.json` — juros/relatório não confinavam esses vínculos.
- GREEN intermediário: `external-runtime-qa-0x9pbqde/results.json`.

Reset e adulteração:

- `reset-bytes-qa-il2s3sfd/report.json` guarda primeira preparação, mutação deliberada de todos os seus recursos, segunda preparação em outro diretório e hashes por arquivo nas três trilhas.
- Segunda preparação recompôs os bytes originais de todos os arquivos declarados; primeira cópia permaneceu mutada; pacote de origem permaneceu íntegro.
- Adulteração do arquivo DALYTRAN após selecionar o descriptor foi rejeitada por hash/tamanho antes de qualquer recurso ser escrito.
- O teste de prova de reset agora rejeita comparação que omite um recurso, em vez de conferir só a interseção de nomes.

## Comandos efetivamente exercitados

A partir de P2b:

    ../P2a/.venv/bin/python -m unittest discover -s tests -v

Resultado final: 21 testes, OK. Incluem as regressões anteriores de relatório misto, ordem/multiplicidade, enquadramento 133/350 e ausência versus vazio.

A partir de P3:

    ../P2a/.venv/bin/python -m unittest discover -s tests -v
    ../P2a/.venv/bin/python pretest_config.py
    ../P2a/.venv/bin/python qa_external_runtime.py
    ../P2a/.venv/bin/python qa_reset_packages.py

Resultado: cinco testes de configuração OK; execution_decision.allowed=false. QA runtime explícita: um teste com as três trilhas, OK. Reset técnico verificado nas três trilhas; adulteração rejeitada. Esses scripts criam novos diretórios de evidência; não são geradores ou runners T1/T2/T3/T4.

Preparador técnico exercitado:

    ../P2a/.venv/bin/python prepare_technical_packages.py technical-packages-v2

O pacote inicial incompleto foi preservado. A revisão `technical-packages-v2-complete` incorporou `XREFFILE.1` e novos pins; o preparador atual inclui esse recurso. Para reproduzir a preparação, escolher um diretório novo; não sobrescrever pacotes anteriores. O preparador realiza build e exige arquivar os logs/manifests mutáveis antes disso.

HTTP e schema, a partir de P2b:

    P2B_FIXTURE_REGISTRY="<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/technical-packages-v2-complete/registry.json" ../P2a/.venv/bin/python p2b_binding.py smoke > latest-smoke.stdout.json
    ../P2a/.venv/bin/python validate_p2b.py > latest-schema.stdout.json

Resultado: três 200; jsonschema overall_passed=true nas três respostas e no exemplo estrutural InterfaceError. O exemplo de 400 do validador é schema QA, não requisição HTTP real adicional. Encerramento do servidor com returncode 0, stdout/stderr vazios.

## Preservação

Antes da continuação direta:

    ../P2b/evidence-archive/resume-20260915T094623Z/archive-manifest.json

Antes do smoke HTTP/schema final:

    ../P2b/evidence-archive/external-bytes-final-20260915T095423Z/archive-manifest.json

Fallback rejeitado anteriormente:

    ../P2b/evidence-archive/schema-subset-rejected-20260914T210006Z/archive-manifest.json

Runs e pacotes RED/GREEN permanecem no disco. O Git raiz continua sem commits, com arquivos preexistentes não rastreados; não houve reset/clean/staging/commit. Conferência dos pins documentais do manifesto histórico não encontrou mudanças em protocolo, plano congelado, specs Stage 7/8 e suas autorizações consultadas. O build conferiu os pins de corpus usados; isto não é auditoria integral de toda a árvore protegida.

## Limites concretos ainda abertos antes das campanhas

Esta entrega fecha a seleção de recursos e a QA técnica, não todas as obrigações da API:

1. Juros ainda usa o driver técnico com parâmetro fixo `2022071800`, identificado na proveniência. Seleção de arquivos externos NÃO demonstra parametrização externa desse argumento. Não tratá-lo como default público ou regra de negócio. A parametrização do wrapper local continua pendente, sem editar o COBOL original.
2. Postagem ainda constrói progress a partir do número de itens do dump e representa rejections.items como lista vazia. Isso não é captura geral dos contadores/rejeições emitidos. O dump indexado também não prova ordem/multiplicidade das ocorrências de escrita. A seleção de fixtures não corrige essas lacunas preexistentes; fixtures oficiais não nominais exigem corrigir esse mapeamento, não aceitar o smoke nominal como prova.
3. O caminho de falha da rotina pode preservar 503 por ausência de captura antes de classificar o evento técnico conhecido. O RED de juros com erro de abertura é evidência dessa limitação de precedência. É necessária a classificação atribuída dos eventos do wrapper/captura, sem tratar todo exit não zero como significado COBOL inventado.
4. Os testes atuais não demonstram fidelidade de todo padding/conversão, completude de relatório, durabilidade, retry safety, estado EOF ou job encadeado. Regressões de parser não equivalem a validação runtime integral.
5. Não houve nova revisão de código em contexto independente após o bloqueio de quota. A conferência direta local identificou e corrigiu as lacunas documentadas; scan estático limitado não encontrou shell=True/os.system/pickle/eval nos arquivos examinados. Não é certificação de segurança.
6. Fixtures oficiais, modelo/expectativas MBT independentes, campanhas, ferramentas/versões finais e APIs dos outros braços continuam pendentes conforme a proposta. Nada foi marcado como aprovado.

Próximo trabalho técnico delimitado: completar captura de postagem/precedência de falhas e parâmetro externo do wrapper de juros antes de declarar prontidão integral da API. Próxima decisão humana: D1–D8 de `PROPOSTA-EXPERIMENTAL-PARA-ACEITE.md`, como direção; não como autorização implícita de execução ou aprovação de conteúdo ainda ausente.
