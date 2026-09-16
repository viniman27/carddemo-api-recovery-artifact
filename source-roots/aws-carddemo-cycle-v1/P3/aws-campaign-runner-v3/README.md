# aws-campaign-runner-v2

Official-capable AWS CardDemo campaign wrapper over the current qualified P3 harness/API/coverage integration.

Scope: executable wrapper only. It does not generate T1/T2/T3/T4 suites, does not read evaluation-quarantine oracle/expected-output files, and does not authorize or start an official campaign by labels alone.

## Prerequisites

- Frozen parent-supplied T1/T2/T3/T4 suite JSON files accepted by `campaign-harness-v3.load_frozen_suite`.
- P2a Python: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P2a/.venv/bin/python`.
- Current 7-contract/21-operation campaign config: `P3/campaign-configuration-v2/campaign-config-v2.json` with source hash/byte pins intact.
- Current harness-v3 module hash: `0e5a9606b7d1ec10c2c07929a2fd18b72748e90ebdc4987a937bdc8fed5dd36e`.
- For real P2b/P2c execution only: existing unified-preflight-v3 integration, GnuCOBOL/gcc-11/gcov-11 toolchain, fixture package/registry, research corpus/support files.
- T3 or other suites that omit `contractId`/`operationId`/`track` require explicit parent-supplied `--case-metadata` keyed by `suite_id:case_id` or `case_id`; v2 does not infer arbitrary aliases from origin/cell text.
- Official execution requires a separate readiness JSON with `officialReady: true` and `campaignAuthorized: true` supplied by the parent. No official execution was run here.

## Plan-only candidate invocation

```bash
<WORKSPACE>/aws-carddemo-cycle-v1/P2a/.venv/bin/python \
  P3/aws-campaign-runner-v2/aws_campaign_runner_cli.py \
  --mode plan \
  --suite /ABS/PARENT/FROZEN/T1.json \
  --suite /ABS/PARENT/FROZEN/T2.json \
  --suite /ABS/PARENT/FROZEN/T3.json \
  --suite /ABS/PARENT/FROZEN/T4.json \
  --case-metadata /ABS/PARENT/case-metadata.json \
  --output P3/aws-campaign-runner-v2/plan.json
```

## Official execution candidate invocation for parent only

```bash
<WORKSPACE>/aws-carddemo-cycle-v1/P2a/.venv/bin/python \
  P3/aws-campaign-runner-v2/aws_campaign_runner_cli.py \
  --mode execute \
  --official-ready-json /ABS/PARENT/official-readiness.json \
  --suite /ABS/PARENT/FROZEN/T1.json \
  --suite /ABS/PARENT/FROZEN/T2.json \
  --suite /ABS/PARENT/FROZEN/T3.json \
  --suite /ABS/PARENT/FROZEN/T4.json \
  --case-metadata /ABS/PARENT/case-metadata.json \
  --output /ABS/PARENT/OFFICIAL-RUN-DIR
```

## Policies implemented

- Serial one-attempt execution; no retries.
- Per-case replay directories under `SUITE/cases/CASE/replay`, so every attempted case has a complete receipt/application record even when a later stop condition occurs.
- Per-contract target dispatch through current qualified integration: zero-shot E1 via `P2c-zero-shot/p2c_facade.py serve --contract`, few-shot E2 via `P2c-few-shot/p2c_facade.py serve --contract-id`, SDD via unified `target_p2b`.
- Per-application local target lifecycle; transport/deadline/startup/quietness failures stop subsequent execution.
- Structural response checks are independent of harness expectations and use the contract source pinned for the case `contractId`.
- Experimental structural/schema/status and expectation violations are recorded and execution continues; harness expectation `inconclusive_until_checker_bound` remains a business expectation result, separate from structural checker authority.
- Raw response bytes are preserved as `response_body_b64`; request body bytes are pinned in plan output.
- Resume mode skips every previously attempted case ID, including failed attempts; it does not retry failed cases.
- Coverage evidence is collected from unified-preflight-v3 `collect_fresh_coverage_evidence(p2b, audit_path, track)` using explicit case track metadata, not URL suffix guesses; gcov errors/missing denominator are inadmissible, never coerced to zero.
