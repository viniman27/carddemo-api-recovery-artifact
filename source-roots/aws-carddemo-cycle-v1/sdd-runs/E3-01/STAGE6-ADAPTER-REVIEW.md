# Revisão independente — Stage 6 adapter

**Escopo:** auditoria read-only do `sdd-command-adapter/stage6_adapter.py` e testes associados, com consulta local dos metadados reais aprovados de Stage 5. Não fiz init/prepare/execute real de Stage 6, não gerei contrato, não usei rede/modelo e não alterei código, specs, aprovações, framework ou corpus. Único arquivo criado: este relatório.

## Verificações executadas

- Código auditado: `casos/aws-carddemo-cycle-v1/sdd-command-adapter/stage6_adapter.py`.
- Dependências de confiança lidas: `adapter.py`, `stage5_adapter.py`, `stage4_adapter.py`, `stage3_adapter.py`, `pipeline-sdd-v3/pipeline/tools/check_gate.py`.
- Metadados reais lidos em modo read-only:
  - `specs/canonical-data-boundary-carddemo/spec.json` linhas 1-80.
  - `reviews/stage-5-authorization.json` linhas 1-20.
  - `STAGE5-COUNTEREXAMPLE-REVIEW.md` linhas 1-113.
  - `stage5-counterexample-findings.json` linhas 1-419.
  - `specs/canonical-data-boundary-carddemo/input-pins.json` linhas 1-268.
  - `casos/aws-carddemo-preparation/evidence/research-package.json` linhas 1-140.
- Comando de testes local: `python3 -m unittest discover -s tests -v`, em `casos/aws-carddemo-cycle-v1/sdd-command-adapter`.
- Resultado dos testes: **41 tests passed**, `Ran 41 tests in 15.174s`, `OK`; saída completa salva pelo runtime em `<REDACTED_LOCAL_PATH>/.run-cache/cache/terminal-output/out-1789251562-94583-c50.log`, resumo nas linhas 247-250 desse log.
- Consulta read-only de `stage6_current_input_pins(...)` contra o run real retornou: 5 upstream specs, 5 artifacts, 5 authorizations, 3 review attachments, `expected_real_corpus_file_count=19`, `actual_corpus_file_count=19`, `source_bodies_count=19`, `framework_context_count=13`, `gate_check.status=current`, `gate_check.ok=true`, `human_approval_granted=false`.

## Parecer resumido

O adapter Stage 6 está **substancialmente alinhado** ao objetivo de preparar uma requisição Stage 6 sem rede por padrão, preservando a cadeia upstream, anexos Stage 5, corpus real de 19 arquivos e restrições contra implementação/Stage 7. Porém encontrei **dois ajustes necessários antes de confiar em execução autorizada real** e **três lacunas de teste/documentação**.

A maior questão semântica não é a presença de route/method/status/schema no Stage 6: isso é legítimo quando tratado como decisão de representação registrada em `D-n`, conforme o template. O risco é o prompt atual bloquear ou marcar como gap qualquer decisão de contrato que Stage 5 não especificou literalmente, mesmo quando a decisão é apenas representação de API e não garantia de negócio.

## Achados

### F-1 — Necessário / severidade média-alta: Stage 5 authorization é pinada, mas seu conteúdo não é validado semanticamente

**Evidência no código:**

- `stage6_adapter.py` exige que `spec.json` Stage 5 tenha `pipeline_stage == 5` e `artifact_type == canonical-data-boundary` nas linhas 132-133.
- Exige `mandatory_tracks == [posting, interest, reporting]` nas linhas 134-135.
- Exige upstream Stage 4 direto e pin stale/non-stale nas linhas 136-144.
- Executa `adapter.run_gate_checker(...)` na linha 129 e carrega o arquivo de autorização Stage 5 nas linhas 148-150.
- Depois apenas inclui essa autorização em `pins["authorizations"]` na linha 158; não há checagem de `decision`, `stage`, `artifact.path`, `scope`, `residual_limits`, `reviewer` ou `recorded_at` do JSON de autorização.

**Evidência do gate checker:**

- `check_gate.py` valida `review['decision'] == 'approve'` na linha 80 e hashes de `review['artifact']`, `review['authorization']` e `review['upstream_specs']` nas linhas 82-87.
- Mas ele não valida o conteúdo semântico do arquivo de autorização; a linha 113 fixa `human_approval_granted = False` e a linha 114 define `ok` apenas por `status == current`.

