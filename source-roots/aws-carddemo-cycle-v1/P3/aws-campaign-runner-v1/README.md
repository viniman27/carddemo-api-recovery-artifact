# aws-campaign-runner-v1

Official-capable AWS CardDemo campaign wrapper over the current qualified P3 harness/API/coverage integration.

Scope: executable wrapper only. It does not generate T1/T2/T3/T4 suites, does not read evaluation-quarantine oracle/expected-output files, and does not authorize or start an official campaign by labels alone.

## Prerequisites

- Frozen parent-supplied T1/T2/T3/T4 suite JSON files accepted by `campaign-harness-v3.load_frozen_suite`.
- P2a Python: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P2a/.venv/bin/python`.
- Current 7-contract/21-operation campaign config: `P3/campaign-configuration-v2/campaign-config-v2.json` with source hash/byte pins intact.
- Current harness-v3 module hash: `0e5a9606b7d1ec10c2c07929a2fd18b72748e90ebdc4987a937bdc8fed5dd36e`.
- For real P2b execution only: existing unified-preflight-v3 integration, GnuCOBOL/gcc-11/gcov-11 toolchain, fixture package/registry, research corpus/support files.
- Official execution requires a separate readiness JSON with `officialReady: true` and `campaignAuthorized: true` supplied by the parent. No official execution was run here.

## Plan-only candidate invocation

```bash
<WORKSPACE>/aws-carddemo-cycle-v1/P2a/.venv/bin/python \
  P3/aws-campaign-runner-v1/aws_campaign_runner_cli.py \
  --mode plan \
  --suite /ABS/PARENT/FROZEN/T1.json \
  --suite /ABS/PARENT/FROZEN/T2.json \
  --suite /ABS/PARENT/FROZEN/T3.json \
  --suite /ABS/PARENT/FROZEN/T4.json \
  --output P3/aws-campaign-runner-v1/plan.json
```

## Official execution candidate invocation for parent only

```bash
<WORKSPACE>/aws-carddemo-cycle-v1/P2a/.venv/bin/python \
  P3/aws-campaign-runner-v1/aws_campaign_runner_cli.py \
  --mode execute \
  --official-ready-json /ABS/PARENT/official-readiness.json \
  --suite /ABS/PARENT/FROZEN/T1.json \
  --suite /ABS/PARENT/FROZEN/T2.json \
  --suite /ABS/PARENT/FROZEN/T3.json \
  --suite /ABS/PARENT/FROZEN/T4.json \
  --output /ABS/PARENT/OFFICIAL-RUN-DIR
```

## Policies implemented

- Serial one-attempt execution; no retries.
- Per-application local target lifecycle; stop must prove quiet or execution stops.
- Structural response checks are independent of harness expectations and use the contract source pinned for the case `contractId`.
- Raw response bytes are preserved as `response_body_b64`; request body bytes are pinned in plan output.
- Resume mode skips only case IDs already completed in prior receipts and writes a new replay directory.
- Coverage evidence is collected from unified-preflight-v3 helpers for real P2b runs; gcov errors/missing denominator are inadmissible, never coerced to zero.
