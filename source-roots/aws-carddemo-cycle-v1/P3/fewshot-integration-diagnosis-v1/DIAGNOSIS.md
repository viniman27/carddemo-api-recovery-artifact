# fewshot-integration-diagnosis-v1

Escopo: diagnóstico técnico dos dois achados E2-2 da integração real, com correção mínima testada em cópia isolada. Não editei `P2c-few-shot/` original nem runs antigos; tudo novo ficou neste diretório.

## Cópia isolada

- Cópia operacional: `isolated-cycle/aws-carddemo-cycle-v1/`
- Facade original copiado de `P2c-few-shot/p2c_facade.py`
  - SHA-256 original: `ebe50eebc8c4157ad240b491054187b5499c8b9d761d8c71d6371a1b98da72a8`
  - SHA-256 modificado na cópia: `bdb4d378e56ab27efbefefa88a98904a200ec2dccbf513aedf25a8482cc8ea9d`
- Registry copiado atual: `isolated-cycle/aws-carddemo-cycle-v1/P3/technical-packages-v3-argument/registry.json`
  - SHA-256: `b292dcad37968721da598dc206b3dbb2a6cce8aa4241ca9da0248ec54b9a72c1`
- Contrato E2-2 copiado: `collection-01/E2-2/response-original.txt`
  - SHA-256: `c79c27b56fee0ee985e8c3642c494869c2701054dce7a06cff90fa2519259820`

Patch proposto aplicável ao original, mas não aplicado: `proposed-p2c-few-shot.patch`

- SHA-256 do patch: `45f81b7dbcbf103688134246bcb324a8ca1e3531e7b662c3958f2d11bb56ecde`
- Dry-run e aplicação em cópia de verificação: `/usr/bin/patch -d patch-apply-check -p0 --dry-run < proposed-p2c-few-shot.patch` passou; arquivo resultante teve SHA-256 `bdb4d378e56ab27efbefefa88a98904a200ec2dccbf513aedf25a8482cc8ea9d`, igual à cópia testada.

## Achado 1 — E2-2 posting sem `processingTimestamp`

Decisão: defeito de implementação da projeção P2c, corrigível por patch mínimo.

Causa-raiz:

- O contrato E2-2 define `Transaction.processingTimestamp` como campo obrigatório também para `Rejection.transaction`.
- O COBOL/P2b preserva o byte-span de `processingTimestamp` no registro rejeitado, mas a camada P2b o renomeia internamente para `suppliedProcessingTimestamp` para indicar que veio do DALYTRAN de entrada.
- `P2c-few-shot/p2c_facade.py` publicava esse nome interno dentro de `rejections[].transaction`, quebrando o schema público. Não faltava byte de runtime; faltava remapeamento para o nome contratual.
- A correção não inventa timestamp de negócio. Ela somente reexpõe o valor capturado no receptor COBOL (`suppliedProcessingTimestamp`) como o campo contratual `processingTimestamp` quando o campo público está ausente.

Evidência RED:

- Teste novo: `isolated-cycle/aws-carddemo-cycle-v1/P2c-few-shot/tests/test_e2_2_integration_defects.py::test_rejected_posting_transaction_preserves_required_processing_timestamp`
- Antes do patch: `KeyError: 'processingTimestamp'`.

Evidência GREEN/HTTP:

- `P2a/.venv/bin/python -m unittest discover -s tests -v` em `isolated-cycle/aws-carddemo-cycle-v1/P2c-few-shot`: 2/2 OK.
- `P2a/.venv/bin/python run_e2_2_http_probe.py`: posting retornou HTTP 200, schema OK, `reachedCobol=true`, `programExit=4`.
- Relatório HTTP: `e2_2_http_probe.json`, linha de posting:
  - request SHA-256 `63face503cda567edfe9f8742f7027199e72ca2fed652f4aa42c1bcbb3ebe256`
  - response SHA-256 `9a2bc91910f0913b2cc1440cb1e77a3883d35774d670cc62bf128918be517ac3`
  - `rejections[0].transaction.processingTimestamp = "2025-01-01-00.00.00.000000"`

## Achado 2 — E2-2 reporting `local_compatibility_abort`, exit 12, `reached_cobol=false`

