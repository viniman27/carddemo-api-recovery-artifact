# complementary-matrix-v1

Final local preparation package for the complementary essential-scenario × seven-contract matrix.

## Scope

- 12 essential scenarios: 6 posting, 2 interest, 4 reporting.
- 7 frozen contracts from `campaign-configuration-v2`.
- 84 candidate applications in `latest/suite.freeze.json`.
- Uses actual existing complementary fixture evidence/freeze files and qualified semantic-checker metadata.
- Does not generate new external cases, call LLMs, alter contracts, alter COBOL, or start the full 84-run execution.

## Verified commands

```bash
cd "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/complementary-matrix-v1"
python3 -m unittest discover -s tests -v
python3 matrix_cli.py --plan --output latest
python3 matrix_cli.py --verify-plan latest/execution-plan.json
```

## Main-process launch command

Read `latest/execution-plan.json` field `parentOwnedLaunchCommand`. It points to the frozen suite and readiness file under `latest/` and writes results to `latest/FULL-84-RUN`.

The SDD public contract accepts `{}` only for these operations; fixture-specific inputs are therefore explicitly recorded as nonexpressible blocks rather than smuggled into the request.