**Evidência real:**

- O arquivo real `reviews/stage-5-authorization.json` tem `decision: approve` na linha 5, escopo que autoriza Stage 6 documental e proíbe Stage 7/implementação/COBOL na linha 10, e limites residuais na linha 11. Isso está correto no run atual, mas o adapter não exige esses campos.

**Risco:** uma autorização Stage 5 pinada e hash-current, porém semanticamente errada ou contraditória, poderia passar desde que o review do `spec.json` declare `decision: approve`. Para Stage 6, isso é uma falha de integridade de gate, porque a autorização é uma autoridade upstream, não apenas anexo passivo.

**Mudança necessária:** em `stage6_current_input_pins`, após carregar `stage5_auth`, validar pelo menos:

- `decision == "approve"` ou `approved is True` conforme formato aceito;
- `stage == 5` quando presente;
- `artifact.path == STAGE5_ARTIFACT` e hash atual quando presente;
- `scope`/`conditional_scope` não autoriza Stage 7, implementação ou COBOL execution;
- `review_reference` e `findings_reference` existem e batem com os pins já verificados.

**Teste necessário:** fixture com `stage-5-authorization.json` pinado mas `decision: reject` ou `stage: 4` deve fazer `/sdd:spec-init ... --stage 6` e `/sdd:spec-requirements ... --prepare-only` retornarem 2.

---

### F-2 — Necessário / severidade média: o prompt pode bloquear escolhas legítimas de representação de Stage 6

**Evidência do prompt Stage 6:**

- `required_tracks` permite superfície de operação “only where licensed by Stage5 canonical elements or explicit D-n decisions” nas linhas 243-246.
- Porém `contract_rules` diz que Stage 6 deve exigir gaps bloqueantes para qualquer método, rota, schema, validação, status, erro ou state/recovery “unsupported by Stage5” nas linhas 249-254.
- `negative_constraints` proíbe inventar políticas como unidades, rounding, date validity, durability, retry/idempotency etc. nas linhas 256-263.

**Evidência do template Stage 6:**

- `api-contract-spec.md` linha 7: todo elemento de contrato deriva de elemento canônico **ou decisão registrada `D-n`**.
- Linha 10: decisões de estratégia de erro são decisões de design, registradas, justificadas e rastreáveis.
- Linhas 25-26: method/route decisions com rationale; escolhas não óbvias devem ser registradas como `D-n`.
- Linhas 49-50: rationale para status decisions não óbvias, também `D-n`.
- Linhas 68-70: nem todo comportamento precisa virar endpoint; justificar exposição ou não exposição.

**Distinção metodológica:**

- **Legítimo em Stage 6:** escolher método HTTP, rota, shape de schema, status de transporte/domínio, formato OpenAPI e agrupamento de operações como **representação de contrato**, desde que documentado como `D-n`, reversível/rastreável a Stage 5 e sem prometer semântica de negócio não licenciada.
- **Não legítimo:** transformar a escolha de representação em garantia de negócio — por exemplo, prometer idempotência, rollback, persistência, autenticação, paginação, calendário válido, moeda/unidade, reset ou completude de relatório quando Stage 5 deixou isso como unknown/gap.

**Risco:** a frase das linhas 253-254 pode induzir o modelo a marcar como gap decisões normais de API contract que o próprio template manda tomar em Stage 6. Isso pode gerar uma Stage 6 excessivamente bloqueada, sem contrato revisável, apesar de Stage 5 ter autorizado documentação de contrato para posting/interest/reporting.

**Mudança necessária:** ajustar a instrução para: “Stage 6 may make representation choices for method, route, schemas, status and error categories as `D-n` decisions when they do not create new business guarantees; only unsupported business/semantic guarantees or unrepresentable canonical obligations become blocking gaps.”

**Teste necessário:** teste literal no payload garantindo simultaneamente:

- presença de texto permitindo `D-n representation choices` para route/method/status/schema;
- presença de texto proibindo business guarantees não licenciadas;
- ausência de frase equivalente a “qualquer route/method/status não especificado em Stage5 é gap bloqueante”.

---

### F-3 — Necessário / severidade média: contagem real de corpus é registrada, mas não é enforceada

**Evidência no código:**

