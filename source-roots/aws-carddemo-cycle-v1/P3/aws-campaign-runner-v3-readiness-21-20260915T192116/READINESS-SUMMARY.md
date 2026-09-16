# AWS CardDemo runner v3 local readiness summary

Scope: bounded local readiness only, not an official campaign and not a T4 result.

## Execution

Command:

```bash
cd "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/aws-campaign-runner-v3"
../../P2a/.venv/bin/python local_readiness_21.py ../aws-campaign-runner-v3-readiness-21-20260915T192116
```

Output:

```json
{
  "attempted": 21,
  "completed": 21,
  "structural_ok": 21,
  "measurement_admissible": 3,
  "planned": 21,
  "stopPolicy": {"stopped": false, "reason": null},
  "officialExecutionStarted": false,
  "localReadinessExecution": true
}
```

## Observations

- Selection covered 7 contracts × 3 tracks = 21 frozen requests from `P3/campaign-freeze-package-v1`, preserving request bytes. Case/suite IDs were changed only for unique local-readiness directories.
- Runner v3 copied all six E1/E2 `response-original.txt` contract sources into the isolated cycle and built isolated P2b before facade startup.
- HTTP/contract structural checks passed for all 21: 8×200, 3×400, 10×documented 500.
- Same-invocation audit linkage was found for 9/21: all SDD cases and E2-1/E2-3 few-shot facade cases.
- Preparatory coverage was admissible for the 3 SDD/P2b direct cases only.
- E1 zero-shot cases returned documented 500 technical-failure responses before P2b audit creation (`unresolved local binding token` class); E2-2 selected requests returned 400 before P2b audit creation. These are preserved readiness findings, not treated as oracle failures.

Evidence files:

- Full report: `campaign-report.json`
- Selection manifest: `../aws-campaign-runner-v3/readiness-selection-v1/SELECTION-MANIFEST.json`
- Per-case receipts/applications: suite `cases/*/replay/` subdirectories under this run root.
