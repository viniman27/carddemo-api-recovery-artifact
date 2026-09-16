# Report — pacote pré-campanha v1

Resultado: pacote preparado localmente e **bloqueado para execução oficial**.

## Artefatos persistidos

- `MANIFEST.json`: manifesto canônico com 7 contratos, 21 operações, pins, readiness T1–T4 e bloqueios.
- `t1-outbound-payloads/*.payload.json`: 7 payloads outbound T1 reais, `not_sent`, um por contrato.
- `ACCEPTANCE-PTBR.md`: explicação curta em PT-BR das faltas materiais e decisão eventual de provedor/pacote externo.
- `tools/verify_manifest.py`: verificador local.
- `verify/verify.json`: execução base do verificador.
- `tests/verify-self-test.json`: testes negativos do verificador.
- `REPORT.json`: resumo mecânico da verificação.

## Verificação real

`python3 tools/verify_manifest.py MANIFEST.json` retornou `ok=true`.

`python3 tools/verify_manifest.py MANIFEST.json --self-test` retornou `ok=true` e cobriu:

- base_manifest
- detect_missing_dependency
- detect_tamper
- reject_label_as_authorization
- detect_stale_hash

## Limites

Nenhum provider/model call foi feito. Nenhuma campanha, runner oficial, HTTP AWS ou suíte T1/T2/T3/T4 oficial foi executada. T3 permanece bloqueado por ausência de referência/MBT independente, mapeamentos executáveis e runner oficial integrado.
