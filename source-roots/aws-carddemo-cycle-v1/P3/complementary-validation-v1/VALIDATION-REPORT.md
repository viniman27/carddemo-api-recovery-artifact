# Relatório de validação mecânica — complementary-validation-v1

Comando executado no diretório `casos/aws-carddemo-cycle-v1`:

```bash
python3 P3/complementary-validation-v1/validate_catalog.py
```

Saída real:

```json
{
  "status": "PASS",
  "errors": [],
  "checked": {
    "obligations": 25,
    "contracts": 7,
    "operations": 21,
    "mappingCells": 525,
    "sourceBase": "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-preparation/research-corpus"
  }
}
```

A validação conferiu contagens, unicidade do mapeamento obrigação×contrato×operação, hashes/linhas dos anchors de fonte e pins dos artefatos usados como base. Não executou campanha, COBOL, APIs ou chamadas externas.