- `stage6_adapter.py` registra `expected_real_corpus_file_count: 19` e `actual_corpus_file_count: len(source_bodies)` nas linhas 165-166.
- Não há `if len(source_bodies) != 19: raise AdapterError(...)`.
- A retenção exata do corpus depende de `stage5_adapter.stage5_current_input_pins(...)` linha 146 e da cadeia Stage 4/3, não de uma checagem Stage 6 própria.

**Evidência real:**

- `research-package.json` contém 19 arquivos nas linhas 9-123.
- `specs/canonical-data-boundary-carddemo/input-pins.json` registra `expected_real_corpus_file_count: 19` e `actual_corpus_file_count: 19` nas linhas 244-245.
- A consulta read-only do adapter Stage 6 também retornou `actual_corpus_file_count=19`.

**Risco:** no run real atual não há divergência. Mas o campo `expected_real_corpus_file_count` em Stage 6 é apenas declarativo; se a cadeia upstream ou package for indevidamente reduzida e ainda passar nos gates, Stage 6 não falha por contagem. Isso importa porque o escopo exige retenção exata do corpus/framework e porque fixtures sintéticas podem esconder o problema.

**Mudança necessária:** em Stage 6, falhar se `len(source_bodies) != 19` para este adapter específico AWS CardDemo, ou derivar o esperado de uma autoridade aprovada e comparar contra ela explicitamente. Se o adapter também deve suportar fixtures sintéticas, isolar a política por parâmetro de teste, não por silêncio em produção.

**Teste necessário:** package sintético ou fixture upstream com apenas 2 arquivos deve falhar em modo real, ou o teste deve declarar explicitamente que está em modo fixture e não valida a política real.

---

### F-4 — Opcional mas recomendável / severidade baixa-média: blind spot de fixtures para paths reais dos anexos Stage 5

**Evidência real:**

- `reviews/stage-5-authorization.json` usa `review_reference.path = "STAGE5-COUNTEREXAMPLE-REVIEW.md"` nas linhas 12-14.
- Usa `findings_reference.path = "stage5-counterexample-findings.json"` nas linhas 16-18.
- Ambos existem na raiz do RUN, não sob `reviews/`.

**Evidência do teste Stage 6:**

- A fixture cria `STAGE5-COUNTEREXAMPLE-REVIEW.md` na raiz nas linhas 25-28 de `tests/test_stage6_adapter.py`.
- Mas cria findings em `reviews/stage5-counterexample-findings.json` nas linhas 26 e 29, enquanto o real é `stage5-counterexample-findings.json` na raiz.
- O teste espera `reviews/stage5-counterexample-findings.json` em `review_attachments` na linha 105.

**Evidência no código:**

- `_select_attachment` aceita path exato ou sufixo de basename nas linhas 75-83, então o formato real funciona.

**Risco:** a compatibilidade real foi inspecionada e passou, mas a suíte não cobre exatamente o shape real de Stage 5 findings. Um regressão futura poderia passar na fixture e quebrar o run real.

**Teste recomendado:** acrescentar teste Stage 6 com `findings_reference.path = "stage5-counterexample-findings.json"` e review root-relative, espelhando o metadata real.

---

### F-5 — Opcional / severidade baixa: suíte passa, mas testa mais presença literal que invariantes estruturais

**Evidência:**

- `tests/test_stage6_adapter.py` valida tokens no payload por `assertIn` nas linhas 79-91.
- Valida conteúdo bruto de Stage 5 review/findings no prompt nas linhas 92-95.
- Valida ordem dos upstream specs, número de authorizations e attachments nas linhas 99-106.
- Valida `execute_authorized == False` no metadata preparado nas linhas 107-110.
- Testa stale/tamper e Stage 7 refusal nas linhas 112-130, e auth execution errada nas linhas 132-145.

**O que falta:**

- Não testa autorização Stage 5 semanticamente negativa mas pinada.
- Não testa root-relative `stage5-counterexample-findings.json` real.
- Não testa que `framework_context` contém exatamente os 13 documentos esperados de Stage 6, inclusive `ears-format.md` e `api-contract-spec.md`.
- Não testa que `source_bodies` no payload preserva `content` e `numbered_lines`, apenas compara contagem na linha 96.
- Não testa que prompt diferencia “representation D-n choice” de “unsupported business guarantee”.

**Risco:** a alegação “41 tests passed” é verdadeira, mas não suficiente como evidência de completude metodológica para os pontos acima.

## Pontos positivos confirmados

