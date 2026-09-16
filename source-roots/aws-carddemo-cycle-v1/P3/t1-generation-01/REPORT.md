# T1 generation 01 — real transport attempt

Status: **blocked before T1 generation calls**.

## Authorization recorded

Real consent was recorded in `consent.json` from the delegated task context: user replied “Pode prosseguir” to the parent authorization question. No signature or administrative approval was fabricated.

Authorized scope recorded: one fresh synthetic probe and, only if it passed, exactly one T1 generation call per prepared contract using `openai-codex` / `gpt-6-astra`, with `store=false`, `tools=[]`, `previous_response_id=null`, no `temperature`, no `max_output_tokens`, no `seed`, no retry/fallback/model switch, and only contract/instruction/metadata in outbound payloads.

## Pre-send checks completed

- Verified package `REPORT.json`: `verify_ok=true`, `self_test_ok=true`.
- Verified seven prepared T1 payload pins against `MANIFEST.json`.
- Materialized `transformations.json` describing the effective outbound transformation:
  - preserved the prepared user prompt containing common T1 instruction and contract text;
  - preserved generic exclusion-policy wording from the original prompt;
  - removed the preparation/admin/system layer and local absolute source-path metadata from the effective provider request;
  - recorded preview hashes for the effective outbound requests.

## Real provider probe result

One fresh synthetic probe was sent and persisted:

- runner session: `proc_2a5864b7dc44` (exited)
- HTTP status: `400`
- provider body persisted at `raw-sse/probe-synthetic-fresh.sse.txt`
- provider error body: `{"detail":"Unsupported parameter: previous_response_id"}`
- request persisted at `outbound-effective/probe-synthetic-fresh.request.json`
- receipt persisted at `receipts/probe-synthetic-fresh.receipt.json`

Because the authorized transport required `previous_response_id=null` and the provider rejected that parameter, the run stopped without attempting any official T1 contract generation.

## Counts

- Expected contracts: 7
- Probe completed: 0
- Complete T1 generations: 0
- Invalid T1 generations: 0
- Interrupted T1 generations: 0
- Blocked T1 generations: 0

No model output was repaired, no synthetic importer output was promoted as official generation, no duplicate provider calls were made after the blocker, and no T2/T3/T4/API/COBOL campaign runtime was executed.
