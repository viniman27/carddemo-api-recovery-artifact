# T3 Campaign Adapter v2

Status: candidate/static preparation only. Official AWS campaign generated: false.

## Fixed in this adapter

- Resolves the exact seven `contractId` values from `campaign-configuration-v2/campaign-config-v2.json`.
- Extracts each pinned OpenAPI from its original source (`parsed.json` text for E1/E2, P2a JSON for SDD) and preserves source identity/hash/bytes.
- Builds and runs T3 with the requested contract's own schema; E1/E2 are never validated against the SDD schema.
- Fails closed on unknown contract IDs, cross-contract path/schema mismatches, and blocked upstream cells.
- Keeps reference-engine guard traversal, fixture materialization, and explicit freeze behavior unchanged.

## Static all7 check

Contract count: `7`.
Joined/block/inconclusive summary: `{"E1-1": {"blockedJoinedCells": 79, "eligibleJoinedCells": 11, "inconclusiveTransitionsWithoutCells": 0}, "E1-2": {"blockedJoinedCells": 79, "eligibleJoinedCells": 11, "inconclusiveTransitionsWithoutCells": 0}, "E1-3": {"blockedJoinedCells": 79, "eligibleJoinedCells": 11, "inconclusiveTransitionsWithoutCells": 0}, "E2-1": {"blockedJoinedCells": 90, "eligibleJoinedCells": 0, "inconclusiveTransitionsWithoutCells": 0}, "E2-2": {"blockedJoinedCells": 79, "eligibleJoinedCells": 11, "inconclusiveTransitionsWithoutCells": 0}, "E2-3": {"blockedJoinedCells": 90, "eligibleJoinedCells": 0, "inconclusiveTransitionsWithoutCells": 0}, "E3-SDD-stage6r3": {"blockedJoinedCells": 0, "eligibleJoinedCells": 0, "inconclusiveTransitionsWithoutCells": 62}}`.
Remaining materialization blocks by real type after correct schema binding: `{"E1-1": {"schema_validation_failed": 16}, "E1-2": {"schema_validation_failed": 16}, "E1-3": {"unsupported_sequential_record_format": 16}, "E2-1": {"unsupported_sequential_record_format": 14}, "E2-2": {"unsupported_sequential_record_format": 16}, "E2-3": {"unsupported_sequential_record_format": 14}, "E3-SDD-stage6r3": {}}`.

## Simple invocation for next authorized generation

```bash
cd "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1"
P2a/.venv/bin/python P3/t3-campaign-adapter-v2/src/t3_campaign_adapter.py   --contract-id E1-1   --capability CBTRN02C_POSTTRAN --capability CBACT04C_INTCALC --capability CBTRN03C_TRANREPT   --max-depth 8 --max-paths-per-capability 100   --freeze-output P3/t3-campaign-adapter-v2/evidence/T3-E1-1-authorized-candidate.json
```

Do not run that freeze command as an official campaign unless P3 authorization covers the output path and budgets.