Decisão: dois aspectos separados.

1. Defeito de implementação P2c: o audit marcava `reached_cobol=false` quando o programa abortava antes de produzir `TRANREPT` ou `END OF EXECUTION`, apesar de stdout conter `START OF EXECUTION OF PROGRAM CBTRN03C`. Corrigido na cópia para reconhecer início da rotina como alcance real de COBOL.
2. Limitação/precondição operacional da fixture/request corrente: o 500 é documentado e schema válido, mas a causa é lookup inválido em dataset exigido, não sucesso funcional. O request HTTP é válido pelo schema e alcança `CBTRN03C`; a execução aborta porque o CARDXREF da fixture copiada atual não contém a chave `0000000000000001` usada pelo request técnico padrão.

Causa-raiz rastreada:

- `e2_2_http_probe.json` para reporting registra stdout:
  - `START OF EXECUTION OF PROGRAM CBTRN03C`
  - `INVALID CARD NUMBER : 0000000000000001`
  - `FILE STATUS IS: NNNN0023`
  - `ABENDING PROGRAM`
- Evento preservado após patch:
  - `kind=cobol_precondition_failure`
  - `lookup=CARDXREF`
  - `key=0000000000000001`
  - `fileStatus=23`
  - autoridade: DISPLAY do `CBTRN03C` antes de `9999-ABEND-PROGRAM`
- O diagnóstico local `LOCAL-CEE3ABD/2 CODE=+0000000999 TIMING=+0000000000` permanece registrado como compatibilidade local, mas agora não é a única explicação.

Evidência de bytes/precondição:

- `reporting-cardxref-dump-evidence.json` usou `io_XREFFILE` para dump técnico do `CARDXREF` copiado atual.
- Dump: 2 registros de 50 bytes, chaves `4111111111111111` e `4222222222222222`; `containsRequestedKey=false` para `0000000000000001`.
- Isso fundamenta a classificação como precondição de dados não satisfeita pela fixture/request atual, não como falha de schema.

Evidência adicional:

- `e2_2_reporting_present_card_probe.json` trocou só `cardNumber` para chave presente (`4111111111111111`), com request ainda schema-válido. O COBOL foi alcançado e avançou até a próxima precondição: `INVALID TRAN CATG KEY : 010001`, `fileStatus=23`, `TRANCATG`. Isso confirma que o primeiro abort não era barreira de transporte nem ausência de rotina; eram precondições de datasets/keys.

Evidência RED/GREEN:

- RED antes do patch: teste `test_reporting_abort_records_reached_cobol_and_exact_precondition_failure` falhou com `AssertionError: False is not true` para `reached_cobol` e não havia evento `cobol_precondition_failure`.
- GREEN após patch: mesmo teste OK.
- HTTP técnico pós-patch: reporting retornou HTTP 500 documentado, schema OK, `reachedCobol=true`, `programExit=12`, com eventos de `CARDXREF`/status 23 e `local_compatibility_abort` preservados.

## Testes executados

1. RED após criar regressões, antes da correção:
   - comando: `P2a/.venv/bin/python -m unittest tests.test_e2_2_integration_defects -v`
   - resultado: 2 testes falharam pelos sintomas esperados (`processingTimestamp` ausente; `reached_cobol=false`).
2. GREEN específico:
   - comando: `P2a/.venv/bin/python -m unittest tests.test_e2_2_integration_defects -v`
   - resultado: 2/2 OK.
3. GREEN suite local da cópia:
   - comando: `P2a/.venv/bin/python -m unittest discover -s tests -v`
   - resultado: 2/2 OK.
4. HTTP técnico isolado com fixture copiada atual:
   - comando: `P2a/.venv/bin/python run_e2_2_http_probe.py`
   - resultado: posting 200/schema OK/reached COBOL; reporting 500 documentado/schema OK/reached COBOL/precondição `CARDXREF` status 23.

## Limites preservados

- Não regenerei contratos.
- Não li quarentena, oráculos ou expected outputs.
- Não comparei braços para reparar SDD.
- Não fiz model calls.
- Não apliquei patch no original.
- Não tentei fabricar fixture semanticamente perfeita; a classificação do reporting fica limitada à fixture/request técnico atual e às precondições demonstradas.
