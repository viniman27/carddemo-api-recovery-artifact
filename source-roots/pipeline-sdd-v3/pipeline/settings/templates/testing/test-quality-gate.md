# Post-Stage-9 Test Quality and Coverage Gate

This is a complementary downstream testing gate after Stage 9 reports `api_ready_for_testing=true`. It is not Stage 10, does not reopen stages 1–9, and does not approve T1–T4 execution by itself. Stage 8 remains the semantic validation plan; this gate qualifies whether prepared test suites, oracles, fixtures, coverage accounting and checker evidence are ready for human review before campaign execution or before interpreting results.

## Entry condition

- Stage 9 handoff evidence exists and records `api_ready_for_testing=true` separately from `campaign_ready`.
- The runnable API, contract pins, fixture/resource setup, reset mechanism and known limits are documented by Stage 9 or by the operational handoff it references.
- No stage 1–8 artifact, Stage 9 evidence, source corpus, contract, API, fixture bytes or prepared case bytes are edited to satisfy this gate.

## Freeze discipline

- Freeze the suite, budgets, seeds, checker versions, fixture package, resource reset procedure, coverage denominator and oracle inventory before observing campaign results.
- Record the freeze ID and timestamp in the manifest.
- Descriptive post-observation supplementation is allowed only as a separate addendum. It may explain observed failures or add examples for readers, but it must not be counted as pre-frozen coverage or used to redefine success after results.
- Do not choose a coverage-percent target after seeing results. Coverage is evaluated against a known inventory of obligations/checks and explicitly reported gaps, not gamed toward a convenient percentage.

## Oracle rules

- Contract/schema checks answer only structural conformance: status codes, media types, JSON schema shape and documented error envelopes.
- Business/semantic checks require an expected-outcome authority independent of the LLM outputs that produced the contract, adapter, validation plan or checker. A generated contract, generated harness, third-party fuzzer, or LLM answer is not an independent business oracle.
- Tool independence and oracle independence are separate. A fuzzer driven only by OpenAPI can find structural issues, but cannot attest fidelity to the legacy/domain obligation.
- Each business/semantic oracle must include at least one wrong-output counterexample that would fail the checker. A checker that only accepts happy outputs without a known bad-output rejection test is inconclusive.
- Do not label human review as approved from a tool result. Tool output can say ready for review, fail, or inconclusive; only the recorded reviewer can approve.

## Coverage accounting

Record a known denominator before execution. The denominator is the set of obligations/checks eligible for this run, not the number of successful requests.

| Field | Meaning |
|---|---|
| `executed` | A frozen check actually ran and produced enough observation for a verdict. |
| `not_executed` | A planned obligation had no valid execution; keep the reason. Do not hide it as N/A. |
| `inconclusive` | Execution happened or evidence exists, but observation is insufficient for the claimed question. |
| `not_applicable` | The obligation is outside this run by justified scope, not because it failed to run. |
| `gap_items` | Missing authority, missing fixture, missing checker binding, missing observation or unresolved traceability. |

The counts must sum to the denominator. `all not_executed` is not unobservable success and not N/A. A baseline can be structurally all-pass while semantic coverage remains inconclusive; report those lanes separately.

## Fixture/resource reset

- Reset must be per case, not merely per process or per suite, unless the frozen test design explicitly proves cases are independent without reset.
- Compare resource snapshots before and after setup, after mutation, and after a fresh preparation. Include every physical resource needed by the program, not only logical names.
- Fixture selection and reset evidence are infrastructure evidence, not business oracles.

## Campaign-specific integrity checklist

### T1 — Generated or model-proposed cases

- Preserve bad or unusable generator outputs in results/evidence; do not delete them to make the generator look perfect.
- Count generated, frozen, executed and verdict-bearing cases separately.
- A revised prompt or manually repaired output is a new version or supplementation, not an independent replica of the original output.

### T2 — OpenAPI fuzzing and domain fuzzing

- State whether the run is pure OpenAPI fuzzing or domain-guided fuzzing.
- Pure OpenAPI fuzzing must not claim domain coverage by itself.
- Domain fuzzing must declare the extra domain authority and keep it separate from contract-derived generation.
- Generate/freeze offline, then replay frozen requests once with redirects/retries disabled when side effects matter.

### T3 — Model-based tests

- Guards and transitions must be bound to executable checkers, not just prose diagrams.
- Exclude cases whose guard result is not the boolean value `true` from execution-ready suites; record exclusions separately.
- Model state coverage and business obligation coverage are different denominators.

### T4 — Union suite

- The union introduces no new cases; it combines frozen qualified T1/T2/T3 inputs.
- The union has fresh reset/isolation for every case.
- The union is not an independent replica and must not be counted as a fourth independent evidence source.

## Mutation and negative evidence

Mutations may qualify test/checker strength only. They must not alter the source corpus, contracts, APIs, frozen prepared cases, fixtures or results. Record mutation evidence as checker evidence: which wrong behavior was injected or simulated, which checker rejected it, and what original artifact remained unchanged.

## Ready / fail / inconclusive

- `ready_for_review`: the manifest satisfies mechanical prerequisites, distinguishes schema from business oracles, accounts for coverage denominator/counts, records reset evidence, campaign integrity, mutation scope and traceability gaps. This is not human approval.
- `fail`: a required prerequisite is missing or contradicted: no independent business oracle for business claims, unknown denominator, all obligations not executed, missing reset, unfrozen results, T3 checker bindings missing, T4 adds new cases, mutations alter source artifacts, or a tool claims human approval.
- `inconclusive`: substantive reviewer state when evidence exists but does not support the question. Record it as a result, not as a pass or fail. Examples: HTTP/schema pass without semantic oracle; coverage generated by execution but no semantic checker; observed legacy exit without enough output authority.

## Manifest validation

Instantiate `test-quality-gate-manifest.json` and run, from `pipeline/`:

```bash
python3 tools/check_test_quality_gate.py path/to/test-quality-gate.json
```

The validator is intentionally narrow and generic. It checks the manifest discipline above; it does not inspect raw HTTP traces, authenticate reviewers, compute coverage, run T1–T4, or approve campaigns.
