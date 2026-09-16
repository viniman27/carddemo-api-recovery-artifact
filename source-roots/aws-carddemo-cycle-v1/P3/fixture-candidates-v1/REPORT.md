# Fixture candidates v1 — relatório pré-teste

Status: `candidate_needs_review`.

Este pacote é candidato técnico pré-teste. Não promove smoke a oficial, não congela casos, não contém expectativas/oráculos e não executa COBOL de negócio.

## Escopo autorizado lido

- `P3/reference-authoring-input-v1/README.md`
- `P3/reference-authoring-input-v1/input-manifest.json`
- Corpus autorizado em `P3/reference-authoring-input-v1/corpus/` para layouts, JCL/proc e fontes das três trilhas.
- `P3/reference-executable-v4/README.md` e `model.json` para limites de seleção abstrata, sem tratar PASS como resultado universal.
- `P3/reference-independent-review-v4/REVIEW.md`
- `P3/PROPOSTA-EXPERIMENTAL-PARA-ACEITE.md`

Materiais excluídos continuam excluídos: contratos/APIs/SDD/runs/quarentena/expected outputs/pacotes técnicos existentes.

## Artefatos criados

- `manifest.json` — inventário materializado, famílias, pré-condições, reset, bloqueios e hashes.
- `tools/generate_fixtures.py` — gerador local determinístico.
- `tools/verify_manifest.py` — verificação de bytes e SHA-256.
- `tests/test_generate_fixtures.py` — testes TDD do gerador.
- `data/sequential/` — bytes reais de entradas sequenciais.
- `data/indexed-logical/` — imagens lógicas JSONL para recursos indexados, não BDB pronto.
- `layouts/` — cópias dos layouts/JCL/proc autorizados usados como proveniência.
- `reports/generated-summary.json` — sumário mecânico gerado.

## Recursos sequenciais materializados

| Recurso | Registros | LRECL | Bytes | SHA-256 |
|---|---:|---:|---:|---|
| `data/sequential/posting/DALYTRAN.dat` | 2 | 350 | 700 | `c1b8044fc500000f57518660c61ee1f45e037395703d25941d71e669b2957b88` |
| `data/sequential/interest/TCATBALF.dat` | 2 | 50 | 100 | `63e5263e53d6e8afa62e1159286e2a9eaaadf3538ade1cbd651ccbc72e10643d` |
| `data/sequential/reporting/TRANFILE.dat` | 2 | 350 | 700 | `f4950998dcf5ae388651921faec4e3ce7de601322c377ec3102e71d4aa19c3b7` |
| `data/sequential/reporting/TRANFILE.empty.dat` | 0 | 350 | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `data/sequential/reporting/DATEPARM.dat` | 1 | 80 | 80 | `5a47e35736982d76dd9c9125257df9cfd6511b8fce3a2ec07f588aa5badd8237` |

Encoding dos sequenciais: `ascii-fixed-width-no-newline`.

## Recursos indexados — definição lógica materializável depois

Entregues como JSONL com `recordImage` em layout fixo e chaves declaradas:

- `data/indexed-logical/CARDXREF.jsonl` — bytes 391, SHA-256 `490c21b45f1a181a4d6d0d72ca0935b8c48eeeebd3b27efcedd7175c6b003a60`.
- `data/indexed-logical/ACCTFILE.jsonl` — bytes 728, SHA-256 `75fba2089a4f61a82f0b735556f8ce0ba0ce55b09591241aa43bedae4b48a2ce`.
- `data/indexed-logical/DISCGRP.jsonl` — bytes 357, SHA-256 `f08d8c8834729bf1869ddfd6a3c5f79fa8104b792a954a415f886340f2f8af03`.
- `data/indexed-logical/TCATBALF.jsonl` — bytes 240, SHA-256 `edc8db924ee3c685aad83dc52ab3fa45678b917a0158c9d8e223e5bcbb4f8609`.
- `data/indexed-logical/TRANSACT.jsonl` — bytes 836, SHA-256 `226c1e6b850967b0afde59f86323e42a89d27b2c9c029cc3da7692c0ab9fc5c5`.
- `data/indexed-logical/TRANTYPE.jsonl` — bytes 115, SHA-256 `e9ba420570bd8915d8487d76374f6386c78f64a15ade9a8c8fcf8208ea2f11f6`.
- `data/indexed-logical/TRANCATG.jsonl` — bytes 119, SHA-256 `0aae3dedfd0654c3c16010a018ab12facd80f320b9bcc73da6d26ff01071d527`.

Bloqueio preciso: os arquivos indexados físicos BDB/GnuCOBOL não foram materializados porque o corpus autorizado não inclui materializador/rebuild aprovado e os componentes físicos são dependentes do ambiente. `CARDXREF` em particular exige considerar componente/path de chave alternativa como `XREFFILE.1`; JSONL lógico não prova prontidão BDB.

## Famílias cobertas para revisão

- Posting: `posting.lookup.present`, `posting.lookup.absent`.
- Interest: `interest.rate.zero`, `interest.rate.nonzero`.
- Reporting: `reporting.date-selection`, `reporting.empty-input`, `reporting.absent-input-blocked`.

`empty-input` é bytes vazios materializados. `absent-input-blocked` é pré-condição/bloqueio, não substituição por arquivo vazio.

## Pré-condições e reset

Pré-condições principais:

1. Não fazer fallback para smoke fixtures ou pacotes técnicos anteriores.
2. Materializar recursos indexados com loader aprovado antes de invocar programas com `ORGANIZATION INDEXED`.
3. Declarar DDs explicitamente por workspace preparado; não herdar bindings externos.
4. Revisar conteúdo antes de qualquer congelamento oficial.

Reset proposto:

```sh
rm -rf /tmp/aws-carddemo-fixture-run && mkdir -p /tmp/aws-carddemo-fixture-run
cp -R P3/fixture-candidates-v1/data /tmp/aws-carddemo-fixture-run/
python3 P3/fixture-candidates-v1/tools/verify_manifest.py P3/fixture-candidates-v1/manifest.json
```

## Comandos reais executados

A partir de `P3/fixture-candidates-v1/`:

```sh
python3 -m unittest discover -s tests -v
```

Primeira execução RED falhou porque `tools/generate_fixtures.py` ainda não existia. Após implementação, um defeito de diretório `reports/` foi capturado e corrigido.

Verificação final executada:

```sh
python3 tools/generate_fixtures.py && python3 tools/verify_manifest.py manifest.json && python3 -m unittest discover -s tests -v
```

Resultado final:

```text
{
  "errors": [],
  "ok": true
}
test_generator_materializes_required_manifest_and_binary_records ... ok
test_indexed_resources_are_logical_not_claimed_bdb_ready ... ok
test_required_families_are_declared_without_expected_outputs ... ok

Ran 3 tests in 0.129s
OK
```

## Limites

- Sem execução de COBOL de negócio.
- Sem casos oficiais, campanha, freeze ou oráculo.
- Bytes `S9` foram materializados como imagens DISPLAY lógicas ASCII candidatas; sem validação runtime de representação de sinal/overpunch.
- Recursos indexados permanecem lógicos até loader BDB/GnuCOBOL aprovado.
- O PASS da referência v4 foi usado somente para delimitar seleção abstrata/famílias, não para valores esperados universais.
