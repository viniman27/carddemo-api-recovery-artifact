# Complementary validation implementation v1

Status: local implementation slice, not a campaign, no external calls, no edits to COBOL/API contracts/original artifacts.

This directory implements executable, source-grounded semantic checkers for representative essential obligations across all three AWS CardDemo tracks:

- posting: accepted transaction copy/timestamp, missing-card reject, reject return-code, TRANFILE effect order;
- interest: zero/nonzero rate guard and Decimal monthly formula, written interest transaction fields;
- reporting: inclusive textual date filter, detail-line and total accumulation.

The remaining obligations from `../complementary-validation-v2/scenario-catalog.json` are returned as explicit `pending`, not fake passes.

## Verify

```bash
../../P2a/.venv/bin/python -m unittest discover -s tests -v
../../P2a/.venv/bin/python -m semantic_checkers --verify-source fixtures/synthetic_success_all_tracks.json --out evidence/synthetic_success_results.json
../../P2a/.venv/bin/python -m semantic_checkers --verify-source fixtures/synthetic_known_wrong_all_tracks.json --out evidence/synthetic_known_wrong_results.json
../../P2a/.venv/bin/python - <<'PY'
import json
from pathlib import Path
import jsonschema
schema=json.loads(Path('schema/check-results.schema.json').read_text())
for p in [Path('evidence/synthetic_success_results.json'), Path('evidence/synthetic_known_wrong_results.json')]:
    jsonschema.validate(json.loads(p.read_text()), schema)
    print('schema ok', p)
PY
```

## Runner interface

Input: fixture JSON with typed observations under `observations.posting`, `observations.interest`, and `observations.reporting`.

Output: JSON object with `fixtureId` and 25 `results`. Each result has:

- `obligationId`
- `track`
- `status` (`pass`, `failed`, `pending`, `inconclusive`)
- `sourceAnchors`
- `boundaries`
- `details.sourceExpected`
- `details.observed`
- optional `details.failures` or `details.pendingReason`

`rawBytes`/`reportLineBytes` missing is a failure distinct from an empty byte string.
