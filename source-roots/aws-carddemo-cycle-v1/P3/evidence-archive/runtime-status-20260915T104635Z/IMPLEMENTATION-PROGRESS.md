# P3 implementation progress — preparation only

Current successor: `FIXTURE-INTEGRATION-V2.md` and `current-pretest-state-v2.json`. External resource bytes are now bound and technically exercised across three tracks; official readiness remains false, including explicit residual binding defects. The remainder is preserved historical evidence.

Status: APIs and local preparation checks advanced; experimental readiness remains **not approved** and non-executable until P3 freeze.

## Implemented APIs / local infrastructure

- Closed P2b `TRANREPT` mixed known+unknown capture defect in `P2b/p2b_binding.py`.
  - Unknown meaningful report records now classify the whole capture as `unmapped_meaningful` even when public records were also parsed.
  - Response remains within approved semantics: `500 technical_failure` with `availableContent` carrying the parsed public content; no public contract fields/routes/status semantics were added.
  - Raw report evidence remains in audit classifications and preview; no silent loss of unknown records.
- Added unit regression in `P2b/tests/test_p2b_contract.py` for mixed known+unknown report output.
- Added non-executing P3 configuration validator in `P3/pretest_config.py`.
- Added sample review-only local fixture registry and campaign config:
  - `P3/fixture-registry.sample.json`
  - `P3/campaign-config.sample.json`
- Added P3 schema/preparation tests in `P3/tests/test_pretest_config.py`.

## Verified outputs from this run

Pre-edit smoke evidence was archived before edits/rerun:

- `P2b/evidence-archive/20260914T204319Z/archive-manifest.json`

Commands executed after changes:

```text
cd P2b && python3 -m unittest discover -s tests -v
cd P3 && python3 -m unittest discover -s tests -v && python3 pretest_config.py > latest-pretest-config.stdout.json
cd P2b && python3 p2b_binding.py smoke > latest-smoke.stdout.json && ../P2a/.venv/bin/python validate_p2b.py > latest-schema.stdout.json
```

Observed results:

- P2b unit QA: 10 tests, OK.
- P3 config/schema QA: 3 tests, OK.
- P3 config validator output: fixture registry OK, campaign config OK, `execution_decision.allowed=false` because freeze approval is missing and config is non-executing.
- P2b actual three-track technical smoke:
  - posting: HTTP 200, body hash `dc0993245be957bdfbc1b0eec578d6d8d04768950b5ad4fe1a8291cb0d3cd73c`
  - interest: HTTP 200, body hash `b27f4bb9963fe61a42a2447840080758d01c8b01aae4b4f89d6648cc4182751d`
  - reporting: HTTP 200, body hash `3b23608f612159d0925be6d104a377a808c6716832e7deeb631fd5510e1643d3`
- Schema QA: `overall_passed=true` for posting, interest, reporting and bad-request shape.

Current changed artifact hashes:

```text
bbbe31796614e2a8ee24ba14c2fe8c81f158c0a755dcd7f5c2ab61fd87c29c99  P2b/p2b_binding.py
d8cb5b4e6cdb63069f216fa278146fa2741f07c20388959a13b2e5010b0bbb74  P2b/tests/test_p2b_contract.py
1aeecfe23c3866c10f176d69dded672b302a01f2ec5dbdf0d34631a7a43f2097  P3/pretest_config.py
82ab2acbd51929745cacfa6f240c9639b184ec14d66fed71b4b3d7fbdfbe22fe  P3/tests/test_pretest_config.py
468ac4c2dabc5f05697468d46a4c0193de4ee6483b3cf7f467f810bbbc983d6e  P3/fixture-registry.sample.json
f70f2a91aee533c3913f163eb41a2cc2a690f3e84250e6d793129e110bcbb256  P3/campaign-config.sample.json
```

## Implementation remaining

- Replace sample fixture registry entries with frozen human-approved fixture records and real content hashes.
- Add official fixture materializer only after fixture policy and contents are frozen.
- Add campaign runner only after budgets, seeds, order, reset, oracle and analysis policies are frozen.
- Define independent T3 MBT oracle/model package; current P3 schema only marks it pending.
- Define official before/after resource hash checks and stateful sequence handling; current default is fresh directory per run, with stateful sequences pending.

## Experimental readiness / unresolved choices

Not ready for official pretests. Missing decisions remain pending:

- T1 model/version, budget, repetitions/retry and seed policy.
- T2 fuzzer/tool/version, budget, checkers and seeds.
- T3 independent model/oracle authority.
- T4 union/deduplication policy and dependent-analysis treatment.
- Official fixture selection and exposure policy.
- Oracle/failure taxonomy and analysis denominators.
- Stateful sequence policy, if any.

No official fixtures, oracle answers, model generations, E1/E2 comparisons, production services, or T1/T2/T3/T4 executions were created or run.
