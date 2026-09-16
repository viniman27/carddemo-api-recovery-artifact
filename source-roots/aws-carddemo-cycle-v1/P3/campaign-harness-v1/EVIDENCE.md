# Evidência — campaign-harness-v1

Gerada em `evidence/latest/` por execução local sintética com HTTP loopback. Não houve AWS, COBOL, API pública, oráculos/quarentena ou chamadas de modelo.

## Comandos executados

```bash
python3 -m unittest tests/test_campaign_harness.py -v
python3 qualification_demo.py --output evidence/latest
python3 campaign_harness_cli.py --mode official-aws --config evidence/latest/report.json
```

A verificação final confirmou também que o retorno 2 da CLI oficial é esperado/fail-closed:

```text
official_cli_status=2
```

## Resultado dos testes

```text
Ran 6 tests in 2.898s
OK
```

Cobertura comportamental dos testes sintéticos:

1. hash de freeze detecta adulteração;
2. body ausente, bytes vazios e JSON `{}` são distintos no fio e na identidade;
3. união T4 preserva ordem, proveniência e expectativas distintas;
4. reset copia recurso fresco e detecta mutação após aplicação;
5. deadline é separado de 500 documentado;
6. CLI aceita só qualificação sintética e falha fechada para campanha oficial.

## Totais calculados da demonstração

De `evidence/latest/report.json`:

```json
{
  "union_cases": 6,
  "httpCallsObserved": 12,
  "firstRunTotals": {
    "planned": 6,
    "attempted": 6,
    "completed": 5,
    "deadline_failures": 1,
    "transport_failures": 0,
    "http_failures": 0
  },
  "secondRunTotals": {
    "planned": 6,
    "attempted": 6,
    "completed": 5,
    "deadline_failures": 1,
    "transport_failures": 0,
    "http_failures": 0
  }
}
```

Observações:

- T4 foi reexecutado duas vezes, não derivado por soma das suítes anteriores.
- `tamperDetected=true` com erro `suite freeze hash mismatch`.
- `freshCopyVerified=true` e `mutationDetectedAfterFirstApplication=true` demonstram cópia fresca após adulteração local.
- `documented500NotHttpFailure=true`; o 500 documentado não foi reclassificado como falha de infraestrutura.
- `deadlineFailuresSeparated=true`; deadline tem contador próprio.

## Artefatos de evidência

- `evidence/latest/report.json`: relatório agregado.
- `evidence/latest/frozen-suites/T1.json`, `T2.json`, `T3.json`, `T4-union.json`: suítes congeladas com hashes.
- `evidence/latest/tamper-copy.json`: cópia adulterada propositalmente para demonstrar falha de hash.
- `evidence/latest/runs/T4-mutated/`: primeira reexecução T4 com mutação de recurso pós-aplicação.
- `evidence/latest/runs/T4-fresh-copy/`: segunda reexecução T4 demonstrando reset por cópia fresca.