- Stage-only/feature-only: `parse_stage6` recusa qualquer estágio diferente de 6 nas linhas 26-33; `command_spec_init` e `command_spec_requirements` recusam feature diferente de `api-contract-carddemo` nas linhas 185-186 e 299-300.
- Não sobrescreve diretórios existentes: spec dir nas linhas 190-192; prepared dir nas linhas 301-316; escrita usa `adapter.write_json_new/write_text_new`, que recusam arquivo existente em `adapter.py` linhas 72-83.
- Gate recursivo upstream é usado: Stage 6 chama `run_gate_checker` para Stage 5 na linha 129; Stage 5 chama gate Stage 4 em `stage5_adapter.py` linha 85; Stage 4 chama gate Stage 3-r2 em `stage4_adapter.py` linha 57; Stage 3 chama gate Stage 2-r2 em `stage3_adapter.py` linha 85; Stage 1 pins são recuperados por `adapter.stage1_pins` em `adapter.py` linhas 299-313. O `check_gate.py` recursa nos upstreams nas linhas 88-99.
- Stage 5 review + findings são anexos obrigatórios: `_attachment_pins_from` inclui `review_reference` e `findings_reference` nas linhas 64-67; `require_stage5_review_attachment_pins` exige ambos nas linhas 87-107 e verifica hash atual nas linhas 80-83/96-101.
- Retenção de Stage 4 review herdada: `pins["review_attachments"] = pins15.get(...) + attachment_pins` em Stage 6 linhas 159; no real, a lista contém `STAGE4-COUNTEREXAMPLE-REVIEW.md`, `STAGE5-COUNTEREXAMPLE-REVIEW.md` e `stage5-counterexample-findings.json`.
- Retenção de source bodies e representações: Stage 3 constrói `content`, `numbered_lines` e `derived_representation_sha256` em `stage3_adapter.py` linhas 63-79; Stage 6 passa `source_bodies` completo no prompt na linha 269 e pins com derived hash nas linhas 161-163.
- Prepare-only não chama rede: payload/metadata são escritos nas linhas 317-320 e `--prepare-only` retorna `network_called: false` nas linhas 321-323.
- Execução exige autorização de request hash: Stage 6 só chama `adapter.execute_request` em path `--execute` nas linhas 303-314/324-326; `adapter.verify_execution_authorization` exige `approved`, `stage`, `run_id`, `model`, `base_url` e `request_sha256` nas linhas 546-560.
- Stage 7 é recusado: `parse_stage6` bloqueia `--stage 7` nas linhas 26-33; teste cobre isso em `tests/test_stage6_adapter.py` linha 130.

## Decisão sobre route/method/status/schema vs garantias de negócio

Não recomendo bloquear Stage 6 só porque Stage 5 não especifica rotas, métodos HTTP, status codes ou shapes OpenAPI. O template Stage 6 existe justamente para tomar essas decisões de representação (`api-contract-spec.md` linhas 21-50), desde que elas sejam:

1. registradas como `D-n` quando não óbvias;
2. rastreáveis a elementos canônicos/constraints Stage 5;
3. explícitas sobre exclusões, external/unsupported ou gaps;
4. neutras quanto a garantias não licenciadas.

Recomendo bloquear ou marcar gap somente quando a escolha de contrato cria uma promessa de negócio/runtime que Stage 5 recusou ou deixou desconhecida: durabilidade, rollback, idempotência, reset, isolamento, autenticação/autorização real, paginação, calendário, moeda/unidade, rounding, validade de parâmetro, completude de relatório, EOF storage, retry safety ou persistência.

## Recomendação antes de Stage 6 real

**Necessário antes de execução autorizada real:**

1. Validar semanticamente o JSON real de autorização Stage 5, não apenas o pin/hash (F-1).
2. Ajustar o prompt para permitir escolhas legítimas de representação Stage 6 como `D-n`, separando-as de garantias de negócio não licenciadas (F-2).
3. Enforcear a contagem/retention real de 19 arquivos do corpus neste adapter específico, ou declarar formalmente o modo fixture quando não for real (F-3).

**Opcional/recomendável:**

4. Acrescentar fixture que reproduza exatamente os paths reais root-relative de review/findings Stage 5 (F-4).
5. Fortalecer testes estruturais para `source_bodies.content`, `numbered_lines`, framework_context exato e invariantes semânticas do prompt (F-5).

**Status final:** não aprovo Stage 6, não aprovo Stage 7 e não recomendo execução/model call antes dos ajustes necessários acima.
