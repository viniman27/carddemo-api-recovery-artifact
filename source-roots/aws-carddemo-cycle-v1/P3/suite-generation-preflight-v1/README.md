# suite-generation-preflight-v1

Status: synthetic/preparation only. Campaign authorization: `false`.

This package adds the missing T1/T2/T3 preparation layer that can feed the real `campaign-harness-v3` freeze/load/union path without starting AWS, LLM, or official test campaigns.

## Scope

- T1 outbound package preparation only: versioned contract + common instruction + declared supported parameters marked `pending_approval`; no provider call and no model availability/probe claim.
- T1 response ingestion: strict import from a preserved raw response; concrete requests are imported, abstract/invalid entries are counted and preserved as invalid; omissions are not repaired or completed.
- T2 Schemathesis: pinned `schemathesis==4.27.1` offline generation against synthetic OpenAPI 3.1 only; generation is persisted before import; Hypothesis uses `Phase.generate`, no database/shrinking/replay HTTP; seeds/directions/budgets are configurable and qualification caps are smaller/explicit.
- T3 MBT preparation: deterministic BFS over a synthetic finite model; only explicit concrete mappings become requests; guard/variant-sensitive or abstract entries are blocked fail-closed under the v3 rule.
- Union: freezes and reloads T1/T2/T3 through `P3/campaign-harness-v3/src/campaign_harness.py`, asserts the module path, then builds union with the harness v3 `UnionBuilder`.

## CLI

```bash
P3/.venv-fuzz-preflight/bin/python P3/suite-generation-preflight-v1/suite_generation_cli.py synthetic-preparation --output P3/suite-generation-preflight-v1/evidence-synthetic-20260915T-prep
```

There is intentionally no official generation mode:

```bash
P3/.venv-fuzz-preflight/bin/python P3/suite-generation-preflight-v1/suite_generation_cli.py official --output /tmp/blocked
# exits 2: official generation is gate-closed
```

## Gate-closed future instructions

External/T1 package submission and model/provider probes remain pending approval. Before campaign use, an official gate must approve the external package/model/transport, official fixture authority, official T2 budgets/runners, reviewed independent reference/mapping variants, and execution harness campaign run.

Synthetic evidence in this directory must not be promoted to official T1/T2/T3/T4 campaign evidence.
