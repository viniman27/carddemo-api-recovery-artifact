# Few-shot coverage closure v1

Bounded readiness reproduction for the readiness-21 few-shot coverage failure.

## Scope

- Uses existing `aws-campaign-runner-v3` readiness selections for E2-1 and E2-3 only.
- Applies reusable isolated measurement adaptation from `unified-preflight-v3/src/coverage_runner_v3.py` through the normal v3 runner preparation path.
- Does not edit original COBOL, OpenAPI/contracts, public facade response projection, or business rules.
- Does not read business oracles.

## Verification command

```bash
cd "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1"
P2a/.venv/bin/python P3/fewshot-coverage-closure-v1/run_fewshot_readiness_subset.py
```

Latest evidence: `evidence-20260915T192853Z/fewshot-coverage-summary.json`

Result summary:

- planned/attempted/completed: 6/6/6
- structural_ok: 6
- measurement_admissible: 6
- measurementWarnings: []
- business `.gcda` present for all six same-invocation runs
- `GCOV_PREFIX` observed for all six business commands
- `gcov-11` exit code 0 for CBTRN02C, CBACT04C, CBTRN03C units

Normal non-zero COBOL process exits are preserved as process exits, not rewritten: E2 posting exited 4; E2-1 reporting exited 12.
