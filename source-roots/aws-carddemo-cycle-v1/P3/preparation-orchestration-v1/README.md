# Preparation orchestration v1

Local-only orchestration closure for AWS CardDemo P3 preparation.

This package does not authorize or run official AWS generation, campaign replay, external T1 sending, COBOL/API execution, or fixture/oracle promotion.

## What it fixes locally

- T2 seed/direction CLI defaults are handled without `append` default duplication in this wrapper.
- T2 cases are bound to candidate fixture package IDs per operation track (`posting`, `interest`, `reporting`) instead of a placeholder resource package.
- T3 records the explicit final candidate budget `maxDepth=6`, `maxPathsPerTrackFixture=50` while preserving existing `t3-sdd-external-selection-v3` static evidence produced under `maxPaths=12`.
- Consolidated candidate config pins current `t2-offline-preparation-v4` and `t3-sdd-external-selection-v3` entrypoints and records the promotion/freeze procedure.

## Static dry-run

```bash
python3 orchestration_cli.py dry-run \
  --config ../campaign-configuration-v2/campaign-config-v2.json \
  --output DRY-RUN-ALL7-21-default \
  --t3-max-paths-per-track-fixture 50
```

Outputs:

- `STATIC-DRY-RUN.json` — all 7 contracts / 21 operations with candidate per-operation resource binding and no release.
- `CONSOLIDATED-CANDIDATE-CONFIG.json` — pinned local candidate configuration.
- `PROMOTION-FREEZE-PROCEDURE.md` — human gate procedure for promotion/freeze.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

The tests are synthetic/local only and include no provider, API, COBOL, official freeze, or replay calls.
