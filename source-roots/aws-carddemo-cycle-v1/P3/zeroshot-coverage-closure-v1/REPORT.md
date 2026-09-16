# Zero-shot coverage closure v1

Scope: bounded local readiness only; not an official campaign.

## Change

`unified-preflight-v3/src/coverage_runner_v3.py` now resolves command-log evidence from the audited P2b run directory. Direct P2b/few-shot runs still use `P2b/command-log.jsonl`; zero-shot facade runs under `{application}/zero-shot-runs/p2b-runs/{track-*}` also search the audit-bound `{application}/zero-shot-runs/command-log.jsonl`. This preserves the prefix evidence gate: GCOV_PREFIX is accepted only when an exact command-log row for the exact run dir and business program is present.

## Bounded run

Input suite: `inputs/T3-BINDING-CLOSURE-V1-E1-1-3TRACK.json`, filtered from `../t3-binding-closure-v1/amended-candidates/T3-BINDING-CLOSURE-V1.json`.

Execution output: `real-readiness-E1-1-3track/campaign-report.json`.

Summary: `SUMMARY.json`.

Results:

- planned/attempted/completed: 3/3/3
- structural_ok: 3
- measurement_admissible: 3
- experimentalViolations: []
- measurementWarnings: []
- officialCampaign: false

Admissible receipts:

- `BINDCLOSE-E1-1-interest-T3-0001-d3efd655d1ef` → `CBACT04C`, GCOV prefix observed in `zero-shot-runs/command-log.jsonl`
- `BINDCLOSE-E1-1-posting-T3-0019-bb43244b06b8` → `CBTRN02C`, GCOV prefix observed in `zero-shot-runs/command-log.jsonl`
- `BINDCLOSE-E1-1-reporting-T3-0026-deffa082a6b3` → `CBTRN03C`, GCOV prefix observed in `zero-shot-runs/command-log.jsonl`

## Verification commands

```bash
../P2a/.venv/bin/python -m unittest discover -s unified-preflight-v3/tests -v
../P2a/.venv/bin/python -m unittest discover -s aws-campaign-runner-v3/tests -v
../P2a/.venv/bin/python zeroshot-coverage-closure-v1/run_e1_1_3track_readiness.py
```
