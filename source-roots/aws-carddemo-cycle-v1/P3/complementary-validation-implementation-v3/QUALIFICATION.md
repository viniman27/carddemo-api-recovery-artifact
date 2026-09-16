# Qualification — complementary validation implementation v1

Status: qualified local implementation slice. Not a frozen campaign, not human approval, and not evidence of real API/COBOL execution.

## Scope actually implemented

- New versioned implementation directory: `P3/complementary-validation-implementation-v1/`.
- Source catalog is loaded from `../complementary-validation-v2/scenario-catalog.json`.
- Source anchors are verified against pinned SHA-256 files under the v2 `sourceBase` before CLI execution when `--verify-source` is used.
- Implemented representative essential source-grounded obligations: 8/25.
- Explicit pending obligations: 17/25.
- Synthetic fixtures only; no external LLM calls, no campaign runner, no quarantine expected-output reads, no original COBOL/API/contract edits.

## TDD evidence

RED 1:

```text
../../P2a/.venv/bin/python -m unittest discover -s tests -v
...
ModuleNotFoundError: No module named 'semantic_checkers'
FAILED (errors=1)
```

GREEN 1:

```text
../../P2a/.venv/bin/python -m unittest discover -s tests -v
Ran 7 tests in 0.019s
OK
```

RED 2 (CLI output parent-directory behavior added after real failure):

```text
../../P2a/.venv/bin/python -m unittest tests.test_semantic_checkers.SemanticCheckerTests.test_cli_creates_parent_directory_for_machine_readable_output -v
...
FileNotFoundError: ... nested/results.json
FAILED (failures=1)
```

GREEN 2 / full suite:

```text
../../P2a/.venv/bin/python -m unittest discover -s tests -v
Ran 8 tests in 0.061s
OK
```

## Executed qualification commands

```text
../../P2a/.venv/bin/python -m unittest discover -s tests -v && \
../../P2a/.venv/bin/python -m semantic_checkers --verify-source fixtures/synthetic_success_all_tracks.json --out evidence/synthetic_success_results.json && \
../../P2a/.venv/bin/python -m semantic_checkers --verify-source fixtures/synthetic_known_wrong_all_tracks.json --out evidence/synthetic_known_wrong_results.json && \
../../P2a/.venv/bin/python - <<'PY'
import json
from pathlib import Path
for name in ['synthetic_success_results.json','synthetic_known_wrong_results.json']:
    p=Path('evidence')/name
    data=json.loads(p.read_text())
    counts={}
    for r in data['results']:
        counts[r['status']]=counts.get(r['status'],0)+1
    print(name, counts)
PY
```

Observed output:

```text
Ran 8 tests in 0.061s
OK
synthetic_success_results.json {'pending': 17, 'pass': 8}
synthetic_known_wrong_results.json {'pending': 17, 'failed': 8}
```

Schema validation using `../../P2a/.venv/bin/python` + `jsonschema`:

```text
schema ok evidence/synthetic_success_results.json
schema ok evidence/synthetic_known_wrong_results.json
```

## Traceability to 25 obligations

| Obligation | Capability | v1 checker status | Title |
| --- | --- | --- | --- |
| POSTTRAN-OBL-001 | CBTRN02C/POSTTRAN | pending | Arquivos externos e abertura |
| POSTTRAN-OBL-002 | CBTRN02C/POSTTRAN | pending | Loop DALYTRAN e EOF |
| POSTTRAN-OBL-003 | CBTRN02C/POSTTRAN | implemented | Layout e cópia para transação postada |
| POSTTRAN-OBL-004 | CBTRN02C/POSTTRAN | implemented | Validação de cartão |
| POSTTRAN-OBL-005 | CBTRN02C/POSTTRAN | pending | Validação de conta, limite e expiração textual |
| POSTTRAN-OBL-006 | CBTRN02C/POSTTRAN | implemented | Rejeitos e return-code |
| POSTTRAN-OBL-007 | CBTRN02C/POSTTRAN | pending | TCATBAL create/update |
| POSTTRAN-OBL-008 | CBTRN02C/POSTTRAN | pending | Atualização ACCOUNT e ordem de efeitos |
| POSTTRAN-OBL-009 | CBTRN02C/POSTTRAN | implemented | WRITE TRANFILE após efeitos anteriores |
| INTCALC-OBL-001 | CBACT04C/INTCALC | pending | Arquivos, parâmetro e abertura |
| INTCALC-OBL-002 | CBACT04C/INTCALC | pending | Varredura e agrupamento por conta |
| INTCALC-OBL-003 | CBACT04C/INTCALC | pending | Leitura ACCOUNT e XREF por conta |
| INTCALC-OBL-004 | CBACT04C/INTCALC | pending | Taxa específica ou DEFAULT |
| INTCALC-OBL-005 | CBACT04C/INTCALC | implemented | Fórmula e guarda de juros |
| INTCALC-OBL-006 | CBACT04C/INTCALC | implemented | Campos da transação de juros |
| INTCALC-OBL-007 | CBACT04C/INTCALC | pending | Update de conta em quebra de grupo |
| INTCALC-OBL-008 | CBACT04C/INTCALC | pending | Última conta no EOF |
| TRANREPT-OBL-001 | CBTRN03C/TRANREPT | pending | Contexto JCL e arquivos |
| TRANREPT-OBL-002 | CBTRN03C/TRANREPT | implemented | DATEPARM e filtro textual antes do EOF |
| TRANREPT-OBL-003 | CBTRN03C/TRANREPT | pending | Leitura TRANFILE e EOF condicional |
| TRANREPT-OBL-004 | CBTRN03C/TRANREPT | pending | Quebra por cartão e lookups |
| TRANREPT-OBL-005 | CBTRN03C/TRANREPT | pending | Cabeçalhos e paginação |
| TRANREPT-OBL-006 | CBTRN03C/TRANREPT | implemented | Linha de detalhe e acumulação |
| TRANREPT-OBL-007 | CBTRN03C/TRANREPT | pending | Totais de página/grand no EOF condicional |
| TRANREPT-OBL-008 | CBTRN03C/TRANREPT | pending | Ausência de Account Total final no EOF |

## Limits / pending

- 17 obligations are intentionally `pending`; this is breadth traceability, not fake semantic coverage.
- Fixtures are independent manually computed synthetic observations, not replayed API responses and not business campaign outcomes.
- Decimal interest example is manually computed from source formula: `(1500.00 * 10.00) / 1200 = 12.50`.
- No mutation score or test pass is claimed as business coverage.
- Future integration runner should write the same output schema from real API/COBOL observations and preserve raw bytes for every observable file/report record.
